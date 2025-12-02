"""Tests for sector mapping utilities."""
import pytest
from core.utils.sector_mapping import (
    map_subreddit_to_sector,
    get_all_sectors,
    get_subreddits_by_sector,
    get_sector_stats,
    SUBREDDIT_SECTOR_MAP,
)


def test_map_known_subreddit_saas():
    """Test mapping of Technology & SaaS subreddits."""
    assert map_subreddit_to_sector("saas") == "Technology & SaaS"
    assert map_subreddit_to_sector("indiehackers") == "Technology & SaaS"
    assert map_subreddit_to_sector("microsaas") == "Technology & SaaS"


def test_map_known_subreddit_fitness():
    """Test mapping of Health & Fitness subreddits."""
    assert map_subreddit_to_sector("fitness") == "Health & Fitness"
    assert map_subreddit_to_sector("loseit") == "Health & Fitness"
    assert map_subreddit_to_sector("yoga") == "Health & Fitness"


def test_map_known_subreddit_finance():
    """Test mapping of Finance & Investing subreddits."""
    assert map_subreddit_to_sector("personalfinance") == "Finance & Investing"
    assert map_subreddit_to_sector("investing") == "Finance & Investing"
    assert map_subreddit_to_sector("fire") == "Finance & Investing"


def test_map_known_subreddit_education():
    """Test mapping of Education & Career subreddits."""
    assert map_subreddit_to_sector("learnprogramming") == "Education & Career"
    assert map_subreddit_to_sector("startups") == "Education & Career"


def test_map_known_subreddit_travel():
    """Test mapping of Travel & Experiences subreddits."""
    assert map_subreddit_to_sector("travel") == "Travel & Experiences"
    assert map_subreddit_to_sector("digitalnomad") == "Travel & Experiences"


def test_map_known_subreddit_realestate():
    """Test mapping of Real Estate subreddits."""
    assert map_subreddit_to_sector("realestate") == "Real Estate"
    assert map_subreddit_to_sector("landlord") == "Real Estate"


def test_map_unknown_subreddit():
    """Test mapping of unknown subreddit returns Technology & SaaS."""
    assert map_subreddit_to_sector("unknown_sub_12345") == "Technology & SaaS"
    assert map_subreddit_to_sector("random") == "Technology & SaaS"
    assert map_subreddit_to_sector("doesnotexist") == "Technology & SaaS"


def test_map_empty_subreddit():
    """Test mapping empty string returns Technology & SaaS."""
    assert map_subreddit_to_sector("") == "Technology & SaaS"


def test_map_none_subreddit():
    """Test mapping None returns Technology & SaaS."""
    assert map_subreddit_to_sector(None) == "Technology & SaaS"


def test_case_insensitive():
    """Test that mapping is case-insensitive."""
    assert map_subreddit_to_sector("Fitness") == "Health & Fitness"
    assert map_subreddit_to_sector("FITNESS") == "Health & Fitness"
    assert map_subreddit_to_sector("FiTnEsS") == "Health & Fitness"
    assert map_subreddit_to_sector("SaaS") == "Technology & SaaS"
    assert map_subreddit_to_sector("SAAS") == "Technology & SaaS"


def test_get_all_sectors():
    """Test getting all unique sectors."""
    sectors = get_all_sectors()

    # Check expected sectors are present
    assert "Technology & SaaS" in sectors
    assert "Health & Fitness" in sectors
    assert "Finance & Investing" in sectors
    assert "Education & Career" in sectors
    assert "Travel & Experiences" in sectors
    assert "Real Estate" in sectors

    # Check it's sorted
    assert sectors == sorted(sectors)

    # Check count matches unique values
    assert len(sectors) == len(set(SUBREDDIT_SECTOR_MAP.values()))


def test_get_subreddits_by_sector_tech():
    """Test getting subreddits for Technology & SaaS sector."""
    tech_subs = get_subreddits_by_sector("Technology & SaaS")

    assert "saas" in tech_subs
    assert "indiehackers" in tech_subs
    assert "microsaas" in tech_subs
    assert "webdev" in tech_subs

    # Should not contain subreddits from other sectors
    assert "fitness" not in tech_subs
    assert "personalfinance" not in tech_subs


def test_get_subreddits_by_sector_fitness():
    """Test getting subreddits for Health & Fitness sector."""
    fitness_subs = get_subreddits_by_sector("Health & Fitness")

    assert "fitness" in fitness_subs
    assert "loseit" in fitness_subs
    assert "yoga" in fitness_subs
    assert "running" in fitness_subs

    # Should not contain subreddits from other sectors
    assert "saas" not in fitness_subs


def test_get_subreddits_by_sector_nonexistent():
    """Test getting subreddits for non-existent sector returns empty list."""
    result = get_subreddits_by_sector("NonExistent Sector")
    assert result == []


def test_get_sector_stats():
    """Test getting sector statistics."""
    stats = get_sector_stats()

    # Check all sectors are represented
    assert "Technology & SaaS" in stats
    assert "Health & Fitness" in stats
    assert "Finance & Investing" in stats

    # Check counts are positive integers
    for sector, count in stats.items():
        assert isinstance(count, int)
        assert count > 0

    # Check total counts match total subreddits
    assert sum(stats.values()) == len(SUBREDDIT_SECTOR_MAP)

    # Check stats are sorted by count (descending)
    counts = list(stats.values())
    assert counts == sorted(counts, reverse=True)


def test_sector_stats_health_fitness_count():
    """Test that Health & Fitness has expected number of subreddits."""
    stats = get_sector_stats()
    # Based on the mapping, Health & Fitness should have 20 subreddits
    assert stats["Health & Fitness"] == 20


def test_sector_stats_finance_count():
    """Test that Finance & Investing has expected number of subreddits."""
    stats = get_sector_stats()
    # Based on the mapping, Finance & Investing should have 17 subreddits
    assert stats["Finance & Investing"] == 17


@pytest.mark.parametrize("subreddit", SUBREDDIT_SECTOR_MAP.keys())
def test_all_mappings_return_valid_sector(subreddit):
    """Test that all defined mappings return non-empty sectors."""
    sector = map_subreddit_to_sector(subreddit)
    assert sector
    assert isinstance(sector, str)
    assert len(sector) > 0
    # Verify it's one of the known sectors
    assert sector in SUBREDDIT_SECTOR_MAP.values()


@pytest.mark.parametrize(
    "subreddit,expected_sector",
    [
        ("fitness", "Health & Fitness"),
        ("saas", "Technology & SaaS"),
        ("personalfinance", "Finance & Investing"),
        ("travel", "Travel & Experiences"),
        ("realestate", "Real Estate"),
        ("learnprogramming", "Education & Career"),
    ],
)
def test_specific_mappings(subreddit, expected_sector):
    """Test specific subreddit to sector mappings."""
    assert map_subreddit_to_sector(subreddit) == expected_sector


def test_mapping_count():
    """Test total number of subreddit mappings."""
    # Verify we have all expected mappings
    assert len(SUBREDDIT_SECTOR_MAP) == 78  # Total subreddits in mapping


def test_no_duplicate_subreddits():
    """Test that there are no duplicate subreddit entries."""
    subreddits = list(SUBREDDIT_SECTOR_MAP.keys())
    assert len(subreddits) == len(set(subreddits))
