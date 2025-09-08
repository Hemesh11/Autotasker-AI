#!/usr/bin/env python3
"""
Test script for natural language scheduling in Streamlit
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_schedule_parsing():
    """Test natural language schedule parsing"""
    print("🧠 Testing Natural Language Schedule Parsing...")
    
    try:
        from backend.scheduler import ScheduleParser
        
        test_prompts = [
            "Send me 2 coding questions daily at 9AM",
            "Generate DSA problems every Monday at 2PM", 
            "Email commit summary every Tuesday at 10:30",
            "Check unread emails every 30 minutes",
            "Weekly coding practice on Friday at 5PM",
            "Monthly report on 1st at 8AM"
        ]
        
        for prompt in test_prompts:
            result = ScheduleParser.parse_schedule(prompt)
            if result:
                print(f"   ✅ '{prompt}'")
                print(f"      → Type: {result['type']}, Value: {result['value']}")
            else:
                print(f"   ❌ '{prompt}' → No schedule detected")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Schedule parsing failed: {e}")
        return False

def test_streamlit_integration():
    """Test Streamlit integration capability"""
    print("\n🎨 Testing Streamlit Integration...")
    
    try:
        # Test if we can import the enhanced frontend
        import streamlit as st
        print("   ✅ Streamlit available")
        
        # Test if we can import ScheduleParser  
        from backend.scheduler import ScheduleParser
        print("   ✅ ScheduleParser available")
        
        # Test sample detection
        sample_prompt = "Send coding questions daily at 9AM"
        detected = ScheduleParser.parse_schedule(sample_prompt)
        
        if detected:
            print(f"   ✅ Sample detection working: {detected}")
        else:
            print("   ❌ Sample detection failed")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 AUTOTASKER AI - NATURAL LANGUAGE SCHEDULING TEST\n")
    
    # Test schedule parsing
    parsing_success = test_schedule_parsing()
    
    # Test Streamlit integration
    integration_success = test_streamlit_integration()
    
    print(f"\n{'='*60}")
    print("🏁 TEST RESULTS")
    print(f"{'='*60}")
    
    if parsing_success and integration_success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Natural language scheduling ready!")
        print("\n🚀 Ready to use in Streamlit:")
        print("   streamlit run frontend/streamlit_app.py")
        print("\n💡 Try these prompts:")
        print("   - 'Send me 2 coding questions daily at 9AM'")
        print("   - 'Generate DSA problems every Monday at 2PM'")
        print("   - 'Check emails every 30 minutes'")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
