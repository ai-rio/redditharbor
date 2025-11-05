# API Reference Documentation

<div style="text-align: center; margin: 20px 0;">
  <h2 style="color: #FF6B35;">RedditHarbor API Reference</h2>
  <p style="color: #004E89;">Complete API documentation and function reference</p>
</div>

## 📚 Available Documentation

### API Analysis & Testing
- **[API Rate Limit Analysis](./api-rate-limit-analysis.md)** - Comprehensive analysis of API rate limits for MiniMax, Z.AI, and OpenRouter APIs with testing results and recommendations

---

## 🔍 Find What You Need

<div style="background: #F5F5F5; padding: 20px; border-radius: 8px; margin: 20px 0;">
  <h3 style="color: #1A1A1A; margin-top: 0;">Quick Navigation</h3>
  <ul style="color: #1A1A1A;">
    <li><strong>Rate Limits:</strong> Understanding API constraints and best practices</li>
    <li><strong>API Testing:</strong> How to test API integrations</li>
    <li><strong>Error Handling:</strong> Managing 429 and other API errors</li>
    <li><strong>Best Practices:</strong> Optimizing API usage</li>
  </ul>
</div>

---

## 📊 Current API Status

### OpenRouter Integration ✅
- **Status:** Fully operational with Claude Haiku 4.5
- **Model:** `anthropic/claude-haiku-4.5`
- **Rate Limit:** 3-5 seconds between requests
- **Cost:** $0.000001/1K prompt, $0.000005/1K completion
- **Response Time:** ~1 second

### MiniMax API ⚠️
- **Status:** API key invalid
- **Issue:** Key needs regeneration
- **Documentation:** See [Rate Limit Analysis](./API_RATE_LIMIT_ANALYSIS.md)

### Z.AI GLM API ⚠️
- **Status:** Rate limited
- **Issue:** Immediate 429 errors even with delays
- **Recommendation:** Upgrade to paid tier
- **Documentation:** See [Rate Limit Analysis](./API_RATE_LIMIT_ANALYSIS.md)

---

## 🛠️ API Integration Guide

### OpenRouter Setup

```bash
# 1. Get API key from https://openrouter.ai/keys
echo "OPENROUTER_API_KEY=sk-or-v1-..." >> .env.local

# 2. Set model
echo "OPENROUTER_MODEL=anthropic/claude-haiku-4.5" >> .env.local

# 3. Run generation script
source .venv/bin/activate
python scripts/generate_opportunity_insights_openrouter.py
```

### Rate Limiting Best Practices

1. **Conservative Delays:** Use 3-5 second delays between requests
2. **Exponential Backoff:** Implement retry logic with increasing delays
3. **Request Tracking:** Monitor request counts and timing
4. **Error Handling:** Gracefully handle 429 and timeout errors

---

## 📖 Related Documentation

- **[Main Documentation](../README.md)** - Complete project overview
- **[Implementation Documentation](../implementation/README.md)** - Implementation guides and results
- **[Security Guide](../guides/security-guide.md)** - Security and privacy practices
- **[Architecture Documentation](../architecture/README.md)** - System design decisions

---

## 🚀 Getting Started

1. **Review API Limits:** Read the [Rate Limit Analysis](./API_RATE_LIMIT_ANALYSIS.md)
2. **Choose Provider:** Select appropriate API based on your needs
3. **Configure Credentials:** Set up API keys in `.env.local`
4. **Run Tests:** Use test scripts to verify integration
5. **Monitor Usage:** Track API usage and costs

---

<div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #F5F5F5;">
  <p style="color: #666; font-size: 0.9em;">
    Need help? Check our <a href="../guides/setup-checklist.md" style="color: #004E89;">Setup Checklist</a> or <a href="../guides/security-guide.md" style="color: #004E89;">Security Guide</a>
  </p>
</div>
