#!/usr/bin/env .venv/bin/python
"""
RedditHarbor Instant Opportunity Analyzer
Analyzes your collected Reddit data to identify business opportunities immediately
"""

import os
import sys
import json
import re
from datetime import datetime
from collections import Counter, defaultdict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import RedditHarbor components
from redditharbor.login import supabase
import config.settings as settings


class InstantOpportunityAnalyzer:
    """Analyzes collected Reddit data for business opportunities"""

    def __init__(self):
        self.supabase_client = supabase(
            url=settings.SUPABASE_URL,
            private_key=settings.SUPABASE_KEY
        )
        self.opportunities = []
        self.problem_patterns = {}

    def run_instant_analysis(self):
        """Run immediate analysis of collected data"""

        print("🚀 RedditHarbor Instant Opportunity Analysis")
        print("=" * 50)
        print("Analyzing your collected Reddit data for business opportunities...")
        print()

        try:
            # Fetch all collected data
            print("📊 Fetching your research data...")
            all_data = self.fetch_all_data()

            if not all_data:
                print("❌ No data found. Make sure your research has collected data.")
                return

            print(f"✅ Found {len(all_data)} submissions to analyze")
            print()

            # Analyze by domain
            domain_analysis = self.analyze_by_domain(all_data)

            # Extract business opportunities
            opportunities = self.extract_opportunities(all_data)

            # Generate recommendations
            recommendations = self.generate_recommendations(opportunities)

            # Display results
            self.display_results(domain_analysis, opportunities, recommendations)

            # Save analysis
            self.save_analysis(domain_analysis, opportunities, recommendations)

        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()

    def fetch_all_data(self):
        """Fetch all research data from Supabase"""

        try:
            # Get all submissions
            response = self.supabase_client.table("submission")\
                .select("*")\
                .order("created_at", desc=True)\
                .limit(2000)\
                .execute()

            return response.data if response.data else []

        except Exception as e:
            print(f"⚠️ Error fetching data: {e}")
            return []

    def analyze_by_domain(self, data):
        """Analyze data by domain"""

        print("🔍 Analyzing by domain...")

        domain_mapping = {
            "personal_finance": ["personalfinance", "poverty", "debtfree", "FinancialPlanning", "StudentLoans"],
            "skill_acquisition": ["learnprogramming", "language_learning", "learnmath", "learnart"],
            "chronic_disease": ["diabetes", "ChronicPain", "ibs", "epilepsy", "fibromyalgia"],
            "budget_travel": ["solotravel", "backpacking", "travel", "Flights"]
        }

        domain_analysis = {}

        for domain, subreddits in domain_mapping.items():
            domain_data = [post for post in data if post.get('subreddit') in subreddits]

            if domain_data:
                analysis = {
                    "total_posts": len(domain_data),
                    "high_engagement": sum(1 for post in domain_data if isinstance(post.get('score', 0), (int, float)) and post.get('score', 0) > 100),
                    "avg_score": sum(post.get('score', 0) for post in domain_data if isinstance(post.get('score', 0), (int, float))) / len(domain_data),
                    "top_problems": self.extract_top_problems(domain_data)
                }
                domain_analysis[domain] = analysis
                print(f"   📊 {domain.replace('_', ' ').title()}: {len(domain_data)} posts")

        return domain_analysis

    def extract_top_problems(self, domain_data):
        """Extract top problems from domain data"""

        problem_keywords = {
            "help": ["help", "advice", "recommendation", "suggestion", "guidance"],
            "confusion": ["confused", "lost", "unclear", "don't understand", "unsure"],
            "struggle": ["struggle", "struggling", "difficulty", "hard", "challenge"],
            "money": ["budget", "save", "debt", "invest", "money", "financial"],
            "learning": ["learn", "study", "practice", "progress", "skill"],
            "health": ["pain", "symptom", "treatment", "health", "medication"],
            "travel": ["travel", "trip", "flight", "hotel", "cost"]
        }

        problems = []

        for post in domain_data:
            title = post.get('title', '').lower()
            score = post.get('score', 0)

            # Classify problem type
            problem_type = "General"
            for category, keywords in problem_keywords.items():
                if any(keyword in title for keyword in keywords):
                    problem_type = category.title()
                    break

            # Only include posts with clear problems
            problem_indicators = ["?", "help", "how", "what", "confused", "struggle", "issue", "problem"]
            if any(indicator in title for indicator in problem_indicators) and isinstance(score, (int, float)) and score > 10:
                problems.append({
                    "title": post.get('title', ''),
                    "score": score,
                    "type": problem_type,
                    "subreddit": post.get('subreddit', '')
                })

        # Sort by engagement
        problems.sort(key=lambda x: x['score'], reverse=True)
        return problems[:5]

    def extract_opportunities(self, data):
        """Extract business opportunities from data"""

        print("💡 Identifying business opportunities...")

        opportunities = []

        # Group similar problems
        problem_clusters = self.cluster_problems(data)

        for cluster_name, posts in problem_clusters.items():
            if len(posts) >= 3:  # Only significant clusters
                opportunity = self.create_opportunity(cluster_name, posts)
                if opportunity:  # Only add valid opportunities
                    opportunities.append(opportunity)

        # Sort by potential
        opportunities.sort(key=lambda x: x['potential_score'], reverse=True)
        return opportunities

    def cluster_problems(self, data):
        """Cluster posts by similar problems"""

        clusters = defaultdict(list)

        # Define problem patterns
        patterns = {
            "Budget Management": ["budget", "save money", "spending", "expenses", "financial plan"],
            "Debt Problems": ["debt", "loan", "credit card", "pay off", "debt free"],
            "Learning Progress": ["learn", "study", "progress", "understand", "confused"],
            "Career Development": ["career", "job", "skill", "development", "find job"],
            "Health Tracking": ["health", "symptom", "track", "manage", "treatment"],
            "Travel Planning": ["travel", "trip", "plan", "booking", "itinerary"],
            "Income Growth": ["income", "salary", "earn more", "raise", "side hustle"],
            "Investment Help": ["invest", "investment", "portfolio", "stocks", "crypto"]
        }

        for post in data:
            title = post.get('title', '').lower()

            for pattern_name, keywords in patterns.items():
                if any(keyword in title for keyword in keywords):
                    clusters[pattern_name].append(post)
                    break

        return dict(clusters)

    def create_opportunity(self, cluster_name, posts):
        """Create opportunity from problem cluster"""

        # Calculate metrics
        valid_scores = [post.get('score', 0) for post in posts if isinstance(post.get('score', 0), (int, float))]
        total_score = sum(valid_scores)
        avg_score = total_score / len(valid_scores) if valid_scores else 0
        potential_score = (len(posts) * 10) + (avg_score * 2)

        # Generate app concept
        app_concepts = {
            "Budget Management": {
                "concept": "Smart Budget Assistant",
                "features": ["Automated expense tracking", "Budget optimization", "Spending insights"],
                "viability": "High"
            },
            "Debt Problems": {
                "concept": "Debt Payoff Planner",
                "features": ["Debt snowball calculator", "Payment tracking", "Progress visualization"],
                "viability": "High"
            },
            "Learning Progress": {
                "concept": "Skill Progress Tracker",
                "features": ["Learning milestones", "Progress tracking", "Motivation tools"],
                "viability": "High"
            },
            "Health Tracking": {
                "concept": "Health Symptom Tracker",
                "features": ["Symptom logging", "Trend analysis", "Doctor sharing"],
                "viability": "Medium"
            },
            "Travel Planning": {
                "concept": "Budget Travel Planner",
                "features": ["Trip budgeting", "Cost tracking", "Destination insights"],
                "viability": "Medium"
            },
            "Income Growth": {
                "concept": "Income Growth Coach",
                "features": ["Salary negotiation", "Side hustle ideas", "Skill monetization"],
                "viability": "High"
            },
            "Investment Help": {
                "concept": "Simple Investment Tracker",
                "features": ["Portfolio monitoring", "Basic analytics", "Goal tracking"],
                "viability": "Medium"
            }
        }

        concept = app_concepts.get(cluster_name, {
            "concept": f"{cluster_name} Solution",
            "features": ["Core feature 1", "Core feature 2", "Core feature 3"],
            "viability": "Medium"
        })

        return {
            "problem_cluster": cluster_name,
            "app_concept": concept["concept"],
            "features": concept["features"],
            "viability": concept["viability"],
            "metrics": {
                "posts_mentioned": len(posts),
                "total_engagement": total_score,
                "avg_engagement": round(avg_score, 2),
                "potential_score": round(potential_score, 2)
            },
            "potential_score": round(potential_score, 2),  # Add top-level score for sorting
            "sample_posts": [post.get('title', '') for post in posts[:3]]
        }

    def generate_recommendations(self, opportunities):
        """Generate strategic recommendations"""

        print("📈 Generating strategic recommendations...")

        recommendations = []

        # Top opportunity recommendation
        if opportunities:
            top_opp = opportunities[0]
            recommendations.append({
                "priority": "High",
                "action": "Immediate MVP Development",
                "concept": top_opp['app_concept'],
                "reason": f"Highest potential score ({top_opp['metrics']['potential_score']}) and strong user engagement",
                "timeline": "2-3 months",
                "next_steps": [
                    "Validate concept with target users",
                    "Create low-fidelity prototype",
                    "Test core functionality"
                ]
            })

        # Domain-specific recommendations
        high_viability = [opp for opp in opportunities if opp['viability'] == 'High']

        if len(high_viability) >= 2:
            recommendations.append({
                "priority": "Medium",
                "action": "Parallel Opportunity Pipeline",
                "concepts": [opp['app_concept'] for opp in high_viability[:3]],
                "reason": "Multiple high-viability opportunities identified",
                "timeline": "6-12 months",
                "next_steps": [
                    "Develop validation plan for each concept",
                    "Create user personas",
                    "Estimate market size"
                ]
            })

        # Continuous monitoring recommendation
        recommendations.append({
            "priority": "Medium",
            "action": "Automate Opportunity Detection",
            "concept": "Real-time Analysis System",
            "reason": "Continuous stream of new problems being identified",
            "timeline": "4-6 weeks",
            "next_steps": [
                "Set up automated analysis pipeline",
                "Create opportunity alert system",
                "Implement decision scoring"
            ]
        })

        return recommendations

    def display_results(self, domain_analysis, opportunities, recommendations):
        """Display analysis results"""

        print("\n" + "="*60)
        print("🎯 ANALYSIS RESULTS")
        print("="*60)

        # Domain overview
        print("\n📊 DOMAIN ANALYSIS:")
        for domain, analysis in domain_analysis.items():
            print(f"\n📍 {domain.replace('_', ' ').title()}:")
            print(f"   Posts: {analysis['total_posts']}")
            print(f"   High engagement: {analysis['high_engagement']}")
            print(f"   Avg score: {analysis['avg_score']:.1f}")
            print(f"   Top problem: {analysis['top_problems'][0]['title'][:60]}..." if analysis['top_problems'] else "   No clear problems identified")

        # Top opportunities
        print(f"\n💡 TOP {len(opportunities)} BUSINESS OPPORTUNITIES:")
        for i, opp in enumerate(opportunities[:5], 1):
            print(f"\n{i}. {opp['app_concept']} ({opp['viability']} Viability)")
            print(f"   Problem: {opp['problem_cluster']}")
            print(f"   Potential Score: {opp['metrics']['potential_score']}")
            print(f"   Features: {', '.join(opp['features'])}")
            print(f"   Sample: {opp['sample_posts'][0][:50]}...")

        # Recommendations
        print(f"\n🚀 STRATEGIC RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['action']} ({rec['priority']} Priority)")
            print(f"   Concept: {rec.get('concept', 'Multiple concepts')}")
            print(f"   Timeline: {rec['timeline']}")
            print(f"   Reason: {rec['reason']}")
            print(f"   Next steps: {', '.join(rec['next_steps'][:2])}...")

        print("\n" + "="*60)

    def save_analysis(self, domain_analysis, opportunities, recommendations):
        """Save analysis results"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        analysis_data = {
            "generated_at": datetime.now().isoformat(),
            "domain_analysis": domain_analysis,
            "opportunities": opportunities,
            "recommendations": recommendations
        }

        # Save JSON
        json_filename = f"opportunity_analysis_{timestamp}.json"
        with open(json_filename, 'w') as f:
            json.dump(analysis_data, f, indent=2)

        # Save markdown
        md_filename = f"opportunity_analysis_{timestamp}.md"
        with open(md_filename, 'w') as f:
            f.write("# RedditHarbor Opportunity Analysis\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## Top Business Opportunities\n\n")
            for i, opp in enumerate(opportunities[:5], 1):
                f.write(f"### {i}. {opp['app_concept']} ({opp['viability']} Viability)\n")
                f.write(f"**Problem**: {opp['problem_cluster']}\n")
                f.write(f"**Potential Score**: {opp['metrics']['potential_score']}\n")
                f.write(f"**Features**: {', '.join(opp['features'])}\n\n")

            f.write("## Recommendations\n\n")
            for i, rec in enumerate(recommendations, 1):
                f.write(f"### {i}. {rec['action']}\n")
                f.write(f"**Priority**: {rec['priority']}\n")
                f.write(f"**Timeline**: {rec['timeline']}\n")
                f.write(f"**Reason**: {rec['reason']}\n\n")

        print(f"\n📋 Analysis saved:")
        print(f"   📄 JSON: {json_filename}")
        print(f"   📝 Markdown: {md_filename}")


def main():
    """Main execution"""

    analyzer = InstantOpportunityAnalyzer()
    analyzer.run_instant_analysis()


if __name__ == "__main__":
    main()