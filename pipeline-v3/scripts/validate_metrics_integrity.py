#!/usr/bin/env python3
"""
Metrics Collection Integrity Validation
Comprehensive validation of pipeline_metrics data integrity and quality

Validation Requirements:
1. Data Completeness Check - Verify all critical fields are populated
2. Data Consistency Verification - Check format consistency
3. Relationship Integrity - Verify opportunity tracking completeness
4. Performance Metrics Validation - Validate calculations
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import psycopg2
from psycopg2.extras import RealDictCursor

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_settings


class MetricsIntegrityValidator:
    """Validates metrics collection integrity and quality"""

    def __init__(self):
        self.settings = get_settings()
        self.conn = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "validation_results": {},
            "data_quality_score": 0,
            "recommendations": []
        }

    def connect_db(self):
        """Connect to database"""
        try:
            # Use correct port for Supabase
            db_url = "postgresql://postgres:postgres@127.0.0.1:54331/postgres"
            self.conn = psycopg2.connect(db_url)
            print("✓ Database connection successful")
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False

    def validate_data_completeness(self, time_window_hours: int = 1) -> Dict[str, Any]:
        """
        Validation 1: Data Completeness Check
        Verify all critical fields are populated and no data loss
        """
        print("\n📊 1. Data Completeness Check")
        print("-" * 40)

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if pipeline_metrics table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'pipeline_metrics'
                );
            """)
            table_exists = cur.fetchone()['exists']

            if not table_exists:
                print("✗ pipeline_metrics table does not exist")
                return {
                    "status": "FAIL",
                    "error": "Table pipeline_metrics not found",
                    "recommendation": "Run metrics migration script first"
                }

            # Data Quality Check
            cur.execute(f"""
                SELECT
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN opportunity_id IS NULL THEN 1 END) as null_opp_id,
                    COUNT(CASE WHEN agent_name IS NULL THEN 1 END) as null_agent,
                    COUNT(CASE WHEN phase IS NULL THEN 1 END) as null_phase,
                    COUNT(CASE WHEN success IS NULL THEN 1 END) as null_success,
                    COUNT(CASE WHEN duration_seconds IS NULL THEN 1 END) as null_duration,
                    COUNT(CASE WHEN duration_seconds <= 0 THEN 1 END) as invalid_duration,
                    COUNT(CASE WHEN api_cost_usd IS NULL THEN 1 END) as null_cost,
                    COUNT(CASE WHEN api_cost_usd < 0 THEN 1 END) as negative_cost
                FROM pipeline_metrics
                WHERE created_at >= NOW() - INTERVAL '{time_window_hours} hour'
            """)

            result = cur.fetchone()

            # Calculate quality metrics
            total_records = result['total_records']
            if total_records == 0:
                print("⚠️  No records found in the last hour")
                return {
                    "status": "WARN",
                    "message": "No recent records found",
                    "total_records": 0
                }

            null_percentage = {
                "opportunity_id": (result['null_opp_id'] / total_records) * 100,
                "agent_name": (result['null_agent'] / total_records) * 100,
                "phase": (result['null_phase'] / total_records) * 100,
                "success": (result['null_success'] / total_records) * 100,
                "duration_seconds": (result['null_duration'] / total_records) * 100,
                "api_cost_usd": (result['null_cost'] / total_records) * 100
            }

            invalid_percentage = {
                "duration": (result['invalid_duration'] / total_records) * 100,
                "cost": (result['negative_cost'] / total_records) * 100
            }

            print(f"Total records: {total_records}")
            print("\nNULL value percentages:")
            for field, pct in null_percentage.items():
                status = "✓" if pct == 0 else "✗"
                print(f"  {status} {field}: {pct:.2f}%")

            print("\nInvalid value percentages:")
            for field, pct in invalid_percentage.items():
                status = "✓" if pct == 0 else "✗"
                print(f"  {status} {field}: {pct:.2f}%")

            # Determine status
            all_zeros = all(pct == 0 for pct in list(null_percentage.values()) + list(invalid_percentage.values()))
            status = "PASS" if all_zeros else "FAIL"

            return {
                "status": status,
                "total_records": total_records,
                "null_percentages": null_percentage,
                "invalid_percentages": invalid_percentage,
                "details": dict(result)
            }

    def validate_data_consistency(self, time_window_hours: int = 1) -> Dict[str, Any]:
        """
        Validation 2: Data Consistency Verification
        Check format consistency for all fields
        """
        print("\n🔍 2. Data Consistency Verification")
        print("-" * 40)

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Opportunity Coverage Check
            cur.execute(f"""
                SELECT
                    COUNT(DISTINCT opportunity_id) as unique_opportunities,
                    COUNT(*) as total_records,
                    MIN(opportunity_id) as min_opp_id,
                    MAX(opportunity_id) as max_opp_id,
                    COUNT(CASE WHEN opportunity_id ~ '^opp-[0-9]+$' THEN 1 END) as valid_format,
                    COUNT(CASE WHEN opportunity_id IS NOT NULL AND opportunity_id !~ '^opp-[0-9]+$' THEN 1 END) as invalid_format
                FROM pipeline_metrics
                WHERE created_at >= NOW() - INTERVAL '{time_window_hours} hour'
            """)

            opp_result = cur.fetchone()

            # Agent Distribution Check
            cur.execute(f"""
                SELECT
                    agent_name,
                    COUNT(*) as executions,
                    AVG(duration_seconds) as avg_duration,
                    AVG(api_cost_usd) as avg_cost,
                    COUNT(CASE WHEN success = false THEN 1 END) as errors
                FROM pipeline_metrics
                WHERE created_at >= NOW() - INTERVAL '{time_window_hours} hour'
                GROUP BY agent_name
                ORDER BY executions DESC
            """)

            agent_results = cur.fetchall()

            # Phase Distribution Check
            cur.execute(f"""
                SELECT
                    phase,
                    COUNT(*) as executions,
                    COUNT(CASE WHEN success = false THEN 1 END) as errors,
                    AVG(duration_seconds) as avg_duration
                FROM pipeline_metrics
                WHERE created_at >= NOW() - INTERVAL '{time_window_hours} hour'
                GROUP BY phase
                ORDER BY executions DESC
            """)

            phase_results = cur.fetchall()

            # Expected values
            expected_agents = ['wtp', 'segment', 'price', 'payment', 'market', 'consensus', 'all',
                             'reddit_client', 'database_loader', 'agno_analyzer']
            expected_phases = ['extract', 'transform', 'load', 'end_to_end']

            # Validate formats
            print(f"Unique opportunities: {opp_result['unique_opportunities']}")
            print(f"Opportunity format validation:")
            print(f"  ✓ Valid format (opp-xxxxx): {opp_result['valid_format']}")
            if opp_result['invalid_format'] > 0:
                print(f"  ✗ Invalid format: {opp_result['invalid_format']}")

            print("\nAgent distribution:")
            found_agents = set()
            for agent in agent_results:
                found_agents.add(agent['agent_name'])
                valid = "✓" if agent['agent_name'] in expected_agents else "⚠️"
                print(f"  {valid} {agent['agent_name']}: {agent['executions']} executions")

            missing_agents = set(expected_agents) - found_agents
            if missing_agents:
                print(f"  ⚠️  Missing agents: {', '.join(missing_agents)}")

            print("\nPhase distribution:")
            found_phases = set()
            for phase in phase_results:
                found_phases.add(phase['phase'])
                valid = "✓" if phase['phase'] in expected_phases else "✗"
                print(f"  {valid} {phase['phase']}: {phase['executions']} executions")

            missing_phases = set(expected_phases) - found_phases
            if missing_phases:
                print(f"  ⚠️  Missing phases: {', '.join(missing_phases)}")

            # Calculate consistency score
            format_valid_pct = (opp_result['valid_format'] / opp_result['total_records']) * 100 if opp_result['total_records'] > 0 else 0
            agent_coverage_pct = (len(found_agents & set(expected_agents)) / len(expected_agents)) * 100
            phase_coverage_pct = (len(found_phases & set(expected_phases)) / len(expected_phases)) * 100

            avg_consistency = (format_valid_pct + agent_coverage_pct + phase_coverage_pct) / 3
            status = "PASS" if avg_consistency >= 90 else "FAIL"

            return {
                "status": status,
                "consistency_score": round(avg_consistency, 2),
                "opportunity_validation": {
                    "unique_opportunities": opp_result['unique_opportunities'],
                    "valid_format_pct": format_valid_pct,
                    "invalid_count": opp_result['invalid_format']
                },
                "agent_validation": {
                    "found_agents": list(found_agents),
                    "missing_agents": list(missing_agents),
                    "coverage_pct": agent_coverage_pct
                },
                "phase_validation": {
                    "found_phases": list(found_phases),
                    "missing_phases": list(missing_phases),
                    "coverage_pct": phase_coverage_pct
                }
            }

    def validate_relationship_integrity(self, time_window_hours: int = 1) -> Dict[str, Any]:
        """
        Validation 3: Relationship Integrity
        Verify opportunity tracking completeness and phase order
        """
        print("\n🔗 3. Relationship Integrity Check")
        print("-" * 40)

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check opportunity pipeline completeness
            cur.execute(f"""
                SELECT
                    opportunity_id,
                    COUNT(DISTINCT phase) as phases_covered,
                    BOOL_AND(phase IN ('extract', 'transform', 'load', 'end_to_end')) as valid_phases,
                    COUNT(*) as total_executions
                FROM pipeline_metrics
                WHERE created_at >= NOW() - INTERVAL '{time_window_hours} hour'
                AND opportunity_id IS NOT NULL
                GROUP BY opportunity_id
                ORDER BY opportunity_id
            """)

            opportunity_results = cur.fetchall()

            # Phase execution order check
            cur.execute(f"""
                WITH phase_order AS (
                    SELECT
                        opportunity_id,
                        phase,
                        MIN(created_at) as first_execution,
                        ROW_NUMBER() OVER (
                            PARTITION BY opportunity_id
                            ORDER BY MIN(created_at)
                        ) as execution_order
                    FROM pipeline_metrics
                    WHERE created_at >= NOW() - INTERVAL '{time_window_hours} hour'
                    AND opportunity_id IS NOT NULL
                    AND phase IN ('extract', 'transform', 'load')
                    GROUP BY opportunity_id, phase
                )
                SELECT
                    opportunity_id,
                    STRING_AGG(phase || ' (' || execution_order || ')', ', ' ORDER BY execution_order) as phase_sequence
                FROM phase_order
                GROUP BY opportunity_id
                HAVING COUNT(DISTINCT phase) > 1
                LIMIT 10
            """)

            sequence_results = cur.fetchall()

            # Check for orphaned records (records without opportunity_id)
            cur.execute(f"""
                SELECT
                    COUNT(*) as orphaned_records,
                    phase,
                    agent_name
                FROM pipeline_metrics
                WHERE created_at >= NOW() - INTERVAL '{time_window_hours} hour'
                AND opportunity_id IS NULL
                GROUP BY phase, agent_name
            """)

            orphaned_results = cur.fetchall()

            print(f"Opportunities tracked: {len(opportunity_results)}")

            # Analyze completeness
            complete_opportunities = sum(1 for opp in opportunity_results if opp['phases_covered'] >= 3)
            partial_opportunities = len(opportunity_results) - complete_opportunities

            print(f"  Complete pipeline tracking: {complete_opportunities}")
            print(f"  Partial pipeline tracking: {partial_opportunities}")

            if sequence_results:
                print("\nPhase execution sequences (sample):")
                for seq in sequence_results[:5]:
                    print(f"  {seq['opportunity_id']}: {seq['phase_sequence']}")

            if orphaned_results:
                print("\nOrphaned records (no opportunity_id):")
                for orphan in orphaned_results:
                    print(f"  {orphan['phase']}/{orphan['agent_name']}: {orphan['orphaned_records']} records")

            # Calculate integrity score
            if len(opportunity_results) > 0:
                completeness_pct = (complete_opportunities / len(opportunity_results)) * 100
                orphaned_pct = (sum(r['orphaned_records'] for r in orphaned_results) /
                              (sum(r['total_executions'] for r in opportunity_results) +
                               sum(r['orphaned_records'] for r in orphaned_results))) * 100 if opportunity_results else 0
            else:
                completeness_pct = 0
                orphaned_pct = 0

            integrity_score = completeness_pct - (orphaned_pct * 0.5)
            status = "PASS" if integrity_score >= 80 else "FAIL"

            return {
                "status": status,
                "integrity_score": round(integrity_score, 2),
                "opportunity_tracking": {
                    "total_opportunities": len(opportunity_results),
                    "complete_tracking": complete_opportunities,
                    "partial_tracking": partial_opportunities,
                    "completeness_pct": completeness_pct
                },
                "orphaned_records": {
                    "total_orphaned": sum(r['orphaned_records'] for r in orphaned_results),
                    "orphaned_pct": orphaned_pct,
                    "details": [dict(r) for r in orphaned_results]
                }
            }

    def validate_performance_metrics(self, time_window_hours: int = 1) -> Dict[str, Any]:
        """
        Validation 4: Performance Metrics Validation
        Validate duration and cost calculations
        """
        print("\n📈 4. Performance Metrics Validation")
        print("-" * 40)

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Timestamp analysis
            cur.execute(f"""
                SELECT
                    MIN(created_at) as first_execution,
                    MAX(created_at) as last_execution,
                    EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at))) as total_seconds,
                    COUNT(DISTINCT opportunity_id) as opportunities_processed,
                    COUNT(*) as total_executions
                FROM pipeline_metrics
                WHERE created_at >= NOW() - INTERVAL '{time_window_hours} hour'
            """)

            timestamp_result = cur.fetchone()

            # Duration distribution analysis
            cur.execute(f"""
                SELECT
                    phase,
                    agent_name,
                    COUNT(*) as executions,
                    AVG(duration_seconds) as avg_duration,
                    MIN(duration_seconds) as min_duration,
                    MAX(duration_seconds) as max_duration,
                    STDDEV(duration_seconds) as stddev_duration,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_seconds) as median_duration,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_seconds) as p95_duration
                FROM pipeline_metrics
                WHERE created_at >= NOW() - INTERVAL '{time_window_hours} hour'
                AND duration_seconds > 0
                GROUP BY phase, agent_name
                ORDER BY avg_duration DESC
            """)

            duration_results = cur.fetchall()

            # Cost accumulation validation
            cur.execute(f"""
                SELECT
                    SUM(api_cost_usd) as total_cost,
                    AVG(api_cost_usd) as avg_cost,
                    MIN(api_cost_usd) as min_cost,
                    MAX(api_cost_usd) as max_cost,
                    COUNT(CASE WHEN api_cost_usd > 0 THEN 1 END) as non_zero_costs,
                    COUNT(*) as total_records
                FROM pipeline_metrics
                WHERE created_at >= NOW() - INTERVAL '{time_window_hours} hour'
            """)

            cost_result = cur.fetchone()

            print(f"Time window analysis:")
            if timestamp_result['first_execution']:
                duration_span = timestamp_result['total_seconds']
                print(f"  First execution: {timestamp_result['first_execution']}")
                print(f"  Last execution: {timestamp_result['last_execution']}")
                print(f"  Time span: {duration_span:.2f} seconds")
                print(f"  Opportunities processed: {timestamp_result['opportunities_processed']}")

                # Calculate throughput
                if duration_span > 0 and timestamp_result['opportunities_processed'] > 0:
                    throughput = timestamp_result['opportunities_processed'] / (duration_span / 3600)
                    print(f"  Throughput: {throughput:.2f} opportunities/hour")

            print("\nDuration distribution (top 5 by avg duration):")
            for dur in duration_results[:5]:
                print(f"  {dur['phase']}/{dur['agent_name']}:")
                print(f"    Avg: {dur['avg_duration']:.3f}s")
                print(f"    Range: {dur['min_duration']:.3f}s - {dur['max_duration']:.3f}s")
                print(f"    Median: {dur['median_duration']:.3f}s")
                print(f"    P95: {dur['p95_duration']:.3f}s")

            print(f"\nCost analysis:")
            print(f"  Total cost: ${cost_result['total_cost']:.6f}")
            print(f"  Average cost per execution: ${cost_result['avg_cost']:.6f}")
            print(f"  Non-zero cost records: {cost_result['non_zero_costs']}/{cost_result['total_records']}")

            # Validate reasonable ranges
            issues = []
            for dur in duration_results:
                if dur['max_duration'] > 300:  # > 5 minutes
                    issues.append(f"Very slow execution: {dur['phase']}/{dur['agent_name']} ({dur['max_duration']:.1f}s)")
                if dur['avg_duration'] > 60:  # > 1 minute average
                    issues.append(f"Slow average: {dur['phase']}/{dur['agent_name']} ({dur['avg_duration']:.1f}s)")

            if cost_result['max_cost'] > 1.0:  # > $1 per execution
                issues.append(f"High cost detected: ${cost_result['max_cost']:.2f}")

            if issues:
                print("\n⚠️  Performance issues detected:")
                for issue in issues:
                    print(f"  - {issue}")

            status = "PASS" if len(issues) == 0 else "WARN"

            return {
                "status": status,
                "time_window": {
                    "first_execution": timestamp_result['first_execution'].isoformat() if timestamp_result['first_execution'] else None,
                    "last_execution": timestamp_result['last_execution'].isoformat() if timestamp_result['last_execution'] else None,
                    "total_seconds": timestamp_result['total_seconds'],
                    "opportunities_processed": timestamp_result['opportunities_processed'],
                    "throughput_per_hour": timestamp_result['opportunities_processed'] / (timestamp_result['total_seconds'] / 3600) if timestamp_result['total_seconds'] > 0 else 0
                },
                "duration_analysis": {
                    "executions_analyzed": len(duration_results),
                    "issues_detected": issues
                },
                "cost_analysis": {
                    "total_cost": cost_result['total_cost'],
                    "avg_cost": cost_result['avg_cost'],
                    "cost_per_opportunity": cost_result['total_cost'] / timestamp_result['opportunities_processed'] if timestamp_result['opportunities_processed'] > 0 else 0
                }
            }

    def run_validation(self, time_window_hours: int = 1) -> Dict[str, Any]:
        """
        Run all validation checks and generate comprehensive report
        """
        print("=" * 60)
        print("METRICS COLLECTION INTEGRITY VALIDATION")
        print("=" * 60)
        print(f"Time window: Last {time_window_hours} hour(s)")

        if not self.connect_db():
            return {
                "overall_status": "FAIL",
                "error": "Database connection failed"
            }

        # Run all validations
        validations = [
            ("data_completeness", self.validate_data_completeness),
            ("data_consistency", self.validate_data_consistency),
            ("relationship_integrity", self.validate_relationship_integrity),
            ("performance_metrics", self.validate_performance_metrics)
        ]

        results = {}
        scores = []

        for validation_name, validation_func in validations:
            try:
                result = validation_func(time_window_hours)
                results[validation_name] = result

                # Extract score if available
                if 'consistency_score' in result:
                    scores.append(result['consistency_score'])
                elif 'integrity_score' in result:
                    scores.append(result['integrity_score'])

            except Exception as e:
                print(f"✗ {validation_name} validation failed: {e}")
                results[validation_name] = {
                    "status": "ERROR",
                    "error": str(e)
                }

        # Calculate overall data quality score
        if scores:
            self.results["data_quality_score"] = round(sum(scores) / len(scores), 2)
        else:
            # Derive from pass/fail status
            passed = sum(1 for r in results.values() if r.get("status") == "PASS")
            total = len(results)
            self.results["data_quality_score"] = round((passed / total) * 100, 2) if total > 0 else 0

        self.results["validation_results"] = results

        # Generate recommendations
        self._generate_recommendations(results)

        # Print summary
        self._print_summary()

        if self.conn:
            self.conn.close()

        return self.results

    def _generate_recommendations(self, results: Dict[str, Any]):
        """Generate recommendations based on validation results"""
        recommendations = []

        # Data completeness recommendations
        completeness = results.get("data_completeness", {})
        if completeness.get("status") == "FAIL":
            if completeness.get("null_percentages", {}).get("opportunity_id", 0) > 0:
                recommendations.append("Ensure opportunity_id is always populated during metric recording")
            if completeness.get("null_percentages", {}).get("duration_seconds", 0) > 0:
                recommendations.append("Fix duration calculation logic to avoid NULL values")

        # Data consistency recommendations
        consistency = results.get("data_consistency", {})
        if consistency.get("opportunity_validation", {}).get("valid_format_pct", 100) < 100:
            recommendations.append("Standardize opportunity_id format to 'opp-xxxxx'")
        missing_agents = consistency.get("agent_validation", {}).get("missing_agents", [])
        if missing_agents:
            recommendations.append(f"Ensure metrics are recorded for all agents: {', '.join(missing_agents)}")

        # Relationship integrity recommendations
        integrity = results.get("relationship_integrity", {})
        if integrity.get("integrity_score", 100) < 90:
            recommendations.append("Track complete pipeline execution for each opportunity")
        orphaned = integrity.get("orphaned_records", {}).get("total_orphaned", 0)
        if orphaned > 0:
            recommendations.append("Associate all metric records with an opportunity_id")

        # Performance metrics recommendations
        performance = results.get("performance_metrics", {})
        if performance.get("duration_analysis", {}).get("issues_detected"):
            recommendations.append("Investigate and optimize slow pipeline executions")

        if not recommendations:
            recommendations.append("All validations passed - metrics collection is operating correctly")

        self.results["recommendations"] = recommendations

    def _print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)

        print(f"\nOverall Data Quality Score: {self.results['data_quality_score']}%")

        print("\nValidation Results:")
        for name, result in self.results["validation_results"].items():
            status = result.get("status", "UNKNOWN")
            symbol = {
                "PASS": "✓",
                "FAIL": "✗",
                "WARN": "⚠️",
                "ERROR": "❌"
            }.get(status, "?")
            print(f"  {symbol} {name.replace('_', ' ').title()}: {status}")

        print("\nRecommendations:")
        for i, rec in enumerate(self.results["recommendations"], 1):
            print(f"  {i}. {rec}")

        # Overall status
        has_failures = any(
            r.get("status") in ["FAIL", "ERROR"]
            for r in self.results["validation_results"].values()
        )

        overall_status = "FAIL" if has_failures else "PASS"

        print("\n" + "=" * 60)
        if overall_status == "PASS":
            print("🎉 METRICS INTEGRITY VALIDATION PASSED")
        else:
            print("❌ METRICS INTEGRITY VALIDATION FAILED")
        print("=" * 60)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Validate metrics collection integrity")
    parser.add_argument(
        "--hours",
        type=int,
        default=1,
        help="Time window in hours to validate (default: 1)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file to save validation results (JSON)"
    )

    args = parser.parse_args()

    validator = MetricsIntegrityValidator()
    results = validator.run_validation(args.hours)

    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nValidation results saved to: {args.output}")

    # Exit with appropriate code
    sys.exit(0 if not any(
        r.get("status") in ["FAIL", "ERROR"]
        for r in results["validation_results"].values()
    ) else 1)


if __name__ == "__main__":
    main()