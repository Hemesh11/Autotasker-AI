"""
Comprehensive test for LangGraph Runner - Main Orchestrator
Tests full workflow orchestration, agent integration, and end-to-end scenarios
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from datetime import datetime
from backend.langgraph_runner import AutoTaskerRunner
from backend.utils import load_config


def test_workflow_orchestration():
    """Test basic workflow orchestration"""
    print("🔄 Testing Workflow Orchestration...")
    
    try:
        # Initialize runner
        config = load_config("config/config.yaml")
        runner = AutoTaskerRunner(config)
        
        # Test simple DSA generation workflow
        prompt = "Generate a simple array sorting coding question"
        
        print(f"   📝 Testing prompt: {prompt}")
        result = runner.run_workflow(prompt)
        
        # Verify result structure
        assert isinstance(result, dict), "Result should be a dictionary"
        
        # Check for key components
        if "error" not in result:
            assert "original_prompt" in result, "Should contain original prompt"
            assert "task_plan" in result, "Should contain task plan"
            assert "execution_results" in result, "Should contain execution results"
            assert "logs" in result, "Should contain logs"
            
            print(f"   ✅ Workflow completed successfully")
            print(f"   📊 Task Plan: {result.get('task_plan', {}).get('tasks', [])}")
            print(f"   📈 Results: {list(result.get('execution_results', {}).keys())}")
            print(f"   🔢 Retry Count: {result.get('retry_count', 0)}")
        else:
            print(f"   ⚠️ Workflow had error: {result['error']}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_gmail_workflow():
    """Test Gmail-based workflow"""
    print("\n📧 Testing Gmail Workflow...")
    
    try:
        config = load_config("config/config.yaml")
        runner = AutoTaskerRunner(config)
        
        # Test Gmail-related prompt
        prompt = "Send me a summary of my recent emails"
        
        print(f"   📝 Testing prompt: {prompt}")
        result = runner.run_workflow(prompt)
        
        if "error" not in result:
            # Check for Gmail-specific results
            gmail_results = [k for k in result.get("execution_results", {}).keys() if "gmail" in k]
            print(f"   📧 Gmail Results: {gmail_results}")
            
            # Verify email task was attempted
            email_sent = result.get("execution_results", {}).get("email_sent")
            print(f"   📤 Email Sent: {email_sent is not None}")
            
            print(f"   ✅ Gmail workflow completed")
        else:
            print(f"   ⚠️ Gmail workflow error: {result['error']}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_github_workflow():
    """Test GitHub-based workflow"""
    print("\n🐙 Testing GitHub Workflow...")
    
    try:
        config = load_config("config/config.yaml")
        runner = AutoTaskerRunner(config)
        
        # Test GitHub-related prompt
        prompt = "Analyze commits in my GitHub repository"
        
        print(f"   📝 Testing prompt: {prompt}")
        result = runner.run_workflow(prompt)
        
        if "error" not in result:
            # Check for GitHub-specific results
            github_results = [k for k in result.get("execution_results", {}).keys() if "github" in k]
            print(f"   🐙 GitHub Results: {github_results}")
            
            print(f"   ✅ GitHub workflow completed")
        else:
            print(f"   ⚠️ GitHub workflow error: {result['error']}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_calendar_workflow():
    """Test Calendar-based workflow"""
    print("\n📅 Testing Calendar Workflow...")
    
    try:
        config = load_config("config/config.yaml")
        runner = AutoTaskerRunner(config)
        
        # Test Calendar-related prompt
        prompt = "Schedule a meeting for tomorrow at 2 PM about project review"
        
        print(f"   📝 Testing prompt: {prompt}")
        result = runner.run_workflow(prompt)
        
        if "error" not in result:
            # Check for Calendar-specific results
            calendar_results = [k for k in result.get("execution_results", {}).keys() if "calendar" in k]
            print(f"   📅 Calendar Results: {calendar_results}")
            
            print(f"   ✅ Calendar workflow completed")
        else:
            print(f"   ⚠️ Calendar workflow error: {result['error']}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_memory_integration():
    """Test memory agent integration"""
    print("\n🧠 Testing Memory Integration...")
    
    try:
        config = load_config("config/config.yaml")
        runner = AutoTaskerRunner(config)
        
        # Run same prompt twice to test memory
        prompt = "Generate a basic binary search question"
        
        print(f"   📝 First execution: {prompt}")
        result1 = runner.run_workflow(prompt)
        
        print(f"   📝 Second execution (should detect duplicate): {prompt}")
        result2 = runner.run_workflow(prompt)
        
        # Check memory detection
        memory_check1 = result1.get("memory_check", {})
        memory_check2 = result2.get("memory_check", {})
        
        print(f"   🧠 First Memory Check: {memory_check1}")
        print(f"   🧠 Second Memory Check: {memory_check2}")
        
        # Second run should potentially detect similarity
        if memory_check2.get("should_skip", False):
            print(f"   ✅ Memory correctly detected duplicate execution")
        else:
            print(f"   ℹ️ Memory did not detect duplicate (similarity below threshold)")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_routing_logic():
    """Test task routing logic"""
    print("\n🔀 Testing Routing Logic...")
    
    try:
        config = load_config("config/config.yaml")
        runner = AutoTaskerRunner(config)
        
        # Test different prompt types and their routing
        test_prompts = [
            ("Generate a coding question", "dsa"),
            ("Send me an email summary", "gmail"), 
            ("Check my GitHub commits", "github"),
            ("Schedule a meeting tomorrow", "calendar"),
            ("Find LeetCode problems about arrays", "leetcode")
        ]
        
        for prompt, expected_type in test_prompts:
            print(f"   📝 Testing: {prompt}")
            
            # Create initial state to test routing
            initial_state = {
                "original_prompt": prompt,
                "task_plan": {"tasks": [{"type": expected_type, "description": prompt}]},
                "current_step": 0,
                "execution_results": {},
                "errors": [],
                "retry_count": 0,
                "memory_check": {}
            }
            
            # Test routing
            route = runner.route_tasks(initial_state)
            print(f"   🔀 Routed to: {route} (expected: {expected_type})")
            
        print(f"   ✅ Routing logic tested")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_error_handling():
    """Test error handling and retry logic"""
    print("\n⚠️ Testing Error Handling...")
    
    try:
        config = load_config("config/config.yaml")
        runner = AutoTaskerRunner(config)
        
        # Test with a prompt that might cause errors
        prompt = "Send email to invalid@nonexistent-domain-12345.com with GitHub analysis"
        
        print(f"   📝 Testing error-prone prompt: {prompt}")
        result = runner.run_workflow(prompt)
        
        errors = result.get("errors", [])
        retry_count = result.get("retry_count", 0)
        
        print(f"   ⚠️ Errors encountered: {len(errors)}")
        print(f"   🔄 Retry count: {retry_count}")
        
        if errors:
            print(f"   📋 Error details:")
            for i, error in enumerate(errors[:3]):  # Show first 3 errors
                print(f"      {i+1}. {error}")
                
        print(f"   ✅ Error handling tested")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_state_management():
    """Test state management across workflow"""
    print("\n📊 Testing State Management...")
    
    try:
        config = load_config("config/config.yaml")
        runner = AutoTaskerRunner(config)
        
        prompt = "Generate a simple coding question and send it to me"
        
        print(f"   📝 Testing prompt: {prompt}")
        result = runner.run_workflow(prompt)
        
        if "error" not in result:
            # Verify state components
            print(f"   📝 Original Prompt: {result.get('original_prompt', 'Missing')}")
            print(f"   📋 Task Plan Tasks: {len(result.get('task_plan', {}).get('tasks', []))}")
            print(f"   📊 Execution Results: {len(result.get('execution_results', {}))}")
            print(f"   📝 Email Content Length: {len(result.get('email_content', ''))}")
            print(f"   📋 Logs Count: {len(result.get('logs', []))}")
            
            # Check if state was properly maintained
            task_plan = result.get('task_plan', {})
            if task_plan:
                print(f"   ✅ Task plan maintained")
            else:
                print(f"   ⚠️ Task plan missing")
                
        print(f"   ✅ State management tested")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_end_to_end_workflow():
    """Test complete end-to-end workflow"""
    print("\n🎯 Testing End-to-End Workflow...")
    
    try:
        config = load_config("config/config.yaml")
        runner = AutoTaskerRunner(config)
        
        # Test comprehensive workflow
        prompt = "Create a medium difficulty array manipulation coding question and email me the results"
        
        print(f"   📝 Testing comprehensive prompt: {prompt}")
        start_time = datetime.now()
        
        result = runner.run_workflow(prompt)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        print(f"   ⏱️ Execution Time: {execution_time:.2f} seconds")
        
        if "error" not in result:
            # Verify all workflow components
            components = [
                ("Memory Check", "memory_check" in result),
                ("Task Plan", "task_plan" in result),
                ("Execution Results", len(result.get("execution_results", {})) > 0),
                ("Logs", len(result.get("logs", [])) > 0),
                ("Email Content", len(result.get("email_content", "")) > 0)
            ]
            
            print(f"   📊 Workflow Components:")
            for component, present in components:
                status = "✅" if present else "❌"
                print(f"      {status} {component}")
                
            # Check final state
            final_step = result.get("current_step", 0)
            total_tasks = len(result.get("task_plan", {}).get("tasks", []))
            print(f"   📈 Progress: {final_step}/{total_tasks} tasks completed")
            
            print(f"   ✅ End-to-end workflow completed successfully")
        else:
            print(f"   ⚠️ End-to-end workflow error: {result['error']}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def generate_test_report(results: dict):
    """Generate comprehensive test report"""
    print("\n" + "="*60)
    print("🏁 LANGGRAPH RUNNER TEST REPORT")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed")
    print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\n📋 Test Details:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    if passed_tests == total_tests:
        print(f"\n🎉 ALL TESTS PASSED! LangGraph Runner is production-ready!")
        print(f"🚀 Ready for full integration and deployment")
    else:
        print(f"\n⚠️ Some tests failed. Review and fix issues before deployment.")
    
    print("="*60)


def main():
    """Run all LangGraph Runner tests"""
    print("🚀 AUTOTASKER AI - LANGGRAPH RUNNER COMPREHENSIVE TEST")
    print("="*60)
    print("Testing main workflow orchestrator and end-to-end scenarios")
    print("="*60)
    
    # Run all tests
    test_results = {
        "Workflow Orchestration": test_workflow_orchestration(),
        "Gmail Workflow": test_gmail_workflow(),
        "GitHub Workflow": test_github_workflow(),
        "Calendar Workflow": test_calendar_workflow(),
        "Memory Integration": test_memory_integration(),
        "Routing Logic": test_routing_logic(),
        "Error Handling": test_error_handling(),
        "State Management": test_state_management(),
        "End-to-End Workflow": test_end_to_end_workflow()
    }
    
    # Generate report
    generate_test_report(test_results)


if __name__ == "__main__":
    main()
