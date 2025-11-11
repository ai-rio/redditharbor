#!/usr/bin/env python3
"""
RedditHarbor 60+ Score Hunter
Specialized ultra-rare opportunity detection system for exceptional app opportunities

Based on E2E testing showing 50+ scores are extremely rare (0% in 217 posts),
60+ opportunities are expected to be ultra-rare unicorns requiring specialized detection.
"""

import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv(project_root / '.env.local')

import os

from agent_tools.opportunity_analyzer_agent import OpportunityAnalyzerAgent
from scripts.batch_opportunity_scoring import LLMProfiler
from supabase import create_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error_log/score_hunter_60_plus.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class UltraRareOpportunity:
    """Structure for ultra-rare opportunity tracking"""
    opportunity_id: str
    score: float
    confidence_level: str  # "High", "Medium", "Speculative"
    rarity_tier: str  # "Legendary" (70+), "Epic" (60-69), "Rare" (50-59)
    discovery_method: str
    validation_status: str
    market_size_estimate: str
    competitive_advantage: str
    timestamp: str

class ScoreHunter60Plus:
    """Specialized hunter for ultra-rare 60+ scoring opportunities"""

    def __init__(self):
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

        self.agent = OpportunityAnalyzerAgent()
        self.profiler = LLMProfiler()

        # Ultra-rare opportunity characteristics based on methodology analysis
        self.ultra_rare_indicators = {
            # Market Demand Signals (35% weight)
            'market_signals': {
                'explosive_growth': ['explosive', 'viral', 'skyrocketing', 'overnight success'],
                'massive_pain': ['desperate', 'urgent', 'critical', 'emergency', 'breaking point'],
                'high_stakes': ['millions', 'seven figures', 'life changing', 'career defining'],
                'enterprise_need': ['company-wide', 'department-wide', 'team-wide', 'organizational']
            },

            # Pain Intensity Signals (40% weight)
            'pain_signals': {
                'extreme_frustration': ['hell', 'nightmare', 'disaster', 'catastrophe', 'unbearable'],
                'business_critical': ['revenue loss', 'customer churn', 'competitive disadvantage', 'market share'],
                'time_sensitive': ['deadline', 'time is money', 'losing money daily', 'urgent need'],
                'complex_workarounds': ['10+ steps', 'hours of work', 'manual processes', 'spreadsheets hell']
            },

            # Monetization Signals (25% weight)
            'monetization_signals': {
                'high_willingness_to_pay': ['pay anything', 'budget allocated', 'approved purchase', 'expense approved'],
                'business_model': ['enterprise', 'b2b saas', 'high ticket', 'premium solution'],
                'revenue_potential': ['six figures', 'seven figures', 'million dollar', 'unicorn'],
                'recurring_revenue': ['subscription mandatory', 'monthly fee', 'annual contract', 'retention critical']
            }
        }

    def calculate_ultra_rare_score(self, submission_data: dict[str, Any]) -> dict[str, Any]:
        """
        Enhanced scoring specifically for ultra-rare opportunities
        Uses weighted indicators optimized for 60+ detection
        """
        text = submission_data.get("text", "").lower()
        title = submission_data.get("title", "").lower()
        combined_text = f"{title} {text}"

        scores = {
            'market_explosiveness': 0,
            'pain_intensity': 0,
            'monetization_potential': 0,
            'simplicity_bonus': 0,
            'virality_signals': 0
        }

        # Calculate Market Explosiveness (0-100)
        for category, signals in self.ultra_rare_indicators['market_signals'].items():
            for signal in signals:
                if signal in combined_text:
                    weights = {
                        'explosive_growth': 30,
                        'massive_pain': 25,
                        'high_stakes': 35,
                        'enterprise_need': 40
                    }
                    scores['market_explosiveness'] += weights.get(category, 20)

        # Calculate Pain Intensity (0-100)
        for category, signals in self.ultra_rare_indicators['pain_signals'].items():
            for signal in signals:
                if signal in combined_text:
                    weights = {
                        'extreme_frustration': 35,
                        'business_critical': 40,
                        'time_sensitive': 30,
                        'complex_workarounds': 25
                    }
                    scores['pain_intensity'] += weights.get(category, 20)

        # Calculate Monetization Potential (0-100)
        for category, signals in self.ultra_rare_indicators['monetization_signals'].items():
            for signal in combined_text:
                weights = {
                    'high_willingness_to_pay': 40,
                    'business_model': 35,
                    'revenue_potential': 45,
                    'recurring_revenue': 30
                }
                scores['monetization_potential'] += weights.get(category, 25)

        # Cap scores at 100
        for key in scores:
            scores[key] = min(100, scores[key])

        # Calculate weighted ultra-rare score
        ultra_rare_score = (
            scores['market_explosiveness'] * 0.30 +
            scores['pain_intensity'] * 0.40 +
            scores['monetization_potential'] * 0.25 +
            scores['simplicity_bonus'] * 0.05
        )

        return {
            'ultra_rare_score': round(ultra_rare_score, 1),
            'component_scores': scores,
            'raw_indicators': self._extract_raw_indicators(combined_text),
            'assessment': self._assess_ultra_rare_potential(scores, ultra_rare_score)
        }

    def _extract_raw_indicators(self, text: str) -> dict[str, list[str]]:
        """Extract specific indicators found in the text"""
        found_indicators = {}

        for category, signals in self.ultra_rare_indicators.items():
            found_indicators[category] = []
            for signal_list in signals.values():
                for signal in signal_list:
                    if signal in text:
                        found_indicators[category].append(signal)

        return found_indicators

    def _assess_ultra_rare_potential(self, scores: dict[str, float], ultra_score: float) -> dict[str, Any]:
        """Assess the potential classification of ultra-rare opportunity"""

        if ultra_score >= 70:
            tier = "Legendary"
            confidence = "High"
            description = "Unicorn-level opportunity - extremely rare transformational potential"
        elif ultra_score >= 60:
            tier = "Epic"
            confidence = "Medium-High"
            description = "Exceptional opportunity - rare high-impact potential"
        elif ultra_score >= 50:
            tier = "Rare"
            confidence = "Medium"
            description = "High-value opportunity - uncommon market potential"
        else:
            tier = "Common"
            confidence = "Low"
            description = "Standard opportunity - typical market potential"

        return {
            'tier': tier,
            'confidence': confidence,
            'description': description,
            'market_size_estimate': self._estimate_market_size(scores),
            'competitive_advantage': self._assess_competitive_advantage(scores)
        }

    def _estimate_market_size(self, scores: dict[str, float]) -> str:
        """Estimate market size based on scoring components"""
        overall_score = sum(scores.values()) / len(scores)

        if overall_score >= 80:
            return "Billion-dollar market potential"
        elif overall_score >= 70:
            return "Hundred-million-dollar market potential"
        elif overall_score >= 60:
            return "Ten-million-dollar market potential"
        elif overall_score >= 50:
            return "Million-dollar market potential"
        else:
            return "Sub-million-dollar niche"

    def _assess_competitive_advantage(self, scores: dict[str, float]) -> str:
        """Assess potential competitive advantage"""
        if scores['market_explosiveness'] >= 70:
            return "First-mover advantage in emerging market"
        elif scores['pain_intensity'] >= 70:
            return "Pain-killer solution with strong moat"
        elif scores['monetization_potential'] >= 70:
            return "Premium positioning with pricing power"
        else:
            return "Incremental improvement opportunity"

    def hunt_ultra_rare_opportunities(self, limit: int = 100) -> list[UltraRareOpportunity]:
        """
        Hunt for ultra-rare 60+ scoring opportunities in recent submissions
        """
        logger.info("🔍 Starting 60+ Score Hunter - Ultra-Rare Opportunity Detection")
        logger.info(f"🎯 Analyzing up to {limit} recent submissions for unicorn potential")

        # Fetch recent submissions (last 7 days)
        cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()

        try:
            result = self.supabase.table('submissions').select('*').gte(
                'created_at', cutoff_date
            ).order('created_at', desc=True).limit(limit).execute()

            submissions = result.data or []
            logger.info(f"📊 Found {len(submissions)} recent submissions to analyze")

        except Exception as e:
            logger.error(f"❌ Error fetching submissions: {e}")
            return []

        ultra_rare_opportunities = []

        for i, submission in enumerate(submissions):
            if i % 10 == 0:
                logger.info(f"🔍 Processing submission {i+1}/{len(submissions)}")

            try:
                # Calculate ultra-rare score
                ultra_rare_analysis = self.calculate_ultra_rare_score(submission)
                ultra_score = ultra_rare_analysis['ultra_rare_score']

                # Only consider opportunities with potential for 60+
                if ultra_score >= 45:  # Threshold for further analysis
                    logger.info(f"🎯 High-potential candidate found: {ultra_score} - {submission.get('title', 'Unknown')[:50]}...")

                    # Run full AI profiling for high-potential candidates
                    ai_profile = self.profiler.profile_submission(submission)

                    if ai_profile and ai_profile.get('opportunity_score', 0) >= 50:
                        opportunity = UltraRareOpportunity(
                            opportunity_id=submission.get('id', 'unknown'),
                            score=ai_profile.get('opportunity_score', 0),
                            confidence_level=ultra_rare_analysis['assessment']['confidence'],
                            rarity_tier=ultra_rare_analysis['assessment']['tier'],
                            discovery_method='ultra_rare_scanner',
                            validation_status='candidate',
                            market_size_estimate=ultra_rare_analysis['assessment']['market_size_estimate'],
                            competitive_advantage=ultra_rare_analysis['assessment']['competitive_advantage'],
                            timestamp=datetime.now().isoformat()
                        )

                        ultra_rare_opportunities.append(opportunity)

                        if opportunity.score >= 60:
                            logger.info(f"🌟 EPIC FIND: {opportunity.score} - {submission.get('title', 'Unknown')[:80]}...")
                        elif opportunity.score >= 50:
                            logger.info(f"⭐ RARE FIND: {opportunity.score} - {submission.get('title', 'Unknown')[:80]}...")

            except Exception as e:
                logger.error(f"❌ Error processing submission {submission.get('id')}: {e}")
                continue

        # Sort by score (highest first)
        ultra_rare_opportunities.sort(key=lambda x: x.score, reverse=True)

        # Store ultra-rare findings
        if ultra_rare_opportunities:
            self._store_ultra_rare_findings(ultra_rare_opportunities)

        return ultra_rare_opportunities

    def _store_ultra_rare_findings(self, opportunities: list[UltraRareOpportunity]):
        """Store ultra-rare opportunity findings to dedicated table"""
        try:
            findings_data = []
            for opp in opportunities:
                findings_data.append({
                    'opportunity_id': opp.opportunity_id,
                    'score': opp.score,
                    'confidence_level': opp.confidence_level,
                    'rarity_tier': opp.rarity_tier,
                    'discovery_method': opp.discovery_method,
                    'validation_status': opp.validation_status,
                    'market_size_estimate': opp.market_size_estimate,
                    'competitive_advantage': opp.competitive_advantage,
                    'discovery_timestamp': opp.timestamp,
                    'hunter_version': '1.0'
                })

            self.supabase.table('ultra_rare_opportunities').upsert(
                findings_data, on_conflict='opportunity_id'
            ).execute()

            logger.info(f"📊 Stored {len(findings_data)} ultra-rare opportunity findings")

        except Exception as e:
            logger.error(f"❌ Error storing ultra-rare findings: {e}")

    def generate_hunter_report(self, opportunities: list[UltraRareOpportunity]) -> dict[str, Any]:
        """Generate comprehensive hunter report"""
        legendary_count = len([o for o in opportunities if o.rarity_tier == "Legendary"])
        epic_count = len([o for o in opportunities if o.rarity_tier == "Epic"])
        rare_count = len([o for o in opportunities if o.rarity_tier == "Rare"])

        high_confidence = len([o for o in opportunities if o.confidence_level == "High"])

        report = {
            'hunt_timestamp': datetime.now().isoformat(),
            'total_candidates': len(opportunities),
            'legendary_opportunities': legendary_count,
            'epic_opportunities': epic_count,
            'rare_opportunities': rare_count,
            'high_confidence_findings': high_confidence,
            'hit_rate': {
                'overall': f"{len(opportunities) / 100:.1%}" if opportunities else "0%",
                'legendary': f"{legendary_count / 100:.2%}" if legendary_count else "0%",
                'epic': f"{epic_count / 100:.2%}" if epic_count else "0%"
            },
            'top_opportunities': [
                {
                    'id': opp.opportunity_id,
                    'score': opp.score,
                    'tier': opp.rarity_tier,
                    'confidence': opp.confidence_level,
                    'market_size': opp.market_size_estimate
                }
                for opp in opportunities[:10]
            ]
        }

        return report

def main():
    """Main execution function for 60+ score hunter"""
    logger.info("🚀 RedditHarbor 60+ Score Hunter")
    logger.info("🔍 Specialized ultra-rare opportunity detection")

    hunter = ScoreHunter60Plus()

    # Hunt for ultra-rare opportunities
    opportunities = hunter.hunt_ultra_rare_opportunities(limit=200)

    # Generate and display report
    report = hunter.generate_hunter_report(opportunities)

    logger.info("\n🎯 60+ SCORE HUNTER REPORT")
    logger.info("=" * 50)
    logger.info("📊 Total candidates analyzed: 200")
    logger.info(f"⭐ Ultra-rare opportunities found: {report['total_candidates']}")
    logger.info(f"🌟 Legendary (70+): {report['legendary_opportunities']}")
    logger.info(f"🔥 Epic (60-69): {report['epic_opportunities']}")
    logger.info(f"💎 Rare (50-59): {report['rare_opportunities']}")
    logger.info(f"🎯 High confidence: {report['high_confidence_findings']}")
    logger.info(f"📈 Overall hit rate: {report['hit_rate']['overall']}")

    if report['top_opportunities']:
        logger.info("\n🏆 TOP ULTRA-RARE OPPORTUNITIES:")
        for i, opp in enumerate(report['top_opportunities'][:5], 1):
            logger.info(f"   {i}. [{opp['score']}] {opp['tier']} - {opp['confidence']} confidence")

    logger.info(f"\n✅ 60+ Score Hunter completed at {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()
