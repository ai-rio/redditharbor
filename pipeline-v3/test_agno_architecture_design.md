# AgnoOpportunityAnalyzer Test Architecture Design

## Overview

This document outlines the comprehensive test architecture for the AgnoOpportunityAnalyzer implementation, designed to support Test-Driven Development (TDD) for multi-agent systems while maintaining maintainability and scalability.

## 1. Test Structure

### Directory Structure

```
pipeline-v3/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Pytest configuration and shared fixtures
│   ├── pytest.ini                    # Pytest configuration
│   ├── .coveragerc                   # Coverage configuration
│   └── helpers/
│       ├── __init__.py
│       ├── base_test.py              # Base test classes
│       ├── mock_agno_agents.py       # Mock implementations
│       ├── test_data_factory.py      # Test data generation
│       └── assertion_helpers.py     # Custom assertions
│
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_agno_analyzer.py      # Core analyzer tests
│   │   ├── test_agent_specialists.py  # Individual agent tests
│   │   ├── test_response_parser.py   # Response parsing tests
│   │   ├── test_score_calculation.py # Score calculation tests
│   │   ├── test_field_mapping.py     # Field normalization tests
│   │   └── test_consensus_logic.py   # Multi-agent consensus tests
│
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_pipeline_v3.py       # Pipeline v3 integration
│   │   ├── test_database_integration.py # Database interaction tests
│   │   ├── test_agent_ops_integration.py # AgentOps integration tests
│   │   ├── test_supabase_client.py  # Supabase client tests
│   │   └── test_reddit_api_client.py # Reddit API client tests
│
│   ├── performance/
│   │   ├── __init__.py
│   │   ├── test_batch_processing.py  # Batch processing performance
│   │   ├── test_memory_usage.py      # Memory usage tests
│   │   ├── test_concurrency.py       # Concurrency tests
│   │   └── test_response_time.py     # Response time tests
│
│   ├── e2e/
│   │   ├── __init__.py
│   │   ├── test_complete_workflow.py  # End-to-end workflow tests
│   │   ├── test_multi_agent_sync.py  # Multi-agent synchronization tests
│   │   └── test_error_scenarios.py   # Error recovery tests
│
│   ├── fixtures/
│   │   ├── __init__.py
│   │   ├── reddit_submissions.json    # Sample Reddit submission data
│   │   ├── agent_responses.json      # Mock agent response data
│   │   ├── test_scenarios.yaml        # Test scenario definitions
│   │   └── performance_data.json     # Performance test datasets
│
│   └── utils/
│       ├── __init__.py
│       ├── test_runner.py            # Custom test runner
│       ├── data_generation.py         # Test data generation utilities
│       └── mocking_strategies.py     # Mock configuration helpers
```

### Test Naming Conventions

- **Unit Tests**: `test_<module_name>_<functionality>.py`
  - Example: `test_agno_analyzer_wtp_analysis.py`
- **Integration Tests**: `test_<integration_point>_<scenario>.py`
  - Example: `test_database_submission_insert.py`
- **Performance Tests**: `test_performance_<metric>_<condition>.py`
  - Example: `test_batch_processing_throughput.py`
- **E2E Tests**: `test_<workflow_name>_<flow>.py`
  - Example: `test_monetization_analysis_workflow.py`

### Fixture Organization

1. **Shared Fixtures** (`conftest.py`):
   - Mock Supabase client
   - Mock Reddit API client
   - Base analyzer instance
   - Common test data

2. **Module-Specific Fixtures**:
   - Reddit submission fixtures
   - Agent response fixtures
   - Database state fixtures
   - Configuration fixtures

3. **Dynamic Fixtures**:
   - Parameterized test data
   - Scenario-based fixtures
   - Performance test data generators

## 2. Test Data Management

### Test Reddit Submission Fixtures

Create a comprehensive set of test submissions covering various scenarios:

```python
# fixtures/reddit_submissions.json
{
    "submissions": {
        "high_wtp_b2b": {
            "id": "sub_001",
            "title": "Looking for CRM solution for 50-person team",
            "text": "We're currently using spreadsheets and need a proper CRM. Budget approved for $10k-15k. Need implementation by Q2.",
            "subreddit": "startups",
            "score": 45,
            "num_comments": 23,
            "author": "business_manager_123"
        },
        "low_wtp_b2c": {
            "id": "sub_002",
            "title": "NOT paying for another fitness app",
            "text": "Too many subscriptions already. Looking for free alternatives to MyFitnessPal that work offline.",
            "subreddit": "fitness",
            "score": 12,
            "num_comments": 8,
            "author": "fitness_enthusiast"
        },
        "mixed_segment": {
            "id": "sub_003",
            "title": "Project management for small team + personal use",
            "text": "Need a tool that works for both my team of 5 and personal projects. Monthly budget around $50.",
            "subreddit": "productivity",
            "score": 28,
            "num_comments": 15,
            "author": "freelancer_pro"
        }
    }
}
```

### Mock Agent Response Data

Create structured mock responses for testing agent outputs:

```python
# fixtures/agent_responses.json
{
    "agent_responses": {
        "wtp_agent": {
            "positive_sentiment": {
                "sentiment_toward_payment": "Positive",
                "willingness_to_pay_score": 85,
                "evidence": ["willing to pay", "budget approved"],
                "reasoning": "Strong positive sentiment with budget approval"
            },
            "negative_sentiment": {
                "sentiment_toward_payment": "Negative",
                "willingness_to_pay_score": 25,
                "evidence": ["not willing", "too expensive"],
                "reasoning": "Explicit unwillingness to pay"
            }
        },
        "segment_agent": {
            "b2b_classification": {
                "customer_segment": "B2B",
                "confidence": 0.9,
                "indicators": ["team", "budget", "implementation"],
                "segment_score": 95
            },
            "b2c_classification": {
                "customer_segment": "B2C",
                "confidence": 0.8,
                "indicators": ["personal", "subscription", "individual"],
                "segment_score": 85
            }
        }
    }
}
```

### Edge Case Test Scenarios

```python
# fixtures/test_scenarios.yaml
scenarios:
  - name: "empty_submission"
    data:
      title: ""
      text: ""
      subreddit: "test"
    expected:
      willingness_to_pay_score: 50
      customer_segment: "Unknown"
      confidence: 0.3

  - name: "malformed_json_response"
    data:
      raw_response: "{ invalid json }"
    expected:
      fallback_response_triggered: true

  - name: "network_timeout"
    conditions:
      simulate_timeout: true
    expected:
      error_handling: "graceful degradation"
      default_scores: true
```

### Performance Test Data Sets

```python
# fixtures/performance_data.json
{
    "performance_test_data": {
        "small_batch": {
            "size": 10,
            "avg_word_count": 150
        },
        "medium_batch": {
            "size": 100,
            "avg_word_count": 200
        },
        "large_batch": {
            "size": 1000,
            "avg_word_count": 180
        },
        "edge_cases": {
            "size": 50,
            "varied_lengths": [10, 500, 1000]
        }
    }
}
```

## 3. Testing Infrastructure

### Base Test Classes

```python
# tests/helpers/base_test.py
"""
Base test classes providing common functionality for Agno analyzer tests
"""

import pytest
from typing import Dict, Any, Optional
from unittest.mock import Mock, MagicMock
from dataclasses import asdict

from core.agents.monetization.agno_analyzer import (
    MonetizationAgnoAnalyzer,
    MonetizationAnalysis
)


class BaseAgnoTest:
    """Base class for all Agno analyzer tests"""

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client"""
        return Mock()

    @pytest.fixture
    def mock_agentops(self):
        """Mock AgentOps client"""
        return Mock()

    @pytest.fixture
    def mock_openrouter(self):
        """Mock OpenRouter API"""
        return Mock()

    @pytest.fixture
    def base_analyzer(self, mock_openrouter, mock_agentops):
        """Base analyzer instance with mocked dependencies"""
        return MonetizationAgnoAnalyzer(
            model="anthropic/claude-haiku-4.5",
            agentops_api_key="test_key"
        )

    def assert_monetization_analysis_valid(self, analysis: MonetizationAnalysis):
        """Assert that a MonetizationAnalysis object is valid"""
        assert isinstance(analysis, MonetizationAnalysis)
        assert 0 <= analysis.willingness_to_pay_score <= 100
        assert 0 <= analysis.market_segment_score <= 100
        assert 0 <= analysis.price_sensitivity_score <= 100
        assert 0 <= analysis.revenue_potential_score <= 100
        assert 0 <= analysis.llm_monetization_score <= 100
        assert 0 <= analysis.confidence <= 1
        assert isinstance(analysis.customer_segment, str)
        assert isinstance(analysis.mentioned_price_points, list)
        assert isinstance(analysis.payment_friction_indicators, list)


class MockAgentResponse:
    """Helper class for creating mock agent responses"""

    @staticmethod
    def create_wtp_response(score: int, sentiment: str, evidence: list = None) -> Dict[str, Any]:
        return {
            "sentiment_toward_payment": sentiment,
            "willingness_to_pay_score": score,
            "evidence": evidence or ["test evidence"],
            "reasoning": "Test reasoning for WTP"
        }

    @staticmethod
    def create_segment_response(segment: str, confidence: float) -> Dict[str, Any]:
        return {
            "customer_segment": segment,
            "confidence": confidence,
            "indicators": ["test indicator"],
            "segment_score": int(confidence * 100)
        }

    @staticmethod
    def create_price_response(prices: list) -> Dict[str, Any]:
        return {
            "mentioned_price_points": [
                {"price": price, "context": "test context"}
                for price in prices
            ],
            "budget_ceiling": "$100/month",
            "pricing_model": "Subscription"
        }

    @staticmethod
    def create_behavior_response(spending: str) -> Dict[str, Any]:
        return {
            "current_spending": spending,
            "switching_willingness": "High",
            "spending_evidence": ["test evidence"],
            "behavior_score": 75
        }
```

### Mock Implementations for Agno Agents

```python
# tests/helpers/mock_agno_agents.py
"""
Mock implementations of Agno agents for testing
"""

from unittest.mock import Mock
from typing import Dict, Any


class MockWTPAgent:
    """Mock Willingness to Pay Agent"""

    def __init__(self, response_data: Dict[str, Any] = None):
        self.response_data = response_data or {
            "sentiment_toward_payment": "Positive",
            "willingness_to_pay_score": 75,
            "evidence": ["test evidence"],
            "reasoning": "Test reasoning"
        }

    def run(self, prompt: str) -> str:
        """Mock run method"""
        return str(self.response_data)


class MockSegmentAgent:
    """Mock Market Segment Agent"""

    def __init__(self, response_data: Dict[str, Any] = None):
        self.response_data = response_data or {
            "customer_segment": "B2B",
            "confidence": 0.8,
            "indicators": ["business", "team"],
            "segment_score": 80
        }

    def run(self, prompt: str) -> str:
        """Mock run method"""
        return str(self.response_data)


class MockPriceAgent:
    """Mock Price Point Agent"""

    def __init__(self, response_data: Dict[str, Any] = None):
        self.response_data = response_data or {
            "mentioned_price_points": [
                {"price": "$100/month", "context": "budget"}
            ],
            "budget_ceiling": "$150/month",
            "pricing_model": "Subscription"
        }

    def run(self, prompt: str) -> str:
        """Mock run method"""
        return str(self.response_data)


class MockBehaviorAgent:
    """Mock Payment Behavior Agent"""

    def __init__(self, response_data: Dict[str, Any] = None):
        self.response_data = response_data or {
            "current_spending": "$200/month on Salesforce",
            "switching_willingness": "Medium",
            "spending_evidence": ["current pain points"],
            "behavior_score": 65
        }

    def run(self, prompt: str) -> str:
        """Mock run method"""
        return str(self.response_data)


class MockAgnoTeam:
    """Mock Agno Team for coordinated testing"""

    def __init__(self, agents: Dict[str, Mock] = None):
        self.agents = agents or {
            "wtp": MockWTPAgent(),
            "segment": MockSegmentAgent(),
            "price": MockPriceAgent(),
            "behavior": MockBehaviorAgent()
        }

    def run_agent(self, agent_name: str, prompt: str) -> str:
        """Run a specific mock agent"""
        if agent_name in self.agents:
            return self.agents[agent_name].run(prompt)
        raise ValueError(f"Unknown agent: {agent_name}")
```

### Test Utilities for Synthesis Validation

```python
# tests/helpers/assertion_helpers.py
"""
Custom assertion helpers for Agno analysis validation
"""

import json
from typing import Dict, Any, List
from dataclasses import asdict

from core.agents.monetization.agno_analyzer import MonetizationAnalysis


class AgnoAnalysisAssertions:
    """Custom assertions for Agno analysis results"""

    @staticmethod
    def assert_valid_json_response(response: str):
        """Assert that response is valid JSON"""
        try:
            parsed = json.loads(response)
            assert isinstance(parsed, dict)
            return parsed
        except json.JSONDecodeError:
            pytest.fail(f"Invalid JSON response: {response}")

    @staticmethod
    def assert_field_mapping(mapped_data: Dict[str, Any], expected_fields: List[str]):
        """Assert that all expected fields are present in mapped data"""
        for field in expected_fields:
            assert field in mapped_data, f"Missing expected field: {field}"

    @staticmethod
    def assert_score_ranges(analysis: MonetizationAnalysis):
        """Assert that all scores are within valid ranges"""
        scores_to_check = [
            "willingness_to_pay_score",
            "market_segment_score",
            "price_sensitivity_score",
            "revenue_potential_score",
            "llm_monetization_score"
        ]

        for score_field in scores_to_check:
            score = getattr(analysis, score_field)
            assert 0 <= score <= 100, (
                f"{score_field} {score} is out of range [0, 100]"
            )

    @staticmethod
    def assert_consensus_metadata(consensus_data: Dict[str, Any]):
        """Assert consensus metadata structure"""
        required_fields = [
            "agent_count",
            "agreement_level",
            "outliers_detected"
        ]

        for field in required_fields:
            assert field in consensus_data, f"Missing consensus metadata: {field}"

        assert consensus_data["agent_count"] > 0
        assert consensus_data["agreement_level"] in [
            "high", "medium", "low", "very_low", "single_agent", "unknown"
        ]
        assert consensus_data["outliers_detected"] >= 0

    @staticmethod
    def assert_friction_indicators(friction_indicators: List[str]):
        """Assert friction indicators are valid"""
        valid_indicators = [
            "price_objection",
            "budget_constraint",
            "subscription_fatigue",
            "free_alternative_preference",
            "switching_cost_concern",
            "none_detected"
        ]

        for indicator in friction_indicators:
            assert indicator in valid_indicators, (
                f"Invalid friction indicator: {indicator}"
            )

    @staticmethod
    def assert_urgency_levels(urgency: str):
        """Assert urgency level is valid"""
        valid_levels = ["Critical", "High", "Medium", "Low"]
        assert urgency in valid_levels, f"Invalid urgency level: {urgency}"

    @staticmethod
    def assert_customer_segment(segment: str):
        """Assert customer segment is valid"""
        valid_segments = ["B2B", "B2C", "Mixed", "Unknown"]
        assert segment in valid_segments, f"Invalid customer segment: {segment}"
```

## 4. Integration Test Framework

### Pipeline v3 Integration Test Setup

```python
# tests/integration/conftest.py
"""
Integration test configuration for pipeline v3
"""

import pytest
from unittest.mock import Mock, patch
import asyncio
from typing import Dict, Any

from scripts.core.batch_opportunity_scoring import process_batch
from scripts.core.opp_agent import OpportunityAnalyzerAgent


@pytest.fixture
def mock_supabase_integration():
    """Mock Supabase client for integration tests"""
    with patch('scripts.core.batch_opportunity_scoring.supabase') as mock:
        yield mock


@pytest.fixture
def mock_opportunity_agent():
    """Mock opportunity analyzer agent"""
    with patch('scripts.core.opp_agent.OpportunityAnalyzerAgent') as mock:
        agent = Mock(spec=OpportunityAnalyzerAgent)
        agent.analyze_opportunity.return_value = {
            'final_score': 75.0,
            'monetization_potential': 80.0,
            'problem_alignment': 85.0
        }
        yield agent


@pytest.fixture
def test_batch_data():
    """Test batch data for integration testing"""
    return [
        {
            'submission_id': 'test_001',
            'title': 'CRM for small business',
            'text': 'Need a CRM solution for 10-person team. Budget $5k.',
            'subreddit': 'startups',
            'author': 'business_owner',
            'reddit_score': 45,
            'num_comments': 12
        },
        {
            'submission_id': 'test_002',
            'title': 'Free project management tool',
            'text': 'Looking for free alternatives to Asana for personal use.',
            'subreddit': 'productivity',
            'author': 'freelancer',
            'reddit_score': 23,
            'num_comments': 8
        }
    ]


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing"""
    env_vars = {
        'MONETIZATION_LLM_ENABLED': 'true',
        'MONETIZATION_LLM_THRESHOLD': '50.0',
        'OPENROUTER_API_KEY': 'test_api_key',
        'AGENTOPS_API_KEY': 'test_agentops_key'
    }

    with patch.dict('os.environ', env_vars):
        yield


@pytest.fixture
async def async_test_context():
    """Async test context for async test functions"""
    return {
        'loop': asyncio.get_event_loop(),
        'results': []
    }
```

### Database Test Fixtures

```python
# tests/integration/database_fixtures.py
"""
Database fixtures for integration testing
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta


@pytest.fixture
def mock_database_state():
    """Mock database state for testing"""
    return {
        'business_concepts': [
            {
                'id': 1,
                'concept_name': 'CRM Solutions',
                'has_agno_analysis': True,
                'last_analyzed': datetime.now() - timedelta(days=1),
                'wtp_score_avg': 75.0
            },
            {
                'id': 2,
                'concept_name': 'Project Management',
                'has_agno_analysis': False,
                'last_analyzed': None,
                'wtp_score_avg': None
            }
        ],
        'opportunities_unified': [
            {
                'submission_id': 'sub_001',
                'business_concept_id': 1,
                'title': 'CRM needed for growing team',
                'text': 'We need a CRM as we scale from 10 to 50 employees',
                'subreddit': 'startups'
            },
            {
                'submission_id': 'sub_002',
                'business_concept_id': 2,
                'title': 'Project management tool search',
                'text': 'Looking for tools to manage remote team projects',
                'subreddit': 'remoteWork'
            }
        ]
    }


@pytest.fixture
def mock_agno_analysis_results():
    """Mock Agno analysis results for database storage"""
    return {
        'willingness_to_pay_score': 85,
        'customer_segment': 'B2B',
        'payment_sentiment': 'Positive',
        'urgency_level': 'High',
        'mentioned_price_points': ['$5000', '$100/month'],
        'payment_friction_indicators': ['none_detected'],
        'llm_monetization_score': 82.5,
        'confidence': 0.9,
        'reasoning': 'Strong B2B signals with clear budget and timeline',
        'model_used': 'anthropic/claude-haiku-4.5'
    }
```

### AgentOps Mock Configuration

```python
# tests/integration/agentops_mock.py
"""
AgentOps mocking utilities for integration testing
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any, Optional


class MockAgentOps:
    """Mock AgentOps for testing cost tracking"""

    def __init__(self):
        self.events = []
        self.traces = []
        self.current_trace = None

    def start_trace(self, name: str, tags: Optional[list] = None) -> str:
        """Mock start trace"""
        trace_id = f"trace_{name}_{len(self.traces)}"
        self.current_trace = trace_id
        self.traces.append({
            'id': trace_id,
            'name': name,
            'tags': tags or [],
            'start_time': 'test_time',
            'status': 'running'
        })
        return trace_id

    def end_trace(self, trace_id: str, status: str = "Success"):
        """Mock end trace"""
        if self.current_trace == trace_id:
            self.current_trace = None

        for trace in self.traces:
            if trace['id'] == trace_id:
                trace['status'] = status
                trace['end_time'] = 'test_time'
                break

    def record(self, event_name: str, data: Dict[str, Any]):
        """Mock record event"""
        self.events.append({
            'event_name': event_name,
            'data': data,
            'timestamp': 'test_time'
        })

    def Event(self, event_name: str, data: Dict[str, Any]):
        """Mock AgentOps Event method (v4 compatibility)"""
        self.record(event_name, data)


@pytest.fixture
def mock_agentops_instance():
    """Mock AgentOps instance"""
    return MockAgentOps()


@pytest.fixture
def mock_agentops_integration():
    """Mock AgentOps integration"""
    with patch('agentops.init') as mock_init, \
         patch('agentops.start_trace') as mock_start_trace, \
         patch('agentops.end_trace') as mock_end_trace, \
         patch('agentops.Event') as mock_event:

        # Setup mocks
        mock_init.return_value = None
        mock_start_trace.return_value = "test_trace_id"
        mock_end_trace.return_value = None
        mock_event.return_value = None

        # Create mock instance
        mock_instance = MockAgentOps()
        mock_start_trace.side_effect = mock_instance.start_trace
        mock_end_trace.side_effect = mock_instance.end_trace
        mock_event.side_effect = mock_instance.Event

        yield {
            'init': mock_init,
            'start_trace': mock_start_trace,
            'end_trace': mock_end_trace,
            'Event': mock_event,
            'instance': mock_instance
        }
```

### End-to-End Test Scenarios

```python
# tests/e2e/test_complete_workflow.py
"""
End-to-end tests for complete Agno analysis workflow
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from typing import Dict, Any

from scripts.core.batch_opportunity_scoring import process_batch
from core.agents.monetization.agno_analyzer import MonetizationAgnoAnalyzer


class TestCompleteWorkflow:
    """End-to-end workflow tests"""

    @pytest.mark.asyncio
    async def test_end_to_end_analysis_workflow(self, mock_supabase_integration,
                                               mock_opportunity_agent,
                                               test_batch_data,
                                               mock_env_vars):
        """Test complete workflow from submission to analysis"""

        # Mock successful Agno analysis
        mock_supabase_integration.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
            # First call: check for duplicates - return empty (unique)
            Mock(data=[]),
            # Second call: get concept details
            Mock(data=[{"has_agno_analysis": False}])
        ]

        # Mock successful analysis
        mock_opportunity_agent.analyze_opportunity.return_value = {
            'final_score': 78.5,
            'monetization_potential': 82.0,
            'problem_alignment': 85.0,
            'agno_enhanced': True
        }

        # Process batch
        results = await process_batch(
            submissions=test_batch_data,
            agent=mock_opportunity_agent,
            batch_number=1,
            ai_profile_threshold=50.0
        )

        # Verify results
        assert len(results) == 2
        for result in results:
            assert result['processed'] is True
            assert result['analysis_result'] is not None
            assert result['final_score'] >= 50.0

    def test_error_handling_workflow(self, mock_supabase_integration,
                                   mock_opportunity_agent,
                                   test_batch_data):
        """Test error handling in complete workflow"""

        # Mock database error
        mock_supabase_integration.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Database connection failed")

        # Process should handle errors gracefully
        with pytest.raises(Exception):
            process_batch(
                submissions=test_batch_data,
                agent=mock_opportunity_agent,
                batch_number=1,
                ai_profile_threshold=50.0
            )

    def test_agentops_tracking_workflow(self, mock_agentops_integration,
                                       mock_supabase_integration,
                                       test_batch_data):
        """Test AgentOps tracking in complete workflow"""

        # Mock successful database operations
        mock_supabase_integration.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(data=[])

        # Process batch with AgentOps tracking
        results = process_batch(
            submissions=test_batch_data,
            agent=mock_opportunity_agent,
            batch_number=1,
            ai_profile_threshold=50.0
        )

        # Verify AgentOps events were recorded
        assert len(mock_agentops_integration['instance'].events) > 0
        assert len(mock_agentops_integration['instance'].traces) > 0
```

## 5. Performance Test Framework

### Performance Test Configuration

```python
# tests/performance/conftest.py
"""
Performance test configuration
"""

import pytest
import time
import asyncio
from typing import List, Dict, Any
from unittest.mock import Mock


@pytest.fixture
def performance_metrics():
    """Performance metrics collector"""
    return {
        'start_time': None,
        'end_time': None,
        'memory_usage': [],
        'response_times': [],
        'throughput': 0
    }


@pytest.fixture
def large_test_batch():
    """Large batch for performance testing"""
    return [
        {
            'submission_id': f'sub_{i:04d}',
            'title': f'Performance test submission {i}',
            'text': 'This is a test submission for performance testing. ' * 10,
            'subreddit': 'startups',
            'author': f'user_{i % 100}',
            'reddit_score': i % 100,
            'num_comments': i % 50
        }
        for i in range(1000)
    ]


@pytest.fixture
def stress_test_scenarios():
    """Stress test scenarios"""
    return [
        {'batch_size': 10, 'concurrent_requests': 1},
        {'batch_size': 100, 'concurrent_requests': 5},
        {'batch_size': 500, 'concurrent_requests': 10},
        {'batch_size': 1000, 'concurrent_requests': 20}
    ]


@pytest.fixture
async def performance_test_context(performance_metrics):
    """Performance test context"""
    performance_metrics['start_time'] = time.time()
    yield performance_metrics
    performance_metrics['end_time'] = time.time()
    performance_metrics['throughput'] = (
        len(performance_metrics['response_times']) /
        (performance_metrics['end_time'] - performance_metrics['start_time'])
    )
```

### Performance Test Cases

```python
# tests/performance/test_batch_processing.py
"""
Batch processing performance tests
"""

import pytest
import asyncio
import time
from typing import List

from scripts.core.batch_opportunity_scoring import process_batch


class TestBatchProcessingPerformance:
    """Performance tests for batch processing"""

    @pytest.mark.performance
    @pytest.mark.parametrize("batch_size", [10, 100, 500, 1000])
    def test_batch_processing_throughput(self, batch_size, large_test_batch,
                                        performance_metrics):
        """Test throughput for different batch sizes"""

        # Select subset of test data
        test_batch = large_test_batch[:batch_size]

        # Mock dependencies
        with patch('scripts.core.batch_opportunity_scoring.supabase') as mock_supabase, \
             patch('scripts.core.batch_opportunity_scoring.OpportunityAnalyzerAgent') as mock_agent:

            # Setup mocks
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(data=[])
            mock_agent.return_value.analyze_opportunity.return_value = {
                'final_score': 75.0,
                'monetization_potential': 80.0,
                'problem_alignment': 85.0
            }

            # Measure processing time
            start_time = time.time()

            # Process batch
            results = process_batch(
                submissions=test_batch,
                agent=mock_agent.return_value,
                batch_number=1,
                ai_profile_threshold=50.0
            )

            end_time = time.time()

            # Calculate metrics
            processing_time = end_time - start_time
            throughput = len(results) / processing_time

            # Record metrics
            performance_metrics['response_times'].append(processing_time)

            # Assert performance requirements
            assert throughput >= 5.0, f"Throughput {throughput} < 5.0 submissions/sec"
            assert processing_time <= batch_size * 0.1, (
                f"Processing time {processing_time}s > {batch_size * 0.1}s"
            )

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_batch_processing(self, stress_test_scenarios,
                                            performance_metrics):
        """Test performance under concurrent load"""

        for scenario in stress_test_scenarios:
            batch_size = scenario['batch_size']
            concurrent_requests = scenario['concurrent_requests']

            # Prepare test data
            test_batch = [
                {
                    'submission_id': f'sub_{i:04d}',
                    'title': f'Concurrent test submission {i}',
                    'text': 'Concurrent test text. ' * 5,
                    'subreddit': 'startups',
                    'author': f'user_{i % 100}',
                    'reddit_score': i % 100,
                    'num_comments': i % 50
                }
                for i in range(batch_size)
            ]

            # Mock dependencies
            with patch('scripts.core.batch_opportunity_scoring.supabase') as mock_supabase, \
                 patch('scripts.core.batch_opportunity_scoring.OpportunityAnalyzerAgent') as mock_agent:

                mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(data=[])
                mock_agent.return_value.analyze_opportunity.return_value = {
                    'final_score': 75.0,
                    'monetization_potential': 80.0,
                    'problem_alignment': 85.0
                }

                # Measure concurrent processing time
                start_time = time.time()

                # Process batches concurrently
                tasks = []
                for i in range(concurrent_requests):
                    task = asyncio.create_task(
                        process_batch(
                            submissions=test_batch,
                            agent=mock_agent.return_value,
                            batch_number=i + 1,
                            ai_profile_threshold=50.0
                        )
                    )
                    tasks.append(task)

                results = await asyncio.gather(*tasks)

                end_time = time.time()

                # Calculate metrics
                total_submissions = sum(len(r) for r in results)
                total_time = end_time - start_time
                throughput = total_submissions / total_time

                # Record metrics
                performance_metrics['response_times'].append(total_time)

                # Assert performance requirements
                assert throughput >= concurrent_requests * 3.0, (
                    f"Concurrent throughput {throughput} < {concurrent_requests * 3.0} submissions/sec"
                )
                assert total_time <= concurrent_requests * 2.0, (
                    f"Concurrent processing time {total_time}s > {concurrent_requests * 2.0}s"
                )
```

### Memory Usage Tests

```python
# tests/performance/test_memory_usage.py
"""
Memory usage performance tests
"""

import pytest
import psutil
import os
from typing import Dict, Any
from unittest.mock import Mock


class TestMemoryUsage:
    """Memory usage performance tests"""

    @pytest.fixture
    def memory_monitor(self):
        """Memory usage monitor"""
        process = psutil.Process(os.getpid())
        return process

    def test_memory_usage_growth(self, large_test_batch, memory_monitor):
        """Test that memory usage grows predictably with batch size"""

        initial_memory = memory_monitor.memory_info().rss / 1024 / 1024  # MB

        # Mock dependencies
        with patch('scripts.core.batch_opportunity_scoring.supabase') as mock_supabase, \
             patch('scripts.core.batch_opportunity_scoring.OpportunityAnalyzerAgent') as mock_agent:

            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(data=[])
            mock_agent.return_value.analyze_opportunity.return_value = {
                'final_score': 75.0,
                'monetization_potential': 80.0,
                'problem_alignment': 85.0
            }

            # Process batches of increasing size
            batch_sizes = [10, 50, 100, 500]
            memory_usage = []

            for batch_size in batch_sizes:
                test_batch = large_test_batch[:batch_size]

                # Process batch
                process_batch(
                    submissions=test_batch,
                    agent=mock_agent.return_value,
                    batch_number=1,
                    ai_profile_threshold=50.0
                )

                # Measure memory
                current_memory = memory_monitor.memory_info().rss / 1024 / 1024
                memory_usage.append(current_memory - initial_memory)

            # Assert memory growth is linear or sub-linear
            # Last memory increase should not be more than 5x first increase
            assert memory_usage[-1] <= memory_usage[0] * 5, (
                f"Memory growth too steep: {memory_usage[-1]}MB vs {memory_usage[0]}MB"
            )

            # Average memory per submission should be reasonable
            avg_memory_per_submission = memory_usage[-1] / batch_sizes[-1]
            assert avg_memory_per_submission <= 1.0, (
                f"Memory per submission too high: {avg_memory_per_submission}MB"
            )
```

## 6. Coverage Configuration

### .coveragerc Configuration

```ini
# .coveragerc
[run]
source = pipeline-v3/core
omit =
    */venv/*
    */__pycache__/*
    */migrations/*
    */tests/*
    */docs/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:

[html]
directory = htmlcov

[xml]
output = coverage.xml

[json]
output = coverage.json
```

### pytest.ini Configuration

```ini
# pytest.ini
[pytest]
minversion = 6.0
addopts =
    -v
    --tb=short
    --strict-markers
    --strict-config
    --cov=pipeline-v3/core
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml
    --cov-fail-under=80
    --asyncio-mode=auto

markers =
    unit: Unit tests for core functionality
    integration: Integration tests with external dependencies
    performance: Performance tests
    e2e: End-to-end tests
    mock: Tests using mocks
    slow: Tests that run slowly

testpaths = tests

python_files = test_*.py
python_classes = Test*
python_functions = test_*

asyncio_mode = auto
```

## 7. TDD Workflow Support

### Test Generation Templates

```python
# tests/utils/tdd_templates.py
"""
TDD template generator for creating failing tests first
"""

from typing import Dict, Any, List
import json


class TDDTestGenerator:
    """Generate TDD-compliant test templates"""

    @staticmethod
    def generate_failing_test(module_name: str, function_name: str,
                           description: str, input_params: Dict[str, Any],
                           expected_output: Any) -> str:
        """Generate a failing test following TDD principles"""

        template = f'''
"""Failing test for {module_name}.{function_name} - TDD"""

import pytest
from unittest.mock import Mock, patch

# Add project root to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from {module_name} import {function_name}


class Test{function_name.title().replace('_', '')}:
    """Test suite for {function_name} following TDD"""

    def test_{function_name}_{description.replace(' ', '_').lower()}:
        """
        Test: {description}

        Expected: {json.dumps(expected_output, indent=2)}
        """
        # Setup test data
        test_input = {json.dumps(input_params, indent=8)}

        # Mock dependencies
        with patch('module_name.dependency') as mock_dep:
            mock_dep.return_value = mock_value

            # This test should fail initially
            # We write the test first, then implement the function

            # TODO: Implement test assertion
            # result = {function_name}(**test_input)
            # assert result == {json.dumps(expected_output)}

            # For now, explicitly fail to enforce TDD
            pytest.fail("Test not implemented - TDD red state")
'''

        return template

    @staticmethod
    def generate_unit_test_template(agent_name: str, method_name: str,
                                  test_cases: List[Dict[str, Any]]) -> str:
        """Generate unit test template for agent methods"""

        template = f'''
"""Unit tests for {agent_name}.{method_name} - TDD"""

import pytest
from unittest.mock import Mock, patch

from core.agents.monetization.agno_analyzer import {agent_name}
from tests.helpers.mock_agno_agents import Mock{agent_name}


class Test{agent_name.replace('Agent', '')}Unit:
    """Unit tests for {agent_name} following TDD"""
'''

        for i, test_case in enumerate(test_cases):
            template += f'''

    @pytest.mark.unit
    def test_{method_name}_case_{i+1}_{test_case['name'].replace(' ', '_').lower()}(
        self, mock_openrouter, mock_agentops
    ):
        """
        Test {method_name} - {test_case['description']}

        Input: {json.dumps(test_case['input'], indent=12)}
        Expected: {json.dumps(test_case['expected'], indent=12)}
        """
        # Setup
        agent = {agent_name}(
            model="test_model",
            api_key="test_key",
            base_url="test_url"
        )

        # Mock agent response
        agent.run = Mock(return_value={json.dumps(test_case['mock_response'])})

        # Execute (should fail initially)
        result = agent.{method_name}(**test_case['input'])

        # Verify (will fail until implementation)
        assert result == {json.dumps(test_case['expected'])}

        # TODO: Implement the actual method and remove this failure
        pytest.fail("Test not implemented - waiting for green state")
'''

        return template
```

### Continuous Integration Setup

```yaml
# .github/workflows/test-agno-integration.yml
name: Agno Integration Tests

on:
  push:
    branches: [ develop, feature/* ]
  pull_request:
    branches: [ develop, feature/* ]

jobs:
  test-agno-architecture:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: supabase/postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 54322:5432

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r pipeline-v3/requirements.txt
        pip install pytest pytest-asyncio pytest-cov pytest-mock
        pip install pytest-benchmark pytest-xdist

    - name: Run unit tests
      run: |
        pytest pipeline-v3/tests/unit/ -v --cov=core.agents.monetization.agno_analyzer

    - name: Run integration tests
      run: |
        pytest pipeline-v3/tests/integration/ -v --cov=core.agents.monetization.agno_analyzer

    - name: Run performance tests
      run: |
        pytest pipeline-v3/tests/performance/ -v --benchmark-only

    - name: Run E2E tests
      run: |
        pytest pipeline-v3/tests/e2e/ -v

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./pipeline-v3/coverage.xml
        flags: unittests
        name: codecov-umbrella

    - name: Upload benchmark results
      uses: benchmark-action/github-action-benchmark@v1
      with:
        tool: 'pytest'
        output-file-path: 'pipeline-v3/tests/performance/benchmark_results.json'
```

This comprehensive test architecture provides:

1. **Modular Structure**: Clear separation of concerns with dedicated directories for different test types
2. **TDD Support**: Templates for generating failing tests first
3. **Comprehensive Coverage**: Unit, integration, performance, and E2E tests
4. **Mock Strategies**: Flexible mocking for external dependencies
5. **Performance Monitoring**: Built-in performance benchmarks and memory usage tracking
6. **CI/CD Integration**: Ready-to-use GitHub Actions workflow
7. **Maintainability**: Clear naming conventions, fixtures, and documentation

The architecture supports the multi-agent nature of the AgnoOpportunityAnalyzer while ensuring test reliability and maintainability as the codebase evolves.