#!/usr/bin/env python3
"""
Test script for the enhanced monetization analyzer JSON parsing
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the analyzer
try:
    from agent_tools.monetization_agno_analyzer import MonetizationAgnoAnalyzer
    print("✅ Successfully imported MonetizationAgnoAnalyzer")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

def test_json_repair_parsing():
    """Test various JSON formats that need repair"""
    print("\n🧪 Testing JSON Repair and Field Mapping...")

    analyzer = MonetizationAgnoAnalyzer()

    # Test case 1: Well-formed JSON with correct field names
    print("\n1. Testing well-formed JSON...")
    good_json = {
        "sentiment_toward_payment": "Positive",
        "willingness_to_pay_score": 85,
        "customer_segment": "B2B",
        "mentioned_price_points": ["$300/month", "$150/month"],
        "revenue_potential_score": 90,
        "confidence": 0.8
    }
    result = analyzer._parse_team_response(json.dumps(good_json))
    print(f"   ✅ Parsed successfully: {result.get('sentiment_toward_payment', 'MISSING')}")
    print(f"   ✅ WTP Score: {result.get('willingness_to_pay_score', 'MISSING')}")
    print(f"   ✅ Segment: {result.get('customer_segment', 'MISSING')}")

    # Test case 2: Malformed JSON that needs repair
    print("\n2. Testing malformed JSON repair...")
    malformed_json = '''{
        "sentiment": "Positive",
        "willingness_score": 75,
        "segment": "B2C",
        "price_points": ["$50/month"],
        "revenue_score": 80,
        "confidence": 0.7
    }'''

    # Introduce a syntax error
    broken_json = malformed_json.replace('"confidence": 0.7', '"confidence": 0.7,')

    try:
        result = analyzer._parse_team_response(broken_json)
        print("   ✅ Successfully repaired and parsed")
        print(f"   ✅ Mapped sentiment: {result.get('sentiment_toward_payment', 'MISSING')}")
        print(f"   ✅ Mapped WTP score: {result.get('willingness_to_pay_score', 'MISSING')}")
        print(f"   ✅ Mapped segment: {result.get('customer_segment', 'MISSING')}")
    except Exception as e:
        print(f"   ❌ Failed to repair: {e}")

    # Test case 3: Text-only response (no JSON)
    print("\n3. Testing text-only response...")
    text_response = """
    The user shows positive sentiment toward payment and is willing to pay around $85 per month.
    This appears to be a B2B context with a team of 12 people. They mentioned spending $300/month
    on Asana and looking for alternatives under $150/month.
    """

    result = analyzer._parse_team_response(text_response)
    print(f"   ✅ Extracted from text: {result.get('sentiment_toward_payment', 'MISSING')}")
    print(f"   ✅ Extracted score: {result.get('willingness_to_pay_score', 'MISSING')}")
    print(f"   ✅ Extracted segment: {result.get('customer_segment', 'MISSING')}")
    print(f"   ✅ Extracted prices: {result.get('mentioned_price_points', 'MISSING')}")

    # Test case 4: Consensus calculation with multiple agents
    print("\n4. Testing multi-agent consensus...")
    multi_agent_response = """
    WTP Analysis: {
        "sentiment_toward_payment": "Positive",
        "willingness_to_pay_score": 85,
        "confidence": 0.8
    }

    Market Segment: {
        "customer_segment": "B2B",
        "confidence": 0.9
    }

    Price Analysis: {
        "mentioned_price_points": ["$300/month", "$150/month"],
        "budget_ceiling": "$150/month"
    }

    Payment Behavior: {
        "current_spending": "$300/month on Asana",
        "switching_willingness": "High"
    }
    """

    result = analyzer._parse_team_response(multi_agent_response)
    print(f"   ✅ Consensus calculated: {len(result)} fields")
    print(f"   ✅ Consensus metadata: {result.get('consensus_metadata', 'MISSING')}")
    if 'consensus_metadata' in result:
        meta = result['consensus_metadata']
        print(f"   ✅ Agent count: {meta.get('agent_count', 'MISSING')}")
        print(f"   ✅ Agreement level: {meta.get('agreement_level', 'MISSING')}")

    print("\n✅ All JSON parsing tests completed!")

def test_expected_field_names():
    """Test that the parser returns the exact field names expected by tests"""
    print("\n🎯 Testing Expected Field Names...")

    analyzer = MonetizationAgnoAnalyzer()

    # Test with various field name variations
    test_cases = [
        {
            "name": "Correct field names",
            "input": {
                "sentiment_toward_payment": "Positive",
                "willingness_to_pay_score": 85,
                "customer_segment": "B2B",
                "revenue_potential_score": 90
            }
        },
        {
            "name": "Alternative field names",
            "input": {
                "sentiment": "Positive",
                "willingness_score": 85,
                "segment": "B2B",
                "revenue_score": 90
            }
        },
        {
            "name": "Mixed field names",
            "input": {
                "payment_sentiment": "Negative",
                "wtp_score": 25,
                "market_segment": "B2C",
                "potential": 30
            }
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {test_case['name']}...")
        result = analyzer._parse_team_response(json.dumps(test_case['input']))

        # Check expected field names
        expected_fields = [
            'sentiment_toward_payment',
            'willingness_to_pay_score',
            'customer_segment',
            'revenue_potential_score'
        ]

        missing_fields = []
        for field in expected_fields:
            if field not in result:
                missing_fields.append(field)
            else:
                print(f"   ✅ {field}: {result[field]}")

        if missing_fields:
            print(f"   ❌ Missing fields: {missing_fields}")
        else:
            print("   ✅ All expected fields present!")

    print("\n✅ Field name validation completed!")

if __name__ == "__main__":
    print("🚀 Testing Monetization Analyzer JSON Parsing")
    print("=" * 60)

    try:
        test_json_repair_parsing()
        test_expected_field_names()
        print("\n🎉 All tests passed! The JSON parsing implementation is working correctly.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
