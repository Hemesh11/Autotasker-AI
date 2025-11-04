"""
Quick test to verify calendar datetime parsing is fixed
"""

import re

def clean_timezone_suffix(datetime_str):
    """
    Remove timezone suffixes from datetime string
    Handles: Z, +HH:MM, -HH:MM, +HHMM, -HHMM
    """
    # Remove 'Z' suffix (UTC indicator)
    if datetime_str.endswith('Z'):
        datetime_str = datetime_str[:-1]
    
    # Remove timezone offset like +05:30 or -05:00 (but ONLY from end of string)
    # Pattern: optional +/- followed by HH:MM or HHMM at the END of string
    datetime_str = re.sub(r'[+-]\d{2}:\d{2}$', '', datetime_str)  # Remove +05:30 or -05:00
    datetime_str = re.sub(r'[+-]\d{4}$', '', datetime_str)        # Remove +0530 or -0500
    
    return datetime_str

# Test cases
test_cases = [
    # (input, expected_output, description)
    ("2025-11-08T17:30:00", "2025-11-08T17:30:00", "No timezone suffix"),
    ("2025-11-08T17:30:00Z", "2025-11-08T17:30:00", "Z suffix"),
    ("2025-11-08T17:30:00+05:30", "2025-11-08T17:30:00", "Positive offset with colon"),
    ("2025-11-08T17:30:00-05:00", "2025-11-08T17:30:00", "Negative offset with colon"),
    ("2025-11-08T17:30:00+0530", "2025-11-08T17:30:00", "Positive offset without colon"),
    ("2025-11-08T17:30:00-0500", "2025-11-08T17:30:00", "Negative offset without colon"),
    ("2025-11-05T14:00:00", "2025-11-05T14:00:00", "Date with dashes (should NOT be affected)"),
]

print("=" * 80)
print("Testing Timezone Suffix Removal")
print("=" * 80)

all_passed = True
for input_str, expected, description in test_cases:
    result = clean_timezone_suffix(input_str)
    passed = result == expected
    status = "✅ PASS" if passed else "❌ FAIL"
    
    print(f"\n{status}: {description}")
    print(f"  Input:    {input_str}")
    print(f"  Expected: {expected}")
    print(f"  Got:      {result}")
    
    if not passed:
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("✅ All tests passed!")
else:
    print("❌ Some tests failed!")
print("=" * 80)
