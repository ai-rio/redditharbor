"""Deduplication cost savings statistics.

This module tracks and reports cost savings from deduplication. Provides
visibility into the $3,528/year savings achieved by preventing redundant
AI analyses.

Key Features:
- Calculate cost savings by analysis type
- Track skip and copy statistics
- Project monthly and yearly savings
- Report savings by category
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class DeduplicationStatsUpdater:
    """
    Track and update deduplication cost savings.

    Manages statistics and cost calculations for deduplication skip logic.
    Provides reporting on savings achieved by preventing redundant analyses.

    Attributes:
        client: Initialized Supabase client
        AGNO_ANALYSIS_COST: Cost per Agno analysis ($0.15)
        PROFILER_ANALYSIS_COST: Cost per Profiler analysis ($0.05)

    Examples:
        >>> from supabase import create_client
        >>> client = create_client(url, key)
        >>> updater = DeduplicationStatsUpdater(client)
        >>> savings = updater.update_savings('agno', skipped=10, copied=5)
        >>> assert savings == 2.25  # (10 + 5) * $0.15
    """

    # Cost per analysis (based on average token usage and pricing)
    AGNO_ANALYSIS_COST = 0.15  # $0.15 per monetization analysis
    PROFILER_ANALYSIS_COST = 0.05  # $0.05 per profiler analysis

    def __init__(self, supabase_client: Any):
        """
        Initialize deduplication stats updater.

        Args:
            supabase_client: Initialized Supabase client
        """
        self.client = supabase_client

    def update_savings(
        self,
        analysis_type: str,
        skipped_count: int,
        copied_count: int,
    ) -> float:
        """
        Calculate and record cost savings.

        Computes total savings based on analyses that were skipped or copied
        instead of running fresh analyses.

        Args:
            analysis_type: Type of analysis ('agno' or 'profiler')
            skipped_count: Number of analyses skipped
            copied_count: Number of analyses copied

        Returns:
            float: Total savings amount in dollars

        Examples:
            >>> updater = DeduplicationStatsUpdater(client)
            >>> # 10 skipped + 5 copied Agno analyses
            >>> savings = updater.update_savings('agno', 10, 5)
            >>> assert savings == 2.25  # 15 * $0.15
            >>>
            >>> # 20 skipped + 10 copied Profiler analyses
            >>> savings = updater.update_savings('profiler', 20, 10)
            >>> assert savings == 1.50  # 30 * $0.05
        """
        cost_map = {
            "agno": self.AGNO_ANALYSIS_COST,
            "profiler": self.PROFILER_ANALYSIS_COST,
        }

        cost_per_analysis = cost_map.get(analysis_type, 0)
        total_avoided = skipped_count + copied_count
        total_saved = total_avoided * cost_per_analysis

        logger.info(
            f"{analysis_type.capitalize()} deduplication saved ${total_saved:.2f} "
            f"({skipped_count} skipped, {copied_count} copied, "
            f"${cost_per_analysis:.2f} per analysis)"
        )

        return total_saved

    def calculate_batch_savings(
        self,
        agno_stats: dict[str, int],
        profiler_stats: dict[str, int],
    ) -> dict[str, float]:
        """
        Calculate total savings for a batch run.

        Computes savings across both Agno and Profiler analyses for a
        complete batch processing run.

        Args:
            agno_stats: Dictionary with 'skipped' and 'copied' counts for Agno
            profiler_stats: Dictionary with 'skipped' and 'copied' counts for Profiler

        Returns:
            dict: Breakdown of savings with keys:
                - agno_savings: Savings from Agno deduplication
                - profiler_savings: Savings from Profiler deduplication
                - total_savings: Combined savings
                - avoided_analyses: Total number of analyses avoided

        Examples:
            >>> agno_stats = {'skipped': 10, 'copied': 5}
            >>> profiler_stats = {'skipped': 20, 'copied': 10}
            >>> savings = updater.calculate_batch_savings(agno_stats, profiler_stats)
            >>> assert savings['agno_savings'] == 2.25  # 15 * $0.15
            >>> assert savings['profiler_savings'] == 1.50  # 30 * $0.05
            >>> assert savings['total_savings'] == 3.75
        """
        agno_skipped = agno_stats.get("skipped", 0)
        agno_copied = agno_stats.get("copied", 0)
        agno_savings = self.update_savings("agno", agno_skipped, agno_copied)

        profiler_skipped = profiler_stats.get("skipped", 0)
        profiler_copied = profiler_stats.get("copied", 0)
        profiler_savings = self.update_savings("profiler", profiler_skipped, profiler_copied)

        total_savings = agno_savings + profiler_savings
        avoided_analyses = (
            agno_skipped + agno_copied + profiler_skipped + profiler_copied
        )

        return {
            "agno_savings": agno_savings,
            "profiler_savings": profiler_savings,
            "total_savings": total_savings,
            "avoided_analyses": avoided_analyses,
        }

    def project_monthly_savings(
        self,
        daily_agno_avoided: int,
        daily_profiler_avoided: int,
        days_per_month: int = 30,
    ) -> dict[str, float]:
        """
        Project monthly savings based on daily deduplication rates.

        Estimates monthly and yearly cost savings based on observed daily
        deduplication performance.

        Args:
            daily_agno_avoided: Average Agno analyses avoided per day
            daily_profiler_avoided: Average Profiler analyses avoided per day
            days_per_month: Days to project over (default: 30)

        Returns:
            dict: Projected savings with keys:
                - monthly_agno: Monthly Agno savings
                - monthly_profiler: Monthly Profiler savings
                - monthly_total: Total monthly savings
                - yearly_total: Projected yearly savings

        Examples:
            >>> # If we avoid 5 Agno and 10 Profiler analyses per day
            >>> savings = updater.project_monthly_savings(5, 10)
            >>> # Monthly Agno: 5 * 30 * $0.15 = $22.50
            >>> # Monthly Profiler: 10 * 30 * $0.05 = $15.00
            >>> # Monthly Total: $37.50
            >>> # Yearly: $37.50 * 12 = $450.00
            >>> assert savings['monthly_total'] == 37.50
            >>> assert savings['yearly_total'] == 450.00
        """
        monthly_agno = daily_agno_avoided * days_per_month * self.AGNO_ANALYSIS_COST
        monthly_profiler = (
            daily_profiler_avoided * days_per_month * self.PROFILER_ANALYSIS_COST
        )
        monthly_total = monthly_agno + monthly_profiler
        yearly_total = monthly_total * 12

        logger.info(
            f"Projected savings: ${monthly_total:.2f}/month, ${yearly_total:.2f}/year"
        )

        return {
            "monthly_agno": monthly_agno,
            "monthly_profiler": monthly_profiler,
            "monthly_total": monthly_total,
            "yearly_total": yearly_total,
        }

    def log_savings_summary(
        self,
        agno_stats: dict[str, int],
        profiler_stats: dict[str, int],
    ) -> None:
        """
        Log comprehensive savings summary.

        Provides detailed logging of deduplication performance and cost savings.
        Useful for monitoring and reporting.

        Args:
            agno_stats: Dictionary with Agno deduplication statistics
            profiler_stats: Dictionary with Profiler deduplication statistics

        Examples:
            >>> agno_stats = {'skipped': 10, 'copied': 5, 'fresh': 85, 'errors': 0}
            >>> profiler_stats = {'skipped': 20, 'copied': 10, 'fresh': 70, 'errors': 0}
            >>> updater.log_savings_summary(agno_stats, profiler_stats)
            # Logs detailed breakdown to console
        """
        savings = self.calculate_batch_savings(agno_stats, profiler_stats)

        logger.info("=" * 60)
        logger.info("DEDUPLICATION COST SAVINGS SUMMARY")
        logger.info("=" * 60)

        logger.info(
            f"Agno Deduplication: {agno_stats.get('skipped', 0)} skipped, "
            f"{agno_stats.get('copied', 0)} copied | "
            f"Savings: ${savings['agno_savings']:.2f}"
        )

        logger.info(
            f"Profiler Deduplication: {profiler_stats.get('skipped', 0)} skipped, "
            f"{profiler_stats.get('copied', 0)} copied | "
            f"Savings: ${savings['profiler_savings']:.2f}"
        )

        logger.info(f"Total Savings: ${savings['total_savings']:.2f}")
        logger.info(f"Analyses Avoided: {savings['avoided_analyses']}")

        logger.info("=" * 60)
