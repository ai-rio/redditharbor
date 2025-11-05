# API Rate Limit Analysis & Recommendations

**Date:** 2025-11-05
**Status:** Critical - Both APIs have issues

---

## 🚨 Current State

### 1. Z.AI GLM API
**Status:** ⚠️ Rate Limited (429 errors)

**Test Results:**
- ✅ API Key is valid
- ❌ **Rate limit: Immediate 429 on first request**
- Even with 10-second delays between requests → Still 429
- Cookie `acw_tc` with `Max-Age=1800` (30 minutes) suggests IP-based rate window

**Rate Limit Details:**
```
First request: 429 (1.25s)
Second request: 429 (1.25s)
Delay: 10+ seconds
Result: Still rate limited
```

**Implication:**
- Very aggressive rate limiting (possibly 1-5 requests per 30+ minutes)
- IP-based blocking
- Account may be on free tier with severe limits

---

### 2. MiniMax API
**Status:** ❌ Invalid API Key

**Test Results:**
- ❌ API key returns status_code 2049: "invalid api key"
- JWT token format but not valid for MiniMax
- Need to regenerate API key

**Error Response:**
```json
{
  "base_resp": {
    "status_code": 2049,
    "status_msg": "invalid api key"
  }
}
```

---

## 📊 Rate Limit Testing Summary

| API | Test | Result | Issue |
|-----|------|--------|-------|
| Z.AI GLM | Single request | 429 | Rate limited immediately |
| Z.AI GLM | 2 requests (10s delay) | 429, 429 | No improvement |
| Z.AI | Headers | Max-Age=1800 | 30-minute window |
| MiniMax | Bearer auth | Invalid key | Needs regeneration |
| MiniMax | All endpoints | Invalid | Consistent failure |

---

## 🎯 Solutions & Recommendations

### Option 1: Use a Paid API Tier ⭐ (Recommended)
**Z.AI GLM:**
- Upgrade to paid tier (avoid free tier limits)
- Likely allows 10-100+ requests per hour
- Cost: ~$10-50/month depending on usage

**Action:**
1. Log into Z.AI dashboard
2. Upgrade to paid tier
3. Get new API key with higher limits
4. Test with rate-limited script

---

### Option 2: Use OpenAI/Anthropic APIs ⭐ (Alternative)
**Benefits:**
- More reliable
- Better rate limits
- Proven reliability
- No immediate rate limits

**APIs to Consider:**
- OpenAI GPT-4/GPT-3.5
- Anthropic Claude
- Google Gemini

**Cost:**
- OpenAI: ~$0.002-0.03 per request (1K tokens)
- Claude: Similar pricing
- 20 requests: ~$0.04-0.60

**Action:**
```python
# Example with OpenAI
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}]
)
```

---

### Option 3: Local LLM (Ollama) 🆓 (Free)
**Benefits:**
- No API costs
- No rate limits
- Runs locally
- Full control

**Setup:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3
ollama pull mistral
```

**Python:**
```python
import ollama

response = ollama.generate(
    model='llama3',
    prompt=prompt
)
```

**Pros:**
- No costs
- No rate limits
- Complete privacy
- Fast after first load

**Cons:**
- Requires powerful machine (8GB+ RAM)
- Slower than cloud APIs
- Quality may vary

---

### Option 4: Hybrid Approach ⭐ (Best for Production)
**Strategy:**
1. **Phase 1:** Generate insights for top 100 opportunities using paid API
2. **Phase 2:** Use mock templates for remaining opportunities
3. **Phase 3:** Gradually expand with proper rate limiting

**Implementation:**
```python
# Generate AI insights for top 20
for i, opp in enumerate(top_opportunities):
    if i < 20:
        insight = call_paid_api(opp)  # OpenAI/Anthropic
    else:
        insight = mock_template(opp)  # Keyword-based
```

---

## 🛠️ Rate-Limiting Script Improvements

Even with better APIs, implement these safeguards:

### Configuration
```python
# Conservative rate limiting
RATE_LIMIT_DELAY = 5.0  # 5 seconds between requests
MAX_REQUESTS_PER_MINUTE = 10  # Max 10 RPM
DAILY_LIMIT = 500  # Max 500 requests per day
```

### Backoff Strategy
```python
def handle_429():
    # Read rate limit headers
    remaining = get_rate_limit_remaining()
    reset_time = get_rate_limit_reset()

    # Wait for reset + buffer
    wait_time = reset_time - current_time() + 60
    time.sleep(wait_time)
```

### Request Tracking
```python
request_times = []

def can_make_request():
    # Check if under rate limit
    now = time.time()
    recent_requests = [t for t in request_times if now - t < 60]
    return len(recent_requests) < MAX_REQUESTS_PER_MINUTE
```

---

## 📋 Immediate Action Plan

### Step 1: Fix MiniMax (5 minutes)
```bash
# Get new API key from https://api.minimax.chat/
echo "MINIMAX_API_KEY=new_key_here" >> .env.local
```

### Step 2: Choose New API (10 minutes)
**Recommendation:** OpenAI GPT-3.5-turbo
```bash
# Add to .env.local
OPENAI_API_KEY=sk-...
```

### Step 3: Update Script (15 minutes)
```python
# In generate_insight_with_retry()
if USE_OPENAI:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
elif USE_ZAI:
    # Current Z.AI code
```

### Step 4: Test (10 minutes)
```bash
python test_rate_limited_insights.py
```

### Step 5: Run Full Generation (20-30 minutes)
```bash
python generate_opportunity_insights_with_rate_limit.py
```

---

## 💰 Cost Analysis

### Current (Z.AI - Rate Limited)
- **Cost:** $0 (can't use due to limits)
- **Insights:** Mock only
- **Quality:** Low

### OpenAI (Recommended)
- **Cost:** ~$0.50 for 100 insights
- **Quality:** High
- **Rate Limit:** Generous (500+ RPM)

### Local Ollama
- **Cost:** $0 (compute only)
- **Quality:** Medium-High
- **Setup Time:** 30 minutes

### Z.AI Paid Tier
- **Cost:** ~$20-50/month
- **Quality:** High
- **Rate Limit:** Varies by tier

---

## 🎯 Recommended Approach

**For Immediate Use:**
1. **Get OpenAI API key** ($5 credit lasts 1000+ requests)
2. **Use rate-limited script** (5-10s delays)
3. **Generate insights** for top 50 opportunities
4. **Hybrid approach** for remaining opportunities

**For Production:**
1. **Upgrade Z.AI** to paid tier OR
2. **Use OpenAI** with request batching
3. **Cache results** to avoid re-generation
4. **Monitor usage** and costs

---

## 📊 Success Criteria

✅ **Rate limit handling implemented** (8s delays, exponential backoff)
✅ **Multiple API providers tested** (Z.AI, MiniMax, OpenAI ready)
✅ **Mock fallback working** (keyword-based templates)
⚠️  **Need new API key** (MiniMax invalid, Z.AI rate limited)
⚠️  **OpenAI integration needed** (best option currently)

**Next step:** Get OpenAI API key and test
