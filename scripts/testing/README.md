# RedditHarbor Testing Suite

This directory contains comprehensive testing scripts for validating RedditHarbor functionality, including integration tests, performance tests, and validation utilities.

## 📊 **Test Categories**

### **🔧 Integration Tests**
| Test File | Purpose | Status |
|-----------|---------|--------|
| **test_hybrid_integration.py** | Complete Jina MCP integration testing | ✅ Production Ready |
| **test_final_validation.py** | End-to-end system validation | ✅ Production Ready |
| **test_market_validation_integration.py** | Market validation pipeline testing | ✅ Production Ready |

### **🤖 AgentOps Observability Tests**
| Test File | Purpose | Status |
|-----------|---------|--------|
| **test_agentops_observability.py** | Advanced AgentOps monitoring and cost tracking | ✅ Development Complete |
| **test_simple_agentops.py** | Basic AgentOps functionality testing | ✅ Development Complete |
| **test_agentops_auth.py** | AgentOps authentication and API validation | ✅ Development Complete |

### **🔄 MCP Integration Tests**
| Test File | Purpose | Status |
|-----------|---------|--------|
| **test_mcp_jina_integration.py** | Direct Jina MCP server integration | ✅ Development Complete |
| **test_simple_mcp_integration.py** | Basic MCP functionality validation | ✅ Development Complete |

### **💰 Cost & Performance Tests**
| Test File | Purpose | Status |
|-----------|---------|--------|
| **test_cost_tracking_pipeline.py** | LLM cost tracking and optimization | ✅ Production Ready |
| **test_hybrid_strategy_with_high_scores.py** | High-scoring opportunity validation | ✅ Production Ready |

### **📈 Data & Lead Tests**
| Test File | Purpose | Status |
|-----------|---------|--------|
| **test_option_b_leads.py** | Lead generation and validation testing | ✅ Production Ready |
| **test_save_leads.py** | Lead persistence and storage testing | ✅ Production Ready |

## 🚀 **Quick Start**

### **Run Production Tests**
```bash
# Test core Jina MCP integration
uv run scripts/testing/test_hybrid_integration.py

# Test end-to-end validation
uv run scripts/testing/test_final_validation.py

# Test market validation pipeline
uv run scripts/testing/test_market_validation_integration.py
```

### **Run Development Tests**
```bash
# Test AgentOps integration
uv run scripts/testing/test_agentops_observability.py

# Test MCP capabilities
uv run scripts/testing/test_mcp_jina_integration.py

# Test authentication
uv run scripts/testing/test_agentops_auth.py
```

### **Run Performance Tests**
```bash
# Test cost tracking
uv run scripts/testing/test_cost_tracking_pipeline.py

# Test high-score strategy
uv run scripts/testing/test_hybrid_strategy_with_high_scores.py
```

## 📋 **Test Execution Guidelines**

### **Before Running Tests**
1. **Environment Setup**:
   ```bash
   # Ensure all environment variables are set
   echo "JINA_API_KEY: ${JINA_API_KEY:0:10}..."
   echo "AGENTOPS_API_KEY: ${AGENTOPS_API_KEY:0:10}..."
   echo "OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:0:10}..."
   ```

2. **Dependencies Check**:
   ```bash
   # Verify required packages
   uv pip list | grep -E "(jina|agentops|agno)"
   ```

3. **Database Status**:
   ```bash
   # Check Supabase connection
   supabase status
   ```

### **Test Categories by Purpose**

#### **🏭 Production Validation**
- Use for pre-deployment verification
- Run daily to ensure system health
- Critical for production monitoring

#### **🔬 Development Testing**
- Use during feature development
- Validate new integrations
- Debug specific functionality

#### **📊 Performance Analysis**
- Monitor system performance
- Track cost optimization
- Analyze efficiency metrics

#### **🧪 Integration Validation**
- Test third-party service integrations
- Validate API connectivity
- Ensure data flow integrity

## 🔧 **Test Configuration**

### **Environment Variables Required**
```bash
# Core API Keys
JINA_API_KEY=your_jina_key_here
AGENTOPS_API_KEY=your_agentops_key_here
OPENROUTER_API_KEY=your_openrouter_key_here

# Rate Limiting
JINA_READ_RPM_LIMIT=500
JINA_SEARCH_RPM_LIMIT=100
JINA_REQUEST_TIMEOUT=30
```

### **Test Data Requirements**
- Reddit data access via configured APIs
- Supabase database connection
- Network connectivity for external services

## 📈 **Test Results Interpretation**

### **Success Indicators**
- ✅ All tests pass without errors
- ✅ Response times within expected ranges
- ✅ Cost tracking reports accurate metrics
- ✅ MCP capabilities detected where expected

### **Common Issues & Solutions**
| Issue | Cause | Solution |
|-------|--------|----------|
| Rate limit errors | Too many API calls | Check rate limiting settings |
| Authentication failures | Missing/expired API keys | Verify environment variables |
| MCP detection fails | MCP server not available | Graceful fallback to HTTP client |
| Database connection errors | Supabase offline | Check `supabase status` |

## 📚 **Documentation References**

### **Related Documentation**
- **[Jina Integration](../../docs/integrations/jina/)** - Jina Reader API integration
- **[AgentOps Integration](../../docs/integrations/agentops/)** - Observability and cost tracking
- **[MCP Integration Status](../../docs/integrations/mcp-integration-status.md)** - MCP capabilities and status
- **[Implementation Guide](../../docs/implementation/)** - Architecture and implementation details

### **Development Resources**
- **[Cleanup Analysis](../../docs/implementation/jina-mcp-cleanup-analysis.md)** - File organization and cleanup
- **[Market Validation](../../docs/integrations/jina/market-validation-implementation.md)** - Validation pipeline documentation

## 🛠️ **Maintenance**

### **Regular Tasks**
1. **Weekly**: Run production validation tests
2. **Monthly**: Review and update test configurations
3. **Quarterly**: Archive obsolete test files to `scripts/archive/`

### **Test File Organization**
- **Active Tests**: Current production and development tests
- **Archive Tests**: Moved to `scripts/archive/testing/` when obsolete
- **Documentation**: Keep README updated with current test status

## 🎯 **Best Practices**

1. **Run tests in sequence**: Start with basic functionality, then integration
2. **Monitor costs**: Use AgentOps dashboard during test execution
3. **Check logs**: Review `agentops.log` for detailed trace information
4. **Validate results**: Cross-check test outputs with expected behavior
5. **Document issues**: Track any test failures with detailed reproduction steps

---

**Last Updated**: 2025-11-17
**Maintainer**: RedditHarbor Development Team
**For issues**: Use project issues and include test logs