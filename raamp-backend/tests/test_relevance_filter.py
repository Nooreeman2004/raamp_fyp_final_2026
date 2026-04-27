"""Test relevance filtering for trends"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from application.services.trend_simplification_service import TrendSimplificationService

# Test cases
test_cases = [
    ('biryani', 'restaurant', 'food', True),
    ('getafe vs barcelona', 'restaurant', 'fashion', False),
    ('bubble tea', 'cafe', 'beverages', True),
    ('manchester united', 'restaurant', 'food', False),
    ('ramadan special', 'restaurant', 'food', True),
    ('cricket match', 'restaurant', 'food', False),
    ('pizza recipe', 'restaurant', 'food', True),
    ('election results', 'restaurant', 'food', False),
]

print("\nRelevance Filter Test Results:")
print("=" * 80)
print(f"{'Keyword':<30} | {'Business':<12} | {'Niche':<12} | {'Expected':<10} | {'Result'}")
print("-" * 80)

passed = 0
failed = 0

for keyword, biz_type, niche, expected in test_cases:
    result = TrendSimplificationService.is_relevant_for_business(keyword, biz_type, niche)
    status = "PASS" if result == expected else "FAIL"
    symbol = "✓" if result else "✗"
    
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    print(f"{keyword:<30} | {biz_type:<12} | {niche:<12} | {str(expected):<10} | {symbol} {status}")

print("-" * 80)
print(f"Results: {passed} passed, {failed} failed")
print("=" * 80)
