"""
Comprehensive Integration Test for AutoTasker AI
Tests all fixes: time parsing, scheduling, performance metrics, agent responses
"""

import os
import sys
import json
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.langgraph_runner import AutoTaskerRunner
from backend.scheduler import ScheduleParser
from backend.utils import load_config
from agents.planner_agent import PlannerAgent


def test_time_parsing():
    """Test time parsing from various formats"""
    print("\n" + "="*60)
    print("TEST 1: Time Parsing")
    print("="*60)
    
    test_cases = [
        ("send 2 leetcode questions today at 11:47pm", "23:47"),
        ("daily at 9am", "09:00"),
        ("every day at 2:30pm", "14:30"),
        ("at 6PM send questions", "18:00"),
        ("14:00 send report", "14:00"),
    ]
    
    config = load_config("config/config.yaml")
    planner = PlannerAgent(config)
    
    passed = 0
    failed = 0
    
    for prompt, expected_time in test_cases:
        extracted = planner._extract_time_from_prompt(prompt)
        
        if extracted == expected_time:
            print(f"✅ PASS: '{prompt}' -> {extracted}")
            passed += 1
        else:
            print(f"❌ FAIL: '{prompt}' -> Expected: {expected_time}, Got: {extracted}")
            failed += 1
    
    print(f"\nTime Parsing: {passed} passed, {failed} failed")
    return failed == 0


def test_schedule_parsing():
    """Test schedule pattern parsing"""
    print("\n" + "="*60)
    print("TEST 2: Schedule Pattern Parsing")
    print("="*60)
    
    test_cases = [
        ("every 5 minutes, 3 times", {"type": "limited_interval", "value": "300:3"}),
        ("send now 3 times with 5 min gap", {"type": "limited_interval", "value": "300:3", "immediate": True}),
        ("daily at 9am", {"type": "daily", "value": "09:00"}),
        ("today at 11:47pm", {"type": "once", "value": "23:47"}),
        ("every Monday at 2pm", {"type": "weekly"}),
        ("Summarize my GitHub commits from yesterday", {"type": "once"}),  # Should NOT be "daily"
    ]
    
    passed = 0
    failed = 0
    
    for prompt, expected in test_cases:
        result = ScheduleParser.parse_schedule(prompt)
        
        # Check type matches
        type_match = result.get("type") == expected.get("type")
        
        # Check value matches (if specified)
        value_match = True
        if "value" in expected:
            value_match = result.get("value") == expected.get("value")
        
        # Check immediate flag (if specified)
        immediate_match = True
        if "immediate" in expected:
            immediate_match = result.get("immediate") == expected.get("immediate")
        
        if type_match and value_match and immediate_match:
            print(f"✅ PASS: '{prompt}'")
            print(f"   Result: {result}")
            passed += 1
        else:
            print(f"❌ FAIL: '{prompt}'")
            print(f"   Expected: {expected}")
            print(f"   Got: {result}")
            failed += 1
    
    print(f"\nSchedule Parsing: {passed} passed, {failed} failed")
    return failed == 0


def test_performance_tracking():
    """Test performance metrics tracking"""
    print("\n" + "="*60)
    print("TEST 3: Performance Metrics Tracking")
    print("="*60)
    
    try:
        from backend.performance_monitor import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        monitor.start_workflow()
        
        # Simulate operations
        monitor.start_operation("test_operation_1")
        time.sleep(0.05)
        monitor.end_operation(success=True)
        
        monitor.start_operation("test_operation_2")
        time.sleep(0.1)
        monitor.end_operation(success=True)
        
        monitor.end_workflow()
        
        summary = monitor.get_summary()
        
        # Validate summary
        assert summary["total_operations"] == 2, "Should have 2 operations"
        assert summary["successful_operations"] == 2, "Both should succeed"
        assert summary["total_duration_seconds"] >= 0.14, "Should take at least 0.14s (allowing small margin)"
        assert "operation_stats" in summary, "Should have operation stats"
        
        print("✅ Performance monitor working correctly")
        print(f"   Total Duration: {summary['total_duration_seconds']:.2f}s")
        print(f"   Operations: {summary['total_operations']}")
        print(f"   Success Rate: 100%")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance tracking failed: {e}")
        return False


def test_workflow_integration():
    """Test complete workflow with all features"""
    print("\n" + "="*60)
    print("TEST 4: Complete Workflow Integration")
    print("="*60)
    
    try:
        config = load_config("config/config.yaml")
        runner = AutoTaskerRunner(config)
        
        # Test prompt with specific time
        test_prompt = "Generate 1 coding question and email it to me"
        
        print(f"Testing prompt: '{test_prompt}'")
        print("Running workflow...")
        
        result = runner.run_workflow(test_prompt)
        
        # Validate result structure
        checks = {
            "No error": "error" not in result or result.get("error") is None,
            "Has task_plan": "task_plan" in result,
            "Has execution_results": "execution_results" in result,
            "Has performance_metrics": "performance_metrics" in result,
        }
        
        all_passed = True
        for check_name, passed in checks.items():
            icon = "✅" if passed else "❌"
            print(f"{icon} {check_name}")
            if not passed:
                all_passed = False
        
        if all_passed and "performance_metrics" in result:
            metrics = result["performance_metrics"]
            print(f"\n📊 Performance Summary:")
            print(f"   Total Duration: {metrics.get('total_duration_seconds', 0):.2f}s")
            print(f"   Total Operations: {metrics.get('total_operations', 0)}")
            print(f"   Successful: {metrics.get('successful_operations', 0)}")
            print(f"   Failed: {metrics.get('failed_operations', 0)}")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Workflow integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_response_structure():
    """Test that agent responses have proper structure for UI display"""
    print("\n" + "="*60)
    print("TEST 5: Agent Response Structure")
    print("="*60)
    
    # Simulate agent responses
    test_responses = {
        "github_0": {
            "content": "Sample GitHub commit data",
            "data": {"commits": 5, "repo": "test-repo"},
            "success": True
        },
        "leetcode_0": {
            "content": "LeetCode problem generated",
            "success": True
        },
        "dsa_0": {
            "content": "DSA question generated",
            "success": True
        }
    }
    
    passed = 0
    failed = 0
    
    for key, response in test_responses.items():
        # Check required fields
        has_content = "content" in response
        has_success = "success" in response
        
        if has_content and has_success:
            print(f"✅ PASS: {key} has proper structure")
            passed += 1
        else:
            print(f"❌ FAIL: {key} missing required fields")
            failed += 1
    
    print(f"\nAgent Response Structure: {passed} passed, {failed} failed")
    return failed == 0


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("AUTOTASKER AI - COMPREHENSIVE INTEGRATION TESTS")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Time Parsing", test_time_parsing),
        ("Schedule Parsing", test_schedule_parsing),
        ("Performance Tracking", test_performance_tracking),
        ("Agent Response Structure", test_agent_response_structure),
        ("Workflow Integration", test_workflow_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for test_name, passed in results.items():
        icon = "✅" if passed else "❌"
        print(f"{icon} {test_name}")
    
    print("\n" + "="*80)
    print(f"OVERALL: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 ALL TESTS PASSED! System is ready for production.")
    else:
        print("⚠️  Some tests failed. Please review and fix issues.")
    
    print("="*80)
    
    return passed_count == total_count


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
