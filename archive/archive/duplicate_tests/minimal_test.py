#!/usr/bin/env python3
"""
Minimal collection test
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redditharbor.login import reddit, supabase

from config.settings import (
    DB_CONFIG,
    REDDIT_PUBLIC,
    REDDIT_SECRET,
    REDDIT_USER_AGENT,
    SUPABASE_KEY,
    SUPABASE_URL,
)
from core.collection import collect_monetizable_opportunities_data

# Create clients
reddit_client = reddit(public_key=REDDIT_PUBLIC, secret_key=REDDIT_SECRET, user_agent=REDDIT_USER_AGENT)
supabase_client = supabase(url=SUPABASE_URL, private_key=SUPABASE_KEY)

print("Starting collection from r/personalfinance only...")

success = collect_monetizable_opportunities_data(
    reddit_client=reddit_client,
    supabase_client=supabase_client,
    db_config=DB_CONFIG,
    market_segment="finance_investing",  # Just finance segment
    limit_per_sort=3,  # Tiny limit
    time_filter="week",
    mask_pii=False
)

print(f"Collection result: {success}")
