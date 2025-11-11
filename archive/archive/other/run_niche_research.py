#!/usr/bin/env .venv/bin/python
"""
RedditHarbor Niche Research Runner
Execute all 4 niche research studies to identify recurring problems for app business models
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def run_all_niche_research():
    """Run all 4 niche research studies"""
    print("🔬 RedditHarbor Niche Research: Finding App Business Opportunities")
    print("=" * 65)
    print("Goal: Identify most recurrent daily problems across 4 domains")
    print("Domains: Personal Finance, Skill Acquisition, Chronic Disease, Budget Travel")
    print()

    try:
        # Import our research modules
        from research_budget_travel import research_budget_travel_constraints
        from research_chronic_disease import research_chronic_disease_management
        from research_personal_finance import research_personal_finance_struggles
        from research_skill_acquisition import research_skill_acquisition_pain_points

        print("📊 Starting 4-domain niche research...")
        print()

        # Research 1: Personal Finance Struggles
        print("1️⃣ Personal Finance Daily Struggles")
        research_personal_finance_struggles()
        print()

        # Research 2: Skill Acquisition Pain Points
        print("2️⃣ Skill Acquisition Pain Points")
        research_skill_acquisition_pain_points()
        print()

        # Research 3: Chronic Disease Management
        print("3️⃣ Chronic Disease Daily Management")
        research_chronic_disease_management()
        print()

        # Research 4: Budget Travel Constraints
        print("4️⃣ Budget Travel Constraints")
        research_budget_travel_constraints()
        print()

        print("🎉 All niche research complete!")
        print("=" * 40)
        print("📈 Next Steps:")
        print("1. Analyze data in Supabase Studio: http://127.0.0.1:54323")
        print("2. Look for high-frequency recurring problems")
        print("3. Identify solvable daily pain points")
        print("4. Develop 1-3 functionality app business models")
        print()
        print("🔍 Analysis Focus Areas:")
        print("• Common themes across submissions and comments")
        print("• Daily vs. occasional problems")
        print("• Emotional intensity of frustrations")
        print("• Existing solution gaps")

    except ImportError as e:
        print(f"❌ Error importing research modules: {e}")
        print("Make sure all research scripts are in the scripts/ directory")
    except Exception as e:
        print(f"❌ Error running research: {e}")

def interactive_research_menu():
    """Interactive menu for running specific research studies"""
    print("🔬 RedditHarbor Niche Research Menu")
    print("=" * 40)
    print("Select research to run:")
    print()
    print("1. 💰 Personal Finance Daily Struggles")
    print("2. 🎓 Skill Acquisition Pain Points")
    print("3. 🏥 Chronic Disease Daily Management")
    print("4. ✈️ Budget Travel Constraints")
    print("5. 🚀 Run All 4 Studies (Recommended)")
    print()

    try:
        choice = input("Select research (1-5): ")

        if choice == "1":
            from research_personal_finance import research_personal_finance_struggles
            research_personal_finance_struggles()
        elif choice == "2":
            from research_skill_acquisition import (
                research_skill_acquisition_pain_points,
            )
            research_skill_acquisition_pain_points()
        elif choice == "3":
            from research_chronic_disease import research_chronic_disease_management
            research_chronic_disease_management()
        elif choice == "4":
            from research_budget_travel import research_budget_travel_constraints
            research_budget_travel_constraints()
        elif choice == "5":
            run_all_niche_research()
        else:
            print("❌ Invalid choice. Please select 1-5.")

    except KeyboardInterrupt:
        print("\n👋 Research cancelled.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔬 RedditHarbor Niche Research Platform")
    print("=" * 40)
    print("Purpose: Find recurring daily problems for app opportunities")
    print()
    print("🚀 Running all 4 niche research studies automatically...")

    # Run all research automatically for non-interactive execution
    run_all_niche_research()
