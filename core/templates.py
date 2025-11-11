#!/usr/bin/env python3
"""
RedditHarbor Project Templates for Different Research Types
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

try:
    from config import ENABLE_PII_ANONYMIZATION
except ImportError:
    from config.settings import ENABLE_PII_ANONYMIZATION

try:
    from redditharbor_setup import setup_redditharbor
except ImportError:
    from core.setup import setup_redditharbor


def academic_research_project(pipeline, topic_subreddits, time_period="recent"):
    """
    Template for academic research projects
    Focus: comprehensive data collection with strict privacy controls
    """
    print(f"🎓 Academic Research: {topic_subreddits}")

    # Academic collection with PII anonymization
    pipeline.subreddit_submission(
        subreddits=topic_subreddits,
        sort_types=["hot", "top", "new"],
        limit=500,
        mask_pii=True,  # Always anonymize for academic research
    )

    pipeline.subreddit_comment(subreddits=topic_subreddits, limit=1000, mask_pii=True)


def market_research_project(pipeline, industry_subreddits):
    """
    Template for market research
    Focus: sentiment analysis and trend monitoring
    """
    print(f"💼 Market Research: {industry_subreddits}")

    pipeline.subreddit_submission(
        subreddits=industry_subreddits,
        sort_types=["hot", "rising"],  # Focus on trending content
        limit=300,
        mask_pii=ENABLE_PII_ANONYMIZATION,
    )


def trend_analysis_project(pipeline, trend_subreddits):
    """
    Template for trend analysis
    Focus: tracking emerging topics and discussions
    """
    print(f"📈 Trend Analysis: {trend_subreddits}")

    pipeline.subreddit_submission(
        subreddits=trend_subreddits,
        sort_types=["hot", "rising", "new"],
        limit=200,
        mask_pii=ENABLE_PII_ANONYMIZATION,
    )


def community_analysis_project(pipeline, community_subreddits):
    """
    Template for community analysis
    Focus: understanding community behavior and engagement
    """
    print(f"👥 Community Analysis: {community_subreddits}")

    pipeline.subreddit_submission(
        subreddits=community_subreddits,
        sort_types=["hot", "top"],
        limit=400,
        mask_pii=ENABLE_PII_ANONYMIZATION,
    )

    # More comments for community analysis
    pipeline.subreddit_comment(
        subreddits=community_subreddits, limit=800, mask_pii=ENABLE_PII_ANONYMIZATION
    )


def keyword_research_project(pipeline, keywords):
    """
    Template for keyword-based research
    Focus: tracking specific topics across Reddit
    """
    print(f"🔍 Keyword Research: {keywords}")

    # This requires the keyword collection method
    # Note: You may need to implement this based on your specific needs
    pass


def monetizable_opportunity_research(pipeline, industry_subreddits):
    """
    Template for identifying monetizable app opportunities
    Focus: comprehensive problem analysis with scoring metrics
    """
    print(f"💰 Monetizable Opportunity Research: {industry_subreddits}")

    # Enhanced data collection for opportunity analysis
    pipeline.subreddit_submission(
        subreddits=industry_subreddits,
        sort_types=["hot", "rising", "top"],
        limit=1000,
        mask_pii=ENABLE_PII_ANONYMIZATION,
    )

    # Deep comment analysis for solution mentions
    pipeline.subreddit_comment(
        subreddits=industry_subreddits,
        limit=2000,
        mask_pii=ENABLE_PII_ANONYMIZATION,
    )


def problem_first_opportunity_research(pipeline, industry_subreddits):
    """
    Template for problem-first data collection
    Focus: Collect only posts describing real user problems, then analyze for opportunities
    """
    print(f"🎯 Problem-First Opportunity Research: {industry_subreddits}")

    # Stage 1: Collect all posts
    print("  Stage 1: Collecting posts...")
    pipeline.subreddit_submission(
        subreddits=industry_subreddits,
        sort_types=["hot", "rising", "top"],
        limit=1000,
        mask_pii=ENABLE_PII_ANONYMIZATION,
    )

    # Stage 2: Tag posts with problem indicators
    print("  Stage 2: Tagging problem indicators...")
    # This would run a post-processing step to identify and tag problem posts
    # The tagging is done in the collection.py extract_problem_keywords() function

    # Stage 3: Deep comment collection
    print("  Stage 3: Collecting comments...")
    pipeline.subreddit_comment(
        subreddits=industry_subreddits,
        limit=2000,
        mask_pii=ENABLE_PII_ANONYMIZATION,
    )

    print("  ✅ Problem-first collection complete!")
    print("  Next: Run AI analysis to identify app opportunities from tagged problems")


def market_segment_research(pipeline, segment_config):
    """
    Template for deep-dive research into specific market segments
    Focus: comprehensive analysis of problems, solutions, and monetization potential
    """
    segment_name = segment_config.get("name", "Unknown Segment")
    subreddits = segment_config.get("subreddits", [])

    print(f"🎯 Market Segment Research: {segment_name}")

    # Collect comprehensive data from segment-specific subreddits
    pipeline.subreddit_submission(
        subreddits=subreddits,
        sort_types=["hot", "top", "rising", "new"],
        limit=1500,
        mask_pii=ENABLE_PII_ANONYMIZATION,
    )

    # Deep comment analysis for problem-solution patterns
    pipeline.subreddit_comment(
        subreddits=subreddits,
        limit=3000,
        mask_pii=ENABLE_PII_ANONYMIZATION,
    )


def validation_research(pipeline, opportunity_keywords, validation_subreddits):
    """
    Template for validating identified opportunities
    Focus: cross-referencing opportunities and confirming market demand
    """
    print(f"✅ Validation Research: {opportunity_keywords}")

    # Search for specific opportunity mentions across validation subreddits
    pipeline.subreddit_submission(
        subreddits=validation_subreddits,
        sort_types=["hot", "new"],
        limit=500,
        mask_pii=ENABLE_PII_ANONYMIZATION,
    )

    # Comment analysis for validation signals
    pipeline.subreddit_comment(
        subreddits=validation_subreddits,
        limit=1000,
        mask_pii=ENABLE_PII_ANONYMIZATION,
    )


# Example usage configurations
PROJECT_CONFIGS = {
    "tech_research": {
        "template": academic_research_project,
        "subreddits": [
            "programming",
            "ComputerScience",
            "coding",
            "softwareengineering",
        ],
        "description": "Academic research on programming discussions",
    },
    "ai_ml_monitoring": {
        "template": trend_analysis_project,
        "subreddits": ["MachineLearning", "artificial", "deeplearning", "OpenAI"],
        "description": "Monitoring AI/ML trends and discussions",
    },
    "startup_analysis": {
        "template": market_research_project,
        "subreddits": ["startups", "Entrepreneur", "SaaS", "SideProject"],
        "description": "Market research for startup ecosystem",
    },
    "gaming_community": {
        "template": community_analysis_project,
        "subreddits": ["gaming", "GamingBuddies", "GameDevs", "IndieGaming"],
        "description": "Community analysis for gaming trends",
    },
    # Monetizable App Opportunity Research Templates
    "health_fitness_opportunities": {
        "template": market_segment_research,
        "config": {
            "name": "Health & Fitness",
            "subreddits": [
                "fitness", "bodyweightfitness", "nutrition", "loseit", "gainit",
                "keto", "running", "cycling", "yoga", "meditation", "mentalhealth",
                "personaltraining", "homegym", "fitness30plus"
            ]
        },
        "description": "Identifying monetizable app opportunities in health & fitness",
    },
    "finance_opportunities": {
        "template": market_segment_research,
        "config": {
            "name": "Finance & Investing",
            "subreddits": [
                "personalfinance", "investing", "stocks", "Bogleheads", "financialindependence",
                "CryptoCurrency", "cryptocurrencymemes", "Bitcoin", "ethfinance",
                "FinancialCareers", "tax", "Accounting", "RealEstateInvesting"
            ]
        },
        "description": "Identifying monetizable app opportunities in finance & investing",
    },
    "education_career_opportunities": {
        "template": market_segment_research,
        "config": {
            "name": "Education & Career",
            "subreddits": [
                "learnprogramming", "cscareerquestions", "IWantToLearn",
                "selfimprovement", "getdisciplined", "productivity", "study",
                "careerguidance", "resumes", "jobs", "interviews"
            ]
        },
        "description": "Identifying monetizable app opportunities in education & career",
    },
    "travel_opportunities": {
        "template": market_segment_research,
        "config": {
            "name": "Travel & Experiences",
            "subreddits": [
                "travel", "solotravel", "backpacking", "digitalnomad",
                "TravelHacks", "flights", "airbnb", "cruise", "roadtrips",
                "AskTourism", "TravelTips", "Shoestring"
            ]
        },
        "description": "Identifying monetizable app opportunities in travel & experiences",
    },
    "real_estate_opportunities": {
        "template": market_segment_research,
        "config": {
            "name": "Real Estate",
            "subreddits": [
                "RealEstate", "realtors", "FirstTimeHomeBuyer", "HomeImprovement",
                "landlord", "Renting", "PropertyManagement", "Homeowners",
                "RealEstateTech", "houseflipper", "zillowgonewild"
            ]
        },
        "description": "Identifying monetizable app opportunities in real estate",
    },
    "productivity_saaS_opportunities": {
        "template": market_segment_research,
        "config": {
            "name": "Technology & SaaS Productivity",
            "subreddits": [
                "SaaS", "startups", "Entrepreneur", "SideProject",
                "antiwork", "workreform", "productivity", "selfhosted",
                "apphookup", "iosapps", "androidapps", "software"
            ]
        },
        "description": "Identifying monetizable app opportunities in technology & SaaS",
    },
    "cross_industry_validation": {
        "template": validation_research,
        "subreddits": ["ProductHunt", "apps", "SaaSHat", "bootstrap"],
        "description": "Validating identified opportunities across broader tech communities",
    },
    "general_opportunity_scan": {
        "template": monetizable_opportunity_research,
        "subreddits": [
            "findareddit", "AskReddit", "LifeProTips", "YouShouldKnow",
            "Damnthatsinteresting", "todayilearned"
        ],
        "description": "Broad scan for monetizable opportunities across popular subreddits",
    },
}


def run_project(project_name, pipeline):
    """
    Run a predefined project template
    """
    if project_name not in PROJECT_CONFIGS:
        print(f"❌ Unknown project: {project_name}")
        print("Available projects:", list(PROJECT_CONFIGS.keys()))
        return

    config = PROJECT_CONFIGS[project_name]
    print(f"\n🚀 Running: {config['description']}")

    try:
        # Handle different template parameter structures
        template = config["template"]
        if "config" in config:
            # For market_segment_research templates
            template(pipeline, config["config"])
        elif "keywords" in config:
            # For validation_research templates (would have keywords)
            template(pipeline, config["keywords"], config["subreddits"])
        else:
            # For standard templates with just subreddits
            template(pipeline, config["subreddits"])

        print(f"✅ Project '{project_name}' completed successfully!")
    except Exception as e:
        print(f"❌ Project '{project_name}' failed: {e}")


if __name__ == "__main__":
    print("📋 RedditHarbor Project Templates")
    print("=" * 40)

    # Setup
    pipeline = setup_redditharbor()

    if pipeline:
        print("\n📁 Available Project Templates:")
        for name, config in PROJECT_CONFIGS.items():
            print(f"  • {name}: {config['description']}")

        # Interactive project selection
        project_name = input("\n🎯 Enter project name to run: ")
        run_project(project_name, pipeline)
