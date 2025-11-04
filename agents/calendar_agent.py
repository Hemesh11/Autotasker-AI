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

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv("config/.env")
except ImportError:
    # Try loading without dotenv
    env_path = "config/.env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"')

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
            
            # Get LLM configuration
            llm_config = config.get('llm', {})
            provider = llm_config.get('provider', 'openai')
            
            if provider == 'openrouter':
                # Use OpenRouter API
                api_key = os.getenv('OPENROUTER_API_KEY')
                if not api_key:
                    raise ValueError("OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable.")
                return OpenAI(
                    api_key=api_key,
                    base_url="https://openrouter.ai/api/v1"
                )
            else:
                # Use OpenAI API
                api_key = os.getenv('OPENAI_API_KEY') or llm_config.get('api_key')
                if not api_key:
                    raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
                return OpenAI(api_key=api_key)
                
        except ImportError:
            return None
        except Exception as e:
            print(f"Warning: Failed to initialize LLM client: {e}")
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
        
        # Get user's timezone from config or environment, default to Asia/Kolkata (IST)
        self.user_timezone = config.get("timezone", os.getenv("TIMEZONE", "Asia/Kolkata"))
        self.logger.info(f"Using timezone: {self.user_timezone}")
        
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
            description = task.get("description", "").lower()
            parameters = task.get("parameters", {})
            
            # Detect if this is a LIST/FETCH operation (not CREATE)
            list_keywords = ["what's on", "show", "list", "get", "fetch", "view", "see", "display", "check"]
            is_list_operation = any(keyword in description for keyword in list_keywords)
            
            # Detect if this is explicitly a CREATE operation
            create_keywords = ["schedule", "create", "add", "book", "set up", "make"]
            is_create_operation = any(keyword in description for keyword in create_keywords)
            
            # If asking about existing events (list), don't create
            if is_list_operation and not is_create_operation:
                self.logger.info(f"Detected LIST operation from description: {description}")
                return self._list_events(task.get("description", ""))
            
            # Check if we have pre-parsed parameters from the planner (for CREATE)
            if parameters.get("start_time") and parameters.get("end_time"):
                # Use parameters directly instead of re-parsing
                self.logger.info(f"Using pre-parsed calendar parameters from planner")
                return self._create_event_from_parameters(parameters)
            
            # Fallback to type-based detection
            if "list" in task_type or "show" in task_type or "fetch" in task_type or "get" in task_type:
                return self._list_events(task.get("description", ""))
            elif "delete" in task_type or "remove" in task_type:
                return self._delete_event(task.get("description", ""))
            elif "create" in task_type or "add" in task_type or "schedule" in task_type:
                return self._create_event(task.get("description", ""))
            else:
                # Default: if description suggests listing, list; otherwise create
                if is_list_operation:
                    return self._list_events(task.get("description", ""))
                else:
                    return self._create_event(task.get("description", ""))
                
        except Exception as e:
            self.logger.error(f"Calendar task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"Failed to execute calendar task: {str(e)}"
            }
    
    def _create_event_from_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a calendar event from pre-parsed parameters (from planner)"""
        try:
            # Extract parameters
            summary = parameters.get("summary", "Meeting")
            description = parameters.get("description", "")
            start_time = parameters.get("start_time")
            end_time = parameters.get("end_time")
            reminders = parameters.get("reminders", [{"method": "popup", "minutes": 15}])
            
            # Validate required fields
            if not start_time or not end_time:
                raise ValueError("Missing start_time or end_time in parameters")
            
            # Clean timezone suffixes if present
            import re
            if isinstance(start_time, str):
                start_time = start_time.replace('Z', '')
                start_time = re.sub(r'[+-]\d{2}:\d{2}$', '', start_time)
                start_time = re.sub(r'[+-]\d{4}$', '', start_time)
            
            if isinstance(end_time, str):
                end_time = end_time.replace('Z', '')
                end_time = re.sub(r'[+-]\d{2}:\d{2}$', '', end_time)
                end_time = re.sub(r'[+-]\d{4}$', '', end_time)
            
            self.logger.info(f"Creating event: {summary} at {start_time} (timezone: {self.user_timezone})")
            
            if not GOOGLE_AVAILABLE:
                return {
                    "success": False,
                    "error": "Google Calendar API not available",
                    "content": f"Would create event: {summary} on {start_time}"
                }
            
            # Check if we have a valid calendar service
            if not self.calendar_service:
                return {
                    "success": False,
                    "error": "Calendar service not initialized",
                    "content": f"❌ Calendar not connected. Please set up Google Calendar OAuth.\n\nWould create: {summary} on {start_time}"
                }
            
            # Create the event
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time,
                    'timeZone': self.user_timezone,
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': self.user_timezone,
                },
            }
            
            # Add reminders
            if reminders:
                event['reminders'] = {
                    'useDefault': False,
                    'overrides': reminders
                }
            
            # Create the event
            created_event = self.calendar_service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return {
                "success": True,
                "content": f"✅ Calendar event created successfully!\n\n"
                          f"📅 Event: {summary}\n"
                          f"🕐 Date/Time: {start_time}\n"
                          f"🔔 Reminders: {len(reminders)} set\n"
                          f"🔗 Event ID: {created_event.get('id')}",
                "data": {
                    "event_id": created_event.get('id'),
                    "event_link": created_event.get('htmlLink'),
                    "event_details": {
                        "summary": summary,
                        "description": description,
                        "start_time": start_time,
                        "end_time": end_time,
                        "reminders": reminders
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create calendar event from parameters: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"❌ Failed to create calendar event: {str(e)}"
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
                    'timeZone': self.user_timezone,  # Use user's timezone
                },
                'end': {
                    'dateTime': event_details['end_time'],
                    'timeZone': self.user_timezone,  # Use user's timezone
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
            # Get current date for context (in user's timezone)
            from datetime import timezone
            import pytz
            
            # Get user's timezone
            try:
                user_tz = pytz.timezone(self.user_timezone)
                current_time = datetime.now(user_tz)
            except:
                # Fallback to UTC if timezone is invalid
                current_time = datetime.now()
            
            current_date = current_time.strftime("%Y-%m-%d")
            current_day = current_time.strftime("%A, %B %d, %Y")
            
            # Use OpenAI to parse the natural language description
            prompt = f"""You are a calendar event parser. Parse the following request into a JSON object.

TODAY'S DATE: {current_date} ({current_day})
USER REQUEST: "{description}"

STEP-BY-STEP PARSING INSTRUCTIONS:

1. EXTRACT DATE:
   - Look for explicit dates like "November 7th", "Nov 8", "2025-11-08"
   - Convert month names to numbers: January=01, February=02, ..., November=11, December=12
   - If "tomorrow", use {(current_time + timedelta(days=1)).strftime("%Y-%m-%d")}
   - Format as: YYYY-MM-DD

2. EXTRACT TIME:
   - Look for times like "5:30 am", "2pm", "14:00"
   - Convert to 24-hour format: 1am=01:00, 2pm=14:00, 5:30am=05:30, 5:30pm=17:30
   - Format as: HH:MM:SS (always include :00 for seconds)

3. CALCULATE END TIME:
   - If duration mentioned (e.g., "40 minutes", "1 hour"), add to start time
   - If no duration, default to 1 hour after start
   - Format as: YYYY-MM-DDTHH:MM:SS

4. BUILD DATETIME STRINGS:
   - Combine date and time: YYYY-MM-DDTHH:MM:SS
   - Example: Date "2025-11-07" + Time "05:30:00" = "2025-11-07T05:30:00"
   - DO NOT add any timezone suffix (no Z, no +00:00, no +05:30)

REQUIRED JSON FORMAT:
{{
    "summary": "Meeting title from description or default to 'Meeting'",
    "description": "Additional details if any",
    "start_time": "YYYY-MM-DDTHH:MM:SS",
    "end_time": "YYYY-MM-DDTHH:MM:SS",
    "reminders": [{{"method": "popup", "minutes": 15}}]
}}

EXAMPLE - Input: "Schedule meeting on November 7th at 5:30 am for 40 minutes"
CORRECT OUTPUT:
{{
    "summary": "Meeting",
    "description": "",
    "start_time": "2025-11-07T05:30:00",
    "end_time": "2025-11-07T06:10:00",
    "reminders": [{{"method": "popup", "minutes": 15}}]
}}

Now parse the user request and return ONLY the JSON object (no explanation, no markdown)."""
            
            # Get the appropriate model
            llm_config = self.config.get('llm', {})
            model = llm_config.get('model', 'gpt-4')
            
            # If no OpenAI client available, skip AI parsing
            if not self.openai_client:
                self.logger.warning("No LLM client available, using fallback parsing")
                raise Exception("LLM client not available")
            
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a precise calendar event parser. You MUST follow the date and time from the user's request exactly. Parse dates and times literally - do not make assumptions or change them. Return only valid JSON with no markdown formatting."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0  # Use 0.0 for maximum consistency
            )
            
            event_json = response.choices[0].message.content.strip()
            
            # Log the raw LLM response for debugging
            self.logger.info(f"LLM parsed event: {event_json[:200]}...")
            
            # Clean markdown code blocks if present
            if event_json.startswith('```json'):
                event_json = event_json.replace('```json', '').replace('```', '').strip()
            elif event_json.startswith('```'):
                event_json = event_json.replace('```', '').strip()
            
            event_details = json.loads(event_json)
            
            # Log parsed details
            self.logger.info(f"Parsed start_time: {event_details.get('start_time')}, end_time: {event_details.get('end_time')}")
            
            # Validate and set defaults
            if not event_details.get('summary'):
                event_details['summary'] = "AutoTasker AI Event"
            
            # Validate start_time format
            if not event_details.get('start_time'):
                # Default to tomorrow at 9 AM in user's timezone
                try:
                    import pytz
                    user_tz = pytz.timezone(self.user_timezone)
                    tomorrow = datetime.now(user_tz) + timedelta(days=1)
                    event_details['start_time'] = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S")
                except:
                    tomorrow = datetime.now() + timedelta(days=1)
                    event_details['start_time'] = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0).isoformat()
            else:
                # Validate that start_time is a proper ISO datetime
                start_time = str(event_details['start_time'])
                if 'T' not in start_time or len(start_time) < 19:
                    # Malformed datetime - try to fix it
                    self.logger.warning(f"Malformed start_time received: {start_time}")
                    # If it's just a date, add default time
                    if len(start_time) == 10 and start_time.count('-') == 2:
                        start_time = f"{start_time}T14:00:00"
                    else:
                        # Can't fix it, use default
                        try:
                            import pytz
                            user_tz = pytz.timezone(self.user_timezone)
                            tomorrow = datetime.now(user_tz) + timedelta(days=1)
                            start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S")
                        except:
                            tomorrow = datetime.now() + timedelta(days=1)
                            start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0).isoformat()
                    
                    event_details['start_time'] = start_time
            
            # Ensure start_time doesn't have timezone suffix and is properly formatted
            if 'start_time' in event_details and isinstance(event_details['start_time'], str):
                start_time = event_details['start_time']
                
                # Remove 'Z' suffix (UTC indicator)
                if start_time.endswith('Z'):
                    start_time = start_time[:-1]
                
                # Remove timezone offset like +05:30 or -05:00 (but ONLY from end of string)
                # Use regex to safely remove timezone offset without affecting date/time parts
                import re
                # Pattern: optional +/- followed by HH:MM or HHMM at the END of string
                start_time = re.sub(r'[+-]\d{2}:\d{2}$', '', start_time)  # Remove +05:30 or -05:00
                start_time = re.sub(r'[+-]\d{4}$', '', start_time)        # Remove +0530 or -0500
                
                event_details['start_time'] = start_time
            
            if not event_details.get('end_time'):
                # Default to 1 hour after start
                start_dt = parse_date(event_details['start_time'])
                end_dt = start_dt + timedelta(hours=1)
                event_details['end_time'] = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
            
            # Ensure end_time doesn't have timezone suffix and is properly formatted
            if 'end_time' in event_details and isinstance(event_details['end_time'], str):
                end_time = event_details['end_time']
                
                # Remove 'Z' suffix (UTC indicator)
                if end_time.endswith('Z'):
                    end_time = end_time[:-1]
                
                # Remove timezone offset like +05:30 or -05:00 (but ONLY from end of string)
                # Use regex to safely remove timezone offset without affecting date/time parts
                import re
                # Pattern: optional +/- followed by HH:MM or HHMM at the END of string
                end_time = re.sub(r'[+-]\d{2}:\d{2}$', '', end_time)  # Remove +05:30 or -05:00
                end_time = re.sub(r'[+-]\d{4}$', '', end_time)        # Remove +0530 or -0500
                
                event_details['end_time'] = end_time
            
            # Add default reminder if not specified
            if not event_details.get('reminders'):
                event_details['reminders'] = [
                    {"method": "popup", "minutes": 15}
                ]
            
            return event_details
            
        except Exception as e:
            self.logger.error(f"Failed to parse event description: {e}")
            # Fallback parsing - use user's timezone
            try:
                import pytz
                user_tz = pytz.timezone(self.user_timezone)
                tomorrow = datetime.now(user_tz) + timedelta(days=1)
                start_time = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S")
                end_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S")
            except:
                tomorrow = datetime.now() + timedelta(days=1)
                start_time = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S")
                end_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S")
            
            return {
                "summary": f"Meeting: {description[:50]}...",
                "description": description,
                "start_time": start_time,
                "end_time": end_time,
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
