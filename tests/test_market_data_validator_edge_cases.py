#!/usr/bin/env python3
"""
Unit tests for MarketDataValidator edge cases and error handling.

Tests:
- Malformed JSON handling
- Empty/null responses
- Partial data recovery
- Query sanitization
- Extraction metrics tracking
- Retry logic
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent_tools.jina_reader_client import JinaResponse  # noqa: E402
from agent_tools.market_data_validator import MarketDataValidator  # noqa: E402


class TestJSONParsing:
    """Tests for JSON parsing robustness"""

    @pytest.fixture
    def validator(self):
        """Create a validator with mocked Jina client"""
        mock_client = Mock()
        return MarketDataValidator(jina_client=mock_client)

    def test_clean_json_with_markdown_code_block(self, validator):
        """Test removing markdown code blocks"""
        content = """```json
{
    "company_name": "Test Corp",
    "pricing_model": "subscription"
}
```"""
        cleaned = validator._clean_json_response(content)
        assert cleaned.startswith("{")
        assert cleaned.endswith("}")
        assert "```" not in cleaned

    def test_clean_json_with_text_before_json(self, validator):
        """Test extracting JSON when preceded by text"""
        content = """Here is the pricing information:
{
    "company_name": "Test Corp",
    "pricing_model": "subscription"
}"""
        cleaned = validator._clean_json_response(content)
        assert cleaned.startswith("{")
        assert "company_name" in cleaned

    def test_clean_json_with_text_after_json(self, validator):
        """Test extracting JSON when followed by extra content"""
        content = """{
    "company_name": "Test Corp",
    "pricing_model": "subscription"
}

I hope this helps! Let me know if you need more information."""
        cleaned = validator._clean_json_response(content)
        assert cleaned.endswith("}")
        assert "hope this helps" not in cleaned

    def test_clean_json_with_nested_braces(self, validator):
        """Test handling JSON with nested objects"""
        content = """{
    "company_name": "Test Corp",
    "pricing_tiers": [
        {
            "tier": "Basic",
            "price": "$10/month",
            "features": ["feature1", "feature2"]
        },
        {
            "tier": "Pro",
            "price": "$25/month"
        }
    ]
}

Extra text here"""
        cleaned = validator._clean_json_response(content)
        # Should find the correct closing brace
        assert cleaned.endswith("}")
        assert "Extra text" not in cleaned
        # Verify it's valid JSON
        import json

        data = json.loads(cleaned)
        assert len(data["pricing_tiers"]) == 2

    def test_clean_json_with_trailing_comma(self, validator):
        """Test fixing trailing commas"""
        content = """{
    "company_name": "Test Corp",
    "pricing_tiers": [
        {"tier": "Basic", "price": "$10",},
    ],
}"""
        cleaned = validator._clean_json_response(content)
        # Should remove trailing commas
        assert ",}" not in cleaned
        assert ",]" not in cleaned

    def test_clean_json_empty_content(self, validator):
        """Test handling empty content"""
        cleaned = validator._clean_json_response("")
        assert cleaned == "{}"

    def test_clean_json_no_json_object(self, validator):
        """Test handling content with no JSON"""
        content = "This is just plain text with no JSON at all."
        cleaned = validator._clean_json_response(content)
        assert cleaned == "{}"

    def test_clean_json_with_json_language_tag(self, validator):
        """Test removing json language identifier"""
        content = """json
{
    "company_name": "Test"
}"""
        cleaned = validator._clean_json_response(content)
        assert not cleaned.startswith("json")
        assert cleaned.startswith("{")


class TestPartialDataRecovery:
    """Tests for partial JSON recovery from malformed responses"""

    @pytest.fixture
    def validator(self):
        """Create a validator instance"""
        mock_client = Mock()
        return MarketDataValidator(jina_client=mock_client)

    def test_recover_company_name_only(self, validator):
        """Test recovering just company name from malformed JSON"""
        malformed = """{
    "company_name": "Acme Corp",
    "pricing_model": "subscription"
    // This comment breaks JSON
}"""
        recovered = validator._attempt_partial_json_recovery(malformed)
        assert recovered is not None
        assert recovered["company_name"] == "Acme Corp"
        assert recovered["pricing_model"] == "subscription"

    def test_recover_pricing_tier(self, validator):
        """Test recovering pricing tier from malformed JSON"""
        malformed = """{
    "company_name": "TestCo",
    "pricing_tiers": [
        {
            "tier": "Professional",
            "price": "$49.99/month"
            invalid json here
        }
    ]
}"""
        recovered = validator._attempt_partial_json_recovery(malformed)
        assert recovered is not None
        assert recovered["company_name"] == "TestCo"
        assert len(recovered["pricing_tiers"]) == 1
        assert recovered["pricing_tiers"][0]["tier"] == "Professional"
        assert recovered["pricing_tiers"][0]["price"] == "$49.99/month"

    def test_recovery_fails_without_company_name(self, validator):
        """Test that recovery returns None without company name"""
        malformed = """{
    "pricing_model": "subscription",
    "target_market": "B2C"
}"""
        recovered = validator._attempt_partial_json_recovery(malformed)
        # Should be None because company_name is missing
        assert recovered is None

    def test_recover_all_fields(self, validator):
        """Test recovering multiple fields"""
        malformed = """
        "company_name": "Example Inc",
        "pricing_model": "freemium",
        "target_market": "B2B",
        this is not valid JSON but fields are extractable
        """
        recovered = validator._attempt_partial_json_recovery(malformed)
        assert recovered is not None
        assert recovered["company_name"] == "Example Inc"
        assert recovered["pricing_model"] == "freemium"
        assert recovered["target_market"] == "B2B"


class TestQuerySanitization:
    """Tests for search query sanitization"""

    @pytest.fixture
    def validator(self):
        """Create a validator instance"""
        mock_client = Mock()
        return MarketDataValidator(jina_client=mock_client)

    def test_sanitize_removes_special_characters(self, validator):
        """Test that special characters are removed"""
        query = 'expense "tracking" app (with AI)'
        sanitized = validator._sanitize_search_query(query)
        assert '"' not in sanitized
        assert "(" not in sanitized
        assert ")" not in sanitized
        assert "expense" in sanitized
        assert "tracking" in sanitized

    def test_sanitize_removes_operators(self, validator):
        """Test that logical operators are removed"""
        query = "app & tool | software"
        sanitized = validator._sanitize_search_query(query)
        assert "&" not in sanitized
        assert "|" not in sanitized

    def test_sanitize_limits_query_length(self, validator):
        """Test that very long queries are truncated"""
        query = " ".join(["word"] * 20)
        sanitized = validator._sanitize_search_query(query)
        words = sanitized.split()
        assert len(words) <= 10

    def test_sanitize_removes_short_words(self, validator):
        """Test that very short words are removed"""
        query = "a an is of expense tracking"
        sanitized = validator._sanitize_search_query(query)
        assert "expense" in sanitized
        assert "tracking" in sanitized
        # Short words should be filtered out
        words = sanitized.split()
        assert all(len(w) > 2 for w in words)

    def test_sanitize_preserves_meaningful_short_words(self, validator):
        """Test that meaningful short words like AI are preserved"""
        query = "AI ML app development"
        sanitized = validator._sanitize_search_query(query)
        assert "AI" in sanitized or "ai" in sanitized
        assert "ML" in sanitized or "ml" in sanitized

    def test_sanitize_empty_query(self, validator):
        """Test handling empty query"""
        sanitized = validator._sanitize_search_query("")
        assert sanitized == ""

    def test_sanitize_handles_multiple_spaces(self, validator):
        """Test that multiple spaces are normalized"""
        query = "expense    tracking      app"
        sanitized = validator._sanitize_search_query(query)
        assert "  " not in sanitized


class TestExtractionMetrics:
    """Tests for extraction statistics tracking"""

    @pytest.fixture
    def validator(self):
        """Create a validator with fresh stats"""
        mock_client = Mock()
        return MarketDataValidator(jina_client=mock_client)

    def test_initial_stats_are_zero(self, validator):
        """Test that stats start at zero"""
        stats = validator.get_extraction_stats()
        assert stats["json_parse_errors"] == 0
        assert stats["json_parse_successes"] == 0
        assert stats["search_failures"] == 0
        assert stats["successful_extractions"] == 0

    def test_stats_include_success_rate(self, validator):
        """Test that success rate is calculated"""
        validator._extraction_stats["successful_extractions"] = 8
        validator._extraction_stats["failed_extractions"] = 2

        stats = validator.get_extraction_stats()
        assert stats["success_rate"] == 80.0

    def test_stats_include_json_success_rate(self, validator):
        """Test JSON parse success rate calculation"""
        validator._extraction_stats["json_parse_successes"] = 9
        validator._extraction_stats["json_parse_errors"] = 1

        stats = validator.get_extraction_stats()
        assert stats["json_success_rate"] == 90.0

    def test_reset_stats(self, validator):
        """Test that stats can be reset"""
        validator._extraction_stats["json_parse_errors"] = 5
        validator._extraction_stats["successful_extractions"] = 10

        validator.reset_extraction_stats()

        stats = validator.get_extraction_stats()
        assert stats["json_parse_errors"] == 0
        assert stats["successful_extractions"] == 0

    def test_stats_zero_division_handling(self, validator):
        """Test that zero division is handled gracefully"""
        stats = validator.get_extraction_stats()
        assert stats["success_rate"] == 0.0
        assert stats["json_success_rate"] == 0.0


class TestTitleExtraction:
    """Tests for title extraction from Jina responses"""

    @pytest.fixture
    def client(self):
        """Create a JinaReaderClient"""
        from agent_tools.jina_reader_client import JinaReaderClient

        return JinaReaderClient()

    def test_extract_title_from_title_prefix(self, client):
        """Test extracting title from 'Title:' format"""
        content = """Title: Best Expense Tracking Apps 2024

URL Source: https://example.com

Main content here..."""
        title = client._extract_title_from_content(content)
        assert title == "Best Expense Tracking Apps 2024"

    def test_extract_title_from_markdown_header(self, client):
        """Test extracting title from markdown header"""
        content = """# Personal Finance Software Guide

This guide covers the best options..."""
        title = client._extract_title_from_content(content)
        assert title == "Personal Finance Software Guide"

    def test_extract_title_from_h2_header(self, client):
        """Test extracting title from H2 header when no H1"""
        content = """Some preamble text

## Product Pricing Overview

Details here..."""
        title = client._extract_title_from_content(content)
        assert title == "Product Pricing Overview"

    def test_no_title_found(self, client):
        """Test handling content with no recognizable title"""
        content = """Just plain text content without any headers or title markers.

More content here."""
        title = client._extract_title_from_content(content)
        assert title is None

    def test_empty_content(self, client):
        """Test handling empty content"""
        title = client._extract_title_from_content("")
        assert title is None

    def test_title_in_middle_of_document(self, client):
        """Test finding title even if not in first line"""
        content = """
Some metadata

Title: The Actual Page Title

Content starts here"""
        title = client._extract_title_from_content(content)
        assert title == "The Actual Page Title"


class TestRetryLogic:
    """Tests for extraction retry behavior"""

    @pytest.fixture
    def mock_jina_client(self):
        """Create a mock Jina client"""
        mock = Mock()
        mock.read_url = Mock(
            return_value=JinaResponse(
                content="Test pricing page content with pricing information",
                url="https://example.com/pricing",
                word_count=100,
            )
        )
        return mock

    @patch("agent_tools.market_data_validator.litellm")
    def test_retry_on_json_parse_error(self, mock_litellm, mock_jina_client):
        """Test that extraction retries with simplified prompt on JSON error"""
        validator = MarketDataValidator(jina_client=mock_jina_client)

        # First call returns malformed JSON, second call returns valid JSON
        first_response = Mock()
        first_response.choices = [Mock(message=Mock(content="{ invalid json here }}"))]
        first_response.usage = Mock(total_tokens=100)

        second_response = Mock()
        second_response.choices = [
            Mock(
                message=Mock(
                    content="""{
            "company_name": "Test Corp",
            "pricing_model": "subscription",
            "pricing_tiers": [],
            "confidence": 0.5
        }"""
                )
            )
        ]
        second_response.usage = Mock(total_tokens=80)

        mock_litellm.completion.side_effect = [first_response, second_response]

        validator._extract_competitor_pricing(
            "https://example.com/pricing", "test app"
        )

        # Should have retried
        assert mock_litellm.completion.call_count == 2
        assert validator._extraction_stats["extraction_retries"] >= 1
        # Should have tracked JSON error
        assert validator._extraction_stats["json_parse_errors"] >= 1

    @patch("agent_tools.market_data_validator.litellm")
    def test_partial_recovery_after_all_retries_fail(
        self, mock_litellm, mock_jina_client
    ):
        """Test partial recovery when all retry attempts fail"""
        validator = MarketDataValidator(jina_client=mock_jina_client)

        # Both attempts return parseable but malformed JSON
        malformed_response = Mock()
        malformed_response.choices = [
            Mock(
                message=Mock(
                    content="""
        {
            "company_name": "Partial Corp",
            "pricing_model": "freemium",
            "pricing_tiers": [
                {"tier": "Free", "price": "$0"
            ]
        }
        Some extra text that breaks parsing
        """
                )
            )
        ]
        malformed_response.usage = Mock(total_tokens=100)

        mock_litellm.completion.return_value = malformed_response

        validator._extract_competitor_pricing(
            "https://example.com/pricing", "test app"
        )

        # Should track JSON errors
        assert validator._extraction_stats["json_parse_errors"] >= 1


class TestEmptyAndNullResponses:
    """Tests for handling empty or null responses"""

    @pytest.fixture
    def validator(self):
        """Create a validator instance"""
        mock_client = Mock()
        return MarketDataValidator(jina_client=mock_client)

    def test_short_content_rejected(self, validator):
        """Test that pages with too little content are rejected"""
        mock_response = JinaResponse(
            content="Short", url="https://example.com", word_count=1
        )
        validator.jina_client.read_url.return_value = mock_response

        result = validator._extract_competitor_pricing("https://example.com", "test")
        assert result is None
        assert validator._extraction_stats["failed_extractions"] >= 1

    def test_clean_json_handles_none_like_values(self, validator):
        """Test cleaning JSON with null values"""
        content = """{
            "company_name": "Test",
            "tam_value": null,
            "sam_value": null,
            "growth_rate": null
        }"""
        cleaned = validator._clean_json_response(content)
        import json

        data = json.loads(cleaned)
        assert data["tam_value"] is None

    def test_empty_pricing_tiers(self, validator):
        """Test handling empty pricing tiers array"""
        content = """{
            "company_name": "No Pricing Corp",
            "pricing_model": "unknown",
            "pricing_tiers": []
        }"""
        cleaned = validator._clean_json_response(content)
        import json

        data = json.loads(cleaned)
        assert data["pricing_tiers"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
