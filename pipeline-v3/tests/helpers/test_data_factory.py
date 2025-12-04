"""
Test data factory for generating test data sets
"""

import json
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid


class RedditSubmissionFactory:
    """Factory for creating Reddit submission test data"""

    @staticmethod
    def create_high_wtp_b2b() -> Dict[str, Any]:
        """Create high willingness-to-pay B2B submission"""
        return {
            "submission_id": f"sub_{uuid.uuid4().hex[:8]}",
            "title": "CRM solution needed for growing team",
            "text": "We're currently using spreadsheets and need a proper CRM solution. Budget approved for $10k-15k. Need implementation by Q2. Team of 50 people. Looking for enterprise-grade solution with reporting and analytics capabilities.",
            "subreddit": "startups",
            "score": random.randint(40, 80),
            "num_comments": random.randint(15, 40),
            "author": f"business_{uuid.uuid4().hex[:4]}",
            "created_utc": datetime.now().isoformat(),
            "trust_score": random.randint(70, 90),
            "trust_badge": "Trusted"
        }

    @staticmethod
    def create_low_wtp_b2c() -> Dict[str, Any]:
        """Create low willingness-to-pay B2C submission"""
        return {
            "submission_id": f"sub_{uuid.uuid4().hex[:8]}",
            "title": "NOT paying for another fitness app",
            "text": "Too many subscriptions already. Looking for free alternatives to MyFitnessPal that work offline and don't require premium features. Budget is tight and I'm not willing to pay for basic functionality.",
            "subreddit": "fitness",
            "score": random.randint(5, 30),
            "num_comments": random.randint(5, 20),
            "author": f"fitness_{uuid.uuid4().hex[:4]}",
            "created_utc": datetime.now().isoformat(),
            "trust_score": random.randint(40, 60),
            "trust_badge": "New"
        }

    @staticmethod
    def create_mixed_segment() -> Dict[str, Any]:
        """Create mixed B2B/B2C segment submission"""
        return {
            "submission_id": f"sub_{uuid.uuid4().hex[:8]}",
            "title": "Project management for small team + personal use",
            "text": "Need a tool that works for both my team of 5 and personal projects. Monthly budget around $50. Looking for something with team collaboration features but also works well for individual task management.",
            "subreddit": "productivity",
            "score": random.randint(20, 50),
            "num_comments": random.randint(10, 30),
            "author": f"freelancer_{uuid.uuid4().hex[:4]}",
            "created_utc": datetime.now().isoformat(),
            "trust_score": random.randint(60, 80),
            "trust_badge": "Trusted"
        }

    @staticmethod
    def create_urgent_needs() -> Dict[str, Any]:
        """Create urgent needs submission"""
        return {
            "submission_id": f"sub_{uuid.uuid4().hex[:8]}",
            "title": "URGENT: Need accounting software by end of month",
            "text": "Tax deadline approaching fast! Need accounting software ASAP. Budget up to $200/month. Must have tax preparation features and integration with bank accounts. Need to decide by end of month.",
            "subreddit": "smallbusiness",
            "score": random.randint(30, 60),
            "num_comments": random.randint(20, 50),
            "author": f"business_owner_{uuid.uuid4().hex[:4]}",
            "created_utc": datetime.now().isoformat(),
            "trust_score": random.randint(70, 90),
            "trust_badge": "Verified"
        }

    @staticmethod
    def create_price_sensitive() -> Dict[str, Any]:
        """Create price-sensitive submission"""
        return {
            "submission_id": f"sub_{uuid.uuid4().hex[:8]}",
            "title": "Looking for affordable design tool alternatives",
            "text": "Currently paying $99/month for Adobe Creative Cloud. Too expensive for freelance work. Looking for alternatives under $30/month that can handle basic design tasks. Need vector editing and basic image manipulation.",
            "subreddit": "design",
            "score": random.randint(25, 55),
            "num_comments": random.randint(15, 35),
            "author": f"designer_{uuid.uuid4().hex[:4]}",
            "created_utc": datetime.now().isoformat(),
            "trust_score": random.randint(50, 70),
            "trust_badge": "Trusted"
        }

    @staticmethod
    def create_enterprise_needs() -> Dict[str, Any]:
        """Create enterprise-level needs submission"""
        return {
            "submission_id": f"sub_{uuid.uuid4().hex[:8]}",
            "title": "Enterprise security platform for 5000+ employees",
            "text": "Fortune 500 company needs comprehensive security platform. Budget approved: $500k-1M annually. Requirements include SSO, MFA, threat detection, and compliance reporting. Need vendor proposals by next quarter.",
            "subreddit": " cybersecurity",
            "score": random.randint(60, 100),
            "num_comments": random.randint(30, 80),
            "author": f"cto_{uuid.uuid4().hex[:4]}",
            "created_utc": datetime.now().isoformat(),
            "trust_score": random.randint(80, 100),
            "trust_badge": "Verified"
        }

    @staticmethod
    def create_batch_submissions(count: int, mix: Dict[str, int] = None) -> List[Dict[str, Any]]:
        """Create batch of submissions with specified mix"""
        if mix is None:
            mix = {
                "high_wtp_b2b": 20,
                "low_wtp_b2c": 20,
                "mixed_segment": 20,
                "urgent_needs": 15,
                "price_sensitive": 15,
                "enterprise_needs": 10
            }

        submissions = []
        categories = []
        for category, count in mix.items():
            categories.extend([category] * count)

        random.shuffle(categories)

        for category in categories:
            if category == "high_wtp_b2b":
                submissions.append(RedditSubmissionFactory.create_high_wtp_b2b())
            elif category == "low_wtp_b2c":
                submissions.append(RedditSubmissionFactory.create_low_wtp_b2c())
            elif category == "mixed_segment":
                submissions.append(RedditSubmissionFactory.create_mixed_segment())
            elif category == "urgent_needs":
                submissions.append(RedditSubmissionFactory.create_urgent_needs())
            elif category == "price_sensitive":
                submissions.append(RedditSubmissionFactory.create_price_sensitive())
            elif category == "enterprise_needs":
                submissions.append(RedditSubmissionFactory.create_enterprise_needs())

        return submissions


class AgentResponseFactory:
    """Factory for creating mock agent responses"""

    @staticmethod
    def create_wtp_variations() -> List[Dict[str, Any]]:
        """Create various WTP agent responses"""
        return [
            {
                "sentiment_toward_payment": "Positive",
                "willingness_to_pay_score": 85,
                "evidence": ["budget approved", "clear timeline"],
                "reasoning": "Strong positive sentiment with budget approval and clear timeline"
            },
            {
                "sentiment_toward_payment": "Neutral",
                "willingness_to_pay_score": 60,
                "evidence": ["considering options", "price conscious"],
                "reasoning": "Neutral sentiment, considering options but price conscious"
            },
            {
                "sentiment_toward_payment": "Negative",
                "willingness_to_pay_score": 25,
                "evidence": ["not willing", "too expensive"],
                "reasoning": "Explicit unwillingness to pay, citing cost concerns"
            },
            {
                "sentiment_toward_payment": "Positive",
                "willingness_to_pay_score": 95,
                "evidence": ["enterprise budget", "urgent need"],
                "reasoning": "Very high willingness with enterprise budget and urgent need"
            }
        ]

    @staticmethod
    def create_segment_variations() -> List[Dict[str, Any]]:
        """Create various segment agent responses"""
        return [
            {
                "customer_segment": "B2B",
                "confidence": 0.9,
                "indicators": ["team", "budget", "implementation"],
                "segment_score": 95
            },
            {
                "customer_segment": "B2C",
                "confidence": 0.8,
                "indicators": ["personal", "individual", "hobby"],
                "segment_score": 85
            },
            {
                "customer_segment": "Mixed",
                "confidence": 0.7,
                "indicators": ["both business and personal use"],
                "segment_score": 75
            },
            {
                "customer_segment": "Unknown",
                "confidence": 0.5,
                "indicators": ["unclear context"],
                "segment_score": 50
            }
        ]

    @staticmethod
    def create_price_variations() -> List[Dict[str, Any]]:
        """Create various price agent responses"""
        return [
            {
                "mentioned_price_points": [
                    {"price": "$100/month", "context": "current spending"},
                    {"price": "$500/month", "context": "target budget"}
                ],
                "budget_ceiling": "$500/month",
                "pricing_model": "Subscription"
            },
            {
                "mentioned_price_points": [
                    {"price": "$99/year", "context": "competitor pricing"}
                ],
                "budget_ceiling": "$150/year",
                "pricing_model": "Annual"
            },
            {
                "mentioned_price_points": [
                    {"price": "$5000", "context": "one-time fee"},
                    {"price": "$200/month", "context": "maintenance"}
                ],
                "budget_ceiling": "$7500",
                "pricing_model": "Hybrid"
            },
            {
                "mentioned_price_points": [],
                "budget_ceiling": "Unknown",
                "pricing_model": "Undetermined"
            }
        ]

    @staticmethod
    def create_behavior_variations() -> List[Dict[str, Any]]:
        """Create various behavior agent responses"""
        return [
            {
                "current_spending": "$300/month on Salesforce",
                "switching_willingness": "High",
                "spending_evidence": ["pain points with current solution"],
                "behavior_score": 80
            },
            {
                "current_spending": "No current spending",
                "switching_willingness": "Medium",
                "spending_evidence": ["new to category"],
                "behavior_score": 60
            },
            {
                "current_spending": "$50/month on multiple tools",
                "switching_willingness": "Low",
                "spending_evidence": ["subscription fatigue", "loyalty to current provider"],
                "behavior_score": 40
            },
            {
                "current_spending": "$2000/month on enterprise suite",
                "switching_willingness": "Medium",
                "spending_evidence": ["evaluating alternatives"],
                "behavior_score": 70
            }
        ]

    @staticmethod
    def create_consensus_scenarios() -> List[Dict[str, Any]]:
        """Create consensus calculation scenarios"""
        return [
            {
                "name": "high_agreement",
                "wtp_scores": [80, 85, 82],
                "segments": ["B2B", "B2B", "B2B"],
                "expected_confidence": 0.9,
                "expected_agreement": "high"
            },
            {
                "name": "medium_agreement",
                "wtp_scores": [70, 80, 85],
                "segments": ["B2B", "B2B", "B2C"],
                "expected_confidence": 0.75,
                "expected_agreement": "medium"
            },
            {
                "name": "low_agreement",
                "wtp_scores": [50, 80, 95],
                "segments": ["B2C", "B2B", "Enterprise"],
                "expected_confidence": 0.6,
                "expected_agreement": "low"
            },
            {
                "name": "outlier_present",
                "wtp_scores": [75, 78, 30],  # 30 is an outlier
                "segments": ["B2B", "B2B", "B2C"],
                "expected_confidence": 0.75,
                "expected_agreement": "medium"
            }
        ]


class ErrorScenarioFactory:
    """Factory for creating error scenarios"""

    @staticmethod
    def create_json_parse_error() -> str:
        """Create malformed JSON response"""
        return '''{
            "sentiment": "Positive",
            "willingness_to_pay_score": 85,
            "evidence": ["test evidence"
            // Missing closing brace and quotes
        '''

    @staticmethod
    def create_empty_response() -> str:
        """Create empty response"""
        return ""

    @staticmethod
    def create_partial_json() -> str:
        """Create partial JSON response"""
        return '{"willingness_to_pay_score": 75, '

    @staticmethod
    def create_non_json_response() -> str:
        """Create non-JSON response"""
        return "This is a text response without any JSON structure"

    @staticmethod
    def create_inconsistent_fields() -> str:
        """Create response with inconsistent field names"""
        return '''{
            "sentiment": "Positive",
            "wtp_score": 85,
            "segment": "B2B",
            "prices": ["$100/month"],
            "payment_behavior": "$200/month"
        }'''

    @staticmethod
    def create_missing_required_fields() -> str:
        """Create response missing required fields"""
        return '''{
            "some_field": "value"
        }'''

    @staticmethod
    def create_invalid_score_values() -> str:
        """Create response with invalid score values"""
        return '''{
            "sentiment_toward_payment": "Positive",
            "willingness_to_pay_score": 150,  // Invalid score
            "customer_segment": "B2B"
        }'''


class PerformanceDataFactory:
    """Factory for creating performance test data"""

    @staticmethod
    def create_large_batch(size: int = 1000) -> List[Dict[str, Any]]:
        """Create large batch for performance testing"""
        return RedditSubmissionFactory.create_batch_submissions(
            size,
            mix={
                "high_wtp_b2b": size // 3,
                "low_wtp_b2c": size // 3,
                "mixed_segment": size // 3
            }
        )

    @staticmethod
    def create_edge_case_submissions() -> List[Dict[str, Any]]:
        """Create edge case submissions"""
        edge_cases = [
            # Very long text
            {
                "submission_id": "edge_long",
                "title": "Very Long Title " * 10,
                "text": "Very long text content. " * 100,
                "subreddit": "test",
                "score": 0,
                "num_comments": 0,
                "author": "test_user"
            },
            # Very short text
            {
                "submission_id": "edge_short",
                "title": "Short",
                "text": "Need help.",
                "subreddit": "test",
                "score": 1,
                "num_comments": 0,
                "author": "test_user"
            },
            # Empty text
            {
                "submission_id": "edge_empty",
                "title": "Empty post",
                "text": "",
                "subreddit": "test",
                "score": 0,
                "num_comments": 0,
                "author": "test_user"
            },
            # Special characters
            {
                "submission_id": "edge_special",
                "title": "Special chars: áéíóú ñ ¿?",
                "text": "Text with special characters: áéíóú ñ ¿? $100,000+ 🚀",
                "subreddit": "test",
                "score": 5,
                "num_comments": 0,
                "author": "test_user"
            }
        ]

        return edge_cases

    @staticmethod
    def create_concurrent_test_scenarios() -> List[Dict[str, Any]]:
        """Create concurrent test scenarios"""
        return [
            {"batches": 1, "batch_size": 10, "concurrent": True},
            {"batches": 5, "batch_size": 20, "concurrent": True},
            {"batches": 10, "batch_size": 50, "concurrent": True},
            {"batches": 20, "batch_size": 100, "concurrent": True},
            {"batches": 50, "batch_size": 200, "concurrent": True}
        ]

    @staticmethod
    def create_memory_test_data() -> List[Dict[str, Any]]:
        """Create data for memory testing"""
        # Create data with varying memory footprints
        datasets = []

        # Small dataset
        small_data = RedditSubmissionFactory.create_batch_submissions(10)
        datasets.append({"name": "small", "data": small_data, "expected_memory_mb": 1})

        # Medium dataset
        medium_data = RedditSubmissionFactory.create_batch_submissions(100)
        datasets.append({"name": "medium", "data": medium_data, "expected_memory_mb": 10})

        # Large dataset
        large_data = RedditSubmissionFactory.create_batch_submissions(1000)
        datasets.append({"name": "large", "data": large_data, "expected_memory_mb": 100})

        return datasets


class TestDatasetGenerator:
    """Main test dataset generator"""

    @staticmethod
    def generate_complete_test_dataset() -> Dict[str, Any]:
        """Generate complete test dataset"""
        return {
            "submissions": {
                "high_wtp_b2b": [RedditSubmissionFactory.create_high_wtp_b2b() for _ in range(10)],
                "low_wtp_b2c": [RedditSubmissionFactory.create_low_wtp_b2c() for _ in range(10)],
                "mixed_segment": [RedditSubmissionFactory.create_mixed_segment() for _ in range(10)],
                "urgent_needs": [RedditSubmissionFactory.create_urgent_needs() for _ in range(5)],
                "price_sensitive": [RedditSubmissionFactory.create_price_sensitive() for _ in range(5)],
                "enterprise_needs": [RedditSubmissionFactory.create_enterprise_needs() for _ in range(3)]
            },
            "agent_responses": {
                "wtp": AgentResponseFactory.create_wtp_variations(),
                "segment": AgentResponseFactory.create_segment_variations(),
                "price": AgentResponseFactory.create_price_variations(),
                "behavior": AgentResponseFactory.create_behavior_variations()
            },
            "error_scenarios": {
                "json_parse_error": ErrorScenarioFactory.create_json_parse_error(),
                "empty_response": ErrorScenarioFactory.create_empty_response(),
                "partial_json": ErrorScenarioFactory.create_partial_json(),
                "non_json_response": ErrorScenarioFactory.create_non_json_response(),
                "inconsistent_fields": ErrorScenarioFactory.create_inconsistent_fields(),
                "missing_required_fields": ErrorScenarioFactory.create_missing_required_fields(),
                "invalid_score_values": ErrorScenarioFactory.create_invalid_score_values()
            },
            "performance_data": {
                "small_batch": PerformanceDataFactory.create_large_batch(10),
                "medium_batch": PerformanceDataFactory.create_large_batch(100),
                "large_batch": PerformanceDataFactory.create_large_batch(1000),
                "edge_cases": PerformanceDataFactory.create_edge_case_submissions()
            },
            "consensus_scenarios": AgentResponseFactory.create_consensus_scenarios()
        }

    @staticmethod
    def save_test_dataset(filepath: str, dataset: Dict[str, Any]):
        """Save test dataset to file"""
        with open(filepath, 'w') as f:
            json.dump(dataset, f, indent=2, default=str)

    @staticmethod
    def load_test_dataset(filepath: str) -> Dict[str, Any]:
        """Load test dataset from file"""
        with open(filepath, 'r') as f:
            return json.load(f)