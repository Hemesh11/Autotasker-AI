#!/usr/bin/env python3
"""
Individual Test for Gmail Agent
Tests Gmail functionality independently
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.gmail_agent import GmailAgent
from backend.utils import load_config


def test_gmail_agent():
    """Test Gmail Agent functionality - BASIC API OPERATIONS ONLY"""
    
    print("=" * 60)
    print("GMAIL AGENT INDIVIDUAL TEST - BASIC OPERATIONS")
    print("=" * 60)
    print("This test checks basic Gmail API operations.")
    print("For NATURAL LANGUAGE tests, run: test_gmail_natural_language.py")
    print("=" * 60)
    
    # Load configuration
    try:
        config = load_config("config/config.yaml")
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        # Use minimal config
        config = {
            "google": {
                "credentials_path": "google_auth/credentials.json",
                "gmail_token_path": "google_auth/gmail_token.json"
            }
        }
    
    # Check if credentials.json exists
    creds_path = "google_auth/credentials.json"
    if not os.path.exists(creds_path):
        print(f"❌ ERROR: {creds_path} not found!")
        print("📋 TO FIX:")
        print("1. Go to Google Cloud Console")
        print("2. Create project or select existing") 
        print("3. Enable Gmail API")
        print("4. Create OAuth 2.0 credentials")
        print("5. Download credentials.json")
        print("6. Save to google_auth/credentials.json")
        return False
    else:
        print(f"✓ Found credentials file: {creds_path}")
    
    # Initialize Gmail Agent
    print("\n" + "-" * 40)
    print("INITIALIZING GMAIL AGENT")
    print("-" * 40)
    
    try:
        agent = GmailAgent(config)
        print("✓ Gmail Agent initialized")
        
        # Check if authentication worked
        if agent.service:
            print("✓ Gmail authentication successful")
        else:
            print("⚠️ Gmail service not initialized (OAuth needed)")
        
    except Exception as e:
        print(f"✗ Failed to initialize Gmail Agent: {e}")
        return False
    
    # Test Cases
    test_cases = [
        {
            "name": "List Recent Emails",
            "task": {
                "parameters": {
                    "operation": "get_emails",
                    "limit": 5,
                    "filter": "unread"
                }
            }
        },
        {
            "name": "Search Emails",
            "task": {
                "parameters": {
                    "operation": "search_emails", 
                    "query": "subject:meeting",
                    "limit": 3
                }
            }
        },
        {
            "name": "Send Test Email",
            "task": {
                "parameters": {
                    "operation": "send_email",
                    "to": "your-email@gmail.com",  # Will be replaced with sender's email
                    "subject": "AutoTasker AI Test Email",
                    "body": f"This is a test email sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
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
            # For send email test, use agent's own email as recipient
            if test_case['name'] == "Send Test Email" and agent.service:
                try:
                    # Get user's email address
                    profile = agent.service.users().getProfile(userId='me').execute()
                    user_email = profile.get('emailAddress')
                    if user_email:
                        test_case['task']['parameters']['to'] = user_email
                        print(f"Sending test email to: {user_email}")
                except:
                    print("Could not get user email, using placeholder")
            
            result = agent.execute_task(test_case["task"])
            
            print(f"Success: {result.get('success', False)}")
            
            # Show content preview
            content = result.get('content', 'No content')
            if len(content) > 200:
                print(f"Content: {content[:200]}...")
            else:
                print(f"Content: {content}")
            
            if result.get('error'):
                print(f"Error: {result['error']}")
            
            # Show data summary
            if result.get('data'):
                data = result['data']
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key == 'emails' and isinstance(value, list):
                            print(f"Found {len(value)} emails")
                        elif key not in ['emails']:
                            print(f"{key}: {value}")
            
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
    
    if not os.path.exists("google_auth/gmail_token.json"):
        print("""
📋 FIRST TIME SETUP:
1. Run this test script
2. Browser will open for Google OAuth
3. Sign in to your Google account
4. Grant Gmail permissions (read & send)
5. gmail_token.json will be created automatically
6. Future runs will use saved token

🔑 WHAT HAPPENS:
- credentials.json: OAuth app configuration (you provide)
- gmail_token.json: Your access token (auto-generated)
        """)
    else:
        print("✓ gmail_token.json already exists")
        print("  - OAuth completed previously")
        print("  - Token will be refreshed automatically if needed")
    
    return successful == total


if __name__ == "__main__":
    try:
        success = test_gmail_agent()
        if success:
            print("\n🎉 All Gmail Agent tests passed!")
        else:
            print("\n⚠️ Some Gmail Agent tests failed")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
