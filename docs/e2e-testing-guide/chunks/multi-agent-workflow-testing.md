# Multi-Agent Workflow Testing

<div style="text-align: center; margin: 20px 0;">
  <h1 style="color: #FF6B35;">🤖 Multi-Agent Workflow Testing</h1>
  <p style="color: #004E89; font-size: 1.2em;">Deep testing of Agno multi-agent coordination system</p>
</div>

---

## 📋 Overview

This **Multi-Agent Workflow Testing** guide provides comprehensive testing scenarios for RedditHarbor's Agno multi-agent framework. The testing validates the 4-agent coordination system that powers opportunity analysis: WTP Analyst, Market Segment Analyst, Price Point Analyst, and Payment Behavior Analyst.

**What you'll test:**
1. 🤖 **Agent Coordination** - How the 4 agents work together
2. 💰 **WTP Scoring** - Willingness-to-pay analysis accuracy
3. 🎯 **Customer Segmentation** - B2B vs B2C classification
4. 💵 **Price Point Analysis** - Optimal pricing recommendations
5. 💳 **Payment Behavior** - Payment preference analysis

**Time Investment:** 20 minutes
**Expected Performance:** ~52 seconds per analysis
**Success Threshold:** 85% agent coordination accuracy

---

## 🚀 Quick Start Multi-Agent Testing

### **Step 1: Agno Framework Validation (5 minutes)**

```bash
# Test Agno analyzer factory function
source .venv/bin/activate && python -c "
from agent_tools.monetization_agno_analyzer import create_monetization_analyzer

# Test factory pattern
agno_analyzer = create_monetization_analyzer(framework='agno')
dspy_analyzer = create_monetization_analyzer(framework='dspy')

print(f'✅ Agno Analyzer: {agno_analyzer is not None}')
print(f'✅ DSPy Analyzer: {dspy_analyzer is not None}')
print(f'✅ Factory Pattern: Working correctly')
"

# Test basic agent initialization
source .venv/bin/activate && python -c "
from agent_tools.monetization_agno_analyzer import create_monetization_analyzer
analyzer = create_monetization_analyzer()

# Test that agents are properly initialized
print(f'Analyzer type: {type(analyzer).__name__}')
print(f'Framework: {getattr(analyzer, \"framework\", \"unknown\")}')
print('✅ Multi-agent system initialized successfully')
"
```

### **Step 2: Individual Agent Testing (8 minutes)**

```bash
# Test WTP Analysis Agent
source .venv/bin/activate && python -c "
from agent_tools.monetization_agno_analyzer import create_monetization_analyzer
analyzer = create_monetization_analyzer()

# Test WTP scoring
result = analyzer.analyze(
    text='Looking for expense tracking software for our 15-person consulting firm. Budget around \$150/month.',
    subreddit='smallbusiness'
)

print(f'✅ WTP Score: {result.willingness_to_pay_score}/100')
print(f'✅ Customer Segment: {result.customer_segment}')
print(f'✅ Price Sensitivity: {result.price_sensitivity}')
print(f'✅ Market Segment: {result.market_segment}')

# Validate WTP score is reasonable (should be high for this text)
wtp_reasonable = result.willingness_to_pay_score > 60
segment_reasonable = result.customer_segment == 'B2B'
print(f'✅ WTP Analysis Quality: {\"Good\" if wtp_reasonable and segment_reasonable else \"Needs Review\"}')
"
```

### **Step 3: Agent Coordination Testing (7 minutes)**

```bash
# Test multi-agent workflow with complex scenario
source .venv/bin/activate && python -c "
import asyncio
from agent_tools.monetization_agno_analyzer import create_monetization_analyzer

analyzer = create_monetization_analyzer()

# Test scenarios for different agent coordination
test_cases = [
    {
        'text': 'As a freelance designer, I need project management tool under \$50/month that integrates with QuickBooks.',
        'subreddit': 'freelance',
        'expected_segment': 'B2C',
        'expected_wtp_range': (40, 70)
    },
    {
        'text': 'Our startup needs CRM solution for 50 employees. Willing to pay \$500/month for enterprise features.',
        'subreddit': 'startups',
        'expected_segment': 'B2B',
        'expected_wtp_range': (70, 95)
    }
]

for i, case in enumerate(test_cases, 1):
    print(f'--- Test Case {i} ---')
    result = analyzer.analyze(text=case['text'], subreddit=case['subreddit'])

    segment_match = result.customer_segment == case['expected_segment']
    wtp_in_range = case['expected_wtp_range'][0] <= result.willingness_to_pay_score <= case['expected_wtp_range'][1]

    print(f'Segment: {result.customer_segment} ({\"✅\" if segment_match else \"❌\"})')
    print(f'WTP Score: {result.willingness_to_pay_score} ({\"✅\" if wtp_in_range else \"❌\"})')
    print(f'Price Sensitivity: {result.price_sensitivity}')
    print(f'Market Segment: {result.market_segment}')
    print()
"
```

---

## 📊 Multi-Agent Performance Analysis

### **Agent Performance Metrics**

| Agent | Expected Performance | Validation Method |
|-------|---------------------|-------------------|
| **WTP Analyst** | Scores 0-100, logical consistency | Compare scores against expected ranges |
| **Market Segment Analyst** | B2B/B2C classification accuracy | Verify segment matches context |
| **Price Point Analyst** | Reasonable price recommendations | Check price sensitivity and ranges |
| **Payment Behavior Analyst** | Payment preference detection | Validate behavior patterns |

### **Performance Testing Commands**

```bash
# Test multi-agent performance with timing
source .venv/bin/activate && python -c "
import time
from agent_tools.monetization_agno_analyzer import create_monetization_analyzer

analyzer = create_monetization_analyzer()

# Performance test with multiple concurrent analyses
test_texts = [
    'Small business needs accounting software',
    'Freelancer wants invoicing tool',
    'Enterprise requires CRM solution',
    'Startup needs project management',
    'Individual wants budget tracking app'
]

start_time = time.time()
results = []

for text in test_texts:
    result_start = time.time()
    analysis = analyzer.analyze(text=text, subreddit='productivity')
    result_time = time.time() - result_start

    results.append({
        'text': text[:30] + '...',
        'wtp_score': analysis.willingness_to_pay_score,
        'segment': analysis.customer_segment,
        'time': result_time
    })

total_time = time.time() - start_time
avg_time = total_time / len(test_texts)

print(f'📊 Multi-Agent Performance Results:')
print(f'Total analyses: {len(results)}')
print(f'Total time: {total_time:.2f}s')
print(f'Average time per analysis: {avg_time:.2f}s')
print(f'Expected: ~52s per analysis')
print(f'Performance: {\"✅ Good\" if avg_time < 60 else \"⚠️  Slow\" if avg_time < 90 else \"❌ Too Slow\"}')
"
```

### **Agent Coordination Quality Assessment**

```bash
# Test agent coordination quality
source .venv/bin/activate && python -c "
from agent_tools.monetization_agno_analyzer import create_monetization_analyzer

analyzer = create_monetization_analyzer()

# Quality test scenarios
quality_tests = [
    {
        'scenario': 'High-value B2B opportunity',
        'text': 'Enterprise company needs comprehensive ERP system for 500 employees. Budget \$10,000/month.',
        'subreddit': 'sysadmin',
        'expectations': {
            'wtp_score': (85, 100),
            'segment': 'B2B',
            'price_sensitivity': 'low'
        }
    },
    {
        'scenario': 'Low-cost B2C opportunity',
        'text': 'Student looking for free note-taking app with basic features.',
        'subreddit': 'students',
        'expectations': {
            'wtp_score': (0, 30),
            'segment': 'B2C',
            'price_sensitivity': 'high'
        }
    }
]

coordination_scores = []

for test in quality_tests:
    result = analyzer.analyze(text=test['text'], subreddit=test['subreddit'])
    exp = test['expectations']

    # Score each agent's performance
    wtp_score = 1.0 if exp['wtp_score'][0] <= result.willingness_to_pay_score <= exp['wtp_score'][1] else 0.0
    segment_score = 1.0 if result.customer_segment == exp['segment'] else 0.0
    price_score = 1.0 if result.price_sensitivity == exp['price_sensitivity'] else 0.0

    test_score = (wtp_score + segment_score + price_score) / 3
    coordination_scores.append(test_score)

    print(f'{test[\"scenario\"]}:')
    print(f'  WTP Score: {result.willingness_to_pay_score} ({\"✅\" if wtp_score else \"❌\"})')
    print(f'  Segment: {result.customer_segment} ({\"✅\" if segment_score else \"❌\"})')
    print(f'  Price Sensitivity: {result.price_sensitivity} ({\"✅\" if price_score else \"❌\"})')
    print(f'  Coordination Score: {test_score:.1%}')
    print()

overall_coordination = sum(coordination_scores) / len(coordination_scores)
print(f'🎯 Overall Agent Coordination: {overall_coordination:.1%}')
print(f'Quality: {\"✅ Excellent\" if overall_coordination >= 0.85 else \"⚠️  Good\" if overall_coordination >= 0.70 else \"❌ Needs Improvement\"}')
"
```

---

## 🧪 Advanced Agent Testing Scenarios

### **Scenario 1: Complex Multi-Context Analysis**

```bash
# Test agents with complex, multi-layered opportunities
source .venv/bin/activate && python -c "
from agent_tools.monetization_agno_analyzer import create_monetization_analyzer

analyzer = create_monetization_analyzer()

complex_scenarios = [
    {
        'name': 'Hybrid B2B2C Model',
        'text': 'Building a platform where consultants can offer services to small businesses. Need subscription management and payment processing. Target \$100/month from consultants, who charge \$500/month to businesses.',
        'subreddit': 'Entrepreneur',
        'analysis_points': ['Should recognize complex revenue model', 'Multiple customer segments', 'Platform business model']
    },
    {
        'name': 'Enterprise with Free Tier',
        'text': 'SaaS company offering free tier for startups under 5 employees, then \$50/month for growing teams, and enterprise custom pricing. Need user management and billing automation.',
        'subreddit': 'saas',
        'analysis_points': ['Tiered pricing structure', 'Startup focus', 'Enterprise scalability']
    }
]

for scenario in complex_scenarios:
    print(f'=== {scenario[\"name\"]} ===')
    result = analyzer.analyze(text=scenario['text'], subreddit=scenario['subreddit'])

    print(f'WTP Score: {result.willingness_to_pay_score}')
    print(f'Customer Segment: {result.customer_segment}')
    print(f'Market Segment: {result.market_segment}')
    print(f'Price Sensitivity: {result.price_sensitivity}')

    # Check if agents detected complexity
    complexity_detected = result.willingness_to_pay_score > 50  # Should recognize high value
    print(f'Complexity Detected: {\"✅\" if complexity_detected else \"❌\"}')
    print(f'Key Insights: High-value opportunity with multiple revenue streams')
    print()
"
```

### **Scenario 2: Edge Case Testing**

```bash
# Test agents with edge cases and ambiguous scenarios
source .venv/bin/activate && python -c "
from agent_tools.monetization_agno_analyzer import create_monetization_analyzer

analyzer = create_monetization_agno_analyzer()

edge_cases = [
    {
        'name': 'Very Low Budget',
        'text': 'Need completely free solution for personal use. No budget whatsoever.',
        'subreddit': 'frugal',
        'expected_wtp': (0, 20)
    },
    {
        'name': 'Very High Budget',
        'text': 'Fortune 500 company needs enterprise solution. Money is no object, quality is priority.',
        'subreddit': 'CIO',
        'expected_wtp': (90, 100)
    },
    {
        'name': 'Ambiguous Business Model',
        'text': 'Looking for software solution. Not sure if for personal use or business yet.',
        'subreddit': 'casual',
        'expected_wtp': (30, 70)  # Wide range acceptable
    }
]

for case in edge_cases:
    print(f'--- Edge Case: {case[\"name\"]} ---')
    result = analyzer.analyze(text=case['text'], subreddit=case['subreddit'])

    wtp_in_expected = case['expected_wtp'][0] <= result.willingness_to_pay_score <= case['expected_wtp'][1]

    print(f'Text: {case[\"text\"][:60]}...')
    print(f'WTP Score: {result.willingness_to_pay_score} ({\"✅\" if wtp_in_expected else \"❌\"})')
    print(f'Segment: {result.customer_segment}')
    print(f'Expected Range: {case[\"expected_wtp\"]}')
    print()
"
```

### **Scenario 3: Consistency Testing**

```bash
# Test agent consistency across similar inputs
source .venv/bin/activate && python -c "
from agent_tools.monetization_agno_analyzer import create_monetization_analyzer

analyzer = create_monetization_analyzer()

# Consistency test - similar requests should get similar scores
similar_requests = [
    'Need project management tool for small business',
    'Looking for PM software for our company',
    'Small business needs project tracking solution',
    'Our team wants project organization software'
]

results = []
for request in similar_requests:
    result = analyzer.analyze(text=request, subreddit='smallbusiness')
    results.append({
        'text': request,
        'wtp': result.willingness_to_pay_score,
        'segment': result.customer_segment,
        'price_sensitivity': result.price_sensitivity
    })

# Analyze consistency
wtp_scores = [r['wtp'] for r in results]
segments = [r['segment'] for r in results]

wtp_variance = max(wtp_scores) - min(wtp_scores)
segment_consistency = len(set(segments)) == 1  # All segments should be the same

print(f'🎯 Consistency Analysis Results:')
print(f'WTP Score Range: {min(wtp_scores):.1f} - {max(wtp_scores):.1f}')
print(f'WTP Variance: {wtp_variance:.1f} ({\"✅\" if wtp_variance < 20 else \"⚠️\" if wtp_variance < 40 else \"❌\"})')
print(f'Segment Consistency: {\"✅\" if segment_consistency else \"❌\"}')
print(f'Consistent Segment: {segments[0] if segment_consistency else \"Variable\"}')

for i, result in enumerate(results, 1):
    print(f'{i}. WTP: {result[\"wtp\"]:.1f}, Segment: {result[\"segment\"]}')
"
```

---

## 📈 Monitoring Multi-Agent Performance

### **Real-time Agent Performance Dashboard**

```bash
# Create a performance monitoring function
monitor_agent_performance() {
    echo "🤖 Agno Multi-Agent Performance Monitor"
    echo "======================================"

    source .venv/bin/activate && python -c "
import time
import statistics
from agent_tools.monetization_agno_analyzer import create_monetization_analyzer

analyzer = create_monetization_analyzer()

# Test performance with sample data
test_samples = [
    ('Small business needs CRM', 'smallbusiness'),
    ('Freelancer wants time tracking', 'freelance'),
    ('Startup needs accounting software', 'startups'),
    ('Enterprise requires ERP system', 'sysadmin'),
    ('Individual wants budget app', 'personalfinance')
]

times = []
wtp_scores = []
segments = []

print('Running performance tests...')
for text, subreddit in test_samples:
    start = time.time()
    result = analyzer.analyze(text=text, subreddit=subreddit)
    duration = time.time() - start

    times.append(duration)
    wtp_scores.append(result.willingness_to_pay_score)
    segments.append(result.customer_segment)

    print(f'  {text[:25]}... {duration:.2f}s (WTP: {result.willingness_to_pay_score})')

# Performance metrics
avg_time = statistics.mean(times)
avg_wtp = statistics.mean(wtp_scores)
segment_dist = {seg: segments.count(seg) for seg in set(segments)}

print(f'\\n📊 Performance Metrics:')
print(f'  Average Analysis Time: {avg_time:.2f}s')
print(f'  Time Range: {min(times):.2f}s - {max(times):.2f}s')
print(f'  Average WTP Score: {avg_wtp:.1f}')
print(f'  Segment Distribution: {segment_dist}')
print(f'  Performance Status: {\"✅ Optimal\" if avg_time < 45 else \"⚠️  Acceptable\" if avg_time < 75 else \"❌ Needs Optimization\"}')
"
}

# Usage: monitor_agent_performance
```

### **Agent Health Check**

```bash
# Comprehensive agent health check
source .venv/bin/activate && python -c "
from agent_tools.monetization_agno_analyzer import create_monetization_analyzer

print('🏥 Agno Multi-Agent Health Check')
print('================================')

try:
    # Test system initialization
    analyzer = create_monetization_analyzer()
    print('✅ System Initialization: OK')

    # Test basic functionality
    result = analyzer.analyze(
        text='Test analysis for health check',
        subreddit='test'
    )

    # Validate result structure
    required_fields = ['willingness_to_pay_score', 'customer_segment', 'price_sensitivity', 'market_segment']
    missing_fields = [field for field in required_fields if not hasattr(result, field)]

    if not missing_fields:
        print('✅ Result Structure: Complete')
    else:
        print(f'❌ Result Structure: Missing {missing_fields}')

    # Validate data ranges
    wtp_valid = 0 <= result.willingness_to_pay_score <= 100
    segment_valid = result.customer_segment in ['B2B', 'B2C']

    print(f'✅ WTP Score Range: {\"Valid\" if wtp_valid else \"Invalid\"} ({result.willingness_to_pay_score})')
    print(f'✅ Customer Segment: {\"Valid\" if segment_valid else \"Invalid\"} ({result.customer_segment})')

    # Overall health
    overall_health = not missing_fields and wtp_valid and segment_valid
    print(f'\\n🎯 Overall Agent Health: {\"✅ Healthy\" if overall_health else \"❌ Unhealthy\"}')

except Exception as e:
    print(f'❌ Agent Health Check Failed: {e}')
"
```

---

## 🎯 Success Indicators

### **When Multi-Agent Testing is Successful:**

1. **✅ Factory Pattern Working**: Both Agno and DSPy analyzers can be created
2. **✅ Agent Coordination**: 4 agents work together seamlessly
3. **✅ Performance Targets**: Analysis time ~52 seconds (±20 seconds)
4. **✅ Accuracy Metrics**: 85%+ coordination accuracy across test cases
5. **✅ Consistency**: Similar inputs produce consistent outputs

### **Expected Performance Baselines:**

| Metric | Target | Acceptable Range |
|--------|--------|------------------|
| **Analysis Time** | 52 seconds | 40-75 seconds |
| **WTP Score Accuracy** | 85% | 70-90% |
| **Segment Classification** | 90% | 80-95% |
| **Coordination Quality** | 85% | 70-90% |
| **Consistency Score** | 90% | 80-95% |

### **Troubleshooting Common Issues:**

#### **❌ Slow Analysis Performance**
```bash
# Check system resources
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)"
echo "Memory: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"

# Check API rate limits
python -c "
import os
print(f'AgentOps configured: {bool(os.getenv(\"AGENTOPS_API_KEY\"))}')
print(f'OpenRouter configured: {bool(os.getenv(\"OPENROUTER_API_KEY\"))}')
"
```

#### **❌ Inconsistent Results**
```bash
# Test with standardized inputs
source .venv/bin/activate && python -c "
from agent_tools.monetization_agno_analyzer import create_monetization_analyzer

analyzer = create_monetization_analyzer()

# Run same test multiple times
test_text = 'Small business needs accounting software'
results = []
for i in range(3):
    result = analyzer.analyze(text=test_text, subreddit='smallbusiness')
    results.append(result.willingness_to_pay_score)
    print(f'Run {i+1}: {result.willingness_to_pay_score}')

print(f'Variance: {max(results) - min(results):.1f} (lower is better)')
"
```

#### **❌ Agent Import Errors**
```bash
# Verify installation
source .venv/bin/activate && python -c "
try:
    import agno
    print('✅ Agno installed')
except ImportError:
    print('❌ Agno not installed - run: pip install agno')

try:
    from agent_tools.monetization_agno_analyzer import create_monetization_analyzer
    print('✅ Agent tools available')
except ImportError as e:
    print(f'❌ Agent tools error: {e}')
"
```

---

## 📚 Additional Resources

### **Related Documentation:**
- **[Integration Validation Quickstart](./integration-validation-quickstart.md)** - Basic integration testing
- **[Evidence-Based Profiling Testing](./evidence-based-profiling-testing.md)** - AI profiling validation
- **[MCP Integration Testing](./mcp-integration-testing.md)** - Jina hybrid client testing
- **[Production Pipeline Testing](./production-pipeline-testing.md)** - End-to-end production testing

### **Quick Reference Commands:**
```bash
# Quick agent test
python -c "from agent_tools.monetization_agno_analyzer import create_monetization_analyzer; print('✅ Agno ready')"

# Performance test
time python -c "from agent_tools.monetization_agno_analyzer import create_monetization_analyzer; analyzer = create_monetization_analyzer(); result = analyzer.analyze('test', 'test')"

# Consistency test
monitor_agent_performance
```

---

<div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #F5F5F5;">
  <p style="color: #666; font-size: 0.9em;">
    Continue with <a href="./evidence-based-profiling-testing.md" style="color: #004E89; font-weight: bold;">Evidence-Based Profiling Testing</a> to validate AI profiling integration! 🧠
  </p>
</div>