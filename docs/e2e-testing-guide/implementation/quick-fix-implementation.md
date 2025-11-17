# Quick Fix Implementation Guide

**Purpose:** Immediate code changes to address multi-agent consensus and performance issues
**Estimated Time:** 30 minutes
**Target Files:** `/agent_tools/monetization_agno_analyzer.py`

## 🚨 Immediate Fixes Required

### **Issue Summary:**
- Consensus Score: 42.2% (Target: ≥70%)
- Performance Benchmarks: 2/3 met
- JSON parsing failures causing default values

## 📝 Step-by-Step Implementation

### **Step 1: Add Enhanced Response Parsing**

**Location:** In `/agent_tools/monetization_agno_analyzer.py` - Add after the `__init__` method

```python
def _parse_agent_response(self, response_data):
    """Parse agent response data with robust JSON handling"""
    import json
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Handle RunOutput objects (from Agno)
        if hasattr(response_data, 'result'):
            result = response_data.result
            if isinstance(result, str):
                return json.loads(result)
            elif hasattr(result, 'content'):
                return json.loads(result.content)
            elif hasattr(result, '__dict__'):
                return vars(result)
            return result

        # Handle direct JSON strings
        if isinstance(response_data, str):
            if response_data.strip().startswith('{'):
                return json.loads(response_data)
            return {"raw_response": response_data}

        # Handle dict responses
        if isinstance(response_data, dict):
            return response_data

        # Handle other objects
        if hasattr(response_data, '__dict__'):
            return vars(response_data)

        return {}
    except (json.JSONDecodeError, AttributeError, TypeError, ValueError) as e:
        logger.warning(f"Failed to parse agent response: {e}")
        return {}
```

### **Step 2: Fix Consensus Calculation**

**Location:** Replace the existing `calculate_consensus_score` method

```python
def calculate_consensus_score(self, agent_results):
    """Calculate consensus score with improved error handling"""
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

    # Define metrics to check
    metrics = [
        'monetization_score', 'llm_monetization_score',
        'willingness_to_pay_score', 'wtp_score',
        'revenue_potential_score'
    ]

    for metric in metrics:
        values = []
        for result in parsed_results:
            if metric in result and isinstance(result[metric], (int, float)):
                values.append(result[metric])

        if len(values) >= 2:
            # Calculate standard deviation
            mean_val = sum(values) / len(values)
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)

            # Convert to consensus score (lower variance = higher consensus)
            max_variance = 2500  # Maximum possible variance for 0-100 scores
            consensus_score = max(0, (1 - variance / max_variance)) * 100
            consensus_scores.append(consensus_score)

    return sum(consensus_scores) / len(consensus_scores) if consensus_scores else 0.0
```

### **Step 3: Enhance Result Aggregation**

**Location:** Replace the existing `aggregate_agent_results` method

```python
def aggregate_agent_results(self, agent_results):
    """Aggregate agent results with improved parsing"""
    if not agent_results:
        return self._create_default_result()

    # Parse all results
    parsed_results = []
    for result in agent_results:
        parsed = self._parse_agent_response(result)
        if parsed:
            parsed_results.append(parsed)

    if not parsed_results:
        return self._create_default_result()

    # Aggregate metrics
    final_result = {
        'llm_monetization_score': self._get_average_metric(parsed_results, ['monetization_score', 'llm_monetization_score']),
        'customer_segment': self._get_most_common(parsed_results, ['customer_segment', 'segment']),
        'willingness_to_pay_score': self._get_average_metric(parsed_results, ['willingness_to_pay_score', 'wtp_score']),
        'revenue_potential_score': self._get_average_metric(parsed_results, ['revenue_potential_score']),
        'sentiment_toward_payment': self._get_most_common(parsed_results, ['sentiment', 'sentiment_toward_payment', 'payment_sentiment']),
        'urgency_level': self._get_most_common(parsed_results, ['urgency', 'urgency_level']),
        'confidence_score': min(90, 60 + len(parsed_results) * 10),  # Higher confidence with more agents
        'agent_count': len(parsed_results)
    }

    return final_result

def _get_average_metric(self, results, metric_names):
    """Get average value for metric from multiple possible field names"""
    values = []
    for result in results:
        for metric in metric_names:
            if metric in result and isinstance(result[metric], (int, float)):
                values.append(result[metric])
                break

    if not values:
        return 50.0  # Conservative default

    return sum(values) / len(values)

def _get_most_common(self, results, field_names):
    """Get most common value from multiple possible field names"""
    values = []
    for result in results:
        for field in field_names:
            if field in result and result[field]:
                values.append(result[field])
                break

    if not values:
        return "Unknown"

    # Count frequency and return most common
    from collections import Counter
    counter = Counter(values)
    return counter.most_common(1)[0][0]

def _create_default_result(self):
    """Create default result when no valid agent results"""
    return {
        'llm_monetization_score': 50.0,
        'customer_segment': "Unknown",
        'willingness_to_pay_score': 50.0,
        'revenue_potential_score': 50.0,
        'sentiment_toward_payment': "Neutral",
        'urgency_level': "Medium",
        'confidence_score': 30.0,
        'agent_count': 0
    }
```

### **Step 4: Add Performance Monitoring**

**Location:** Modify the `analyze_monetization_with_agents` method

```python
async def analyze_monetization_with_agents(self, text):
    """Analyze monetization using multiple agents with performance tracking"""
    import time
    import asyncio

    start_time = time.time()

    try:
        # Create agent tasks with individual timeouts
        tasks = [
            self.run_agent_with_timeout(self.wtp_analyzer, text, timeout=12),
            self.run_agent_with_timeout(self.segment_analyzer, text, timeout=15),
            self.run_agent_with_timeout(self.price_analyzer, text, timeout=10),
            self.run_agent_with_timeout(self.payment_analyzer, text, timeout=18)
        ]

        # Run agents concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        valid_results = [r for r in results if r is not None and not isinstance(r, Exception)]

        if len(valid_results) < 2:
            return self._create_default_result()

        # Calculate consensus and aggregate
        consensus_score = self.calculate_consensus_score(valid_results)
        final_result = self.aggregate_agent_results(valid_results)
        final_result['consensus_score'] = consensus_score
        final_result['total_analysis_time'] = time.time() - start_time

        return final_result

    except Exception as e:
        return self._create_default_result()

async def run_agent_with_timeout(self, agent, input_text, timeout=15):
    """Run individual agent with timeout protection"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        result = await asyncio.wait_for(agent.run(input_text), timeout=timeout)
        return result
    except asyncio.TimeoutError:
        logger.warning(f"Agent {agent.name} timed out after {timeout}s")
        return None
    except Exception as e:
        logger.error(f"Agent {agent.name} failed: {e}")
        return None
```

## 🧪 Quick Test

**After implementing the fixes, run:**

```bash
source .venv/bin/activate && python scripts/testing/test_agno_multi_agent_system.py
```

**Expected improvements:**
- Consensus Score: ≥70%
- No default values (50.0, "Unknown")
- Better performance consistency
- Proper JSON parsing

## 🔍 Validation Checklist

- [ ] **Parse agent responses** working correctly
- [ ] **Consensus score** ≥70%
- [ ] **No default values** in final results
- [ ] **Performance benchmarks** 3/3 met
- [ ] **JSON parsing** 100% successful

## ⚡ Quick Win vs Complete Fix

**Quick Win (30 min):** Implement the above fixes
**Complete Fix (2 hours):** Add advanced coordination and learning patterns

The quick implementation should address the core issues identified in the testing and bring the consensus score above 70%.

---

*Implementation based on analysis of `multi-agent-workflow-testing-2025-11-17.json`*
*Target: Increase consensus from 42.2% to ≥70% and fix JSON parsing issues*