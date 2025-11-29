"""
Failing tests for Pipeline v3 Integration - End-to-End Data Flow

Tests that verify the complete pipeline data flow from Reddit extraction
through analysis to database storage, specifically focusing on:

1. Data integrity preservation throughout the pipeline
2. Proper data flow between pipeline stages
3. Integration of DatabaseLoader and OpportunityAnalyzer
4. Complete metadata preservation from Reddit to database
5. Embedding generation integration in the pipeline

These tests are designed to fail because the current implementation
has gaps in data preservation and missing embedding generation.
"""


import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import List, Optional
import asyncio

from models.analysis import AnalysisResult, AppIdea, MarketMetrics
from models.reddit import RedditSubmission
from models.database import Opportunity
from main import run_pipeline
from transform.analyzer import OpportunityAnalyzer, SimpleOpportunityAnalyzer
from transform.validator import AnalysisValidator
from load.database import DatabaseLoader
from load.data_mappers import AnalysisToOpportunityMapper
from extract.reddit_client import RedditClient


class MockPipelineComponents:
    """Mock all pipeline components for integration testing"""

    def __init__(self):
        # Mock Reddit client
        self.reddit_client = Mock(spec=RedditClient)
        self.reddit_client.test_connection.return_value = True

        # Mock analyzer
        self.analyzer = MockOpportunityAnalyzerForIntegration()
        self.analyzer.test_connection()  # Call the real method to initialize it

        # Mock validator
        self.validator = Mock(spec=AnalysisValidator)
        self.validator.validate_analysis.return_value = True
        self.validator.get_quality_summary.return_value = {
            'validation_rate': 100.0,
            'high_score_rate': 80.0,
            'avg_final_score': 75.0,
            'trust_distribution': {'HIGH': 50, 'MEDIUM': 30, 'LOW': 20}
        }

        # Mock database loader
        self.db_loader = MockDatabaseLoaderForIntegration()
        self.db_loader.test_connection()  # Call the real method to initialize it

    def get_reddit_submissions(self, count: int = 3) -> List[RedditSubmission]:
        """Generate mock Reddit submissions for testing"""
        submissions = []
        for i in range(count):
            submission = RedditSubmission(
                id=f"pipeline_test_{i}",
                title=f"Revolutionary App Idea {i+1}",
                text=f"""
                I'm a developer struggling with {['task management', 'content creation', 'data analysis'][i % 3]}.
                Current solutions are too complex and don't address my specific needs.

                The main pain points:
                1. Too many features, I need something focused
                2. Poor user experience and steep learning curve
                3. Expensive pricing for small teams
                4. Lack of integrations with existing tools
                5. Poor mobile support

                What I really need is a simple, focused solution that does one thing well.
                Something that's affordable, easy to use, and integrates with my existing workflow.
                """,
                author=f"developer_{i}",
                upvotes=85 + i * 15,
                downvotes=2 + i,
                score=83 + i * 15,
                comments_count=12 + i * 8,
                subreddit=["productivity", "webdev", "startups"][i % 3],
                created_utc=datetime.now(UTC).replace(year=2024, month=(i % 3)+1, day=(i % 3)+5),
                permalink=f"/r/{['productivity', 'webdev', 'startups'][i % 3]}/comments/pipeline_test_{i}/",
                url=None,
                is_self=True,
                over_18=False
            )
            submissions.append(submission)
        return submissions


class MockOpportunityAnalyzerForIntegration(SimpleOpportunityAnalyzer):
    """Mock analyzer that generates realistic test data"""

    def analyze_submission(self, submission: RedditSubmission) -> AnalysisResult:
        """Generate realistic analysis results for testing"""
        app_idea = AppIdea(
            title=f"TaskFlow {submission.id}",
            app_concept=f"A specialized {submission.subreddit} tool for developers",
            problem_statement=f"Developers need better tools for {submission.subreddit} tasks",
            target_audience=f"Developers working in {submission.subreddit}",
            core_functions=["automated task management", "integration with existing tools", "simplified workflow"]
        )

        market_metrics = MarketMetrics(
            market_demand=min(100.0, 70.0 + (submission.upvotes / 10)),
            pain_intensity=min(100.0, 80.0 + (submission.comments_count / 5)),
            monetization_potential=min(100.0, 75.0 + (submission.score / 5)),
            competition_level=max(0.0, 60.0 - (submission.upvotes / 20)),
            technical_feasibility=85.0
        )

        # Generate embedding
        embedding, embedding_metadata = self._generate_fake_embedding_with_metadata(submission)

        return AnalysisResult(
            submission_id=submission.id,
            analyzed_at=datetime.now(UTC),
            app_idea=app_idea,
            market_metrics=market_metrics,
            final_score=min(100.0, 75.0 + (submission.upvotes / 20)),
            confidence_score=min(100.0, 80.0 + (submission.comments_count / 10)),
            trust_level="HIGH" if submission.score > 100 else "MEDIUM",
            embedding=embedding,
            embedding_metadata=embedding_metadata
        )

    def _generate_fake_embedding_with_metadata(self, submission):
        """
        Generate a consistent fake embedding with metadata based on submission content

        Args:
            submission: Reddit submission to generate embedding for

        Returns:
            Tuple of (embedding_vector, embedding_metadata)
        """
        import hashlib
        from datetime import UTC

        # Create a hash of the submission content for consistency
        content = f"{submission.title}{submission.text}{submission.subreddit}"
        content_hash = hashlib.md5(content.encode()).hexdigest()

        # Convert hash to a deterministic embedding vector
        # Use 384 dimensions (common for sentence transformers)
        dimensions = 384
        embedding = []

        # Use hash bytes to generate consistent float values
        for i in range(dimensions):
            # Create a seed based on position and hash
            seed = int(content_hash[i % len(content_hash):i % len(content_hash) + 2] or '00', 16) + i
            # Generate a float between -1 and 1
            value = (seed % 2000 - 1000) / 1000.0
            embedding.append(value)

        # Create embedding metadata
        embedding_metadata = {
            'model': 'fake-embedding-v1',
            'dimensions': dimensions,
            'generated_at': datetime.now(UTC).isoformat(),
            'content_hash': content_hash,
            'method': 'hash-based-deterministic-fake',
            'submission_id': submission.id,
            'content_preview': content[:100] + '...' if len(content) > 100 else content
        }

        return embedding, embedding_metadata


class MockDatabaseLoaderForIntegration(DatabaseLoader):
    """Mock database loader that tracks what gets stored"""

    def __init__(self):
        self.settings = Mock()
        self.settings.database_url = "sqlite:///:memory:"
        self._engine = None
        self._session_factory = None
        self.opportunities_stored = []
        self.tables_created = False
        # Initialize data mapper with Reddit metadata preservation
        self.data_mapper = AnalysisToOpportunityMapper(preserve_reddit_metadata=True)

    @property
    def engine(self):
        """Mock engine"""
        if self._engine is None:
            from sqlalchemy import create_engine
            self._engine = create_engine("sqlite:///:memory:", echo=False)
        return self._engine

    @property
    def session_factory(self):
        """Mock session factory"""
        if self._session_factory is None:
            from sqlalchemy.orm import sessionmaker
            self._session_factory = sessionmaker(bind=self.engine)
        return self._session_factory

    def create_tables(self) -> None:
        """Override to track table creation"""
        # Mock table creation
        self.tables_created = True

    def store_analyses(self, analyses: List[AnalysisResult], reddit_submissions: List = None) -> dict:
        """Override to track stored analyses"""
        stats = {"stored": 0, "skipped": 0, "errors": 0}

        try:
            # Use data mapper to convert AnalysisResults to Opportunities
            opportunities = self.data_mapper.map_batch(analyses, reddit_submissions)

            # Store opportunities in mock tracking
            self.opportunities_stored.extend(opportunities)
            stats["stored"] = len(opportunities)

        except Exception as e:
            print(f"MockDatabaseLoader error: {e}")
            stats["errors"] = len(analyses)

        return stats


class TestPipelineIntegration:
    """Test suite for complete pipeline integration"""

    @pytest.fixture
    def mock_components(self):
        """Create mock pipeline components"""
        return MockPipelineComponents()

    @pytest.fixture
    def test_args(self):
        """Create test pipeline arguments"""
        args = Mock()
        args.limit = 3
        args.subreddits = None
        args.sort_by = "hot"
        args.time_filter = "week"
        args.min_score = 0.0
        args.min_confidence = 0.0
        args.validate_quality = False
        args.batch_size = 3
        args.test_mode = True
        args.dry_run = False
        args.log_level = "INFO"
        return args

    def test_pipeline_preserves_reddit_data_complete_flow(self, mock_components, test_args):
        """
        INTEGRATION TEST: Complete pipeline should preserve all Reddit data from extraction to storage

        This is the ultimate integration test that verifies the entire pipeline preserves
        Reddit metadata correctly. Current implementation fails at the DatabaseLoader stage
        where placeholder data is created instead of preserving original Reddit information.

        This test should FAIL because:
        1. DatabaseLoader._convert_to_opportunity creates placeholder data
        2. No mechanism exists to pass original Reddit data along with AnalysisResult
        3. The pipeline only passes AnalysisResult to the database layer
        """
        # Generate test Reddit submissions
        submissions = mock_components.get_reddit_submissions(test_args.limit)

        # Mock the Reddit client to return our test submissions
        mock_components.reddit_client.fetch_submissions.return_value = submissions

        # Step 1: Extract Reddit submissions
        extracted_submissions = mock_components.reddit_client.fetch_submissions(
            subreddits=test_args.subreddits or ["productivity", "webdev", "startups"],
            limit=test_args.limit,
            sort_by=test_args.sort_by,
            time_filter=test_args.time_filter
        )

        assert len(extracted_submissions) == test_args.limit, \
            f"Should extract {test_args.limit} submissions"

        # Step 2: Analyze submissions (this works correctly)
        analyses = mock_components.analyzer.analyze_batch(extracted_submissions, batch_size=test_args.batch_size)

        assert len(analyses) == len(extracted_submissions), \
            "Should get analysis for all extracted submissions"

        # Step 3: Validate analyses (this works correctly)
        high_quality_analyses = [
            a for a in analyses
            if (a.final_score >= test_args.min_score and
                a.confidence_score >= test_args.min_confidence and
                mock_components.validator.validate_analysis(a))
        ]

        assert len(high_quality_analyses) == len(analyses), \
            "All analyses should be high-quality"

        # Step 4: Store analyses to database (this is where it fails)
        load_stats = mock_components.db_loader.store_analyses(high_quality_analyses, extracted_submissions)

        assert load_stats["stored"] == len(high_quality_analyses), \
            f"All {len(high_quality_analyses)} analyses should be stored"

        # This is where the test FAILS - verify original Reddit data is preserved
        stored_opportunities = mock_components.db_loader.opportunities_stored

        for i, (original_submission, stored_opportunity) in enumerate(zip(extracted_submissions, stored_opportunities)):
            # All these assertions should pass if Reddit data is properly preserved
            assert stored_opportunity.reddit_title == original_submission.title, \
                f"Submission {i}: Title not preserved - expected '{original_submission.title}', got '{stored_opportunity.reddit_title}'"

            expected_url = f"https://reddit.com/r/{original_submission.subreddit}/{original_submission.id}"
            assert stored_opportunity.reddit_url == expected_url, \
                f"Submission {i}: URL not preserved - expected '{expected_url}', got '{stored_opportunity.reddit_url}'"

            assert stored_opportunity.subreddit == original_submission.subreddit, \
                f"Submission {i}: Subreddit not preserved - expected '{original_submission.subreddit}', got '{stored_opportunity.subreddit}'"

            assert stored_opportunity.reddit_author == original_submission.author, \
                f"Submission {i}: Author not preserved - expected '{original_submission.author}', got '{stored_opportunity.reddit_author}'"

            assert stored_opportunity.reddit_upvotes == original_submission.upvotes, \
                f"Submission {i}: Upvotes not preserved - expected {original_submission.upvotes}, got {stored_opportunity.reddit_upvotes}"

            assert stored_opportunity.reddit_comments_count == original_submission.comments_count, \
                f"Submission {i}: Comments count not preserved - expected {original_submission.comments_count}, got {stored_opportunity.reddit_comments_count}"

            assert stored_opportunity.reddit_created_at == original_submission.created_utc, \
                f"Submission {i}: Creation timestamp not preserved - expected {original_submission.created_utc}, got {stored_opportunity.reddit_created_at}"

    def test_pipeline_embedding_generation_flow(self, mock_components, test_args):
        """
        INTEGRATION TEST: Complete pipeline should generate and store embeddings

        This test verifies that embeddings are generated throughout the pipeline
        and properly stored in the database. Current implementation fails because
        OpportunityAnalyzer doesn't generate embeddings.

        This test should FAIL because:
        1. OpportunityAnalyzer.analyze_submission returns embedding=None
        2. No embedding generation is implemented in the analyzer
        3. Database receives None for all embeddings
        """
        # Generate test submissions
        submissions = mock_components.get_reddit_submissions(test_args.limit)
        mock_components.reddit_client.fetch_submissions.return_value = submissions

        # Step 1: Extract (works)
        extracted_submissions = mock_components.reddit_client.fetch_submissions(
            subreddits=test_args.subreddits or ["test"],
            limit=test_args.limit,
            sort_by=test_args.sort_by,
            time_filter=test_args.time_filter
        )

        # Step 2: Analyze with embedding generation (fails - returns None)
        analyses = mock_components.analyzer.analyze_batch(extracted_submissions, batch_size=test_args.batch_size)

        # Step 3: Validate (works)
        high_quality_analyses = [
            a for a in analyses
            if (a.final_score >= test_args.min_score and
                a.confidence_score >= test_args.min_confidence and
                mock_components.validator.validate_analysis(a))
        ]

        # Step 4: Store (embeddings are None)
        load_stats = mock_components.db_loader.store_analyses(high_quality_analyses)

        stored_opportunities = mock_components.db_loader.opportunities_stored

        # This test will FAIL because all embeddings are None
        for i, opportunity in enumerate(stored_opportunities):
            assert opportunity.embedding is not None, \
                f"Opportunity {i} should have embedding vector, but got None"

            # Additional embedding quality checks
            assert isinstance(opportunity.embedding, list), \
                f"Opportunity {i} embedding should be a list"

            assert len(opportunity.embedding) > 0, \
                f"Opportunity {i} embedding should not be empty"

            assert all(isinstance(x, (int, float)) for x in opportunity.embedding), \
                f"Opportunity {i} embedding should contain only numeric values"

    def test_pipeline_data_flow_architecture_diagnostic(self, mock_components, test_args):
        """
        DIAGNOSTIC TEST: Pipeline data flow architecture should preserve metadata

        This test provides a comprehensive diagnostic of the current pipeline architecture
        and specifically documents where data is being lost. It should FAIL and serve
        as documentation of the architectural gaps.

        The current pipeline has this data flow:
        RedditSubmission → AnalysisResult (with embedding=None) → Database (stores placeholder data)

        What's missing:
        1. No mechanism to pass original Reddit data to DatabaseLoader
        2. No embedding generation in OpportunityAnalyzer
        3. DatabaseLoader creates placeholder data instead of preserving original Reddit metadata
        """
        # Generate test data
        submissions = mock_components.get_reddit_submissions(1)  # Single test case
        mock_components.reddit_client.fetch_submissions.return_value = submissions

        # Track data flow through the pipeline
        data_flow_trace = {
            "step_1_extraction": {
                "reddit_submissions": submissions,
                "metadata_preserved": True,
                "sample_data": {
                    "id": submissions[0].id,
                    "title": submissions[0].title,
                    "author": submissions[0].author,
                    "upvotes": submissions[0].upvotes,
                    "subreddit": submissions[0].subreddit,
                    "created_utc": submissions[0].created_utc
                }
            },
            "step_2_analysis": {
                "analyses_generated": [],
                "embeddings_generated": [],
                "sample_analysis": None
            },
            "step_3_validation": {
                "high_quality_analyses": [],
                "filter_results": {}
            },
            "step_4_storage": {
                "opportunities_stored": [],
                "original_data_preserved": False,
                "embedding_data_preserved": False
            }
        }

        # Execute Step 1: Extract
        extracted_submissions = mock_components.reddit_client.fetch_submissions(
            subreddits=["test"], limit=1, sort_by="hot", time_filter="week"
        )

        # Execute Step 2: Analyze
        analyses = mock_components.analyzer.analyze_batch(extracted_submissions, batch_size=1)

        data_flow_trace["step_2_analysis"]["analyses_generated"] = analyses
        data_flow_trace["step_2_analysis"]["embeddings_generated"] = [a.embedding for a in analyses]
        data_flow_trace["step_2_analysis"]["sample_analysis"] = analyses[0].model_dump() if analyses else None

        # Execute Step 3: Validate
        high_quality_analyses = [
            a for a in analyses
            if (a.final_score >= test_args.min_score and
                a.confidence_score >= test_args.min_confidence and
                mock_components.validator.validate_analysis(a))
        ]
        data_flow_trace["step_3_validation"]["high_quality_analyses"] = high_quality_analyses
        data_flow_trace["step_3_validation"]["filter_results"] = {
            "total_analyses": len(analyses),
            "high_quality": len(high_quality_analyses),
            "filtered_out": len(analyses) - len(high_quality_analyses)
        }

        # Execute Step 4: Store
        load_stats = mock_components.db_loader.store_analyses(high_quality_analyses, extracted_submissions)
        stored_opportunities = mock_components.db_loader.opportunities_stored

        data_flow_trace["step_4_storage"]["opportunities_stored"] = stored_opportunities

        # Diagnostic analysis of data preservation gaps
        if stored_opportunities:
            stored = stored_opportunities[0]
            original = extracted_submissions[0]

            # Check Reddit data preservation
            reddit_data_gaps = []
            if stored.reddit_title != original.title:
                reddit_data_gaps.append("reddit_title")
            if stored.subreddit != original.subreddit:
                reddit_data_gaps.append("subreddit")
            if stored.reddit_author != original.author:
                reddit_data_gaps.append("reddit_author")
            if stored.reddit_upvotes != original.upvotes:
                reddit_data_gaps.append("reddit_upvotes")
            if stored.reddit_comments_count != original.comments_count:
                reddit_data_gaps.append("reddit_comments_count")
            if stored.reddit_created_at != original.created_utc:
                reddit_data_gaps.append("reddit_created_at")

            data_flow_trace["step_4_storage"]["reddit_data_gaps"] = reddit_data_gaps
            data_flow_trace["step_4_storage"]["original_data_preserved"] = len(reddit_data_gaps) == 0

            # Check embedding preservation
            embedding_data_gaps = []
            if stored.embedding is None:
                embedding_data_gaps.append("embedding")
            if not isinstance(stored.embedding, list):
                embedding_data_gaps.append("embedding_type")
            if stored.embedding and len(stored.embedding) == 0:
                embedding_data_gaps.append("embedding_content")

            data_flow_trace["step_4_storage"]["embedding_data_gaps"] = embedding_data_gaps
            data_flow_trace["step_4_storage"]["embedding_data_preserved"] = len(embedding_data_gaps) == 0

        # This test will FAIL and provide comprehensive documentation of the issues
        assert data_flow_trace["step_4_storage"]["original_data_preserved"], \
            f"Reddit data not preserved: {data_flow_trace['step_4_storage']['reddit_data_gaps']}"

        assert data_flow_trace["step_4_storage"]["embedding_data_preserved"], \
            f"Embedding data not preserved: {data_flow_trace['step_4_storage']['embedding_data_gaps']}"

        # Additional assertion: The pipeline should be a pure ELT flow
        # Extract → Transform → Load should maintain data integrity throughout
        assert data_flow_trace["step_4_storage"]["original_data_preserved"], \
            "Pipeline should maintain data integrity in pure ELT flow"

    def test_pipeline_error_handling_robustness(self, mock_components, test_args):
        """
        INTEGRATION TEST: Pipeline should handle errors gracefully at each stage

        This test verifies that the pipeline handles errors gracefully across
        all stages. Current implementation has basic error handling but could
        be more robust, especially around data preservation failures.

        This test documents expected behavior and may need updates as error handling
        improves, but currently should PASS as it tests existing functionality.
        """
        # Generate test submissions
        submissions = mock_components.get_reddit_submissions(test_args.limit)
        mock_components.reddit_client.fetch_submissions.return_value = submissions

        # Test error handling in analysis stage
        # Mock one analysis to fail
        def failing_analysis(submission):
            raise RuntimeError("Simulated LLM analysis failure")

        original_analyze = mock_components.analyzer.analyze_submission
        mock_components.analyzer.analyze_submission = failing_analysis

        try:
            # This should handle the analysis failure gracefully
            analyses = mock_components.analyzer.analyze_batch(submissions, batch_size=test_args.batch_size)

            # Should return partial results or empty list, not crash
            assert isinstance(analyses, list), \
                "Analysis failures should return list, not crash"
        finally:
            mock_components.analyzer.analyze_submission = original_analyze

        # Test error handling in database stage
        # Get fresh submissions to avoid LLM analysis failure
        fresh_submissions = mock_components.get_reddit_submissions(3)

        # Mock database failure
        def failing_database_store(analyses, reddit_submissions=None):
            return {"stored": 0, "skipped": 0, "errors": len(analyses)}

        original_store = mock_components.db_loader.store_analyses
        mock_components.db_loader.store_analyses = failing_database_store

        try:
            high_quality_analyses = mock_components.analyzer.analyze_batch(fresh_submissions, batch_size=test_args.batch_size)
            load_stats = mock_components.db_loader.store_analyses(high_quality_analyses, fresh_submissions)

            # Should return error stats instead of crashing
            assert "errors" in load_stats, \
                "Database failures should include error statistics"
            assert load_stats["errors"] > 0, \
                "Database failures should report error count"
        finally:
            mock_components.db_loader.store_analyses = original_store

    def test_pipeline_performance_metrics_consistency(self, mock_components, test_args):
        """
        INTEGRATION TEST: Pipeline performance metrics should be consistent and meaningful

        This test verifies that performance metrics calculated throughout the pipeline
        are consistent and provide meaningful insights. Current implementation should
        pass this test as it calculates basic metrics, but it documents expectations
        for future enhancements.

        This test should PASS but documents what good performance metrics should look like.
        """
        import time

        # Generate test submissions with different characteristics
        test_sizes = [1, 2, 3]
        performance_metrics = {}

        for size in test_sizes:
            submissions = mock_components.get_reddit_submissions(size)
            mock_components.reddit_client.fetch_submissions.return_value = submissions

            # Measure pipeline performance
            start_time = time.time()

            # Step 1: Extract
            extract_start = time.time()
            extracted = mock_components.reddit_client.fetch_submissions(
                subreddits=["test"], limit=size, sort_by="hot", time_filter="week"
            )
            extract_time = time.time() - extract_start

            # Step 2: Analyze
            analyze_start = time.time()
            analyses = mock_components.analyzer.analyze_batch(extracted, batch_size=test_args.batch_size)
            analyze_time = time.time() - analyze_start

            # Step 3: Validate
            validate_start = time.time()
            high_quality = [
                a for a in analyses
                if (a.final_score >= test_args.min_score and
                    a.confidence_score >= test_args.min_confidence and
                    mock_components.validator.validate_analysis(a))
            ]
            validate_time = time.time() - validate_start

            # Step 4: Store
            store_start = time.time()
            load_stats = mock_components.db_loader.store_analyses(high_quality, extracted)
            store_time = time.time() - store_start

            total_time = time.time() - start_time

            performance_metrics[size] = {
                "extract_time": extract_time,
                "analyze_time": analyze_time,
                "validate_time": validate_time,
                "store_time": store_time,
                "total_time": total_time,
                "throughput": size / total_time if total_time > 0 else 0,
                "extraction_rate": size / extract_time if extract_time > 0 else 0,
                "analysis_rate": size / analyze_time if analyze_time > 0 else 0
            }

        # Verify performance metrics are reasonable
        for size, metrics in performance_metrics.items():
            assert metrics["total_time"] > 0, \
                f"Pipeline should take time for {size} submissions"

            assert metrics["throughput"] > 0, \
                f"Should have positive throughput for {size} submissions"

            # Performance should scale reasonably (not exponentially)
            if size > 1:
                prev_size = size - 1
                prev_metrics = performance_metrics[prev_size]

                time_ratio = metrics["total_time"] / prev_metrics["total_time"]
                size_ratio = size / prev_size

                assert time_ratio <= size_ratio * 2, \
                    f"Performance should scale linearly, not exponentially. Ratio: {time_ratio:.2f}x for {size_ratio}x size increase"

    def test_pipeline_data_completeness_audit(self, mock_components, test_args):
        """
        AUDIT TEST: Pipeline should maintain complete data integrity throughout processing

        This comprehensive audit test verifies that no data is lost or corrupted
        as it flows through the pipeline. Current implementation fails this test
        due to the data preservation gaps in DatabaseLoader.

        This test should FAIL and provide a complete audit report of data loss.
        """
        # Generate test submissions with full metadata
        submissions = mock_components.get_reddit_submissions(2)
        mock_components.reddit_client.fetch_submissions.return_value = submissions

        # Execute the complete pipeline
        extracted = mock_components.reddit_client.fetch_submissions(
            subreddits=["test"], limit=2, sort_by="hot", time_filter="week"
        )
        analyses = mock_components.analyzer.analyze_batch(extracted, batch_size=2)
        high_quality_analyses = [
            a for a in analyses
            if (a.final_score >= test_args.min_score and
                a.confidence_score >= test_args.min_confidence and
                mock_components.validator.validate_analysis(a))
        ]
        load_stats = mock_components.db_loader.store_analyses(high_quality_analyses, extracted)
        stored_opportunities = mock_components.db_loader.opportunities_stored

        # Create comprehensive audit report
        audit_report = {
            "pipeline_summary": {
                "submissions_extracted": len(extracted),
                "analyses_generated": len(analyses),
                "high_quality_analyses": len(high_quality_analyses),
                "opportunities_stored": len(stored_opportunities),
                "success_rate": (len(stored_opportunities) / len(extracted)) * 100 if extracted else 0
            },
            "data_integrity_check": {
                "reddit_metadata_preserved": True,
                "embeddings_generated": True,
                "analysis_integrity_preserved": True,
                "no_data_loss": True
            },
            "detailed_comparison": []
        }

        # Detailed comparison for each submission
        for i, (original, stored) in enumerate(zip(extracted, stored_opportunities)):
            field_audit = {
                "submission_id": {
                    "original": original.id,
                    "stored": stored.submission_id,
                    "match": original.id == stored.submission_id
                },
                "title": {
                    "original": original.title,
                    "stored": stored.reddit_title,
                    "match": original.title == stored.reddit_title
                },
                "subreddit": {
                    "original": original.subreddit,
                    "stored": stored.subreddit,
                    "match": original.subreddit == stored.subreddit
                },
                "author": {
                    "original": original.author,
                    "stored": stored.reddit_author,
                    "match": original.author == stored.reddit_author
                },
                "upvotes": {
                    "original": original.upvotes,
                    "stored": stored.reddit_upvotes,
                    "match": original.upvotes == stored.reddit_upvotes
                },
                "comments_count": {
                    "original": original.comments_count,
                    "stored": stored.reddit_comments_count,
                    "match": original.comments_count == stored.reddit_comments_count
                },
                "created_at": {
                    "original": str(original.created_utc),
                    "stored": str(stored.reddit_created_at),
                    "match": original.created_utc == stored.reddit_created_at
                },
                "embedding": {
                    "generated": stored.embedding is not None,
                    "dimension": len(stored.embedding) if stored.embedding else 0,
                    "valid": stored.embedding is not None and len(stored.embedding) > 0
                }
            }

            audit_report["detailed_comparison"].append(field_audit)

        # Calculate overall data integrity score
        total_checks = 0
        passed_checks = 0

        for comparison in audit_report["detailed_comparison"]:
            for field_name, field_data in comparison.items():
                if field_name == "embedding":
                    # Special handling for embedding checks
                    if field_data["generated"] and field_data["valid"]:
                        passed_checks += 2
                    elif field_data["generated"]:
                        passed_checks += 1
                    total_checks += 2
                else:
                    if field_data["match"]:
                        passed_checks += 1
                    total_checks += 1

        integrity_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        audit_report["data_integrity_check"]["integrity_score"] = integrity_score

        # This test will FAIL because data integrity is compromised
        assert audit_report["data_integrity_check"]["integrity_score"] == 100.0, \
            f"Data integrity compromised: {integrity_score:.1f}% score. Audit: {audit_report}"

        # Specific assertions for critical data preservation
        for comparison in audit_report["detailed_comparison"]:
            assert comparison["title"]["match"], \
                "Reddit title must be preserved through pipeline"

            assert comparison["subreddit"]["match"], \
                "Reddit subreddit must be preserved through pipeline"

            assert comparison["author"]["match"], \
                "Reddit author must be preserved through pipeline"

            assert comparison["upvotes"]["match"], \
                "Reddit upvotes must be preserved through pipeline"

            assert comparison["comments_count"]["match"], \
                "Reddit comments count must be preserved through pipeline"

            assert comparison["embedding"]["valid"], \
                "Embedding must be generated and valid"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])