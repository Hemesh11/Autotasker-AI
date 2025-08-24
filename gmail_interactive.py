#!/usr/bin/env python3
"""
Interactive Gmail Script
Simple script to send emails to anyone about anything
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.gmail_agent import GmailAgent
from backend.utils import load_config
from backend.llm_factory import create_llm_client, get_chat_completion


def send_email_interactive():
    """Interactive email sending"""
    
    print("=" * 60)
    print("GMAIL INTERACTIVE - SEND EMAIL TO ANYONE")
    print("=" * 60)
    
    # Initialize Gmail Agent and LLM
    try:
        config = load_config("config/config.yaml")
        gmail_agent = GmailAgent(config)
        llm_client = create_llm_client(config)
        print("✓ Gmail and LLM ready!\n")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    while True:
        print("\nWhat do you want to do?")
        print("1. Send email to someone")
        print("2. Search my emails") 
        print("3. Get recent emails")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            # Send email
            print("\n" + "-" * 40)
            print("SEND EMAIL")
            print("-" * 40)
            
            to_email = input("Send to (email address): ").strip()
            if not to_email or "@" not in to_email:
                print("❌ Invalid email address!")
                continue
            
            subject = input("Subject: ").strip()
            if not subject:
                subject = "Message from AutoTasker AI"
            
            print("\nWhat should the email be about?")
            topic = input("Topic/Content: ").strip()
            if not topic:
                print("❌ Please provide some content!")
                continue
            
            # Generate email content using LLM
            print("🤖 Generating email content with AI...")
            
            try:
                prompt = f"""Write a professional and informative email about: {topic}

The email should be:
- Well-structured and engaging
- Informative with relevant details
- Professional but friendly tone
- About 150-200 words
- Include specific information about the topic

Topic: {topic}

Write the email body (without greeting and signature):"""

                body_content = get_chat_completion(
                    client=llm_client,
                    messages=[
                        {"role": "system", "content": "You are a professional email writer. Write clear, informative, and engaging email content."},
                        {"role": "user", "content": prompt}
                    ],
                    model=config.get("llm", {}).get("model", "gpt-3.5-turbo"),
                    temperature=0.7,
                    max_tokens=400
                )
                
                # Create final email body
                body = f"""Hi!

{body_content.strip()}

This email was sent using AutoTasker AI at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.

Best regards!
"""
                
                print("✅ AI content generated!")
                
            except Exception as e:
                print(f"⚠️ LLM failed ({e}), using basic content...")
                body = f"""Hi!

I wanted to share some information about: {topic}

{topic}

This email was sent using AutoTasker AI at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.

Best regards!
"""
            
            print(f"\n📧 Sending email...")
            print(f"   To: {to_email}")
            print(f"   Subject: {subject}")
            
            # Send the email
            result = gmail_agent.execute_task({
                "parameters": {
                    "operation": "send_email",
                    "to": to_email,
                    "subject": subject,
                    "body": body
                }
            })
            
            if result.get('success'):
                print("✅ Email sent successfully!")
                print(f"   Message ID: {result.get('message_id', 'N/A')}")
            else:
                print(f"❌ Failed to send email: {result.get('error', 'Unknown error')}")
        
        elif choice == "2":
            # Search emails
            print("\n" + "-" * 40)
            print("SEARCH EMAILS")
            print("-" * 40)
            
            query = input("Search for: ").strip()
            if not query:
                print("❌ Please provide search terms!")
                continue
            
            print(f"🔍 Searching for: {query}")
            
            result = gmail_agent.execute_task({
                "parameters": {
                    "operation": "search_emails",
                    "query": query,
                    "limit": 5
                }
            })
            
            if result.get('success'):
                emails = result.get('data', {}).get('emails', [])
                if emails:
                    print(f"✅ Found {len(emails)} emails:")
                    for i, email in enumerate(emails, 1):
                        if email:
                            print(f"\n[{i}] From: {email.get('from', 'Unknown')}")
                            print(f"    Subject: {email.get('subject', 'No Subject')}")
                            print(f"    Date: {email.get('date', 'Unknown')}")
                            if email.get('snippet'):
                                print(f"    Preview: {email['snippet'][:100]}...")
                else:
                    print("❌ No emails found!")
            else:
                print(f"❌ Search failed: {result.get('error', 'Unknown error')}")
        
        elif choice == "3":
            # Get recent emails
            print("\n" + "-" * 40)
            print("RECENT EMAILS")
            print("-" * 40)
            
            limit = input("How many emails? (default 10): ").strip()
            try:
                limit = int(limit) if limit else 10
                limit = min(limit, 20)  # Max 20
            except:
                limit = 10
            
            print(f"📬 Getting {limit} recent emails...")
            
            result = gmail_agent.execute_task({
                "parameters": {
                    "operation": "get_emails",
                    "limit": limit
                }
            })
            
            if result.get('success'):
                print("✅ Recent emails:")
                print(result.get('content', 'No content'))
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        elif choice == "4":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice! Please enter 1-4.")


if __name__ == "__main__":
    try:
        send_email_interactive()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
