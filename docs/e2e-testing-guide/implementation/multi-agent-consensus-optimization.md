# Multi-Agent System Optimization Guide

**Created:** 2025-11-17
**Purpose:** Implementation guide for addressing multi-agent consensus and performance issues
**Evidence Base:** `multi-agent-workflow-testing-2025-11-17.json`

## 🎯 Issues Identified

### 1. **Consensus Score: 42.2% (Target: ≥70%)**
- **Current State:** Poor coordination quality
- **Evidence:** Consensus scores ranging from 34-67% (`multi-agent-workflow-testing-2025-11-17.json:47-95`)
- **Root Cause:** JSON parsing issues affecting consensus calculations

### 2. **Performance Benchmarks: 2/3 met**
- **Current State:** Individual agent performance failing
- **Evidence:** `multi-agent-workflow-testing-2025-11-17.json:114-118`
- **Root Cause:** Response time variance and individual agent delays

### 3. **Team Response Parsing: JSON issues**
- **Current State:** Results showing default values (50.0, "Unknown")
- **Evidence:** `multi-agent-workflow-testing-2025-11-17.json:51-57, 67-73, 83-89, 99-105`
- **Root Cause:** Agent result aggregation not properly parsing individual responses

## 🔧 Implementation Solutions

### **Solution 1: Fix JSON Parsing in Consensus Calculator**

**File:** `/agent_tools/monetization_agno_analyzer.py`

**Issue:** Consensus calculation not properly parsing individual agent JSON responses

**Implementation:**

```python
def _parse_agent_response(self, response_data):
    """Enhanced response parsing with better JSON handling"""
    try:
        # Handle RunOutput objects
        if hasattr(response_data, 'result'):
            result = response_data.result
            if isinstance(result, str):
                return json.loads(result)
            elif hasattr(result, 'content'):
                return json.loads(result.content)
            return result

        # Handle direct JSON strings
        if isinstance(response_data, str):
            return json.loads(response_data)

        # Handle dict responses
        if isinstance(response_data, dict):
            return response_data

        return {}
    except (json.JSONDecodeError, AttributeError, TypeError) as e:
        logger.warning(f"Failed to parse agent response: {e}")
        return {}
```

### **Solution 2: Improve Inter-Agent Communication**

**File:** `/agent_tools/monetization_agno_analyzer.py`

**Issue:** Poor consensus coordination due to inadequate result aggregation

**Implementation:**

```python
def calculate_consensus_score(self, agent_results):
    """Enhanced consensus calculation with better error handling"""
    if not agent_results:
        return 0.0

    # Parse all agent responses
    parsed_results = []
    for result in agent_results:
        parsed = self._parse_agent_response(result)
        if parsed:
            parsed_results.append(parsed)

    if len(parsed_results) < 2:
        return 0.0

    # Calculate consensus for each key metric
    consensus_scores = []

    for metric in ['monetization_score', 'willingness_to_pay_score', 'revenue_potential_score']:
        values = []
        for result in parsed_results:
            if metric in result and isinstance(result[metric], (int, float)):
                values.append(result[metric])

        if values:
            # Calculate standard deviation and consensus
            mean_val = sum(values) / len(values)
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)

            # Convert to consensus score (lower variance = higher consensus)
            max_variance = 2500  # Maximum possible variance for 0-100 scores
            consensus_score = max(0, (1 - variance / max_variance)) * 100
            consensus_scores.append(consensus_score)

    return sum(consensus_scores) / len(consensus_scores) if consensus_scores else 0.0
```

### **Solution 3: Optimize Individual Agent Performance**

**File:** `/agent_tools/monetization_agno_analyzer.py`

**Issue:** Individual agents not meeting performance benchmarks

**Implementation:**

```python
async def analyze_monetization_with_agents(self, text):
    """Optimized agent coordination with better performance"""

    # Create optimized agent tasks
    tasks = [
        self.run_agent_with_timeout(self.wtp_analyzer, text, timeout=10),
        self.run_agent_with_timeout(self.segment_analyzer, text, timeout=12),
        self.run_agent_with_timeout(self.price_analyzer, text, timeout=8),
        self.run_agent_with_timeout(self.payment_analyzer, text, timeout=15)
    ]

    # Run with timeout and error handling
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"Agent coordination failed: {e}")
        return self._create_fallback_result(text)

    # Process results with better error handling
    valid_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(f"Agent {i} failed: {result}")
            continue
        if result:
            valid_results.append(result)

    # Ensure minimum results for consensus
    if len(valid_results) < 2:
        logger.warning("Insufficient valid agent results for consensus")
        return self._create_fallback_result(text)

    # Calculate consensus and final result
    consensus_score = self.calculate_consensus_score(valid_results)
    final_result = self.aggregate_agent_results(valid_results)
    final_result['consensus_score'] = consensus_score

    return final_result

async def run_agent_with_timeout(self, agent, input_text, timeout=10):
    """Run individual agent with timeout and performance tracking"""
    start_time = time.time()

    try:
        # Use asyncio.wait_for for timeout control
        result = await asyncio.wait_for(
            agent.run(input_text),
            timeout=timeout
        )

        execution_time = time.time() - start_time
        logger.info(f"Agent {agent.name} completed in {execution_time:.2f}s")

        return result

    except asyncio.TimeoutError:
        execution_time = time.time() - start_time
        logger.warning(f"Agent {agent.name} timed out after {execution_time:.2f}s")
        return None
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Agent {agent.name} failed after {execution_time:.2f}s: {e}")
        return None
```

### **Solution 4: Enhance Result Aggregation Logic**

**File:** `/agent_tools/monetization_agno_analyzer.py`

**Issue:** Default values (50.0, "Unknown") indicating aggregation failure

**Implementation:**

```python
def aggregate_agent_results(self, agent_results):
    """Enhanced result aggregation with proper parsing"""
    if not agent_results:
        return self._create_default_result()

    parsed_results = []
    for result in agent_results:
        parsed = self._parse_agent_response(result)
        if parsed:
            parsed_results.append(parsed)

    if not parsed_results:
        return self._create_default_result()

    # Aggregate metrics with weighted averaging
    final_result = {
        'llm_monetization_score': self._aggregate_metric(parsed_results, 'monetization_score'),
        'customer_segment': self._aggregate_categorical(parsed_results, 'customer_segment'),
        'willingness_to_pay_score': self._aggregate_metric(parsed_results, 'willingness_to_pay_score'),
        'revenue_potential_score': self._aggregate_metric(parsed_results, 'revenue_potential_score'),
        'sentiment_toward_payment': self._aggregate_categorical(parsed_results, 'sentiment'),
        'urgency_level': self._aggregate_categorical(parsed_results, 'urgency'),
        'confidence_score': self._calculate_confidence(parsed_results),
        'agent_count': len(parsed_results)
    }

    return final_result

def _aggregate_metric(self, results, metric_name):
    """Aggregate numerical metrics with outlier detection"""
    values = []
    for result in results:
        if metric_name in result and isinstance(result[metric_name], (int, float)):
            values.append(result[metric_name])

    if not values:
        return 50.0  # Conservative default

    # Remove outliers using IQR method
    values.sort()
    n = len(values)
    q1 = values[n // 4]
    q3 = values[3 * n // 4]
    iqr = q3 - q1

    filtered_values = [v for v in values if q1 - 1.5 * iqr <= v <= q3 + 1.5 * iqr]

    if not filtered_values:
        return sum(values) / len(values)

    return sum(filtered_values) / len(filtered_values)

def _aggregate_categorical(self, results, field_name):
    """Aggregate categorical fields using majority voting"""
    values = []
    for result in results:
        # Handle different field name variations
        for field in [field_name, f"{field_name}_score", f"{field_name}_level"]:
            if field in result and result[field]:
                values.append(result[field])
                break

    if not values:
        return "Unknown"

    # Count frequency and return most common
    from collections import Counter
    counter = Counter(values)
    return counter.most_common(1)[0][0]
```

## 📋 Implementation Checklist

### **Phase 1: Core Fixes (Immediate)**

- [ ] **File:** `/agent_tools/monetization_agno_analyzer.py`
  - [ ] Add `_parse_agent_response()` method
  - [ ] Update `calculate_consensus_score()` with better error handling
  - [ ] Implement `run_agent_with_timeout()` for performance
  - [ ] Enhance `aggregate_agent_results()` logic
  - [ ] Add `_aggregate_metric()` and `_aggregate_categorical()` helpers

### **Phase 2: Performance Optimization (Week 1)**

- [ ] **File:** `/agent_tools/monetization_agno_analyzer.py`
  - [ ] Implement timeout controls for each agent
  - [ ] Add performance monitoring and logging
  - [ ] Optimize result aggregation algorithms
  - [ ] Add fallback mechanisms for failed agents

### **Phase 3: Advanced Coordination (Week 2)**

- [ ] **File:** `/agent_tools/monetization_agno_analyzer.py`
  - [ ] Implement weighted consensus based on agent confidence
  - [ ] Add conflict resolution for disagreeing agents
  - [ ] Create adaptive consensus thresholds
  - [ ] Implement learning from successful consensus patterns

## 🧪 Testing Validation

**Test Command:**
```bash
source .venv/bin/activate && python scripts/testing/test_agno_multi_agent_system.py
```

**Expected Results After Fix:**
- Consensus Score: ≥70% (target: 70%+)
- Performance Benchmarks: 3/3 met
- No default values in results
- JSON parsing success: 100%

## 📊 Success Metrics

### **Before Fix:**
- Consensus Score: 42.2%
- Performance Benchmarks: 2/3 met
- Results: Default values (50.0, "Unknown")

### **After Fix (Target):**
- Consensus Score: ≥70%
- Performance Benchmarks: 3/3 met
- Results: Properly aggregated values
- JSON Parsing: 100% success

## 🔍 Verification Steps

1. **Implement fixes** in `/agent_tools/monetization_agno_analyzer.py`
2. **Run test suite:** `python scripts/testing/test_agno_multi_agent_system.py`
3. **Verify consensus score** ≥70%
4. **Check performance benchmarks** 3/3 met
5. **Validate result quality** (no default values)
6. **Monitor AgentOps dashboard** for cost tracking

---

*Implementation Guide created based on evidence from multi-agent workflow testing*
*All changes target the specific issues identified in `multi-agent-workflow-testing-2025-11-17.json`*