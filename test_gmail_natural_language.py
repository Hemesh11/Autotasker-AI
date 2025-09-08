#!/usr/bin/env python3
"""
Natural Language Gmail Test
Tests Gmail Agent with natural language prompts through the Planner Agent
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.gmail_agent import GmailAgent
from agents.planner_agent import PlannerAgent
from backend.utils import load_config


def test_natural_language_gmail():
    """Test Gmail with natural language prompts"""
    
    print("=" * 70)
    print("GMAIL AGENT - NATURAL LANGUAGE TEST")
    print("=" * 70)
    
    # Load configuration
    try:
        config = load_config("config/config.yaml")
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        return False
    
    # Initialize agents
    try:
        gmail_agent = GmailAgent(config)
        planner_agent = PlannerAgent(config)
        print("✓ Agents initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize agents: {e}")
        return False
    
    # Natural Language Test Cases
    natural_language_prompts = [
        {
            "prompt": "Send an email to myself with the subject 'AutoTasker Test' and tell them about this awesome AI system",
            "expected_operations": ["send_email"]
        },
        {
            "prompt": "Check my recent emails and tell me if there are any important ones from work",
            "expected_operations": ["get_emails", "summarize"]
        },
        {
            "prompt": "Send a professional email to myself explaining what AutoTasker AI can do",
            "expected_operations": ["send_email"]
        }
    ]
    
    print("\n" + "-" * 50)
    print("TESTING NATURAL LANGUAGE PROMPTS")
    print("-" * 50)
    
    results = []
    
    for i, test_case in enumerate(natural_language_prompts, 1):
        print(f"\n[{i}] Natural Language Prompt:")
        print(f"'{test_case['prompt']}'")
        print("-" * 30)
        
        try:
            # Step 1: Convert natural language to task plan
            print("Step 1: Converting to task plan...")
            task_plan = planner_agent.create_task_plan(test_case['prompt'])
            
            if not task_plan.get('success', True):
                print(f"✗ Planning failed: {task_plan.get('error', 'Unknown error')}")
                results.append({
                    "prompt": test_case['prompt'],
                    "success": False,
                    "error": "Planning failed"
                })
                continue
            
            print(f"✓ Created plan with {len(task_plan.get('tasks', []))} tasks")
            print(f"Intent: {task_plan.get('intent', 'N/A')}")
            
            # Step 2: Execute Gmail-related tasks
            gmail_tasks = [task for task in task_plan.get('tasks', []) 
                          if task.get('type') == 'gmail']
            
            if not gmail_tasks:
                print("⚠️ No Gmail tasks found in plan")
                results.append({
                    "prompt": test_case['prompt'],
                    "success": False,
                    "error": "No Gmail tasks generated"
                })
                continue
            
            print(f"Step 2: Executing {len(gmail_tasks)} Gmail tasks...")
            
            gmail_results = []
            for task in gmail_tasks:
                print(f"  Executing: {task.get('description', 'N/A')}")
                
                # Convert planner task to Gmail agent format
                gmail_task = {
                    "description": task.get('description', ''),
                    "parameters": task.get('parameters', {})
                }
                
                # For send email tasks, enhance the content
                if 'send' in task.get('description', '').lower():
                    params = gmail_task['parameters']
                    if 'to' not in params:
                        # Get user's email for testing
                        try:
                            profile = gmail_agent.service.users().getProfile(userId='me').execute()
                            params['to'] = profile.get('emailAddress')
                        except:
                            params['to'] = 'test@example.com'
                    
                    # Enhance email content based on prompt
                    if 'autotasker' in test_case['prompt'].lower():
                        params['subject'] = params.get('subject', 'AutoTasker AI Demo')
                        params['body'] = params.get('body', 
                            f"""Hello!

This email was sent by AutoTasker AI, a smart workflow automation system.

AutoTasker AI can:
- 📧 Process and send emails automatically
- 📅 Manage calendar events and reminders  
- 🔍 Analyze GitHub repositories and code
- 💻 Generate coding questions and study materials
- 📊 Summarize content and data
- 🤖 Handle complex multi-step workflows

This email was generated from the natural language prompt:
"{test_case['prompt']}"

Sent automatically at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Best regards,
AutoTasker AI 🤖
""")
                
                result = gmail_agent.execute_task(gmail_task)
                gmail_results.append(result)
                
                if result.get('success'):
                    print(f"  ✓ Task completed successfully")
                    if 'send' in task.get('description', '').lower():
                        print(f"    Email sent to: {result.get('to', 'Unknown')}")
                        print(f"    Subject: {result.get('subject', 'N/A')}")
                else:
                    print(f"  ✗ Task failed: {result.get('error', 'Unknown error')}")
            
            # Check overall success
            all_success = all(r.get('success', False) for r in gmail_results)
            
            results.append({
                "prompt": test_case['prompt'],
                "success": all_success,
                "tasks_executed": len(gmail_tasks),
                "results": gmail_results
            })
            
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append({
                "prompt": test_case['prompt'],
                "success": False,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "=" * 70)
    print("NATURAL LANGUAGE TEST SUMMARY")
    print("=" * 70)
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"Total Prompts Tested: {total}")
    print(f"Successfully Processed: {successful}")
    print(f"Failed: {total - successful}")
    
    for i, result in enumerate(results, 1):
        status = "✓" if result['success'] else "✗"
        prompt_preview = result['prompt'][:50] + "..." if len(result['prompt']) > 50 else result['prompt']
        print(f"\n{status} [{i}] {prompt_preview}")
        
        if result.get('tasks_executed'):
            print(f"    Tasks executed: {result['tasks_executed']}")
        
        if result.get('error'):
            print(f"    Error: {result['error']}")
    
    print("\n" + "=" * 70)
    print("WHAT THIS TEST SHOWS")
    print("=" * 70)
    print("""
✅ Natural Language Processing:
   - Converts plain English to structured tasks
   - Understands email sending intentions
   - Plans multi-step workflows

📧 Gmail Operations:
   - Send emails with custom content
   - Fetch and filter emails
   - Handle authentication automatically

🤖 AI Integration:
   - Uses LLM (OpenAI/OpenRouter) for planning
   - Generates appropriate email content
   - Handles context and intent understanding

🔗 Multi-Agent Workflow:
   - Planner Agent converts language to tasks
   - Gmail Agent executes email operations
   - Seamless integration between agents
    """)
    
    return successful == total


if __name__ == "__main__":
    try:
        success = test_natural_language_gmail()
        if success:
            print("\n🎉 All natural language Gmail tests passed!")
            print("AutoTasker AI can handle complex email requests! 🚀")
        else:
            print("\n⚠️ Some natural language Gmail tests failed")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
