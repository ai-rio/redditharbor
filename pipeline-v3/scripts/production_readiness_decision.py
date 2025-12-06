#!/usr/bin/env python3
"""
Production Readiness Decision Generator
Aggregates Phase 1-3 results and makes GO/NO-GO recommendation

Decision Matrix:
- Production Ready: All Tier 1 PASS + All Tier 2 PASS → GO
- Needs Optimization: All Tier 1 PASS + 1-2 Tier 2 FAIL → CONDITIONAL GO
- Major Issues: 1-2 Tier 1 FAIL → NO-GO
- Complete Failure: 3+ Tier 1 FAIL → STOP
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import glob

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ProductionReadinessDecision:
    """Makes production readiness decision based on test results"""

    def __init__(self):
        self.reports_dir = project_root / "reports"
        self.decision = {
            "generated_at": datetime.now().isoformat(),
            "phase_results": {},
            "tier1_status": {},
            "tier2_status": {},
            "decision": "UNKNOWN",
            "confidence": 0.0,
            "recommendations": [],
            "deployment_plan": None
        }

    def load_latest_report(self, pattern: str) -> Dict:
        """Load most recent report matching pattern"""
        files = glob.glob(str(self.reports_dir / pattern))
        if not files:
            return None

        latest = max(files, key=lambda x: Path(x).stat().st_mtime)
        with open(latest, 'r') as f:
            return json.load(f)

    def analyze_phase1(self):
        """Analyze Phase 1 smoke test results"""
        print("📋 Phase 1: Smoke Test")
        # Smoke test doesn't have Tier KPIs, just infrastructure validation
        self.decision["phase_results"]["phase1"] = {
            "name": "Smoke Test",
            "status": "N/A - Infrastructure validation only"
        }
        print("  Status: Infrastructure validation (not scored)")

    def analyze_phase2(self):
        """Analyze Phase 2 quality validation results"""
        print("\n📋 Phase 2: Quality Validation")

        report = self.load_latest_report("quality_report_*.json")
        if not report:
            print("  ⚠️  No quality report found")
            self.decision["phase_results"]["phase2"] = {"status": "MISSING"}
            return

        tier1_kpis = report.get("tier1_kpis", {})

        # Extract Tier 1 results
        for kpi_name, kpi_data in tier1_kpis.items():
            status = kpi_data.get("status", "UNKNOWN")
            self.decision["tier1_status"][f"phase2_{kpi_name}"] = status
            print(f"  {'✓' if status == 'PASS' else '✗'} {kpi_name}: {status}")

        self.decision["phase_results"]["phase2"] = {
            "name": "Quality Validation",
            "overall_status": report.get("overall_status", "UNKNOWN"),
            "kpis_passed": sum(1 for v in tier1_kpis.values() if v.get("status") == "PASS"),
            "kpis_total": len(tier1_kpis)
        }

    def analyze_phase3(self):
        """Analyze Phase 3 performance validation results"""
        print("\n📋 Phase 3: Performance Validation")

        report = self.load_latest_report("performance_report_*.json")
        if not report:
            print("  ⚠️  No performance report found")
            self.decision["phase_results"]["phase3"] = {"status": "MISSING"}
            return

        tier2_kpis = report.get("tier2_kpis", {})

        # Extract Tier 2 results
        for kpi_name, kpi_data in tier2_kpis.items():
            status = kpi_data.get("status", "UNKNOWN")
            self.decision["tier2_status"][f"phase3_{kpi_name}"] = status
            print(f"  {'✓' if status == 'PASS' else '✗'} {kpi_name}: {status}")

        self.decision["phase_results"]["phase3"] = {
            "name": "Performance Validation",
            "overall_status": report.get("overall_status", "UNKNOWN"),
            "kpis_passed": sum(1 for v in tier2_kpis.values() if v.get("status") == "PASS"),
            "kpis_total": len(tier2_kpis)
        }

    def make_decision(self):
        """Apply decision matrix and make GO/NO-GO recommendation"""
        print("\n" + "=" * 80)
        print("PRODUCTION READINESS DECISION")
        print("=" * 80)

        # Count Tier 1 and Tier 2 results
        tier1_pass = sum(1 for v in self.decision["tier1_status"].values() if v == "PASS")
        tier1_fail = sum(1 for v in self.decision["tier1_status"].values() if v == "FAIL")
        tier1_total = len(self.decision["tier1_status"])

        tier2_pass = sum(1 for v in self.decision["tier2_status"].values() if v == "PASS")
        tier2_fail = sum(1 for v in self.decision["tier2_status"].values() if v == "FAIL")
        tier2_total = len(self.decision["tier2_status"])

        print(f"\nTier 1 (Business Value): {tier1_pass}/{tier1_total} PASS")
        print(f"Tier 2 (Performance): {tier2_pass}/{tier2_total} PASS")

        # Apply decision matrix
        if tier1_fail >= 3:
            # Complete Failure
            self.decision["decision"] = "🛑 STOP"
            self.decision["confidence"] = 1.0
            self.decision["recommendations"] = [
                "CRITICAL: 3+ Tier 1 KPIs failed",
                "Redesign Required: Multi-agent approach may not be viable",
                "Conduct comprehensive post-mortem",
                "Evaluate alternative architectures",
                "DO NOT proceed to production"
            ]
            self.decision["deployment_plan"] = "NONE - Redesign required"

        elif tier1_fail >= 1:
            # Major Issues
            self.decision["decision"] = "❌ NO-GO"
            self.decision["confidence"] = 0.9
            self.decision["recommendations"] = [
                f"Fix {tier1_fail} critical Tier 1 KPI failure(s)",
                "Re-run Phase 2 validation after fixes",
                "Root cause analysis required for failures",
                "Consider architecture adjustments",
                "DO NOT deploy until all Tier 1 KPIs pass"
            ]
            self.decision["deployment_plan"] = "Fix critical issues → Re-validate → Re-assess"

        elif tier1_pass == tier1_total and tier2_pass == tier2_total:
            # Production Ready
            self.decision["decision"] = "✅ GO - Production Ready"
            self.decision["confidence"] = 1.0
            self.decision["recommendations"] = [
                "All KPIs passed - system ready for production",
                "Deploy with full monitoring enabled",
                "Set up AgentOps dashboards",
                "Create production runbook",
                "Schedule weekly quality reviews for first month"
            ]
            self.decision["deployment_plan"] = "Immediate → Full production deployment"

        elif tier1_pass == tier1_total and tier2_fail <= 2:
            # Needs Optimization
            self.decision["decision"] = "⚠️  CONDITIONAL GO"
            self.decision["confidence"] = 0.7
            self.decision["recommendations"] = [
                "All critical business KPIs passed",
                f"Optimize {tier2_fail} performance KPI(s) that failed",
                "Deploy with conservative rate limits",
                "Monitor closely for 2 weeks",
                "Create optimization roadmap (2-4 weeks)",
                "Performance improvements can be done post-launch"
            ]
            self.decision["deployment_plan"] = "Staged deployment → Monitor → Optimize in parallel"

        else:
            # Edge case
            self.decision["decision"] = "⚠️  UNCERTAIN"
            self.decision["confidence"] = 0.0
            self.decision["recommendations"] = [
                "Unusual test results - manual review required",
                "Check test data completeness",
                "Re-run failed test phases"
            ]
            self.decision["deployment_plan"] = "Manual review required"

    def print_decision(self):
        """Print final decision and recommendations"""
        print("\n" + "=" * 80)
        print(f"FINAL DECISION: {self.decision['decision']}")
        print(f"Confidence: {self.decision['confidence']*100:.0f}%")
        print("=" * 80)

        print("\n📋 RECOMMENDATIONS:")
        for i, rec in enumerate(self.decision["recommendations"], 1):
            print(f"{i}. {rec}")

        print(f"\n📅 DEPLOYMENT PLAN:")
        print(f"   {self.decision['deployment_plan']}")

        print("\n" + "=" * 80)

    def save_decision(self):
        """Save decision to file"""
        decision_path = self.reports_dir / f"production_readiness_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        decision_path.parent.mkdir(exist_ok=True)

        with open(decision_path, 'w') as f:
            json.dump(self.decision, f, indent=2)

        print(f"\n💾 Decision saved to: {decision_path}")

    def generate_decision(self) -> dict:
        """Generate complete production readiness decision"""
        print("=" * 80)
        print("AGGREGATING LIVE TEST RESULTS")
        print("=" * 80)

        self.analyze_phase1()
        self.analyze_phase2()
        self.analyze_phase3()

        self.make_decision()
        self.print_decision()
        self.save_decision()

        return self.decision


def main():
    """Main entry point"""
    decision_maker = ProductionReadinessDecision()
    decision = decision_maker.generate_decision()

    # Exit codes:
    # 0 = GO (Production Ready)
    # 1 = CONDITIONAL GO (Needs Optimization)
    # 2 = NO-GO (Major Issues)
    # 3 = STOP (Complete Failure)
    exit_codes = {
        "✅ GO - Production Ready": 0,
        "⚠️  CONDITIONAL GO": 1,
        "❌ NO-GO": 2,
        "🛑 STOP": 3,
        "⚠️  UNCERTAIN": 2
    }

    sys.exit(exit_codes.get(decision["decision"], 2))


if __name__ == "__main__":
    main()
