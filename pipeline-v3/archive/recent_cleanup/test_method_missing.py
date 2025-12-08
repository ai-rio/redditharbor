#!/usr/bin/env python
"""
Direct test to verify start_analysis_session method is missing
"""

import sys

sys.path.insert(0, '/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3')

# Test 1: Verify the method doesn't exist (should fail)
try:
    from transform.agno_analyzer import AgnoOpportunityAnalyzer
    analyzer = AgnoOpportunityAnalyzer(enable_agentops=False)

    # Try to call the method - this should fail
    analyzer.start_analysis_session("test", ["tag"])
    print("ERROR: Method should not exist yet!")
except AttributeError as e:
    print(f"✓ Confirmed missing method: {e}")
    print("\nThis confirms the test failure is due to missing method.")
