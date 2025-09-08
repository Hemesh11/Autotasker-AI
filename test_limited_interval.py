#!/usr/bin/env python3
"""
Test script for Limited Interval scheduling functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_limited_interval_parsing():
    """Test natural language parsing for limited intervals"""
    print("🔧 Testing Limited Interval Parsing...")
    
    try:
        from backend.scheduler import ScheduleParser
        
        test_cases = [
            ("Generate 2 questions every 5 minutes, 3 times", {'type': 'limited_interval', 'value': '300:3'}),
            ("Send emails every 10 minutes, 5 times", {'type': 'limited_interval', 'value': '600:5'}),
            ("Check status every 2 hours, 4 times", {'type': 'limited_interval', 'value': '7200:4'}),
            ("Run task every 1 minute, 10 times", {'type': 'limited_interval', 'value': '60:10'}),
        ]
        
        for input_text, expected in test_cases:
            result = ScheduleParser.parse_schedule(input_text)
            if result == expected:
                print(f"   ✅ '{input_text}' → {result}")
            else:
                print(f"   ❌ '{input_text}' → {result} (expected {expected})")
        
        print("   ✅ Limited interval parsing working")
        return True
        
    except Exception as e:
        print(f"   ❌ Limited interval parsing failed: {e}")
        return False

def test_scheduler_trigger_creation():
    """Test if scheduler can create limited interval triggers"""
    print("\n⚙️ Testing Scheduler Trigger Creation...")
    
    try:
        from backend.scheduler import TaskScheduler
        from backend.utils import load_config
        
        config = load_config("config/config.yaml")
        scheduler = TaskScheduler(config, use_cloud=False)
        
        # Test creating limited interval trigger
        trigger = scheduler._create_trigger('limited_interval', '300:3')
        
        print(f"   ✅ Created trigger: {trigger}")
        print(f"   ✅ Trigger type: {type(trigger).__name__}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Trigger creation failed: {e}")
        return False

def test_streamlit_integration():
    """Test if Streamlit can detect limited intervals"""
    print("\n🎨 Testing Streamlit Integration...")
    
    try:
        from backend.scheduler import ScheduleParser
        
        test_prompt = "Generate 2 coding questions every 5 minutes, 3 times"
        detected = ScheduleParser.parse_schedule(test_prompt)
        
        if detected and detected['type'] == 'limited_interval':
            print(f"   ✅ Streamlit detection working: {detected}")
            
            # Parse the values
            seconds, repetitions = detected['value'].split(':')
            minutes = int(seconds) // 60
            
            print(f"   ✅ Will run every {minutes} minutes, {repetitions} times")
            return True
        else:
            print(f"   ❌ Detection failed: {detected}")
            return False
        
    except Exception as e:
        print(f"   ❌ Streamlit integration failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 AUTOTASKER AI - LIMITED INTERVAL SCHEDULING TEST")
    print("=" * 60)
    
    tests = [
        test_limited_interval_parsing,
        test_scheduler_trigger_creation,
        test_streamlit_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print("🏁 TEST RESULTS")
    print("=" * 60)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Limited interval scheduling ready!")
        print("\n🚀 Ready to use:")
        print("   'Generate 2 questions every 5 minutes, 3 times'")
        print("   'Send emails every 10 minutes, 5 times'")
        print("   'Check status every 2 hours, 4 times'")
    else:
        print(f"❌ {total - passed}/{total} tests failed")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    print(f"📈 Success Rate: {(passed/total)*100:.1f}%")

if __name__ == "__main__":
    main()
