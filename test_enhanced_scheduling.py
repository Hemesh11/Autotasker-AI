#!/usr/bin/env python3
"""
Test enhanced scheduling patterns
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.scheduler import ScheduleParser

def test_enhanced_patterns():
    """Test the enhanced scheduling patterns"""
    print("🚀 TESTING ENHANCED SCHEDULING PATTERNS")
    print("=" * 60)
    
    test_cases = [
        'Generate 2 leetcode question every 2 minutes once, for 5 times',
        'every 2 minutes, 5 times', 
        'every 3 minutes for 4 times',
        'every 1 hour repeat 3 times',
        'every 5 minutes 3 times',
        'run every 10 minutes for 2 times',
        'execute every 1 hour, repeat 6 times'
    ]
    
    for test in test_cases:
        result = ScheduleParser.parse_schedule(test)
        print(f"   '{test}'")
        print(f"   → {result}")
        print()

if __name__ == "__main__":
    test_enhanced_patterns()
