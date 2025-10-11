#!/usr/bin/env python3
"""
Individual Test for Calendar Agent
Tests calendar functionality independently
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.calendar_agent import CalendarAgent
from backend.utils import load_config


def test_calendar_agent():
    """Test Calendar Agent functionality"""
    
    print("=" * 60)
    print("CALENDAR AGENT INDIVIDUAL TEST")
    print("=" * 60)
    
    # Load configuration
    try:
        config = load_config("config/config.yaml")
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        # Use minimal config
        config = {
            "llm": {
                "model": "gpt-4",
                "api_key": os.getenv("OPENAI_API_KEY")
            },
            "google": {
                "credentials_path": "google_auth/credentials.json",
                "calendar_token_path": "google_auth/calendar_token.json"
            }
        }
    
    # Check if credentials.json exists
    creds_path = "google_auth/credentials.json"
    if not os.path.exists(creds_path):
        print(f"❌ ERROR: {creds_path} not found!")
        print("📋 TO FIX:")
        print("1. Go to Google Cloud Console")
        print("2. Create project or select existing")
        print("3. Enable Calendar API")
        print("4. Create OAuth 2.0 credentials")
        print("5. Download credentials.json")
        print("6. Save to google_auth/credentials.json")
        return False
    else:
        print(f"✓ Found credentials file: {creds_path}")
    
    # Initialize Calendar Agent
    print("\n" + "-" * 40)
    print("INITIALIZING CALENDAR AGENT")
    print("-" * 40)
    
    try:
        agent = CalendarAgent(config)
        print("✓ Calendar Agent initialized")
        
        # Check if authentication worked
        if agent.calendar_service:
            print("✓ Google Calendar authentication successful")
        else:
            print("⚠️ Calendar service not initialized (OAuth needed)")
        
    except Exception as e:
        print(f"✗ Failed to initialize Calendar Agent: {e}")
        return False
    
    # Test Cases
    test_cases = [
        {
            "name": "Create Event - Tomorrow Meeting",
            "task": {
                "type": "create_event", 
                "description": "Team meeting tomorrow at 6 PM IST with 1 hour reminder"
            }
        },
        {
            "name": "Create Event - Specific Date",
            "task": {
                "type": "create_event",
                "description": "Doctor appointment on September 28th at 10:30 AM IST with 30 minute reminder"
            }
        },
        {
            "name": "List Upcoming Events",
            "task": {
                "type": "list_events",
                "description": "Show my upcoming calendar events"
            }
        }
    ]
    
    print("\n" + "-" * 40)
    print("RUNNING TEST CASES")
    print("-" * 40)
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}] Testing: {test_case['name']}")
        print("-" * 30)
        
        try:
            result = agent.execute_task(test_case["task"])
            
            print(f"Success: {result.get('success', False)}")
            print(f"Content: {result.get('content', 'No content')[:1000]}...")
            
            if result.get('error'):
                print(f"Error: {result['error']}")
            
            results.append({
                "test": test_case['name'],
                "success": result.get('success', False),
                "error": result.get('error')
            })
            
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append({
                "test": test_case['name'],
                "success": False,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    
    for result in results:
        status = "✓" if result['success'] else "✗"
        error_info = f" - {result.get('error', '')}" if result.get('error') else ""
        print(f"{status} {result['test']}{error_info}")
    
    # OAuth Instructions
    print("\n" + "=" * 60)
    print("OAUTH SETUP INSTRUCTIONS")
    print("=" * 60)
    
    if not os.path.exists("google_auth/calendar_token.json"):
        print("""
📋 FIRST TIME SETUP:
1. Run this test script
2. Browser will open for Google OAuth
3. Sign in to your Google account
4. Grant Calendar permissions
5. calendar_token.json will be created automatically
6. Future runs will use saved token

🔑 WHAT HAPPENS:
- credentials.json: OAuth app configuration (you provide)
- calendar_token.json: Your access token (auto-generated)
        """)
    else:
        print("✓ calendar_token.json already exists")
        print("  - OAuth completed previously")
        print("  - Token will be refreshed automatically if needed")
    
    return successful == total


if __name__ == "__main__":
    try:
        success = test_calendar_agent()
        if success:
            print("\n🎉 All Calendar Agent tests passed!")
        else:
            print("\n⚠️ Some Calendar Agent tests failed")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
