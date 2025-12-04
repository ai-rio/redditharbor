"""
ValidationEvidence Data Structures for Phase 3 Jina Market Research Integration

GREEN PHASE: Minimal implementation to pass all TDD tests
Based on Phase 3 Jina Integration Documentation lines 366-427

This module implements the data structures for market validation evidence
extracted using Jina API integration with Pydantic validation and serialization.
"""

import json
import re
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class CompetitorPricing:
    """Extracted pricing data from competitor website

    Represents pricing information extracted from competitor websites
    including pricing tiers, models, and target market segments.
    """

    company_name: str
    pricing_model: str  # subscription/freemium/one-time/usage-based
    pricing_tiers: List[Dict[str, Any]]  # [{"name": "Pro", "price": "$29/mo"}]
    target_market: str  # B2B/B2C/Enterprise/SMB/B2B2C
    source_url: str
    confidence: float  # 0-100

    def __post_init__(self):
        """Validate fields after initialization"""
        # Validate required fields are not empty
        if not self.company_name or not self.company_name.strip():
            raise ValueError("company_name cannot be empty")
        if not self.source_url or not self.source_url.strip():
            raise ValueError("source_url cannot be empty")

        # Validate pricing model
        valid_models = ["subscription", "freemium", "one-time", "usage-based"]
        if self.pricing_model not in valid_models:
            raise ValueError(f"pricing_model must be one of {valid_models}")

        # Validate target market
        valid_markets = ["B2B", "B2C", "Enterprise", "SMB", "B2B2C"]
        if self.target_market not in valid_markets:
            raise ValueError(f"target_market must be one of {valid_markets}")

        # Validate confidence bounds
        if not (0.0 <= self.confidence <= 100.0):
            raise ValueError("confidence must be between 0.0 and 100.0")

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, json_str: str) -> 'CompetitorPricing':
        """Deserialize from JSON string"""
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class MarketSizeData:
    """Market size information from industry reports

    Contains market size data (TAM/SAM), growth rates, and source information
    extracted from industry research reports and market analysis.
    """

    tam_value: str  # e.g., "$50B"
    growth_rate: str  # e.g., "15% CAGR"
    source_name: str  # e.g., "Gartner 2024"
    source_url: str
    year: int
    sam_value: str = None  # e.g., "$5B" (optional)

    def __post_init__(self):
        """Validate fields after initialization"""
        # Validate TAM value format
        if not self.tam_value:
            raise ValueError("tam_value is required")

        # Validate growth rate format
        if not self.growth_rate or "%" not in self.growth_rate:
            raise ValueError("growth_rate must contain percentage")

        # Validate source fields
        if not self.source_name or not self.source_url:
            raise ValueError("source_name and source_url are required")

        # Validate year bounds (2000-2025)
        current_year = datetime.now().year
        if not (2000 <= self.year <= current_year + 1):
            raise ValueError(f"year must be between 2000 and {current_year + 1}")

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, json_str: str) -> 'MarketSizeData':
        """Deserialize from JSON string"""
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class ProductLaunchData:
    """Product launch benchmarks

    Contains launch performance metrics from platforms like Product Hunt,
    Hacker News, and other launch platforms for benchmarking.
    """

    product_name: str
    launch_platform: str  # Product Hunt, Hacker News, etc.
    launch_date: str  # ISO date string
    upvotes: int
    comments: int
    source_url: str

    def __post_init__(self):
        """Validate fields after initialization"""
        # Validate required fields
        if not self.product_name or not self.launch_platform:
            raise ValueError("product_name and launch_platform are required")

        # Validate platform
        valid_platforms = [
            "Product Hunt", "Hacker News", "Reddit", "Indie Hackers",
            "BetaList", "AngelList", "TechCrunch", "YC Launch"
        ]
        if self.launch_platform not in valid_platforms:
            raise ValueError(f"launch_platform must be one of {valid_platforms}")

        # Validate engagement metrics (non-negative)
        if self.upvotes < 0:
            raise ValueError("upvotes cannot be negative")
        if self.comments < 0:
            raise ValueError("comments cannot be negative")

        # Validate URL
        if not self.source_url:
            raise ValueError("source_url is required")

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, json_str: str) -> 'ProductLaunchData':
        """Deserialize from JSON string"""
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class ValidationEvidence:
    """Real market data from Jina API

    Main data structure for market validation results containing
    competitor analysis, market size data, and launch benchmarks.
    """

    # From competitor analysis
    competitor_pricing: List[CompetitorPricing]  # Real pricing data

    # From industry reports
    market_size: Optional[MarketSizeData]  # TAM/SAM/growth rates

    # From launch platforms
    similar_launches: List[ProductLaunchData]  # Benchmark metrics

    # Quality metrics
    validation_score: float  # 0-100 (evidence-based)
    data_quality_score: float  # 0-100 (source credibility)
    reasoning: str  # Evidence-backed reasoning

    # Metadata
    search_queries_used: List[str]  # Jina search queries
    urls_fetched: List[str]  # Sources fetched
    total_cost: float  # Jina + LLM costs

    def __post_init__(self):
        """Validate fields after initialization"""
        # Validate score bounds
        if not (0.0 <= self.validation_score <= 100.0):
            raise ValueError("validation_score must be between 0.0 and 100.0")
        if not (0.0 <= self.data_quality_score <= 100.0):
            raise ValueError("data_quality_score must be between 0.0 and 100.0")

        # Validate cost (non-negative)
        if self.total_cost < 0:
            raise ValueError("total_cost cannot be negative")

        # Validate reasoning
        if not self.reasoning or not self.reasoning.strip():
            raise ValueError("reasoning cannot be empty")

    def to_json(self) -> str:
        """Serialize to JSON string"""
        # Convert nested objects to dictionaries
        data = asdict(self)

        # Convert nested objects to their JSON representations
        data['competitor_pricing'] = [
            json.loads(comp.to_json()) if hasattr(comp, 'to_json') else asdict(comp)
            for comp in self.competitor_pricing
        ]

        if self.market_size:
            data['market_size'] = (
                json.loads(self.market_size.to_json())
                if hasattr(self.market_size, 'to_json')
                else asdict(self.market_size)
            )

        data['similar_launches'] = [
            json.loads(launch.to_json()) if hasattr(launch, 'to_json') else asdict(launch)
            for launch in self.similar_launches
        ]

        return json.dumps(data, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> 'ValidationEvidence':
        """Deserialize from JSON string"""
        data = json.loads(json_str)

        # Recreate nested objects
        competitor_pricing = [
            CompetitorPricing(**comp_data)
            for comp_data in data['competitor_pricing']
        ]

        market_size = None
        if data.get('market_size'):
            market_size = MarketSizeData(**data['market_size'])

        similar_launches = [
            ProductLaunchData(**launch_data)
            for launch_data in data['similar_launches']
        ]

        return cls(
            competitor_pricing=competitor_pricing,
            market_size=market_size,
            similar_launches=similar_launches,
            validation_score=data['validation_score'],
            data_quality_score=data['data_quality_score'],
            reasoning=data['reasoning'],
            search_queries_used=data['search_queries_used'],
            urls_fetched=data['urls_fetched'],
            total_cost=data['total_cost']
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics from validation evidence"""
        return {
            'competitors_found': len(self.competitor_pricing),
            'market_data_available': self.market_size is not None,
            'launches_analyzed': len(self.similar_launches),
            'total_sources': len(self.urls_fetched),
            'search_queries_count': len(self.search_queries_used),
            'validation_level': self.get_validation_level()
        }

    def get_validation_level(self) -> str:
        """Determine validation level based on scores"""
        avg_score = (self.validation_score + self.data_quality_score) / 2

        if avg_score >= 80:
            return "HIGH"
        elif avg_score >= 60:
            return "MEDIUM"
        else:
            return "LOW"

    def get_quality_metrics(self) -> Dict[str, str]:
        """Get quality assessment metrics"""
        # Calculate overall quality
        avg_score = (self.validation_score + self.data_quality_score) / 2

        if avg_score >= 80:
            overall_quality = "HIGH"
        elif avg_score >= 60:
            overall_quality = "MEDIUM"
        else:
            overall_quality = "LOW"

        # Assess source diversity
        total_sources = len(self.urls_fetched)
        if total_sources >= 3:
            source_diversity = "GOOD"
        elif total_sources >= 2:
            source_diversity = "FAIR"
        else:
            source_diversity = "POOR"

        # Assess data completeness
        has_competitors = len(self.competitor_pricing) > 0
        has_market_size = self.market_size is not None
        has_launches = len(self.similar_launches) > 0

        completeness_score = sum([has_competitors, has_market_size, has_launches])
        if completeness_score == 3:
            data_completeness = "COMPLETE"
        elif completeness_score == 2:
            data_completeness = "PARTIAL"
        else:
            data_completeness = "MINIMAL"

        return {
            'overall_quality': overall_quality,
            'source_diversity': source_diversity,
            'data_completeness': data_completeness,
            'competitor_count': len(self.competitor_pricing),
            'launch_benchmarks': len(self.similar_launches)
        }

    def to_database_dict(self) -> Dict[str, Any]:
        """Convert to database-compatible dictionary"""
        return {
            'competitor_pricing': json.loads(self.to_json())['competitor_pricing'],
            'market_size': json.loads(self.to_json())['market_size'],
            'similar_launches': json.loads(self.to_json())['similar_launches'],
            'validation_score': self.validation_score,
            'data_quality_score': self.data_quality_score,
            'reasoning': self.reasoning,
            'search_queries_used': self.search_queries_used,
            'urls_fetched': self.urls_fetched,
            'total_cost': self.total_cost
        }

    @classmethod
    def from_database_dict(cls, db_dict: Dict[str, Any]) -> 'ValidationEvidence':
        """Create from database dictionary"""
        return cls(
            competitor_pricing=[
                CompetitorPricing(**comp_data)
                for comp_data in db_dict['competitor_pricing']
            ],
            market_size=(
                MarketSizeData(**db_dict['market_size'])
                if db_dict['market_size']
                else None
            ),
            similar_launches=[
                ProductLaunchData(**launch_data)
                for launch_data in db_dict['similar_launches']
            ],
            validation_score=db_dict['validation_score'],
            data_quality_score=db_dict['data_quality_score'],
            reasoning=db_dict['reasoning'],
            search_queries_used=db_dict['search_queries_used'],
            urls_fetched=db_dict['urls_fetched'],
            total_cost=db_dict['total_cost']
        )

    def to_analysis_result_format(self) -> Dict[str, Any]:
        """Convert to AnalysisResult-compatible format for Pipeline v3"""
        return {
            'jina_validation_score': self.validation_score,
            'jina_data_quality_score': self.data_quality_score,
            'jina_competitor_count': len(self.competitor_pricing),
            'jina_market_size_tam': self.market_size.tam_value if self.market_size else None,
            'jina_market_size_growth': self.market_size.growth_rate if self.market_size else None,
            'jina_evidence_urls': self.urls_fetched,
            'jina_api_cost_usd': self.total_cost,
            'validation_level': self.get_validation_level(),
            'quality_metrics': self.get_quality_metrics()
        }

    def get_cost_analysis(self) -> Dict[str, Any]:
        """Get detailed cost analysis"""
        return {
            'total_cost': self.total_cost,
            'cost_per_competitor': (
                self.total_cost / len(self.competitor_pricing)
                if self.competitor_pricing else 0
            ),
            'cost_per_source': (
                self.total_cost / len(self.urls_fetched)
                if self.urls_fetched else 0
            ),
            'cost_breakdown_available': True  # Could be expanded with detailed breakdown
        }

    def get_cost_optimization_recommendations(self) -> List[str]:
        """Get cost optimization recommendations"""
        recommendations = []

        # Analyze current usage patterns
        if len(self.urls_fetched) > 10:
            recommendations.append("Consider reducing the number of sources to optimize cost")

        if len(self.competitor_pricing) > 5:
            recommendations.append("Focus on top 5 competitors to reduce extraction costs")

        if self.total_cost > 0.01:
            recommendations.append("Implement caching for frequently accessed competitor data")

        if not self.urls_fetched:
            recommendations.append("No data fetched - consider if market validation is necessary")

        # Add general recommendations
        recommendations.extend([
            "Use selective validation for opportunities with scores > 70",
            "Implement tiered validation strategy (basic vs comprehensive)",
            "Cache market size data for 30 days (changes infrequently)"
        ])

        return recommendations