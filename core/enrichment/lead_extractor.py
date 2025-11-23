#!/usr/bin/env python3
"""
Lead Extraction Engine for Option B (Customer Lead Generation)

Extracts actionable sales leads from Reddit posts using simple regex + keyword matching.

KEY INSIGHT: We're ALREADY collecting this data in the pipeline!
We just need to extract lead-specific fields:
- Reddit username (the actual lead!)
- Budget signals ("$300/month", "budget approved")
- Competitor mentions ("Asana", "Salesforce", "MyFitnessPal")
- Team size ("12 users", "team of 10")
- Buying intent (awareness → evaluation → ready_to_buy)
- Urgency (low → medium → high → critical)

This is SIMPLE extraction - no complex AI needed!
Just parse the fields we're already collecting but not using.
"""

import re
from dataclasses import asdict, dataclass
from datetime import datetime

# =============================================================================
# COMPETITOR DATABASES (expand based on your customers)
# =============================================================================

COMPETITORS = {
    # Project Management
    "projectmanagement": ["Asana", "Monday.com", "ClickUp", "Trello", "Jira", "Basecamp", "Notion"],

    # CRM
    "sales": ["Salesforce", "HubSpot", "Pipedrive", "Zoho", "Copper"],
    "smallbusiness": ["Salesforce", "HubSpot", "Zoho"],

    # Fitness / Health
    "fitness": ["MyFitnessPal", "LoseIt", "Cronometer", "Fitbit"],
    "loseit": ["MyFitnessPal", "LoseIt", "Noom"],

    # Finance / Budgeting
    "personalfinance": ["Mint", "YNAB", "EveryDollar", "PocketGuard"],
    "budget": ["Mint", "YNAB", "EveryDollar"],

    # General SaaS
    "saas": ["Slack", "Zoom", "Microsoft Teams", "Google Workspace"],
    "startups": ["Slack", "Notion", "Linear", "Figma"],
}


def get_competitors_for_subreddit(subreddit: str) -> list[str]:
    """Get relevant competitors for a subreddit"""
    subreddit_lower = subreddit.lower()
    return COMPETITORS.get(subreddit_lower, [])


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class LeadSignals:
    """Extracted lead signals from Reddit post"""

    # Lead identification
    reddit_username: str
    reddit_post_id: str
    reddit_post_url: str

    # Problem context
    problem_description: str
    full_text: str
    current_solution: str | None = None
    competitor_mentioned: str | None = None

    # Budget signals
    budget_mentioned: str | None = None
    budget_amount: float | None = None
    budget_period: str | None = None  # month, year
    budget_status: str = "unknown"  # mentioned, approved, constrained, unknown

    # Company/team indicators
    team_size: int | None = None
    company_indicators: list[str] = None
    decision_maker_likely: bool = False

    # Buying intent
    buying_intent_stage: str = "awareness"  # awareness, evaluation, ready_to_buy
    urgency_level: str = "low"  # low, medium, high, critical
    timeline_mentioned: str | None = None

    # Pain points & requirements
    pain_points: list[str] = None
    feature_requirements: list[str] = None

    # Context
    subreddit: str = ""
    posted_at: datetime | None = None

    # Scoring
    lead_score: float = 0.0
    lead_status: str = "new"  # new, contacted, qualified, won, lost

    def __post_init__(self):
        """Initialize empty lists"""
        if self.company_indicators is None:
            self.company_indicators = []
        if self.pain_points is None:
            self.pain_points = []
        if self.feature_requirements is None:
            self.feature_requirements = []


# =============================================================================
# EXTRACTION PATTERNS
# =============================================================================

# Budget patterns
BUDGET_PATTERNS = [
    r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:per|/|a)?\s*(month|mo|year|yr|annually)',
    r'budget.*?\$(\d+(?:,\d{3})*)',
    r'paying\s+\$(\d+(?:,\d{3})*)',
    r'under\s+\$(\d+(?:,\d{3})*)',
    r'around\s+\$(\d+(?:,\d{3})*)',
    r'about\s+\$(\d+(?:,\d{3})*)',
]

# Team size patterns
TEAM_SIZE_PATTERNS = [
    r'team of (\d+)',
    r'(\d+)\s+users?',
    r'(\d+)\s+people',
    r'(\d+)\s+employees?',
    r'(\d+)\s+members?',
]

# Timeline patterns
TIMELINE_PATTERNS = [
    r'by\s+(Q\d)',
    r'end of\s+(Q\d|quarter)',
    r'by\s+(next month|this month|this week)',
    r'within\s+(\d+\s+(?:days?|weeks?|months?))',
    r'deadline.*?(\w+)',
]

# Company/team indicators
COMPANY_INDICATORS = [
    "our company", "our team", "our organization", "our business",
    "we're", "we are", "we need", "we use", "we're using",
    "my team", "my company", "my organization",
]

# Decision maker indicators
DECISION_MAKER_PHRASES = [
    "i'm the", "i am the", "cto", "ceo", "founder", "director",
    "vp of", "head of", "lead", "manager", "decision maker",
]

# Urgency indicators
URGENCY_INDICATORS = {
    "critical": ["urgent", "asap", "immediately", "emergency", "critical", "now"],
    "high": ["soon", "this week", "this month", "deadline", "by end of"],
    "medium": ["looking for", "need", "searching", "considering", "evaluating"],
    "low": ["curious", "wondering", "thinking about", "might need"],
}

# Buying stage indicators
BUYING_STAGE_INDICATORS = {
    "ready_to_buy": [
        "switching from", "migrating from", "leaving", "budget approved",
        "ready to purchase", "need asap", "need recommendations", "which should I choose"
    ],
    "evaluation": [
        "looking for", "alternatives to", "comparing", "vs", "versus",
        "reviews of", "opinions on", "thoughts on", "which is better"
    ],
    "awareness": [
        "what is", "how do", "does anyone use", "curious about",
        "heard of", "recommendations for"
    ],
}

# Pain point keywords
PAIN_POINT_KEYWORDS = {
    "pricing": ["expensive", "costly", "overpriced", "too expensive", "pricing", "cost too much"],
    "performance": ["slow", "laggy", "performance", "speed", "crashes", "buggy"],
    "features": ["missing features", "lacks", "doesn't have", "no support for", "limited"],
    "complexity": ["complicated", "complex", "hard to use", "confusing", "steep learning curve"],
    "support": ["poor support", "no support", "customer service", "unresponsive"],
}


# =============================================================================
# LEAD EXTRACTOR
# =============================================================================

class LeadExtractor:
    """
    Extracts sales leads from Reddit posts

    This is SIMPLE extraction using regex + keywords.
    No complex AI needed - just parse what's already there!
    """

    def extract_from_reddit_post(
        self,
        post: dict,
        opportunity_score: float = 0.0
    ) -> LeadSignals:
        """
        Extract lead signals from a Reddit post

        Args:
            post: Reddit post dict with keys: id, author, title, selftext, subreddit, created_utc
            opportunity_score: Optional score from opportunity_analyzer_agent

        Returns:
            LeadSignals with extracted data
        """
        # Extract basic fields
        post_id = post.get("id", "")
        username = post.get("author", "unknown")
        title = post.get("title", "")
        text = post.get("selftext", "") or post.get("text", "")
        subreddit = post.get("subreddit", "")
        created_utc = post.get("created_utc")

        # Combine title + text for analysis
        full_text = f"{title}\n\n{text}"

        # Extract all signals
        budget_info = self._extract_budget(full_text)
        team_size = self._extract_team_size(full_text)
        competitor = self._extract_competitor(full_text, subreddit)
        timeline = self._extract_timeline(full_text)
        company_indicators = self._extract_company_indicators(full_text)
        decision_maker_likely = self._is_decision_maker(full_text)
        buying_stage = self._determine_buying_stage(full_text)
        urgency = self._determine_urgency(full_text)
        pain_points = self._extract_pain_points(full_text)
        requirements = self._extract_requirements(full_text)

        # Build Reddit post URL
        post_url = f"https://reddit.com/r/{subreddit}/comments/{post_id}"

        # Convert timestamp
        posted_at = None
        if created_utc:
            try:
                posted_at = datetime.fromtimestamp(created_utc)
            except:
                pass

        # Build lead signals
        return LeadSignals(
            reddit_username=username,
            reddit_post_id=post_id,
            reddit_post_url=post_url,
            problem_description=title,
            full_text=full_text,
            current_solution=competitor,
            competitor_mentioned=competitor,
            budget_mentioned=budget_info.get("budget_text"),
            budget_amount=budget_info.get("amount"),
            budget_period=budget_info.get("period"),
            budget_status=budget_info.get("status", "unknown"),
            team_size=team_size,
            company_indicators=company_indicators,
            decision_maker_likely=decision_maker_likely,
            buying_intent_stage=buying_stage,
            urgency_level=urgency,
            timeline_mentioned=timeline,
            pain_points=pain_points,
            feature_requirements=requirements,
            subreddit=subreddit,
            posted_at=posted_at,
            lead_score=opportunity_score,
            lead_status="new"
        )

    def _extract_budget(self, text: str) -> dict:
        """Extract budget signals from text"""
        text_lower = text.lower()

        for pattern in BUDGET_PATTERNS:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                # Get amount
                amount_str = match.group(1).replace(",", "")
                try:
                    amount = float(amount_str)
                except:
                    amount = None

                # Get period if in pattern
                period = None
                if len(match.groups()) > 1:
                    period_text = match.group(2)
                    if period_text in ["month", "mo"]:
                        period = "month"
                    elif period_text in ["year", "yr", "annually"]:
                        period = "year"

                # Determine budget status
                status = "mentioned"
                if "budget approved" in text_lower or "budget is approved" in text_lower:
                    status = "approved"
                elif "tight budget" in text_lower or "limited budget" in text_lower:
                    status = "constrained"

                return {
                    "budget_text": match.group(0),
                    "amount": amount,
                    "period": period,
                    "status": status
                }

        return {}

    def _extract_team_size(self, text: str) -> int | None:
        """Extract team size from text"""
        for pattern in TEAM_SIZE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except:
                    continue
        return None

    def _extract_competitor(self, text: str, subreddit: str) -> str | None:
        """Extract competitor mention from text"""
        # Get relevant competitors for this subreddit
        competitors = get_competitors_for_subreddit(subreddit)

        # Also add generic common competitors
        competitors.extend(["Salesforce", "Microsoft", "Google", "Apple", "Amazon"])

        # Check for mentions
        for competitor in competitors:
            if competitor.lower() in text.lower():
                return competitor

        return None

    def _extract_timeline(self, text: str) -> str | None:
        """Extract timeline mentions"""
        for pattern in TIMELINE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_company_indicators(self, text: str) -> list[str]:
        """Extract company/team indicators"""
        text_lower = text.lower()
        indicators = []

        for indicator in COMPANY_INDICATORS:
            if indicator in text_lower:
                indicators.append("team_reference")
                break

        return indicators if indicators else []

    def _is_decision_maker(self, text: str) -> bool:
        """Check if user is likely a decision maker"""
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in DECISION_MAKER_PHRASES)

    def _determine_buying_stage(self, text: str) -> str:
        """Determine buying intent stage"""
        text_lower = text.lower()

        # Check ready to buy first (highest intent)
        for phrase in BUYING_STAGE_INDICATORS["ready_to_buy"]:
            if phrase in text_lower:
                return "ready_to_buy"

        # Check evaluation
        for phrase in BUYING_STAGE_INDICATORS["evaluation"]:
            if phrase in text_lower:
                return "evaluation"

        # Default to awareness
        return "awareness"

    def _determine_urgency(self, text: str) -> str:
        """Determine urgency level"""
        text_lower = text.lower()

        # Check from highest to lowest
        for level in ["critical", "high", "medium", "low"]:
            for indicator in URGENCY_INDICATORS[level]:
                if indicator in text_lower:
                    return level

        return "low"

    def _extract_pain_points(self, text: str) -> list[str]:
        """Extract pain point categories"""
        text_lower = text.lower()
        pain_points = []

        for category, keywords in PAIN_POINT_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                pain_points.append(category)

        return pain_points if pain_points else []

    def _extract_requirements(self, text: str) -> list[str]:
        """Extract feature requirements"""
        requirements = []

        # Look for requirement patterns
        req_patterns = [
            r'need[s]?\s+([^.!?\n]+)',
            r'looking for\s+([^.!?\n]+)',
            r'must have\s+([^.!?\n]+)',
            r'require[s]?\s+([^.!?\n]+)',
        ]

        for pattern in req_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            requirements.extend(matches)

        return requirements[:5]  # Limit to top 5


# =============================================================================
# CONVERSION UTILITIES
# =============================================================================

def convert_to_database_record(lead: LeadSignals) -> dict:
    """Convert LeadSignals to database-ready dict"""
    record = asdict(lead)

    # Convert datetime to string for JSON serialization
    if record.get("posted_at"):
        record["posted_at"] = record["posted_at"].isoformat()

    return record


def format_lead_for_slack(lead: LeadSignals) -> str:
    """Format lead as Slack message"""

    urgency_emoji = {
        "critical": "🚨",
        "high": "🔥",
        "medium": "⚡",
        "low": "📋"
    }

    stage_emoji = {
        "ready_to_buy": "💰",
        "evaluation": "🔍",
        "awareness": "👀"
    }

    emoji = urgency_emoji.get(lead.urgency_level, "📋")
    stage = stage_emoji.get(lead.buying_intent_stage, "")

    msg = f"{emoji} {lead.urgency_level.upper()} URGENCY LEAD"
    if lead.posted_at:
        msg += f" - Posted {lead.posted_at.strftime('%Y-%m-%d %H:%M')}\n"
    else:
        msg += "\n"

    msg += f"\n**Reddit:** u/{lead.reddit_username}"
    msg += f"\n**Subreddit:** r/{lead.subreddit}"
    msg += f"\n**Problem:** {lead.problem_description[:100]}..."

    if lead.current_solution:
        msg += f"\n**Currently Using:** {lead.current_solution}"

    if lead.budget_mentioned:
        status_icon = "✅" if lead.budget_status == "approved" else "💵"
        msg += f"\n**Budget:** {status_icon} {lead.budget_mentioned}"
        if lead.budget_status == "approved":
            msg += " (approved)"

    if lead.team_size:
        msg += f"\n**Team Size:** {lead.team_size} users"

    if lead.timeline_mentioned:
        msg += f"\n**Timeline:** {lead.timeline_mentioned}"

    msg += f"\n**Stage:** {stage} {lead.buying_intent_stage.replace('_', ' ').title()}"

    if lead.pain_points:
        msg += f"\n**Pain Points:** {', '.join(lead.pain_points)}"

    if lead.feature_requirements:
        msg += f"\n**Needs:** {lead.feature_requirements[0][:100]}"

    msg += f"\n\n**Lead Score:** {lead.lead_score:.0f}/100"
    msg += f"\n**View Post:** {lead.reddit_post_url}"

    return msg


# =============================================================================
# TESTING & DEMO
# =============================================================================

def demo_extraction():
    """Demo lead extraction with realistic examples"""

    print("\n" + "="*80)
    print("LEAD EXTRACTION DEMO")
    print("="*80 + "\n")

    # Example posts (realistic Reddit data)
    examples = [
        {
            "id": "abc123",
            "author": "startup_cto_42",
            "title": "Switching from Asana - need recommendations",
            "selftext": """We're a team of 12 and currently paying $360/month for Asana.
It's gotten too expensive after the latest pricing change.

Looking for alternatives that:
- Cost under $200/month
- Integrate with Slack
- Have good mobile apps

Our budget is approved, need to decide by end of Q1. Any recommendations?""",
            "subreddit": "projectmanagement",
            "created_utc": 1705334567
        },
        {
            "id": "def456",
            "author": "fitness_enthusiast",
            "title": "MyFitnessPal alternatives?",
            "selftext": """I'm so frustrated with MyFitnessPal. The free version is too limited and $10/month for premium is expensive.

Looking for something that tracks macros properly and syncs with Apple Watch. Budget is around $5-8/month max.""",
            "subreddit": "fitness",
            "created_utc": 1705334567
        },
        {
            "id": "ghi789",
            "author": "small_biz_owner",
            "title": "What CRM do you use?",
            "selftext": "Small business owner here. Curious what CRM tools people use for managing customer relationships. Salesforce seems overkill for us.",
            "subreddit": "smallbusiness",
            "created_utc": 1705334567
        }
    ]

    extractor = LeadExtractor()

    for i, post in enumerate(examples, 1):
        print(f"\n{'='*80}")
        print(f"EXAMPLE {i}: {post['title']}")
        print(f"{'='*80}\n")

        lead = extractor.extract_from_reddit_post(post, opportunity_score=85.0)

        # Show Slack format
        slack_msg = format_lead_for_slack(lead)
        print(slack_msg)

        # Show database record
        print(f"\n{'-'*80}")
        print("DATABASE RECORD:")
        print(f"{'-'*80}")
        db_record = convert_to_database_record(lead)
        for key, value in db_record.items():
            if value and value != [] and value != "unknown":
                print(f"{key}: {value}")

    print(f"\n{'='*80}")
    print("EXTRACTION COMPLETE")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    demo_extraction()
