"""
Gmail Agent: Handles all Gmail API operations
"""

import os
import base64
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from backend.utils import retry_on_failure, clean_html


class GmailAgent:
    """Agent for Gmail operations - fetching, filtering, and sending emails"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send'
    ]
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.GmailAgent")
        
        self.credentials_path = config.get("google", {}).get("credentials_path", "google_auth/credentials.json")
        self.token_path = config.get("google", {}).get("token_path", "google_auth/token.json")
        
        self.service = None
        self._authenticate()
    
    def _authenticate(self) -> None:
        """Authenticate with Google Gmail API"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
        
        # If no valid credentials, go through OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    self.logger.error(f"Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(f"Gmail credentials file not found: {self.credentials_path}")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        # Build the Gmail service
        self.service = build('gmail', 'v1', credentials=creds)
        self.logger.info("Gmail authentication successful")
    
    @retry_on_failure(max_retries=3)
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Gmail-related task
        
        Args:
            task: Task configuration with parameters
            
        Returns:
            Task execution results
        """
        
        task_type = task.get("description", "").lower()
        parameters = task.get("parameters", {})
        
        try:
            if "fetch" in task_type or "get" in task_type:
                return self.fetch_emails(parameters)
            elif "send" in task_type:
                return self.send_email(parameters)
            else:
                # Default to fetching emails
                return self.fetch_emails(parameters)
                
        except Exception as e:
            self.logger.error(f"Gmail task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"Failed to execute Gmail task: {e}"
            }
    
    def fetch_emails(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch emails based on parameters
        
        Args:
            parameters: Query parameters (query, max_results, time_range)
            
        Returns:
            Fetched email data
        """
        
        query = parameters.get("query", "is:unread")
        max_results = parameters.get("max_results", 10)
        time_range = parameters.get("time_range", "1d")
        
        # Add time constraint to query
        query_with_time = self._add_time_constraint(query, time_range)
        
        try:
            # Search for messages
            results = self.service.users().messages().list(
                userId='me',
                q=query_with_time,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return {
                    "success": True,
                    "count": 0,
                    "content": "No emails found matching the criteria",
                    "emails": []
                }
            
            # Fetch detailed message data
            email_data = []
            for message in messages[:max_results]:
                email_details = self._get_message_details(message['id'])
                if email_details:
                    email_data.append(email_details)
            
            # Create summary content
            content = self._format_email_summary(email_data)
            
            self.logger.info(f"Fetched {len(email_data)} emails")
            
            return {
                "success": True,
                "count": len(email_data),
                "content": content,
                "emails": email_data,
                "query_used": query_with_time
            }
            
        except HttpError as e:
            self.logger.error(f"Gmail API error: {e}")
            return {
                "success": False,
                "error": f"Gmail API error: {e}",
                "content": "Failed to fetch emails due to API error"
            }
    
    def _add_time_constraint(self, query: str, time_range: str) -> str:
        """Add time constraint to Gmail query"""
        
        # Parse time range
        if time_range.endswith('d'):
            days = int(time_range[:-1])
            date = (datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')
            return f"{query} after:{date}"
        elif time_range.endswith('h'):
            hours = int(time_range[:-1])
            # Gmail doesn't support hour precision, convert to days
            days = max(1, hours // 24)
            date = (datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')
            return f"{query} after:{date}"
        else:
            return query
    
    def _get_message_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific message"""
        
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}
            
            # Extract body
            body = self._extract_message_body(message['payload'])
            
            # Extract date
            internal_date = int(message['internalDate']) / 1000
            email_date = datetime.fromtimestamp(internal_date)
            
            return {
                "id": message_id,
                "subject": headers.get('Subject', 'No Subject'),
                "from": headers.get('From', 'Unknown'),
                "to": headers.get('To', 'Unknown'),
                "date": email_date.strftime('%Y-%m-%d %H:%M:%S'),
                "snippet": message.get('snippet', ''),
                "body": body[:1000],  # Truncate body
                "labels": message.get('labelIds', [])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get message details for {message_id}: {e}")
            return None
    
    def _extract_message_body(self, payload: Dict[str, Any]) -> str:
        """Extract body text from message payload"""
        
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body_data = part['body']['data']
                        body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/html':
                    if 'data' in part['body']:
                        body_data = part['body']['data']
                        html_body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        body = clean_html(html_body)
        else:
            if payload['mimeType'] == 'text/plain':
                if 'data' in payload['body']:
                    body_data = payload['body']['data']
                    body = base64.urlsafe_b64decode(body_data).decode('utf-8')
            elif payload['mimeType'] == 'text/html':
                if 'data' in payload['body']:
                    body_data = payload['body']['data']
                    html_body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                    body = clean_html(html_body)
        
        return body.strip()
    
    def _format_email_summary(self, emails: List[Dict[str, Any]]) -> str:
        """Format emails into a readable summary"""
        
        if not emails:
            return "No emails found."
        
        summary_parts = [
            f"=== EMAIL SUMMARY ({len(emails)} emails) ===\n"
        ]
        
        for i, email in enumerate(emails, 1):
            summary_parts.append(f"{i}. FROM: {email['from']}")
            summary_parts.append(f"   SUBJECT: {email['subject']}")
            summary_parts.append(f"   DATE: {email['date']}")
            summary_parts.append(f"   PREVIEW: {email['snippet'][:100]}...")
            summary_parts.append("")
        
        return "\n".join(summary_parts)
    
    @retry_on_failure(max_retries=3)
    def send_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send an email via Gmail API
        
        Args:
            email_data: Email content and metadata
            
        Returns:
            Send result
        """
        
        try:
            # Get recipient - default to configured email
            to_email = email_data.get("to", os.getenv("GMAIL_ADDRESS"))
            subject = email_data.get("subject", "AutoTasker AI Results")
            body = email_data.get("body", "No content provided")
            
            # Create message
            message = MIMEMultipart()
            message['to'] = to_email
            message['subject'] = subject
            
            # Add body
            if email_data.get("format", "text") == "html":
                message.attach(MIMEText(body, 'html'))
            else:
                message.attach(MIMEText(body, 'plain'))
            
            # Encode message
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send message
            send_result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            self.logger.info(f"Email sent successfully to {to_email}")
            
            return {
                "success": True,
                "message_id": send_result['id'],
                "to": to_email,
                "subject": subject,
                "content": f"Email sent successfully to {to_email}"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"Failed to send email: {e}"
            }
    
    def mark_as_read(self, message_ids: List[str]) -> Dict[str, Any]:
        """Mark messages as read"""
        
        try:
            self.service.users().messages().batchModify(
                userId='me',
                body={
                    'ids': message_ids,
                    'removeLabelIds': ['UNREAD']
                }
            ).execute()
            
            return {"success": True, "marked_read": len(message_ids)}
            
        except Exception as e:
            self.logger.error(f"Failed to mark messages as read: {e}")
            return {"success": False, "error": str(e)}
    
    def search_emails(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search emails with custom query"""
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            return [self._get_message_details(msg['id']) for msg in messages]
            
        except Exception as e:
            self.logger.error(f"Email search failed: {e}")
            return []
