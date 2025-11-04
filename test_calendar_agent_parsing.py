"""
Test calendar agent datetime parsing with the exact user prompt
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
from agents.calendar_agent import CalendarAgent

# Load config
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create calendar agent
agent = CalendarAgent(config)

# Test prompts that were failing
test_cases = [
    "Schedule a meeting in calendar on November 7th at 5:30 am for 40minutes",
    "Schedule a meeting in calendar with name hemesh DA on November 8th at 5:30 pm for 40minutes",
    "Create a meeting in Google Calendar on November 7th at 5:30 am for 40 minutes",
]

print("=" * 80)
print("Testing Calendar Agent DateTime Parsing")
print("=" * 80)

for i, description in enumerate(test_cases, 1):
    print(f"\n{'='*80}")
    print(f"Test {i}: {description}")
    print(f"{'='*80}")
    
    try:
        # Call the internal parsing method
        event_details = agent._parse_event_description(description)
        
        print(f"✅ Parsed successfully!")
        print(f"  Summary:    {event_details.get('summary')}")
        print(f"  Start Time: {event_details.get('start_time')}")
        print(f"  End Time:   {event_details.get('end_time')}")
        
        # Validate the dates
        start = event_details.get('start_time', '')
        end = event_details.get('end_time', '')
        
        # Check format
        if 'T' in start and len(start) >= 19:
            print(f"  ✓ Start time format is correct")
        else:
            print(f"  ✗ Start time format is WRONG: {start}")
        
        # Check if date matches request
        if 'November 7th' in description or 'Nov 7' in description:
            if '2025-11-07' in start:
                print(f"  ✓ Date is correct (November 7th)")
            else:
                print(f"  ✗ Date is WRONG - expected 2025-11-07, got {start[:10]}")
        
        if 'November 8th' in description or 'Nov 8' in description:
            if '2025-11-08' in start:
                print(f"  ✓ Date is correct (November 8th)")
            else:
                print(f"  ✗ Date is WRONG - expected 2025-11-08, got {start[:10]}")
        
        # Check if time matches request
        if '5:30 am' in description.lower():
            if 'T05:30:00' in start:
                print(f"  ✓ Time is correct (5:30 AM)")
            else:
                print(f"  ✗ Time is WRONG - expected 05:30:00, got {start[11:19]}")
        
        if '5:30 pm' in description.lower():
            if 'T17:30:00' in start:
                print(f"  ✓ Time is correct (5:30 PM)")
            else:
                print(f"  ✗ Time is WRONG - expected 17:30:00, got {start[11:19]}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")

print(f"\n{'='*80}")
print("Test Complete")
print(f"{'='*80}")
