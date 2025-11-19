"""Subreddit to business sector mapping utilities."""
from typing import Dict, Optional


# Comprehensive sector mappings extracted from batch_opportunity_scoring.py
SUBREDDIT_SECTOR_MAP: Dict[str, str] = {
    # Health & Fitness
    "fitness": "Health & Fitness",
    "loseit": "Health & Fitness",
    "bodyweightfitness": "Health & Fitness",
    "nutrition": "Health & Fitness",
    "healthyfood": "Health & Fitness",
    "yoga": "Health & Fitness",
    "running": "Health & Fitness",
    "weightlifting": "Health & Fitness",
    "xxfitness": "Health & Fitness",
    "progresspics": "Health & Fitness",
    "gainit": "Health & Fitness",
    "flexibility": "Health & Fitness",
    "naturalbodybuilding": "Health & Fitness",
    "eatcheapandhealthy": "Health & Fitness",
    "keto": "Health & Fitness",
    "cycling": "Health & Fitness",
    "meditation": "Health & Fitness",
    "mentalhealth": "Health & Fitness",
    "fitness30plus": "Health & Fitness",
    "homegym": "Health & Fitness",
    # Finance & Investing
    "personalfinance": "Finance & Investing",
    "financialindependence": "Finance & Investing",
    "investing": "Finance & Investing",
    "stocks": "Finance & Investing",
    "wallstreetbets": "Finance & Investing",
    "realestateinvesting": "Finance & Investing",
    "povertyfinance": "Finance & Investing",
    "frugal": "Finance & Investing",
    "fire": "Finance & Investing",
    "bogleheads": "Finance & Investing",
    "dividends": "Finance & Investing",
    "options": "Finance & Investing",
    "smallbusiness": "Finance & Investing",
    "cryptocurrency": "Finance & Investing",
    "tax": "Finance & Investing",
    "accounting": "Finance & Investing",
    "financialcareers": "Finance & Investing",
    # Education & Career
    "learnprogramming": "Education & Career",
    "cscareerquestions": "Education & Career",
    "careerguidance": "Education & Career",
    "resumes": "Education & Career",
    "jobs": "Education & Career",
    "studentloans": "Education & Career",
    "college": "Education & Career",
    "gradschool": "Education & Career",
    "teaching": "Education & Career",
    "entrepreneurs": "Education & Career",
    "startups": "Education & Career",
    # Travel & Experiences
    "travel": "Travel & Experiences",
    "solotravel": "Travel & Experiences",
    "digitalnomad": "Travel & Experiences",
    "backpacking": "Travel & Experiences",
    "roadtrip": "Travel & Experiences",
    "travel_hacks": "Travel & Experiences",
    "shoestring": "Travel & Experiences",
    "expats": "Travel & Experiences",
    "travelpartners": "Travel & Experiences",
    "budgettravel": "Travel & Experiences",
    "vagabond": "Travel & Experiences",
    # Real Estate
    "realestate": "Real Estate",
    "firsttimehomebuyer": "Real Estate",
    "homeimprovement": "Real Estate",
    "diy": "Real Estate",
    "homeowners": "Real Estate",
    "renters": "Real Estate",
    "mortgages": "Real Estate",
    "landlord": "Real Estate",
    "realestate_canada": "Real Estate",
    "housingmarkets": "Real Estate",
    # Technology & SaaS
    "saas": "Technology & SaaS",
    "indiehackers": "Technology & SaaS",
    "sidehustle": "Technology & SaaS",
    "juststart": "Technology & SaaS",
    "roastmystartup": "Technology & SaaS",
    "buildinpublic": "Technology & SaaS",
    "microsaas": "Technology & SaaS",
    "nocode": "Technology & SaaS",
    "webdev": "Technology & SaaS",
}


def map_subreddit_to_sector(subreddit: str) -> str:
    """
    Map a subreddit name to its business sector.

    Args:
        subreddit: Name of the subreddit (case-insensitive)

    Returns:
        str: Business sector, or 'Technology & SaaS' if not found

    Examples:
        >>> map_subreddit_to_sector('SaaS')
        'Technology & SaaS'
        >>> map_subreddit_to_sector('fitness')
        'Health & Fitness'
        >>> map_subreddit_to_sector('unknown')
        'Technology & SaaS'
    """
    if not subreddit:
        return "Technology & SaaS"

    subreddit_lower = subreddit.lower()
    return SUBREDDIT_SECTOR_MAP.get(subreddit_lower, "Technology & SaaS")


def get_all_sectors() -> list[str]:
    """
    Get list of all unique sectors.

    Returns:
        list[str]: Sorted list of unique sector names
    """
    return sorted(set(SUBREDDIT_SECTOR_MAP.values()))


def get_subreddits_by_sector(sector: str) -> list[str]:
    """
    Get all subreddits for a given sector.

    Args:
        sector: Name of the sector

    Returns:
        list[str]: List of subreddit names in that sector
    """
    return [
        subreddit
        for subreddit, s in SUBREDDIT_SECTOR_MAP.items()
        if s == sector
    ]


def get_sector_stats() -> Dict[str, int]:
    """
    Get statistics about sector distribution.

    Returns:
        dict: Mapping of sector name to count of subreddits
    """
    stats: Dict[str, int] = {}
    for sector in SUBREDDIT_SECTOR_MAP.values():
        stats[sector] = stats.get(sector, 0) + 1
    return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))
