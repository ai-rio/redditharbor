#!/usr/bin/env .venv/bin/python
"""
RedditHarbor Intelligent Research Analysis System
Uses Agent SDK to speed up decision-making based on research results
"""

import asyncio
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime
from typing import Any

import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import Agent SDK
try:
    from claude_agent_sdk import SDKClient, query
except ImportError:
    print("❌ Agent SDK not installed. Install with: pip install claude-agent-sdk")
    sys.exit(1)

# Import RedditHarbor components
from redditharbor.login import supabase

import config.settings as settings


class IntelligentResearchAnalyzer:
    """AI-powered research analysis using Agent SDK for decision-making"""

    def __init__(self):
        self.supabase_client = supabase(
            url=settings.SUPABASE_URL,
            private_key=settings.SUPABASE_KEY
        )
        self.analysis_cache = {}
        self.decision_history = []

    async def analyze_research_data_with_ai(self, domain: str, limit: int = 100) -> dict[str, Any]:
        """Use Agent SDK to intelligently analyze research data"""

        print(f"🧠 AI Analysis: {domain} domain research data")
        print("=" * 50)

        try:
            # Fetch recent research data
            data = await self._fetch_research_data(domain, limit)

            if not data:
                return {"error": f"No data found for {domain} domain"}

            # Prepare data for AI analysis
            research_text = self._prepare_data_for_analysis(data)

            # Use Agent SDK for intelligent analysis
            analysis_prompt = f"""
            Analyze this Reddit research data from {domain} domain to identify:

            1. **Top 5 Recurring Problems**: Most frequently mentioned issues
            2. **Problem Categories**: Group similar problems together
            3. **Pain Point Severity**: Rate problems by urgency/frustration level
            4. **App Opportunities**: Suggest 1-3 functionality apps for each top problem
            5. **Market Viability**: Assess business potential (High/Medium/Low)

            Data:
            {research_text}

            Provide analysis in JSON format:
            {{
                "top_problems": [
                    {{
                        "problem": "Problem description",
                        "frequency": "How often mentioned",
                        "severity": "High/Medium/Low",
                        "app_opportunities": [
                            {{
                                "concept": "App concept",
                                "functionality": "1-3 key features",
                                "viability": "High/Medium/Low"
                            }}
                        ]
                    }}
                ],
                "market_insights": {{
                    "total_addressable_market": "Size estimation",
                    "competition_level": "High/Medium/Low",
                    "growth_potential": "High/Medium/Low"
                }}
            }}
            """

            print("🔄 Processing with AI...")

            # Get AI analysis using Agent SDK
            ai_analysis = await self._get_ai_analysis(analysis_prompt)

            # Enhance with quantitative data
            enhanced_analysis = await self._enhance_with_metrics(data, ai_analysis)

            # Store analysis for decision tracking
            self._store_analysis(domain, enhanced_analysis)

            return enhanced_analysis

        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return {"error": str(e)}

    async def _fetch_research_data(self, domain: str, limit: int) -> list[dict]:
        """Fetch research data from Supabase"""

        try:
            # Map domains to subreddit patterns
            domain_subreddits = {
                "personal_finance": ["personalfinance", "poverty", "debtfree", "FinancialPlanning"],
                "skill_acquisition": ["learnprogramming", "language_learning", "learnmath", "learnart"],
                "chronic_disease": ["diabetes", "ChronicPain", "ibs", "epilepsy"],
                "budget_travel": ["solotravel", "backpacking", "travel", "Flights"]
            }

            subreddits = domain_subreddits.get(domain, [])
            if not subreddits:
                return []

            all_data = []

            for subreddit in subreddits:
                try:
                    # Query submissions from this subreddit
                    response = self.supabase_client.table("submission")\
                        .select("*")\
                        .eq("subreddit", subreddit)\
                        .order("created_at", desc=True)\
                        .limit(limit // len(subreddits))\
                        .execute()

                    if response.data:
                        all_data.extend(response.data)
                        print(f"📊 Retrieved {len(response.data)} submissions from r/{subreddit}")

                except Exception as e:
                    print(f"⚠️ Error fetching from r/{subreddit}: {e}")
                    continue

            print(f"✅ Total data retrieved: {len(all_data)} submissions")
            return all_data

        except Exception as e:
            print(f"❌ Data fetch failed: {e}")
            return []

    def _prepare_data_for_analysis(self, data: list[dict]) -> str:
        """Prepare research data for AI analysis"""

        research_text = "REDDIT POSTS ANALYSIS:\n\n"

        for i, post in enumerate(data[:50]):  # Limit to avoid token limits
            title = post.get('title', '').strip()
            selftext = post.get('selftext', '').strip()
            subreddit = post.get('subreddit', '')
            score = post.get('score', 0)

            research_text += f"Post {i+1} (r/{subreddit}, Score: {score}):\n"
            research_text += f"Title: {title}\n"

            if selftext and len(selftext) > 50:
                # Truncate long posts but keep key points
                truncated = selftext[:500] + "..." if len(selftext) > 500 else selftext
                research_text += f"Content: {truncated}\n"

            research_text += "\n" + "-"*50 + "\n\n"

        return research_text

    async def _get_ai_analysis(self, prompt: str) -> dict:
        """Get AI analysis using Agent SDK"""

        try:
            async for message in query(prompt=prompt):
                if isinstance(message, dict):
                    return message
                elif isinstance(message, str):
                    # Try to extract JSON from string response
                    try:
                        json_match = re.search(r'\{.*\}', message, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group())
                    except:
                        return {"raw_analysis": message}

            return {"error": "No valid response from AI"}

        except Exception as e:
            print(f"⚠️ AI analysis error: {e}")
            return {"error": str(e)}

    async def _enhance_with_metrics(self, data: list[dict], ai_analysis: dict) -> dict:
        """Enhance AI analysis with quantitative metrics"""

        try:
            # Calculate quantitative metrics
            total_posts = len(data)
            total_score = sum(post.get('score', 0) for post in data)
            avg_score = total_score / total_posts if total_posts > 0 else 0

            # Count posts by subreddit
            subreddit_counts = Counter(post.get('subreddit', '') for post in data)

            # Extract common keywords from titles
            all_titles = [post.get('title', '') for post in data]
            common_words = self._extract_common_words(all_titles)

            # Enhanced analysis
            enhanced = {
                "ai_analysis": ai_analysis,
                "quantitative_metrics": {
                    "total_posts_analyzed": total_posts,
                    "average_engagement": round(avg_score, 2),
                    "top_subreddits": dict(subreddit_counts.most_common(5)),
                    "common_keywords": common_words[:10],
                    "analysis_timestamp": datetime.now().isoformat()
                },
                "data_quality": {
                    "posts_with_content": sum(1 for post in data if post.get('selftext', '').strip()),
                    "high_engagement_posts": sum(1 for post in data if post.get('score', 0) > 100),
                    "recent_posts": sum(1 for post in data if self._is_recent_post(post))
                }
            }

            return enhanced

        except Exception as e:
            print(f"⚠️ Metrics enhancement error: {e}")
            return ai_analysis

    def _extract_common_words(self, titles: list[str], min_freq: int = 3) -> list[str]:
        """Extract common words from titles"""

        words = []
        for title in titles:
            # Clean and split words
            cleaned = re.findall(r'\b\w+\b', title.lower())
            words.extend([word for word in cleaned if len(word) > 3])

        # Count frequencies
        word_counts = Counter(words)

        # Filter common words (exclude generic terms)
        generic_words = {'just', 'like', 'know', 'time', 'think', 'really', 'want', 'need', 'good', 'help'}
        filtered = {word: count for word, count in word_counts.items()
                   if word not in generic_words and count >= min_freq}

        return [word for word, count in sorted(filtered.items(), key=lambda x: x[1], reverse=True)]

    def _is_recent_post(self, post: dict) -> bool:
        """Check if post is recent (last 7 days)"""
        try:
            created_at = post.get('created_at')
            if created_at:
                post_date = pd.to_datetime(created_at)
                return (datetime.now() - post_date).days <= 7
        except:
            pass
        return False

    def _store_analysis(self, domain: str, analysis: dict):
        """Store analysis for decision tracking"""

        self.analysis_cache[domain] = {
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

        # Save to file for persistence
        cache_file = f"analysis_cache_{domain}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.analysis_cache[domain], f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save cache: {e}")

    async def generate_decision_report(self, domains: list[str]) -> str:
        """Generate comprehensive decision-making report"""

        print("📋 Generating Decision Report")
        print("=" * 40)

        report = []
        report.append("# RedditHarbor Intelligent Decision Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Domains Analyzed: {', '.join(domains)}")
        report.append("")

        # Executive Summary
        report.append("## 🎯 Executive Summary")

        all_opportunities = []
        for domain in domains:
            if domain in self.analysis_cache:
                analysis = self.analysis_cache[domain]["analysis"]
                if "ai_analysis" in analysis and "top_problems" in analysis["ai_analysis"]:
                    for problem in analysis["ai_analysis"]["top_problems"]:
                        if "app_opportunities" in problem:
                            for opp in problem["app_opportunities"]:
                                all_opportunities.append({
                                    "domain": domain,
                                    "problem": problem.get("problem", ""),
                                    "concept": opp.get("concept", ""),
                                    "viability": opp.get("viability", "")
                                })

        # Top opportunities by viability
        high_viability = [opp for opp in all_opportunities if opp.get("viability") == "High"]

        report.append(f"**Total Opportunities Identified**: {len(all_opportunities)}")
        report.append(f"**High-Viability Opportunities**: {len(high_viability)}")
        report.append("")

        if high_viability:
            report.append("### 🚀 Top High-Viability App Concepts:")
            for i, opp in enumerate(high_viability[:3], 1):
                report.append(f"{i}. **{opp['concept']}** ({opp['domain']})")
                report.append(f"   - Solves: {opp['problem'][:100]}...")
                report.append("")

        # Domain-specific insights
        report.append("## 📊 Domain-Specific Insights")
        report.append("")

        for domain in domains:
            if domain in self.analysis_cache:
                analysis = self.analysis_cache[domain]["analysis"]
                report.append(f"### {domain.replace('_', ' ').title()}")

                if "quantitative_metrics" in analysis:
                    metrics = analysis["quantitative_metrics"]
                    report.append(f"- **Posts Analyzed**: {metrics.get('total_posts_analyzed', 0)}")
                    report.append(f"- **Avg Engagement**: {metrics.get('average_engagement', 0)}")
                    report.append(f"- **Top Keywords**: {', '.join(metrics.get('common_keywords', [])[:5])}")

                if "ai_analysis" in analysis and "top_problems" in analysis["ai_analysis"]:
                    report.append("**Top Problems Identified:**")
                    for problem in analysis["ai_analysis"]["top_problems"][:3]:
                        report.append(f"- {problem.get('problem', '')} ({problem.get('severity', '')} severity)")

                report.append("")

        # Strategic Recommendations
        report.append("## 💡 Strategic Recommendations")
        report.append("")

        if high_viability:
            report.append("### 🎯 Immediate Action Items:")
            report.append("1. **Prioritize High-Viability Concepts**: Focus development on apps marked 'High' viability")
            report.append("2. **Validate Problem-Solution Fit**: Conduct user interviews for top 3 concepts")
            report.append("3. **Build MVPs**: Create minimum viable products for highest-impact solutions")
            report.append("")

        report.append("### 📈 Next Steps:")
        report.append("1. **Deep Dive Research**: Analyze top 20-30 posts for each high-viability opportunity")
        report.append("2. **Competitive Analysis**: Research existing solutions for each concept")
        report.append("3. **User Persona Development**: Create detailed user profiles based on research data")
        report.append("4. **Technical Feasibility Assessment**: Evaluate development complexity")
        report.append("5. **Go-to-Market Strategy**: Plan launch approach for top opportunities")

        return "\n".join(report)

    async def run_continuous_analysis(self, domains: list[str], interval_minutes: int = 30):
        """Run continuous analysis for real-time decision-making"""

        print(f"🔄 Starting Continuous Analysis (every {interval_minutes} minutes)")
        print("=" * 60)

        while True:
            try:
                print(f"\n🕐 Analysis Cycle: {datetime.now().strftime('%H:%M:%S')}")

                for domain in domains:
                    print(f"📊 Analyzing {domain}...")
                    analysis = await self.analyze_research_data_with_ai(domain)

                    if "error" not in analysis:
                        print(f"✅ {domain} analysis complete")
                    else:
                        print(f"❌ {domain} analysis failed: {analysis['error']}")

                # Generate updated report
                report = await self.generate_decision_report(domains)

                # Save report
                report_file = f"decision_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                with open(report_file, 'w') as f:
                    f.write(report)

                print(f"📋 Report saved: {report_file}")

                # Wait for next cycle
                print(f"⏳ Waiting {interval_minutes} minutes...")
                await asyncio.sleep(interval_minutes * 60)

            except KeyboardInterrupt:
                print("\n🛑 Continuous analysis stopped by user")
                break
            except Exception as e:
                print(f"❌ Analysis cycle error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying


async def main():
    """Main execution function"""

    print("🧠 RedditHarbor Intelligent Research Analysis System")
    print("=" * 55)
    print("Using Agent SDK for AI-powered decision-making")
    print()

    analyzer = IntelligentResearchAnalyzer()

    # Define domains to analyze
    domains = ["personal_finance", "skill_acquisition", "chronic_disease", "budget_travel"]

    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--continuous":
            # Run continuous analysis
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            await analyzer.run_continuous_analysis(domains, interval)
        elif sys.argv[1] == "--single":
            # Run single analysis
            for domain in domains:
                analysis = await analyzer.analyze_research_data_with_ai(domain)
                if "error" not in analysis:
                    print(f"✅ {domain} analysis complete")
                else:
                    print(f"❌ {domain} analysis failed")

            # Generate final report
            report = await analyzer.generate_decision_report(domains)

            # Save and display report
            report_file = f"decision_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(report_file, 'w') as f:
                f.write(report)

            print(f"\n📋 Decision Report Generated: {report_file}")
            print("\n" + "="*60)
            print("📊 REPORT SUMMARY:")
            print("="*60)
            print(report[:1000] + "\n..." if len(report) > 1000 else report)
        else:
            print("Usage:")
            print("  python intelligent_research_analyzer.py --single")
            print("  python intelligent_research_analyzer.py --continuous [interval_minutes]")
    else:
        print("Usage:")
        print("  python intelligent_research_analyzer.py --single")
        print("  python intelligent_research_analyzer.py --continuous [interval_minutes]")


if __name__ == "__main__":
    asyncio.run(main())
