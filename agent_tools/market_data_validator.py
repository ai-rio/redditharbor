#!/usr/bin/env python3
"""
Market Data Validator for Data-Driven Monetization Analysis

This module provides real market data validation to support monetization potential
scoring with actual evidence instead of LLM opinions.

Features:
- Competitor pricing analysis from real pricing pages
- Market size estimation from industry reports
- Similar product launch success metrics
- Industry benchmark data
- Evidence-based validation scores with citations
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

import litellm

from agent_tools.jina_hybrid_client import JinaHybridClient, get_jina_hybrid_client
from agent_tools.jina_reader_client import JinaReaderClient, get_jina_client
from config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================


@dataclass
class CompetitorPricing:
    """Extracted competitor pricing information"""

    company_name: str
    pricing_tiers: list[dict]  # [{tier: "Basic", price: "$9.99/mo", features: [...]}]
    pricing_model: str  # subscription, freemium, one-time, usage-based
    target_market: str  # B2B, B2C, Enterprise, SMB
    source_url: str
    extracted_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    confidence: float = 0.0  # 0-1


@dataclass
class MarketSizeData:
    """Market size and growth information"""

    tam_value: str | None = None  # "$50B"
    sam_value: str | None = None  # "$10B"
    som_value: str | None = None  # "$1B"
    growth_rate: str | None = None  # "15% CAGR"
    year: int = 2024
    source_url: str = ""
    source_name: str = ""  # e.g., "Grand View Research"
    confidence: float = 0.0  # 0-1


@dataclass
class ProductLaunchData:
    """Product launch success metrics"""

    product_name: str
    launch_platform: str  # Product Hunt, etc.
    upvotes: int | None = None
    rank: str | None = None  # "#1 Product of the Day"
    funding_raised: str | None = None
    user_count: str | None = None
    source_url: str = ""
    launch_date: str | None = None


@dataclass
class ValidationEvidence:
    """Consolidated market validation evidence"""

    competitor_pricing: list[CompetitorPricing] = field(default_factory=list)
    market_size: MarketSizeData | None = None
    similar_launches: list[ProductLaunchData] = field(default_factory=list)
    industry_benchmarks: dict = field(default_factory=dict)
    validation_score: float = 0.0  # 0-100
    data_quality_score: float = 0.0  # 0-100
    reasoning: str = ""
    search_queries_used: list[str] = field(default_factory=list)
    urls_fetched: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    total_cost: float = 0.0  # LLM cost for extraction


# =============================================================================
# MARKET DATA VALIDATOR
# =============================================================================


class MarketDataValidator:
    """
    Validates monetization potential using real market data.

    This validator:
    1. Identifies competitors based on app concept
    2. Extracts pricing information from competitor websites
    3. Searches for market size data
    4. Finds similar product launches for benchmarking
    5. Synthesizes evidence into validation scores
    """

    def __init__(self, jina_client: JinaReaderClient | JinaHybridClient | None = None, enable_mcp_experimental: bool = False):
        """
        Initialize the MarketDataValidator.

        Args:
            jina_client: Optional JinaReaderClient or JinaHybridClient instance.
                        If not provided, uses the hybrid client with direct HTTP primary.
            enable_mcp_experimental: Whether to enable experimental MCP features in hybrid client
        """
        if jina_client is None:
            # Use hybrid client by default for better reliability and future MCP support
            try:
                self.jina_client = get_jina_hybrid_client(enable_mcp_experimental=enable_mcp_experimental)
                logger.info("MarketDataValidator using JinaHybridClient")
            except Exception as e:
                logger.warning(f"Failed to initialize hybrid client, falling back to direct client: {e}")
                self.jina_client = get_jina_client()
                logger.info("MarketDataValidator using direct JinaReaderClient")
        else:
            self.jina_client = jina_client

        self.llm_model = settings.OPENROUTER_MODEL
        self.total_tokens = 0
        self.total_cost = 0.0

        # Extraction metrics tracking
        self._extraction_stats = {
            "json_parse_errors": 0,
            "json_parse_successes": 0,
            "search_failures": 0,
            "search_successes": 0,
            "extraction_retries": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "partial_recoveries": 0,
        }

        logger.info(f"MarketDataValidator initialized with model: {self.llm_model}")

    def get_extraction_stats(self) -> dict:
        """
        Get extraction success/failure metrics.

        Returns:
            Dictionary containing:
            - json_parse_errors: Number of JSON parsing failures
            - json_parse_successes: Number of successful JSON parses
            - search_failures: Number of failed web searches
            - search_successes: Number of successful web searches
            - extraction_retries: Number of retry attempts made
            - successful_extractions: Total successful data extractions
            - failed_extractions: Total failed data extractions
            - partial_recoveries: Number of partial data recoveries
            - success_rate: Overall success rate percentage
        """
        stats = self._extraction_stats.copy()

        # Calculate success rate
        total_attempts = stats["successful_extractions"] + stats["failed_extractions"]
        if total_attempts > 0:
            stats["success_rate"] = (
                stats["successful_extractions"] / total_attempts
            ) * 100
        else:
            stats["success_rate"] = 0.0

        # Calculate JSON parse success rate
        total_json = stats["json_parse_successes"] + stats["json_parse_errors"]
        if total_json > 0:
            stats["json_success_rate"] = (
                stats["json_parse_successes"] / total_json
            ) * 100
        else:
            stats["json_success_rate"] = 0.0

        return stats

    def reset_extraction_stats(self) -> None:
        """Reset all extraction metrics to zero."""
        for key in self._extraction_stats:
            self._extraction_stats[key] = 0
        logger.info("Extraction statistics reset")

    def validate_opportunity(
        self,
        app_concept: str,
        target_market: str,
        problem_description: str,
        max_searches: int | None = None,
    ) -> ValidationEvidence:
        """
        Validate monetization potential using real market data.

        Args:
            app_concept: Description of the app concept
            target_market: Target market (B2B, B2C, etc.)
            problem_description: The problem being solved
            max_searches: Maximum number of web searches (default from settings)

        Returns:
            ValidationEvidence with collected market data and scores
        """
        if max_searches is None:
            max_searches = settings.MARKET_VALIDATION_MAX_SEARCHES

        logger.info(f"Starting market validation for: {app_concept}")

        evidence = ValidationEvidence()
        self.total_tokens = 0
        self.total_cost = 0.0

        # Step 1: Identify and analyze competitors
        try:
            competitors = self._identify_competitors(
                app_concept, target_market, max_searches // 2
            )
            for competitor_url in competitors[:3]:  # Limit to top 3
                pricing = self._extract_competitor_pricing(competitor_url, app_concept)
                if pricing:
                    evidence.competitor_pricing.append(pricing)
                    evidence.urls_fetched.append(competitor_url)
        except Exception as e:
            logger.error(f"Error identifying competitors: {e}")

        # Step 2: Search for market size data
        try:
            market_size = self._search_market_size(app_concept, target_market)
            if market_size:
                evidence.market_size = market_size
        except Exception as e:
            logger.error(f"Error searching market size: {e}")

        # Step 3: Find similar product launches
        try:
            launches = self._find_similar_launches(app_concept)
            evidence.similar_launches = launches[:3]  # Top 3
        except Exception as e:
            logger.error(f"Error finding similar launches: {e}")

        # Step 4: Get industry benchmarks
        try:
            benchmarks = self._get_industry_benchmarks(app_concept, target_market)
            evidence.industry_benchmarks = benchmarks
        except Exception as e:
            logger.error(f"Error getting benchmarks: {e}")

        # Step 5: Synthesize validation score
        evidence.validation_score = self._calculate_validation_score(evidence)
        evidence.data_quality_score = self._calculate_data_quality_score(evidence)
        evidence.reasoning = self._generate_reasoning(evidence, app_concept)
        evidence.total_cost = self.total_cost

        logger.info(
            f"Market validation complete: "
            f"score={evidence.validation_score:.1f}, "
            f"data_quality={evidence.data_quality_score:.1f}, "
            f"cost=${self.total_cost:.4f}"
        )

        return evidence

    def _identify_competitors(
        self, app_concept: str, target_market: str, max_results: int = 5
    ) -> list[str]:
        """
        Identify competitor websites based on app concept.

        Returns list of competitor pricing page URLs.
        """
        # Build search query for competitors
        search_query = f"{app_concept} {target_market} pricing alternatives"
        logger.info(f"Searching for competitors: {search_query}")

        results = self.jina_client.search_web(search_query, num_results=max_results)

        # Extract URLs that look like pricing or product pages
        competitor_urls = []
        for result in results:
            url = result.url
            # Prioritize pricing pages
            if any(
                kw in url.lower() for kw in ["pricing", "plans", "cost", "subscribe"]
            ):
                competitor_urls.append(url)
            elif not any(
                skip in url.lower()
                for skip in ["wikipedia", "reddit", "quora", "youtube"]
            ):
                competitor_urls.append(url)

        logger.info(f"Found {len(competitor_urls)} potential competitor URLs")
        return competitor_urls

    def _extract_competitor_pricing(
        self, url: str, app_concept: str
    ) -> CompetitorPricing | None:
        """
        Extract pricing information from a competitor's website.

        Uses LLM to parse the webpage content and extract structured pricing data.
        Handles edge cases like enterprise pricing, usage-based pricing, and
        contact-us models. Includes retry logic with simplified prompts on failure.
        """
        try:
            # Fetch the page content
            logger.info(f"Fetching pricing data from: {url}")
            response = self.jina_client.read_url(url)

            if response.word_count < 50:
                logger.warning(f"Page content too short: {url}")
                self._extraction_stats["failed_extractions"] += 1
                return None

            # Try extraction with main prompt, then retry with simplified if needed
            max_attempts = 2
            for attempt in range(max_attempts):
                if attempt > 0:
                    self._extraction_stats["extraction_retries"] += 1
                    logger.info(f"Retry attempt {attempt + 1} with simplified prompt")

                # Use simplified prompt on retry
                if attempt == 0:
                    prompt = self._build_pricing_extraction_prompt(
                        response.content[:10000]
                    )
                else:
                    prompt = self._build_simplified_pricing_prompt(
                        response.content[:10000]
                    )

                try:
                    llm_response = litellm.completion(
                        model=f"openrouter/{self.llm_model}",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=1500 if attempt == 0 else 800,
                        temperature=0.1,
                    )

                    # Track costs
                    if llm_response.usage:
                        self.total_tokens += llm_response.usage.total_tokens
                        # Approximate cost (varies by model)
                        self.total_cost += llm_response.usage.total_tokens * 0.00001

                    # Parse JSON response
                    content = llm_response.choices[0].message.content.strip()
                    content = self._clean_json_response(content)

                    data = json.loads(content)
                    self._extraction_stats["json_parse_successes"] += 1

                    # Validate and score the extracted data
                    confidence = self._calculate_pricing_confidence(data)

                    if data.get("company_name") and confidence > 0.2:
                        logger.info(
                            f"Extracted pricing for {data['company_name']} "
                            f"({len(data.get('pricing_tiers', []))} tiers, "
                            f"confidence: {confidence:.2f})"
                        )
                        self._extraction_stats["successful_extractions"] += 1
                        return CompetitorPricing(
                            company_name=data["company_name"],
                            pricing_tiers=data.get("pricing_tiers", []),
                            pricing_model=data.get("pricing_model", "unknown"),
                            target_market=data.get("target_market", "unknown"),
                            source_url=url,
                            confidence=confidence,
                        )
                    else:
                        conf_val = f"{confidence:.2f}"
                        logger.warning(
                            f"Low confidence pricing extraction from {url}: {conf_val}"
                        )
                        # Try partial recovery
                        if data.get("company_name"):
                            self._extraction_stats["partial_recoveries"] += 1

                except json.JSONDecodeError as e:
                    self._extraction_stats["json_parse_errors"] += 1
                    logger.error(
                        f"JSON parsing error for {url} (attempt {attempt + 1}): {e}"
                    )
                    # Log the problematic content for debugging
                    logger.debug(
                        f"Raw content that failed to parse: {content[:500]}..."
                    )

                    # Try to extract partial data from malformed JSON
                    if attempt == max_attempts - 1:
                        partial_data = self._attempt_partial_json_recovery(content)
                        if partial_data and partial_data.get("company_name"):
                            self._extraction_stats["partial_recoveries"] += 1
                            logger.info(f"Partial recovery successful for {url}")
                            return CompetitorPricing(
                                company_name=partial_data["company_name"],
                                pricing_tiers=partial_data.get("pricing_tiers", []),
                                pricing_model=partial_data.get(
                                    "pricing_model", "unknown"
                                ),
                                target_market=partial_data.get(
                                    "target_market", "unknown"
                                ),
                                source_url=url,
                                confidence=0.3,  # Low confidence for partial recovery
                            )
                    continue

        except Exception as e:
            logger.error(f"Error extracting pricing from {url}: {e}")

        self._extraction_stats["failed_extractions"] += 1
        return None

    def _build_pricing_extraction_prompt(self, content: str) -> str:
        """Build the main pricing extraction prompt."""
        return f"""You are a pricing analyst. Extract pricing info from this page.

WEBPAGE CONTENT:
{content}

INSTRUCTIONS:
1. Identify the company/product name from the page
2. Determine the primary pricing model:
   - "subscription": Monthly/yearly recurring fees
   - "freemium": Free tier plus paid upgrades
   - "one-time": Single purchase
   - "usage-based": Pay-per-use (API calls, storage, etc.)
   - "enterprise": Custom pricing, contact sales
   - "hybrid": Mix of models (e.g., subscription + usage)
3. Identify target market based on features and pricing:
   - "B2B": Business-to-business
   - "B2C": Consumer-focused
   - "Enterprise": Large organizations
   - "SMB": Small-medium businesses
4. Extract ALL pricing tiers, including:
   - Free/trial tiers
   - Enterprise tiers (even if "Contact Us")
   - Usage-based pricing (extract unit prices)
   - Annual vs monthly pricing (prefer monthly, note annual)

Return ONLY valid JSON, no markdown, no explanation:
{{
    "company_name": "Exact product/company name",
    "pricing_model": "subscription|freemium|one-time|usage-based|enterprise|hybrid",
    "target_market": "B2B|B2C|Enterprise|SMB",
    "pricing_tiers": [
        {{
            "tier": "Plan name",
            "price": "$X/month or $X/year or Contact Sales",
            "price_monthly_normalized": null or dollar amount as number,
            "features": ["feature 1", "feature 2"],
            "limits": "user limit or usage limit",
            "is_enterprise": false
        }}
    ],
    "has_free_trial": true or false,
    "has_free_tier": true or false,
    "currency": "USD|EUR|GBP|other",
    "notes": "Any important pricing notes",
    "confidence": 0.0 to 1.0
}}

If NO pricing information is found, return:
{{"company_name": "Name if found", "pricing_model": "unknown", "pricing_tiers": [], \
"confidence": 0.0}}"""

    def _build_simplified_pricing_prompt(self, content: str) -> str:
        """Build a simplified prompt for retry attempts."""
        return f"""Extract pricing from this webpage. Return ONLY valid JSON.

CONTENT:
{content[:5000]}

Return this exact JSON structure:
{{
    "company_name": "company name here",
    "pricing_model": "subscription",
    "target_market": "B2C",
    "pricing_tiers": [
        {{"tier": "Basic", "price": "$10/month", "features": ["feature1"]}}
    ],
    "confidence": 0.5
}}

If no pricing found:
{{"company_name": "unknown", "pricing_model": "unknown", "pricing_tiers": [], \
"confidence": 0.0}}"""

    def _attempt_partial_json_recovery(self, malformed_json: str) -> dict | None:
        """
        Attempt to recover partial data from malformed JSON.

        Uses regex patterns to extract key fields even when JSON is invalid.
        """
        try:
            recovered = {}

            # Try to extract company name
            company_match = re.search(r'"company_name"\s*:\s*"([^"]+)"', malformed_json)
            if company_match:
                recovered["company_name"] = company_match.group(1)

            # Try to extract pricing model
            model_match = re.search(r'"pricing_model"\s*:\s*"([^"]+)"', malformed_json)
            if model_match:
                recovered["pricing_model"] = model_match.group(1)

            # Try to extract target market
            market_match = re.search(r'"target_market"\s*:\s*"([^"]+)"', malformed_json)
            if market_match:
                recovered["target_market"] = market_match.group(1)

            # Try to extract at least one pricing tier
            tier_match = re.search(
                r'"tier"\s*:\s*"([^"]+)".*?"price"\s*:\s*"([^"]+)"',
                malformed_json,
                re.DOTALL,
            )
            if tier_match:
                recovered["pricing_tiers"] = [
                    {
                        "tier": tier_match.group(1),
                        "price": tier_match.group(2),
                        "features": [],
                    }
                ]
            else:
                recovered["pricing_tiers"] = []

            logger.debug(f"Partial recovery extracted: {list(recovered.keys())}")
            return recovered if recovered.get("company_name") else None

        except Exception as e:
            logger.debug(f"Partial recovery failed: {e}")
            return None

    def _clean_json_response(self, content: str) -> str:
        """
        Clean LLM response to extract valid JSON.

        This method uses multiple strategies to extract JSON:
        1. Remove markdown code blocks
        2. Find JSON object boundaries
        3. Fix common JSON syntax issues
        4. Handle nested objects and trailing content
        """
        if not content:
            logger.warning("Empty content received for JSON cleaning")
            return "{}"

        original_content = content
        content = content.strip()

        # Strategy 1: Remove markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            # Find start and end of JSON block
            start_idx = 0
            end_idx = len(lines)
            for i, line in enumerate(lines):
                if line.startswith("```") and i == 0:
                    start_idx = 1
                elif line.startswith("```") and i > 0:
                    end_idx = i
                    break
            content = "\n".join(lines[start_idx:end_idx])

        # Remove json language identifier if present
        if content.startswith("json"):
            content = content[4:]

        content = content.strip()

        # Strategy 2: Find JSON object boundaries with brace matching
        if not content.startswith("{"):
            start = content.find("{")
            if start != -1:
                content = content[start:]
            else:
                logger.warning("No JSON object start '{' found in response")
                return "{}"

        # Strategy 3: Match braces to find the correct end
        # This handles cases where there's extra content after the JSON
        brace_count = 0
        in_string = False
        escape_next = False
        json_end = -1

        for i, char in enumerate(content):
            if escape_next:
                escape_next = False
                continue

            if char == "\\" and in_string:
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if not in_string:
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i
                        break

        if json_end != -1:
            content = content[: json_end + 1]
        elif not content.endswith("}"):
            # Fallback: find last closing brace
            end = content.rfind("}")
            if end != -1:
                content = content[: end + 1]
            else:
                logger.warning("No JSON object end '}' found in response")
                return "{}"

        # Strategy 4: Fix common JSON syntax issues
        # Remove trailing commas before closing braces/brackets
        content = re.sub(r",\s*}", "}", content)
        content = re.sub(r",\s*]", "]", content)

        # Fix unescaped newlines in strings (common LLM issue)
        # This is tricky, so we log if we attempt it
        if "\n" in content:
            # Try to detect if newlines are inside strings improperly
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                if "Unterminated string" in str(e) or "control character" in str(e):
                    logger.debug("Attempting to fix newlines in JSON strings")
                    # Replace literal newlines that aren't properly escaped
                    content = content.replace("\r\n", "\\n").replace("\r", "\\n")
                    # Only replace newlines inside what looks like string values
                    # This is a simple heuristic that works for most cases

        # Log what was cleaned for debugging
        if content != original_content.strip():
            orig_len = len(original_content)
            clean_len = len(content)
            logger.debug(
                f"JSON cleaned: original length={orig_len}, cleaned length={clean_len}"
            )

        return content

    def _calculate_pricing_confidence(self, data: dict) -> float:
        """
        Calculate confidence score for extracted pricing data.

        Factors:
        - Has company name
        - Has pricing tiers with actual prices
        - Has features listed
        - Model is not 'unknown'
        """
        score = 0.0

        # Base confidence from LLM
        llm_confidence = data.get("confidence", 0.5)

        # Has company name (required)
        if data.get("company_name"):
            score += 0.2

        # Has pricing tiers
        tiers = data.get("pricing_tiers", [])
        if tiers:
            score += 0.2
            # Bonus for multiple tiers
            if len(tiers) >= 2:
                score += 0.1
            if len(tiers) >= 3:
                score += 0.1

            # Check tier quality
            tiers_with_price = sum(
                1 for t in tiers if t.get("price") and t.get("price") != "unknown"
            )
            if tiers_with_price > 0:
                score += 0.2 * (tiers_with_price / len(tiers))

            # Check for features
            tiers_with_features = sum(
                1 for t in tiers if t.get("features") and len(t.get("features", [])) > 0
            )
            if tiers_with_features > 0:
                score += 0.1

        # Known pricing model
        if data.get("pricing_model") and data.get("pricing_model") != "unknown":
            score += 0.1

        # Combine with LLM confidence
        final_confidence = (score * 0.6) + (llm_confidence * 0.4)

        return min(1.0, final_confidence)

    def _search_market_size(
        self, app_concept: str, target_market: str
    ) -> MarketSizeData | None:
        """
        Search for market size data related to the app concept.

        Uses multiple search strategies:
        1. Primary search with market size keywords
        2. Fallback to industry reports (Statista, Grand View, etc.)
        3. Try alternative keyword variations
        """
        # Extract relevant market keywords
        keywords = self._extract_market_keywords(app_concept)

        # Build multiple search queries (try in order of specificity)
        search_queries = [
            f"{keywords} market size TAM billion {target_market} 2024 2025",
            f"{keywords} industry report market forecast CAGR",
            f'"{keywords}" global market size billion',
            f"{keywords} market analysis Statista Grand View Research",
        ]

        logger.info(f"Searching market size for: {keywords}")

        for query_idx, search_query in enumerate(search_queries):
            try:
                log_msg = f"Market size search attempt {query_idx + 1}: {search_query}"
                logger.info(log_msg)
                results = self.jina_client.search_web(search_query, num_results=5)

                # Priority order for sources
                priority_sources = [
                    "statista",
                    "grandviewresearch",
                    "marketsandmarkets",
                    "precedenceresearch",
                    "fortunebusinessinsights",
                    "mordorintelligence",
                ]

                # Sort results by source priority
                results = self._sort_by_source_priority(results, priority_sources)

                # Try to extract from snippets first (faster, no additional API call)
                for result in results:
                    snippet_lower = result.snippet.lower()
                    title_lower = result.title.lower()

                    # Check if snippet contains market data indicators
                    has_value = any(
                        kw in snippet_lower for kw in ["billion", "million", "usd", "$"]
                    )
                    market_terms = [
                        "market size",
                        "market value",
                        "tam",
                        "cagr",
                        "forecast",
                    ]
                    has_market_term = any(
                        kw in snippet_lower or kw in title_lower for kw in market_terms
                    )

                    if has_value and has_market_term:
                        market_data = self._extract_market_data_from_snippet(result)
                        if market_data and market_data.tam_value:
                            logger.info(
                                f"Found market data in snippet: {market_data.tam_value}"
                            )
                            return market_data

                # If no good snippet, try fetching from priority sources
                for result in results[:3]:  # Limit to top 3 to save API calls
                    # Skip non-research URLs
                    skip_domains = [
                        "wikipedia",
                        "reddit",
                        "youtube",
                        "twitter",
                        "linkedin",
                    ]
                    if any(skip in result.url.lower() for skip in skip_domains):
                        continue

                    logger.info(f"Fetching market data from: {result.url}")
                    market_data = self._extract_market_data_from_url(
                        result.url, app_concept
                    )
                    if market_data and market_data.tam_value:
                        return market_data

            except Exception as e:
                err_msg = f"Error in market size search attempt {query_idx + 1}: {e}"
                logger.warning(err_msg)
                continue

        logger.warning("No market size data found after all search attempts")
        return None

    def _sort_by_source_priority(self, results: list, priority_sources: list) -> list:
        """Sort search results by source priority (trusted research sources first)."""

        def get_priority(result):
            url_lower = result.url.lower()
            for idx, source in enumerate(priority_sources):
                if source in url_lower:
                    return idx
            return len(priority_sources)

        return sorted(results, key=get_priority)

    def _extract_market_keywords(self, app_concept: str) -> str:
        """
        Extract key market terms from app concept for industry report searches.

        Uses domain-specific mapping to translate app concepts into
        standard market research terminology.
        """
        concept_lower = app_concept.lower()

        # Domain-specific keyword mappings (app terms -> market research terms)
        domain_mappings = {
            # Finance & Accounting
            ("expense", "budget", "finance", "money", "accounting"): (
                "personal finance software"
            ),
            ("invoice", "billing", "payment"): "invoicing software",
            ("tax", "accounting"): "accounting software",
            ("investment", "stock", "trading", "portfolio"): (
                "investment management software"
            ),
            # Health & Fitness
            ("fitness", "workout", "exercise", "gym"): "fitness app",
            ("health", "wellness", "medical"): "digital health",
            ("diet", "nutrition", "calorie"): "diet and nutrition apps",
            ("mental health", "meditation", "mindfulness"): "mental wellness apps",
            # Productivity
            ("task", "todo", "project", "productivity"): (
                "project management software"
            ),
            ("note", "notes", "documentation"): "note-taking software",
            ("calendar", "scheduling", "appointment"): "scheduling software",
            ("time tracking", "timesheet"): "time tracking software",
            # Communication
            ("chat", "messaging", "communication"): "team collaboration software",
            ("email", "mail"): "email management software",
            ("video", "conference", "meeting"): "video conferencing software",
            # E-commerce
            ("ecommerce", "shopping", "store", "marketplace"): "e-commerce platform",
            ("inventory", "warehouse"): "inventory management software",
            # Education
            ("learning", "education", "course", "study"): "e-learning",
            ("language", "translation"): "language learning apps",
            # CRM & Sales
            ("crm", "customer", "sales", "lead"): "customer relationship management",
            ("marketing", "campaign", "advertising"): ("marketing automation software"),
            # Developer Tools
            ("code", "developer", "programming", "api"): "developer tools",
            ("devops", "deployment", "ci/cd"): "devops platform",
            # AI & Analytics
            ("ai", "artificial intelligence", "machine learning"): (
                "artificial intelligence software"
            ),
            ("analytics", "data", "dashboard", "reporting"): (
                "business intelligence software"
            ),
        }

        # Find matching domain
        for keywords, market_term in domain_mappings.items():
            if any(kw in concept_lower for kw in keywords):
                return market_term

        # Fallback: extract meaningful terms from the concept
        # Remove common stop words and extract key terms
        stop_words = {
            "app",
            "application",
            "tool",
            "software",
            "platform",
            "system",
            "with",
            "for",
            "and",
            "the",
            "a",
            "an",
            "that",
            "which",
            "using",
        }
        words = [w.strip() for w in app_concept.split() if w.lower() not in stop_words]

        if len(words) >= 2:
            # Take first 2-3 meaningful words
            return " ".join(words[:3]) + " software"
        elif words:
            return words[0] + " software"
        else:
            # Last resort: use original concept
            return app_concept + " software"

    def _extract_market_data_from_snippet(self, result) -> MarketSizeData | None:
        """
        Extract market size data from search result snippet.

        Uses advanced pattern matching to find TAM, CAGR, and other market metrics.
        """
        snippet = result.snippet
        title = result.title

        # Combine title and snippet for better matching
        text = f"{title} {snippet}"

        # Multiple patterns for market values (from most specific to least)
        market_value_patterns = [
            # USD $X.XX billion/million pattern
            r"(?:USD\s*)?\$\s*([\d,]+\.?\d*)\s*(billion|million|trillion|bn|mn|B|M|T)",
            # X.XX billion USD pattern
            r"([\d,]+\.?\d*)\s*(billion|million|trillion|bn|mn|B|M|T)\s*(?:USD|US\$|\$)",
            # Valued at $X billion
            r"valued\s+at\s+(?:USD\s*)?\$?\s*([\d,]+\.?\d*)\s*(billion|million|trillion|bn|mn|B|M|T)",
            # Market size of $X billion
            r"market\s+(?:size|value|worth)\s+(?:of\s+)?(?:USD\s*)?\$?\s*([\d,]+\.?\d*)\s*(billion|million|trillion|bn|mn|B|M|T)",
            # Expected to reach $X billion
            r"(?:expected|projected|forecast)\s+to\s+reach\s+(?:USD\s*)?\$?\s*([\d,]+\.?\d*)\s*(billion|million|trillion|bn|mn|B|M|T)",
            # Generic: number + unit
            r"([\d,]+\.?\d*)\s*(billion|million|trillion|bn|mn|B|M|T)",
        ]

        tam_value = None
        for pattern in market_value_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                value_str, unit = matches[0]
                # Clean up value
                value_str = value_str.replace(",", "")
                # Normalize unit
                unit_map = {
                    "billion": "billion",
                    "bn": "billion",
                    "b": "billion",
                    "million": "million",
                    "mn": "million",
                    "m": "million",
                    "trillion": "trillion",
                    "t": "trillion",
                }
                normalized_unit = unit_map.get(unit.lower(), unit)
                tam_value = f"${value_str} {normalized_unit}"
                break

        if not tam_value:
            return None

        # Look for year information
        year_pattern = r"\b(202[0-9]|203[0-9])\b"
        year_matches = re.findall(year_pattern, text)
        year = 2024  # Default
        if year_matches:
            # Take the most recent year mentioned
            years = [int(y) for y in year_matches]
            # Prefer future projections or current year
            year = max(y for y in years if y <= 2030)

        # Look for CAGR (multiple patterns)
        growth_rate = None
        cagr_patterns = [
            r"([\d.]+)\s*%\s*CAGR",
            r"CAGR\s+(?:of\s+)?([\d.]+)\s*%",
            r"(?:grow|growth)\s+(?:rate\s+)?(?:of\s+)?([\d.]+)\s*%",
            r"([\d.]+)\s*%\s*(?:annual|yearly)\s+growth",
        ]
        for pattern in cagr_patterns:
            cagr_match = re.search(pattern, text, re.IGNORECASE)
            if cagr_match:
                growth_rate = f"{cagr_match.group(1)}% CAGR"
                break

        # Calculate confidence based on data quality
        confidence = 0.6  # Base confidence for snippet extraction
        if growth_rate:
            confidence += 0.1
        if year and year >= 2024:
            confidence += 0.1
        # Boost for reputable sources
        if any(
            src in result.url.lower()
            for src in ["statista", "grandview", "marketsandmarkets", "precedence"]
        ):
            confidence += 0.2

        confidence = min(1.0, confidence)

        return MarketSizeData(
            tam_value=tam_value,
            growth_rate=growth_rate,
            year=year,
            source_url=result.url,
            source_name=result.title,
            confidence=confidence,
        )

    def _extract_market_data_from_url(
        self, url: str, app_concept: str
    ) -> MarketSizeData | None:
        """
        Fetch and extract market data from a URL using LLM.

        Uses sophisticated extraction with source-specific handling for different
        market research providers (Statista, Grand View Research, etc.).
        """
        try:
            response = self.jina_client.read_url(url)

            if response.word_count < 100:
                logger.warning(f"Market report page too short: {url}")
                return None

            # Determine source type for tailored extraction
            source_type = "generic"
            if "statista" in url.lower():
                source_type = "statista"
            elif "grandview" in url.lower():
                source_type = "grandview"
            elif "marketsandmarkets" in url.lower():
                source_type = "marketsandmarkets"

            prompt = f"""You are a market research analyst. Extract market size data.

SOURCE TYPE: {source_type}
URL: {url}

CONTENT:
{response.content[:8000]}

EXTRACTION INSTRUCTIONS:
1. Look for Total Addressable Market (TAM) or global market size
2. Look for Serviceable Addressable Market (SAM) if available
3. Look for Serviceable Obtainable Market (SOM) if available
4. Extract Compound Annual Growth Rate (CAGR)
5. Note the year(s) the data refers to
6. Identify the publishing organization/research firm

IMPORTANT:
- TAM is typically the largest value (global/total market)
- SAM is a subset of TAM (target segment)
- SOM is a subset of SAM (realistic capture)
- CAGR shows growth trajectory (look for percentages)
- Report year vs forecast year are different - note both

RESPONSE FORMAT (JSON only):
{{
    "tam_value": "$X.XX billion" or "$X.XX million" or null,
    "sam_value": "$X.XX billion" or null (if mentioned),
    "som_value": "$X.XX billion" or null (if mentioned),
    "growth_rate": "X.X% CAGR" or null,
    "forecast_period": "2024-2030" or similar (if mentioned),
    "base_year": 2024 (the reference year for current market size),
    "forecast_year": 2030 (the year of projected value, if different),
    "source_name": "Research firm or publisher name",
    "market_segments": ["segment1", "segment2"] (if breakdown available),
    "regional_breakdown": {{"North America": "40%", "Europe": "30%"}} or null,
    "key_drivers": ["driver1", "driver2"] (top growth drivers if mentioned),
    "confidence": 0.0 to 1.0
}}

CONFIDENCE SCORING:
- 1.0: Clear market size with specific numbers, CAGR, and source attribution
- 0.8: Market size found but some details missing (e.g., no CAGR)
- 0.6: Partial data available, some estimation needed
- 0.4: Vague references to market size
- 0.2: Only general market commentary, no specific numbers

Return ONLY valid JSON, no explanation."""

            llm_response = litellm.completion(
                model=f"openrouter/{self.llm_model}",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.1,
            )

            if llm_response.usage:
                self.total_tokens += llm_response.usage.total_tokens
                self.total_cost += llm_response.usage.total_tokens * 0.00001

            content = llm_response.choices[0].message.content.strip()
            content = self._clean_json_response(content)

            data = json.loads(content)

            # Validate extracted data
            if not data.get("tam_value"):
                logger.warning(f"No TAM value found in {url}")
                return None

            llm_confidence = data.get("confidence", 0.5)

            # Adjust confidence based on data completeness
            completeness_score = 0.0
            if data.get("tam_value"):
                completeness_score += 0.4
            if data.get("growth_rate"):
                completeness_score += 0.2
            if data.get("source_name"):
                completeness_score += 0.2
            if data.get("sam_value") or data.get("market_segments"):
                completeness_score += 0.2

            final_confidence = (llm_confidence * 0.5) + (completeness_score * 0.5)
            final_confidence = min(1.0, final_confidence)

            if final_confidence < 0.3:
                logger.warning(
                    f"Low confidence market data from {url}: {final_confidence:.2f}"
                )
                return None

            logger.info(
                f"Extracted market data: TAM={data.get('tam_value')}, "
                f"CAGR={data.get('growth_rate')}, confidence={final_confidence:.2f}"
            )

            return MarketSizeData(
                tam_value=data.get("tam_value"),
                sam_value=data.get("sam_value"),
                som_value=data.get("som_value"),
                growth_rate=data.get("growth_rate"),
                year=data.get("base_year", data.get("forecast_year", 2024)),
                source_url=url,
                source_name=data.get("source_name", ""),
                confidence=final_confidence,
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error for market data from {url}: {e}")
        except Exception as e:
            logger.error(f"Error extracting market data from {url}: {e}")

        return None

    def _find_similar_launches(self, app_concept: str) -> list[ProductLaunchData]:
        """
        Find similar product launches across multiple platforms.

        Searches:
        - Product Hunt (primary)
        - Hacker News (Show HN, Launch HN)
        - Reddit launches (r/startups, r/SideProject)
        - TechCrunch funding announcements
        """
        launches = []

        # Sanitize app concept for search queries
        sanitized_concept = self._sanitize_search_query(app_concept)

        # Define search strategies for different platforms
        search_strategies = [
            {
                "platform": "Product Hunt",
                "query": f"site:producthunt.com {sanitized_concept}",
                "num_results": 5,
            },
            {
                "platform": "Hacker News",
                "query": f"site:news.ycombinator.com Show HN {sanitized_concept}",
                "num_results": 3,
            },
            {
                "platform": "Reddit",
                "query": f"site:reddit.com startups {sanitized_concept} launch",
                "num_results": 3,
            },
        ]

        for strategy in search_strategies:
            try:
                logger.info(f"Searching {strategy['platform']}: {strategy['query']}")
                results = self.jina_client.search_web(
                    strategy["query"], num_results=strategy["num_results"]
                )
                self._extraction_stats["search_successes"] += 1

                for result in results:
                    # Extract metadata from result
                    launch_data = self._extract_launch_metadata(
                        result, strategy["platform"]
                    )
                    if launch_data:
                        launches.append(launch_data)

            except Exception as e:
                self._extraction_stats["search_failures"] += 1
                logger.warning(f"Error searching {strategy['platform']}: {e}")
                continue

        # Deduplicate by product name (case-insensitive)
        seen_products = set()
        unique_launches = []
        for launch in launches:
            product_key = launch.product_name.lower().strip()
            if product_key not in seen_products and len(product_key) > 2:
                seen_products.add(product_key)
                unique_launches.append(launch)

        logger.info(f"Found {len(unique_launches)} unique similar launches")
        return unique_launches

    def _sanitize_search_query(self, query: str) -> str:
        """
        Sanitize a search query to prevent 422 errors.

        Removes or encodes special characters that cause issues with
        search APIs, while preserving meaningful search terms.

        Args:
            query: Raw search query string

        Returns:
            Sanitized query string safe for web searches
        """
        if not query:
            return ""

        # Remove characters that cause 422 errors in Reddit/web searches
        # These characters often cause URL encoding or parsing issues
        problematic_chars = [
            '"',
            "'",
            "(",
            ")",
            "[",
            "]",
            "{",
            "}",
            "|",
            "&",
            "\\",
            "/",
            ":",
            ";",
            "!",
            "?",
            "*",
            "+",
            "=",
            "<",
            ">",
            "@",
            "#",
            "$",
            "%",
            "^",
            "~",
            "`",
        ]

        sanitized = query
        for char in problematic_chars:
            sanitized = sanitized.replace(char, " ")

        # Remove multiple spaces and trim
        sanitized = " ".join(sanitized.split())

        # Limit query length to avoid overly complex searches
        words = sanitized.split()
        if len(words) > 10:
            # Keep first 10 meaningful words
            sanitized = " ".join(words[:10])

        # Remove very short words that don't add search value
        words = [
            w
            for w in sanitized.split()
            if len(w) > 2 or w.lower() in ["ai", "ml", "ux", "ui", "app"]
        ]
        sanitized = " ".join(words)

        logger.debug(f"Sanitized query: '{query}' -> '{sanitized}'")
        return sanitized

    def _extract_launch_metadata(
        self, result, platform: str
    ) -> ProductLaunchData | None:
        """Extract detailed launch metadata from search result"""
        title = result.title
        snippet = result.snippet
        url = result.url

        # Clean up product name from title
        product_name = title

        # Platform-specific parsing
        if platform == "Product Hunt":
            # Remove common suffixes like "- Product Hunt"
            if " - Product Hunt" in product_name:
                product_name = product_name.replace(" - Product Hunt", "").strip()
            elif " | Product Hunt" in product_name:
                product_name = product_name.replace(" | Product Hunt", "").strip()

            # Try to extract upvotes from snippet
            upvotes = None
            upvote_patterns = [
                r"(\d+)\s*upvotes?",
                r"(\d+)\s*votes?",
                r"(\d{1,4})\s*\u25B2",  # Unicode up arrow
            ]
            for pattern in upvote_patterns:
                match = re.search(pattern, snippet, re.IGNORECASE)
                if match:
                    upvotes = int(match.group(1))
                    break

            # Try to extract rank
            rank = None
            rank_patterns = [
                r"#(\d+)\s*(?:Product|App|Tool)",
                r"ranked?\s*#?(\d+)",
                r"Product of the (\w+)",
            ]
            for pattern in rank_patterns:
                match = re.search(pattern, snippet, re.IGNORECASE)
                if match:
                    rank = match.group(0)
                    break

        elif platform == "Hacker News":
            # Remove "Show HN:" prefix
            if product_name.startswith("Show HN:"):
                product_name = product_name[8:].strip()
            elif product_name.startswith("Launch HN:"):
                product_name = product_name[10:].strip()

            # Extract points/comments from snippet
            upvotes = None
            points_match = re.search(r"(\d+)\s*points?", snippet, re.IGNORECASE)
            if points_match:
                upvotes = int(points_match.group(1))

            rank = None  # HN doesn't have product ranks

        elif platform == "Reddit":
            # Clean Reddit-specific formatting
            if " : " in product_name:
                product_name = product_name.split(" : ")[0].strip()
            if " - Reddit" in product_name:
                product_name = product_name.replace(" - Reddit", "").strip()

            # Extract upvotes
            upvotes = None
            upvote_pattern = r"(\d+)\s*(?:upvotes?|points?)"
            upvote_match = re.search(upvote_pattern, snippet, re.IGNORECASE)
            if upvote_match:
                upvotes = int(upvote_match.group(1))

            rank = None
        else:
            upvotes = None
            rank = None

        # Try to extract funding information (common across platforms)
        funding_raised = None
        funding_patterns = [
            r"\$\s*([\d.]+)\s*(million|M|billion|B)",
            r"raised\s*\$\s*([\d.]+)\s*(million|M|billion|B|k|K)",
            r"seed\s+round\s+of\s+\$?([\d.]+)\s*(million|M|k|K)",
        ]
        for pattern in funding_patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                amount, unit = match.groups()
                funding_raised = f"${amount}{unit[0].upper()}"
                break

        # Try to extract user count
        user_count = None
        user_patterns = [
            r"([\d,]+)\s*users?",
            r"([\d,]+)\s*customers?",
            r"([\d,]+)\s*active\s*users?",
        ]
        for pattern in user_patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                user_count = match.group(1)
                break

        # Try to extract launch date
        launch_date = None
        date_patterns = [
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s*\d{4})",
            r"(\d{1,2}/\d{1,2}/\d{2,4})",
            r"(launched?\s+(?:in\s+)?(?:\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}))",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                launch_date = match.group(1)
                break

        # Validate product name (should be meaningful)
        if len(product_name) < 2 or len(product_name) > 200:
            return None

        return ProductLaunchData(
            product_name=product_name,
            launch_platform=platform,
            upvotes=upvotes,
            rank=rank,
            funding_raised=funding_raised,
            user_count=user_count,
            source_url=url,
            launch_date=launch_date,
        )

    def _get_industry_benchmarks(self, app_concept: str, target_market: str) -> dict:
        """Get industry benchmarks for the app category"""
        # For now, return static benchmarks based on market type
        # In future, could fetch from industry reports

        benchmarks = {
            "avg_conversion_rate": "2-5%",
            "typical_churn_rate": "5-7% monthly",
            "avg_customer_acquisition_cost": "$50-200",
        }

        if target_market == "B2B":
            benchmarks.update(
                {
                    "avg_contract_value": "$10k-50k/year",
                    "sales_cycle": "3-6 months",
                    "typical_pricing_model": "subscription",
                }
            )
        elif target_market == "B2C":
            benchmarks.update(
                {
                    "avg_arpu": "$10-50/month",
                    "retention_benchmark": "20-40% at 12 months",
                    "typical_pricing_model": "freemium",
                }
            )

        return benchmarks

    def _extract_pricing_with_validation(
        self, pricing_data: list[CompetitorPricing]
    ) -> dict:
        """
        Cross-validate and normalize pricing data from multiple competitors.

        Returns:
            Dictionary containing:
            - normalized_prices: List of monthly normalized prices for comparison
            - price_range: Min/max price range in the market
            - common_model: Most common pricing model
            - data_quality_flags: List of any data quality issues
            - pricing_summary: Human-readable summary
        """
        if not pricing_data:
            return {
                "normalized_prices": [],
                "price_range": None,
                "common_model": "unknown",
                "data_quality_flags": ["No competitor pricing data available"],
                "pricing_summary": "Unable to validate pricing - no competitor data",
            }

        normalized_prices = []
        pricing_models = []
        data_quality_flags = []
        enterprise_only_count = 0

        for competitor in pricing_data:
            pricing_models.append(competitor.pricing_model)

            # Extract and normalize prices
            for tier in competitor.pricing_tiers:
                price_str = tier.get("price", "")
                normalized = tier.get("price_monthly_normalized")

                # If not already normalized, try to parse
                if normalized is None and price_str:
                    normalized = self._parse_price_to_monthly(price_str)

                if normalized is not None and isinstance(normalized, (int, float)):
                    normalized_prices.append(
                        {
                            "company": competitor.company_name,
                            "tier": tier.get("tier", "unknown"),
                            "monthly_price": float(normalized),
                            "original": price_str,
                        }
                    )
                elif (
                    "contact" in price_str.lower() or "enterprise" in price_str.lower()
                ):
                    enterprise_only_count += 1

            # Check for low confidence data
            if competitor.confidence < 0.5:
                conf_msg = (
                    f"Low confidence for {competitor.company_name}: "
                    f"{competitor.confidence:.2f}"
                )
                data_quality_flags.append(conf_msg)

        # Validate data consistency
        if not normalized_prices and enterprise_only_count > 0:
            ent_msg = (
                f"{enterprise_only_count} competitor(s) have "
                "enterprise/contact-only pricing"
            )
            data_quality_flags.append(ent_msg)

        # Calculate price range
        price_range = None
        if normalized_prices:
            all_prices = [p["monthly_price"] for p in normalized_prices]
            # Filter out obvious outliers (0 or extremely high)
            valid_prices = [p for p in all_prices if 0 < p < 10000]
            if valid_prices:
                price_range = {
                    "min": min(valid_prices),
                    "max": max(valid_prices),
                    "median": sorted(valid_prices)[len(valid_prices) // 2],
                    "avg": sum(valid_prices) / len(valid_prices),
                }

                # Check for suspicious pricing
                if price_range["max"] > price_range["min"] * 100:
                    data_quality_flags.append(
                        "Large price variance detected - verify tier comparisons"
                    )

        # Determine most common pricing model
        common_model = "unknown"
        if pricing_models:
            from collections import Counter

            model_counts = Counter(pricing_models)
            common_model = model_counts.most_common(1)[0][0]

        # Generate summary
        pricing_summary = self._generate_pricing_summary(
            normalized_prices, price_range, common_model, enterprise_only_count
        )

        return {
            "normalized_prices": normalized_prices,
            "price_range": price_range,
            "common_model": common_model,
            "data_quality_flags": data_quality_flags,
            "pricing_summary": pricing_summary,
        }

    def _parse_price_to_monthly(self, price_str: str) -> float | None:
        """
        Parse a price string and normalize to monthly value.

        Handles:
        - $X/month or $X/mo
        - $X/year or $X/yr (divide by 12)
        - $X (assume monthly)
        - Contact Sales (return None)
        """
        if not price_str:
            return None

        price_str = price_str.strip().lower()

        # Skip enterprise/contact pricing
        if any(kw in price_str for kw in ["contact", "custom", "enterprise", "call"]):
            return None

        # Extract numeric value
        price_match = re.search(r"\$?\s*([\d,]+\.?\d*)", price_str)
        if not price_match:
            return None

        try:
            amount = float(price_match.group(1).replace(",", ""))
        except ValueError:
            return None

        # Determine time period
        yearly_keywords = ["/year", "/yr", "/annual", "yearly", "annually"]
        if any(kw in price_str for kw in yearly_keywords):
            # Convert yearly to monthly
            return amount / 12.0
        elif any(kw in price_str for kw in ["/month", "/mo", "monthly"]):
            return amount
        elif any(kw in price_str for kw in ["/user", "/seat"]):
            # Per-user pricing, assume monthly
            return amount
        else:
            # Assume monthly if no period specified
            return amount

    def _generate_pricing_summary(
        self,
        normalized_prices: list,
        price_range: dict | None,
        common_model: str,
        enterprise_count: int,
    ) -> str:
        """Generate human-readable pricing summary"""
        summary_parts = []

        if price_range:
            min_price = price_range["min"]
            max_price = price_range["max"]
            median_price = price_range["median"]
            summary_parts.append(
                f"Market pricing ranges from ${min_price:.2f} to "
                f"${max_price:.2f}/month (median: ${median_price:.2f})"
            )
        elif enterprise_count > 0:
            summary_parts.append(
                f"{enterprise_count} competitor(s) use enterprise/custom pricing only"
            )
        else:
            summary_parts.append("Unable to determine market pricing")

        if common_model != "unknown":
            summary_parts.append(f"Common pricing model: {common_model}")

        if normalized_prices:
            # Group by tier type
            free_tiers = [p for p in normalized_prices if p["monthly_price"] == 0]
            paid_tiers = [p for p in normalized_prices if p["monthly_price"] > 0]

            if free_tiers:
                summary_parts.append(f"{len(free_tiers)} competitor(s) offer free tier")

            if paid_tiers:
                entry_prices = [
                    p["monthly_price"]
                    for p in paid_tiers
                    if p["monthly_price"] < 50  # Approximate entry-level threshold
                ]
                if entry_prices:
                    avg_entry = sum(entry_prices) / len(entry_prices)
                    entry_msg = f"Average entry-level price: ${avg_entry:.2f}/month"
                    summary_parts.append(entry_msg)

        return " | ".join(summary_parts)

    def _calculate_validation_score(self, evidence: ValidationEvidence) -> float:
        """Calculate overall validation score based on evidence quality"""
        score = 0.0

        # Competitor pricing (up to 40 points)
        if evidence.competitor_pricing:
            pricing_score = min(40, len(evidence.competitor_pricing) * 15)
            avg_confidence = sum(
                p.confidence for p in evidence.competitor_pricing
            ) / len(evidence.competitor_pricing)
            score += pricing_score * avg_confidence

        # Market size data (up to 30 points)
        if evidence.market_size:
            market_score = 30 * evidence.market_size.confidence
            score += market_score

        # Similar launches (up to 20 points)
        if evidence.similar_launches:
            launch_score = min(20, len(evidence.similar_launches) * 7)
            score += launch_score

        # Industry benchmarks (up to 10 points)
        if evidence.industry_benchmarks:
            score += 10

        return min(100, score)

    def _calculate_data_quality_score(self, evidence: ValidationEvidence) -> float:
        """Calculate data quality score based on evidence completeness"""
        score = 0.0

        # Has competitor data
        if evidence.competitor_pricing:
            score += 25
            if len(evidence.competitor_pricing) >= 3:
                score += 10

        # Has market size
        if evidence.market_size:
            score += 25
            if evidence.market_size.tam_value and evidence.market_size.growth_rate:
                score += 10

        # Has similar launches
        if evidence.similar_launches:
            score += 20

        # Has benchmarks
        if evidence.industry_benchmarks:
            score += 10

        return min(100, score)

    def _generate_reasoning(
        self, evidence: ValidationEvidence, app_concept: str
    ) -> str:
        """Generate human-readable reasoning for the validation score"""
        reasons = []

        # Competitor analysis
        if evidence.competitor_pricing:
            names = [p.company_name for p in evidence.competitor_pricing]
            avg_confidence = sum(
                p.confidence for p in evidence.competitor_pricing
            ) / len(evidence.competitor_pricing)
            competitor_names = ", ".join(names)
            reasons.append(
                f"Found {len(evidence.competitor_pricing)} competitor(s): "
                f"{competitor_names} (avg confidence: {avg_confidence:.0%})"
            )

            # Use pricing validation helper for deeper insights
            pricing_validation = self._extract_pricing_with_validation(
                evidence.competitor_pricing
            )
            if pricing_validation.get("pricing_summary"):
                reasons.append(pricing_validation["pricing_summary"])

            # Flag any data quality issues
            if pricing_validation.get("data_quality_flags"):
                # Limit to 2 flags to avoid overwhelming the summary
                for flag in pricing_validation["data_quality_flags"][:2]:
                    reasons.append(f"Note: {flag}")

        else:
            reasons.append(
                "No competitor pricing data found - market validation incomplete"
            )

        # Market size
        if evidence.market_size:
            if evidence.market_size.tam_value:
                reasons.append(f"Market size (TAM): {evidence.market_size.tam_value}")
            if evidence.market_size.growth_rate:
                reasons.append(f"Market growth: {evidence.market_size.growth_rate}")
            if evidence.market_size.source_name:
                reasons.append(f"Source: {evidence.market_size.source_name}")
        else:
            reasons.append("No market size data found")

        # Similar launches with enhanced details
        if evidence.similar_launches:
            platforms = {launch.launch_platform for launch in evidence.similar_launches}
            platform_list = ", ".join(platforms)
            num_launches = len(evidence.similar_launches)
            reasons.append(
                f"Found {num_launches} similar product(s) on {platform_list}"
            )

            # Highlight notable launches
            notable_launches = [
                launch
                for launch in evidence.similar_launches
                if launch.upvotes and launch.upvotes > 100
            ]
            if notable_launches:
                top_launch = max(notable_launches, key=lambda x: x.upvotes or 0)
                product = top_launch.product_name
                votes = top_launch.upvotes
                reasons.append(f"Top launch: {product} ({votes} upvotes)")

            # Note funding if found
            funded_launches = [
                launch for launch in evidence.similar_launches if launch.funding_raised
            ]
            if funded_launches:
                reasons.append(
                    f"{len(funded_launches)} similar product(s) have raised funding"
                )
        else:
            reasons.append("No similar product launches found")

        # Overall assessment
        if evidence.validation_score >= 70:
            reasons.append(
                "STRONG market validation - good competitor data and market evidence"
            )
        elif evidence.validation_score >= 40:
            reasons.append(
                "MODERATE market validation - some evidence found but gaps exist"
            )
        else:
            reasons.append("WEAK market validation - insufficient market evidence")

        return " | ".join(reasons)


if __name__ == "__main__":
    # Simple test
    import sys

    logging.basicConfig(level=logging.INFO)

    print("Testing MarketDataValidator...")
    print("=" * 60)

    if not settings.MARKET_VALIDATION_ENABLED:
        print("Market validation is disabled in settings")
        sys.exit(0)

    validator = MarketDataValidator()

    # Test with a sample app concept
    app_concept = "expense tracking app with AI categorization"
    target_market = "B2C"
    problem_description = "People struggle to track and categorize expenses manually"

    print(f"Validating: {app_concept}")
    print(f"Target: {target_market}")
    print()

    evidence = validator.validate_opportunity(
        app_concept, target_market, problem_description
    )

    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    print(f"Validation Score: {evidence.validation_score:.1f}/100")
    print(f"Data Quality Score: {evidence.data_quality_score:.1f}/100")
    print(f"Total LLM Cost: ${evidence.total_cost:.4f}")
    print()

    print("Competitor Pricing:")
    for comp in evidence.competitor_pricing:
        print(f"  - {comp.company_name} ({comp.pricing_model})")
        print(f"    Source: {comp.source_url}")

    if evidence.market_size:
        print("\nMarket Size:")
        print(f"  TAM: {evidence.market_size.tam_value}")
        print(f"  Growth: {evidence.market_size.growth_rate}")

    print(f"\nSimilar Launches: {len(evidence.similar_launches)}")

    print("\nReasoning:")
    print(evidence.reasoning)
