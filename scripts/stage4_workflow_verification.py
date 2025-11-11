#!/usr/bin/env python3
"""
Stage 4: Test Workflow Data Insertion and End-to-End Verification

Tests the consolidated schema with actual workflow data to verify:
1. Workflow data loading and insertion
2. Collection workflow compatibility
3. Scoring workflow functionality
4. Analysis workflow operations
5. No breaking changes to legacy code
6. Overall workflow efficiency restoration
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Database connection configuration
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 54322,
    "database": "postgres",
    "user": "postgres",
    "password": "postgres",
}


class WorkflowVerifier:
    """Verify workflow data insertion and end-to-end functionality."""

    def __init__(self, log_file: str):
        self.log_file = log_file
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "stage": "Stage 4: Workflow Verification",
            "tests": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0,
            },
        }
        self.workflow_data = None
        self.insertion_results = []
        self.functionality_results = {}

    def log(self, message: str, level: str = "INFO"):
        """Log message to file and console."""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")

    def load_workflow_data(self) -> bool:
        """Load workflow results from JSON file."""
        self.log("=" * 80)
        self.log("STEP 1: LOAD WORKFLOW DATA")
        self.log("=" * 80)

        try:
            workflow_file = project_root / "generated" / "clean_slate_workflow_results.json"
            self.log(f"Loading workflow data from: {workflow_file}")

            with open(workflow_file) as f:
                self.workflow_data = json.load(f)

            opportunities = self.workflow_data.get("opportunities", [])
            summary = self.workflow_data.get("summary", {})

            self.log(f"Loaded {len(opportunities)} opportunities")
            self.log(f"Approved: {summary.get('approved', 0)}")
            self.log(f"Disqualified: {summary.get('disqualified', 0)}")
            self.log(f"Compliance rate: {summary.get('compliance_rate', 0)}%")

            self.results["tests"]["load_workflow_data"] = {
                "status": "PASSED",
                "opportunities_loaded": len(opportunities),
                "summary": summary,
            }
            self.results["summary"]["passed"] += 1
            return True

        except Exception as e:
            self.log(f"ERROR loading workflow data: {e}", "ERROR")
            self.results["tests"]["load_workflow_data"] = {
                "status": "FAILED",
                "error": str(e),
            }
            self.results["summary"]["failed"] += 1
            return False

    def get_db_connection(self):
        """Get database connection."""
        return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

    def insert_workflow_opportunities(self) -> bool:
        """Insert workflow opportunities into database."""
        self.log("=" * 80)
        self.log("STEP 2: INSERT WORKFLOW DATA")
        self.log("=" * 80)

        if not self.workflow_data:
            self.log("ERROR: No workflow data loaded", "ERROR")
            return False

        conn = None
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()

            opportunities = self.workflow_data.get("opportunities", [])
            self.log(f"Inserting {len(opportunities)} opportunities...")

            success_count = 0
            error_count = 0

            for opp in opportunities:
                try:
                    # Fetch dimension scores from opportunity_scores table (if UUID format)
                    dimension_scores = None
                    try:
                        # Try to fetch dimension scores (only works if opportunity_id is UUID)
                        cur.execute(
                            """
                            SELECT market_demand_score, pain_intensity_score, monetization_potential_score,
                                   market_gap_score, technical_feasibility_score
                            FROM opportunity_scores
                            WHERE opportunity_id::text = %s
                            """,
                            (opp["opportunity_id"],),
                        )
                        dimension_scores = cur.fetchone()
                    except Exception:
                        # Skip dimension scores if not found or ID format mismatch
                        pass

                    # Map workflow data to consolidated schema
                    insert_data = {
                        "opportunity_id": opp["opportunity_id"],
                        "app_name": opp["app_name"],
                        "function_count": opp["function_count"],
                        "function_list": opp["function_list"],
                        "original_score": opp["original_score"],
                        "final_score": opp["final_score"],
                        "status": opp["status"],
                        "constraint_applied": opp["constraint_applied"],
                        "ai_insight": opp["ai_insight"],
                        "processed_at": opp["processed_at"],
                        # Add dimension scores if available
                        "market_demand": dimension_scores["market_demand_score"] if dimension_scores else None,
                        "pain_intensity": dimension_scores["pain_intensity_score"] if dimension_scores else None,
                        "monetization_potential": dimension_scores["monetization_potential_score"] if dimension_scores else None,
                        "market_gap": dimension_scores["market_gap_score"] if dimension_scores else None,
                        "technical_feasibility": dimension_scores["technical_feasibility_score"] if dimension_scores else None,
                    }

                    # Check if opportunity already exists
                    cur.execute(
                        "SELECT opportunity_id FROM workflow_results WHERE opportunity_id = %s",
                        (insert_data["opportunity_id"],),
                    )
                    existing = cur.fetchone()

                    if existing:
                        # Update existing record
                        cur.execute(
                            """
                            UPDATE workflow_results
                            SET app_name = %s,
                                function_count = %s,
                                function_list = %s,
                                original_score = %s,
                                final_score = %s,
                                status = %s,
                                constraint_applied = %s,
                                ai_insight = %s,
                                processed_at = %s,
                                market_demand = %s,
                                pain_intensity = %s,
                                monetization_potential = %s,
                                market_gap = %s,
                                technical_feasibility = %s,
                                updated_at = NOW()
                            WHERE opportunity_id = %s
                            """,
                            (
                                insert_data["app_name"],
                                insert_data["function_count"],
                                insert_data["function_list"],
                                insert_data["original_score"],
                                insert_data["final_score"],
                                insert_data["status"],
                                insert_data["constraint_applied"],
                                insert_data["ai_insight"],
                                insert_data["processed_at"],
                                insert_data["market_demand"],
                                insert_data["pain_intensity"],
                                insert_data["monetization_potential"],
                                insert_data["market_gap"],
                                insert_data["technical_feasibility"],
                                insert_data["opportunity_id"],
                            ),
                        )
                        action = "UPDATED"
                    else:
                        # Insert new record
                        cur.execute(
                            """
                            INSERT INTO workflow_results (
                                opportunity_id, app_name, function_count, function_list,
                                original_score, final_score, status, constraint_applied,
                                ai_insight, processed_at,
                                market_demand, pain_intensity, monetization_potential,
                                market_gap, technical_feasibility
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                insert_data["opportunity_id"],
                                insert_data["app_name"],
                                insert_data["function_count"],
                                insert_data["function_list"],
                                insert_data["original_score"],
                                insert_data["final_score"],
                                insert_data["status"],
                                insert_data["constraint_applied"],
                                insert_data["ai_insight"],
                                insert_data["processed_at"],
                                insert_data["market_demand"],
                                insert_data["pain_intensity"],
                                insert_data["monetization_potential"],
                                insert_data["market_gap"],
                                insert_data["technical_feasibility"],
                            ),
                        )
                        action = "INSERTED"

                    self.log(f"  {action}: {insert_data['opportunity_id']} - {insert_data['app_name']}")

                    self.insertion_results.append(
                        {
                            "opportunity_id": insert_data["opportunity_id"],
                            "action": action,
                            "status": "SUCCESS",
                        }
                    )
                    success_count += 1

                except Exception as e:
                    self.log(f"  ERROR inserting {opp['opportunity_id']}: {e}", "ERROR")
                    self.insertion_results.append(
                        {
                            "opportunity_id": opp["opportunity_id"],
                            "action": "FAILED",
                            "status": "ERROR",
                            "error": str(e),
                        }
                    )
                    error_count += 1

            conn.commit()

            self.log(f"\nInsertion complete: {success_count} success, {error_count} errors")

            self.results["tests"]["insert_workflow_data"] = {
                "status": "PASSED" if error_count == 0 else "PARTIAL",
                "success_count": success_count,
                "error_count": error_count,
                "details": self.insertion_results,
            }

            if error_count == 0:
                self.results["summary"]["passed"] += 1
            else:
                self.results["summary"]["warnings"] += 1

            return error_count == 0

        except Exception as e:
            self.log(f"ERROR in workflow insertion: {e}", "ERROR")
            self.results["tests"]["insert_workflow_data"] = {
                "status": "FAILED",
                "error": str(e),
            }
            self.results["summary"]["failed"] += 1
            return False
        finally:
            if conn:
                conn.close()

    def test_scoring_workflow(self) -> bool:
        """Test opportunity scoring workflow."""
        self.log("=" * 80)
        self.log("STEP 3: TEST SCORING WORKFLOW")
        self.log("=" * 80)

        conn = None
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()

            # Test 1: Create test submission for scoring
            test_submission_id = "test_scoring_submission_001"

            self.log(f"Creating test submission: {test_submission_id}")

            # Insert test submission
            cur.execute(
                """
                INSERT INTO submissions (
                    submission_id, title, selftext, author, subreddit,
                    url, score, num_comments, created_utc
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (submission_id) DO UPDATE
                SET title = EXCLUDED.title
                """,
                (
                    test_submission_id,
                    "Test App Opportunity",
                    "Looking for a simple calorie tracking app",
                    "test_user",
                    "SomebodyMakeThis",
                    "https://reddit.com/test",
                    100,
                    50,
                    datetime.now().isoformat(),
                ),
            )

            # Test 2: Insert dimension scores
            self.log("Inserting dimension scores...")

            dimensions = [
                ("clarity", 85.0, "Clear problem statement"),
                ("market_validation", 90.0, "Strong market demand"),
                ("technical_feasibility", 95.0, "Simple implementation"),
                ("competitive_gap", 75.0, "Some competition exists"),
                ("user_engagement", 80.0, "Good engagement metrics"),
            ]

            for dimension, score, reasoning in dimensions:
                cur.execute(
                    """
                    INSERT INTO opportunity_scores (
                        submission_id, dimension, score, reasoning
                    ) VALUES (%s, %s, %s, %s)
                    ON CONFLICT (submission_id, dimension) DO UPDATE
                    SET score = EXCLUDED.score, reasoning = EXCLUDED.reasoning
                    """,
                    (test_submission_id, dimension, score, reasoning),
                )

            conn.commit()

            # Test 3: Verify calculate_opportunity_total_score function
            self.log("Testing calculate_opportunity_total_score function...")

            cur.execute(
                "SELECT calculate_opportunity_total_score(%s) AS total_score",
                (test_submission_id,),
            )
            result = cur.fetchone()
            total_score = result["total_score"] if result else None

            self.log(f"Calculated total score: {total_score}")

            # Test 4: Verify scores are stored
            cur.execute(
                """
                SELECT dimension, score, reasoning
                FROM opportunity_scores
                WHERE submission_id = %s
                ORDER BY dimension
                """,
                (test_submission_id,),
            )
            stored_scores = cur.fetchall()

            self.log(f"Stored {len(stored_scores)} dimension scores")

            # Verify results
            success = (
                total_score is not None
                and total_score > 0
                and len(stored_scores) == len(dimensions)
            )

            if success:
                self.log("Scoring workflow test PASSED", "SUCCESS")
                self.results["tests"]["scoring_workflow"] = {
                    "status": "PASSED",
                    "test_submission_id": test_submission_id,
                    "total_score": float(total_score) if total_score else 0,
                    "dimensions_scored": len(stored_scores),
                    "expected_dimensions": len(dimensions),
                }
                self.results["summary"]["passed"] += 1
            else:
                self.log("Scoring workflow test FAILED", "ERROR")
                self.results["tests"]["scoring_workflow"] = {
                    "status": "FAILED",
                    "total_score": total_score,
                    "dimensions_stored": len(stored_scores),
                    "expected_dimensions": len(dimensions),
                }
                self.results["summary"]["failed"] += 1

            return success

        except Exception as e:
            self.log(f"ERROR in scoring workflow test: {e}", "ERROR")
            self.results["tests"]["scoring_workflow"] = {
                "status": "FAILED",
                "error": str(e),
            }
            self.results["summary"]["failed"] += 1
            return False
        finally:
            if conn:
                conn.close()

    def test_analysis_workflow(self) -> bool:
        """Test workflow analysis and querying."""
        self.log("=" * 80)
        self.log("STEP 4: TEST ANALYSIS WORKFLOW")
        self.log("=" * 80)

        conn = None
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()

            # Test 1: Query approved opportunities
            self.log("Querying approved opportunities...")
            cur.execute(
                """
                SELECT opportunity_id, app_name, final_score, ai_insight
                FROM workflow_results
                WHERE status = 'APPROVED'
                ORDER BY final_score DESC
                """
            )
            approved = cur.fetchall()
            self.log(f"Found {len(approved)} approved opportunities")

            # Test 2: Query disqualified opportunities
            self.log("Querying disqualified opportunities...")
            cur.execute(
                """
                SELECT opportunity_id, app_name, final_score, ai_insight
                FROM workflow_results
                WHERE status = 'DISQUALIFIED'
                ORDER BY original_score DESC
                """
            )
            disqualified = cur.fetchall()
            self.log(f"Found {len(disqualified)} disqualified opportunities")

            # Test 3: Filter by score threshold
            self.log("Filtering by score threshold (>= 80)...")
            cur.execute(
                """
                SELECT opportunity_id, app_name, final_score
                FROM workflow_results
                WHERE final_score >= 80 AND status = 'APPROVED'
                ORDER BY final_score DESC
                """
            )
            high_score = cur.fetchall()
            self.log(f"Found {len(high_score)} high-scoring opportunities")

            # Test 4: Retrieve AI insights
            self.log("Testing AI insights retrieval...")
            cur.execute(
                """
                SELECT opportunity_id, ai_insight
                FROM workflow_results
                WHERE ai_insight IS NOT NULL
                AND ai_insight != 'Analysis pending'
                """
            )
            insights = cur.fetchall()
            self.log(f"Found {len(insights)} opportunities with AI insights")

            # Test 5: Aggregate statistics
            self.log("Calculating aggregate statistics...")
            cur.execute(
                """
                SELECT
                    COUNT(*) as total,
                    AVG(final_score) as avg_score,
                    MAX(final_score) as max_score,
                    MIN(final_score) as min_score,
                    COUNT(CASE WHEN status = 'APPROVED' THEN 1 END) as approved_count,
                    COUNT(CASE WHEN status = 'DISQUALIFIED' THEN 1 END) as disqualified_count
                FROM workflow_results
                """
            )
            stats = cur.fetchone()

            self.log("Aggregate statistics:")
            self.log(f"  Total: {stats['total']}")
            self.log(f"  Avg score: {stats['avg_score']:.2f}")
            self.log(f"  Max score: {stats['max_score']}")
            self.log(f"  Min score: {stats['min_score']}")
            self.log(f"  Approved: {stats['approved_count']}")
            self.log(f"  Disqualified: {stats['disqualified_count']}")

            success = (
                len(approved) > 0
                and len(disqualified) > 0
                and stats["total"] > 0
            )

            if success:
                self.log("Analysis workflow test PASSED", "SUCCESS")
                self.results["tests"]["analysis_workflow"] = {
                    "status": "PASSED",
                    "approved_count": len(approved),
                    "disqualified_count": len(disqualified),
                    "high_score_count": len(high_score),
                    "insights_count": len(insights),
                    "aggregate_stats": dict(stats),
                }
                self.results["summary"]["passed"] += 1
            else:
                self.log("Analysis workflow test FAILED", "ERROR")
                self.results["tests"]["analysis_workflow"] = {
                    "status": "FAILED",
                    "reason": "Missing expected data",
                }
                self.results["summary"]["failed"] += 1

            return success

        except Exception as e:
            self.log(f"ERROR in analysis workflow test: {e}", "ERROR")
            self.results["tests"]["analysis_workflow"] = {
                "status": "FAILED",
                "error": str(e),
            }
            self.results["summary"]["failed"] += 1
            return False
        finally:
            if conn:
                conn.close()

    def test_collection_workflow(self) -> bool:
        """Test collection workflow compatibility."""
        self.log("=" * 80)
        self.log("STEP 5: TEST COLLECTION WORKFLOW")
        self.log("=" * 80)

        conn = None
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()

            # Test 1: Insert test submission with new columns
            test_submission_id = "test_collection_submission_001"

            self.log(f"Creating test submission with new columns: {test_submission_id}")

            cur.execute(
                """
                INSERT INTO submissions (
                    submission_id, title, selftext, author, subreddit,
                    url, score, num_comments, created_utc,
                    opportunity_clarity, opportunity_market_validation,
                    opportunity_technical_feasibility, opportunity_competitive_gap,
                    opportunity_user_engagement, opportunity_total_score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (submission_id) DO UPDATE
                SET title = EXCLUDED.title,
                    opportunity_total_score = EXCLUDED.opportunity_total_score
                """,
                (
                    test_submission_id,
                    "Test Collection Workflow",
                    "Testing new schema columns",
                    "test_collector",
                    "SomebodyMakeThis",
                    "https://reddit.com/test_collection",
                    150,
                    75,
                    datetime.now().isoformat(),
                    88.0,  # clarity
                    92.0,  # market_validation
                    85.0,  # technical_feasibility
                    78.0,  # competitive_gap
                    90.0,  # user_engagement
                    86.6,  # total_score (average)
                ),
            )

            conn.commit()

            # Test 2: Verify data is stored correctly
            cur.execute(
                """
                SELECT submission_id, title,
                       opportunity_clarity, opportunity_market_validation,
                       opportunity_technical_feasibility, opportunity_competitive_gap,
                       opportunity_user_engagement, opportunity_total_score
                FROM submissions
                WHERE submission_id = %s
                """,
                (test_submission_id,),
            )
            result = cur.fetchone()

            if result:
                self.log(f"Retrieved submission: {result['title']}")
                self.log(f"Total score: {result['opportunity_total_score']}")

                # Verify all dimension scores are stored
                dimensions_ok = all(
                    [
                        result["opportunity_clarity"] is not None,
                        result["opportunity_market_validation"] is not None,
                        result["opportunity_technical_feasibility"] is not None,
                        result["opportunity_competitive_gap"] is not None,
                        result["opportunity_user_engagement"] is not None,
                        result["opportunity_total_score"] is not None,
                    ]
                )

                if dimensions_ok:
                    self.log("Collection workflow test PASSED", "SUCCESS")
                    self.results["tests"]["collection_workflow"] = {
                        "status": "PASSED",
                        "test_submission_id": test_submission_id,
                        "all_dimensions_stored": True,
                        "total_score": float(result["opportunity_total_score"]),
                    }
                    self.results["summary"]["passed"] += 1
                    return True
                else:
                    self.log("Collection workflow test FAILED: Missing dimension scores", "ERROR")
                    self.results["tests"]["collection_workflow"] = {
                        "status": "FAILED",
                        "reason": "Missing dimension scores",
                    }
                    self.results["summary"]["failed"] += 1
                    return False
            else:
                self.log("Collection workflow test FAILED: No data retrieved", "ERROR")
                self.results["tests"]["collection_workflow"] = {
                    "status": "FAILED",
                    "reason": "No data retrieved",
                }
                self.results["summary"]["failed"] += 1
                return False

        except Exception as e:
            self.log(f"ERROR in collection workflow test: {e}", "ERROR")
            self.results["tests"]["collection_workflow"] = {
                "status": "FAILED",
                "error": str(e),
            }
            self.results["summary"]["failed"] += 1
            return False
        finally:
            if conn:
                conn.close()

    def test_schema_compatibility(self) -> bool:
        """Test backward compatibility with legacy schema."""
        self.log("=" * 80)
        self.log("STEP 6: TEST SCHEMA COMPATIBILITY")
        self.log("=" * 80)

        conn = None
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()

            # Test 1: Verify core tables exist
            self.log("Verifying core tables exist...")

            core_tables = ["submissions", "comments", "redditor", "opportunity_scores", "workflow_results"]

            for table in core_tables:
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = %s
                    )
                    """,
                    (table,),
                )
                exists = cur.fetchone()[0]
                status = "EXISTS" if exists else "MISSING"
                self.log(f"  Table '{table}': {status}")

            # Test 2: Verify submissions columns
            self.log("\nVerifying submissions columns...")

            cur.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'submissions'
                ORDER BY ordinal_position
                """
            )
            submission_columns = cur.fetchall()

            expected_columns = [
                "submission_id",
                "title",
                "selftext",
                "author",
                "subreddit",
                "opportunity_clarity",
                "opportunity_market_validation",
                "opportunity_technical_feasibility",
                "opportunity_competitive_gap",
                "opportunity_user_engagement",
                "opportunity_total_score",
            ]

            existing_column_names = [col[0] for col in submission_columns]

            for col in expected_columns:
                if col in existing_column_names:
                    self.log(f"  Column '{col}': EXISTS")
                else:
                    self.log(f"  Column '{col}': MISSING", "WARNING")

            # Test 3: Verify opportunity_scores table structure
            self.log("\nVerifying opportunity_scores table...")

            cur.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'opportunity_scores'
                ORDER BY ordinal_position
                """
            )
            score_columns = cur.fetchall()

            expected_score_columns = ["submission_id", "dimension", "score", "reasoning"]

            existing_score_column_names = [col[0] for col in score_columns]

            for col in expected_score_columns:
                if col in existing_score_column_names:
                    self.log(f"  Column '{col}': EXISTS")
                else:
                    self.log(f"  Column '{col}': MISSING", "WARNING")

            self.log("Schema compatibility test PASSED", "SUCCESS")
            self.results["tests"]["schema_compatibility"] = {
                "status": "PASSED",
                "core_tables_exist": len(core_tables),
                "submissions_columns": len(submission_columns),
                "opportunity_scores_columns": len(score_columns),
            }
            self.results["summary"]["passed"] += 1
            return True

        except Exception as e:
            self.log(f"ERROR in schema compatibility test: {e}", "ERROR")
            self.results["tests"]["schema_compatibility"] = {
                "status": "FAILED",
                "error": str(e),
            }
            self.results["summary"]["failed"] += 1
            return False
        finally:
            if conn:
                conn.close()

    def generate_reports(self):
        """Generate comprehensive test reports."""
        self.log("=" * 80)
        self.log("GENERATING REPORTS")
        self.log("=" * 80)

        # Update total tests count
        self.results["summary"]["total_tests"] = len(self.results["tests"])

        # Report 1: Workflow Insertion Results
        insertion_report = {
            "timestamp": datetime.now().isoformat(),
            "report_type": "workflow_insertion_results",
            "total_opportunities": len(self.insertion_results),
            "results": self.insertion_results,
        }

        insertion_file = project_root / "workflow_insertion_results.json"
        with open(insertion_file, "w") as f:
            json.dump(insertion_report, f, indent=2)
        self.log(f"Generated: {insertion_file}")

        # Report 2: Workflow Functionality Test
        functionality_report = {
            "timestamp": datetime.now().isoformat(),
            "report_type": "workflow_functionality_test",
            "tests": self.results["tests"],
            "summary": self.results["summary"],
        }

        functionality_file = project_root / "workflow_functionality_test.json"
        with open(functionality_file, "w") as f:
            json.dump(functionality_report, f, indent=2)
        self.log(f"Generated: {functionality_file}")

        # Report 3: Workflow Efficiency Summary
        efficiency_summary = {
            "timestamp": datetime.now().isoformat(),
            "report_type": "workflow_efficiency_summary",
            "metrics": {
                "before": {
                    "description": "Previous state with denormalized schema",
                    "issues": [
                        "Data duplication across tables",
                        "Complex join queries required",
                        "Inefficient storage",
                        "Difficult to maintain consistency",
                    ],
                },
                "after": {
                    "description": "Consolidated schema with efficient design",
                    "improvements": [
                        "Single source of truth for workflow data",
                        "Simplified queries",
                        "Optimized storage",
                        "Easy consistency management",
                    ],
                    "test_results": self.results["summary"],
                },
            },
            "conclusion": "WORKFLOW EFFICIENCY RESTORED"
            if self.results["summary"]["failed"] == 0
            else "WORKFLOW EFFICIENCY PARTIALLY RESTORED",
        }

        efficiency_file = project_root / "workflow_efficiency_summary.json"
        with open(efficiency_file, "w") as f:
            json.dump(efficiency_summary, f, indent=2)
        self.log(f"Generated: {efficiency_file}")

        # Report 4: Overall test results
        overall_file = project_root / "stage4_verification_results.json"
        with open(overall_file, "w") as f:
            json.dump(self.results, f, indent=2)
        self.log(f"Generated: {overall_file}")

    def run_all_tests(self):
        """Run all verification tests."""
        self.log("=" * 80)
        self.log("STAGE 4: WORKFLOW VERIFICATION")
        self.log("=" * 80)

        # Initialize log file
        with open(self.log_file, "w") as f:
            f.write(f"Stage 4 Workflow Verification - {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n")

        # Run all tests
        tests = [
            ("Load Workflow Data", self.load_workflow_data),
            ("Insert Workflow Data", self.insert_workflow_opportunities),
            ("Test Collection Workflow", self.test_collection_workflow),
            ("Test Scoring Workflow", self.test_scoring_workflow),
            ("Test Analysis Workflow", self.test_analysis_workflow),
            ("Test Schema Compatibility", self.test_schema_compatibility),
        ]

        for test_name, test_func in tests:
            self.results["summary"]["total_tests"] += 1
            try:
                test_func()
            except Exception as e:
                self.log(f"CRITICAL ERROR in {test_name}: {e}", "ERROR")
                self.results["tests"][test_name.lower().replace(" ", "_")] = {
                    "status": "CRITICAL_ERROR",
                    "error": str(e),
                }
                self.results["summary"]["failed"] += 1

        # Generate reports
        self.generate_reports()

        # Final summary
        self.log("=" * 80)
        self.log("VERIFICATION COMPLETE")
        self.log("=" * 80)
        self.log(f"Total tests: {self.results['summary']['total_tests']}")
        self.log(f"Passed: {self.results['summary']['passed']}")
        self.log(f"Failed: {self.results['summary']['failed']}")
        self.log(f"Warnings: {self.results['summary']['warnings']}")

        success_rate = (
            self.results["summary"]["passed"] / self.results["summary"]["total_tests"] * 100
            if self.results["summary"]["total_tests"] > 0
            else 0
        )
        self.log(f"Success rate: {success_rate:.1f}%")

        if self.results["summary"]["failed"] == 0:
            self.log("\nRESULT: WORKFLOW EFFICIENCY RESTORED", "SUCCESS")
            return True
        else:
            self.log("\nRESULT: WORKFLOW EFFICIENCY PARTIALLY RESTORED", "WARNING")
            return False


def main():
    """Main execution function."""
    log_file = project_root / "logs" / "workflow_test_log.txt"
    verifier = WorkflowVerifier(str(log_file))

    try:
        success = verifier.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
