# Building a False Claim Prevention Claude Code Hook

**Research Report**
**Date:** 2025-12-06
**Query:** How to build a false claim prevention Claude Code hook
**Confidence Level:** High (based on official documentation and recent research)

---

## Executive Summary

This report provides a comprehensive guide to building a Claude Code hook that prevents false claims by intercepting Claude's tool calls before execution. The implementation combines Claude Code's PreToolUse hook system with modern fact-checking and hallucination detection techniques to validate claims in real-time.

**Key Findings:**
- PreToolUse hooks provide the ideal interception point for claim validation
- Multiple fact-checking APIs are available (Google Fact Check API, ClaimBuster)
- Modern LLM hallucination detection techniques can be integrated
- Hooks can block, allow, or request user confirmation for tool execution
- Implementation can be done in Python with minimal overhead

---

## Table of Contents

1. [Claude Code Hooks Architecture](#1-claude-code-hooks-architecture)
2. [False Claim Detection Techniques](#2-false-claim-detection-techniques)
3. [Implementation Approaches](#3-implementation-approaches)
4. [Code Examples](#4-code-examples)
5. [Integration with Fact-Checking APIs](#5-integration-with-fact-checking-apis)
6. [Best Practices](#6-best-practices)
7. [Testing and Validation](#7-testing-and-validation)
8. [References](#references)

---

## 1. Claude Code Hooks Architecture

### 1.1 What are Claude Code Hooks?

Claude Code hooks are user-defined shell commands that execute at various lifecycle events, providing deterministic control over Claude's behavior. They are configured in settings files and can intercept, modify, or block tool executions.

**Available Hook Events:**
- `PreToolUse` - Before tool execution (can block)
- `PostToolUse` - After tool completion
- `UserPromptSubmit` - When user submits a prompt
- `Stop` - When Claude finishes responding
- `SessionStart` - When session begins
- `SessionEnd` - When session ends

**Source:** [Claude Code Hooks Documentation](https://code.claude.com/docs/en/hooks)

### 1.2 Why PreToolUse is Ideal for False Claim Prevention

The `PreToolUse` hook is the **only event that can proactively block tool execution**. It runs after Claude creates tool parameters but before processing the tool call, making it perfect for:

- Validating claims before they're communicated
- Checking factual statements before writing to files
- Verifying information before executing commands
- Preventing hallucinations from reaching users

**Execution Flow:**
1. Claude decides to use a tool (Write, Edit, Bash, etc.)
2. PreToolUse hook intercepts the tool call
3. Hook analyzes the content for false claims
4. Hook returns decision: allow, deny, or ask for confirmation
5. Tool proceeds or is blocked based on decision

**Source:** [Hooks Reference - Claude Docs](https://docs.claude.com/en/docs/claude-code/hooks)

### 1.3 Hook Configuration

Hooks are configured in Claude Code settings with matchers to target specific tools:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/false_claim_detector.py"
          }
        ]
      }
    ]
  }
}
```

**Matcher Patterns:**
- `Write|Edit` - File operations
- `Bash` - Shell commands
- `*` or `""` - All tools
- Regular expressions for complex patterns

**Source:** [Claude Code Hooks Mastery](https://github.com/disler/claude-code-hooks-mastery)

---

## 2. False Claim Detection Techniques

### 2.1 Modern Hallucination Detection Methods (2024-2025)

Recent research has identified several effective techniques for detecting false claims and hallucinations in LLM outputs:

#### 2.1.1 LLM-Check (NeurIPS 2024)

**Approach:** Eigenvalue analysis of internal LLM representations and output token uncertainty quantification

**Benefits:**
- Extremely compute-efficient (45x-450x speedup over baselines)
- Works with both white-box and gray-box models
- No external knowledge base required

**Source:** [LLM-Check Research](https://github.com/GaurangSriramanan/LLM_Check_Hallucination_Detection)

#### 2.1.2 Semantic Entropy (Nature 2024)

**Approach:** Measures uncertainty about the meanings of generated responses rather than the text itself

**Benefits:**
- Detects confabulations (arbitrary and incorrect generations)
- Entropy-based uncertainty estimators
- Language-agnostic approach

**Source:** [Semantic Entropy Research](https://www.nature.com/articles/s41586-024-07421-0)

#### 2.1.3 AutoFactNLI / HaluCheck

**Approach:** Decomposes responses into atomic facts for automated verification

**Benefits:**
- Grounds assessments in external, verifiable knowledge sources
- Explainable verification results
- Integrates multiple detection methods

**Source:** [HaluCheck System](https://www.sciencedirect.com/science/article/abs/pii/S0957417425003343)

#### 2.1.4 MetaQA Framework (ACM 2025)

**Approach:** Uses metamorphic prompt mutations to detect hallucinations in closed-source models

**Benefits:**
- Works without token probabilities or internal access
- Applicable to API-based LLMs like Claude
- No external tools required

**Source:** [LLM Hallucination Detection Techniques](https://www.deepchecks.com/llm-hallucination-detection-and-mitigation-best-techniques/)

### 2.2 Fact-Checking APIs

#### 2.2.1 Google Fact Check API

**Capabilities:**
- Query existing fact-checks from verified publishers
- Access ClaimReview structured data
- Search by claim text or URL

**API Access:**
- Requires API key from Google Cloud Console
- Free tier available with rate limits
- RESTful JSON API

**Endpoint Example:**
```
GET https://factchecktools.googleapis.com/v1alpha1/claims:search?query={claim}&key={API_KEY}
```

**Source:** [Google Fact Check Tools API](https://developers.google.com/fact-check/tools/api)

#### 2.2.2 ClaimBuster API

**Capabilities:**
- Identifies claims worth fact-checking (claim detection)
- Scores claims by check-worthiness (0-1 scale)
- Processes text in real-time

**API Access:**
- Free API key via registration
- Rate limits apply
- RESTful JSON API

**Endpoint Example:**
```
POST https://idir.uta.edu/claimbuster/api/v2/score/text/
Body: {"input_text": "claim to check"}
Response: {"results": [{"score": 0.85, "text": "..."}]}
```

**Source:** [ClaimBuster System](https://idir.uta.edu/claimbuster/)

### 2.3 Traditional Validation Techniques

#### 2.3.1 Log Probability Analysis

**Approach:** Assess token-level probabilities to gauge confidence

**Implementation:** Access token log probabilities if available (requires white-box access)

#### 2.3.2 Sentence Similarity

**Approach:** Compare generated text to source material using embeddings

**Implementation:** Use models like sentence-transformers to compute semantic similarity

#### 2.3.3 External Knowledge Grounding

**Approach:** Verify claims against trusted knowledge bases

**Sources:** Wikipedia, Wikidata, domain-specific databases

**Source:** [LLM Hallucination Detection Best Practices](https://www.lakera.ai/blog/guide-to-hallucinations-in-large-language-models)

---

## 3. Implementation Approaches

### 3.1 Architecture Options

#### Option A: Lightweight Pattern Matching

**Best for:** Simple, fast validation without external dependencies

**Components:**
- Keyword/pattern matching for known false claim categories
- Confidence score threshold checking
- Rule-based validation

**Pros:**
- Fast execution (< 100ms)
- No API dependencies
- Easy to maintain

**Cons:**
- Limited detection accuracy
- Requires manual rule updates
- Misses novel false claims

#### Option B: API-Based Fact Checking

**Best for:** Production systems requiring high accuracy

**Components:**
- Google Fact Check API integration
- ClaimBuster claim detection
- Caching layer for performance

**Pros:**
- High accuracy with verified sources
- Continuously updated fact-check database
- Explainable results

**Cons:**
- Network latency (200-500ms)
- API rate limits
- Requires internet connection

#### Option C: Hybrid Local + Cloud

**Best for:** Balancing speed and accuracy

**Components:**
- Local fast-path validation (pattern matching)
- Cloud API for uncertain cases
- Confidence threshold routing

**Pros:**
- Fast for common cases (< 100ms)
- Accurate for complex claims
- Graceful degradation

**Cons:**
- More complex implementation
- Requires fallback logic

### 3.2 Decision Flow

```
Claude generates tool call
        ↓
PreToolUse hook intercepts
        ↓
Extract claims from content
        ↓
    ┌───────────────────┐
    │ Local Validation  │ (Pattern matching, confidence scoring)
    └─────────┬─────────┘
              │
      ┌───────┴────────┐
      │                │
   PASS             UNCERTAIN
      │                │
      ↓                ↓
   ALLOW      ┌──────────────┐
              │  API Check   │ (Google/ClaimBuster)
              └──────┬───────┘
                     │
              ┌──────┴───────┐
              │              │
           VERIFIED      FALSE CLAIM
              │              │
              ↓              ↓
           ALLOW          DENY/ASK
```

### 3.3 Performance Considerations

**Target Response Times:**
- Local validation: < 100ms
- API validation: < 500ms
- Total hook execution: < 1000ms (recommended)

**Caching Strategy:**
- Cache API responses for 24 hours
- Use claim text hash as cache key
- Store in SQLite or JSON file

**Error Handling:**
- Timeout after 10 seconds
- Fallback to "ask" on network errors
- Log failures for debugging

---

## 4. Code Examples

### 4.1 Basic PreToolUse Hook Structure

```python
#!/usr/bin/env python3
"""
False Claim Prevention Hook for Claude Code
Intercepts tool calls and validates content for false claims
"""
import json
import sys
import re
from typing import Dict, List, Optional

def validate_content(content: str, tool_name: str) -> tuple[bool, Optional[str]]:
    """
    Validate content for false claims.

    Returns:
        (is_valid, reason) - True if content passes validation
    """
    # Implementation will be added in later sections
    pass

def main():
    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract tool information
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only validate content-producing tools
    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        sys.exit(0)  # Allow other tools without validation

    # Extract content to validate
    content = tool_input.get("content", "")
    if not content:
        sys.exit(0)  # No content to validate

    # Validate content
    is_valid, reason = validate_content(content, tool_name)

    if not is_valid:
        # Return JSON decision to block execution
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"False claim detected: {reason}"
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    # Allow execution
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### 4.2 Pattern-Based Claim Detection

```python
#!/usr/bin/env python3
"""
Pattern-based false claim detection
Detects common false claim patterns without external APIs
"""
import re
from typing import List, Tuple

# Known false claim patterns
FALSE_CLAIM_PATTERNS = [
    # Absolute statements without evidence
    (r'\b(always|never|all|none|everyone|nobody)\s+\w+\b',
     "Absolute statement detected - consider qualifying language"),

    # Unverified statistics
    (r'\b\d+%\s+of\s+(?:people|users|developers)\b',
     "Unverified percentage claim - verify with source"),

    # Unsupported superlatives
    (r'\b(best|worst|fastest|slowest|most|least)\s+\w+\s+in\s+the\s+world\b',
     "Superlative claim requires verification"),

    # Common misinformation triggers
    (r'\bstudies show\b|\bresearch shows\b|\bexperts say\b',
     "Vague attribution - specify source"),
]

# Confidence-lowering phrases that may indicate uncertainty
UNCERTAINTY_MARKERS = [
    r'\bmight\b', r'\bcould\b', r'\bpossibly\b', r'\bprobably\b',
    r'\blikely\b', r'\bseems\b', r'\bappears\b', r'\bmay\b'
]

def detect_false_claim_patterns(text: str) -> List[Tuple[str, str]]:
    """
    Detect potential false claims using pattern matching.

    Returns:
        List of (pattern, reason) tuples for detected issues
    """
    issues = []

    # Check for false claim patterns
    for pattern, reason in FALSE_CLAIM_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            match = re.search(pattern, text, re.IGNORECASE)
            issues.append((match.group(0), reason))

    # Count uncertainty markers
    uncertainty_count = sum(
        1 for marker in UNCERTAINTY_MARKERS
        if re.search(marker, text, re.IGNORECASE)
    )

    # If too many uncertainty markers, content may be speculative
    if uncertainty_count > 3:
        issues.append(
            ("Multiple uncertainty markers",
             "Content contains speculative language")
        )

    return issues

def validate_content(content: str, tool_name: str) -> Tuple[bool, str]:
    """
    Validate content for false claims using pattern matching.

    Returns:
        (is_valid, reason)
    """
    issues = detect_false_claim_patterns(content)

    if issues:
        # Format issues for display
        reason = "\n".join([f"• {text}: {msg}" for text, msg in issues])
        return False, reason

    return True, ""
```

### 4.3 API-Based Fact Checking

```python
#!/usr/bin/env python3
"""
API-based fact checking using ClaimBuster and Google Fact Check API
"""
import requests
import hashlib
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, List

class FactChecker:
    def __init__(self, cache_path: str = "~/.claude-code/fact_check_cache.db"):
        self.cache_path = cache_path
        self._init_cache()

    def _init_cache(self):
        """Initialize SQLite cache for API results"""
        conn = sqlite3.connect(self.cache_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fact_checks (
                claim_hash TEXT PRIMARY KEY,
                claim_text TEXT,
                result TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _get_claim_hash(self, claim: str) -> str:
        """Generate hash for claim caching"""
        return hashlib.sha256(claim.encode()).hexdigest()

    def _check_cache(self, claim: str) -> Optional[Dict]:
        """Check if claim result is cached and recent"""
        claim_hash = self._get_claim_hash(claim)
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.execute(
            "SELECT result, timestamp FROM fact_checks WHERE claim_hash = ?",
            (claim_hash,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            result, timestamp = row
            # Cache valid for 24 hours
            cache_time = datetime.fromisoformat(timestamp)
            if datetime.now() - cache_time < timedelta(hours=24):
                return json.loads(result)

        return None

    def _cache_result(self, claim: str, result: Dict):
        """Cache fact check result"""
        claim_hash = self._get_claim_hash(claim)
        conn = sqlite3.connect(self.cache_path)
        conn.execute(
            """
            INSERT OR REPLACE INTO fact_checks
            (claim_hash, claim_text, result, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (claim_hash, claim, json.dumps(result), datetime.now().isoformat())
        )
        conn.commit()
        conn.close()

    def check_with_claimbuster(self, claim: str, api_key: str) -> Dict:
        """
        Check claim worthiness using ClaimBuster API.

        Returns:
            {
                "score": 0.0-1.0,  # Higher = more worth checking
                "claim": "...",
                "requires_checking": bool
            }
        """
        # Check cache first
        cached = self._check_cache(f"claimbuster:{claim}")
        if cached:
            return cached

        try:
            response = requests.post(
                "https://idir.uta.edu/claimbuster/api/v2/score/text/",
                json={"input_text": claim},
                headers={"x-api-key": api_key},
                timeout=5
            )
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            if results:
                max_score = max(r.get("score", 0) for r in results)
                result = {
                    "score": max_score,
                    "claim": claim,
                    "requires_checking": max_score > 0.5
                }
                self._cache_result(f"claimbuster:{claim}", result)
                return result

        except Exception as e:
            return {
                "score": 0.0,
                "claim": claim,
                "requires_checking": False,
                "error": str(e)
            }

    def check_with_google(self, claim: str, api_key: str) -> List[Dict]:
        """
        Check claim against Google Fact Check API.

        Returns:
            List of fact check results with ratings
        """
        # Check cache first
        cached = self._check_cache(f"google:{claim}")
        if cached:
            return cached

        try:
            response = requests.get(
                "https://factchecktools.googleapis.com/v1alpha1/claims:search",
                params={
                    "query": claim,
                    "key": api_key
                },
                timeout=5
            )
            response.raise_for_status()

            data = response.json()
            claims = data.get("claims", [])

            results = []
            for claim_review in claims:
                for review in claim_review.get("claimReview", []):
                    results.append({
                        "claim": claim_review.get("text", ""),
                        "rating": review.get("textualRating", ""),
                        "url": review.get("url", ""),
                        "publisher": review.get("publisher", {}).get("name", "")
                    })

            self._cache_result(f"google:{claim}", results)
            return results

        except Exception as e:
            return [{"error": str(e)}]

def extract_claims(text: str) -> List[str]:
    """
    Extract factual claims from text.
    Simple implementation - can be enhanced with NLP.
    """
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)

    # Filter to declarative statements (simple heuristic)
    claims = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 10:
            continue

        # Look for factual indicators
        factual_indicators = [
            r'\bis\b', r'\bare\b', r'\bwas\b', r'\bwere\b',
            r'\bhas\b', r'\bhave\b', r'\bwill\b',
            r'\d+%', r'\b\d+\s+(?:million|billion|thousand)\b'
        ]

        if any(re.search(indicator, sentence, re.IGNORECASE)
               for indicator in factual_indicators):
            claims.append(sentence)

    return claims
```

### 4.4 Complete Hybrid Implementation

```python
#!/usr/bin/env python3
"""
Complete false claim prevention hook combining local and API validation
"""
import json
import sys
import os
import re
from typing import Dict, List, Tuple, Optional

# Import previous implementations
# from pattern_detector import detect_false_claim_patterns
# from fact_checker import FactChecker, extract_claims

# Configuration
ENABLE_API_CHECKING = os.getenv("ENABLE_API_FACT_CHECK", "false").lower() == "true"
CLAIMBUSTER_API_KEY = os.getenv("CLAIMBUSTER_API_KEY", "")
GOOGLE_FACTCHECK_API_KEY = os.getenv("GOOGLE_FACTCHECK_API_KEY", "")
CLAIM_SCORE_THRESHOLD = 0.7  # ClaimBuster score threshold

def validate_content_hybrid(
    content: str,
    tool_name: str,
    fact_checker: Optional[FactChecker] = None
) -> Tuple[str, Optional[str]]:
    """
    Hybrid validation: fast local check + API verification for uncertain cases.

    Returns:
        ("allow" | "deny" | "ask", reason)
    """
    # Step 1: Fast local pattern matching
    pattern_issues = detect_false_claim_patterns(content)

    if pattern_issues and not ENABLE_API_CHECKING:
        # No API checking - deny based on patterns alone
        reason = "\n".join([f"• {text}: {msg}" for text, msg in pattern_issues])
        return "deny", f"Pattern validation failed:\n{reason}"

    # Step 2: API-based fact checking (if enabled)
    if ENABLE_API_CHECKING and fact_checker:
        claims = extract_claims(content)

        high_risk_claims = []
        false_claims = []

        for claim in claims:
            # Check claim worthiness with ClaimBuster
            if CLAIMBUSTER_API_KEY:
                cb_result = fact_checker.check_with_claimbuster(
                    claim, CLAIMBUSTER_API_KEY
                )

                if cb_result.get("requires_checking"):
                    high_risk_claims.append(claim)

                    # Verify high-risk claims with Google
                    if GOOGLE_FACTCHECK_API_KEY:
                        google_results = fact_checker.check_with_google(
                            claim, GOOGLE_FACTCHECK_API_KEY
                        )

                        # Check for "False" or "Misleading" ratings
                        for result in google_results:
                            rating = result.get("rating", "").lower()
                            if any(x in rating for x in ["false", "misleading", "incorrect"]):
                                false_claims.append({
                                    "claim": claim,
                                    "rating": result.get("rating"),
                                    "source": result.get("publisher")
                                })

        if false_claims:
            # Definite false claims found - deny
            reasons = [
                f"• \"{fc['claim']}\"\n  Rating: {fc['rating']} (Source: {fc['source']})"
                for fc in false_claims
            ]
            return "deny", "False claims detected:\n" + "\n".join(reasons)

        if high_risk_claims:
            # High-risk claims without verification - ask user
            return "ask", f"Content contains {len(high_risk_claims)} claim(s) requiring verification"

    # Step 3: Pattern issues but API enabled - ask user
    if pattern_issues:
        return "ask", "Potential issues detected - please review"

    # All checks passed
    return "allow", None

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only validate content-producing tools
    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        sys.exit(0)

    content = tool_input.get("content", "")
    if not content:
        sys.exit(0)

    # Initialize fact checker if API checking enabled
    fact_checker = None
    if ENABLE_API_CHECKING:
        fact_checker = FactChecker()

    # Validate content
    decision, reason = validate_content_hybrid(content, tool_name, fact_checker)

    # Build hook response
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision
        }
    }

    if reason:
        output["hookSpecificOutput"]["permissionDecisionReason"] = reason

    print(json.dumps(output))
    sys.exit(0)

if __name__ == "__main__":
    main()
```

**Source:** Implementation patterns adapted from [Claude Code Hooks Mastery](https://github.com/disler/claude-code-hooks-mastery)

---

## 5. Integration with Fact-Checking APIs

### 5.1 Setting Up Google Fact Check API

**Steps:**

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing

2. **Enable Fact Check Tools API**
   - Navigate to "APIs & Services" > "Library"
   - Search for "Fact Check Tools API"
   - Click "Enable"

3. **Create API Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy API key and store securely

4. **Configure Environment**
   ```bash
   export GOOGLE_FACTCHECK_API_KEY="your_api_key_here"
   ```

5. **Test API Access**
   ```bash
   curl "https://factchecktools.googleapis.com/v1alpha1/claims:search?query=climate%20change&key=YOUR_API_KEY"
   ```

**Rate Limits:**
- Free tier: 1,000 queries/day
- Quota increases available on request

**Source:** [Google Fact Check Tools API Documentation](https://developers.google.com/fact-check/tools/api)

### 5.2 Setting Up ClaimBuster API

**Steps:**

1. **Register for API Access**
   - Visit [ClaimBuster](https://idir.uta.edu/claimbuster/)
   - Click "API Access" or "Register"
   - Complete registration form

2. **Obtain API Key**
   - Check email for API key
   - Store securely in environment variables

3. **Configure Environment**
   ```bash
   export CLAIMBUSTER_API_KEY="your_api_key_here"
   ```

4. **Test API Access**
   ```bash
   curl -X POST \
     https://idir.uta.edu/claimbuster/api/v2/score/text/ \
     -H "x-api-key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"input_text": "The economy grew by 5% last year"}'
   ```

**Rate Limits:**
- Free tier: Rate limits apply (check documentation)
- Contact for higher quotas

**Source:** [ClaimBuster Documentation](https://idir.uta.edu/claimbuster/)

### 5.3 Error Handling and Fallbacks

```python
def safe_api_call(api_func, *args, **kwargs):
    """
    Safely call API with timeout and error handling.
    Returns (success, result_or_error)
    """
    try:
        result = api_func(*args, **kwargs, timeout=5)
        return True, result
    except requests.Timeout:
        return False, "API timeout - network issue"
    except requests.RequestException as e:
        return False, f"API error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

# Usage in hook
success, result = safe_api_call(
    fact_checker.check_with_google,
    claim,
    GOOGLE_FACTCHECK_API_KEY
)

if not success:
    # Fallback to local validation or ask user
    return "ask", f"Could not verify claim: {result}"
```

---

## 6. Best Practices

### 6.1 Performance Optimization

**1. Implement Aggressive Caching**
```python
# Cache API results for 24 hours
# Use SQLite for persistence across sessions
# Cache both positive and negative results
```

**2. Use Timeout Guards**
```python
# Set 5-second timeout for API calls
# Total hook execution < 10 seconds
# Graceful degradation on timeout
```

**3. Parallel API Calls**
```python
import concurrent.futures

def check_multiple_claims(claims: List[str]) -> List[Dict]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(fact_checker.check_with_google, claim, api_key)
            for claim in claims
        ]
        return [f.result(timeout=5) for f in futures]
```

### 6.2 User Experience

**1. Informative Error Messages**
```python
# Bad
return "deny", "False claim detected"

# Good
return "deny", """False claim detected:
• Claim: "95% of developers use this tool"
• Rating: Misleading
• Source: FactCheck.org
• Reason: Actual usage is ~40% according to Stack Overflow Survey 2024
"""
```

**2. Graduated Responses**
- **Allow**: High-confidence, verified content
- **Ask**: Uncertain or unverified claims (let user decide)
- **Deny**: Definite false claims with evidence

**3. Non-Blocking for Internal Code**
```python
# Don't block code comments or internal documentation
if tool_name == "Edit" and is_code_file(file_path):
    # More lenient validation for code
    pass
```

### 6.3 Security Considerations

**1. API Key Management**
```bash
# Store in environment variables, never in code
export GOOGLE_FACTCHECK_API_KEY="..."
export CLAIMBUSTER_API_KEY="..."

# Use .env file with proper permissions
chmod 600 .env
```

**2. Input Sanitization**
```python
def sanitize_claim(claim: str) -> str:
    # Remove potential injection attempts
    claim = claim.replace('\x00', '')  # Null bytes
    claim = claim[:1000]  # Limit length
    return claim.strip()
```

**3. Rate Limiting**
```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()

    def allow_call(self) -> bool:
        now = time.time()
        # Remove old calls outside time window
        while self.calls and self.calls[0] < now - self.time_window:
            self.calls.popleft()

        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False
```

### 6.4 Configuration Management

**Example Configuration File** (`~/.claude-code/false_claim_config.json`):

```json
{
  "enabled": true,
  "validation_mode": "hybrid",
  "local_validation": {
    "enabled": true,
    "patterns": "standard"
  },
  "api_validation": {
    "enabled": true,
    "claimbuster": {
      "enabled": true,
      "score_threshold": 0.7
    },
    "google": {
      "enabled": true,
      "check_on_high_risk": true
    }
  },
  "performance": {
    "cache_ttl_hours": 24,
    "api_timeout_seconds": 5,
    "max_hook_execution_seconds": 10
  },
  "behavior": {
    "block_definite_false_claims": true,
    "ask_on_uncertain": true,
    "allow_code_files": true
  }
}
```

---

## 7. Testing and Validation

### 7.1 Unit Tests

```python
import unittest
from false_claim_detector import detect_false_claim_patterns, extract_claims

class TestFalseClaimDetection(unittest.TestCase):
    def test_absolute_statement_detection(self):
        text = "Everyone knows that Python is always better than JavaScript"
        issues = detect_false_claim_patterns(text)
        self.assertTrue(len(issues) > 0)
        self.assertIn("Absolute statement", issues[0][1])

    def test_unverified_statistics(self):
        text = "95% of developers prefer this framework"
        issues = detect_false_claim_patterns(text)
        self.assertTrue(any("percentage" in issue[1].lower() for issue in issues))

    def test_valid_content_passes(self):
        text = "This function implements the quicksort algorithm"
        issues = detect_false_claim_patterns(text)
        self.assertEqual(len(issues), 0)

    def test_claim_extraction(self):
        text = """
        Python is a popular programming language.
        It was created in 1991.
        Many developers use it for data science.
        """
        claims = extract_claims(text)
        self.assertTrue(len(claims) >= 2)

if __name__ == "__main__":
    unittest.main()
```

### 7.2 Integration Tests

```python
import unittest
from unittest.mock import patch, MagicMock
from fact_checker import FactChecker

class TestFactCheckerIntegration(unittest.TestCase):
    def setUp(self):
        self.fact_checker = FactChecker(cache_path=":memory:")

    @patch('requests.post')
    def test_claimbuster_api(self, mock_post):
        mock_post.return_value.json.return_value = {
            "results": [{"score": 0.85, "text": "Test claim"}]
        }

        result = self.fact_checker.check_with_claimbuster(
            "Test claim",
            "fake_api_key"
        )

        self.assertEqual(result["score"], 0.85)
        self.assertTrue(result["requires_checking"])

    @patch('requests.get')
    def test_google_factcheck_api(self, mock_get):
        mock_get.return_value.json.return_value = {
            "claims": [{
                "text": "Test claim",
                "claimReview": [{
                    "textualRating": "False",
                    "url": "https://example.com",
                    "publisher": {"name": "FactCheck.org"}
                }]
            }]
        }

        results = self.fact_checker.check_with_google(
            "Test claim",
            "fake_api_key"
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["rating"], "False")

    def test_caching(self):
        # First call - no cache
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                "results": [{"score": 0.9}]
            }
            result1 = self.fact_checker.check_with_claimbuster(
                "Cached claim",
                "key"
            )

        # Second call - should use cache (no API call)
        with patch('requests.post') as mock_post:
            result2 = self.fact_checker.check_with_claimbuster(
                "Cached claim",
                "key"
            )
            mock_post.assert_not_called()

        self.assertEqual(result1, result2)

if __name__ == "__main__":
    unittest.main()
```

### 7.3 End-to-End Testing

**Test Scenarios:**

1. **Verified True Claim**
   - Input: "Python was created by Guido van Rossum"
   - Expected: Allow (verified fact)

2. **Known False Claim**
   - Input: "JavaScript was invented in 1960"
   - Expected: Deny with source

3. **Unverified Claim**
   - Input: "95% of Fortune 500 companies use our product"
   - Expected: Ask (requires verification)

4. **Code Content**
   - Input: Code file with implementation
   - Expected: Allow (code not fact-checked)

5. **Network Timeout**
   - Simulate: API timeout
   - Expected: Fallback to local validation or ask

**Test Script:**

```bash
#!/bin/bash
# test_hook.sh - End-to-end hook testing

test_hook() {
    local tool_name=$1
    local content=$2
    local expected_decision=$3

    input_json=$(cat <<EOF
{
  "tool_name": "$tool_name",
  "tool_input": {
    "content": "$content"
  }
}
EOF
)

    output=$(echo "$input_json" | python3 false_claim_hook.py)
    decision=$(echo "$output" | jq -r '.hookSpecificOutput.permissionDecision')

    if [ "$decision" == "$expected_decision" ]; then
        echo "✓ Test passed: $tool_name"
    else
        echo "✗ Test failed: Expected $expected_decision, got $decision"
    fi
}

# Run tests
test_hook "Write" "Python is a programming language" "allow"
test_hook "Write" "Everyone always uses this tool" "deny"
test_hook "Edit" "95% of users love this feature" "ask"
```

---

## References

### Official Documentation
- [Get started with Claude Code hooks](https://code.claude.com/docs/en/hooks-guide)
- [Hooks reference - Claude Docs](https://docs.claude.com/en/docs/claude-code/hooks)
- [Google Fact Check Tools API](https://developers.google.com/fact-check/tools/api)

### Research Papers
- [Detecting hallucinations in large language models using semantic entropy | Nature](https://www.nature.com/articles/s41586-024-07421-0)
- [LLM-Check: Investigating Detection of Hallucinations in Large Language Models (NeurIPS 2024)](https://github.com/GaurangSriramanan/LLM_Check_Hallucination_Detection)
- [A Survey on Automated Fact-Checking | MIT Press](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00454/109469/A-Survey-on-Automated-Fact-Checking)

### Implementation Examples
- [GitHub - disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery)
- [GitHub - johnlindquist/claude-hooks](https://github.com/johnlindquist/claude-hooks)
- [GitHub - carlrannaberg/claudekit](https://github.com/carlrannaberg/claudekit)

### Tools and APIs
- [ClaimBuster: Automated Live Fact-Checking](https://idir.uta.edu/claimbuster/)
- [Full Fact AI - AI-Powered Fact Checking Tools](https://fullfact.ai/)
- [10 Best AI Fact-Checking Tools to Trust in 2025](https://sider.ai/blog/ai-tools/best-ai-fact-checking-tools-to-trust-in-2025)

### Best Practices and Guides
- [LLM Hallucination Detection and Mitigation: Best Techniques](https://www.deepchecks.com/llm-hallucination-detection-and-mitigation-best-techniques/)
- [Detecting hallucinations with LLM-as-a-judge | Datadog](https://www.datadoghq.com/blog/ai/llm-hallucination-detection/)
- [LLM Hallucinations in 2025 | Lakera](https://www.lakera.ai/blog/guide-to-hallucinations-in-large-language-models)
- [Automate Your AI Workflows with Claude Code Hooks | Butler's Log](https://blog.gitbutler.com/automate-your-ai-workflows-with-claude-code-hooks)

---

## Appendix A: Quick Start Guide

### Minimal Implementation (5 minutes)

1. **Create hook file:** `~/.claude-code/hooks/false_claim_check.py`

```python
#!/usr/bin/env python3
import json
import sys
import re

DENY_PATTERNS = [
    r'\b(always|never|all|none)\s+\w+',
    r'\d+%\s+of\s+(?:people|users)'
]

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
content = input_data.get("tool_input", {}).get("content", "")

if tool_name in ["Write", "Edit"] and content:
    for pattern in DENY_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": "Potential false claim detected"
                }
            }
            print(json.dumps(output))
            sys.exit(0)

sys.exit(0)
```

2. **Make executable:**
```bash
chmod +x ~/.claude-code/hooks/false_claim_check.py
```

3. **Configure in Claude Code settings:**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{
          "type": "command",
          "command": "~/.claude-code/hooks/false_claim_check.py"
        }]
      }
    ]
  }
}
```

4. **Test:**
```bash
echo '{"tool_name":"Write","tool_input":{"content":"Everyone always uses this"}}' | \
  python3 ~/.claude-code/hooks/false_claim_check.py
```

---

## Appendix B: Advanced Configuration Examples

### Multi-Tier Validation

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude-code/hooks/tier1_pattern_check.py",
            "description": "Fast pattern matching"
          },
          {
            "type": "command",
            "command": "~/.claude-code/hooks/tier2_api_verify.py",
            "description": "API-based verification",
            "condition": "tier1_uncertain"
          }
        ]
      }
    ]
  }
}
```

### Selective Tool Validation

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [{
          "type": "command",
          "command": "~/.claude-code/hooks/strict_validation.py"
        }]
      },
      {
        "matcher": "Edit",
        "hooks": [{
          "type": "command",
          "command": "~/.claude-code/hooks/lenient_validation.py"
        }]
      }
    ]
  }
}
```

---

**End of Report**

Generated: 2025-12-06
Research Depth: Deep
Total Sources: 20+
Confidence: High