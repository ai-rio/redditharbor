#!/usr/bin/env .venv/bin/python
"""
RedditHarbor Real-Time Decision Dashboard
Leverages Agent SDK for intelligent decision-making based on research results
"""

import os
import sys
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
from collections import defaultdict, Counter
import re

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import Agent SDK
try:
    from claude_agent_sdk import SDKClient
except ImportError:
    print("❌ Agent SDK not installed")
    sys.exit(1)

# Import RedditHarbor components
from redditharbor.login import supabase
import config.settings as settings


class RealTimeDecisionDashboard:
    """Real-time dashboard for intelligent decision-making"""

    def __init__(self):
        self.supabase_client = supabase(
            url=settings.SUPABASE_URL,
            private_key=settings.SUPABASE_KEY
        )
        self.sdk_client = SDKClient()
        self.opportunities_cache = []
        self.decision_history = []
        self.last_analysis = {}

    async def start_decision_engine(self):
        """Start the real-time decision-making engine"""

        print("🚀 RedditHarbor Decision Engine Starting...")
        print("=" * 50)
        print("📊 Monitoring research data for opportunities...")
        print("🧠 Using AI for intelligent analysis...")
        print("⚡ Real-time decision-making active...")
        print()

        # Initialize with existing data analysis
        await self.analyze_existing_data()

        # Start continuous monitoring
        await self.continuous_decision_loop()

    async def analyze_existing_data(self):
        """Analyze existing research data to identify opportunities"""

        print("🔍 Analyzing existing research data...")

        domains = {
            "personal_finance": ["personalfinance", "poverty", "debtfree", "FinancialPlanning"],
            "skill_acquisition": ["learnprogramming", "language_learning", "learnmath"],
            "chronic_disease": ["diabetes", "ChronicPain", "ibs"],
            "budget_travel": ["solotravel", "backpacking", "travel"]
        }

        for domain, subreddits in domains.items():
            print(f"\n📊 Analyzing {domain.replace('_', ' ').title()}...")

            # Fetch data from Supabase
            data = await self.fetch_domain_data(domain, subreddits, limit=50)

            if data:
                # Use Agent SDK for analysis
                opportunities = await self.identify_opportunities_with_ai(domain, data)

                if opportunities:
                    self.opportunities_cache.extend(opportunities)
                    print(f"✅ Found {len(opportunities)} opportunities in {domain}")

                    # Display top opportunities
                    for i, opp in enumerate(opportunities[:3], 1):
                        print(f"   {i}. {opp['concept']} (Viability: {opp['viability']})")
                        print(f"      Problem: {opp['problem'][:80]}...")

        print(f"\n🎯 Total Opportunities Identified: {len(self.opportunities_cache)}")

    async def fetch_domain_data(self, domain: str, subreddits: List[str], limit: int = 50) -> List[Dict]:
        """Fetch data for a specific domain"""

        all_data = []

        for subreddit in subreddits:
            try:
                # Get recent posts with high engagement
                response = self.supabase_client.table("submission")\
                    .select("*")\
                    .eq("subreddit", subreddit)\
                    .gte("score", 10)  # Filter for posts with decent engagement\
                    .order("created_at", desc=True)\
                    .limit(limit // len(subreddits))\
                    .execute()

                if response.data:
                    all_data.extend(response.data)

            except Exception as e:
                print(f"⚠️ Error fetching from r/{subreddit}: {e}")
                continue

        return all_data

    async def identify_opportunities_with_ai(self, domain: str, data: List[Dict]) -> List[Dict]:
        """Use Agent SDK to identify business opportunities"""

        try:
            # Prepare data for AI analysis
            analysis_data = self.prepare_data_for_ai(domain, data)

            # Create AI analysis prompt
            prompt = f"""
            Analyze this Reddit data from {domain.replace('_', ' ')} to identify app business opportunities.

            Data Sample:
            {analysis_data}

            Identify the TOP 3 most promising app opportunities that:
            1. Solve recurring problems mentioned in the data
            2. Have 1-3 core functionality (simple apps)
            3. Address real pain points
            4. Have good business potential

            For each opportunity, provide:
            - Problem being solved
            - App concept (1-3 sentence description)
            - Core functionality (what the app does)
            - Viability rating (High/Medium/Low)
            - Target users
            - Market size estimate (Small/Medium/Large)

            Return as JSON array of opportunities.
            """

            # Get AI analysis
            response = await self.sdk_client.query(prompt)

            # Parse AI response
            opportunities = self.parse_ai_opportunities(response, domain)

            return opportunities

        except Exception as e:
            print(f"⚠️ AI analysis failed for {domain}: {e}")
            return []

    def prepare_data_for_ai(self, domain: str, data: List[Dict]) -> str:
        """Prepare data for AI analysis"""

        # Select top posts by engagement
        sorted_data = sorted(data, key=lambda x: x.get('score', 0), reverse=True)[:20]

        sample_text = f"Domain: {domain.replace('_', ' ').title()}\n\n"
        sample_text += "TOP POSTS BY ENGAGEMENT:\n\n"

        for i, post in enumerate(sorted_data, 1):
            title = post.get('title', '').strip()
            score = post.get('score', 0)
            subreddit = post.get('subreddit', '')

            sample_text += f"{i}. [r/{subreddit}] Score: {score}\n"
            sample_text += f"   {title}\n"

            # Include content if available
            content = post.get('selftext', '').strip()
            if content and len(content) > 50:
                truncated = content[:300] + "..." if len(content) > 300 else content
                sample_text += f"   Content: {truncated}\n"

            sample_text += "\n"

        return sample_text

    def parse_ai_opportunities(self, ai_response: str, domain: str) -> List[Dict]:
        """Parse AI response to extract opportunities"""

        opportunities = []

        try:
            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())

                for opp in parsed:
                    opportunity = {
                        "domain": domain,
                        "concept": opp.get("app concept", opp.get("concept", "")),
                        "problem": opp.get("problem being solved", opp.get("problem", "")),
                        "functionality": opp.get("core functionality", ""),
                        "viability": opp.get("viability rating", opp.get("viability", "Medium")),
                        "target_users": opp.get("target users", ""),
                        "market_size": opp.get("market size estimate", "Medium"),
                        "identified_at": datetime.now().isoformat(),
                        "confidence_score": self.calculate_confidence_score(opp)
                    }
                    opportunities.append(opportunity)

            else:
                # Fallback: extract from text response
                opportunities = self.extract_from_text_response(ai_response, domain)

        except Exception as e:
            print(f"⚠️ Error parsing AI response: {e}")

        return opportunities

    def calculate_confidence_score(self, opportunity: Dict) -> float:
        """Calculate confidence score for an opportunity"""

        score = 0.5  # Base score

        # Boost for clear problem statement
        if opportunity.get("problem being solved") and len(opportunity["problem being solved"]) > 50:
            score += 0.2

        # Boost for specific viability rating
        viability = opportunity.get("viability rating", "").lower()
        if viability == "high":
            score += 0.2
        elif viability == "medium":
            score += 0.1

        # Boost for target users specification
        if opportunity.get("target users"):
            score += 0.1

        return min(score, 1.0)

    def extract_from_text_response(self, response: str, domain: str) -> List[Dict]:
        """Extract opportunities from text response when JSON parsing fails"""

        opportunities = []

        # Simple pattern matching for opportunity extraction
        lines = response.split('\n')
        current_opp = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for numbered opportunities
            if re.match(r'^\d+\.', line):
                if current_opp:
                    opportunities.append(self.create_opportunity_from_dict(current_opp, domain))
                current_opp = {"raw_text": line}
            elif current_opp:
                if "raw_text" in current_opp:
                    current_opp["raw_text"] += " " + line
                else:
                    current_opp["raw_text"] = line

        # Add last opportunity
        if current_opp:
            opportunities.append(self.create_opportunity_from_dict(current_opp, domain))

        return opportunities

    def create_opportunity_from_dict(self, opp_dict: Dict, domain: str) -> Dict:
        """Create opportunity from parsed dictionary"""

        raw_text = opp_dict.get("raw_text", "")

        return {
            "domain": domain,
            "concept": "Extracted from analysis",
            "problem": raw_text[:200],
            "functionality": "To be determined",
            "viability": "Medium",
            "target_users": "To be identified",
            "market_size": "Medium",
            "identified_at": datetime.now().isoformat(),
            "confidence_score": 0.5,
            "raw_analysis": raw_text
        }

    async def continuous_decision_loop(self):
        """Continuous loop for real-time decision-making"""

        print("\n🔄 Starting continuous decision loop...")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                # Check for new data
                await self.check_for_new_opportunities()

                # Update decision recommendations
                await self.update_decision_recommendations()

                # Display current status
                self.display_decision_status()

                # Wait before next check
                await asyncio.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            print("\n🛑 Decision engine stopped by user")

    async def check_for_new_opportunities(self):
        """Check for new data and opportunities"""

        try:
            # Get recent submissions from the last hour
            one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()

            response = self.supabase_client.table("submission")\
                .select("*")\
                .gte("created_at", one_hour_ago)\
                .order("created_at", desc=True)\
                .limit(20)\
                .execute()

            if response.data:
                print(f"📊 Found {len(response.data)} new submissions")

                # Analyze new data for opportunities
                for post in response.data:
                    if post.get('score', 0) > 50:  # Only analyze high-engagement posts
                        opportunity = await self.analyze_single_post(post)
                        if opportunity:
                            self.opportunities_cache.append(opportunity)
                            print(f"💡 New opportunity: {opportunity['concept']}")

        except Exception as e:
            print(f"⚠️ Error checking for new opportunities: {e}")

    async def analyze_single_post(self, post: Dict) -> Optional[Dict]:
        """Analyze a single post for opportunity potential"""

        try:
            title = post.get('title', '')
            subreddit = post.get('subreddit', '')
            score = post.get('score', 0)

            # Quick AI analysis
            prompt = f"""
            Analyze this Reddit post for app business opportunities:

            Post: {title}
            Subreddit: r/{subreddit}
            Score: {score}

            Is there a recurring problem here that could be solved with a 1-3 functionality app?
            If yes, provide a brief app concept. If no, respond with "No clear opportunity".

            Keep response under 100 words.
            """

            response = await self.sdk_client.query(prompt)

            if "no clear opportunity" not in response.lower():
                return {
                    "domain": self.map_subreddit_to_domain(subreddit),
                    "concept": response[:100],
                    "problem": title,
                    "functionality": "To be determined",
                    "viability": "Medium",
                    "source": "real_time_analysis",
                    "identified_at": datetime.now().isoformat(),
                    "confidence_score": 0.6,
                    "original_post": post.get('id')
                }

        except Exception as e:
            print(f"⚠️ Error analyzing post: {e}")

        return None

    def map_subreddit_to_domain(self, subreddit: str) -> str:
        """Map subreddit to domain"""

        mapping = {
            "personalfinance": "personal_finance",
            "poverty": "personal_finance",
            "debtfree": "personal_finance",
            "learnprogramming": "skill_acquisition",
            "language_learning": "skill_acquisition",
            "diabetes": "chronic_disease",
            "ChronicPain": "chronic_disease",
            "solotravel": "budget_travel",
            "backpacking": "budget_travel"
        }

        return mapping.get(subreddit, "other")

    async def update_decision_recommendations(self):
        """Update decision recommendations based on current opportunities"""

        # Sort opportunities by confidence score and viability
        high_viability = [opp for opp in self.opportunities_cache
                         if opp.get('viability') == 'High' or opp.get('confidence_score', 0) > 0.7]

        # Get top 5 opportunities
        top_opportunities = sorted(high_vailability,
                                 key=lambda x: x.get('confidence_score', 0),
                                 reverse=True)[:5]

        self.last_analysis = {
            "total_opportunities": len(self.opportunities_cache),
            "high_viability_count": len(high_viability),
            "top_opportunities": top_opportunities,
            "last_updated": datetime.now().isoformat()
        }

    def display_decision_status(self):
        """Display current decision status"""

        os.system('clear' if os.name == 'posix' else 'cls')

        print("🧠 RedditHarbor Decision Dashboard")
        print("=" * 40)
        print(f"📊 Total Opportunities: {len(self.opportunities_cache)}")
        print(f"🎯 High Viability: {len([o for o in self.opportunities_cache if o.get('viability') == 'High'])}")
        print(f"⏰ Last Update: {datetime.now().strftime('%H:%M:%S')}")
        print()

        if self.last_analysis.get("top_opportunities"):
            print("🚀 TOP OPPORTUNITIES:")
            print("-" * 30)

            for i, opp in enumerate(self.last_analysis["top_opportunities"][:5], 1):
                print(f"{i}. {opp['concept'][:60]}...")
                print(f"   Domain: {opp['domain'].replace('_', ' ').title()}")
                print(f"   Viability: {opp['viability']} | Confidence: {opp.get('confidence_score', 0):.2f}")
                print()

        print("💡 DECISION INSIGHTS:")
        print("-" * 25)

        # Domain breakdown
        domain_counts = Counter(opp['domain'] for opp in self.opportunities_cache)
        for domain, count in domain_counts.most_common():
            print(f"• {domain.replace('_', ' ').title()}: {count} opportunities")

        print()
        print("🔄 Monitoring for new opportunities... (Ctrl+C to stop)")

    async def export_decision_report(self):
        """Export comprehensive decision report"""

        report = {
            "generated_at": datetime.now().isoformat(),
            "total_opportunities": len(self.opportunities_cache),
            "analysis_summary": self.last_analysis,
            "all_opportunities": self.opportunities_cache,
            "recommendations": self.generate_recommendations()
        }

        filename = f"decision_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"📋 Decision report exported: {filename}")

    def generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""

        recommendations = []

        if len(self.opportunities_cache) > 10:
            recommendations.append("🎯 FOCUS: Prioritize high-viability opportunities with confidence scores > 0.7")

        high_viability_count = len([o for o in self.opportunities_cache if o.get('viability') == 'High'])
        if high_viability_count > 0:
            recommendations.append(f"🚀 ACTION: {high_viability_count} high-viability opportunities ready for validation")

        domain_counts = Counter(opp['domain'] for opp in self.opportunities_cache)
        if domain_counts:
            top_domain = domain_counts.most_common(1)[0]
            recommendations.append(f"📊 TREND: {top_domain[0].replace('_', ' ').title()} shows most opportunity density")

        recommendations.append("🔄 MONITORING: Continue real-time analysis for emerging patterns")

        return recommendations


async def main():
    """Main execution"""

    dashboard = RealTimeDecisionDashboard()

    if len(sys.argv) > 1 and sys.argv[1] == "--export":
        # Export existing analysis
        await dashboard.analyze_existing_data()
        await dashboard.export_decision_report()
    else:
        # Start real-time dashboard
        await dashboard.start_decision_engine()


if __name__ == "__main__":
    asyncio.run(main())