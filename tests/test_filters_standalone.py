#!/usr/bin/env python3
"""
Standalone tests for monetization and simplicity constraint filters.

This version copies the filter logic for testing without dependencies.
"""

import re

# Business logic filtering: Monetization signals
MONETIZATION_SIGNALS = [
    # Willingness to pay phrases
    "would pay", "willing to pay", "happy to pay", "i'd pay", "i'll pay",
    "subscription", "worth $", "worth paying", "premium", "paid version",
    # Commercial gap mentions
    "nothing good exists", "existing solutions suck", "can't find anything",
    "no good options", "everything is bad", "all options are terrible",
    "existing tools don't work", "current solutions are expensive",
    # Revenue model discussions
    "freemium", "saas", "pricing", "business model", "pay monthly",
    "pay yearly", "one-time payment", "affordable price", "free trial",
    "upgrade to pro", "premium features"
]

# Business logic filtering: Feature/function indicators
FEATURE_INDICATORS = [
    "feature", "function", "functionality", "capability", "can do",
    "does", "ability to", "allows", "enables", "supports"
]

# Business logic filtering: Simple list patterns
LIST_PATTERNS = [
    r'\d+\.',  # Numbered lists: 1. 2. 3.
    r'[-•*]',  # Bullet points: - • *
    r'\n\s*\d+\)',  # Parenthetical numbers: 1) 2) 3)
]


def has_monetization_signals(text: str) -> bool:
    """Check if text contains monetization signals."""
    if not text:
        return False

    text_lower = text.lower()
    has_signal = any(signal in text_lower for signal in MONETIZATION_SIGNALS)
    return has_signal


def meets_simplicity_constraint(text: str) -> bool:
    """Check if described solution is simple (1-3 core functions only)."""
    if not text:
        return True  # Benefit of doubt

    text_lower = text.lower()

    # Strategy 1: Count explicit feature/function mentions
    feature_count = 0
    for indicator in FEATURE_INDICATORS:
        if indicator in text_lower:
            feature_count += text_lower.count(indicator)

    if feature_count >= 4:
        return False

    # Strategy 2: Detect lists and count items
    list_items = []
    for pattern in LIST_PATTERNS:
        matches = re.findall(pattern, text)
        list_items.extend(matches)

    if len(list_items) >= 4:
        return False

    # Strategy 3: Count comma-separated items in feature descriptions
    for sentence in text.split('.'):
        sentence_lower = sentence.lower()

        # Count commas in sentences that describe capabilities
        if any(word in sentence_lower for word in ["track", "manage", "monitor", "create", "generate", "send", "receive"]):
            comma_count = sentence_lower.count(",")

            # If 3+ commas in an action sentence, likely 4+ functions
            if comma_count >= 3:
                return False

    # Strategy 4: Count "and" conjunctions in function descriptions
    if any(keyword in text_lower for keyword in ["can", "does", "allows", "enables"]):
        sentences = text.split('.')
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in ["can", "does", "allows", "enables"]):
                and_count = sentence_lower.count(" and ")
                comma_count = sentence_lower.count(",")
                if and_count + comma_count >= 3:
                    return False

    return True


def test_has_monetization_signals():
    """Test monetization signal detection."""
    print("\n=== Testing has_monetization_signals() ===\n")

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
        status = "✓" if result == expected else "✗"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"[{status}] Expected: {expected}, Got: {result}")
        print(f"    Text: '{text[:60]}...'")

    print(f"\n  Results: {passed} passed, {failed} failed\n")
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
        (
            "It has these features: feature 1, feature 2, feature 3, feature 4",
            False
        ),

        # Edge cases - benefit of doubt
        ("Looking for a simple solution", True),
        ("", True),
        ("Just need something basic", True),
    ]

    passed = 0
    failed = 0

    for text, expected in test_cases:
        result = meets_simplicity_constraint(text)
        status = "✓" if result == expected else "✗"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"[{status}] Expected: {expected}, Got: {result}")
        print(f"    Text: '{text[:60]}...'")

    print(f"\n  Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_integrated_filtering():
    """Test integrated filtering logic."""
    print("\n=== Testing Integrated Filtering ===\n")

    # Scenarios that should pass both filters
    good_posts = [
        "I would pay $20/month for a simple habit tracker that just tracks daily streaks",
        "Nothing good exists for a basic timer with break reminders. I'd happily pay for premium features",
        "Existing solutions suck for expense tracking. Just need: add expense and categorize",
    ]

    # Scenarios that should fail monetization
    no_monetization = [
        "I have a problem with my simple todo app",
        "Looking for a basic habit tracker",
    ]

    # Scenarios that should fail simplicity
    too_complex = [
        "I would pay for an all-in-one app with 5 features: time tracking, project management, invoicing, client chat, and reporting",
        "Existing tools don't have these 5 features: 1. task management 2. calendar 3. notes 4. file storage 5. team collaboration",
    ]

    print("Good posts (should pass both filters):")
    all_passed = True
    for text in good_posts:
        monetization = has_monetization_signals(text)
        simplicity = meets_simplicity_constraint(text)
        passes = monetization and simplicity
        status = "✓" if passes else "✗"
        if not passes:
            all_passed = False
        print(f"  [{status}] Monetization={monetization}, Simplicity={simplicity}")
        print(f"      '{text[:70]}...'")

    print("\nNo monetization (should fail monetization filter):")
    for text in no_monetization:
        monetization = has_monetization_signals(text)
        simplicity = meets_simplicity_constraint(text)
        correctly_fails = not monetization
        status = "✓" if correctly_fails else "✗"
        print(f"  [{status}] Monetization={monetization}, Simplicity={simplicity}")
        print(f"      '{text[:70]}...'")

    print("\nToo complex (should fail simplicity filter):")
    for text in too_complex:
        monetization = has_monetization_signals(text)
        simplicity = meets_simplicity_constraint(text)
        correctly_fails = not simplicity
        status = "✓" if correctly_fails else "✗"
        print(f"  [{status}] Monetization={monetization}, Simplicity={simplicity}")
        print(f"      '{text[:70]}...'")

    return all_passed


def main():
    """Run all tests."""
    print("=" * 80)
    print("Monetization and Simplicity Constraint Filter Tests")
    print("=" * 80)

    test1_pass = test_has_monetization_signals()
    test2_pass = test_meets_simplicity_constraint()
    test3_pass = test_integrated_filtering()

    print("\n" + "=" * 80)
    print("Overall Results:")
    print(f"  has_monetization_signals:     {'PASS ✓' if test1_pass else 'FAIL ✗'}")
    print(f"  meets_simplicity_constraint:  {'PASS ✓' if test2_pass else 'FAIL ✗'}")
    print(f"  integrated_filtering:         {'PASS ✓' if test3_pass else 'FAIL ✗'}")
    print("=" * 80)

    all_pass = test1_pass and test2_pass and test3_pass
    if all_pass:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed.")

    return 0 if all_pass else 1


if __name__ == "__main__":
    exit(main())
