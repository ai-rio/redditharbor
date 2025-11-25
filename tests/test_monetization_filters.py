#!/usr/bin/env python3
"""
Unit tests for monetization and simplicity constraint filters.

Tests the business logic filtering functions added to supabase_collection.py
based on the monetizable app research methodology.
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.reddit.supabase_collection import (
    has_monetization_signals,
    meets_simplicity_constraint,
)


def test_has_monetization_signals():
    """Test monetization signal detection."""
    print("\n=== Testing has_monetization_signals() ===\n")

    # Test cases with expected results
    test_cases = [
        # Willingness to pay
        ("I would pay $10/month for this feature", True),
        ("willing to pay for a good solution", True),
        ("This premium feature is worth it", True),

        # Commercial gaps
        ("Nothing good exists for this problem", True),
        ("All existing solutions suck", True),
        ("Can't find anything that works", True),

        # Revenue model discussions
        ("I prefer a freemium model", True),
        ("What's the pricing for this SaaS?", True),
        ("Looking for subscription-based tools", True),

        # No monetization signals
        ("This is just a random discussion", False),
        ("I have a problem with my code", False),
        ("Looking for advice on career change", False),
    ]

    passed = 0
    failed = 0

    for text, expected in test_cases:
        result = has_monetization_signals(text)
        status = "PASS" if result == expected else "FAIL"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"[{status}] Expected: {expected}, Got: {result}")
        print(f"  Text: '{text[:60]}...'")
        print()

    print(f"Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_meets_simplicity_constraint():
    """Test simplicity constraint (1-3 functions)."""
    print("\n=== Testing meets_simplicity_constraint() ===\n")

    test_cases = [
        # Simple (1-3 functions)
        ("A timer and break reminder", True),
        ("Just a simple todo list", True),
        ("Track expenses and categorize them", True),
        ("Single function: habit tracking", True),

        # Complex (4+ functions)
        (
            "Track habits, set goals, view stats, share progress, compete with friends",
            False
        ),
        (
            "Features: time tracking, invoice generation, project management, "
            "client communication, expense tracking",
            False
        ),
        (
            "App does: 1. Task management 2. Time tracking 3. Reports 4. Team chat 5. Calendar",
            False
        ),

        # Edge cases - benefit of doubt
        ("Looking for a simple solution", True),
        ("", True),  # Empty text - benefit of doubt
        ("Just need something basic", True),
    ]

    passed = 0
    failed = 0

    for text, expected in test_cases:
        result = meets_simplicity_constraint(text)
        status = "PASS" if result == expected else "FAIL"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"[{status}] Expected: {expected}, Got: {result}")
        print(f"  Text: '{text[:60]}...'")
        print()

    print(f"Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_integrated_filtering():
    """Test integrated filtering logic."""
    print("\n=== Testing Integrated Filtering ===\n")

    # Scenarios that should pass both filters
    good_posts = [
        "I would pay $20/month for a simple habit tracker that just tracks daily streaks",
        "Nothing good exists for a basic timer with break reminders. I'd happily pay for premium features",
        "Existing solutions suck for expense tracking. Just need simple: add expense, categorize, view monthly summary",
    ]

    # Scenarios that should fail monetization
    no_monetization = [
        "I have a problem with my simple todo app",
        "Looking for a basic habit tracker",
    ]

    # Scenarios that should fail simplicity
    too_complex = [
        "I would pay for an all-in-one app with time tracking, project management, invoicing, client chat, and reporting",
        "Existing tools don't have these 5 features: task management, calendar, notes, file storage, team collaboration",
    ]

    print("Good posts (should pass both filters):")
    for text in good_posts:
        monetization = has_monetization_signals(text)
        simplicity = meets_simplicity_constraint(text)
        status = "PASS" if (monetization and simplicity) else "FAIL"
        print(f"  [{status}] Monetization={monetization}, Simplicity={simplicity}")
        print(f"    '{text[:60]}...'")
        print()

    print("\nNo monetization (should fail monetization):")
    for text in no_monetization:
        monetization = has_monetization_signals(text)
        simplicity = meets_simplicity_constraint(text)
        status = "PASS" if not monetization else "FAIL"
        print(f"  [{status}] Monetization={monetization}, Simplicity={simplicity}")
        print(f"    '{text[:60]}...'")
        print()

    print("\nToo complex (should fail simplicity):")
    for text in too_complex:
        monetization = has_monetization_signals(text)
        simplicity = meets_simplicity_constraint(text)
        status = "PASS" if not simplicity else "FAIL"
        print(f"  [{status}] Monetization={monetization}, Simplicity={simplicity}")
        print(f"    '{text[:60]}...'")
        print()


def main():
    """Run all tests."""
    print("=" * 80)
    print("Monetization and Simplicity Constraint Filter Tests")
    print("=" * 80)

    test1_pass = test_has_monetization_signals()
    test2_pass = test_meets_simplicity_constraint()
    test_integrated_filtering()

    print("\n" + "=" * 80)
    print("Overall Results:")
    print(f"  has_monetization_signals: {'PASS' if test1_pass else 'FAIL'}")
    print(f"  meets_simplicity_constraint: {'PASS' if test2_pass else 'FAIL'}")
    print("=" * 80)

    return 0 if (test1_pass and test2_pass) else 1


if __name__ == "__main__":
    sys.exit(main())
