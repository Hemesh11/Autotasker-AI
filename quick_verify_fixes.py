"""
Quick Verification Script - Test All Latest Fixes
Run this to verify all fixes are working correctly
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.scheduler import ScheduleParser


def test_schedule_patterns():
    """Test schedule pattern detection"""
    print("=" * 60)
    print("VERIFYING SCHEDULE PATTERN FIXES")
    print("=" * 60)
    
    test_cases = [
        # Should NOT be detected as "daily"
        ("Summarize my GitHub commits from yesterday", "once", False),
        ("Show me commits from yesterday", "once", False),
        ("yesterday's data", "once", False),
        
        # Should be detected as "daily"
        ("Send me reports daily at 9am", "daily", True),
        ("every day at 2pm send updates", "daily", True),
        
        # Specific time patterns
        ("today at 11:47pm", "once", True),
        ("tonight at 9pm", "once", True),
        
        # Immediate repeated execution
        ("now 3 times with 5 min gap", "limited_interval", True),
        ("send now 3 times", "limited_interval", True),
    ]
    
    passed = 0
    failed = 0
    
    for prompt, expected_type, should_have_schedule in test_cases:
        result = ScheduleParser.parse_schedule(prompt)
        result_type = result.get("type")
        
        # Check if type matches
        type_match = result_type == expected_type
        
        # For "yesterday" cases, we want "once" but NOT "daily"
        if "yesterday" in prompt.lower():
            type_match = result_type != "daily"  # Should NOT be daily
        
        if type_match:
            print(f"✅ PASS: '{prompt[:50]}'")
            print(f"   → {result}")
            passed += 1
        else:
            print(f"❌ FAIL: '{prompt[:50]}'")
            print(f"   Expected type: {expected_type}")
            print(f"   Got: {result}")
            failed += 1
    
    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'=' * 60}\n")
    
    return failed == 0


def check_streamlit_files():
    """Verify correct streamlit file exists"""
    print("=" * 60)
    print("VERIFYING STREAMLIT FILES")
    print("=" * 60)
    
    import os
    
    frontend_dir = "frontend"
    
    files = {
        "streamlit_app.py": "✅ MAIN FILE (should exist)",
        "streamlit_app_enhanced.py": "⚠️ OLD FILE (can be archived)",
        "streamlit_app_original.py": "⚠️ BACKUP FILE (can be archived)"
    }
    
    for filename, description in files.items():
        filepath = os.path.join(frontend_dir, filename)
        exists = os.path.exists(filepath)
        
        if filename == "streamlit_app.py":
            if exists:
                print(f"✅ {filename} - {description}")
            else:
                print(f"❌ {filename} - MISSING! This is required!")
                return False
        else:
            status = "Present" if exists else "Not present"
            print(f"ℹ️  {filename} - {status} - {description}")
    
    print(f"\n{'=' * 60}")
    print("✅ Correct streamlit file (streamlit_app.py) exists!")
    print(f"{'=' * 60}\n")
    
    return True


def check_performance_monitor():
    """Verify performance monitor works"""
    print("=" * 60)
    print("VERIFYING PERFORMANCE MONITOR")
    print("=" * 60)
    
    try:
        from backend.performance_monitor import PerformanceMonitor
        import time
        
        monitor = PerformanceMonitor()
        monitor.start_workflow()
        
        # Quick test
        monitor.start_operation("test_op")
        time.sleep(0.05)
        monitor.end_operation(success=True)
        
        monitor.end_workflow()
        summary = monitor.get_summary()
        
        if summary["total_operations"] == 1 and summary["successful_operations"] == 1:
            print("✅ Performance monitor working correctly")
            print(f"   Total Duration: {summary['total_duration_seconds']:.2f}s")
            print(f"   Operations: {summary['total_operations']}")
            return True
        else:
            print("❌ Performance monitor has issues")
            return False
            
    except Exception as e:
        print(f"❌ Performance monitor test failed: {e}")
        return False
    finally:
        print(f"{'=' * 60}\n")


def main():
    """Run all verification checks"""
    print("\n" + "=" * 60)
    print("🔍 QUICK VERIFICATION - ALL LATEST FIXES")
    print("=" * 60)
    print()
    
    results = {
        "Schedule Patterns": test_schedule_patterns(),
        "Streamlit Files": check_streamlit_files(),
        "Performance Monitor": check_performance_monitor()
    }
    
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        icon = "✅" if passed else "❌"
        print(f"{icon} {test_name}: {'PASSED' if passed else 'FAILED'}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("✨ ALL VERIFICATIONS PASSED! ✨")
        print("\n🚀 System is ready! You can now:")
        print("   1. Run: streamlit run frontend/streamlit_app.py")
        print("   2. Test prompts:")
        print("      - 'Summarize my GitHub commits from yesterday'")
        print("      - 'Send me 2 leetcode questions today at 11:47pm'")
        print("      - 'Send me questions now 3 times with 5 min gap'")
        print("=" * 60)
        return 0
    else:
        print("⚠️ SOME VERIFICATIONS FAILED")
        print("Please review the output above for details.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
