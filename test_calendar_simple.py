#!/usr/bin/env python3
"""
Simple standalone test for Calendar Agent without backend dependencies.
"""

import os
import sys
import json
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_calendar_agent():
    """Test calendar agent with simple configuration."""
    
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
    if os.path.exists(config_path):
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        config = {
            'google': {
                'credentials_file': 'google_auth/credentials.json',
                'calendar_token_file': 'google_auth/calendar_token.json'
            }
        }
    
    # Import calendar agent
    from agents.calendar_agent import CalendarAgent
    
    # Create agent instance
    agent = CalendarAgent(config)
    
    # Test 1: Create a simple event
    print("Test 1: Creating a simple event...")
    task = {
        'title': 'Test Meeting',
        'description': 'This is a test event created by AutoTasker AI',
        'start_time': (datetime.now() + timedelta(hours=1)).isoformat(),
        'end_time': (datetime.now() + timedelta(hours=2)).isoformat(),
        'attendees': []
    }
    
    try:
        result = agent.execute_task(task)
        print(f"Result: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            print("✅ Event created successfully!")
            print(f"Event ID: {result.get('event_id')}")
            print(f"Event Link: {result.get('event_link')}")
        else:
            print(f"❌ Failed to create event: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
    
    # Test 2: Natural language event creation
    print("\nTest 2: Natural language event creation...")
    nl_task = {
        'prompt': 'Schedule a team standup meeting tomorrow at 9 AM for 30 minutes'
    }
    
    try:
        result = agent.execute_task(nl_task)
        print(f"Result: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            print("✅ Natural language event created successfully!")
        else:
            print(f"❌ Failed to create event: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error during natural language test: {str(e)}")

if __name__ == '__main__':
    from datetime import timedelta
    
    print("🗓️  AutoTasker AI - Calendar Agent Test")
    print("=" * 50)
    
    # Check if Google Calendar libraries are available
    try:
        from google.oauth2.credentials import Credentials
        print("✅ Google Calendar libraries are available")
    except ImportError:
        print("❌ Google Calendar libraries not found. Please install:")
        print("pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        sys.exit(1)
    
    # Check if credentials file exists
    creds_path = os.path.join(os.path.dirname(__file__), 'google_auth', 'credentials.json')
    if not os.path.exists(creds_path):
        print(f"❌ Credentials file not found at: {creds_path}")
        print("Please follow the setup instructions in docs/GOOGLE_CALENDAR_SETUP.md")
        sys.exit(1)
    
    print("✅ Starting calendar agent tests...")
    test_calendar_agent()
    print("\n🎉 Calendar agent tests completed!")
