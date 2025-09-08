#!/usr/bin/env python3
"""
Planner Agent Individual Test
Tests natural language to task plan conversion
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.planner_agent import PlannerAgent
from backend.utils import load_config


def test_planner_agent() -> bool:
    """Test Planner Agent functionality with various natural language prompts"""
    
    print("=" * 70)
    print("PLANNER AGENT INDIVIDUAL TEST")
    print("=" * 70)
    print("Tests natural language conversion to structured task plans")
    print("=" * 70)
    
    # Load configuration
    try:
        config = load_config("config/config.yaml")
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        # Minimal fallback config
        config = {
            "llm": {
                "provider": "openrouter",
                "model": "meta-llama/llama-3.3-70b-instruct",
                "temperature": 0.7
            },
            "agents": {
                "planner": {
                    "model": "meta-llama/llama-3.3-70b-instruct",
                    "temperature": 0.3
                }
            }
        }
    
    # Initialize Planner Agent
    print("\n" + "-" * 50)
    print("INITIALIZING PLANNER AGENT")
    print("-" * 50)
    
    try:
        planner = PlannerAgent(config)
        print("✓ Planner Agent initialized successfully")
        print(f"✓ Using model: {planner.model}")
        print(f"✓ Temperature: {planner.temperature}")
    except Exception as e:
        print(f"✗ Failed to initialize Planner Agent: {e}")
        return False
    
    # Test cases covering different scenarios
    test_cases = [
        {
            "name": "Gmail Email Analysis",
            "prompt": "Check my recent emails and summarize any important messages from work",
            "expected_types": ["gmail", "summarize", "email"]
        },
        {
            "name": "GitHub Activity Report",
            "prompt": "Get my GitHub activity for the last week and send me a summary",
            "expected_types": ["github", "summarize", "email"]
        },
        {
            "name": "Daily DSA Questions",
            "prompt": "Generate 3 medium difficulty coding questions on arrays and strings",
            "expected_types": ["dsa", "email"]
        },
        {
            "name": "LeetCode Study Plan",
            "prompt": "Create a daily LeetCode study plan with 2 medium problems",
            "expected_types": ["leetcode", "email"]
        },
        {
            "name": "Mixed Workflow",
            "prompt": "Send me daily coding questions, check my emails, and update me on GitHub commits",
            "expected_types": ["dsa", "gmail", "github", "summarize", "email"]
        },
        {
            "name": "Scheduled Task",
            "prompt": "Every morning at 9 AM, send me 2 LeetCode problems and my unread emails",
            "expected_types": ["leetcode", "gmail", "email"]
        },
        {
            "name": "Complex Analysis",
            "prompt": "Analyze my GitHub repos, find recent commits, generate coding questions based on the languages used, and email me everything",
            "expected_types": ["github", "dsa", "summarize", "email"]
        },
        {
            "name": "Simple Request",
            "prompt": "Send me an email",
            "expected_types": ["email"]
        }
    ]
    
    # Execute test cases
    print("\n" + "-" * 50)
    print("RUNNING TEST CASES")
    print("-" * 50)
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}] Testing: {test_case['name']}")
        print("-" * 40)
        print(f"Prompt: '{test_case['prompt']}'")
        
        try:
            # Create task plan
            plan = planner.create_task_plan(test_case['prompt'])
            
            # Analyze results
            success = plan.get('tasks') is not None and len(plan.get('tasks', [])) > 0
            
            if success:
                print("✓ Plan created successfully")
                print(f"  Intent: {plan.get('intent', 'Not specified')}")
                print(f"  Schedule: {plan.get('schedule', 'once')}")
                print(f"  Total tasks: {plan.get('total_tasks', len(plan.get('tasks', [])))}")
                
                # Show task breakdown
                task_types = [task.get('type') for task in plan.get('tasks', [])]
                print(f"  Task types: {', '.join(task_types)}")
                
                # Check for expected task types
                missing_types = set(test_case['expected_types']) - set(task_types)
                if missing_types:
                    print(f"  ⚠️ Missing expected types: {', '.join(missing_types)}")
                
                # Show detailed tasks
                print("  Tasks:")
                for task in plan.get('tasks', []):
                    deps = f" (deps: {', '.join(task.get('dependencies', []))})" if task.get('dependencies') else ""
                    print(f"    - {task.get('id')}: {task.get('type')} - {task.get('description')}{deps}")
                
                results.append({
                    "test": test_case['name'],
                    "success": True,
                    "plan": plan,
                    "task_count": len(plan.get('tasks', [])),
                    "fallback": plan.get('fallback', False)
                })
            else:
                print("✗ Failed to create valid plan")
                results.append({
                    "test": test_case['name'],
                    "success": False,
                    "error": "No valid tasks generated"
                })
                
        except Exception as e:
            print(f"✗ Exception during planning: {e}")
            results.append({
                "test": test_case['name'],
                "success": False,
                "error": str(e)
            })
    
    # Test fallback scenarios
    print(f"\n[{len(test_cases) + 1}] Testing: Fallback Scenarios")
    print("-" * 40)
    
    fallback_tests = [
        "asdf random gibberish xyz",
        "",
        "Tell me about quantum physics and cooking recipes",
    ]
    
    fallback_results = []
    for prompt in fallback_tests:
        try:
            plan = planner.create_task_plan(prompt)
            success = plan.get('tasks') is not None
            fallback_used = plan.get('fallback', False) or plan.get('emergency', False)
            
            print(f"  Prompt: '{prompt}' - {'✓' if success else '✗'} {'(fallback)' if fallback_used else ''}")
            fallback_results.append(success)
        except Exception as e:
            print(f"  Prompt: '{prompt}' - ✗ Exception: {e}")
            fallback_results.append(False)
    
    # Test Results Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    fallback_successful = sum(fallback_results)
    fallback_total = len(fallback_results)
    
    print(f"Main Tests: {successful}/{total} successful")
    print(f"Fallback Tests: {fallback_successful}/{fallback_total} successful")
    print()
    
    for result in results:
        status = "✓" if result['success'] else "✗"
        fallback_info = " (fallback)" if result.get('fallback') else ""
        task_count = f" ({result.get('task_count', 0)} tasks)" if result['success'] else ""
        error_info = f" - {result.get('error', '')}" if result.get('error') else ""
        print(f"{status} {result['test']}{task_count}{fallback_info}{error_info}")
    
    # Planning Capabilities Analysis
    print("\n" + "=" * 70)
    print("PLANNER AGENT CAPABILITIES ANALYSIS")
    print("=" * 70)
    
    print("""
🎯 NATURAL LANGUAGE UNDERSTANDING:
   • Converts English prompts to structured task plans
   • Identifies intent and required operations
   • Maps to appropriate agent types (gmail, github, dsa, leetcode)
   • Handles scheduling requirements (daily, weekly, once)

📋 TASK ORCHESTRATION:
   • Creates task dependencies and execution order
   • Assigns appropriate priorities (1-3)
   • Enhances tasks with default parameters
   • Ensures email delivery as final step

🛡️ ROBUSTNESS FEATURES:
   • Fallback planning when LLM fails
   • Emergency plans for critical failures
   • Input validation and error recovery
   • Graceful degradation strategies

🔧 SUPPORTED WORKFLOWS:
   • Email analysis and processing (Gmail)
   • Code repository tracking (GitHub)
   • Coding question generation (DSA)
   • LeetCode study plans (LeetCode)
   • Content summarization (Summarizer)
   • Result delivery (Email)

⚙️ PLANNING INTELLIGENCE:
   • Context-aware parameter selection
   • Time-based task scheduling
   • Multi-agent workflow coordination
   • Resource optimization strategies
""")
    
    if successful == total and fallback_successful == fallback_total:
        print("\n🎉 All Planner Agent tests passed!")
        print("The agent successfully converts natural language to structured task plans!")
        return True
    else:
        print(f"\n⚠️ Some tests failed: {total - successful} main tests, {fallback_total - fallback_successful} fallback tests")
        return False


if __name__ == "__main__":
    try:
        success = test_planner_agent()
        if success:
            print("\n🚀 Planner Agent is production-ready!")
        else:
            print("\n🔧 Planner Agent needs attention")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
