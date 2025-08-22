"""
Google Calendar Agent for AutoTasker AI
Handles calendar operations like creating events, setting reminders, etc.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
from dateutil.parser import parse as parse_date

# Add project root to Python path for direct execution
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

try:
    from backend.utils import get_openai_client
except ImportError:
    # Fallback for direct execution without backend
    def get_openai_client(config):
        try:
            from openai import OpenAI
            api_key = os.getenv('OPENAI_API_KEY') or config.get('llm', {}).get('api_key')
            if not api_key:
                raise ValueError("OpenAI API key not found")
            return OpenAI(api_key=api_key)
        except ImportError:
            return None


class CalendarAgent:
    """Agent for Google Calendar operations"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.CalendarAgent")
        self.openai_client = get_openai_client(config)
        
        self.credentials_path = config.get("google", {}).get("credentials_path", "google_auth/credentials.json")
        self.token_path = config.get("google", {}).get("calendar_token_path", "google_auth/calendar_token.json")
        
        # Calendar service will be initialized when needed
        self.calendar_service = None
        
        if not GOOGLE_AVAILABLE:
            self.logger.warning("Google Calendar libraries not available. Install google-api-python-client.")
        else:
            self._authenticate()
    
    def _authenticate(self) -> None:
        """Authenticate with Google Calendar API"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
        
        # If no valid credentials, go through OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self.logger.info("Refreshed Calendar API credentials")
                except Exception as e:
                    self.logger.error(f"Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_path):
                    self.logger.error(f"Credentials file not found: {self.credentials_path}")
                    self.logger.error("Please download credentials.json from Google Cloud Console")
                    return
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                    self.logger.info("Completed Calendar API OAuth flow")
                except Exception as e:
                    self.logger.error(f"OAuth flow failed: {e}")
                    return
            
            # Save credentials for next run
            if creds:
                os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
                self.logger.info(f"Saved credentials to {self.token_path}")
        
        # Build the service
        if creds:
            try:
                self.calendar_service = build('calendar', 'v3', credentials=creds)
                self.logger.info("Calendar service initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to build Calendar service: {e}")
        else:
            self.logger.error("No valid credentials available for Calendar API")
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a calendar-related task"""
        try:
            task_type = task.get("type", "").lower()
            description = task.get("description", "")
            
            if "create" in task_type or "add" in task_type or "schedule" in task_type:
                return self._create_event(description)
            elif "list" in task_type or "show" in task_type:
                return self._list_events(description)
            elif "delete" in task_type or "remove" in task_type:
                return self._delete_event(description)
            else:
                return self._create_event(description)  # Default to creating event
                
        except Exception as e:
            self.logger.error(f"Calendar task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"Failed to execute calendar task: {str(e)}"
            }
    
    def _create_event(self, description: str) -> Dict[str, Any]:
        """Create a calendar event based on natural language description"""
        try:
            # Parse the description to extract event details
            event_details = self._parse_event_description(description)
            
            if not GOOGLE_AVAILABLE:
                return {
                    "success": False,
                    "error": "Google Calendar API not available",
                    "content": f"Would create event: {event_details['summary']} on {event_details['start_time']}"
                }
            
            # Check if we have a valid calendar service
            if not self.calendar_service:
                return {
                    "success": False,
                    "error": "Calendar service not initialized",
                    "content": f"❌ Calendar not connected. Please set up Google Calendar OAuth.\n\nWould create: {event_details['summary']} on {event_details['start_time']}"
                }
            
            # Create the event
            event = {
                'summary': event_details['summary'],
                'description': event_details.get('description', ''),
                'start': {
                    'dateTime': event_details['start_time'],
                    'timeZone': event_details.get('timezone', 'UTC'),
                },
                'end': {
                    'dateTime': event_details['end_time'],
                    'timeZone': event_details.get('timezone', 'UTC'),
                },
            }
            
            # Add reminders if specified
            if event_details.get('reminders'):
                event['reminders'] = {
                    'useDefault': False,
                    'overrides': event_details['reminders']
                }
            
            # Create the event
            created_event = self.calendar_service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return {
                "success": True,
                "content": f"✅ Calendar event created successfully!\n\n"
                          f"📅 Event: {event_details['summary']}\n"
                          f"🕐 Date/Time: {event_details['start_time']}\n"
                          f"🔔 Reminders: {len(event_details.get('reminders', []))} set\n"
                          f"🔗 Event ID: {created_event.get('id')}",
                "data": {
                    "event_id": created_event.get('id'),
                    "event_link": created_event.get('htmlLink'),
                    "event_details": event_details
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create calendar event: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"❌ Failed to create calendar event: {str(e)}"
            }
    
    def _parse_event_description(self, description: str) -> Dict[str, Any]:
        """Parse natural language description to extract event details"""
        try:
            # Use OpenAI to parse the natural language description
            prompt = f"""
            Parse this calendar event request and extract the details in JSON format:
            "{description}"
            
            Extract and return a JSON object with these fields:
            - summary: Event title/name
            - description: Additional event details
            - start_time: ISO format datetime (e.g., "2025-08-13T09:00:00")
            - end_time: ISO format datetime (default to 1 hour after start)
            - timezone: timezone (default to "UTC")
            - reminders: array of reminder objects like [{{"method": "popup", "minutes": 15}}]
            
            For dates, assume current year 2025 if not specified. For times, use 24-hour format.
            If reminder is mentioned, add appropriate reminders.
            
            Return only the JSON object, no other text.
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.config.get('llm', {}).get('model', 'gpt-4'),
                messages=[
                    {"role": "system", "content": "You are a calendar event parser. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            event_json = response.choices[0].message.content.strip()
            event_details = json.loads(event_json)
            
            # Validate and set defaults
            if not event_details.get('summary'):
                event_details['summary'] = "AutoTasker AI Event"
            
            if not event_details.get('start_time'):
                # Default to tomorrow at 9 AM
                tomorrow = datetime.now() + timedelta(days=1)
                event_details['start_time'] = tomorrow.replace(hour=9, minute=0, second=0).isoformat()
            
            if not event_details.get('end_time'):
                # Default to 1 hour after start
                start_dt = parse_date(event_details['start_time'])
                end_dt = start_dt + timedelta(hours=1)
                event_details['end_time'] = end_dt.isoformat()
            
            # Add default reminder if not specified
            if not event_details.get('reminders'):
                event_details['reminders'] = [
                    {"method": "popup", "minutes": 15}
                ]
            
            return event_details
            
        except Exception as e:
            self.logger.error(f"Failed to parse event description: {e}")
            # Fallback parsing
            return {
                "summary": f"Meeting: {description[:50]}...",
                "description": description,
                "start_time": (datetime.now() + timedelta(days=1)).replace(hour=9, minute=0, second=0).isoformat(),
                "end_time": (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0).isoformat(),
                "timezone": "UTC",
                "reminders": [{"method": "popup", "minutes": 15}]
            }
    
    def _list_events(self, description: str) -> Dict[str, Any]:
        """List upcoming calendar events"""
        try:
            if not GOOGLE_AVAILABLE:
                return {
                    "success": False,
                    "error": "Google Calendar API not available",
                    "content": "Cannot list events - Google Calendar API not available"
                }
            
            if not self.calendar_service:
                return {
                    "success": False,
                    "error": "Calendar service not initialized",
                    "content": "❌ Calendar not connected. Please set up Google Calendar OAuth."
                }
            
            # Get events from now to next 30 days
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                return {
                    "success": True,
                    "content": "📅 No upcoming events found."
                }
            
            event_list = ["📅 Upcoming Calendar Events:\n"]
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                event_list.append(f"• {event['summary']} - {start}")
            
            return {
                "success": True,
                "content": "\n".join(event_list),
                "data": {"events": events}
            }
            
        except Exception as e:
            self.logger.error(f"Failed to list calendar events: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"❌ Failed to list calendar events: {str(e)}"
            }
    
    def _delete_event(self, description: str) -> Dict[str, Any]:
        """Delete a calendar event"""
        # This would need more sophisticated parsing to identify which event to delete
        return {
            "success": False,
            "error": "Event deletion not implemented yet",
            "content": "Event deletion feature coming soon!"
        }


# Example usage
if __name__ == "__main__":
    config = {
        "llm": {"model": "gpt-4"},
        "google": {
            "credentials_path": "google_auth/credentials.json",
            "calendar_token_path": "google_auth/calendar_token.json"
        }
    }
    
    agent = CalendarAgent(config)
    
    # Test event creation
    task = {
        "type": "create_event",
        "description": "mark a meeting in google calendar on 13th august 9 am, give reminder"
    }
    
    result = agent.execute_task(task)
    print(f"Result: {result}")
