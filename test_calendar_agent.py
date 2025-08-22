"""
Standalone test script for Calendar Agent
Tests calendar functionality without backend dependencies
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dateutil.parser import parse as parse_date
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False
    print("⚠️ python-dateutil not installed. Install with: pip install python-dateutil")

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("⚠️ Google API libraries not installed. Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI library not installed. Install with: pip install openai")


def get_simple_openai_client():
    """Simple OpenAI client for testing"""
    if not OPENAI_AVAILABLE:
        return None
    
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("⚠️ OPENAI_API_KEY not set in environment variables")
        return None
    
    return openai.OpenAI(api_key=api_key)


class SimpleCalendarAgent:
    """Simplified Calendar Agent for testing"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
        self.openai_client = get_simple_openai_client()
        self.credentials_path = "google_auth/credentials.json"
        self.token_path = "google_auth/calendar_token.json"
        self.calendar_service = None
        
        if GOOGLE_AVAILABLE:
            self._authenticate()
    
    def _authenticate(self):
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
                    print("✅ Refreshed Calendar API credentials")
                except Exception as e:
                    print(f"❌ Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_path):
                    print(f"❌ Credentials file not found: {self.credentials_path}")
                    print("Please download credentials.json from Google Cloud Console")
                    return
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                    print("✅ Completed Calendar API OAuth flow")
                except Exception as e:
                    print(f"❌ OAuth flow failed: {e}")
                    return
            
            # Save credentials for next run
            if creds:
                os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
                print(f"✅ Saved credentials to {self.token_path}")
        
        # Build the service
        if creds:
            try:
                self.calendar_service = build('calendar', 'v3', credentials=creds)
                print("✅ Calendar service initialized successfully")
            except Exception as e:
                print(f"❌ Failed to build Calendar service: {e}")
    
    def parse_simple_event(self, description: str) -> Dict[str, Any]:
        """Simple event parsing without OpenAI"""
        # Basic parsing for testing
        if "13th august" in description.lower() or "august 13" in description.lower():
            start_time = "2025-08-13T09:00:00"
            end_time = "2025-08-13T10:00:00"
        else:
            # Default to tomorrow
            tomorrow = datetime.now() + timedelta(days=1)
            start_time = tomorrow.replace(hour=9, minute=0, second=0).isoformat()
            end_time = tomorrow.replace(hour=10, minute=0, second=0).isoformat()
        
        return {
            "summary": "Test Meeting",
            "description": description,
            "start_time": start_time,
            "end_time": end_time,
            "timezone": "UTC",
            "reminders": [{"method": "popup", "minutes": 15}]
        }
    
    def parse_with_openai(self, description: str) -> Dict[str, Any]:
        """Parse with OpenAI if available"""
        if not self.openai_client:
            print("🔄 Using simple parsing (OpenAI not available)")
            return self.parse_simple_event(description)
        
        try:
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
                model='gpt-4',
                messages=[
                    {"role": "system", "content": "You are a calendar event parser. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            event_json = response.choices[0].message.content.strip()
            event_details = json.loads(event_json)
            print("✅ Used OpenAI to parse event")
            return event_details
            
        except Exception as e:
            print(f"❌ OpenAI parsing failed: {e}, using simple parsing")
            return self.parse_simple_event(description)
    
    def test_create_event(self, description: str):
        """Test creating a calendar event"""
        print(f"\n🧪 Testing Calendar Event Creation...")
        print(f"📝 Description: {description}")
        
        # Parse the event
        event_details = self.parse_with_openai(description)
        print(f"📅 Parsed Event: {event_details['summary']}")
        print(f"🕐 Time: {event_details['start_time']}")
        
        if not GOOGLE_AVAILABLE:
            print("❌ Google libraries not available - would create event with these details")
            return event_details
        
        if not self.calendar_service:
            print("❌ Calendar service not initialized - check OAuth setup")
            return event_details
        
        try:
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
                'reminders': {
                    'useDefault': False,
                    'overrides': event_details.get('reminders', [])
                }
            }
            
            created_event = self.calendar_service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            print("✅ Calendar event created successfully!")
            print(f"🔗 Event ID: {created_event.get('id')}")
            print(f"🌐 Event Link: {created_event.get('htmlLink')}")
            
            return created_event
            
        except Exception as e:
            print(f"❌ Failed to create calendar event: {e}")
            return None
    
    def test_list_events(self):
        """Test listing calendar events"""
        print(f"\n🧪 Testing Calendar Event List...")
        
        if not GOOGLE_AVAILABLE:
            print("❌ Google libraries not available")
            return []
        
        if not self.calendar_service:
            print("❌ Calendar service not initialized")
            return []
        
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=5,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                print("📅 No upcoming events found")
                return []
            
            print("📅 Upcoming events:")
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"  • {event['summary']} - {start}")
            
            return events
            
        except Exception as e:
            print(f"❌ Failed to list events: {e}")
            return []


def main():
    """Test the calendar agent"""
    print("🚀 AutoTasker AI - Calendar Agent Test")
    print("=" * 50)
    
    # Check dependencies
    print("📦 Checking dependencies...")
    if not DATEUTIL_AVAILABLE:
        print("❌ Missing: python-dateutil")
    if not GOOGLE_AVAILABLE:
        print("❌ Missing: Google API libraries")
    if not OPENAI_AVAILABLE:
        print("❌ Missing: OpenAI library")
    
    # Create agent
    agent = SimpleCalendarAgent()
    
    # Test 1: Event parsing
    print("\n" + "="*50)
    test_description = "mark a meeting in google calendar on 13th august 9 am, give reminder"
    agent.test_create_event(test_description)
    
    # Test 2: List events
    print("\n" + "="*50)
    agent.test_list_events()
    
    print("\n" + "="*50)
    print("🎉 Calendar Agent Test Complete!")
    
    if not GOOGLE_AVAILABLE:
        print("\n💡 To enable actual calendar creation:")
        print("   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    
    if not OPENAI_AVAILABLE:
        print("\n💡 To enable smart parsing:")
        print("   pip install openai")
        print("   set OPENAI_API_KEY=your_key")


if __name__ == "__main__":
    main()
