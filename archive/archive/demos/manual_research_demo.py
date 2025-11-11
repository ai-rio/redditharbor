#!/usr/bin/env .venv/bin/python
"""
RedditHarbor Manual Research Demo
Create sample data representing findings from the 4 target domains
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from redditharbor.login import supabase

    from config.settings import *
except ImportError as e:
    print(f"Error: Could not import dependencies: {e}")
    sys.exit(1)

def create_sample_research_data():
    """Create sample research data based on typical Reddit discussions in our target domains"""
    print("🔬 RedditHarbor Manual Research Demo")
    print("=" * 40)
    print("Creating sample data from 4 target domains based on actual Reddit patterns")
    print()

    try:
        # Connect to Supabase
        supabase_client = supabase(
            url=SUPABASE_URL,
            private_key=SUPABASE_KEY
        )

        # Sample Reddit posts based on actual patterns from each domain
        sample_posts = [
            # Personal Finance Struggles (High-frequency daily problems)
            {
                'title': "How do you guys track small daily expenses? I keep losing track of where my $20-50 goes",
                'subreddit': 'personalfinance',
                'score': 342,
                'num_comments': 89,
                'domain': 'finance',
                'problem_type': 'daily_expense_tracking'
            },
            {
                'title': "My daily coffee habit is costing me $150/month. How do you break small spending habits?",
                'subreddit': 'personalfinance',
                'score': 567,
                'num_comments': 234,
                'domain': 'finance',
                'problem_type': 'small_habit_tracking'
            },
            {
                'title': "Struggling to save $5-10 per day. Any apps or tricks that actually work?",
                'subreddit': 'frugal',
                'score': 445,
                'num_comments': 167,
                'domain': 'finance',
                'problem_type': 'micro_savings'
            },

            # Skill Acquisition Pain Points
            {
                'title': "How do you stay consistent with coding practice? I keep skipping days and losing progress",
                'subreddit': 'learnprogramming',
                'score': 789,
                'num_comments': 312,
                'domain': 'learning',
                'problem_type': 'daily_consistency'
            },
            {
                'title': "Language learning streak apps work for first week, then I lose motivation. Help?",
                'subreddit': 'language_learning',
                'score': 623,
                'num_comments': 198,
                'domain': 'learning',
                'problem_type': 'motivation_decay'
            },
            {
                'title': "Can't remember what I studied yesterday. Need a better daily review system",
                'subreddit': 'study',
                'score': 412,
                'num_comments': 134,
                'domain': 'learning',
                'problem_type': 'retention_tracking'
            },

            # Chronic Disease Management (Daily routine problems)
            {
                'title': "Forget to take my medication 3x per week. What reminder systems actually work long-term?",
                'subreddit': 'ChronicIllness',
                'score': 856,
                'num_comments': 267,
                'domain': 'health',
                'problem_type': 'medication_adherence'
            },
            {
                'title': "How do you track daily symptoms without it becoming overwhelming? I need simple",
                'subreddit': 'diabetes',
                'score': 634,
                'num_comments': 189,
                'domain': 'health',
                'problem_type': 'symptom_tracking'
            },
            {
                'title': "Daily blood sugar logging is such a pain. Has anyone found a less annoying way?",
                'subreddit': 'diabetes',
                'score': 923,
                'num_comments': 301,
                'domain': 'health',
                'problem_type': 'daily_logging'
            },

            # Budget Travel Constraints
            {
                'title': "Hidden fees keep ruining my travel budget. How do you track all costs during trip?",
                'subreddit': 'budgettravel',
                'score': 445,
                'num_comments': 156,
                'domain': 'travel',
                'problem_type': 'hidden_fees'
            },
            {
                'title': "Daily travel expenses add up faster than expected. Need better real-time tracking",
                'subreddit': 'solotravel',
                'score': 367,
                'num_comments': 98,
                'domain': 'travel',
                'problem_type': 'real_time_tracking'
            },
            {
                'title': "How do you find cheap last-minute accommodations without spending hours searching?",
                'subreddit': 'backpacking',
                'score': 523,
                'num_comments': 187,
                'domain': 'travel',
                'problem_type': 'last_minute_booking'
            }
        ]

        print(f"📊 Inserting {len(sample_posts)} sample posts representing recurring problems...")

        inserted_count = 0
        for post in sample_posts:
            try:
                # Insert submission data
                result = supabase_client.table("submission").insert({
                    'title': post['title'],
                    'subreddit': post['subreddit'],
                    'score': post['score'],
                    'num_comments': post['num_comments']
                }).execute()

                inserted_count += 1
                print(f"   ✅ Inserted: r/{post['subreddit']} - {post['title'][:60]}...")

            except Exception as e:
                print(f"   ❌ Error inserting post: {e}")

        print(f"\n✅ Successfully inserted {inserted_count} sample research posts!")
        print("📈 Data represents high-frequency daily problems from:")
        print("   • Personal Finance: Daily expense tracking, habit breaking")
        print("   • Skill Learning: Consistency, motivation, retention")
        print("   • Health Management: Medication adherence, symptom tracking")
        print("   • Budget Travel: Real-time expense tracking, hidden fees")

        return inserted_count

    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return 0

if __name__ == "__main__":
    create_sample_research_data()
