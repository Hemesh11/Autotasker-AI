"""
Email Agent: Handles email sending via Gmail API or AWS SES
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Gmail API imports
try:
    from agents.gmail_agent import GmailAgent
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False

# AWS SES imports
try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

from backend.utils import retry_on_failure


class EmailAgent:
    """Agent for sending emails via Gmail API or AWS SES"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.EmailAgent")
        
        # Determine which email service to use
        self.use_gmail = GMAIL_AVAILABLE and config.get("email", {}).get("prefer_gmail", True)
        self.use_ses = AWS_AVAILABLE and config.get("email", {}).get("use_ses", False)
        
        # Initialize services
        self.gmail_agent = None
        self.ses_client = None
        
        if self.use_gmail:
            try:
                self.gmail_agent = GmailAgent(config)
                self.logger.info("Gmail agent initialized for email sending")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Gmail agent: {e}")
                self.use_gmail = False
        
        if self.use_ses or not self.use_gmail:
            try:
                self._initialize_ses()
                self.logger.info("AWS SES initialized for email sending")
            except Exception as e:
                self.logger.warning(f"Failed to initialize AWS SES: {e}")
                self.use_ses = False
        
        if not self.use_gmail and not self.use_ses:
            self.logger.error("No email service available!")
    
    def _initialize_ses(self) -> None:
        """Initialize AWS SES client"""
        self.ses_client = boto3.client(
            'ses',
            region_name=self.config.get("aws", {}).get("region", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
    
    @retry_on_failure(max_retries=3)
    def send_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send email using available service
        
        Args:
            email_data: Email content and metadata
            
        Returns:
            Send result
        """
        
        try:
            # Try Gmail first if available
            if self.use_gmail and self.gmail_agent:
                return self._send_via_gmail(email_data)
            
            # Fallback to SES
            elif self.use_ses and self.ses_client:
                return self._send_via_ses(email_data)
            
            else:
                # Final fallback - save to file
                return self._save_to_file(email_data)
                
        except Exception as e:
            self.logger.error(f"Email sending failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"Failed to send email: {e}"
            }
    
    def _send_via_gmail(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email via Gmail API"""
        
        try:
            result = self.gmail_agent.send_email(email_data)
            
            if result.get("success"):
                self.logger.info("Email sent successfully via Gmail")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Gmail sending failed: {e}")
            raise e
    
    def _send_via_ses(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email via AWS SES"""
        
        try:
            # Get email configuration
            from_email = os.getenv("AWS_SES_EMAIL") or os.getenv("GMAIL_ADDRESS")
            to_email = email_data.get("to", from_email)
            subject = email_data.get("subject", "AutoTasker AI Results")
            body = email_data.get("body", "No content provided")
            
            if not from_email:
                raise ValueError("No sender email configured")
            
            # Prepare email
            message = {
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': body}
                }
            }
            
            # Add HTML version if specified
            if email_data.get("format") == "html":
                message['Body']['Html'] = {'Data': body}
            
            # Send email
            response = self.ses_client.send_email(
                Source=from_email,
                Destination={'ToAddresses': [to_email]},
                Message=message
            )
            
            self.logger.info(f"Email sent successfully via SES to {to_email}")
            
            return {
                "success": True,
                "message_id": response['MessageId'],
                "service": "AWS SES",
                "to": to_email,
                "subject": subject,
                "content": f"Email sent successfully via AWS SES to {to_email}"
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            self.logger.error(f"SES error {error_code}: {e}")
            raise e
        except Exception as e:
            self.logger.error(f"SES sending failed: {e}")
            raise e
    
    def _save_to_file(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save email to file as final fallback"""
        
        try:
            # Create emails directory
            email_dir = "data/emails"
            os.makedirs(email_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"email_{timestamp}.txt"
            filepath = os.path.join(email_dir, filename)
            
            # Format email content
            content = self._format_email_for_file(email_data)
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Email saved to file: {filepath}")
            
            return {
                "success": True,
                "service": "File System",
                "filepath": filepath,
                "to": email_data.get("to", "unknown"),
                "subject": email_data.get("subject", "No Subject"),
                "content": f"Email saved to {filepath} (no email service available)"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to save email to file: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"All email methods failed: {e}"
            }
    
    def _format_email_for_file(self, email_data: Dict[str, Any]) -> str:
        """Format email data for file storage"""
        
        lines = [
            "=" * 60,
            "AUTOTASKER AI EMAIL",
            "=" * 60,
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"To: {email_data.get('to', 'unknown')}",
            f"Subject: {email_data.get('subject', 'No Subject')}",
            f"Format: {email_data.get('format', 'text')}",
            "",
            "CONTENT:",
            "-" * 40,
            email_data.get('body', 'No content'),
            "",
            "=" * 60
        ]
        
        return "\n".join(lines)
    
    def send_notification(self, message: str, subject: str = None) -> Dict[str, Any]:
        """Send a simple notification email"""
        
        if not subject:
            subject = "AutoTasker AI Notification"
        
        email_data = {
            "subject": subject,
            "body": message,
            "format": "text"
        }
        
        return self.send_email(email_data)
    
    def send_error_report(self, error_details: Dict[str, Any]) -> Dict[str, Any]:
        """Send error report email"""
        
        subject = "AutoTasker AI - Error Report"
        
        body_parts = [
            "An error occurred in AutoTasker AI:",
            "",
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Error: {error_details.get('error', 'Unknown error')}",
            f"Task: {error_details.get('task', 'Unknown task')}",
            "",
            "Details:",
            str(error_details),
            "",
            "Please check the logs for more information."
        ]
        
        email_data = {
            "subject": subject,
            "body": "\n".join(body_parts),
            "format": "text"
        }
        
        return self.send_email(email_data)
    
    def send_daily_summary(self, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send formatted daily summary email"""
        
        subject = f"AutoTasker AI Daily Summary - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Format summary content
        body = self._format_daily_summary(summary_data)
        
        email_data = {
            "subject": subject,
            "body": body,
            "format": "text"
        }
        
        return self.send_email(email_data)
    
    def _format_daily_summary(self, summary_data: Dict[str, Any]) -> str:
        """Format daily summary data into email body"""
        
        lines = [
            f"AutoTasker AI Daily Summary",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "=" * 50,
        ]
        
        # Add each section
        for section, content in summary_data.items():
            if content:
                lines.extend([
                    f"\n{section.upper()}:",
                    "-" * 30,
                    str(content),
                    ""
                ])
        
        lines.extend([
            "=" * 50,
            "",
            "AutoTasker AI - Your Personal Task Automation Assistant"
        ])
        
        return "\n".join(lines)
    
    def test_email_service(self) -> Dict[str, Any]:
        """Test email service connectivity"""
        
        test_email = {
            "subject": "AutoTasker AI - Email Service Test",
            "body": f"This is a test email sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "format": "text"
        }
        
        result = self.send_email(test_email)
        
        if result.get("success"):
            self.logger.info("Email service test successful")
        else:
            self.logger.error("Email service test failed")
        
        return result
