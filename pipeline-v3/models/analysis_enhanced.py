"""
Enhanced AnalysisResult with Jina ValidationEvidence Integration

This module extends the existing AnalysisResult model to include
ValidationEvidence fields for Phase 3 Jina Market Research Integration.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union

from pydantic import BaseModel, Field

# Import the base models
from models.analysis import AnalysisResult, AppIdea, MarketMetrics

# Import ValidationEvidence
try:
    from transform.validation_evidence_pydantic import ValidationEvidence
except ImportError:
    try:
        from transform.validation_evidence import ValidationEvidence
    except ImportError:
        # Fallback if neither is available
        ValidationEvidence = None


class AnalysisResultWithJina(AnalysisResult):
    """
    Extended AnalysisResult with Jina ValidationEvidence support

    This extends the base AnalysisResult to include market validation
    evidence from Jina API integration as specified in Phase 3.
    """

    # Jina Market Research fields (from Phase 3 documentation)
    jina_validation_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Jina market research validation score (0-100)"
    )
    jina_data_quality_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Quality score of Jina-extracted data (0-100)"
    )
    jina_competitor_count: Optional[int] = Field(
        None,
        ge=0,
        description="Number of competitors analyzed by Jina"
    )
    jina_market_size_tam: Optional[str] = Field(
        None,
        description="Total Addressable Market size from Jina research"
    )
    jina_market_size_growth: Optional[str] = Field(
        None,
        description="Market growth rate from Jina research"
    )
    jina_evidence_urls: Optional[List[str]] = Field(
        default_factory=list,
        description="List of evidence URLs fetched by Jina"
    )
    jina_api_cost_usd: Optional[float] = Field(
        None,
        ge=0.0,
        description="Total Jina API cost in USD"
    )
    jina_cache_hit_rate: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Jina API cache hit rate (0-1)"
    )

    # Validation metadata
    validation_evidence: Optional[Dict[str, Any]] = Field(
        None,
        description="Full ValidationEvidence data structure"
    )
    validation_level: Optional[str] = Field(
        None,
        description="Validation level (LOW, MEDIUM, HIGH)"
    )

    class Config:
        """Pydantic configuration"""
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    def from_base_analysis_result(
        cls,
        base_result: AnalysisResult,
        validation_evidence: Optional[Dict[str, Any]] = None
    ) -> 'AnalysisResultWithJina':
        """
        Create enhanced AnalysisResult from base AnalysisResult and validation evidence

        Args:
            base_result: Base AnalysisResult instance
            validation_evidence: ValidationEvidence data dictionary

        Returns:
            Enhanced AnalysisResultWithJina instance
        """
        # Extract base fields
        base_data = base_result.model_dump()

        # Add Jina fields from validation evidence
        if validation_evidence:
            jina_fields = {
                "jina_validation_score": validation_evidence.get("validation_score"),
                "jina_data_quality_score": validation_evidence.get("data_quality_score"),
                "jina_competitor_count": len(validation_evidence.get("competitor_pricing", [])),
                "jina_market_size_tam": (
                    validation_evidence.get("market_size", {}).get("tam_value")
                    if validation_evidence.get("market_size")
                    else None
                ),
                "jina_market_size_growth": (
                    validation_evidence.get("market_size", {}).get("growth_rate")
                    if validation_evidence.get("market_size")
                    else None
                ),
                "jina_evidence_urls": validation_evidence.get("urls_fetched", []),
                "jina_api_cost_usd": validation_evidence.get("total_cost", 0.0),
                "validation_evidence": validation_evidence,
                "validation_level": validation_evidence.get("quality_metrics", {}).get("overall_quality")
            }
            base_data.update(jina_fields)

        return cls(**base_data)

    def get_enhanced_summary(self) -> Dict[str, Any]:
        """
        Get enhanced summary including Jina validation data

        Returns:
            Summary dictionary with base and Jina data
        """
        base_summary = {
            "submission_id": self.submission_id,
            "final_score": self.final_score,
            "trust_level": self.trust_level,
            "app_title": self.app_idea.title,
            "market_demand": self.market_metrics.market_demand,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None
        }

        if self.jina_validation_score is not None:
            jina_summary = {
                "jina_validation_score": self.jina_validation_score,
                "jina_data_quality_score": self.jina_data_quality_score,
                "jina_competitor_count": self.jina_competitor_count,
                "jina_market_size_tam": self.jina_market_size_tam,
                "jina_market_size_growth": self.jina_market_size_growth,
                "jina_evidence_count": len(self.jina_evidence_urls) if self.jina_evidence_urls else 0,
                "jina_api_cost_usd": self.jina_api_cost_usd,
                "validation_level": self.validation_level
            }
            base_summary.update({"jina_research": jina_summary})

        return base_summary

    def has_jina_validation(self) -> bool:
        """
        Check if this analysis result has Jina validation data

        Returns:
            True if Jina validation data is present
        """
        return self.jina_validation_score is not None

    def get_validation_quality_rating(self) -> str:
        """
        Get overall validation quality rating

        Returns:
            Quality rating string
        """
        if not self.has_jina_validation():
            return "NO_VALIDATION"

        if self.jina_validation_score >= 80 and self.jina_data_quality_score >= 80:
            return "HIGH_QUALITY"
        elif self.jina_validation_score >= 60 and self.jina_data_quality_score >= 60:
            return "MEDIUM_QUALITY"
        else:
            return "LOW_QUALITY"

    def get_market_insights(self) -> Dict[str, Any]:
        """
        Get market insights from validation evidence

        Returns:
            Market insights dictionary
        """
        insights = {}

        if self.validation_evidence:
            evidence = self.validation_evidence

            # Competitor insights
            competitors = evidence.get("competitor_pricing", [])
            if competitors:
                insights["competitors"] = {
                    "count": len(competitors),
                    "pricing_models": list(set(comp.get("pricing_model") for comp in competitors)),
                    "average_confidence": sum(comp.get("confidence", 0) for comp in competitors) / len(competitors),
                    "top_competitors": [comp.get("company") for comp in competitors[:3]]
                }

            # Market size insights
            market_size = evidence.get("market_size")
            if market_size:
                insights["market_size"] = {
                    "tam": market_size.get("tam_value"),
                    "growth_rate": market_size.get("growth_rate"),
                    "source": market_size.get("source_name")
                }

            # Launch insights
            launches = evidence.get("similar_launches", [])
            if launches:
                insights["product_launches"] = {
                    "count": len(launches),
                    "total_upvotes": sum(launch.get("upvotes", 0) for launch in launches),
                    "platforms": list(set(launch.get("platform") for launch in launches)),
                    "average_engagement": sum(launch.get("upvotes", 0) + launch.get("comments", 0) for launch in launches) / len(launches)
                }

        return insights


def create_analysis_result_with_jina(
    submission_id: str,
    app_idea: AppIdea,
    market_metrics: MarketMetrics,
    final_score: float,
    content_quality_score: float,
    confidence_score: float,
    trust_level: str,
    validation_evidence: Optional[Dict[str, Any]] = None,
    jina_cost: Optional[float] = None,
    is_spam: bool = False,
    spam_indicators: Optional[List[str]] = None
) -> AnalysisResultWithJina:
    """
    Factory function to create AnalysisResultWithJina with proper field mapping

    Args:
        submission_id: Source Reddit submission ID
        app_idea: App idea analysis
        market_metrics: Market analysis metrics
        final_score: Final opportunity score
        content_quality_score: AI content quality score
        confidence_score: Confidence in analysis
        trust_level: Trust level string
        validation_evidence: ValidationEvidence data
        jina_cost: Jina API cost
        is_spam: Whether content is spam
        spam_indicators: List of spam indicators

    Returns:
        AnalysisResultWithJina instance
    """
    # Create base AnalysisResult first
    base_result = AnalysisResult(
        submission_id=submission_id,
        app_idea=app_idea,
        market_metrics=market_metrics,
        final_score=final_score,
        content_quality_score=content_quality_score,
        is_spam=is_spam,
        spam_indicators=spam_indicators or [],
        confidence_score=confidence_score,
        trust_level=trust_level,
        embedding=None,
        embedding_metadata=None
    )

    # Convert to enhanced version with Jina data
    return AnalysisResultWithJina.from_base_analysis_result(
        base_result=base_result,
        validation_evidence=validation_evidence
    )


# Factory function for creating enhanced results from Agno analyzer
def create_enhanced_result_from_agno(
    agno_result: Dict[str, Any],
    validation_evidence: Optional[Dict[str, Any]] = None
) -> AnalysisResultWithJina:
    """
    Create enhanced AnalysisResult from Agno analyzer output

    Args:
        agno_result: Agno analyzer output dictionary
        validation_evidence: ValidationEvidence data

    Returns:
        AnalysisResultWithJina instance
    """
    # Map Agno fields to AnalysisResult fields
    app_idea = AppIdea(
        title=agno_result.get("app_title", "Generated App Idea"),
        app_concept=agno_result.get("app_concept", "AI-generated app concept"),
        problem_statement=agno_result.get("problem_statement", "Problem statement"),
        core_functions=agno_result.get("core_functions", ["Feature 1", "Feature 2"]),
        target_audience=agno_result.get("target_audience", "Target audience")
    )

    market_metrics = MarketMetrics(
        market_demand=agno_result.get("market_demand", 50.0),
        pain_intensity=agno_result.get("pain_intensity", 50.0),
        monetization_potential=agno_result.get("monetization_potential", 50.0),
        competition_level=agno_result.get("competition_level", 50.0),
        technical_feasibility=agno_result.get("technical_feasibility", 80.0)
    )

    return AnalysisResultWithJina(
        submission_id=agno_result.get("submission_id", "unknown"),
        app_idea=app_idea,
        market_metrics=market_metrics,
        final_score=agno_result.get("final_score", 50.0),
        content_quality_score=agno_result.get("content_quality_score", 75.0),
        confidence_score=agno_result.get("confidence_score", 70.0),
        trust_level=agno_result.get("trust_level", "MEDIUM"),
        jina_validation_score=validation_evidence.get("validation_score") if validation_evidence else None,
        jina_data_quality_score=validation_evidence.get("data_quality_score") if validation_evidence else None,
        jina_competitor_count=len(validation_evidence.get("competitor_pricing", [])) if validation_evidence else None,
        jina_market_size_tam=validation_evidence.get("market_size", {}).get("tam_value") if validation_evidence and validation_evidence.get("market_size") else None,
        jina_market_size_growth=validation_evidence.get("market_size", {}).get("growth_rate") if validation_evidence and validation_evidence.get("market_size") else None,
        jina_evidence_urls=validation_evidence.get("urls_fetched", []) if validation_evidence else [],
        jina_api_cost_usd=validation_evidence.get("total_cost", 0.0) if validation_evidence else None,
        validation_evidence=validation_evidence,
        validation_level=validation_evidence.get("quality_metrics", {}).get("overall_quality") if validation_evidence else None,
        embedding=None,
        embedding_metadata=None
    )