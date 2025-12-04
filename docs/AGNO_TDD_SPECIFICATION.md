# Agno Multi-Agent Integration Test-Driven Development Specification

**Generated:** 2025-12-03 19:28:00
**Purpose:** Comprehensive test specification for implementing Agno multi-agent system in Pipeline v3
**Testing Framework:** pytest with fixtures and parameterized tests
**Coverage Target:** 80% minimum requirement

---

## Executive Summary

This document provides a comprehensive test-driven development (TDD) specification for implementing the Agno multi-agent integration into RedditHarbor Pipeline v3. The specification defines all test scenarios, acceptance criteria, edge cases, and validation checkpoints required to ensure a robust, backward-compatible implementation that meets all business requirements.

**Implementation Requirements:**
- 100% backward compatibility with existing Pipeline v3 API
- 80% test coverage minimum
- Multi-agent consensus scoring with real-time market validation
- Cost tracking integration with LiteLLM
- AgentOps monitoring integration
- Performance targets: <10s per analysis

---

## 1. Functional Requirements Breakdown

### 1.1 Core Components to Implement

#### A. **AgnoOpportunityAnalyzer** (`pipeline-v3/transform/agno_analyzer.py`)
**Primary Function:** Multi-agent coordinator implementing Pipeline v3 interface
**Key Responsibilities:**
- Orchestrate 4 specialized agents + MarketResearchAgent
- Implement parallel/sequential execution modes
- Consensus-based scoring synthesis
- Pipeline v3 AnalysisResult format conversion
- Cost tracking and AgentOps integration

#### B. **4 Specialized Agents** (`pipeline-v3/transform/agno_agents.py`)
1. **WillingnessToPayAgent (WTP Agent)**
   - Analyze user sentiment and payment willingness
   - Extract pricing psychology indicators
   - Output: WTP score, confidence level, indicators

2. **MarketSegmentAgent (Segment Agent)**
   - B2B vs B2C classification
   - Industry-specific context analysis
   - Output: Market segment, industry classification, confidence

3. **PricePointAgent (Price Agent)**
   - Revenue modeling and pricing strategy
   - Market positioning analysis
   - Output: Price range, revenue potential, pricing strategy

4. **PaymentBehaviorAgent (Payment Agent)**
   - Purchase pattern analysis
   - Friction identification
   - Output: Payment preferences, friction points, conversion factors

#### C. **MarketResearchAgent** (`pipeline-v3/transform/market_research_agent.py`)
**Integration Point:** Jina API for real market data
**Functions:**
- Web search for competitor pricing
- Market size validation
- Product launch research
- Evidence-based opportunity validation

#### D. **AgnoAnalyzerFactory** (`pipeline-v3/transform/analyzer_factory.py`)
**Pattern:** Factory pattern extension
**Functions:**
- Create AgnoOpportunityAnalyzer instances
- Configuration management
- Dependency injection for agents
- Environment variable handling

---

## 2. Acceptance Criteria

### 2.1 AgnoOpportunityAnalyzer Acceptance Criteria

**CRITERION 1: API Compatibility**
```python
# Test: test_api_compatibility
def test_analyze_submission_interface():
    """Must implement the exact same interface as existing analyzers"""
    # Given: AgnoOpportunityAnalyzer instance
    # When: Calling analyze_submission(submission)
    # Then: Returns AnalysisResult object with all required fields

# Test: test_backward_compatibility
def test_analyze_batch_with_costs_interface():
    """Must implement batch analysis with cost tracking"""
    # Given: List of RedditSubmission objects
    # When: Calling analyze_batch_with_costs(submissions)
    # Then: Returns Tuple[List[AnalysisResult], CostSummary]
```

**CRITERION 2: Multi-Agent Orchestration**
```python
# Test: test_parallel_execution_mode
def test_parallel_agent_execution():
    """Agents must execute in parallel when configured"""
    # Given: Orchestration mode = "parallel"
    # When: Analyzing submission
    # Then: All 4 agents execute concurrently
    # And: Execution time < sequential mode

# Test: test_sequential_execution_mode
def test_sequential_agent_execution():
    """Agents must execute sequentially when configured"""
    # Given: Orchestration mode = "sequential"
    # When: Analyzing submission
    # Then: Agents execute one after another
    # And: Output order matches agent priority
```

**CRITERION 3: Consensus-Based Scoring**
```python
# Test: test_consensus_scoring
def test_multi_agent_consensus():
    """Must implement consensus-based scoring algorithm"""
    # Given: Agent outputs with varying scores
    # When: Synthesizing results
    # Then: Final score reflects consensus weighting
    # And: Low-confidence agents have reduced influence

# Test: test_consensus_threshold
def test_consensus_threshold_enforcement():
    """Must enforce minimum consensus threshold"""
    # Given: Agent outputs below consensus threshold
    # When: Synthesizing results
    # Then: Result marked as low confidence
    # And: Fallback to single-agent analysis if threshold < 60%
```

### 2.2 Specialized Agents Acceptance Criteria

**CRITERION 4: Agent Specialization**
```python
# Test: test_wtp_agent_specialization
def test_wtp_agent_pricing_analysis():
    """WTP Agent must focus on willingness to pay indicators"""
    # Given: Reddit submission discussing budget constraints
    # When: WTP agent analyzes
    # Then: Output includes specific WTP indicators
    # And: Score reflects budget sensitivity

# Test: test_segment_agent_classification
def test_segment_agent_b2b_classification():
    """Segment Agent must correctly classify B2B contexts"""
    # Given: B2B discussion (enterprise tools, etc.)
    # When: Segment agent analyzes
    # Then: Classification = "B2B"
    # And: Industry context is accurate

# Test: test_price_agent_modeling
def test_price_agent_revenue_modeling():
    """Price Agent must provide revenue modeling"""
    # Given: Opportunity with clear market size
    # When: Price agent analyzes
    # Then: Output includes revenue projections
    # And: Pricing strategy is justified

# Test: test_payment_agent_behavior
def test_payment_agent_friction_analysis():
    """Payment Agent must identify friction points"""
    # Given: Discussion about payment difficulties
    # When: Payment agent analyzes
    # Then: Friction points are identified
    # And: Conversion factors are calculated
```

### 2.3 MarketResearchAgent Acceptance Criteria

**CRITERION 5: Jina API Integration**
```python
# Test: test_jina_web_search
def test_market_research_web_search():
    """Must search web for competitor pricing"""
    # Given: Opportunity in specific domain
    # When: MarketResearchAgent searches
    # Then: Returns competitor pricing data
    # And: Validates against real market prices

# Test: test_jina_content_extraction
def test_market_research_extraction():
    """Must extract specific pricing information"""
    # Given: URLs with pricing pages
    # When: Jina Reader extracts content
    # Then: Pricing plans are extracted accurately
    # And: Market size data is retrieved

# Test: test_jina_api_error_handling
def test_jina_api_error_handling():
    """Must handle Jina API failures gracefully"""
    # Given: Jina API is unavailable
    # When: MarketResearchAgent attempts search
    # Then: Continues analysis without market data
    # And: Logs appropriate warnings
```

### 2.4 Factory Pattern Integration

**CRITERION 6: Factory Registration**
```python
# Test: test_agno_factory_registration
def test_analyzer_factory_supports_agno():
    """Factory must support 'agno' analyzer type"""
    # Given: AnalyzerFactoryProvider instance
    # When: Requesting 'agno' analyzer type
    # Then: Returns AgnoOpportunityAnalyzer instance

# Test: test_agno_factory_configuration
def test_agno_factory_configuration():
    """Factory must configure analyzer with settings"""
    # Given: Environment variables for Agno
    # When: Creating Agno analyzer
    # Then: Analyzer is configured with correct settings
    # And: Defaults are applied when missing
```

---

## 3. Edge Cases and Boundary Conditions

### 3.1 Input Edge Cases

**Test Category: Invalid Input Handling**
```python
# Test: test_empty_submission
def test_analyze_empty_submission():
    """Handle empty or minimal submission data"""
    # Given: Submission with empty title/text
    # When: Analyzing with Agno
    # Then: Returns AnalysisResult with appropriate scores
    # And: Does not crash agents

# Test: test_very_long_submission
def test_analyze_very_long_submission():
    """Handle extremely long submission content"""
    # Given: Submission with >50,000 characters
    # When: Analyzing with Agno
    # Then: Content is truncated appropriately
    # And: Analysis completes successfully

# Test: test_malformed_submission
def test_analyze_malformed_submission():
    """Handle submissions with corrupted data"""
    # Given: RedditSubmission with None fields
    # When: Analyzing with Agno
    # Then: Graceful error handling
    # And: Fallback to basic analysis
```

### 3.2 Agent Failure Edge Cases

**Test Category: Agent Resilience**
```python
# Test: test_agent_timeout
def test_agent_timeout_handling():
    """Handle individual agent timeouts"""
    # Given: One agent takes >30 seconds
    # When: Timeout occurs
    # Then: Other agents continue
    # And: Synthesis uses available results

# Test: test_agent_crash
def test_agent_crash_handling():
    """Handle agent crash during analysis"""
    # Given: Agent raises exception
    # When: Analysis in progress
    # Then: Other agents complete
    # And: Error is logged appropriately

# Test: test_agent_partial_failure
def test_multiple_agent_failures():
    """Handle multiple agent failures"""
    # Given: 3 of 5 agents fail
    # When: Analysis in progress
    # Then: Fallback to single-agent mode
    # And: Analysis continues with remaining agents
```

### 3.3 Performance Edge Cases

**Test Category: Performance Degradation**
```python
# Test: test_high_concurrency
def test_concurrent_analyses():
    """Handle multiple concurrent analyses"""
    # Given: 10 concurrent submission analyses
    # When: Executing simultaneously
    # Then: Each analysis completes correctly
    # And: Performance degrades gracefully

# Test: test_memory_pressure
def test_memory_pressure_handling():
    """Handle low memory conditions"""
    # Given: System memory pressure
    # When: Running analysis
    # Then: Analysis completes
    # And: Memory usage stays within limits

# Test: test_network_latency
def test_network_latency_handling():
    """Handle high network latency to APIs"""
    # Given: 5+ second network latency
    # When: Calling external APIs
    # Then: Timeouts are respected
    # And: Analysis continues
```

### 3.4 Data Edge Cases

**Test Category: Data Quality Issues**
```python
# Test: test_unicode_handling
def test_unicode_content():
    """Handle Unicode characters and emojis"""
    # Given: Submission with Unicode/emojis
    # When: Analyzing with agents
    # Then: No encoding errors
    # And: Analysis is accurate

# Test: test_spam_content
def test_spam_detection():
    """Handle spam and low-quality content"""
    # Given: Known spam submission
    # When: Analyzing with Agno
    # Then: spam_indicators are detected
    # And: content_quality_score is appropriate

# Test: test_sensitive_content
def test_sensitive_content_handling():
    """Handle potentially sensitive content"""
    # Given: Submission with PII/sensitive data
    # When: Analyzing with Agno
    # Then: PII is anonymized if enabled
    # And: Analysis respects privacy settings
```

---

## 4. Test Scenarios by Component

### 4.1 AgnoOpportunityAnalyzer Test Suite

#### **Test Suite 1: Basic Functionality**
```python
class TestAgnoOpportunityAnalyzer:
    """Comprehensive tests for AgnoOpportunityAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        """Create AgnoOpportunityAnalyzer instance for testing"""
        return AgnoOpportunityAnalyzer(
            model="anthropic/claude-haiku-4.5",
            api_key="test_key",
            base_url="https://openrouter.ai/api/v1"
        )

    @pytest.fixture
    def sample_submission(self):
        """Create sample RedditSubmission for testing"""
        return RedditSubmission(
            id="test123",
            title="I wish there was an app that could track my startup expenses better",
            text="Currently using spreadsheets and it's a nightmare. Need something that integrates with bank accounts and categorizes expenses automatically.",
            subreddit="Entrepreneur",
            score=145,
            num_comments=23,
            created_at=datetime.now(),
            author="test_user"
        )

    def test_analyze_submission_structure(self, analyzer, sample_submission):
        """Test that analyze_submission returns correct structure"""
        result = analyzer.analyze_submission(sample_submission)

        # Verify AnalysisResult structure
        assert isinstance(result, AnalysisResult)
        assert hasattr(result, 'app_idea')
        assert hasattr(result, 'market_metrics')
        assert hasattr(result, 'validation_evidence')  # New for Agno
        assert result.embedding is not None
        assert len(result.embedding) > 0

    def test_consensus_scoring_algorithm(self, analyzer):
        """Test multi-agent consensus scoring algorithm"""
        # Create mock agent outputs with different scores
        agent_outputs = {
            'wtp_agent': {'score': 85, 'confidence': 0.8},
            'segment_agent': {'score': 75, 'confidence': 0.9},
            'price_agent': {'score': 80, 'confidence': 0.7},
            'payment_agent': {'score': 70, 'confidence': 0.6}
        }

        # Test consensus calculation
        consensus_score = analyzer._calculate_consensus_score(agent_outputs)

        # Verify consensus reflects agent confidence weighting
        assert 70 <= consensus_score <= 85
        assert isinstance(consensus_score, float)

    @pytest.mark.parametrize("orchestration_mode", ["parallel", "sequential"])
    def test_orchestration_modes(self, analyzer, sample_submission, orchestration_mode):
        """Test both parallel and sequential orchestration modes"""
        analyzer.orchestration_mode = orchestration_mode

        start_time = time.time()
        result = analyzer.analyze_submission(sample_submission)
        end_time = time.time()

        # Verify successful analysis
        assert isinstance(result, AnalysisResult)
        assert result.app_idea is not None

        # Verify orchestration completed
        execution_time = end_time - start_time
        assert execution_time < 30  # Should complete within 30 seconds

    def test_cost_tracking_integration(self, analyzer, sample_submission):
        """Test LiteLLM cost tracking integration"""
        result, cost_tracking = analyzer.analyze_submission_with_costs(sample_submission)

        # Verify cost tracking structure
        assert isinstance(cost_tracking, CostTracking)
        assert cost_tracking.total_cost > 0
        assert cost_tracking.total_tokens > 0
        assert cost_tracking.model_used == analyzer.model_name

        # Verify analysis result
        assert isinstance(result, AnalysisResult)

    def test_agentops_integration(self, analyzer, sample_submission):
        """Test AgentOps monitoring integration"""
        # Mock AgentOps tracker
        with patch('monitoring.get_tracker') as mock_tracker:
            mock_tracker.return_value = MockAgentOpsTracker()

            result = analyzer.analyze_submission(sample_submission)

            # Verify AgentOps was called
            mock_tracker.assert_called()
            mock_tracker.return_value.track_operation_result.assert_called()

    def test_fallback_to_single_agent(self, analyzer, sample_submission):
        """Test fallback behavior when consensus threshold not met"""
        # Mock agent outputs to simulate low consensus
        with patch.object(analyzer, '_run_agents') as mock_agents:
            mock_agents.return_value = {
                'wtp_agent': {'score': 20, 'confidence': 0.3},
                'segment_agent': {'score': 15, 'confidence': 0.2},
                'price_agent': {'score': 25, 'confidence': 0.4},
                'payment_agent': {'score': 10, 'confidence': 0.1}
            }

            result = analyzer.analyze_submission(sample_submission)

            # Verify fallback occurred
            assert result.analysis_method == "single_agent_fallback"
            assert hasattr(result, 'fallback_reason')
```

#### **Test Suite 2: Error Handling and Edge Cases**
```python
class TestAgnoOpportunityAnalyzerEdgeCases:
    """Edge cases and error handling for AgnoOpportunityAnalyzer"""

    def test_agent_failure_recovery(self, analyzer):
        """Test recovery from individual agent failures"""
        # Mock agents with one failing
        with patch.object(analyzer, '_run_agents') as mock_agents:
            mock_agents.side_effect = [
                # First call: All agents succeed
                {'wtp_agent': {'score': 80, 'confidence': 0.8}},
                # Second call: One agent fails
                {'segment_agent': {'error': 'Timeout'}, 'price_agent': {'score': 75}}
            ]

            # Test successful recovery
            result = analyzer.analyze_submission(sample_submission)
            assert isinstance(result, AnalysisResult)

    def test_network_timeout_handling(self, analyzer):
        """Test handling of network timeouts"""
        # Mock network timeout
        with patch('litellm.completion') as mock_llm:
            mock_llm.side_effect = TimeoutError("Network timeout")

            result = analyzer.analyze_submission(sample_submission)

            # Verify graceful handling
            assert isinstance(result, AnalysisResult)
            assert result.analysis_method == "fallback_analysis"

    def test_api_rate_limit_handling(self, analyzer):
        """Test handling of API rate limits"""
        # Mock rate limit response
        with patch('litellm.completion') as mock_llm:
            mock_llm.side_effect = Exception("Rate limit exceeded")

            result = analyzer.analyze_submission(sample_submission)

            # Verify retry logic or graceful degradation
            assert isinstance(result, AnalysisResult)

    @pytest.mark.asyncio
    async def test_concurrent_analysis_safety(self, analyzer):
        """Test thread safety during concurrent analyses"""
        import asyncio

        submissions = [create_sample_submission() for _ in range(5)]
        tasks = [analyzer.analyze_submission(sub) for sub in submissions]

        # Run analyses concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all analyses completed successfully
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, AnalysisResult)
```

### 4.2 Specialized Agents Test Suite

#### **Test Suite 3: WillingnessToPayAgent**
```python
class TestWillingnessToPayAgent:
    """Tests for WillingnessToPayAgent"""

    @pytest.fixture
    def wtp_agent(self):
        """Create WTP agent instance"""
        return WillingnessToPayAgent(
            model="anthropic/claude-haiku-4.5",
            api_key="test_key"
        )

    @pytest.mark.parametrize("submission_text,expected_wtp", [
        ("I'd pay $50/month for a solution like this", "high"),
        ("Can't afford more than $10 for this", "low"),
        ("Willing to invest if it saves time", "medium"),
        ("Need a free solution, no budget", "very_low")
    ])
    def test_wtp_indicator_detection(self, wtp_agent, submission_text, expected_wtp):
        """Test detection of willingness to pay indicators"""
        submission = RedditSubmission(
            id="test",
            title="Test",
            text=submission_text,
            subreddit="test"
        )

        result = wtp_agent.analyze(submission)

        assert result['wtp_category'] == expected_wtp
        assert 'wtp_indicators' in result
        assert isinstance(result['confidence'], float)
        assert 0 <= result['confidence'] <= 1

    def test_pricing_psychology_analysis(self, wtp_agent):
        """Test analysis of pricing psychology"""
        submission = RedditSubmission(
            id="test",
            title="Premium tool for enterprises",
            text="We need enterprise-grade features and are willing to pay premium pricing for reliability and support",
            subreddit="sysadmin"
        )

        result = wtp_agent.analyze(submission)

        # Verify psychology indicators
        assert 'premium_willingness' in result
        assert 'value_proposition' in result
        assert 'price_sensitivity' in result
        assert result['wtp_score'] >= 70
```

#### **Test Suite 4: MarketSegmentAgent**
```python
class TestMarketSegmentAgent:
    """Tests for MarketSegmentAgent"""

    @pytest.fixture
    def segment_agent(self):
        """Create Segment agent instance"""
        return MarketSegmentAgent(
            model="anthropic/claude-haiku-4.5",
            api_key="test_key"
        )

    @pytest.mark.parametrize("submission_text,expected_segment", [
        ("Our startup needs better project management tools", "B2B"),
        ("I want an app to track my personal fitness", "B2C"),
        ("School needs attendance tracking system", "B2B_Education"),
        ("Looking for family recipe organizer", "B2C_Family")
    ])
    def test_market_segment_classification(self, segment_agent, submission_text, expected_segment):
        """Test B2B vs B2C classification"""
        submission = RedditSubmission(
            id="test",
            title="Test",
            text=submission_text,
            subreddit="test"
        )

        result = segment_agent.analyze(submission)

        assert result['market_segment'] == expected_segment
        assert 'industry_context' in result
        assert 'target_audience' in result
        assert result['confidence'] >= 0.7

    def test_industry_context_extraction(self, segment_agent):
        """Test extraction of industry-specific context"""
        submission = RedditSubmission(
            id="test",
            title="Healthcare scheduling challenges",
            text="Our clinic struggles with patient appointment scheduling and reminder systems",
            subreddit="HealthcareIT"
        )

        result = segment_agent.analyze(submission)

        # Verify healthcare context
        assert result['industry_context']['sector'] == 'healthcare'
        assert 'clinic' in result['target_audience'].lower()
        assert 'compliance' in result['industry_context'].get('requirements', [])
```

#### **Test Suite 5: PricePointAgent**
```python
class TestPricePointAgent:
    """Tests for PricePointAgent"""

    @pytest.fixture
    def price_agent(self):
        """Create Price agent instance"""
        return PricePointAgent(
            model="anthropic/claude-haiku-4.5",
            api_key="test_key"
        )

    def test_revenue_modeling(self, price_agent):
        """Test revenue projection modeling"""
        submission = RedditSubmission(
            id="test",
            title="SaaS tool for small businesses",
            text="Need a subscription-based tool for inventory management. Would serve thousands of small retailers",
            subreddit="SmallBusiness"
        )

        result = price_agent.analyze(submission)

        # Verify revenue modeling
        assert 'pricing_model' in result
        assert result['pricing_model']['type'] == 'subscription'
        assert 'price_range' in result
        assert result['price_range']['min'] > 0
        assert result['price_range']['max'] > result['price_range']['min']
        assert 'revenue_projection' in result
        assert 'market_size_estimate' in result

    def test_pricing_strategy_recommendation(self, price_agent):
        """Test pricing strategy recommendations"""
        submission = RedditSubmission(
            id="test",
            title="Freemium app idea",
            text="Offer basic features for free, premium features for $10/month",
            subreddit="apps"
        )

        result = price_agent.analyze(submission)

        # Verify strategy recommendations
        assert 'pricing_strategy' in result
        assert result['pricing_strategy']['approach'] == 'freemium'
        assert 'conversion_rate_estimate' in result
        assert 'competitive_positioning' in result
```

#### **Test Suite 6: PaymentBehaviorAgent**
```python
class TestPaymentBehaviorAgent:
    """Tests for PaymentBehaviorAgent"""

    @pytest.fixture
    def payment_agent(self):
        """Create Payment agent instance"""
        return PaymentBehaviorAgent(
            model="anthropic/claude-haiku-4.5",
            api_key="test_key"
        )

    def test_payment_preference_analysis(self, payment_agent):
        """Test payment preference analysis"""
        submission = RedditSubmission(
            id="test",
            title="Hate entering credit cards",
            text="Wish more services accepted Apple Pay and Google Pay for faster checkout",
            subreddit="privacy"
        )

        result = payment_agent.analyze(submission)

        # Verify payment preferences
        assert 'payment_preferences' in result
        assert 'digital_wallet' in result['payment_preferences']
        assert 'friction_points' in result
        assert 'credit_card_entry' in str(result['friction_points'])
        assert 'conversion_factors' in result

    def test_subscription_fatigue_detection(self, payment_agent):
        """Test detection of subscription fatigue"""
        submission = RedditSubmission(
            id="test",
            title="Too many subscriptions",
            text="I'm canceling subscriptions because there are too many monthly charges. Need lifetime options",
            subreddit="personalfinance"
        )

        result = payment_agent.analyze(submission)

        # Verify fatigue detection
        assert 'subscription_fatigue' in result
        assert result['subscription_fatigue']['detected'] is True
        assert 'lifetime_interest' in result
        assert result['lifetime_interest']['high'] is True
```

### 4.3 MarketResearchAgent Test Suite

#### **Test Suite 7: Jina API Integration**
```python
class TestMarketResearchAgent:
    """Tests for MarketResearchAgent with Jina integration"""

    @pytest.fixture
    def market_agent(self):
        """Create MarketResearchAgent instance"""
        return MarketResearchAgent(
            jina_api_key="test_key",
            enable_real_search=False  # Disable for testing
        )

    @pytest.fixture
    def mock_jina_response(self):
        """Mock Jina API response"""
        return {
            "competitors": [
                {
                    "name": "CompetitorA",
                    "pricing": {"basic": "$9/month", "pro": "$29/month"},
                    "features": ["feature1", "feature2"]
                }
            ],
            "market_size": {
                "tam": "$2.5B",
                "sam": "$800M",
                "som": "$50M"
            },
            "validation_score": 0.75
        }

    def test_competitor_pricing_search(self, market_agent, mock_jina_response):
        """Test competitor pricing search via Jina"""
        with patch.object(market_agent, '_search_competitors') as mock_search:
            mock_search.return_value = mock_jina_response

            result = market_agent.research_market("project management software")

            # Verify competitor data extraction
            assert 'competitors' in result
            assert len(result['competitors']) > 0
            assert 'pricing' in result['competitors'][0]
            assert 'basic' in result['competitors'][0]['pricing']

    def test_market_size_validation(self, market_agent, mock_jina_response):
        """Test market size validation"""
        with patch.object(market_agent, '_validate_market_size') as mock_validate:
            mock_validate.return_value = mock_jina_response['market_size']

            result = market_agent.research_market("fitness app")

            # Verify market size data
            assert 'market_size' in result
            assert 'tam' in result['market_size']
            assert 'sam' in result['market_size']
            assert 'som' in result['market_size']

    def test_jina_api_error_handling(self, market_agent):
        """Test Jina API error handling"""
        with patch.object(market_agent, '_call_jina_api') as mock_jina:
            mock_jina.side_effect = Exception("Jina API unavailable")

            result = market_agent.research_market("test market")

            # Verify graceful error handling
            assert 'error' in result
            assert result['fallback_used'] is True
            assert result['market_data_available'] is False

    @pytest.mark.asyncio
    async def test_async_market_research(self, market_agent):
        """Test asynchronous market research capabilities"""
        markets = ["project management", "fitness tracking", "note taking"]

        # Run research in parallel
        tasks = [market_agent.research_market_async(market) for market in markets]
        results = await asyncio.gather(*tasks)

        # Verify all markets researched
        assert len(results) == len(markets)
        for result in results:
            assert isinstance(result, dict)
            assert 'competitors' in result or 'error' in result
```

### 4.4 Factory Pattern Test Suite

#### **Test Suite 8: AgnoAnalyzerFactory**
```python
class TestAgnoAnalyzerFactory:
    """Tests for AgnoAnalyzerFactory integration"""

    @pytest.fixture
    def factory_provider(self):
        """Create factory provider with Agno support"""
        from pipeline_v3.transform.analyzer_factory import AnalyzerFactoryProvider
        return AnalyzerFactoryProvider()

    def test_agno_factory_registration(self, factory_provider):
        """Test that Agno factory is properly registered"""
        # Register Agno factory
        agno_factory = AgnoAnalyzerFactory()
        factory_provider.register_factory('agno', agno_factory)

        # Verify registration
        available_factories = factory_provider.list_available_factories()
        assert 'agno' in available_factories

    def test_agno_analyzer_creation(self, factory_provider):
        """Test creation of Agno analyzer through factory"""
        # Register Agno factory
        agno_factory = AgnoAnalyzerFactory()
        factory_provider.register_factory('agno', agno_factory)

        # Create analyzer
        analyzer = factory_provider.create_analyzer('agno')

        # Verify analyzer type
        assert isinstance(analyzer, AgnoOpportunityAnalyzer)
        assert analyzer.model_name is not None
        assert analyzer.api_key is not None

    def test_agno_configuration_handling(self, factory_provider):
        """Test configuration handling for Agno analyzer"""
        # Register Agno factory with config
        agno_factory = AgnoAnalyzerFactory()
        factory_provider.register_factory('agno', agno_factory)

        # Create analyzer with custom config
        config = {
            'model': 'anthropic/claude-3-haiku',
            'orchestration_mode': 'parallel',
            'consensus_threshold': 70.0
        }

        analyzer = factory_provider.create_analyzer('agno', config)

        # Verify configuration applied
        assert analyzer.model_name == 'anthropic/claude-3-haiku'
        assert analyzer.orchestration_mode == 'parallel'
        assert analyzer.consensus_threshold == 70.0
```

---

## 5. Integration Test Scenarios

### 5.1 End-to-End Pipeline Integration

#### **Test Suite 9: Pipeline v3 Integration**
```python
class TestPipelineV3Integration:
    """Integration tests for full Pipeline v3 with Agno"""

    @pytest.fixture
    def pipeline_config(self):
        """Create pipeline configuration with Agno"""
        return {
            'analyzer_type': 'agno',
            'agno_config': {
                'model': 'anthropic/claude-haiku-4.5',
                'orchestration_mode': 'parallel',
                'enable_market_research': True,
                'consensus_threshold': 60.0
            }
        }

    def test_full_pipeline_analysis(self, pipeline_config):
        """Test complete pipeline analysis with Agno"""
        # Create Reddit submission
        submission = RedditSubmission(
            id="integration_test",
            title="Need a better way to track remote team productivity",
            text="Current tools are invasive and don't capture actual work. Need something that respects privacy while providing insights",
            subreddit="remotework",
            score=234,
            num_comments=45
        )

        # Run through full pipeline
        analyzer = create_analyzer('agno', pipeline_config['agno_config'])
        result = analyzer.analyze_submission(submission)

        # Verify pipeline output
        assert isinstance(result, AnalysisResult)
        assert result.app_idea.title is not None
        assert len(result.app_idea.functions) <= 3  # Simplicity constraint
        assert result.market_metrics is not None
        assert hasattr(result, 'validation_evidence')  # Agno-specific
        assert result.embedding is not None

    def test_database_compatibility(self, pipeline_config):
        """Test database schema compatibility"""
        # Analyze submission
        analyzer = create_analyzer('agno', pipeline_config['agno_config'])
        submission = create_test_submission()
        result = analyzer.analyze_submission(submission)

        # Test database insertion
        db_handler = DatabaseHandler()

        # Should not raise any exceptions
        opportunity_id = db_handler.insert_opportunity(result, submission)
        assert opportunity_id is not None

        # Verify Agno-specific fields are stored
        stored_opportunity = db_handler.get_opportunity(opportunity_id)
        assert stored_opportunity.validation_evidence is not None
        assert stored_opportunity.analysis_method == 'agno_multi_agent'

    def test_backward_compatibility(self):
        """Test backward compatibility with existing pipeline"""
        # Test that existing analyzer types still work
        for analyzer_type in ['simple', 'litellm', 'production']:
            analyzer = create_analyzer(analyzer_type)
            submission = create_test_submission()
            result = analyzer.analyze_submission(submission)

            # All should return AnalysisResult
            assert isinstance(result, AnalysisResult)
            assert result.app_idea is not None
            assert result.market_metrics is not None
```

### 5.2 Cost Tracking Integration

#### **Test Suite 10: LiteLLM Cost Tracking**
```python
class TestCostTrackingIntegration:
    """Tests for LiteLLM cost tracking with Agno"""

    def test_multi_agent_cost_tracking(self):
        """Test cost tracking across multiple agents"""
        analyzer = AgnoOpportunityAnalyzer(
            model="anthropic/claude-haiku-4.5",
            api_key="test_key"
        )

        submission = create_test_submission()
        result, cost_tracking = analyzer.analyze_submission_with_costs(submission)

        # Verify cost tracking includes all agents
        assert isinstance(cost_tracking, CostTracking)
        assert cost_tracking.total_cost > 0
        assert cost_tracking.total_tokens > 0
        assert 'agent_costs' in cost_tracking.metadata
        assert len(cost_tracking.metadata['agent_costs']) == 5  # 4 agents + synthesis

    def test_cost_comparison_single_vs_multi_agent(self):
        """Test cost comparison between single and multi-agent analysis"""
        # Single-agent analysis
        simple_analyzer = create_analyzer('litellm')
        _, simple_cost = simple_analyzer.analyze_submission_with_costs(test_submission)

        # Multi-agent analysis
        agno_analyzer = create_analyzer('agno')
        _, agno_cost = agno_analyzer.analyze_submission_with_costs(test_submission)

        # Multi-agent should cost more but provide better insights
        assert agno_cost.total_cost > simple_cost.total_cost
        assert agno_cost.total_tokens > simple_cost.total_tokens

        # But cost should still be reasonable
        assert agno_cost.total_cost < 0.01  # Less than 1 cent
```

### 5.3 Monitoring Integration

#### **Test Suite 11: AgentOps Integration**
```python
class TestAgentOpsIntegration:
    """Tests for AgentOps monitoring integration"""

    @patch('monitoring.get_tracker')
    def test_agent_ops_tracking(self, mock_get_tracker):
        """Test AgentOps tracking for multi-agent analysis"""
        # Setup mock tracker
        mock_tracker = MockAgentOpsTracker()
        mock_get_tracker.return_value = mock_tracker

        # Create analyzer with AgentOps enabled
        analyzer = AgnoOpportunityAnalyzer(
            model="anthropic/claude-haiku-4.5",
            api_key="test_key",
            enable_agentops_tracking=True
        )

        # Run analysis
        submission = create_test_submission()
        result = analyzer.analyze_submission(submission)

        # Verify AgentOps was called
        mock_tracker.track_operation_result.assert_called()

        # Verify tracking calls include expected metadata
        calls = mock_tracker.track_operation_result.call_args_list
        assert any('agent_execution' in str(call) for call in calls)
        assert any('consensus_scoring' in str(call) for call in calls)

    def test_performance_metrics_tracking(self):
        """Test performance metrics tracking"""
        analyzer = AgnoOpportunityAnalyzer(
            model="anthropic/claude-haiku-4.5",
            api_key="test_key"
        )

        # Track multiple analyses for metrics
        submissions = [create_test_submission() for _ in range(5)]
        for submission in submissions:
            analyzer.analyze_submission(submission)

        # Verify metrics are tracked
        metrics = analyzer.get_performance_metrics()
        assert 'total_analyses' in metrics
        assert 'average_execution_time' in metrics
        assert 'agent_success_rates' in metrics
        assert 'cost_per_analysis' in metrics
```

---

## 6. Performance and Load Testing

### 6.1 Performance Test Scenarios

#### **Test Suite 12: Performance Benchmarks**
```python
class TestAgnoPerformance:
    """Performance tests for Agno analyzer"""

    def test_execution_time_benchmarks(self):
        """Test execution time meets requirements"""
        analyzer = AgnoOpportunityAnalyzer(
            model="anthropic/claude-haiku-4.5",
            api_key="test_key"
        )

        # Test single submission analysis
        start_time = time.time()
        result = analyzer.analyze_submission(create_test_submission())
        execution_time = time.time() - start_time

        # Should complete within 10 seconds
        assert execution_time < 10.0
        assert isinstance(result, AnalysisResult)

    def test_batch_analysis_performance(self):
        """Test batch analysis performance"""
        analyzer = AgnoOpportunityAnalyzer(
            model="anthropic/claude-haiku-4.5",
            api_key="test_key"
        )

        # Create batch of submissions
        submissions = [create_test_submission() for _ in range(10)]

        # Test batch analysis
        start_time = time.time()
        results, cost_summary = analyzer.analyze_batch_with_costs(submissions)
        total_time = time.time() - start_time

        # Verify results
        assert len(results) == len(submissions)
        assert isinstance(cost_summary, CostSummary)

        # Performance should scale reasonably
        avg_time_per_analysis = total_time / len(submissions)
        assert avg_time_per_analysis < 15.0  # Allow some batch overhead

    def test_memory_usage_profiling(self):
        """Test memory usage stays within bounds"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        analyzer = AgnoOpportunityAnalyzer(
            model="anthropic/claude-haiku-4.5",
            api_key="test_key"
        )

        # Run multiple analyses
        for _ in range(20):
            analyzer.analyze_submission(create_test_submission())

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (<100MB)
        assert memory_increase < 100 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_concurrent_performance(self):
        """Test concurrent analysis performance"""
        import asyncio

        analyzer = AgnoOpportunityAnalyzer(
            model="anthropic/claude-haiku-4.5",
            api_key="test_key"
        )

        # Create concurrent tasks
        submissions = [create_test_submission() for _ in range(5)]
        tasks = [analyzer.analyze_submission(sub) for sub in submissions]

        # Run concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Verify all completed successfully
        assert len(results) == len(submissions)
        for result in results:
            assert isinstance(result, AnalysisResult)

        # Concurrent should be faster than sequential
        assert total_time < 30.0  # Much less than 5 * 10s sequential
```

### 6.2 Load Testing Scenarios

#### **Test Suite 13: Load Testing**
```python
class TestAgnoLoadTesting:
    """Load testing for Agno analyzer"""

    def test_sustained_load(self):
        """Test sustained load over time"""
        analyzer = AgnoOpportunityAnalyzer(
            model="anthropic/claude-haiku-4.5",
            api_key="test_key"
        )

        # Run sustained analysis for 5 minutes
        duration = 5 * 60  # 5 minutes
        start_time = time.time()
        analysis_count = 0

        while time.time() - start_time < duration:
            analyzer.analyze_submission(create_test_submission())
            analysis_count += 1
            time.sleep(0.1)  # 10 analyses per second

        # Should handle sustained load
        assert analysis_count > 100

        # Check for memory leaks
        metrics = analyzer.get_performance_metrics()
        assert metrics['memory_growth'] < 50 * 1024 * 1024  # <50MB growth

    def test_spike_load_handling(self):
        """Test handling of sudden load spikes"""
        analyzer = AgnoOpportunityAnalyzer(
            model="anthropic/claude-haiku-4.5",
            api_key="test_key"
        )

        # Sudden spike: 50 analyses at once
        spike_start = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(analyzer.analyze_submission, create_test_submission())
                for _ in range(50)
            ]
            results = [future.result() for future in futures]

        spike_time = time.time() - spike_start

        # Verify all completed successfully
        assert len(results) == 50
        for result in results:
            assert isinstance(result, AnalysisResult)

        # Should handle spike within reasonable time
        assert spike_time < 120  # 2 minutes for 50 analyses

        # System should recover quickly
        time.sleep(1)
        single_analysis_time = time.time()
        analyzer.analyze_submission(create_test_submission())
        single_analysis_time = time.time() - single_analysis_time

        assert single_analysis_time < 15  # Should return to normal performance
```

---

## 7. Success Criteria and Validation Checkpoints

### 7.1 Minimum Viable Product (MVP) Criteria

**CHECKPOINT 1: Core Functionality**
```python
def test_mvp_core_functionality():
    """Validate MVP core functionality"""

    # Required components
    required_components = [
        'AgnoOpportunityAnalyzer',
        'AgnoAnalyzerFactory',
        'WillingnessToPayAgent',
        'MarketSegmentAgent',
        'PricePointAgent',
        'PaymentBehaviorAgent'
    ]

    # Verify all components exist and are importable
    for component in required_components:
        assert component in globals() or component in dir()

    # Verify basic functionality
    analyzer = AgnoOpportunityAnalyzer(
        model="anthropic/claude-haiku-4.5",
        api_key="test_key"
    )

    submission = create_test_submission()
    result = analyzer.analyze_submission(submission)

    # MVP requirements
    assert isinstance(result, AnalysisResult)
    assert hasattr(result, 'validation_evidence')
    assert result.analysis_method == 'agno_multi_agent'
```

**CHECKPOINT 2: API Compatibility**
```python
def test_mvp_api_compatibility():
    """Validate 100% API compatibility"""

    # Test same interface as existing analyzers
    analyzer = AgnoOpportunityAnalyzer(
        model="anthropic/claude-haiku-4.5",
        api_key="test_key"
    )

    # Required methods
    assert hasattr(analyzer, 'analyze_submission')
    assert hasattr(analyzer, 'analyze_batch_with_costs')

    # Method signatures
    submission = create_test_submission()

    # Test analyze_submission
    result = analyzer.analyze_submission(submission)
    assert isinstance(result, AnalysisResult)

    # Test analyze_batch_with_costs
    results, costs = analyzer.analyze_batch_with_costs([submission])
    assert isinstance(results, list)
    assert isinstance(costs, CostSummary)
```

**CHECKPOINT 3: Basic Multi-Agent Functionality**
```python
def test_mvp_multi_agent_functionality():
    """Validate basic multi-agent functionality"""

    analyzer = AgnoOpportunityAnalyzer(
        model="anthropic/claude-haiku-4.5",
        api_key="test_key",
        orchestration_mode='parallel'
    )

    submission = create_test_submission()
    result = analyzer.analyze_submission(submission)

    # Verify multi-agent output
    assert hasattr(result, 'validation_evidence')
    assert result.validation_evidence is not None
    assert 'agent_outputs' in result.validation_evidence
    assert len(result.validation_evidence['agent_outputs']) >= 2  # At least 2 agents

    # Verify consensus scoring
    assert 'consensus_score' in result.validation_evidence
    assert 0 <= result.validation_evidence['consensus_score'] <= 100
```

### 7.2 Full Implementation Criteria

**CHECKPOINT 4: All 5 Agents Working**
```python
def test_full_implementation_all_agents():
    """Validate all 5 agents are working"""

    analyzer = AgnoOpportunityAnalyzer(
        model="anthropic/claude-haiku-4.5",
        api_key="test_key",
        enable_market_research=True
    )

    submission = create_test_submission()
    result = analyzer.analyze_submission(submission)

    # Verify all 5 agents contributed
    agent_outputs = result.validation_evidence['agent_outputs']
    required_agents = [
        'willingness_to_pay_agent',
        'market_segment_agent',
        'price_point_agent',
        'payment_behavior_agent',
        'market_research_agent'
    ]

    for agent in required_agents:
        assert agent in agent_outputs
        assert 'score' in agent_outputs[agent]
        assert 'confidence' in agent_outputs[agent]
```

**CHECKPOINT 5: MarketResearchAgent Integration**
```python
def test_full_implementation_market_research():
    """Validate MarketResearchAgent with Jina integration"""

    analyzer = AgnoOpportunityAnalyzer(
        model="anthropic/claude-haiku-4.5",
        api_key="test_key",
        enable_market_research=True
    )

    submission = RedditSubmission(
        id="market_test",
        title="Project management software competitor",
        text="Looking for alternatives to Jira and Asana",
        subreddit="projectmanagement"
    )

    result = analyzer.analyze_submission(submission)

    # Verify market research data
    market_data = result.validation_evidence['agent_outputs']['market_research_agent']
    assert 'market_research' in market_data
    assert 'competitors' in market_data['market_research']
    assert len(market_data['market_research']['competitors']) > 0
```

**CHECKPOINT 6: Cost and Performance Requirements**
```python
def test_full_implementation_performance():
    """Validate performance requirements"""

    analyzer = AgnoOpportunityAnalyzer(
        model="anthropic/claude-haiku-4.5",
        api_key="test_key"
    )

    # Test execution time < 10s
    start_time = time.time()
    result = analyzer.analyze_submission(create_test_submission())
    execution_time = time.time() - start_time

    assert execution_time < 10.0
    assert isinstance(result, AnalysisResult)

    # Test cost < $0.005 per analysis
    _, cost_tracking = analyzer.analyze_submission_with_costs(create_test_submission())
    assert cost_tracking.total_cost < 0.005
```

---

## 8. Test Coverage Requirements

### 8.1 Coverage Targets

**Minimum Coverage: 80%**
- AgnoOpportunityAnalyzer: 90%
- Specialized Agents: 85%
- MarketResearchAgent: 80%
- AgnoAnalyzerFactory: 85%
- Integration Tests: 75%

**Coverage Measurement Commands:**
```bash
# Run coverage for Agno components
pytest tests/transform/test_agno_analyzer.py --cov=transform.agno_analyzer --cov-report=html
pytest tests/transform/test_agno_agents.py --cov=transform.agno_agents --cov-report=html
pytest tests/integrations/test_jina_client.py --cov=integrations.jina_client --cov-report=html

# Generate combined coverage report
pytest tests/transform/test_agno_*.py --cov=transform --cov-report=html --cov-report=term-missing

# Verify minimum coverage
pytest --cov=transform --cov-fail-under=80
```

### 8.2 Test Coverage by Component

```python
# Coverage requirements for each component
COVERAGE_REQUIREMENTS = {
    'agno_analyzer.py': {
        'functions': 95,  # All functions must be covered
        'statements': 90,
        'branches': 85,
        'lines': 90
    },
    'agno_agents.py': {
        'functions': 90,
        'statements': 85,
        'branches': 80,
        'lines': 85
    },
    'market_research_agent.py': {
        'functions': 85,
        'statements': 80,
        'branches': 75,
        'lines': 80
    },
    'analyzer_factory.py': {
        'functions': 90,  # Only Agno-related functions
        'statements': 85,
        'branches': 80,
        'lines': 85
    }
}
```

---

## 9. Implementation Roadmap with Testing

### 9.1 Phase 1: Core Implementation (Days 1-3)
**Day 1: AgnoOpportunityAnalyzer**
- Write failing tests first (TDD)
- Implement basic structure
- Test: `test_agno_analyzer_basic.py`
- Coverage: 70%

**Day 2: Agent Framework**
- Write tests for agent orchestration
- Implement parallel/sequential modes
- Test: `test_agent_orchestration.py`
- Coverage: 75%

**Day 3: Consensus Scoring**
- Write tests for consensus algorithm
- Implement synthesis logic
- Test: `test_consensus_scoring.py`
- Coverage: 80%

### 9.2 Phase 2: Agent Implementation (Days 4-6)
**Day 4-5: Specialized Agents**
- Write tests for each agent
- Implement agent logic
- Test: `test_specialized_agents.py`
- Coverage: 80%

**Day 6: MarketResearchAgent**
- Write tests for Jina integration
- Implement market research
- Test: `test_market_research_agent.py`
- Coverage: 75%

### 9.3 Phase 3: Integration (Days 7-9)
**Day 7: Factory Integration**
- Write tests for factory pattern
- Implement AgnoAnalyzerFactory
- Test: `test_factory_integration.py`
- Coverage: 85%

**Day 8: Pipeline Integration**
- Write end-to-end tests
- Integrate with Pipeline v3
- Test: `test_pipeline_integration.py`
- Coverage: 80%

**Day 9: Performance Optimization**
- Write performance tests
- Optimize bottlenecks
- Test: `test_performance_optimization.py`
- Coverage: 85%

---

## 10. Test Environment Setup

### 10.1 Testing Infrastructure

**Required Test Dependencies:**
```txt
# requirements-test.txt
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
pytest-mock>=3.11.1
pytest-xdist>=3.3.1  # Parallel testing
pytest-benchmark>=4.0.0  # Performance testing
factory-boy>=3.3.0  # Test data generation
faker>=19.0.0  # Fake data generation
responses>=0.23.0  # Mock HTTP responses
aioresponses>=0.7.4  # Mock async HTTP responses
```

**Test Configuration:**
```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--disable-warnings",
    "--cov=transform",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=80"
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "performance: marks tests as performance tests"
]
```

### 10.2 Mock Services Setup

**Mock API Services:**
```python
# tests/conftest.py
import pytest
from unittest.mock import Mock, patch
import responses

@pytest.fixture
def mock_openrouter_api():
    """Mock OpenRouter API responses"""
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.POST,
            "https://openrouter.ai/api/v1/chat/completions",
            json={
                "choices": [{
                    "message": {
                        "content": '{"test": "response"}'
                    }
                }]
            }
        )
        yield rsps

@pytest.fixture
def mock_jina_api():
    """Mock Jina API responses"""
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "https://r.jina.ai/http://example.com",
            json={
                "title": "Example Page",
                "content": "Extracted content",
                "url": "http://example.com"
            }
        )
        yield rsps

@pytest.fixture
def mock_supabase():
    """Mock Supabase database"""
    with patch('supabase.create_client') as mock_client:
        mock_client.return_value.table.return_value.insert.return_value.execute.return_value.data = [{"id": 1}]
        yield mock_client
```

---

## Conclusion

This comprehensive test specification provides a complete TDD roadmap for implementing the Agno multi-agent integration into RedditHarbor Pipeline v3. The specification covers:

1. **100% API Compatibility** - Ensures backward compatibility with existing Pipeline v3
2. **80% Test Coverage** - Meets the minimum coverage requirement
3. **Comprehensive Edge Cases** - Handles all failure modes and boundary conditions
4. **Performance Validation** - Ensures <10s execution time and <$0.005 cost per analysis
5. **Integration Testing** - Validates end-to-end pipeline functionality
6. **Monitoring Integration** - Ensures LiteLLM and AgentOps tracking work correctly

By following this test-driven development approach, the implementation will be robust, well-tested, and meet all business requirements while maintaining the highest quality standards.

**Next Steps:**
1. Set up test environment with required dependencies
2. Begin implementation with AgnoOpportunityAnalyzer using TDD
3. Progress through each phase following the roadmap
4. Continuously validate against acceptance criteria
5. Monitor coverage and performance throughout development