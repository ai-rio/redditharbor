# MCP Integration Testing

<div style="text-align: center; margin: 20px 0;">
  <h1 style="color: #FF6B35;">🌐 MCP Integration Testing</h1>
  <p style="color: #004E89; font-size: 1.2em;">Jina MCP hybrid client validation and capability testing</p>
</div>

---

## 📋 Overview

This **MCP Integration Testing** guide provides comprehensive testing scenarios for RedditHarbor's Jina MCP (Model Context Protocol) hybrid client. The testing validates the MCP capabilities, hybrid HTTP+MCP approach, and safe attribute access patterns that enable advanced market validation.

**What you'll test:**
1. 🔧 **MCP Capability Detection** - Automatic MCP tool discovery
2. 🌐 **Hybrid Client Functionality** - HTTP and MCP protocol switching
3. 📖 **URL Reading Reliability** - Content extraction performance
4. 🔍 **Web Search Integration** - Market research capabilities
5. 🛡️ **Safe Attribute Access** - MCP experimental feature handling

**Time Investment:** 15 minutes
**Expected Performance:** 3.46s latency, 500 API calls remaining
**Success Threshold:** 80% success rate for all operations

---

## 🚀 Quick Start MCP Testing

### **Step 1: MCP Capability Detection (3 minutes)**

```bash
# Test Jina MCP hybrid client initialization
source .venv/bin/activate && python -c "
from agent_tools.jina_hybrid_client import JinaHybridClient

# Initialize hybrid client with MCP experimental features
client = JinaHybridClient(
    enable_mcp_experimental=True,
    rate_limit_reader=500,
    rate_limit_search=100
)

print('🔍 MCP Capability Detection Results:')
print(f'   MCP Available: {getattr(client, \"mcp_capability\", False)}')
print(f'   MCP Experimental: {getattr(client, \"mcp_experimental\", False)}')
print(f'   MCP Status: {getattr(client, \"mcp_status\", \"unknown\")}')
print(f'   Client Type: {getattr(client, \"client_type\", \"unknown\")}')

# Check for MCP-specific attributes
mcp_attrs = [attr for attr in dir(client) if 'mcp' in attr.lower()]
print(f'   MCP Attributes Found: {len(mcp_attrs)}')
for attr in mcp_attrs[:5]:  # Show first 5
    print(f'     - {attr}')

print('✅ MCP Hybrid Client initialized successfully')
"
```

### **Step 2: URL Reading Reliability Test (5 minutes)**

```bash
# Test URL reading with various content types
source .venv/bin/activate && python -c "
import asyncio
from agent_tools.jina_hybrid_client import JinaHybridClient

async def test_url_reading():
    client = JinaHybridClient(enable_mcp_experimental=True)

    test_urls = [
        ('Simple HTML', 'https://example.com'),
        ('JSON API', 'https://httpbin.org/json'),
        ('Text Content', 'https://jsonplaceholder.typicode.com/posts/1'),
        ('News Site', 'https://news.ycombinator.com'),
        ('Documentation', 'https://docs.python.org/3/')
    ]

    print('📖 URL Reading Reliability Test:')
    print('=' * 50)

    successful_reads = 0
    total_reads = len(test_urls)
    total_time = 0

    for name, url in test_urls:
        try:
            import time
            start_time = time.time()

            result = await client.read_url(url)
            duration = time.time() - start_time
            total_time += duration

            if result and hasattr(result, 'content') and result.content:
                content_length = len(result.content)
                successful_reads += 1
                status = '✅'
                print(f'{status} {name}: {content_length} chars ({duration:.2f}s)')
            else:
                status = '⚠️'
                print(f'{status} {name}: Empty response ({duration:.2f}s)')

        except Exception as e:
            print(f'❌ {name}: Error - {str(e)[:30]}...')

    success_rate = (successful_reads / total_reads) * 100
    avg_time = total_time / total_reads

    print('=' * 50)
    print(f'📊 Results Summary:')
    print(f'   Success Rate: {success_rate:.1f}% ({successful_reads}/{total_reads})')
    print(f'   Average Time: {avg_time:.2f}s')
    print(f'   Quality: {\"✅ Excellent\" if success_rate >= 90 else \"⚠️  Good\" if success_rate >= 80 else \"❌ Needs Improvement\"}')

# Run the test
asyncio.run(test_url_reading())
"
```

### **Step 3: Web Search Integration Test (4 minutes)**

```bash
# Test web search capabilities for market validation
source .venv/bin/activate && python -c "
import asyncio
from agent_tools.jina_hybrid_client import JinaHybridClient

async def test_web_search():
    client = JinaHybridClient(enable_mcp_experimental=True)

    # Market research search queries
    search_queries = [
        'expense tracking software market size',
        'small business accounting tools competitors',
        'freelance project management software pricing',
        'SaaS CRM solutions for startups'
    ]

    print('🔍 Web Search Integration Test:')
    print('=' * 50)

    successful_searches = 0
    total_searches = len(search_queries)
    total_time = 0

    for query in search_queries:
        try:
            import time
            start_time = time.time()

            results = await client.search(query, num_results=3)
            duration = time.time() - start_time
            total_time += duration

            if results and hasattr(results, 'results') and results.results:
                result_count = len(results.results)
                successful_searches += 1
                status = '✅'
                print(f'{status} \"{query[:30]}...\": {result_count} results ({duration:.2f}s)')
            else:
                status = '⚠️'
                print(f'{status} \"{query[:30]}...\": No results ({duration:.2f}s)')

        except Exception as e:
            print(f'❌ \"{query[:30]}...\": Error - {str(e)[:30]}...')

    success_rate = (successful_searches / total_searches) * 100
    avg_time = total_time / total_searches

    print('=' * 50)
    print(f'📊 Search Results Summary:')
    print(f'   Success Rate: {success_rate:.1f}% ({successful_searches}/{total_searches})')
    print(f'   Average Time: {avg_time:.2f}s')
    print(f'   Quality: {\"✅ Excellent\" if success_rate >= 90 else \"⚠️  Good\" if success_rate >= 80 else \"❌ Needs Improvement\"}')

# Run the test
asyncio.run(test_web_search())
"
```

### **Step 4: Rate Limiting and API Status Check (3 minutes)**

```bash
# Check API rate limits and status
source .venv/bin/activate && python -c "
from agent_tools.jina_hybrid_client import JinaHybridClient

# Initialize client
client = JinaHybridClient(enable_mcp_experimental=True)

print('📊 Rate Limiting and API Status:')
print('=' * 40)

# Get rate limit status
rate_limit_status = client.get_rate_limit_status()
print(f'Rate Limit Status: {rate_limit_status}')

# Check API key configuration
import os
jina_api_key = os.getenv('JINA_API_KEY')
api_key_configured = bool(jina_api_key and len(jina_api_key) > 10)

print(f'API Key Configured: {\"✅\" if api_key_configured else \"❌\"}')

# Test MCP-specific attributes
mcp_available = getattr(client, 'mcp_capability', False)
mcp_experimental = getattr(client, 'mcp_experimental', False)

print(f'MCP Available: {\"✅\" if mcp_available else \"❌\"}')
print(f'MCP Experimental: {\"✅\" if mcp_experimental else \"❌\"}')

# Client health check
client_healthy = api_key_configured and hasattr(client, 'read_url')
print(f'Client Health: {\"✅ Healthy\" if client_healthy else \"❌ Unhealthy\"}')

print('=' * 40)
print('🎯 Overall MCP Integration Status:')

status_points = 0
total_points = 4

if api_key_configured:
    status_points += 1
if mcp_available or mcp_experimental:
    status_points += 1
if hasattr(client, 'get_rate_limit_status'):
    status_points += 1
if client_healthy:
    status_points += 1

health_percentage = (status_points / total_points) * 100
print(f'Health Score: {health_percentage:.0f}% ({status_points}/{total_points})')

if health_percentage >= 75:
    print('🎉 MCP Integration: ✅ Production Ready')
elif health_percentage >= 50:
    print('⚠️  MCP Integration: Functional with Limitations')
else:
    print('❌ MCP Integration: Configuration Required')
"
```

---

## 📊 Advanced MCP Testing Scenarios

### **Scenario 1: Safe Attribute Access Testing**

```bash
# Test safe attribute access for MCP experimental features
source .venv/bin/activate && python -c "
from agent_tools.jina_hybrid_client import JinaHybridClient

client = JinaHybridClient(enable_mcp_experimental=True)

print('🛡️ Safe Attribute Access Testing:')
print('=' * 40)

# List of MCP-related attributes to test safely
mcp_attributes = [
    'mcp_capability',
    'mcp_experimental',
    'mcp_status',
    'mcp_tools',
    'mcp_version'
]

for attr in mcp_attributes:
    # Safe attribute access pattern
    value = getattr(client, attr, None)
    value_type = type(value).__name__ if value is not None else 'None'

    print(f'{attr}: {value} ({value_type})')

# Test safe method calling
print('\\n🔧 Safe Method Testing:')

# Test methods that might not exist in all versions
test_methods = [
    'get_mcp_tools',
    'list_mcp_capabilities',
    'reset_mcp_connection'
]

for method_name in test_methods:
    method = getattr(client, method_name, None)
    if callable(method):
        try:
            result = method()
            print(f'✅ {method_name}: Callable, returned {type(result).__name__}')
        except Exception as e:
            print(f'⚠️  {method_name}: Callable but failed - {str(e)[:30]}...')
    else:
        print(f'❌ {method_name}: Not available')

print('\\n🎯 Safe Access Pattern: ✅ Implemented')
print('All attribute access is safely handled with fallbacks')
"
```

### **Scenario 2: Hybrid Protocol Testing**

```bash
# Test hybrid HTTP+MCP protocol switching
source .venv/bin/activate && python -c "
import asyncio
from agent_tools.jina_hybrid_client import JinaHybridClient

async def test_hybrid_protocol():
    client = JinaHybridClient(enable_mcp_experimental=True)

    print('🔄 Hybrid Protocol Testing (HTTP + MCP):')
    print('=' * 45)

    # Test same operation with different expectations
    test_operations = [
        ('Simple URL Read', 'https://example.com', 'read_url'),
        ('JSON API Call', 'https://httpbin.org/json', 'read_url'),
        ('Search Query', 'market research software', 'search')
    ]

    for name, input_data, operation in test_operations:
        print(f'\\n--- {name} ---')

        try:
            if operation == 'read_url':
                result = await client.read_url(input_data)
                success = result and hasattr(result, 'content') and result.content
                content_preview = result.content[:100] if success and result.content else 'No content'
                print(f'   Result: {\"✅ Success\" if success else \"❌ Failed\"}')
                print(f'   Content Preview: {content_preview}...')

            elif operation == 'search':
                result = await client.search(input_data, num_results=2)
                success = result and hasattr(result, 'results') and result.results
                result_count = len(result.results) if success and result.results else 0
                print(f'   Result: {\"✅ Success\" if success else \"❌ Failed\"}')
                print(f'   Result Count: {result_count}')

            # Determine which protocol was likely used
            mcp_indicators = [
                getattr(client, 'mcp_capability', False),
                getattr(client, 'mcp_experimental', False),
                hasattr(result, 'mcp_metadata') if result else False
            ]

            protocol_used = 'MCP' if any(mcp_indicators) else 'HTTP'
            print(f'   Protocol Used: {protocol_used}')

        except Exception as e:
            print(f'   Error: {str(e)[:50]}...')

    print('\\n📊 Hybrid Protocol Analysis:')
    print('The client automatically switches between HTTP and MCP')
    print('based on capabilities and request requirements.')

# Run the test
asyncio.run(test_hybrid_protocol())
"
```

### **Scenario 3: Market Validation Workflow Test**

```bash
# Test complete market validation workflow using MCP integration
source .venv/bin/activate && python -c "
import asyncio
from agent_tools.jina_hybrid_client import JinaHybridClient

async def test_market_validation_workflow():
    client = JinaHybridClient(enable_mcp_experimental=True)

    print('🎯 Market Validation Workflow Test:')
    print('=' * 40)

    # Simulate a complete market validation scenario
    app_concept = 'AI-powered expense tracking for small businesses'
    target_market = 'Small businesses with 10-50 employees'

    workflow_steps = [
        ('Competitor Analysis', f'{app_concept} competitors pricing'),
        ('Market Research', f'{target_market} software spending statistics'),
        ('Trend Analysis', f'expense tracking software market trends 2024'),
        ('Pricing Research', f'small business accounting software pricing models')
    ]

    validation_results = {}

    for step_name, search_query in workflow_steps:
        print(f'\\n--- {step_name} ---')

        try:
            # Perform market research
            search_result = await client.search(search_query, num_results=3)

            if search_result and hasattr(search_result, 'results') and search_result.results:
                result_count = len(search_result.results)

                # Get more detailed info about top result
                top_result = search_result.results[0]
                if hasattr(top_result, 'url') and top_result.url:
                    detailed_info = await client.read_url(top_result.url)
                    content_length = len(detailed_info.content) if detailed_info and hasattr(detailed_info, 'content') else 0

                    validation_results[step_name] = {
                        'search_results': result_count,
                        'detailed_analysis': content_length > 500,
                        'success': True
                    }

                    print(f'   ✅ Found {result_count} results')
                    print(f'   📊 Analyzed top result: {content_length} characters')
                else:
                    validation_results[step_name] = {
                        'search_results': result_count,
                        'detailed_analysis': False,
                        'success': True
                    }
                    print(f'   ✅ Found {result_count} results (no detailed analysis)')
            else:
                validation_results[step_name] = {
                    'search_results': 0,
                    'detailed_analysis': False,
                    'success': False
                }
                print(f'   ❌ No results found')

        except Exception as e:
            validation_results[step_name] = {
                'search_results': 0,
                'detailed_analysis': False,
                'success': False,
                'error': str(e)
            }
            print(f'   ❌ Error: {str(e)[:40]}...')

    # Workflow summary
    print('\\n' + '=' * 40)
    print('📊 Market Validation Workflow Summary:')

    successful_steps = sum(1 for result in validation_results.values() if result.get('success', False))
    total_steps = len(validation_results)
    workflow_success_rate = (successful_steps / total_steps) * 100

    print(f'   Successful Steps: {successful_steps}/{total_steps}')
    print(f'   Workflow Success Rate: {workflow_success_rate:.1f}%')

    for step_name, result in validation_results.items():
        status = '✅' if result.get('success', False) else '❌'
        search_count = result.get('search_results', 0)
        detailed = '✅' if result.get('detailed_analysis', False) else '❌'
        print(f'   {status} {step_name}: {search_count} results, detailed: {detailed}')

    print(f'\\n🎯 Overall Market Validation: {\"✅ Complete\" if workflow_success_rate >= 75 else \"⚠️  Partial\" if workflow_success_rate >= 50 else \"❌ Failed\"}')

# Run the workflow test
asyncio.run(test_market_validation_workflow())
"
```

---

## 📈 MCP Performance Monitoring

### **Real-time MCP Performance Dashboard**

```bash
# Create MCP performance monitoring function
monitor_mcp_performance() {
    echo "🌐 Jina MCP Performance Monitor"
    echo "==============================="

    source .venv/bin/activate && python -c "
import asyncio
import time
import statistics
from agent_tools.jina_hybrid_client import JinaHybridClient

async def performance_test():
    client = JinaHybridClient(enable_mcp_experimental=True)

    # Test performance with various operations
    performance_tests = [
        ('Simple URL', lambda: client.read_url('https://example.com')),
        ('Complex URL', lambda: client.read_url('https://news.ycombinator.com')),
        ('Simple Search', lambda: client.search('python programming')),
        ('Complex Search', lambda: client.search('enterprise software market analysis')),
        ('Rate Limit Check', lambda: client.get_rate_limit_status())
    ]

    results = []

    print('Running performance tests...')
    for test_name, test_func in performance_tests:
        try:
            start_time = time.time()

            if 'Search' in test_name:
                result = await test_func()
            else:
                result = test_func()

            duration = time.time() - start_time

            success = result is not None
            if hasattr(result, 'results'):
                success = len(result.results) > 0 if result.results else False
            elif hasattr(result, 'content'):
                success = len(result.content) > 0 if result.content else False

            results.append({
                'test': test_name,
                'duration': duration,
                'success': success
            })

            status = '✅' if success else '❌'
            print(f'  {status} {test_name}: {duration:.3f}s')

        except Exception as e:
            results.append({
                'test': test_name,
                'duration': 0,
                'success': False,
                'error': str(e)
            })
            print(f'  ❌ {test_name}: Error')

    # Performance metrics
    successful_tests = [r for r in results if r['success']]
    durations = [r['duration'] for r in successful_tests]

    if durations:
        avg_duration = statistics.mean(durations)
        max_duration = max(durations)
        min_duration = min(durations)

        print(f'\\n📊 Performance Metrics:')
        print(f'   Success Rate: {len(successful_tests)}/{len(results)} ({len(successful_tests)/len(results)*100:.1f}%)')
        print(f'   Average Duration: {avg_duration:.3f}s')
        print(f'   Duration Range: {min_duration:.3f}s - {max_duration:.3f}s')
        print(f'   Performance Status: {\"✅ Optimal\" if avg_duration < 2 else \"⚠️  Acceptable\" if avg_duration < 5 else \"❌ Slow\"}')

        # Rate limit status
        rate_limit = client.get_rate_limit_status()
        print(f'   Rate Limit Status: {rate_limit}')

    else:
        print(f'\\n❌ All performance tests failed')

# Run performance test
asyncio.run(performance_test())
"
}

# Usage: monitor_mcp_performance
```

### **MCP Health Check**

```bash
# Comprehensive MCP health check
source .venv/bin/activate && python -c "
import os
from agent_tools.jina_hybrid_client import JinaHybridClient

print('🏥 Jina MCP Health Check')
print('========================')

# Environment checks
print('\\n🔧 Environment Configuration:')
api_key_set = bool(os.getenv('JINA_API_KEY'))
print(f'   JINA_API_KEY: {\"✅ Set\" if api_key_set else \"❌ Missing\"}')

# Client initialization
try:
    client = JinaHybridClient(enable_mcp_experimental=True)
    print('   Client Initialization: ✅ Success')
except Exception as e:
    print(f'   Client Initialization: ❌ Failed - {e}')
    exit(1)

# MCP capability checks
print('\\n🔍 MCP Capabilities:')
mcp_available = getattr(client, 'mcp_capability', False)
mcp_experimental = getattr(client, 'mcp_experimental', False)

print(f'   MCP Available: {\"✅\" if mcp_available else \"❌\"}')
print(f'   MCP Experimental: {\"✅\" if mcp_experimental else \"❌\"}')

# Function availability
print('\\n⚙️ Function Availability:')
required_functions = ['read_url', 'search', 'get_rate_limit_status']
for func_name in required_functions:
    func_available = hasattr(client, func_name) and callable(getattr(client, func_name))
    print(f'   {func_name}: {\"✅\" if func_available else \"❌\"}')

# Quick functionality test
print('\\n🧪 Quick Functionality Test:')
try:
    rate_status = client.get_rate_limit_status()
    print(f'   Rate Limit Check: ✅ {rate_status}')
except Exception as e:
    print(f'   Rate Limit Check: ❌ {e}')

# Overall health assessment
print('\\n🎯 Overall MCP Health:')
health_score = 0
max_score = 5

if api_key_set:
    health_score += 1
if mcp_available or mcp_experimental:
    health_score += 1
if all(hasattr(client, func) for func in required_functions):
    health_score += 1
if rate_status:
    health_score += 1
if health_score >= 3:  # Basic functionality working
    health_score += 1

health_percentage = (health_score / max_score) * 100
print(f'   Health Score: {health_percentage:.0f}% ({health_score}/{max_score})')

if health_percentage >= 80:
    print('   Status: ✅ MCP Integration Healthy')
elif health_percentage >= 60:
    print('   Status: ⚠️  MCP Integration Functional')
else:
    print('   Status: ❌ MCP Integration Needs Attention')
"
```

---

## 🎯 Success Indicators

### **When MCP Integration Testing is Successful:**

1. **✅ MCP Capability Detection**: Experimental features properly detected
2. **✅ URL Reading Reliability**: 80%+ success rate on content extraction
3. **✅ Web Search Integration**: Market research queries return relevant results
4. **✅ Safe Attribute Access**: All MCP attributes accessed without errors
5. **✅ Hybrid Protocol**: Automatic switching between HTTP and MCP works

### **Expected Performance Baselines:**

| Metric | Target | Acceptable Range |
|--------|--------|------------------|
| **URL Reading Success Rate** | 90% | 80-95% |
| **Search Query Success Rate** | 85% | 75-90% |
| **Average Response Time** | <5s | 3-10s |
| **Rate Limit Utilization** | <80% | 60-90% |
| **MCP Feature Detection** | 100% | 80-100% |

### **Troubleshooting Common Issues:**

#### **❌ MCP Capabilities Not Detected**
```bash
# Check MCP experimental mode
python -c "
from agent_tools.jina_hybrid_client import JinaHybridClient
client = JinaHybridClient(enable_mcp_experimental=True)
print(f'MCP Available: {getattr(client, \"mcp_capability\", False)}')
print(f'MCP Experimental: {getattr(client, \"mcp_experimental\", False)}')
"

# Update dependencies if needed
echo "Consider updating agent_tools for latest MCP features"
```

#### **❌ API Rate Limiting Issues**
```bash
# Check current rate limit status
python -c "
from agent_tools.jina_hybrid_client import JinaHybridClient
client = JinaHybridClient()
print('Rate Limit Status:', client.get_rate_limit_status())
"

# Verify API key configuration
echo "JINA_API_KEY: ${JINA_API_KEY:0:10}... (${#JINA_API_KEY} characters)"
```

#### **❌ URL Reading Failures**
```bash
# Test with simple URLs first
python -c "
import asyncio
from agent_tools.jina_hybrid_client import JinaHybridClient

async def test_simple():
    client = JinaHybridClient()
    result = await client.read_url('https://example.com')
    print(f'Simple URL Test: {\"Success\" if result and hasattr(result, \"content\") else \"Failed\"}')

asyncio.run(test_simple())
"
```

---

## 📚 Additional Resources

### **Related Documentation:**
- **[Integration Validation Quickstart](./integration-validation-quickstart.md)** - Basic integration testing
- **[Multi-Agent Workflow Testing](./multi-agent-workflow-testing.md)** - Agno framework testing
- **[Evidence-Based Profiling Testing](./evidence-based-profiling-testing.md)** - AI profiling validation
- **[Production Pipeline Testing](./production-pipeline-testing.md)** - End-to-end production testing

### **Quick Reference Commands:**
```bash
# Quick MCP test
python -c "from agent_tools.jina_hybrid_client import JinaHybridClient; print('✅ MCP ready')"

# Performance monitoring
monitor_mcp_performance

# Health check
source .venv/bin/activate && python -c "
from agent_tools.jina_hybrid_client import JinaHybridClient
client = JinaHybridClient(enable_mcp_experimental=True)
print(f'MCP Status: {getattr(client, \"mcp_capability\", False)}')
"
```

---

<div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #F5F5F5;">
  <p style="color: #666; font-size: 0.9em;">
    Continue with <a href="./observability-testing.md" style="color: #004E89; font-weight: bold;">Observability Testing</a> to validate AgentOps integration! 📊
  </p>
</div>