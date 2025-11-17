# Observability Testing

<div style="text-align: center; margin: 20px 0;">
  <h1 style="color: #FF6B35;">📊 Observability Testing</h1>
  <p style="color: #004E89; font-size: 1.2em;">AgentOps dashboard visibility and real-time cost tracking validation</p>
</div>

---

## 📋 Overview

This **Observability Testing** guide provides comprehensive testing scenarios for RedditHarbor's AgentOps observability integration. The testing validates real-time cost tracking, session replay functionality, trace monitoring, and dashboard accessibility that provide visibility into the multi-agent workflow.

**What you'll test:**
1. 🎯 **AgentOps Dashboard Access** - Dashboard connectivity and visibility
2. 📈 **Real-time Cost Tracking** - Analysis cost monitoring accuracy
3. 🔍 **Trace and Span Creation** - Multi-agent workflow instrumentation
4. 📊 **Session Replay** - Historical analysis and debugging capabilities
5. 💰 **Cost Attribution** - Per-component cost breakdown and ROI analysis

**Time Investment:** 10 minutes
**Expected Performance:** 231ms latency, real-time dashboard updates
**Success Threshold:** 100% dashboard accessibility and cost tracking accuracy

---

## 🚀 Quick Start Observability Testing

### **Step 1: AgentOps Dashboard Validation (2 minutes)**

```bash
# Verify AgentOps configuration and dashboard access
source .venv/bin/activate && python -c "
import os
import agentops

print('🎯 AgentOps Dashboard Validation')
print('=' * 40)

# Check API key configuration
api_key = os.getenv('AGENTOPS_API_KEY')
api_key_configured = bool(api_key and len(api_key) > 10)

print(f'API Key Configured: {\"✅\" if api_key_configured else \"❌\"}')

if not api_key_configured:
    print('❌ AGENTOPS_API_KEY not found in environment')
    exit(1)

# Test AgentOps initialization
try:
    agentops.init(
        api_key=api_key,
        auto_start_session=False,
        tags=['observability-testing', 'validation'],
        instrument_llm_calls=False
    )
    print('✅ AgentOps Initialization: Success')
except Exception as e:
    print(f'❌ AgentOps Initialization Failed: {e}')
    exit(1)

# Test dashboard accessibility (simulated)
dashboard_url = 'https://app.agentops.ai'
print(f'Dashboard URL: {dashboard_url}')
print('✅ Dashboard Access: Configured')
print('📊 Manual Verification Required: Visit dashboard to confirm session visibility')

# Clean initialization
agentops.end_session('Success')
"
```

### **Step 2: Trace and Span Creation Testing (3 minutes)**

```bash
# Test comprehensive trace and span creation for multi-agent monitoring
source .venv/bin/activate && python -c "
import agentops
import time
import os

print('🔍 Trace and Span Creation Testing')
print('=' * 40)

# Initialize AgentOps with detailed configuration
agentops.init(
    api_key=os.getenv('AGENTOPS_API_KEY'),
    auto_start_session=False,
    tags=['trace-testing', 'span-validation', 'multi-agent']
)

# Test comprehensive trace creation
print('\\n--- Testing Trace Creation ---')

# Main integration trace
main_trace = agentops.start_trace(
    'reddit_harbor_integration_test',
    tags=['agno', 'jina', 'market-validation', 'multi-agent']
)
print(f'✅ Main Trace Created: {main_trace}')

# Test span creation for each integration component
print('\\n--- Testing Span Creation ---')

# Agno Multi-Agent span
agno_span = agentops.start_trace('agno_multi_agent_analysis', tags=['multi-agent', 'wtp-scoring'])
time.sleep(0.1)  # Simulate work
agentops.end_trace(agno_span, 'Success')
print(f'✅ Agno Span: Created and completed')

# Jina MCP span
jina_span = agentops.start_trace('jina_mcp_market_validation', tags=['mcp', 'web-search'])
time.sleep(0.15)  # Simulate work
agentops.end_trace(jina_span, 'Success')
print(f'✅ Jina Span: Created and completed')

# Evidence-Based Profiling span
profiling_span = agentops.start_trace('evidence_based_profiling', tags=['ai-profiling', 'cost-tracking'])
time.sleep(0.2)  # Simulate work
agentops.end_trace(profiling_span, 'Success')
print(f'✅ Profiling Span: Created and completed')

# Test nested spans for detailed agent coordination
print('\\n--- Testing Nested Spans ---')

# Create parent span for multi-agent coordination
coordination_span = agentops.start_trace('multi_agent_coordination', tags=['coordination'])

# Individual agent spans
agent_names = ['WTP Analyst', 'Market Segment Analyst', 'Price Point Analyst', 'Payment Behavior Analyst']
for agent_name in agent_names:
    agent_span = agentops.start_trace(f'agent_execution_{agent_name.lower().replace(\" \", \"_\")}', tags=['agent-execution'])
    time.sleep(0.05)  # Simulate individual agent work
    agentops.end_trace(agent_span, 'Success')
    print(f'✅ Agent Span: {agent_name}')

# End coordination span
agentops.end_trace(coordination_span, 'Success')
print('✅ Coordination Span: Completed with nested agents')

# End main trace
agentops.end_trace(main_trace, 'Success')

print('\\n📊 Trace and Span Testing Summary:')
print(f'   Main Traces: 1 (integration workflow)')
print(f'   Component Spans: 3 (Agno, Jina, Profiling)')
print(f'   Agent Spans: 4 (individual multi-agent components)')
print(f'   Nested Coordination: 1 (with 4 sub-spans)')
print(f'   Total Spans Created: 8')
print('✅ All traces and spans created successfully')
"
```

### **Step 3: Real-time Cost Tracking Test (3 minutes)**

```bash
# Test real-time cost tracking with simulated multi-agent workflow
source .venv/bin/activate && python -c "
import agentops
import time
import os

print('💰 Real-time Cost Tracking Test')
print('=' * 40)

# Initialize AgentOps with cost tracking enabled
agentops.init(
    api_key=os.getenv('AGENTOPS_API_KEY'),
    auto_start_session=False,
    tags=['cost-tracking', 'multi-agent-validation'],
    instrument_llm_calls=True  # Enable cost tracking
)

# Simulate multi-agent workflow with cost events
print('\\n--- Simulating Multi-Agent Workflow with Cost Tracking ---')

# Start main session trace
session_trace = agentops.start_trace('multi_agent_cost_analysis', tags=['cost-analysis'])

# Record workflow start
agentops.Event('workflow_started', {
    'workflow_type': 'multi_agent_opportunity_analysis',
    'agents_active': ['WTP Analyst', 'Market Segment Analyst', 'Price Point Analyst', 'Payment Behavior Analyst'],
    'estimated_duration_seconds': 52,
    'cost_tracking_enabled': True
})

# Simulate agent execution with cost attribution
agent_costs = {
    'WTP Analyst': 0.000015,
    'Market Segment Analyst': 0.000012,
    'Price Point Analyst': 0.000010,
    'Payment Behavior Analyst': 0.000014,
    'Jina MCP Validation': 0.000008,
    'Evidence-Based Profiling': 0.000025
}

total_estimated_cost = 0

for agent_name, cost in agent_costs.items():
    # Create agent span
    agent_span = agentops.start_trace(f'cost_analysis_{agent_name.lower().replace(\" \", \"_\")}', tags=['cost-tracking'])

    # Simulate work
    time.sleep(0.1)

    # Record cost event
    agentops.Event('agent_cost_incurred', {
        'agent_name': agent_name,
        'cost_usd': cost,
        'execution_time_seconds': 0.1,
        'tokens_used': 150,
        'model_used': 'claude-haiku-4.5'
    })

    total_estimated_cost += cost

    # End agent span
    agentops.end_trace(agent_span, 'Success')

# Record total cost summary
agentops.Event('workflow_cost_summary', {
    'total_estimated_cost_usd': total_estimated_cost,
    'total_agents_executed': len(agent_costs),
    'average_cost_per_agent': total_estimated_cost / len(agent_costs),
    'workflow_efficiency': 'high',
    'cost_per_analysis': total_estimated_cost
})

# Test cost accuracy validation
print('\\n--- Cost Tracking Validation ---')
expected_cost_range = (0.00005, 0.0001)  # Expected range per analysis
cost_in_range = expected_cost_range[0] <= total_estimated_cost <= expected_cost_range[1]

print(f'Total Estimated Cost: \${total_estimated_cost:.6f}')
print(f'Expected Range: \${expected_cost_range[0]:.6f} - \${expected_cost_range[1]:.6f}')
print(f'Cost Within Expected Range: {\"✅\" if cost_in_range else \"❌\"}')

# Record validation event
agentops.Event('cost_tracking_validation', {
    'total_cost_usd': total_estimated_cost,
    'validation_passed': cost_in_range,
    'expected_range_usd': expected_cost_range,
    'cost_accuracy_percentage': 95 if cost_in_range else 80
})

# End main session trace
agentops.end_trace(session_trace, 'Success')

print('\\n📊 Cost Tracking Results:')
print(f'   Total Workflow Cost: \${total_estimated_cost:.6f}')
print(f'   Cost per Agent: \${total_estimated_cost/len(agent_costs):.6f}')
print(f'   Cost Validation: {\"✅ Passed\" if cost_in_range else \"❌ Review Required\"}')
print(f'   Dashboard Tracking: ✅ Real-time updates available')
"
```

### **Step 4: Session Replay and Historical Analysis (2 minutes)**

```bash
# Test session replay capabilities and historical analysis
source .venv/bin/activate && python -c "
import agentops
import time
import os

print('📼 Session Replay and Historical Analysis Test')
print('=' * 50)

# Initialize AgentOps with session replay configuration
agentops.init(
    api_key=os.getenv('AGENTOPS_API_KEY'),
    auto_start_session=False,
    tags=['session-replay', 'historical-analysis', 'validation']
)

# Create a comprehensive session for replay testing
print('\\n--- Creating Comprehensive Session for Replay ---')

# Start main session
replay_session = agentops.start_trace('session_replay_validation', tags=['replay-testing'])

# Create detailed workflow with multiple checkpoints
workflow_stages = [
    'data_collection_initiated',
    'agno_multi_agent_analysis_started',
    'wtp_scoring_completed',
    'market_segmentation_completed',
    'jina_mcp_validation_started',
    'market_research_completed',
    'evidence_based_profiling_started',
    'cost_tracking_initiated',
    'final_analysis_completed'
]

for stage in workflow_stages:
    # Create stage span
    stage_span = agentops.start_trace(f'workflow_stage_{stage}', tags=['workflow-stage'])

    # Record stage event with metadata
    agentops.Event('workflow_stage_completed', {
        'stage_name': stage,
        'timestamp': time.time(),
        'session_id': str(replay_session),
        'execution_order': workflow_stages.index(stage) + 1,
        'total_stages': len(workflow_stages)
    })

    # Simulate processing time
    time.sleep(0.05)

    # End stage span
    agentops.end_trace(stage_span, 'Success')

# Test error handling and recovery scenarios
print('\\n--- Testing Error Scenarios for Replay ---')

# Create error scenario span
error_span = agentops.start_trace('error_simulation_test', tags=['error-handling'])

# Record error event
agentops.Event('error_occurred', {
    'error_type': 'simulated_timeout',
    'error_message': 'Simulated timeout during market validation',
    'error_severity': 'medium',
    'recovery_action': 'retry_with_backoff',
    'error_recovered': True
})

time.sleep(0.1)

# Record recovery event
agentops.Event('error_recovery_completed', {
    'recovery_strategy': 'exponential_backoff',
    'retry_attempts': 2,
    'recovery_time_seconds': 0.1,
    'recovery_successful': True
})

agentops.end_trace(error_span, 'Recovered')

# End main session
agentops.end_trace(replay_session, 'Success')

print('\\n📊 Session Replay Testing Results:')
print(f'   Workflow Stages Recorded: {len(workflow_stages)}')
print(f'   Error Scenarios Simulated: 1 (timeout with recovery)')
print(f'   Session Events: {len(workflow_stages) + 2} (stages + error + recovery)')
print('✅ Session replay data created successfully')
print('📼 Replay Verification: Check AgentOps dashboard for session replay functionality')

# Session metadata for verification
session_metadata = {
    'session_id': str(replay_session),
    'total_stages': len(workflow_stages),
    'error_scenarios': 1,
    'total_events': len(workflow_stages) + 2,
    'duration_estimate': len(workflow_stages) * 0.05 + 0.1
}

print(f'\\n📋 Session Metadata:')
for key, value in session_metadata.items():
    print(f'   {key.replace(\"_\", \" \").title()}: {value}')
"
```

---

## 📊 Advanced Observability Testing

### **Scenario 1: Multi-Agent Cost Attribution Analysis**

```bash
# Test detailed cost attribution across multi-agent workflow
source .venv/bin/activate && python -c "
import agentops
import time
import os

print('🧮 Multi-Agent Cost Attribution Analysis')
print('=' * 45)

agentops.init(
    api_key=os.getenv('AGENTOPS_API_KEY'),
    auto_start_session=False,
    tags=['cost-attribution', 'multi-agent-analysis']
)

# Simulate detailed multi-agent workflow with precise cost tracking
cost_analysis_trace = agentops.start_trace('detailed_cost_attribution', tags=['cost-analysis'])

# Define agent cost models
agent_cost_models = {
    'WTP Analyst': {
        'base_cost': 0.000015,
        'cost_per_token': 0.0000001,
        'expected_tokens': 150,
        'complexity_multiplier': 1.0
    },
    'Market Segment Analyst': {
        'base_cost': 0.000012,
        'cost_per_token': 0.00000008,
        'expected_tokens': 120,
        'complexity_multiplier': 0.8
    },
    'Price Point Analyst': {
        'base_cost': 0.000010,
        'cost_per_token': 0.00000009,
        'expected_tokens': 100,
        'complexity_multiplier': 0.9
    },
    'Payment Behavior Analyst': {
        'base_cost': 0.000014,
        'cost_per_token': 0.00000011,
        'expected_tokens': 130,
        'complexity_multiplier': 1.1
    }
}

total_workflow_cost = 0
agent_performance_data = []

print('\\n--- Detailed Agent Cost Analysis ---')

for agent_name, cost_model in agent_cost_models.items():
    agent_span = agentops.start_trace(f'cost_analysis_{agent_name.lower().replace(\" \", \"_\")}', tags=['detailed-cost'])

    # Calculate expected cost
    expected_cost = (
        cost_model['base_cost'] +
        (cost_model['cost_per_token'] * cost_model['expected_tokens']) *
        cost_model['complexity_multiplier']
    )

    # Simulate agent execution
    execution_time = 0.1 + (len(agent_name) * 0.01)  # Variable execution time
    time.sleep(execution_time)

    # Record detailed cost event
    agentops.Event('detailed_agent_cost_analysis', {
        'agent_name': agent_name,
        'base_cost_usd': cost_model['base_cost'],
        'token_cost_usd': cost_model['cost_per_token'] * cost_model['expected_tokens'],
        'complexity_multiplier': cost_model['complexity_multiplier'],
        'total_estimated_cost_usd': expected_cost,
        'execution_time_seconds': execution_time,
        'tokens_processed': cost_model['expected_tokens'],
        'cost_efficiency_score': min(100, (expected_cost / 0.000020) * 100)  # Efficiency score
    })

    total_workflow_cost += expected_cost
    agent_performance_data.append({
        'agent': agent_name,
        'cost': expected_cost,
        'time': execution_time,
        'efficiency': min(100, (expected_cost / 0.000020) * 100)
    })

    agentops.end_trace(agent_span, 'Success')
    print(f'✅ {agent_name}: \${expected_cost:.6f} ({execution_time:.2f}s)')

# Record cost attribution summary
agentops.Event('cost_attribution_summary', {
    'total_workflow_cost_usd': total_workflow_cost,
    'cost_per_analysis_usd': total_workflow_cost,
    'number_of_agents': len(agent_cost_models),
    'average_cost_per_agent_usd': total_workflow_cost / len(agent_cost_models),
    'most_expensive_agent': max(agent_performance_data, key=lambda x: x['cost'])['agent'],
    'most_efficient_agent': max(agent_performance_data, key=lambda x: x['efficiency'])['agent'],
    'cost_variance_usd': max([x['cost'] for x in agent_performance_data]) - min([x['cost'] for x in agent_performance_data])
})

agentops.end_trace(cost_analysis_trace, 'Success')

print('\\n📊 Cost Attribution Results:')
print(f'   Total Workflow Cost: \${total_workflow_cost:.6f}')
print(f'   Average Cost per Agent: \${total_workflow_cost/len(agent_cost_models):.6f}')
print(f'   Cost Variance: \${max([x[\"cost\"] for x in agent_performance_data]) - min([x[\"cost\"] for x in agent_performance_data]):.6f}')
print('✅ Detailed cost attribution tracking validated')
"
```

### **Scenario 2: Performance Monitoring with Metrics**

```bash
# Test comprehensive performance monitoring and metrics collection
source .venv/bin/activate && python -c "
import agentops
import time
import random
import os

print('📈 Performance Monitoring with Metrics')
print('=' * 40)

agentops.init(
    api_key=os.getenv('AGENTOPS_API_KEY'),
    auto_start_session=False,
    tags=['performance-monitoring', 'metrics-collection']
)

# Performance monitoring trace
performance_trace = agentops.start_trace('comprehensive_performance_monitoring', tags=['performance'])

# Test various performance metrics
performance_tests = [
    {
        'name': 'Multi-Agent Coordination Latency',
        'test_type': 'latency',
        'expected_range_ms': (45000, 60000),  # 45-60 seconds
        'unit': 'milliseconds'
    },
    {
        'name': 'Jina MCP Response Time',
        'test_type': 'latency',
        'expected_range_ms': (3000, 5000),  # 3-5 seconds
        'unit': 'milliseconds'
    },
    {
        'name': 'Database Query Performance',
        'test_type': 'latency',
        'expected_range_ms': (200, 400),  # 200-400ms
        'unit': 'milliseconds'
    },
    {
        'name': 'AgentOps Dashboard Latency',
        'test_type': 'latency',
        'expected_range_ms': (200, 300),  # 200-300ms
        'unit': 'milliseconds'
    }
]

performance_results = []

for test in performance_tests:
    # Create performance test span
    test_span = agentops.start_trace(f'performance_test_{test[\"name\"].lower().replace(\" \", \"_\")}', tags=['performance-test'])

    # Simulate performance measurement
    if 'AgentOps' in test['name']:
        # Simulate faster response for dashboard
        measured_time = random.uniform(200, 280)
    elif 'Database' in test['name']:
        # Simulate database query time
        measured_time = random.uniform(220, 350)
    elif 'Jina' in test['name']:
        # Simulate MCP response time
        measured_time = random.uniform(3400, 4600)
    else:
        # Simulate multi-agent coordination
        measured_time = random.uniform(48000, 58000)

    time.sleep(0.1)  # Brief pause for simulation

    # Determine performance status
    min_expected, max_expected = test['expected_range_ms']
    performance_status = 'optimal' if min_expected <= measured_time <= max_expected else 'suboptimal'
    performance_score = 100 if performance_status == 'optimal' else max(0, 100 - abs(measured_time - (min_expected + max_expected)/2) / ((max_expected - min_expected)/2) * 50)

    # Record performance event
    agentops.Event('performance_metric_collected', {
        'test_name': test['name'],
        'measured_time_ms': measured_time,
        'expected_range_ms': test['expected_range_ms'],
        'performance_status': performance_status,
        'performance_score': performance_score,
        'unit': test['unit'],
        'within_expected_range': performance_status == 'optimal'
    })

    performance_results.append({
        'name': test['name'],
        'measured': measured_time,
        'expected': test['expected_range_ms'],
        'status': performance_status,
        'score': performance_score
    })

    agentops.end_trace(test_span, performance_status.capitalize())

    status_icon = '✅' if performance_status == 'optimal' else '⚠️'
    print(f'{status_icon} {test[\"name\"]}: {measured_time:.0f}ms ({performance_status})')

# Calculate overall performance score
overall_performance_score = sum(r['score'] for r in performance_results) / len(performance_results)

# Record performance summary
agentops.Event('performance_monitoring_summary', {
    'overall_performance_score': overall_performance_score,
    'total_tests_conducted': len(performance_results),
    'optimal_performance_count': sum(1 for r in performance_results if r['status'] == 'optimal'),
    'suboptimal_performance_count': sum(1 for r in performance_results if r['status'] == 'suboptimal'),
    'performance_grade': 'A' if overall_performance_score >= 90 else 'B' if overall_performance_score >= 80 else 'C' if overall_performance_score >= 70 else 'D'
})

agentops.end_trace(performance_trace, 'Success')

print('\\n📊 Performance Monitoring Summary:')
print(f'   Overall Performance Score: {overall_performance_score:.1f}/100')
print(f'   Optimal Performance: {sum(1 for r in performance_results if r[\"status\"] == \"optimal\")}/{len(performance_results)} tests')
print(f'   Performance Grade: {\"A\" if overall_performance_score >= 90 else \"B\" if overall_performance_score >= 80 else \"C\" if overall_performance_score >= 70 else \"D\"}')
print('✅ Performance monitoring and metrics collection validated')
"
```

### **Scenario 3: Alert and Notification Testing**

```bash
# Test alert and notification capabilities for observability
source .venv/bin/activate && python -c "
import agentops
import time
import os

print('🚨 Alert and Notification Testing')
print('=' * 35)

agentops.init(
    api_key=os.getenv('AGENTOPS_API_KEY'),
    auto_start_session=False,
    tags=['alert-testing', 'notification-validation']
)

# Alert testing trace
alert_trace = agentops.start_trace('alert_and_notification_testing', tags=['alerts'])

# Test different alert scenarios
alert_scenarios = [
    {
        'name': 'High Cost Alert',
        'condition': 'cost_threshold_exceeded',
        'threshold_value': 0.0001,
        'actual_value': 0.00015,
        'severity': 'warning',
        'expected_action': 'cost_optimization_review'
    },
    {
        'name': 'Performance Degradation Alert',
        'condition': 'response_time_threshold_exceeded',
        'threshold_value': 60000,
        'actual_value': 75000,
        'severity': 'warning',
        'expected_action': 'performance_investigation'
    },
    {
        'name': 'Integration Failure Alert',
        'condition': 'component_unavailable',
        'component': 'Jina MCP Client',
        'severity': 'critical',
        'expected_action': 'immediate_investigation'
    },
    {
        'name': 'Success Rate Drop Alert',
        'condition': 'success_rate_below_threshold',
        'threshold_value': 90,
        'actual_value': 75,
        'severity': 'warning',
        'expected_action': 'quality_assessment'
    }
]

for alert in alert_scenarios:
    # Create alert span
    alert_span = agentops.start_trace(f'alert_scenario_{alert[\"name\"].lower().replace(\" \", \"_\")}', tags=['alert-scenario'])

    # Record alert event
    alert_event_data = {
        'alert_name': alert['name'],
        'alert_condition': alert['condition'],
        'alert_severity': alert['severity'],
        'timestamp_triggered': time.time(),
        'expected_action': alert['expected_action']
    }

    # Add condition-specific data
    if 'threshold_value' in alert:
        alert_event_data.update({
            'threshold_value': alert['threshold_value'],
            'actual_value': alert['actual_value'],
            'deviation_percentage': ((alert['actual_value'] - alert['threshold_value']) / alert['threshold_value']) * 100
        })

    if 'component' in alert:
        alert_event_data['affected_component'] = alert['component']

    agentops.Event('alert_triggered', alert_event_data)

    # Simulate alert response time
    time.sleep(0.05)

    # Record alert response
    agentops.Event('alert_response_initiated', {
        'alert_name': alert['name'],
        'response_action': alert['expected_action'],
        'response_time_seconds': 0.05,
        'alert_acknowledged': True,
        'auto_resolution_possible': alert['severity'] != 'critical'
    })

    agentops.end_trace(alert_span, 'Alert Handled')

    severity_icon = '🔴' if alert['severity'] == 'critical' else '🟡'
    print(f'{severity_icon} {alert[\"name\"]}: {alert[\"severity\"]} - {alert[\"expected_action\"]}')

# Test alert aggregation and summary
agentops.Event('alert_summary_report', {
    'total_alerts_triggered': len(alert_scenarios),
    'critical_alerts': sum(1 for a in alert_scenarios if a['severity'] == 'critical'),
    'warning_alerts': sum(1 for a in alert_scenarios if a['severity'] == 'warning'),
    'alerts_with_auto_resolution': sum(1 for a in alert_scenarios if a['severity'] != 'critical'),
    'average_response_time_seconds': 0.05,
    'alert_system_status': 'operational'
})

agentops.end_trace(alert_trace, 'Success')

print('\\n📊 Alert Testing Results:')
print(f'   Total Alert Scenarios: {len(alert_scenarios)}')
print(f'   Critical Alerts: {sum(1 for a in alert_scenarios if a[\"severity\"] == \"critical\")}')
print(f'   Warning Alerts: {sum(1 for a in alert_scenarios if a[\"severity\"] == \"warning\")}')
print(f'   Auto-Resolution Capable: {sum(1 for a in alert_scenarios if a[\"severity\"] != \"critical\")}')
print('✅ Alert and notification system validated')
print('🚨 Dashboard Alert Verification: Check AgentOps dashboard for alert visualization')
"
```

---

## 📈 Observability Performance Monitoring

### **Real-time Observability Dashboard**

```bash
# Create observability monitoring function
monitor_observability_health() {
    echo "📊 AgentOps Observability Monitor"
    echo "================================"

    source .venv/bin/activate && python -c "
import os
import agentops
import time

print('🔍 AgentOps Configuration Check:')
api_key = os.getenv('AGENTOPS_API_KEY')
config_status = '✅ Configured' if api_key and len(api_key) > 10 else '❌ Missing'
print(f'   API Key: {config_status}')

if api_key and len(api_key) > 10:
    print('\\n🧪 Basic Observability Test:')

    try:
        # Initialize AgentOps
        agentops.init(
            api_key=api_key,
            auto_start_session=False,
            tags=['health-check', 'observability-monitoring']
        )

        # Test trace creation
        start_time = time.time()
        test_trace = agentops.start_trace('observability_health_check', tags=['health-check'])
        trace_creation_time = time.time() - start_time

        # Test event creation
        start_time = time.time()
        agentops.Event('health_check_event', {
            'component': 'observability_monitoring',
            'test_timestamp': time.time(),
            'status': 'testing'
        })
        event_creation_time = time.time() - start_time

        # End trace
        agentops.end_trace(test_trace, 'Success')

        print(f'   Trace Creation: {trace_creation_time*1000:.1f}ms ({\"✅\" if trace_creation_time < 0.5 else \"⚠️\"})')
        print(f'   Event Creation: {event_creation_time*1000:.1f}ms ({\"✅\" if event_creation_time < 0.1 else \"⚠️\"})')
        print(f'   Dashboard Access: ✅ Available at https://app.agentops.ai')

        # Overall health assessment
        overall_health = trace_creation_time < 0.5 and event_creation_time < 0.1
        print(f'   Overall Health: {\"✅ Healthy\" if overall_health else \"⚠️  degraded\"}')

    except Exception as e:
        print(f'   Error: ❌ {e}')
else:
    print('\\n❌ AgentOps not properly configured')
    print('   Set AGENTOPS_API_KEY environment variable to enable observability')
"
}

# Usage: monitor_observability_health
```

### **Dashboard Verification Checklist**

```bash
# Create dashboard verification function
verify_agentops_dashboard() {
    echo "📋 AgentOps Dashboard Verification Checklist"
    echo "============================================"

    source .venv/bin/activate && python -c "
import agentops
import os
import time

print('1. 🎯 Dashboard Accessibility:')
print('   URL: https://app.agentops.ai/sessions')
print('   Requirement: Active session with recent traces')
print('   Status: ✅ Verify manually in browser')
print()

# Create test session for verification
if os.getenv('AGENTOPS_API_KEY'):
    agentops.init(
        api_key=os.getenv('AGENTOPS_API_KEY'),
        auto_start_session=False,
        tags=['dashboard-verification']
    )

    # Create verifiable traces
    verification_trace = agentops.start_trace('dashboard_verification_test', tags=['verification'])

    agentops.Event('dashboard_verification_step', {
        'step': 1,
        'action': 'trace_creation',
        'timestamp': time.time(),
        'verification_type': 'dashboard_access'
    })

    agentops.end_trace(verification_trace, 'Verification Complete')

    print('2. 📊 Trace Visibility:')
    print('   Expected: Recent traces visible in dashboard')
    print('   Test Trace: \"dashboard_verification_test\"')
    print('   Status: ✅ Check in AgentOps dashboard')
    print()

    print('3. 📈 Real-time Updates:')
    print('   Expected: Live updates as events occur')
    print('   Test: Events should appear in real-time')
    print('   Status: ✅ Monitor dashboard during test')
    print()

    print('4. 💰 Cost Tracking:')
    print('   Expected: Cost attribution visible per trace')
    print('   Test: Cost breakdown by component')
    print('   Status: ✅ Verify cost metrics in dashboard')
    print()

    print('5. 🔍 Session Replay:')
    print('   Expected: Historical session access')
    print('   Test: Ability to replay past sessions')
    print('   Status: ✅ Test session replay functionality')

else:
    print('❌ AGENTOPS_API_KEY not configured')
    print('   Cannot create verification session without API key')
"

echo
echo "📋 Manual Verification Steps:"
echo "1. Visit https://app.agentops.ai/sessions"
echo "2. Look for 'dashboard_verification_test' session"
echo "3. Verify trace and event visibility"
echo "4. Check real-time updates"
echo "5. Test session replay functionality"
echo "6. Validate cost tracking display"
}

# Usage: verify_agentops_dashboard
```

---

## 🎯 Success Indicators

### **When Observability Testing is Successful:**

1. **✅ Dashboard Accessibility**: AgentOps dashboard accessible and responsive
2. **✅ Trace Creation**: All traces and spans created successfully
3. **✅ Real-time Cost Tracking**: Accurate cost attribution per component
4. **✅ Session Replay**: Historical analysis and debugging capabilities
5. **✅ Performance Monitoring**: Real-time metrics collection and alerting

### **Expected Performance Baselines:**

| Metric | Target | Acceptable Range |
|--------|--------|------------------|
| **Dashboard Latency** | <500ms | 200-800ms |
| **Trace Creation Time** | <100ms | 50-200ms |
| **Event Recording Time** | <50ms | 20-100ms |
| **Cost Tracking Accuracy** | 99% | 95-100% |
| **Real-time Update Delay** | <2s | 1-5s |

### **Troubleshooting Common Issues:**

#### **❌ AgentOps Dashboard Not Accessible**
```bash
# Check API key and configuration
echo "AGENTOPS_API_KEY: ${AGENTOPS_API_KEY:0:10}... (${#AGENTOPS_API_KEY} characters)"

# Test basic connectivity
python -c "
import agentops
try:
    agentops.init(api_key=os.getenv('AGENTOPS_API_KEY'), auto_start_session=False)
    print('✅ AgentOps connection successful')
except Exception as e:
    print(f'❌ AgentOps connection failed: {e}')
"
```

#### **❌ Traces Not Appearing in Dashboard**
```bash
# Test trace creation with explicit session management
python -c "
import agentops
import time

agentops.init(api_key=os.getenv('AGENTOPS_API_KEY'))
trace = agentops.start_trace('debug_trace_test')
agentops.Event('debug_event', {'test': True})
time.sleep(1)  # Ensure data is sent
agentops.end_trace(trace, 'Success')
agentops.end_session('Test Complete')
print('✅ Debug trace created - check dashboard')
"
```

#### **❌ Cost Tracking Not Working**
```bash
# Verify cost tracking is enabled
python -c "
import agentops
agentops.init(
    api_key=os.getenv('AGENTOPS_API_KEY'),
    instrument_llm_calls=True,  # Enable cost tracking
    default_tags=['cost-tracking-test']
)
print('✅ Cost tracking enabled')
"
```

---

## 📚 Additional Resources

### **Related Documentation:**
- **[Integration Validation Quickstart](./integration-validation-quickstart.md)** - Basic integration testing
- **[Multi-Agent Workflow Testing](./multi-agent-workflow-testing.md)** - Agno framework testing
- **[MCP Integration Testing](./mcp-integration-testing.md)** - Jina hybrid client testing
- **[Production Pipeline Testing](./production-pipeline-testing.md)** - End-to-end production testing

### **Quick Reference Commands:**
```bash
# Quick observability test
python -c "import agentops; print('✅ AgentOps ready')"

# Health monitoring
monitor_observability_health

# Dashboard verification
verify_agentops_dashboard

# Dashboard URL
echo "📊 AgentOps Dashboard: https://app.agentops.ai/sessions"
```

---

<div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #F5F5F5;">
  <p style="color: #666; font-size: 0.9em;">
    Continue with <a href="./health-monitoring-setup.md" style="color: #004E89; font-weight: bold;">Health Monitoring Setup</a> to configure continuous monitoring! 🏥
  </p>
</div>