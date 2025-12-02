"""
Analysis validation and quality checking module
"""

import logging
from typing import List

from models.analysis import AnalysisResult, AppIdea, MarketMetrics

logger = logging.getLogger(__name__)


class AnalysisValidator:
    """
    Validates analysis results for quality, consistency, and business viability
    """

    def __init__(self):
        """Initialize validator with quality thresholds"""
        self.min_final_score = 30.0
        self.min_confidence_score = 40.0
        self.max_core_functions = 3

    def validate_analysis(self, analysis: AnalysisResult) -> bool:
        """
        Comprehensive validation of analysis result

        Args:
            analysis: AnalysisResult to validate

        Returns:
            True if analysis passes all validation checks
        """
        validation_results = []

        # Core validation checks
        validation_results.append(self._validate_app_idea(analysis.app_idea))
        validation_results.append(self._validate_market_metrics(analysis.market_metrics))
        validation_results.append(self._validate_scores(analysis))
        validation_results.append(self._validate_trust_level(analysis))
        validation_results.append(self._validate_business_logic(analysis))

        # Log validation results
        passed_checks = sum(validation_results)
        total_checks = len(validation_results)

        if passed_checks == total_checks:
            logger.debug(f"Analysis {analysis.submission_id} passed all {total_checks} validation checks")
            return True
        else:
            logger.warning(
                f"Analysis {analysis.submission_id} failed {total_checks - passed_checks}/{total_checks} validation checks"
            )
            return False

    def _validate_app_idea(self, app_idea: AppIdea) -> bool:
        """Validate app idea structure and content"""
        try:
            # Check title length
            if not (5 <= len(app_idea.title.strip()) <= 100):
                logger.warning(f"Invalid title length: {len(app_idea.title)}")
                return False

            # Check core functions count and quality
            if not (1 <= len(app_idea.core_functions) <= self.max_core_functions):
                logger.warning(f"Invalid core functions count: {len(app_idea.core_functions)}")
                return False

            # Validate each core function
            for func in app_idea.core_functions:
                if not (5 <= len(func.strip()) <= 100):
                    logger.warning(f"Invalid core function length: {len(func)}")
                    return False

            # Check concept and problem statement length
            if not (10 <= len(app_idea.app_concept.strip()) <= 500):
                logger.warning(f"Invalid concept length: {len(app_idea.app_concept)}")
                return False

            if not (10 <= len(app_idea.problem_statement.strip()) <= 1000):
                logger.warning(f"Invalid problem statement length: {len(app_idea.problem_statement)}")
                return False

            # Check target audience
            if not (10 <= len(app_idea.target_audience.strip()) <= 500):
                logger.warning(f"Invalid target audience length: {len(app_idea.target_audience)}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating app idea: {e}")
            return False

    def _validate_market_metrics(self, metrics: MarketMetrics) -> bool:
        """Validate market metrics are within acceptable ranges"""
        try:
            metric_fields = [
                'market_demand', 'pain_intensity', 'monetization_potential',
                'competition_level', 'technical_feasibility'
            ]

            for field in metric_fields:
                value = getattr(metrics, field)
                if not (0.0 <= value <= 100.0):
                    logger.warning(f"Invalid {field}: {value} (must be 0-100)")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating market metrics: {e}")
            return False

    def _validate_scores(self, analysis: AnalysisResult) -> bool:
        """Validate final score and confidence score"""
        try:
            # Check final score range
            if not (0.0 <= analysis.final_score <= 100.0):
                logger.warning(f"Invalid final score: {analysis.final_score}")
                return False

            # Check confidence score range
            if not (0.0 <= analysis.confidence_score <= 100.0):
                logger.warning(f"Invalid confidence score: {analysis.confidence_score}")
                return False

            # Check minimum thresholds
            if analysis.final_score < self.min_final_score:
                logger.warning(f"Final score below threshold: {analysis.final_score} < {self.min_final_score}")
                return False

            if analysis.confidence_score < self.min_confidence_score:
                logger.warning(f"Confidence score below threshold: {analysis.confidence_score} < {self.min_confidence_score}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating scores: {e}")
            return False

    def _validate_trust_level(self, analysis: AnalysisResult) -> bool:
        """Validate trust level value"""
        try:
            valid_trust_levels = ["LOW", "MEDIUM", "HIGH"]
            if analysis.trust_level not in valid_trust_levels:
                logger.warning(f"Invalid trust level: {analysis.trust_level}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating trust level: {e}")
            return False

    def _validate_business_logic(self, analysis: AnalysisResult) -> bool:
        """Validate business logic consistency"""
        try:
            metrics = analysis.market_metrics

            # Consistency check: final score should correlate with key metrics
            # (allowing some variance for LLM judgment)
            expected_avg = (
                metrics.market_demand + metrics.pain_intensity + metrics.monetization_potential
            ) / 3

            # Allow 25 point variance
            if abs(analysis.final_score - expected_avg) > 25:
                logger.warning(
                    f"Score inconsistency: final={analysis.final_score}, expected~={expected_avg:.1f}"
                )
                # Don't fail validation, just warn - LLM might have valid reasoning

            # Business logic: high pain intensity should correlate with high market demand
            if metrics.pain_intensity > 80 and metrics.market_demand < 50:
                logger.warning(
                    f"Business logic warning: high pain ({metrics.pain_intensity}) but low demand ({metrics.market_demand})"
                )

            # Technical feasibility should be reasonable for 1-3 function apps
            if len(analysis.app_idea.core_functions) <= 2 and metrics.technical_feasibility < 60:
                logger.warning(
                    f"Feasibility warning: simple app ({len(analysis.app_idea.core_functions)} functions) but low technical feasibility ({metrics.technical_feasibility})"
                )

            return True

        except Exception as e:
            logger.error(f"Error validating business logic: {e}")
            return False

    def filter_high_quality_analyses(
        self,
        analyses: List[AnalysisResult],
        min_score: float = 70.0,
        min_confidence: float = 60.0
    ) -> List[AnalysisResult]:
        """
        Filter analyses for high quality results

        Args:
            analyses: List of analyses to filter
            min_score: Minimum final score threshold
            min_confidence: Minimum confidence score threshold

        Returns:
            List of high quality analyses
        """
        logger.info(f"Filtering {len(analyses)} analyses for high quality results")

        high_quality = []
        for analysis in analyses:
            if (self.validate_analysis(analysis) and
                analysis.final_score >= min_score and
                analysis.confidence_score >= min_confidence):
                high_quality.append(analysis)

        logger.info(f"✓ Found {len(high_quality)} high quality analyses ({len(high_quality)/len(analyses)*100:.1f}%)")
        return high_quality

    def get_quality_summary(self, analyses: List[AnalysisResult]) -> dict:
        """
        Generate quality summary statistics for a batch of analyses

        Args:
            analyses: List of analyses to summarize

        Returns:
            Dictionary with quality statistics
        """
        if not analyses:
            return {"total": 0}

        total = len(analyses)
        valid_count = sum(1 for a in analyses if self.validate_analysis(a))
        high_score_count = sum(1 for a in analyses if a.final_score >= 70.0)
        high_confidence_count = sum(1 for a in analyses if a.confidence_score >= 60.0)

        # Score distribution
        high_trust = sum(1 for a in analyses if a.trust_level == "HIGH")
        medium_trust = sum(1 for a in analyses if a.trust_level == "MEDIUM")
        low_trust = sum(1 for a in analyses if a.trust_level == "LOW")

        # Average scores
        avg_final_score = sum(a.final_score for a in analyses) / total
        avg_confidence = sum(a.confidence_score for a in analyses) / total

        return {
            "total": total,
            "valid": valid_count,
            "validation_rate": valid_count / total * 100,
            "high_score": high_score_count,
            "high_score_rate": high_score_count / total * 100,
            "high_confidence": high_confidence_count,
            "high_confidence_rate": high_confidence_count / total * 100,
            "trust_distribution": {
                "HIGH": high_trust,
                "MEDIUM": medium_trust,
                "LOW": low_trust
            },
            "avg_final_score": avg_final_score,
            "avg_confidence_score": avg_confidence
        }