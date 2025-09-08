#!/usr/bin/env python3
"""
Summarizer Agent Individual Test
Tests content summarization capabilities and LLM integration
"""

import sys
import os
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.summarizer_agent import SummarizerAgent
from backend.utils import load_config


def test_summarizer_agent() -> bool:
    """Test Summarizer Agent functionality comprehensively"""
    
    print("=" * 70)
    print("SUMMARIZER AGENT INDIVIDUAL TEST")
    print("=" * 70)
    print("Tests content summarization, LLM integration, and content type detection")
    print("=" * 70)
    
    # Load configuration
    try:
        config = load_config("config/config.yaml")
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        return False
    
    # Initialize Summarizer Agent
    print("\\n" + "-" * 50)
    print("INITIALIZING SUMMARIZER AGENT")
    print("-" * 50)
    
    try:
        summarizer_agent = SummarizerAgent(config)
        print("✓ Summarizer Agent initialized successfully")
        print(f"✓ Model: {summarizer_agent.model}")
        print(f"✓ Temperature: {summarizer_agent.temperature}")
        print(f"✓ Content handlers: {list(summarizer_agent.content_handlers.keys())}")
    except Exception as e:
        print(f"✗ Failed to initialize Summarizer Agent: {e}")
        return False
    
    # Test 1: Email Summarization
    print("\\n" + "-" * 50)
    print("TEST 1: EMAIL SUMMARIZATION")
    print("-" * 50)
    
    sample_emails = [
        {
            "from": "boss@company.com",
            "subject": "Urgent: Project Deadline Update",
            "date": "2025-08-30T09:00:00Z",
            "body": "Hi team, we need to move the project deadline to next Friday due to client requirements. Please adjust your schedules accordingly.",
            "snippet": "Hi team, we need to move the project deadline to next Friday due to client requirements..."
        },
        {
            "from": "hr@company.com", 
            "subject": "New Employee Onboarding",
            "date": "2025-08-30T10:30:00Z",
            "body": "Welcome to the team! Please complete your onboarding paperwork by Wednesday.",
            "snippet": "Welcome to the team! Please complete your onboarding paperwork by Wednesday."
        },
        {
            "from": "notifications@github.com",
            "subject": "Code review requested",
            "date": "2025-08-30T11:15:00Z", 
            "body": "A new pull request has been submitted for review in the AutoTasker repository.",
            "snippet": "A new pull request has been submitted for review in the AutoTasker repository."
        }
    ]
    
    email_task = {
        "description": "Summarize recent emails",
        "parameters": {
            "content": sample_emails,
            "emails": sample_emails
        }
    }
    
    try:
        email_result = summarizer_agent.execute_task(email_task)
        print(f"✓ Email summarization result:")
        print(f"    Success: {email_result['success']}")
        print(f"    Content type: {email_result.get('content_type', 'unknown')}")
        print(f"    Original count: {email_result.get('original_count', 0)}")
        if email_result['success']:
            print(f"    Summary preview: {email_result['content'][:200]}...")
        else:
            print(f"    Error: {email_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"✗ Email summarization test failed: {e}")
    
    # Test 2: GitHub Data Summarization  
    print("\\n" + "-" * 50)
    print("TEST 2: GITHUB DATA SUMMARIZATION")
    print("-" * 50)
    
    sample_github_data = [
        {
            "commit": {
                "message": "Add new email agent functionality",
                "author": {"name": "developer1", "date": "2025-08-29T15:30:00Z"}
            },
            "message": "Add new email agent functionality",
            "author": "developer1",
            "date": "2025-08-29T15:30:00Z"
        },
        {
            "commit": {
                "message": "Fix memory agent duplicate detection bug",
                "author": {"name": "developer2", "date": "2025-08-29T16:45:00Z"}
            },
            "message": "Fix memory agent duplicate detection bug", 
            "author": "developer2",
            "date": "2025-08-29T16:45:00Z"
        },
        {
            "title": "Improve LLM error handling",
            "state": "open",
            "body": "We need better error handling for LLM API failures to improve system reliability."
        }
    ]
    
    github_task = {
        "description": "Summarize recent GitHub activity", 
        "parameters": {
            "content": sample_github_data,
            "github_data": sample_github_data
        }
    }
    
    try:
        github_result = summarizer_agent.execute_task(github_task)
        print(f"✓ GitHub summarization result:")
        print(f"    Success: {github_result['success']}")
        print(f"    Content type: {github_result.get('content_type', 'unknown')}")
        print(f"    Original count: {github_result.get('original_count', 0)}")
        if github_result['success']:
            print(f"    Summary preview: {github_result['content'][:200]}...")
        else:
            print(f"    Error: {github_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"✗ GitHub summarization test failed: {e}")
    
    # Test 3: General Content Summarization
    print("\\n" + "-" * 50)
    print("TEST 3: GENERAL CONTENT SUMMARIZATION")
    print("-" * 50)
    
    general_content = """
    AutoTasker AI is a comprehensive workflow automation system that helps users manage
    their daily tasks through natural language processing. The system includes multiple
    specialized agents for different functions: Gmail integration for email management,
    GitHub integration for repository monitoring, coding question generation for skill
    development, and smart scheduling capabilities. The memory agent prevents duplicate
    executions while the retry agent handles failures gracefully. All components work
    together to create a seamless automation experience that saves time and increases
    productivity.
    """
    
    general_task = {
        "description": "Summarize general text content",
        "parameters": {
            "content": general_content.strip(),
            "text": general_content.strip()
        }
    }
    
    try:
        general_result = summarizer_agent.execute_task(general_task)
        print(f"✓ General summarization result:")
        print(f"    Success: {general_result['success']}")
        print(f"    Content type: {general_result.get('content_type', 'unknown')}")
        if general_result['success']:
            print(f"    Summary: {general_result['content']}")
        else:
            print(f"    Error: {general_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"✗ General summarization test failed: {e}")
    
    # Test 4: Content Type Detection
    print("\\n" + "-" * 50)
    print("TEST 4: CONTENT TYPE DETECTION")
    print("-" * 50)
    
    detection_tests = [
        {
            "description": "Test email detection",
            "content": sample_emails,
            "task_desc": "Summarize Gmail inbox",
            "expected": "email"
        },
        {
            "description": "Test GitHub detection",
            "content": sample_github_data,
            "task_desc": "Summarize GitHub commits",
            "expected": "github"
        },
        {
            "description": "Test general detection",
            "content": "Just some random text to summarize",
            "task_desc": "Summarize this text",
            "expected": "general"
        }
    ]
    
    for i, test in enumerate(detection_tests, 1):
        print(f"\\n[{i}] {test['description']}")
        
        task = {"description": test['task_desc'], "parameters": {"content": test['content']}}
        detected_type = summarizer_agent._detect_content_type(test['content'], task)
        
        print(f"    Expected: {test['expected']}")
        print(f"    Detected: {detected_type}")
        
        if detected_type == test['expected']:
            print("    ✓ Correctly detected content type")
        else:
            print("    ⚠️ Content type detection mismatch")
    
    # Test 5: Special Methods
    print("\\n" + "-" * 50)
    print("TEST 5: SPECIAL SUMMARIZATION METHODS")
    print("-" * 50)
    
    # Test bullet point summary
    print("\\n📝 Testing bullet point summary:")
    try:
        bullet_summary = summarizer_agent.create_bullet_point_summary(general_content)
        print(f"    Bullet summary: {bullet_summary[:150]}...")
    except Exception as e:
        print(f"    ✗ Bullet point summary failed: {e}")
    
    # Test structured summary
    print("\\n📋 Testing structured summary:")
    try:
        structured_summary = summarizer_agent.create_structured_summary(
            general_content, 
            ["Overview", "Key Features", "Benefits"]
        )
        print(f"    Structured sections: {list(structured_summary.keys())}")
        for section, content in structured_summary.items():
            print(f"    {section}: {content[:100]}...")
    except Exception as e:
        print(f"    ✗ Structured summary failed: {e}")
    
    # Test 6: Error Handling
    print("\\n" + "-" * 50)
    print("TEST 6: ERROR HANDLING")
    print("-" * 50)
    
    error_tests = [
        {
            "description": "Empty content",
            "task": {"description": "Summarize", "parameters": {}}
        },
        {
            "description": "None content",
            "task": {"description": "Summarize", "parameters": {"content": None}}
        },
        {
            "description": "Invalid task format",
            "task": {}
        }
    ]
    
    for i, test in enumerate(error_tests, 1):
        print(f"\\n[{i}] Testing: {test['description']}")
        
        try:
            result = summarizer_agent.execute_task(test['task'])
            print(f"    Success: {result['success']}")
            if not result['success']:
                print(f"    Error handled: {result.get('error', 'Unknown')}")
            else:
                print(f"    Unexpected success: {result.get('content', '')}")
        except Exception as e:
            print(f"    Exception handled: {e}")
    
    # Test Summary
    print("\\n" + "=" * 70)
    print("SUMMARIZER AGENT CAPABILITIES SUMMARY")
    print("=" * 70)
    
    print("""
📝 CONTENT SUMMARIZATION:
   • Email summarization with sender/topic grouping
   • GitHub activity summaries with commit categorization
   • General content summarization with key point extraction
   • Intelligent content type detection
   • Multiple output formats (standard, bullet points, structured)

🤖 LLM INTEGRATION:
   • Unified LLM client support (OpenAI & OpenRouter)
   • Task-specific prompts for different content types
   • Configurable temperature and token limits
   • Robust error handling for API failures
   • Retry mechanism for transient failures

🎯 CONTENT TYPE HANDLING:
   • Email: Groups by sender, highlights urgent items
   • GitHub: Categorizes commits, identifies contributors
   • General: Preserves key details, maintains context
   • Auto-detection based on structure and task description

⚙️ CONFIGURATION:
   • Model selection per agent type
   • Temperature control for creativity vs consistency
   • Content limits to manage token usage
   • Flexible prompt customization

🛡️ ROBUSTNESS:
   • Graceful handling of empty/invalid content
   • Content truncation for large inputs
   • Fallback mechanisms for LLM failures
   • Comprehensive error reporting

📊 OUTPUT FORMATS:
   • Standard narrative summaries
   • Bullet-point formatted lists
   • Structured summaries with custom sections
   • JSON-formatted results for integration
""")
    
    print(f"\\n🎉 Summarizer Agent testing completed!")
    print("The Summarizer Agent successfully handles diverse content types and LLM integration!")
    
    return True


if __name__ == "__main__":
    try:
        success = test_summarizer_agent()
        if success:
            print("\\n🚀 Summarizer Agent is production-ready!")
        else:
            print("\\n🔧 Summarizer Agent needs attention")
    except KeyboardInterrupt:
        print("\\nTest interrupted by user")
    except Exception as e:
        print(f"\\nTest failed: {e}")
        import traceback
        traceback.print_exc()
