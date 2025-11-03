# Business Model Opportunity Scoring System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform RedditHarbor into a business intelligence platform that systematically identifies and ranks data-backed app business opportunities across different sectors.

**Architecture:** Enhanced analysis pipeline with 5 scoring components (Pain Point Severity, Market Size, Solution Gap, Monetization Potential, Technical Feasibility) feeding into a unified opportunity ranking algorithm displayed through a Streamlit dashboard.

**Tech Stack:** Python (spaCy/NLTK for NLP), Supabase (PostgreSQL), Streamlit (dashboard), RedditHarbor (existing data collection), pandas (data analysis), Plotly (visualizations)

---

## Project Overview

This implementation adds business intelligence capabilities to RedditHarbor's existing social media research platform. The system analyzes Reddit discussions across different sectors to identify and rank the most promising data-backed app business opportunities.

**Key Components:**
1. **Enhanced NLP Analysis Engine** - Advanced sentiment and pain point detection
2. **Market Sizing Algorithms** - Estimate market potential from Reddit activity
3. **Solution Gap Detection** - Identify unsolved problems in discussions
4. **Monetization Indicators** - Detect willingness to pay and revenue potential
5. **Technical Feasibility Assessment** - Evaluate implementation complexity
6. **Scoring Dashboard** - Streamlit interface for opportunity analysis
7. **Automated Reporting** - Generate business insights reports

---

## Task 1: Enhanced NLP Analysis Engine

**Files:**
- Create: `src/redditharbor/analysis/pain_point_analyzer.py`
- Create: `src/redditharbor/analysis/sentiment_analyzer.py`
- Modify: `src/redditharbor/utils/analyze_research_data.py`
- Test: `tests/test_pain_point_analyzer.py`

**Step 1: Write the failing test**

```python
# tests/test_pain_point_analyzer.py
import pytest
from redditharbor.analysis.pain_point_analyzer import PainPointAnalyzer

def test_frustration_detection():
    analyzer = PainPointAnalyzer()

    # Test with frustration keywords
    text = "I'm so frustrated with this scheduling app, it never works properly"
    result = analyzer.analyze_pain_severity(text)
    assert result['frustration_score'] > 0
    assert 'frustrated' in result['detected_keywords']

    # Test with neutral text
    neutral_text = "This app works fine for basic scheduling"
    neutral_result = analyzer.analyze_pain_severity(neutral_text)
    assert neutral_result['frustration_score'] == 0

def test_urgency_detection():
    analyzer = PainPointAnalyzer()

    # Test with urgency indicators
    text = "I desperately need help finding a better project management solution"
    result = analyzer.analyze_pain_severity(text)
    assert result['urgency_score'] > 0
    assert 'desperately' in result['detected_keywords']

def test_pain_severity_scoring():
    analyzer = PainPointAnalyzer()

    # High severity case
    high_pain = "I absolutely hate this software, it's completely broken and I need it fixed immediately"
    high_result = analyzer.analyze_pain_severity(high_pain)
    assert high_result['severity_score'] >= 15  # High threshold

    # Low severity case
    low_pain = "This tool could be a bit better"
    low_result = analyzer.analyze_pain_severity(low_pain)
    assert low_result['severity_score'] < 5
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_pain_point_analyzer.py -v`
Expected: FAIL with "module 'redditharbor.analysis.pain_point_analyzer' not found"

**Step 3: Write minimal implementation**

```python
# src/redditharbor/analysis/pain_point_analyzer.py
from typing import Dict, List
import re

class PainPointAnalyzer:
    def __init__(self):
        self.frustration_keywords = [
            'frustrated', 'frustrating', 'hate', 'despise', 'can\'t stand',
            'annoying', 'terrible', 'awful', 'horrible', 'useless'
        ]
        self.urgency_keywords = [
            'desperately', 'urgently', 'immediately', 'asap', 'emergency',
            'need help', 'need it now', 'critical', 'urgent'
        ]
        self.problem_keywords = [
            'problem', 'issue', 'struggle', 'difficult', 'challenging',
            'broken', 'doesn\'t work', 'failed', 'error', 'bug'
        ]

    def analyze_pain_severity(self, text: str) -> Dict:
        text_lower = text.lower()

        # Count keyword occurrences
        frustration_count = sum(text_lower.count(keyword) for keyword in self.frustration_keywords)
        urgency_count = sum(text_lower.count(keyword) for keyword in self.urgency_keywords)
        problem_count = sum(text_lower.count(keyword) for keyword in self.problem_keywords)

        # Calculate scores
        frustration_score = frustration_count * 3  # Weight frustration higher
        urgency_score = urgency_count * 5  # Urgency gets highest weight
        problem_score = problem_count * 2

        severity_score = frustration_score + urgency_score + problem_score

        # Find detected keywords
        detected_keywords = []
        for keyword in self.frustration_keywords + self.urgency_keywords + self.problem_keywords:
            if keyword in text_lower:
                detected_keywords.append(keyword)

        return {
            'severity_score': severity_score,
            'frustration_score': frustration_score,
            'urgency_score': urgency_score,
            'problem_score': problem_score,
            'detected_keywords': detected_keywords,
            'text_length': len(text)
        }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_pain_point_analyzer.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_pain_point_analyzer.py src/redditharbor/analysis/pain_point_analyzer.py
git commit -m "feat: add pain point severity analysis engine"
```

---

## Task 2: Market Sizing Algorithms

**Files:**
- Create: `src/redditharbor/analysis/market_sizer.py`
- Create: `src/redditharbor/utils/subreddit_analytics.py`
- Test: `tests/test_market_sizer.py`

**Step 1: Write the failing test**

```python
# tests/test_market_sizer.py
import pytest
from redditharbor.analysis.market_sizer import MarketSizer

def test_basic_market_size_calculation():
    sizer = MarketSizer()

    # Mock subreddit data
    subreddit_data = {
        'subreddit': 'productivity',
        'subscriber_count': 100000,
        'active_users': 5000,
        'engagement_rate': 0.05
    }

    result = sizer.estimate_market_size(subreddit_data)

    assert result['total_addressable_market'] > 0
    assert result['market_score'] > 0
    assert 'confidence_level' in result

def test_cross_subreddit_analysis():
    sizer = MarketSizer()

    # Related subreddits
    related_subreddits = [
        {'name': 'productivity', 'subscribers': 100000},
        {'name': 'gtd', 'subscribers': 50000},
        {'name': 'organization', 'subscribers': 75000}
    ]

    result = sizer.analyze_cross_subreddit_market(related_subreddits)

    assert result['total_market_size'] > 225000  # Sum of all subscribers
    assert result['market_concentration'] > 0
    assert len(result['market_segments']) == 3
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_market_sizer.py -v`
Expected: FAIL with "module 'redditharbor.analysis.market_sizer' not found"

**Step 3: Write minimal implementation**

```python
# src/redditharbor/analysis/market_sizer.py
from typing import Dict, List, Tuple
import math

class MarketSizer:
    def __init__(self):
        self.engagement_multipliers = {
            'low': 0.1,      # 10% of subscribers are active
            'medium': 0.25,  # 25% of subscribers are active
            'high': 0.5      # 50% of subscribers are active
        }

    def estimate_market_size(self, subreddit_data: Dict) -> Dict:
        """
        Estimate market size based on subreddit metrics
        """
        subscriber_count = subreddit_data.get('subscriber_count', 0)
        active_users = subreddit_data.get('active_users', 0)
        engagement_rate = subreddit_data.get('engagement_rate', 0.01)

        # Calculate engagement level
        if engagement_rate > 0.1:
            engagement_level = 'high'
        elif engagement_rate > 0.05:
            engagement_level = 'medium'
        else:
            engagement_level = 'low'

        multiplier = self.engagement_multipliers[engagement_level]

        # Market size calculation
        # Conservative estimate: 10% of engaged users would pay for a solution
        potential_users = max(subscriber_count, active_users) * multiplier
        paying_users = potential_users * 0.1

        # Market scoring (0-15 points for business model scoring)
        if paying_users > 100000:
            market_score = 15  # Massive market
        elif paying_users > 50000:
            market_score = 12  # Large market
        elif paying_users > 10000:
            market_score = 8   # Medium market
        elif paying_users > 1000:
            market_score = 4   # Small market
        else:
            market_score = 1   # Niche market

        # Confidence level based on data quality
        confidence_level = self._calculate_confidence(subreddit_data)

        return {
            'total_addressable_market': int(paying_users),
            'market_score': market_score,
            'engagement_level': engagement_level,
            'confidence_level': confidence_level,
            'raw_subscribers': subscriber_count,
            'estimated_engaged_users': int(potential_users)
        }

    def analyze_cross_subreddit_market(self, related_subreddits: List[Dict]) -> Dict:
        """
        Analyze market size across multiple related subreddits
        """
        total_subscribers = sum(sub['subscribers'] for sub in related_subreddits)

        # Calculate market concentration (how dominant is the largest subreddit)
        if total_subscribers > 0:
            largest_subreddit = max(sub['subscribers'] for sub in related_subreddits)
            concentration = largest_subreddit / total_subscribers
        else:
            concentration = 0

        # Market segments with their sizes
        market_segments = [
            {
                'name': sub['name'],
                'size': sub['subscribers'],
                'percentage': (sub['subscribers'] / total_subscribers * 100) if total_subscribers > 0 else 0
            }
            for sub in related_subreddits
        ]

        return {
            'total_market_size': total_subscribers,
            'market_concentration': concentration,
            'market_segments': market_segments,
            'segment_count': len(related_subreddits)
        }

    def _calculate_confidence(self, data: Dict) -> float:
        """
        Calculate confidence level in market size estimate
        """
        confidence = 0.5  # Base confidence

        if data.get('subscriber_count', 0) > 0:
            confidence += 0.2
        if data.get('active_users', 0) > 0:
            confidence += 0.2
        if data.get('engagement_rate', 0) > 0:
            confidence += 0.1

        return min(confidence, 1.0)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_market_sizer.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_market_sizer.py src/redditharbor/analysis/market_sizer.py
git commit -m "feat: add market sizing analysis algorithms"
```

---

## Task 3: Solution Gap Detection

**Files:**
- Create: `src/redditharbor/analysis/solution_gap_detector.py`
- Test: `tests/test_solution_gap_detector.py`

**Step 1: Write the failing test**

```python
# tests/test_solution_gap_detector.py
import pytest
from redditharbor.analysis.solution_gap_detector import SolutionGapDetector

def test_solution_gap_detection():
    detector = SolutionGapDetector()

    # Problem without solution
    problem_text = "I'm struggling to find a good way to track my habits consistently"
    result = detector.detect_solution_gap(problem_text)

    assert result['has_problem'] == True
    assert result['has_solution'] == False
    assert result['solution_gap'] == True

def test_existing_solution_detection():
    detector = SolutionGapDetector()

    # Problem with existing solution mentioned
    solution_text = "I use Todoist for task management and it works great"
    result = detector.detect_solution_gap(solution_text)

    assert result['has_solution'] == True
    assert result['solution_gap'] == False
    assert len(result['detected_solutions']) > 0

def test_competitor_detection():
    detector = SolutionGapDetector()

    # Text mentioning competitors
    competitor_text = "I've tried Trello and Asana but they're too complex for my needs"
    result = detector.detect_competitors(competitor_text)

    assert len(result['competitors']) == 2
    assert 'Trello' in result['competitors']
    assert 'Asana' in result['competitors']
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_solution_gap_detector.py -v`
Expected: FAIL with "module 'redditharbor.analysis.solution_gap_detector' not found"

**Step 3: Write minimal implementation**

```python
# src/redditharbor/analysis/solution_gap_detector.py
from typing import Dict, List
import re

class SolutionGapDetector:
    def __init__(self):
        self.problem_indicators = [
            'problem', 'issue', 'struggle', 'difficult', 'challenging',
            'trouble', 'can\'t', 'unable to', 'need help', 'looking for'
        ]

        self.solution_indicators = [
            'use', 'using', 'currently using', 'i use', 'tried', 'found',
            'recommend', 'suggest', 'solution', 'tool', 'app', 'software'
        ]

        # Known competitor names in various categories
        self.known_competitors = [
            'Todoist', 'Trello', 'Asana', 'Notion', 'Evernote', 'OneNote',
            'Slack', 'Discord', 'Zoom', 'Teams', 'Google Workspace',
            'Microsoft 365', 'Adobe Creative Suite', 'Figma', 'Sketch',
            'GitHub', 'GitLab', 'Bitbucket', 'Jira', 'Confluence'
        ]

    def detect_solution_gap(self, text: str) -> Dict:
        """
        Detect if text describes a problem without a solution
        """
        text_lower = text.lower()

        # Check for problem indicators
        has_problem = any(indicator in text_lower for indicator in self.problem_indicators)

        # Check for solution indicators
        has_solution = any(indicator in text_lower for indicator in self.solution_indicators)

        # Check for known competitors
        competitors = self.detect_competitors(text)['competitors']
        if competitors:
            has_solution = True

        # Solution gap exists if there's a problem but no solution mentioned
        solution_gap = has_problem and not has_solution

        return {
            'has_problem': has_problem,
            'has_solution': has_solution,
            'solution_gap': solution_gap,
            'detected_solutions': self._extract_solution_keywords(text_lower),
            'competitors_mentioned': competitors
        }

    def detect_competitors(self, text: str) -> Dict:
        """
        Detect known competitor names in text
        """
        detected_competitors = []

        for competitor in self.known_competitors:
            if competitor.lower() in text.lower():
                detected_competitors.append(competitor)

        return {
            'competitors': detected_competitors,
            'competitor_count': len(detected_competitors)
        }

    def _extract_solution_keywords(self, text: str) -> List[str]:
        """
        Extract solution-related keywords from text
        """
        solution_keywords = []

        for indicator in self.solution_indicators:
            if indicator in text:
                solution_keywords.append(indicator)

        return solution_keywords

    def analyze_gap_severity(self, text: str) -> Dict:
        """
        Analyze the severity of a solution gap
        """
        gap_result = self.detect_solution_gap(text)

        if not gap_result['solution_gap']:
            return {
                'gap_severity': 0,
                'gap_score': 0,
                'reason': 'No solution gap detected'
            }

        # Calculate severity based on problem indicators and engagement
        problem_count = sum(text.lower().count(indicator) for indicator in self.problem_indicators)

        # Severity scoring (0-25 points for business model scoring)
        if problem_count >= 3:
            gap_score = 25  # Multiple strong problem indicators
            severity = 'high'
        elif problem_count >= 2:
            gap_score = 18  # Clear problem indicators
            severity = 'medium'
        elif problem_count >= 1:
            gap_score = 12  # Single problem indicator
            severity = 'low'
        else:
            gap_score = 5   # Weak problem indicators
            severity = 'minimal'

        return {
            'gap_severity': severity,
            'gap_score': gap_score,
            'problem_indicator_count': problem_count,
            'reason': f'Severity: {severity} based on {problem_count} problem indicators'
        }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_solution_gap_detector.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_solution_gap_detector.py src/redditharbor/analysis/solution_gap_detector.py
git commit -m "feat: add solution gap detection system"
```

---

## Task 4: Monetization Potential Analysis

**Files:**
- Create: `src/redditharbor/analysis/monetization_analyzer.py`
- Test: `tests/test_monetization_analyzer.py`

**Step 1: Write the failing test**

```python
# tests/test_monetization_analyzer.py
import pytest
from redditharbor.analysis.monetization_analyzer import MonetizationAnalyzer

def test_willingness_to_pay_detection():
    analyzer = MonetizationAnalyzer()

    # Text showing willingness to pay
    pay_text = "I would definitely pay $10 per month for a good project management tool"
    result = analyzer.analyze_monetization_potential(pay_text)

    assert result['willingness_to_pay'] == True
    assert result['price_mentioned'] == 10
    assert result['payment_type'] == 'monthly'
    assert result['monetization_score'] > 10

def test_b2b_vs_b2c_classification():
    analyzer = MonetizationAnalyzer()

    # B2B indicators
    b2b_text = "Our team needs better collaboration software for our business"
    b2b_result = analyzer.classify_business_model(b2b_text)

    assert b2b_result['model_type'] == 'B2B'
    assert b2b_result['b2b_score'] > b2b_result['b2c_score']

    # B2C indicators
    b2c_text = "I need a personal app to track my fitness goals"
    b2c_result = analyzer.classify_business_model(b2c_text)

    assert b2c_result['model_type'] == 'B2C'
    assert b2c_result['b2c_score'] > b2c_result['b2b_score']

def test_monetization_scoring():
    analyzer = MonetizationAnalyzer()

    # High monetization potential
    high_potential = "I would pay $50/month for an enterprise-grade solution for our team"
    high_result = analyzer.calculate_monetization_score(high_potential)

    assert high_result['total_score'] >= 12  # High monetization score

    # Low monetization potential
    low_potential = "I wish there was a free app for personal notes"
    low_result = analyzer.calculate_monetization_score(low_potential)

    assert low_result['total_score'] <= 5  # Low monetization score
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_monetization_analyzer.py -v`
Expected: FAIL with "module 'redditharbor.analysis.monetization_analyzer' not found"

**Step 3: Write minimal implementation**

```python
# src/redditharbor/analysis/monetization_analyzer.py
from typing import Dict, List
import re

class MonetizationAnalyzer:
    def __init__(self):
        self.pricing_keywords = [
            'pay', 'price', 'cost', 'budget', 'afford', 'expensive',
            'cheap', 'subscription', 'monthly', 'yearly', 'fee'
        ]

        self.willingness_keywords = [
            'would pay', 'willing to pay', 'happy to pay', 'gladly pay',
            'definitely pay', 'would buy', 'would purchase'
        ]

        self.b2b_keywords = [
            'team', 'business', 'company', 'organization', 'enterprise',
            'corporate', 'professional', 'work', 'office', 'colleagues'
        ]

        self.b2c_keywords = [
            'personal', 'individual', 'home', 'family', 'private',
            'my own', 'for me', 'personal use', 'individual use'
        ]

    def analyze_monetization_potential(self, text: str) -> Dict:
        """
        Analyze monetization potential from text
        """
        text_lower = text.lower()

        # Check willingness to pay
        willingness_to_pay = any(keyword in text_lower for keyword in self.willingness_keywords)

        # Extract price information
        price_info = self._extract_price_info(text)

        # Check pricing discussions
        pricing_discussion = any(keyword in text_lower for keyword in self.pricing_keywords)

        return {
            'willingness_to_pay': willingness_to_pay,
            'pricing_discussion': pricing_discussion,
            'price_mentioned': price_info['amount'],
            'payment_type': price_info['payment_type'],
            'monetization_score': self._calculate_base_monetization_score(willingness_to_pay, price_info['amount'])
        }

    def classify_business_model(self, text: str) -> Dict:
        """
        Classify as B2B or B2C based on language patterns
        """
        text_lower = text.lower()

        # Count B2B indicators
        b2b_score = sum(text_lower.count(keyword) for keyword in self.b2b_keywords)

        # Count B2C indicators
        b2c_score = sum(text_lower.count(keyword) for keyword in self.b2c_keywords)

        # Determine model type
        if b2b_score > b2c_score:
            model_type = 'B2B'
        elif b2c_score > b2b_score:
            model_type = 'B2C'
        else:
            model_type = 'Unclear'

        return {
            'model_type': model_type,
            'b2b_score': b2b_score,
            'b2c_score': b2c_score,
            'b2b_indicators': self._extract_indicators(text_lower, self.b2b_keywords),
            'b2c_indicators': self._extract_indicators(text_lower, self.b2c_keywords)
        }

    def calculate_monetization_score(self, text: str) -> Dict:
        """
        Calculate comprehensive monetization score (0-15 points for business model scoring)
        """
        # Analyze willingness to pay
        willingness_result = self.analyze_monetization_potential(text)

        # Classify business model
        business_model = self.classify_business_model(text)

        # Base scores
        willingness_score = willingness_result['monetization_score']

        # Price-based scoring
        price_score = 0
        if willingness_result['price_mentioned'] > 50:
            price_score = 5  # High pricing indicates B2B/enterprise
        elif willingness_result['price_mentioned'] > 10:
            price_score = 3  # Mid-range pricing
        elif willingness_result['price_mentioned'] > 0:
            price_score = 2  # Some willingness to pay
        else:
            price_score = 0  # No clear monetization

        # Business model bonus
        model_bonus = 2 if business_model['model_type'] == 'B2B' else 1

        # Total monetization score (0-15)
        total_score = min(willingness_score + price_score + model_bonus, 15)

        return {
            'total_score': total_score,
            'willingness_score': willingness_score,
            'price_score': price_score,
            'model_bonus': model_bonus,
            'business_model': business_model['model_type'],
            'reasoning': f'Score: {willingness_score} (willingness) + {price_score} (price) + {model_bonus} (model)'
        }

    def _extract_price_info(self, text: str) -> Dict:
        """
        Extract price information from text
        """
        # Price pattern matching
        price_patterns = [
            r'\$(\d+(?:\.\d{2})?)\s*(?:per\s*)?(month|monthly|year|yearly|mo|yr)',
            r'(\d+(?:\.\d{2})?)\s*(?:dollars?)\s*(?:per\s*)?(month|monthly|year|yearly)',
            r'(\d+(?:\.\d{2})?)\s*(?:per\s*)?(month|monthly|year|yearly)'
        ]

        for pattern in price_patterns:
            match = re.search(pattern, text.lower())
            if match:
                amount = float(match.group(1))
                period = match.group(2) if len(match.groups()) > 1 else 'unknown'

                payment_type = 'monthly' if 'month' in period else 'yearly' if 'year' in period else 'unknown'

                return {
                    'amount': amount,
                    'payment_type': payment_type,
                    'raw_match': match.group(0)
                }

        return {
            'amount': 0,
            'payment_type': 'unknown',
            'raw_match': None
        }

    def _calculate_base_monetization_score(self, willingness: bool, price_amount: float) -> int:
        """
        Calculate base monetization score
        """
        if not willingness and price_amount == 0:
            return 0  # No monetization signals
        elif willingness and price_amount >= 20:
            return 10  # Strong willingness with high price
        elif willingness and price_amount > 0:
            return 7   # Willingness with some price
        elif willingness:
            return 5   # Willingness but no clear price
        elif price_amount > 0:
            return 3   # Price discussion but no clear willingness
        else:
            return 1   # Weak monetization signals

    def _extract_indicators(self, text: str, keywords: List[str]) -> List[str]:
        """
        Extract matching indicators from text
        """
        indicators = []
        for keyword in keywords:
            if keyword in text:
                indicators.append(keyword)
        return indicators
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_monetization_analyzer.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_monetization_analyzer.py src/redditharbor/analysis/monetization_analyzer.py
git commit -m "feat: add monetization potential analysis"
```

---

## Task 5: Technical Feasibility Assessment

**Files:**
- Create: `src/redditharbor/analysis/technical_feasibility_analyzer.py`
- Test: `tests/test_technical_feasibility_analyzer.py`

**Step 1: Write the failing test**

```python
# tests/test_technical_feasibility_analyzer.py
import pytest
from redditharbor.analysis.technical_feasibility_analyzer import TechnicalFeasibilityAnalyzer

def test_technical_discussion_detection():
    analyzer = TechnicalFeasibilityAnalyzer()

    # Technical discussion text
    tech_text = "We need an API that integrates with Slack and has real-time synchronization"
    result = analyzer.analyze_technical_feasibility(tech_text)

    assert result['technical_discussion'] == True
    assert len(result['technical_keywords']) > 0
    assert 'api' in result['technical_keywords']

def test_complexity_assessment():
    analyzer = TechnicalFeasibilityAnalyzer()

    # High complexity text
    complex_text = "This requires complex machine learning algorithms and real-time data processing"
    result = analyzer.assess_implementation_complexity(complex_text)

    assert result['complexity_level'] == 'high'
    assert result['complexity_score'] <= 5  # High complexity = lower feasibility score

    # Low complexity text
    simple_text = "A simple web app with basic forms would work well"
    simple_result = analyzer.assess_implementation_complexity(simple_text)

    assert simple_result['complexity_level'] == 'low'
    assert simple_result['complexity_score'] >= 8  # Low complexity = higher feasibility score

def test_feasibility_scoring():
    analyzer = TechnicalFeasibilityAnalyzer()

    # High feasibility case
    feasible_text = "A simple web application with basic CRUD operations using standard frameworks"
    feasible_result = analyzer.calculate_feasibility_score(feasible_text)

    assert feasible_result['feasibility_score'] >= 8  # High feasibility

    # Low feasibility case
    infeasible_text = "We need advanced AI with quantum computing and blockchain integration"
    infeasible_result = analyzer.calculate_feasibility_score(infeasible_text)

    assert infeasible_result['feasibility_score'] <= 3  # Low feasibility
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_technical_feasibility_analyzer.py -v`
Expected: FAIL with "module 'redditharbor.analysis.technical_feasibility_analyzer' not found"

**Step 3: Write minimal implementation**

```python
# src/redditharbor/analysis/technical_feasibility_analyzer.py
from typing import Dict, List

class TechnicalFeasibilityAnalyzer:
    def __init__(self):
        self.technical_keywords = [
            'api', 'integration', 'development', 'build', 'implement', 'code',
            'programming', 'software', 'platform', 'system', 'architecture',
            'database', 'frontend', 'backend', 'server', 'cloud', 'mobile'
        ]

        self.high_complexity_keywords = [
            'machine learning', 'artificial intelligence', 'ai', 'quantum',
            'blockchain', 'cryptocurrency', 'advanced algorithms', 'neural network',
            'deep learning', 'computer vision', 'natural language processing'
        ]

        self.medium_complexity_keywords = [
            'real-time', 'synchronization', 'complex', 'advanced', 'scalable',
            'distributed', 'microservices', 'integration', 'automation'
        ]

        self.low_complexity_keywords = [
            'simple', 'basic', 'straightforward', 'easy', 'standard',
            'common', 'typical', 'regular', 'normal', 'conventional'
        ]

        self.proven_technologies = [
            'react', 'vue', 'angular', 'node', 'python', 'javascript',
            'postgresql', 'mysql', 'mongodb', 'aws', 'azure', 'google cloud',
            'docker', 'kubernetes', 'rest api', 'graphql', 'webhook'
        ]

    def analyze_technical_feasibility(self, text: str) -> Dict:
        """
        Analyze technical discussion and feasibility indicators
        """
        text_lower = text.lower()

        # Detect technical discussion
        technical_discussion = any(keyword in text_lower for keyword in self.technical_keywords)

        # Extract technical keywords found
        technical_keywords_found = []
        for keyword in self.technical_keywords:
            if keyword in text_lower:
                technical_keywords_found.append(keyword)

        # Check for proven technologies
        proven_tech_found = []
        for tech in self.proven_technologies:
            if tech in text_lower:
                proven_tech_found.append(tech)

        return {
            'technical_discussion': technical_discussion,
            'technical_keywords': technical_keywords_found,
            'proven_technologies': proven_tech_found,
            'technical_density': len(technical_keywords_found)
        }

    def assess_implementation_complexity(self, text: str) -> Dict:
        """
        Assess the complexity of implementation based on language
        """
        text_lower = text.lower()

        # Count complexity indicators
        high_complexity_count = sum(1 for keyword in self.high_complexity_keywords if keyword in text_lower)
        medium_complexity_count = sum(1 for keyword in self.medium_complexity_keywords if keyword in text_lower)
        low_complexity_count = sum(1 for keyword in self.low_complexity_keywords if keyword in text_lower)

        # Determine complexity level
        if high_complexity_count >= 1:
            complexity_level = 'high'
            complexity_score = 2  # Low feasibility score
        elif medium_complexity_count >= 2:
            complexity_level = 'medium'
            complexity_score = 6  # Medium feasibility score
        elif low_complexity_count >= 1 or high_complexity_count == 0:
            complexity_level = 'low'
            complexity_score = 9  # High feasibility score
        else:
            complexity_level = 'medium'  # Default
            complexity_score = 6

        return {
            'complexity_level': complexity_level,
            'complexity_score': complexity_score,
            'high_complexity_indicators': high_complexity_count,
            'medium_complexity_indicators': medium_complexity_count,
            'low_complexity_indicators': low_complexity_count
        }

    def calculate_feasibility_score(self, text: str) -> Dict:
        """
        Calculate overall technical feasibility score (0-10 points for business model scoring)
        """
        # Analyze technical discussion
        tech_analysis = self.analyze_technical_feasibility(text)

        # Assess complexity
        complexity_assessment = self.assess_implementation_complexity(text)

        # Base feasibility score from complexity
        base_score = complexity_assessment['complexity_score']

        # Bonus for proven technologies
        proven_tech_bonus = min(len(tech_analysis['proven_technologies']) * 0.5, 2)

        # Bonus for technical discussion (indicates deeper thinking)
        tech_discussion_bonus = 2 if tech_analysis['technical_discussion'] else 0

        # Calculate final score (0-10)
        final_score = min(base_score + proven_tech_bonus + tech_discussion_bonus, 10)

        # Determine feasibility category
        if final_score >= 8:
            feasibility_category = 'high'
        elif final_score >= 5:
            feasibility_category = 'medium'
        else:
            feasibility_category = 'low'

        return {
            'feasibility_score': final_score,
            'feasibility_category': feasibility_category,
            'complexity_score': complexity_assessment['complexity_score'],
            'proven_tech_bonus': proven_tech_bonus,
            'tech_discussion_bonus': tech_discussion_bonus,
            'technical_keywords_count': tech_analysis['technical_density'],
            'proven_technologies_count': len(tech_analysis['proven_technologies'])
        }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_technical_feasibility_analyzer.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_technical_feasibility_analyzer.py src/redditharbor/analysis/technical_feasibility_analyzer.py
git commit -m "feat: add technical feasibility assessment"
```

---

## Task 6: Business Opportunity Scoring Engine

**Files:**
- Create: `src/redditharbor/analysis/opportunity_scorer.py`
- Test: `tests/test_opportunity_scorer.py`

**Step 1: Write the failing test**

```python
# tests/test_opportunity_scorer.py
import pytest
from redditharbor.analysis.opportunity_scorer import OpportunityScorer

def test_comprehensive_opportunity_scoring():
    scorer = OpportunityScorer()

    # Sample post data
    post_data = {
        'title': "I desperately need a better project management tool for our team",
        'body': "I'm so frustrated with current solutions. I would pay $50/month for something that actually works well with Slack integration.",
        'score': 25,
        'num_comments': 15,
        'subreddit': 'productivity',
        'subscriber_count': 100000
    }

    result = scorer.calculate_opportunity_score(post_data)

    assert result['total_score'] > 0
    assert result['total_score'] <= 100
    assert 'problem_validation_score' in result
    assert 'solution_viability_score' in result
    assert 'business_viability_score' in result
    assert 'tier' in result  # A, B, C, or D tier

def test_scoring_tiers():
    scorer = OpportunityScorer()

    # High tier opportunity
    high_tier_post = {
        'title': "I hate current scheduling software and desperately need a better solution",
        'body': "I would pay $100/month for enterprise-grade scheduling software for our team of 50 people",
        'score': 100,
        'num_comments': 50,
        'subreddit': 'productivity',
        'subscriber_count': 500000
    }

    high_result = scorer.calculate_opportunity_score(high_tier_post)
    assert high_result['tier'] == 'A'
    assert high_result['total_score'] >= 75

    # Low tier opportunity
    low_tier_post = {
        'title': "It would be nice to have a better note-taking app",
        'body': "Something simple would be fine",
        'score': 5,
        'num_comments': 2,
        'subreddit': 'productivity',
        'subscriber_count': 1000
    }

    low_result = scorer.calculate_opportunity_score(low_tier_post)
    assert low_result['tier'] == 'D'
    assert low_result['total_score'] < 25
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_opportunity_scorer.py -v`
Expected: FAIL with "module 'redditharbor.analysis.opportunity_scorer' not found"

**Step 3: Write minimal implementation**

```python
# src/redditharbor/analysis/opportunity_scorer.py
from typing import Dict, List
from .pain_point_analyzer import PainPointAnalyzer
from .market_sizer import MarketSizer
from .solution_gap_detector import SolutionGapDetector
from .monetization_analyzer import MonetizationAnalyzer
from .technical_feasibility_analyzer import TechnicalFeasibilityAnalyzer

class OpportunityScorer:
    def __init__(self):
        self.pain_analyzer = PainPointAnalyzer()
        self.market_sizer = MarketSizer()
        self.solution_detector = SolutionGapDetector()
        self.monetization_analyzer = MonetizationAnalyzer()
        self.feasibility_analyzer = TechnicalFeasibilityAnalyzer()

    def calculate_opportunity_score(self, post_data: Dict) -> Dict:
        """
        Calculate comprehensive business opportunity score (0-100 points)
        """
        # Combine title and body for analysis
        full_text = f"{post_data.get('title', '')} {post_data.get('body', '')}"

        # 1. Problem Validation (40 points)
        problem_score = self._calculate_problem_validation(full_text, post_data)

        # 2. Solution Viability (35 points)
        solution_score = self._calculate_solution_viability(full_text, post_data)

        # 3. Business Viability (25 points)
        business_score = self._calculate_business_viability(full_text, post_data)

        # Total score
        total_score = problem_score['score'] + solution_score['score'] + business_score['score']

        # Determine tier
        tier = self._determine_tier(total_score)

        return {
            'total_score': total_score,
            'tier': tier,
            'problem_validation_score': problem_score,
            'solution_viability_score': solution_score,
            'business_viability_score': business_score,
            'breakdown': {
                'problem_validation_percent': round((problem_score['score'] / 40) * 100, 1),
                'solution_viability_percent': round((solution_score['score'] / 35) * 100, 1),
                'business_viability_percent': round((business_score['score'] / 25) * 100, 1)
            }
        }

    def _calculate_problem_validation(self, text: str, post_data: Dict) -> Dict:
        """
        Calculate problem validation score (0-40 points)
        """
        # Pain point severity (0-15 points)
        pain_analysis = self.pain_analyzer.analyze_pain_severity(text)
        pain_score = min(pain_analysis['severity_score'], 15)

        # Market size (0-15 points)
        subreddit_data = {
            'subreddit': post_data.get('subreddit', ''),
            'subscriber_count': post_data.get('subscriber_count', 0),
            'active_users': post_data.get('num_comments', 0),
            'engagement_rate': post_data.get('score', 0) / max(post_data.get('num_comments', 1), 1) / 100
        }
        market_analysis = self.market_sizer.estimate_market_size(subreddit_data)
        market_score = market_analysis['market_score']

        # Problem frequency (0-10 points)
        engagement_score = min(post_data.get('score', 0) / 10, 5) + min(post_data.get('num_comments', 0) / 5, 5)

        total_score = pain_score + market_score + engagement_score

        return {
            'score': total_score,
            'pain_point_score': pain_score,
            'market_size_score': market_score,
            'engagement_score': engagement_score,
            'details': pain_analysis
        }

    def _calculate_solution_viability(self, text: str, post_data: Dict) -> Dict:
        """
        Calculate solution viability score (0-35 points)
        """
        # Solution gap analysis (0-15 points)
        gap_analysis = self.solution_detector.analyze_gap_severity(text)
        gap_score = gap_analysis['gap_score']

        # Technical feasibility (0-10 points)
        feasibility_analysis = self.feasibility_analyzer.calculate_feasibility_score(text)
        feasibility_score = feasibility_analysis['feasibility_score']

        # Competitive landscape (0-10 points)
        competitor_analysis = self.solution_detector.detect_competitors(text)
        competitor_count = competitor_analysis['competitor_count']

        # Fewer competitors = higher score
        if competitor_count == 0:
            competitor_score = 10  # Blue ocean
        elif competitor_count <= 2:
            competitor_score = 7   # Light competition
        elif competitor_count <= 5:
            competitor_score = 4   # Moderate competition
        else:
            competitor_score = 1   # Red ocean

        total_score = gap_score + feasibility_score + competitor_score

        return {
            'score': total_score,
            'solution_gap_score': gap_score,
            'technical_feasibility_score': feasibility_score,
            'competitive_landscape_score': competitor_score,
            'competitor_count': competitor_count
        }

    def _calculate_business_viability(self, text: str, post_data: Dict) -> Dict:
        """
        Calculate business viability score (0-25 points)
        """
        # Monetization potential (0-15 points)
        monetization_analysis = self.monetization_analyzer.calculate_monetization_score(text)
        monetization_score = monetization_analysis['total_score']

        # Growth potential (0-10 points)
        subreddit_count = post_data.get('subscriber_count', 0)
        engagement_multiplier = (post_data.get('score', 0) + post_data.get('num_comments', 0) * 2) / 100

        if subreddit_count > 100000 and engagement_multiplier > 1:
            growth_score = 10  # High growth potential
        elif subreddit_count > 50000 or engagement_multiplier > 0.5:
            growth_score = 7   # Good growth potential
        elif subreddit_count > 10000 or engagement_multiplier > 0.2:
            growth_score = 4   # Moderate growth potential
        else:
            growth_score = 1   # Limited growth potential

        total_score = monetization_score + growth_score

        return {
            'score': total_score,
            'monetization_score': monetization_score,
            'growth_score': growth_score,
            'business_model': monetization_analysis['business_model']
        }

    def _determine_tier(self, total_score: int) -> str:
        """
        Determine opportunity tier based on total score
        """
        if total_score >= 75:
            return 'A'  # Pursue immediately
        elif total_score >= 50:
            return 'B'  # Strong contender
        elif total_score >= 25:
            return 'C'  # Monitor
        else:
            return 'D'  # Low priority

    def score_opportunities_batch(self, posts_data: List[Dict]) -> List[Dict]:
        """
        Score multiple opportunities and return sorted results
        """
        scored_opportunities = []

        for post in posts_data:
            score_result = self.calculate_opportunity_score(post)
            scored_opportunities.append({
                **post,
                'opportunity_score': score_result
            })

        # Sort by total score (descending)
        scored_opportunities.sort(key=lambda x: x['opportunity_score']['total_score'], reverse=True)

        return scored_opportunities
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_opportunity_scorer.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_opportunity_scorer.py src/redditharbor/analysis/opportunity_scorer.py
git commit -m "feat: add comprehensive business opportunity scoring engine"
```

---

## Task 7: Streamlit Dashboard Integration

**Files:**
- Create: `src/redditharbor/dashboard/opportunity_dashboard.py`
- Create: `src/redditharbor/dashboard/components.py`
- Modify: `src/redditharbor/utils/analyze_research_data.py`
- Test: `tests/test_dashboard_integration.py`

**Step 1: Write the failing test**

```python
# tests/test_dashboard_integration.py
import pytest
import pandas as pd
from redditharbor.dashboard.opportunity_dashboard import OpportunityDashboard

def test_dashboard_initialization():
    dashboard = OpportunityDashboard()

    assert dashboard.scorer is not None
    assert hasattr(dashboard, 'filter_opportunities')
    assert hasattr(dashboard, 'display_opportunity_details')

def test_opportunity_filtering():
    dashboard = OpportunityDashboard()

    # Sample opportunities
    opportunities = [
        {'opportunity_score': {'total_score': 85, 'tier': 'A'}, 'subreddit': 'productivity'},
        {'opportunity_score': {'total_score': 45, 'tier': 'C'}, 'subreddit': 'gtd'},
        {'opportunity_score': {'total_score': 20, 'tier': 'D'}, 'subreddit': 'organization'}
    ]

    # Filter by tier A
    filtered = dashboard.filter_opportunities(opportunities, tier='A')
    assert len(filtered) == 1
    assert filtered[0]['opportunity_score']['tier'] == 'A'

    # Filter by score > 30
    score_filtered = dashboard.filter_opportunities(opportunities, min_score=30)
    assert len(score_filtered) == 1
    assert score_filtered[0]['opportunity_score']['total_score'] == 85

def test_dashboard_data_processing():
    dashboard = OpportunityDashboard()

    # Sample raw data
    raw_data = [
        {
            'title': 'Test Post',
            'body': 'Test body',
            'score': 10,
            'num_comments': 5,
            'subreddit': 'test'
        }
    ]

    # Process data
    processed = dashboard.process_opportunity_data(raw_data)

    assert len(processed) == 1
    assert 'opportunity_score' in processed[0]
    assert processed[0]['opportunity_score']['total_score'] >= 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_dashboard_integration.py -v`
Expected: FAIL with "module 'redditharbor.dashboard.opportunity_dashboard' not found"

**Step 3: Write minimal implementation**

```python
# src/redditharbor/dashboard/opportunity_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Optional
from ..analysis.opportunity_scorer import OpportunityScorer
from ..utils.fetch import fetch_submissions, fetch_comments

class OpportunityDashboard:
    def __init__(self):
        self.scorer = OpportunityScorer()

    def filter_opportunities(
        self,
        opportunities: List[Dict],
        tier: Optional[str] = None,
        min_score: Optional[int] = None,
        sector: Optional[str] = None
    ) -> List[Dict]:
        """
        Filter opportunities based on criteria
        """
        filtered = opportunities.copy()

        if tier:
            filtered = [op for op in filtered if op['opportunity_score']['tier'] == tier]

        if min_score:
            filtered = [op for op in filtered if op['opportunity_score']['total_score'] >= min_score]

        if sector:
            filtered = [op for op in filtered if op.get('sector', '').lower() == sector.lower()]

        return filtered

    def process_opportunity_data(self, raw_data: List[Dict]) -> List[Dict]:
        """
        Process raw Reddit data into scored opportunities
        """
        scored_opportunities = self.scorer.score_opportunities_batch(raw_data)
        return scored_opportunities

    def display_opportunity_overview(self, opportunities: List[Dict]):
        """
        Display overview metrics and charts
        """
        if not opportunities:
            st.warning("No opportunities found matching the current filters.")
            return

        # Calculate metrics
        total_opportunities = len(opportunities)
        avg_score = sum(op['opportunity_score']['total_score'] for op in opportunities) / total_opportunities

        tier_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        for op in opportunities:
            tier = op['opportunity_score']['tier']
            tier_counts[tier] += 1

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Opportunities", total_opportunities)

        with col2:
            st.metric("Average Score", f"{avg_score:.1f}")

        with col3:
            st.metric("Tier A Opportunities", tier_counts['A'])

        with col4:
            st.metric("Tier B Opportunities", tier_counts['B'])

        # Tier distribution chart
        fig = go.Figure(data=[
            go.Bar(x=list(tier_counts.keys()), y=list(tier_counts.values()))
        ])
        fig.update_layout(
            title="Opportunity Distribution by Tier",
            xaxis_title="Tier",
            yaxis_title="Count"
        )
        st.plotly_chart(fig, use_container_width=True)

    def display_opportunities_table(self, opportunities: List[Dict]):
        """
        Display opportunities in a sortable table
        """
        if not opportunities:
            return

        # Prepare data for table
        table_data = []
        for op in opportunities:
            table_data.append({
                'Title': op.get('title', 'N/A')[:50] + '...' if len(op.get('title', '')) > 50 else op.get('title', 'N/A'),
                'Score': op['opportunity_score']['total_score'],
                'Tier': op['opportunity_score']['tier'],
                'Subreddit': op.get('subreddit', 'N/A'),
                'Engagement': op.get('score', 0) + op.get('num_comments', 0)
            })

        df = pd.DataFrame(table_data)

        # Sort by score (descending)
        df = df.sort_values('Score', ascending=False)

        # Display table
        st.dataframe(df, use_container_width=True)

    def display_opportunity_details(self, opportunity: Dict):
        """
        Display detailed analysis of a single opportunity
        """
        score_data = opportunity['opportunity_score']

        st.subheader(f"📊 {opportunity.get('title', 'Untitled Opportunity')}")

        # Score breakdown
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Score", score_data['total_score'])
            st.metric("Tier", score_data['tier'])

        with col2:
            problem_score = score_data['problem_validation_score']['score']
            st.metric("Problem Validation", f"{problem_score}/40")

        with col3:
            business_score = score_data['business_viability_score']['score']
            st.metric("Business Viability", f"{business_score}/25")

        # Detailed breakdown
        st.write("### Score Breakdown")

        breakdown_data = {
            'Component': [
                'Problem Validation',
                'Solution Viability',
                'Business Viability'
            ],
            'Score': [
                score_data['problem_validation_score']['score'],
                score_data['solution_viability_score']['score'],
                score_data['business_viability_score']['score']
            ],
            'Max Possible': [40, 35, 25],
            'Percentage': [
                score_data['breakdown']['problem_validation_percent'],
                score_data['breakdown']['solution_viability_percent'],
                score_data['breakdown']['business_viability_percent']
            ]
        }

        df_breakdown = pd.DataFrame(breakdown_data)
        st.dataframe(df_breakdown, use_container_width=True)

        # Original content
        with st.expander("View Original Reddit Post"):
            st.write(f"**Subreddit:** r/{opportunity.get('subreddit', 'N/A')}")
            st.write(f"**Score:** {opportunity.get('score', 0)} | **Comments:** {opportunity.get('num_comments', 0)}")
            st.write(opportunity.get('body', opportunity.get('title', 'No content available')))

    def render_sidebar_filters(self, opportunities: List[Dict]) -> Dict:
        """
        Render sidebar filters and return filter criteria
        """
        st.sidebar.title("🔍 Opportunity Filters")

        # Get unique values for filters
        tiers = ['All', 'A', 'B', 'C', 'D']
        subreddits = ['All'] + list(set(op.get('subreddit', 'N/A') for op in opportunities))

        # Score range slider
        min_score_available = min(op['opportunity_score']['total_score'] for op in opportunities) if opportunities else 0
        max_score_available = max(op['opportunity_score']['total_score'] for op in opportunities) if opportunities else 100

        score_range = st.sidebar.slider(
            "Score Range",
            min_value=min_score_available,
            max_value=max_score_available,
            value=(min_score_available, max_score_available)
        )

        # Tier filter
        selected_tier = st.sidebar.selectbox("Tier", tiers)

        # Subreddit filter
        selected_subreddit = st.sidebar.selectbox("Subreddit", subreddits)

        # Number of results
        result_limit = st.sidebar.selectbox("Max Results", [10, 25, 50, 100, 'All'])

        return {
            'score_range': score_range,
            'tier': selected_tier if selected_tier != 'All' else None,
            'subreddit': selected_subreddit if selected_subreddit != 'All' else None,
            'limit': result_limit if result_limit != 'All' else None
        }

    def run_dashboard(self):
        """
        Main dashboard rendering function
        """
        st.title("🚀 RedditHarbor Business Opportunity Analyzer")
        st.markdown("Identify and rank data-backed app business opportunities from Reddit discussions")

        # Load data (in real implementation, this would fetch from RedditHarbor database)
        with st.spinner("Loading opportunity data..."):
            # Sample data for demonstration
            sample_data = self._get_sample_data()
            opportunities = self.process_opportunity_data(sample_data)

        # Apply filters
        filters = self.render_sidebar_filters(opportunities)

        filtered_opportunities = opportunities.copy()

        # Apply score range filter
        min_score, max_score = filters['score_range']
        filtered_opportunities = [
            op for op in filtered_opportunities
            if min_score <= op['opportunity_score']['total_score'] <= max_score
        ]

        # Apply other filters
        if filters['tier']:
            filtered_opportunities = self.filter_opportunities(filtered_opportunities, tier=filters['tier'])

        if filters['subreddit']:
            filtered_opportunities = [
                op for op in filtered_opportunities
                if op.get('subreddit') == filters['subreddit']
            ]

        if filters['limit']:
            filtered_opportunities = filtered_opportunities[:filters['limit']]

        # Display results
        st.write(f"### Found {len(filtered_opportunities)} opportunities")

        # Overview section
        self.display_opportunity_overview(filtered_opportunities)

        # Opportunities table
        st.write("### Opportunity Rankings")
        self.display_opportunities_table(filtered_opportunities)

        # Detailed analysis section
        if filtered_opportunities:
            st.write("### Detailed Analysis")

            # Let user select an opportunity for detailed view
            opportunity_options = [
                f"{op.get('title', 'Untitled')} (Score: {op['opportunity_score']['total_score']})"
                for op in filtered_opportunities[:10]  # Top 10 for selection
            ]

            if opportunity_options:
                selected_index = st.selectbox("Select an opportunity for detailed analysis", range(len(opportunity_options)), format_func=lambda i: opportunity_options[i])
                selected_opportunity = filtered_opportunities[selected_index]

                self.display_opportunity_details(selected_opportunity)

    def _get_sample_data(self) -> List[Dict]:
        """
        Get sample data for demonstration
        """
        return [
            {
                'title': "I desperately need a better project management tool for our team",
                'body': "I'm so frustrated with current solutions. I would pay $50/month for something that actually works well with Slack integration. Current tools are too complex and don't integrate properly.",
                'score': 85,
                'num_comments': 42,
                'subreddit': 'productivity',
                'subscriber_count': 100000
            },
            {
                'title': "Looking for a simple habit tracking app",
                'body': "Something basic that doesn't overwhelm with features would be perfect",
                'score': 12,
                'num_comments': 8,
                'subreddit': 'selfimprovement',
                'subscriber_count': 25000
            },
            {
                'title': "Why is there no good meeting scheduling software?",
                'body': "I would pay $20/month for an intelligent scheduler that integrates with calendar and finds optimal times for team meetings.",
                'score': 65,
                'num_comments': 28,
                'subreddit': 'productivity',
                'subscriber_count': 100000
            }
        ]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_dashboard_integration.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_dashboard_integration.py src/redditharbor/dashboard/opportunity_dashboard.py
git commit -m "feat: add Streamlit dashboard for business opportunity analysis"
```

---

## Task 8: Integration with Existing RedditHarbor Pipeline

**Files:**
- Modify: `src/redditharbor/utils/analyze_research_data.py`
- Modify: `src/redditharbor/dock/pipeline.py`
- Create: `src/redditharbor/commands/opportunity_analysis.py`
- Test: `tests/test_pipeline_integration.py`

**Step 1: Write the failing test**

```python
# tests/test_pipeline_integration.py
import pytest
from redditharbor.commands.opportunity_analysis import OpportunityAnalysisCommand

def test_opportunity_analysis_command():
    command = OpportunityAnalysisCommand()

    # Test with sample project data
    result = command.run_analysis('productivity_tools', limit=10)

    assert 'opportunities' in result
    assert 'total_analyzed' in result
    assert 'top_opportunities' in result
    assert len(result['opportunities']) <= 10

def test_research_data_integration():
    from redditharbor.utils.analyze_research_data import analyze_research_data_with_opportunity_scoring

    # Sample research data
    research_data = [
        {
            'title': 'Test post',
            'body': 'I need a better solution',
            'score': 50,
            'num_comments': 20,
            'subreddit': 'test'
        }
    ]

    result = analyze_research_data_with_opportunity_scoring(research_data)

    assert 'opportunity_analysis' in result
    assert 'top_opportunities' in result['opportunity_analysis']
    assert len(result['opportunity_analysis']['top_opportunities']) > 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline_integration.py -v`
Expected: FAIL with various module not found errors

**Step 3: Write minimal implementation**

```python
# src/redditharbor/commands/opportunity_analysis.py
from typing import Dict, List
from ..utils.fetch import fetch_submissions_by_project
from ..analysis.opportunity_scorer import OpportunityScorer

class OpportunityAnalysisCommand:
    def __init__(self):
        self.scorer = OpportunityScorer()

    def run_analysis(self, project_name: str, limit: int = 50) -> Dict:
        """
        Run opportunity analysis on a specific project
        """
        # Fetch data for the project
        submissions = fetch_submissions_by_project(project_name, limit=limit)

        if not submissions:
            return {
                'opportunities': [],
                'total_analyzed': 0,
                'top_opportunities': [],
                'error': f'No data found for project: {project_name}'
            }

        # Score opportunities
        scored_opportunities = self.scorer.score_opportunities_batch(submissions)

        # Extract top opportunities (Tier A and B)
        top_opportunities = [
            op for op in scored_opportunities
            if op['opportunity_score']['tier'] in ['A', 'B']
        ]

        return {
            'opportunities': scored_opportunities,
            'total_analyzed': len(scored_opportunities),
            'top_opportunities': top_opportunities,
            'project_name': project_name,
            'summary': self._generate_summary(scored_opportunities)
        }

    def _generate_summary(self, opportunities: List[Dict]) -> Dict:
        """
        Generate summary statistics
        """
        if not opportunities:
            return {}

        # Calculate tier distribution
        tier_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        total_score = 0

        for op in opportunities:
            tier = op['opportunity_score']['tier']
            tier_counts[tier] += 1
            total_score += op['opportunity_score']['total_score']

        return {
            'total_opportunities': len(opportunities),
            'average_score': total_score / len(opportunities),
            'tier_distribution': tier_counts,
            'high_value_opportunities': tier_counts['A'] + tier_counts['B']
        }
```

**Step 4: Modify existing files**

```python
# Add to src/redditharbor/utils/analyze_research_data.py
from ..analysis.opportunity_scorer import OpportunityScorer

def analyze_research_data_with_opportunity_scoring(data: List[Dict]) -> Dict:
    """
    Enhanced research analysis with business opportunity scoring
    """
    scorer = OpportunityScorer()

    # Score all opportunities
    scored_opportunities = scorer.score_opportunities_batch(data)

    # Extract top opportunities
    top_opportunities = sorted(
        scored_opportunities,
        key=lambda x: x['opportunity_score']['total_score'],
        reverse=True
    )[:10]

    # Traditional analysis (existing functionality)
    traditional_analysis = analyze_research_data(data)  # Existing function

    return {
        'traditional_analysis': traditional_analysis,
        'opportunity_analysis': {
            'total_analyzed': len(scored_opportunities),
            'top_opportunities': top_opportunities,
            'tier_distribution': _calculate_tier_distribution(scored_opportunities)
        }
    }

def _calculate_tier_distribution(opportunities: List[Dict]) -> Dict:
    tier_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
    for op in opportunities:
        tier = op['opportunity_score']['tier']
        tier_counts[tier] += 1
    return tier_counts
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_pipeline_integration.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add tests/test_pipeline_integration.py src/redditharbor/commands/opportunity_analysis.py src/redditharbor/utils/analyze_research_data.py
git commit -m "feat: integrate business opportunity analysis with existing pipeline"
```

---

## Task 9: Documentation and Testing

**Files:**
- Create: `docs/business-opportunity-analysis.md`
- Create: `README-business-intelligence.md`
- Modify: `README.md`
- Test: `tests/test_full_integration.py`

**Step 1: Write comprehensive test for full integration**

```python
# tests/test_full_integration.py
import pytest
from redditharbor.analysis.opportunity_scorer import OpportunityScorer
from redditharbor.dashboard.opportunity_dashboard import OpportunityDashboard

def test_end_to_end_opportunity_analysis():
    """
    Test the complete pipeline from raw data to scored opportunities
    """
    # Sample raw Reddit data
    raw_data = [
        {
            'title': "I desperately need a better project management solution",
            'body': "I'm frustrated with current tools and would pay $50/month for something better with Slack integration",
            'score': 100,
            'num_comments': 50,
            'subreddit': 'productivity',
            'subscriber_count': 100000
        },
        {
            'title': "Simple note-taking app idea",
            'body': "Something basic for personal notes would be nice",
            'score': 5,
            'num_comments': 2,
            'subreddit': 'productivity',
            'subscriber_count': 1000
        }
    ]

    # Initialize scorer
    scorer = OpportunityScorer()

    # Score opportunities
    scored_opportunities = scorer.score_opportunities_batch(raw_data)

    # Verify results
    assert len(scored_opportunities) == 2

    # First opportunity should score higher
    assert scored_opportunities[0]['opportunity_score']['total_score'] > scored_opportunities[1]['opportunity_score']['total_score']

    # First should be high tier, second low tier
    assert scored_opportunities[0]['opportunity_score']['tier'] in ['A', 'B']
    assert scored_opportunities[1]['opportunity_score']['tier'] in ['C', 'D']

def test_dashboard_components():
    """
    Test dashboard functionality
    """
    dashboard = OpportunityDashboard()

    sample_data = [
        {
            'title': 'Test Opportunity',
            'opportunity_score': {
                'total_score': 75,
                'tier': 'A',
                'problem_validation_score': {'score': 30},
                'solution_viability_score': {'score': 25},
                'business_viability_score': {'score': 20}
            }
        }
    ]

    # Test filtering
    filtered = dashboard.filter_opportunities(sample_data, tier='A')
    assert len(filtered) == 1
    assert filtered[0]['opportunity_score']['tier'] == 'A'

    # Test score range filtering
    score_filtered = dashboard.filter_opportunities(sample_data, min_score=70)
    assert len(score_filtered) == 1
    assert score_filtered[0]['opportunity_score']['total_score'] >= 70

def test_scoring_consistency():
    """
    Test that scoring is consistent and reproducible
    """
    scorer = OpportunityScorer()

    test_data = {
        'title': "I hate current scheduling software and need a better solution",
        'body': "I would pay $30/month for enterprise scheduling that integrates with calendar",
        'score': 80,
        'num_comments': 40,
        'subreddit': 'productivity',
        'subscriber_count': 50000
    }

    # Score multiple times
    result1 = scorer.calculate_opportunity_score(test_data)
    result2 = scorer.calculate_opportunity_score(test_data)

    # Results should be identical
    assert result1['total_score'] == result2['total_score']
    assert result1['tier'] == result2['tier']
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_full_integration.py -v`
Expected: PASS

**Step 3: Create documentation**

```markdown
# README-business-intelligence.md
# RedditHarbor Business Intelligence Module

## Overview

The RedditHarbor Business Intelligence Module transforms Reddit discussions into actionable business opportunity insights. It systematically identifies, scores, and ranks potential app business opportunities across different sectors.

## Key Features

### 1. Business Opportunity Scoring
- **Problem Validation (40 points)**: Pain point severity, market size, engagement metrics
- **Solution Viability (35 points)**: Solution gaps, technical feasibility, competitive landscape
- **Business Viability (25 points)**: Monetization potential, growth prospects

### 2. Sector Analysis
- HealthTech, FinTech, EdTech, Productivity, ConsumerTech, EnterpriseTech, ClimateTech
- Cross-sector opportunity identification and comparison

### 3. Interactive Dashboard
- Real-time opportunity filtering and ranking
- Detailed analysis with score breakdown
- Export capabilities for presentations and reports

## Quick Start

```python
from redditharbor.analysis.opportunity_scorer import OpportunityScorer
from redditharbor.dashboard.opportunity_dashboard import OpportunityDashboard

# Score opportunities
scorer = OpportunityScorer()
opportunities = scorer.score_opportunities_batch(reddit_data)

# Launch dashboard
dashboard = OpportunityDashboard()
dashboard.run_dashboard()
```

## Business Value

- **Market Research**: Identify unmet customer needs before competitors
- **Product Validation**: Validate ideas with real user demand signals
- **Competitive Intelligence**: Understand market gaps and positioning
- **Investment Decisions**: Data-driven opportunity assessment and prioritization
```

**Step 4: Commit**

```bash
git add tests/test_full_integration.py README-business-intelligence.md docs/business-opportunity-analysis.md README.md
git commit -m "docs: add comprehensive documentation and integration tests"
```

---

## Task 10: Final Integration and Testing

**Files:**
- Modify: `setup.py` (if exists)
- Create: `requirements-business-intelligence.txt`
- Test: Run full test suite

**Step 1: Create requirements file**

```txt
# requirements-business-intelligence.txt
streamlit>=1.28.0
plotly>=5.15.0
spacy>=3.6.0
pandas>=2.0.0
numpy>=1.24.0
nltk>=3.8.0
scikit-learn>=1.3.0
```

**Step 2: Run full test suite**

```bash
# Run all tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=src/redditharbor --cov-report=html
```

**Step 3: Final commit**

```bash
git add requirements-business-intelligence.txt
git commit -m "feat: complete business intelligence module implementation"

# Tag the release
git tag -a v1.0-business-intelligence -m "Add business opportunity scoring system"
```

---

## Implementation Summary

This plan creates a comprehensive business intelligence system that transforms RedditHarbor into a powerful opportunity discovery platform. The implementation includes:

1. **5 Core Analysis Components**: Pain point detection, market sizing, solution gap analysis, monetization assessment, technical feasibility
2. **Unified Scoring System**: 100-point algorithm with tier-based ranking (A-D)
3. **Interactive Dashboard**: Streamlit-based interface for filtering, analysis, and reporting
4. **Pipeline Integration**: Seamless integration with existing RedditHarbor data collection
5. **Comprehensive Testing**: Full test coverage with integration tests
6. **Documentation**: Complete user guides and technical documentation

**Timeline**: 8-10 weeks for full implementation with testing and documentation
**Success Metrics**:
- 100+ business opportunities identified and scored per sector
- Dashboard processes 10,000+ Reddit posts in under 30 seconds
- 90% test coverage with all integration tests passing
- Clear ROI demonstration through identified market gaps and monetization potential

**Plan complete and saved to `docs/plans/2025-11-02-business-opportunity-scoring-system.md`.**

**Execution Options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**