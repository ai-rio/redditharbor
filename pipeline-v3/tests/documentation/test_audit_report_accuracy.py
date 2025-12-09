#!/usr/bin/env python3
"""
TDD Test Suite: Documentation Accuracy Verification
Tests that the audit report accurately reflects actual test results.

RED Phase: This test will FAIL because documentation contains inaccurate claims.
GREEN Phase: Update documentation to make test pass.
REFACTOR Phase: Improve documentation clarity and consistency.
"""

import re
from pathlib import Path


class TestAuditReportAccuracy:
    """Verify audit report claims match reality."""

    @classmethod
    def setup_class(cls):
        """Load audit report content for testing."""
        audit_report_path = Path(__file__).parent.parent.parent / "agentops-agno-integration-audit-report.md"
        with open(audit_report_path, 'r') as f:
            cls.audit_content = f.read()

    def test_test_failure_rate_is_accurate(self):
        """Test that audit report shows 0% failure rate (7/7 passing) in Test Coverage section."""
        # Find the Test Coverage section specifically
        coverage_section = self._extract_section("Test Coverage")

        # Search for failure rate claims in Test Coverage section only
        failure_pattern = r"(\d+)/(\d+) \((\d+)% failure rate\)"
        match = re.search(failure_pattern, coverage_section)

        assert match, "No failure rate found in Test Coverage section"

        failed = int(match.group(1))
        total = int(match.group(2))
        percentage = int(match.group(3))

        # Assert current status: 0/7 (0% failure rate)
        assert failed == 0, f"Expected 0 failing tests, found {failed}"
        assert total == 7, f"Expected 7 total tests, found {total}"
        assert percentage == 0, f"Expected 0% failure rate, found {percentage}%"

    def _extract_section(self, section_name: str) -> str:
        """Extract a section from the audit report."""
        pattern = rf"##\s+{re.escape(section_name)}(.*?)(?=##|\Z)"
        match = re.search(pattern, self.audit_content, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1)
        return ""

    def test_requirement_5_1_shows_met(self):
        """Test that Requirement 5.1 (Enhanced Test Suite) shows Met status."""
        # Find Phase 5 section - looking for the status indicator
        phase5_pattern = r"Requirement 5\.1.*?Enhanced Test Suite.*?-\s*(❌|✅|⚠️)\s*\*\*(Not Met|Met|Partial)\*\*"
        match = re.search(phase5_pattern, self.audit_content, re.DOTALL | re.IGNORECASE)

        assert match, "Phase 5 Requirement 5.1 not found"

        emoji = match.group(1).strip()
        status = match.group(2).strip()

        assert emoji == "✅", f"Requirement 5.1 should show ✅ emoji, found: {emoji}"
        assert status == "Met", f"Requirement 5.1 should show Met status, found: {status}"

    def test_acceptance_criteria_ac2_passes(self):
        """Test that AC2 (Debug mode properly enabled) shows Pass status."""
        # Find AC2 in acceptance criteria table
        ac2_pattern = r"\|\s*AC2:.*?Debug mode.*?\|\s*(❌ Fail|✅ Pass|⚠️ Partial)\s*\|"
        match = re.search(ac2_pattern, self.audit_content, re.IGNORECASE)

        assert match, "AC2 not found in Acceptance Criteria table"

        status = match.group(1).strip()
        assert status == "✅ Pass", f"AC2 should show '✅ Pass', found: '{status}'"

    def test_acceptance_criteria_ac4_passes(self):
        """Test that AC4 (All tests pass) shows Pass status."""
        # Find AC4 in acceptance criteria table
        ac4_pattern = r"\|\s*AC4:.*?All tests pass.*?\|\s*(❌ Fail|✅ Pass|⚠️ Partial)\s*\|"
        match = re.search(ac4_pattern, self.audit_content, re.IGNORECASE)

        assert match, "AC4 not found in Acceptance Criteria table"

        status = match.group(1).strip()
        assert status == "✅ Pass", f"AC4 should show '✅ Pass', found: '{status}'"

    def test_ready_to_merge_is_yes(self):
        """Test that Sign-Off section shows Ready to Merge: Yes."""
        # Find Ready to Merge line in Sign-Off section
        merge_pattern = r"Ready to Merge.*?:\s*(❌ No|✅ Yes)"
        match = re.search(merge_pattern, self.audit_content, re.IGNORECASE)

        assert match, "Ready to Merge status not found in Sign-Off"

        status = match.group(1).strip()
        assert status == "✅ Yes", f"Should be ready to merge, found: '{status}'"
