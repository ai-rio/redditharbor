# JSON-Repair Integration for Multi-Agent System

**Great News:** RedditHarbor already has `json-repair>=0.24.0` installed!
**Purpose:** Use existing json-repair library to fix agent response parsing issues
**Implementation Time:** 20 minutes

## 🛠️ **Existing JSON-Repair Usage**

The library is already successfully used in:
- `agent_tools/llm_profiler_enhanced.py:15` - `from json_repair import repair_json`
- `agent_tools/llm_profiler.py:15` - `from json_repair import repair_json`

## 🔧 **Enhanced Agent Response Parsing with JSON-Repair**

**File:** `/agent_tools/monetization_agno_analyzer.py`

**Add to imports:**
```python
from json_repair import repair_json
```

### **Solution: Robust Response Parser**

```python
def _parse_agent_response(self, response_data):
    """Parse agent response with json-repair for robust LLM JSON handling"""
    import json
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Handle Agno RunOutput objects
        if hasattr(response_data, 'result'):
            result = response_data.result
            if isinstance(result, str):
                # Use json-repair for LLM responses
                repaired_json = repair_json(result)
                return json.loads(repaired_json)
            elif hasattr(result, 'content'):
                repaired_json = repair_json(result.content)
                return json.loads(repaired_json)
            elif hasattr(result, '__dict__'):
                return vars(result)
            return result

        # Handle direct JSON strings
        if isinstance(response_data, str):
            if response_data.strip().startswith('{'):
                # Use json-repair for LLM responses
                repaired_json = repair_json(response_data)
                return json.loads(repaired_json)
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

### **Enhanced Consensus Calculation**

```python
def calculate_consensus_score(self, agent_results):
    """Calculate consensus score with robust error handling and json-repair"""
    if not agent_results:
        return 0.0

    # Parse all agent responses using robust parser
    parsed_results = []
    for i, result in enumerate(agent_results):
        parsed = self._parse_agent_response(result)
        if parsed:
            parsed_results.append(parsed)
            logger.info(f"Agent {i} parsed successfully: {list(parsed.keys())}")
        else:
            logger.warning(f"Agent {i} failed to parse")

    if len(parsed_results) < 2:
        logger.warning(f"Insufficient parsed results: {len(parsed_results)}/4")
        return 0.0

    # Calculate consensus for each key metric
    consensus_scores = []

    # Define all possible metric names (handles variations from different agents)
    metric_mappings = {
        'monetization_score': ['monetization_score', 'llm_monetization_score', 'score', 'value'],
        'willingness_to_pay_score': ['willingness_to_pay_score', 'willingness_score', 'wtp_score', 'wtp'],
        'revenue_potential_score': ['revenue_potential_score', 'revenue_score', 'potential_score'],
        'customer_segment': ['customer_segment', 'segment', 'market_segment', 'classification'],
        'sentiment_toward_payment': ['sentiment_toward_payment', 'sentiment', 'payment_sentiment', 'attitude']
    }

    for primary_metric, possible_names in metric_mappings.items():
        values = []
        for result in parsed_results:
            for metric_name in possible_names:
                if metric_name in result and isinstance(result[metric_name], (int, float)):
                    values.append(result[metric_name])
                    break

        if len(values) >= 2:
            # Calculate standard deviation
            mean_val = sum(values) / len(values)
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)

            # Convert to consensus score (lower variance = higher consensus)
            max_variance = 2500  # Maximum possible variance for 0-100 scores
            consensus_score = max(0, (1 - variance / max_variance)) * 100
            consensus_scores.append(consensus_score)

            logger.info(f"Consensus for {primary_metric}: {consensus_score:.1f}% from {values}")

    final_consensus = sum(consensus_scores) / len(consensus_scores) if consensus_scores else 0.0
    logger.info(f"Final consensus score: {final_consensus:.1f}%")

    return final_consensus
```

### **Enhanced Result Aggregation**

```python
def aggregate_agent_results(self, agent_results):
    """Aggregate agent results with robust field mapping and json-repair"""
    if not agent_results:
        return self._create_default_result()

    # Parse all results using robust parser
    parsed_results = []
    for i, result in enumerate(agent_results):
        parsed = self._parse_agent_response(result)
        if parsed:
            parsed_results.append(parsed)
            logger.info(f"Agent {i+1} results: {list(parsed.keys())}")

    if not parsed_results:
        logger.warning("No valid agent results parsed, returning default")
        return self._create_default_result()

    # Enhanced field mapping with all possible variations
    field_mappings = {
        'llm_monetization_score': ['monetization_score', 'llm_monetization_score', 'score', 'value', 'rating'],
        'customer_segment': ['customer_segment', 'segment', 'market_segment', 'classification', 'category'],
        'willingness_to_pay_score': ['willingness_to_pay_score', 'willingness_score', 'wtp_score', 'wtp', 'willingness'],
        'revenue_potential_score': ['revenue_potential_score', 'revenue_score', 'potential_score', 'revenue'],
        'sentiment_toward_payment': ['sentiment_toward_payment', 'sentiment', 'payment_sentiment', 'attitude', 'feeling'],
        'urgency_level': ['urgency_level', 'urgency', 'priority', 'time_sensitivity']
    }

    # Aggregate metrics with robust field mapping
    final_result = {}

    for target_field, possible_names in field_mappings.items():
        if target_field in ['customer_segment', 'sentiment_toward_payment', 'urgency_level']:
            # Categorical fields - use most common
            final_result[target_field] = self._get_most_common_robust(parsed_results, possible_names)
        else:
            # Numerical fields - use average
            final_result[target_field] = self._get_average_robust(parsed_results, possible_names)

    # Add metadata
    final_result.update({
        'confidence_score': min(95, 60 + len(parsed_results) * 10),
        'agent_count': len(parsed_results),
        'parsing_success_rate': len(parsed_results) / len(agent_results) * 100
    })

    logger.info(f"Final aggregated result: {final_result}")
    return final_result

def _get_most_common_robust(self, results, field_names):
    """Get most common value with multiple field name fallbacks"""
    values = []
    for result in results:
        for field_name in field_names:
            if field_name in result and result[field_name]:
                values.append(result[field_name])
                break

    if not values:
        defaults = {
            'customer_segment': 'Unknown',
            'sentiment_toward_payment': 'Neutral',
            'urgency_level': 'Medium'
        }
        return defaults.get(field_names[0], 'Unknown')

    # Normalize values (handle B2B vs B2B, etc.)
    normalized_values = []
    for value in values:
        if isinstance(value, str):
            # Normalize segment values
            value = value.lower().replace('_', '')
            if value in ['b2b', 'business']:
                normalized_values.append('B2B')
            elif value in ['b2c', 'consumer']:
                normalized_values.append('B2C')
            elif value in ['mixed', 'hybrid']:
                normalized_values.append('Mixed')
            elif value in ['positive', 'pos', 'favorable']:
                normalized_values.append('Positive')
            elif value in ['negative', 'neg', 'unfavorable']:
                normalized_values.append('Negative')
            elif value in ['neutral', 'neu', 'balanced']:
                normalized_values.append('Neutral')
            elif value in ['low', 'critical']:
                normalized_values.append('Low')
            elif value in ['medium', 'med', 'moderate']:
                normalized_values.append('Medium')
            elif value in ['high', 'urgent']:
                normalized_values.append('High')
            else:
                normalized_values.append(value.title())
        else:
            normalized_values.append(value)

    from collections import Counter
    return Counter(normalized_values).most_common(1)[0][0]

def _get_average_robust(self, results, field_names):
    """Get average value with multiple field name fallbacks"""
    values = []
    for result in results:
        for field_name in field_names:
            if field_name in result and isinstance(result[field_name], (int, float)):
                # Ensure values are in 0-100 range
                value = max(0, min(100, result[field_name]))
                values.append(value)
                break

    if not values:
        return 50.0  # Conservative default

    # Remove outliers using IQR method
    if len(values) >= 3:
        values.sort()
        n = len(values)
        q1 = values[n // 4]
        q3 = values[3 * n // 4]
        iqr = q3 - q1

        filtered_values = [v for v in values if q1 - 1.5 * iqr <= v <= q3 + 1.5 * iqr]
        if filtered_values:
            return sum(filtered_values) / len(filtered_values)

    return sum(values) / len(values)
```

## 🎯 **Integration Steps**

### **Step 1: Add JSON-Repair Import**
```python
from json_repair import repair_json
```

### **Step 2: Replace Existing Parsing Methods**
- Replace any basic JSON parsing with the `_parse_agent_response()` method
- Update consensus calculation to use robust field mapping
- Enhance result aggregation with multiple fallback field names

### **Step 3: Test the Fix**
```bash
source .venv/bin/activate && python scripts/testing/test_agno_multi_agent_system.py
```

## 📊 **Expected Results**

### **Before JSON-Repair Integration:**
- Consensus Score: 42.2%
- JSON parsing failures: High
- Default values: "Unknown", 50.0
- Field name mismatches: Common

### **After JSON-Repair Integration:**
- Consensus Score: 80-90% (significant improvement)
- JSON parsing: 100% success with repair
- Proper values: Based on actual agent analysis
- Field mapping: Robust with multiple fallbacks

## 🚀 **Benefits of JSON-Repair Integration**

1. **Handles LLM JSON Quirks:** Fixes missing quotes, extra commas, trailing commas
2. **Robust Field Mapping:** Handles variations in agent output field names
3. **Graceful Degradation:** Falls back to defaults when agents fail
4. **Better Logging:** Detailed logging of parsing success/failure
5. **Outlier Detection:** Removes outlier values for better consensus

## ⚡ **Why This Works Better**

The `json-repair` library is specifically designed for LLM responses and can handle:
- Missing quotes around strings
- Extra commas in arrays/objects
- Trailing commas
- Malformed escape sequences
- Mixed content (JSON + text)

This is perfect for multi-agent systems where each agent might return slightly different JSON formats.

---

*Leverages existing `json-repair>=0.24.0` installation for robust multi-agent coordination*