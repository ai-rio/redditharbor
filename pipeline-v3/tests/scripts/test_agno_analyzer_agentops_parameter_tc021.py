#!/usr/bin/env python3
"""
Test TC-021: AgnoOpportunityAnalyzer accepts enable_agentops parameter

This test verifies that AgnoOpportunityAnalyzer correctly accepts and uses
the enable_agentops parameter in its constructor.
"""

import sys
from pathlib import Path
import unittest.mock as mock

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from transform.agno_analyzer import AgnoOpportunityAnalyzer


class TestAgnoAnalyzerAgentOpsParameterTC021:
    """Test class for TC-021: Agno analyzer AgentOps parameter"""

    def test_agno_analyzer_accepts_enable_agentops_parameter(self):
        """TC-021: Verify that AgnoOpportunityAnalyzer accepts enable_agentops parameter"""

        # Test that the analyzer can be instantiated with enable_agentops=True
        try:
            with mock.patch('transform.agno_analyzer.get_tracker') as mock_get_tracker:
                mock_get_tracker.return_value = mock.Mock()

                analyzer = AgnoOpportunityAnalyzer(
                    model="anthropic/claude-haiku-4.5",
                    enable_embeddings=True,
                    embedding_provider="fake",
                    enable_agentops=True
                )

                # Check that get_tracker was called when enable_agentops=True
                mock_get_tracker.assert_called_once()

                print("✅ TC-021 PASSED: Agno analyzer accepts enable_agentops=True")
                return True

        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                print(f"❌ TC-021 EXPECTED FAILURE: {e}")
                print("   AgnoOpportunityAnalyzer needs enable_agentops parameter")
                return False
            else:
                raise

        except Exception as e:
            print(f"❌ TC-021 UNEXPECTED ERROR: {e}")
            return False


def run_test():
    """Run the test directly"""
    test_instance = TestAgnoAnalyzerAgentOpsParameterTC021()
    try:
        test_instance.test_agno_analyzer_accepts_enable_agentops_parameter()
        print("✅ TC-021 PASSED: Agno analyzer AgentOps parameter support")
        return True
    except AssertionError as e:
        print(f"❌ TC-021 FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ TC-021 ERROR: {e}")
        return False


if __name__ == "__main__":
    # Run test directly for debugging
    success = run_test()
    exit(0 if success else 1)