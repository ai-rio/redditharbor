#!/usr/bin/env python3
"""
Test importing all modules that the batch script imports
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env.local')

def main():
    print("=" * 60)
    print("TESTING BATCH SCRIPT IMPORTS")
    print("=" * 60)

    print("Testing imports that batch_opportunity_scoring.py uses...")

    try:
        print("1. Importing basic modules...")
        import os
        import json
        import argparse
        from datetime import datetime, timezone
        from typing import Any, List, Dict
        from pathlib import Path
        print("   ✅ Basic modules imported")

        print("2. Importing project modules...")
        from config import SUPABASE_KEY, SUPABASE_URL
        from supabase import create_client
        print("   ✅ Project modules imported")

        print("3. Importing agent modules...")
        from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler
        from agent_tools.opportunity_analyzer_agent import OpportunityAnalyzerAgent
        print("   ✅ Agent modules imported")

        print("4. Importing hybrid strategy modules...")
        from agent_tools.monetization_llm_analyzer import MonetizationLLMAnalyzer, HYBRID_STRATEGY_CONFIG
        from core.lead_extractor import LeadExtractor
        print("   ✅ Hybrid strategy modules imported")

        print("5. Importing DLT modules...")
        try:
            import dlt
            print("   ✅ DLT imported")
        except ImportError as e:
            print(f"   ❌ DLT import failed: {e}")

        print("6. Importing redditharbor modules...")
        try:
            from redditharbor.dock.pipeline import reddit_harbor_dlt
            print("   ✅ redditharbor.dock.pipeline imported")
        except ImportError as e:
            print(f"   ❌ redditharbor.dock.pipeline import failed: {e}")

        print("7. Testing batch script function imports...")
        sys.path.append(str(project_root / 'scripts' / 'core'))
        try:
            from batch_opportunity_scoring import format_submission_for_agent, process_batch
            print("   ✅ batch_opportunity_scoring functions imported")
        except ImportError as e:
            print(f"   ❌ batch_opportunity_scoring import failed: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n✅ All import tests completed!")

if __name__ == "__main__":
    main()