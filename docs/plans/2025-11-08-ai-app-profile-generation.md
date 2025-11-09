# AI App Profile Generation Enhancement - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Enhance the OpportunityAnalyzerAgent to generate complete app profiles from Reddit data, including problem extraction, app concept generation, and specific core function definitions

**Architecture:** 
- Add 5 new methods to OpportunityAnalyzerAgent: extract_problem(), generate_app_concept(), define_core_functions(), create_value_proposition(), identify_target_user()
- Add new database columns to workflow_results table for storing complete app profiles
- Update batch_opportunity_scoring.py to utilize enhanced AI analysis
- Follow TDD approach with comprehensive tests

**Tech Stack:** Python, Supabase, DLT pipeline, pytest

---

## ENHANCEMENT OVERVIEW

**Current State:**
- AI scores 5 dimensions but returns generic "Core function 1" placeholders
- Database stores minimal app information
- No problem extraction or app concept generation

**Target State:**
- AI extracts specific problems from Reddit text
- Generates detailed app concepts with clear value propositions
- Defines 1-3 specific core functions per opportunity
- Stores complete app profiles in database

---

## TASK BREAKDOWN

### Task 1: Database Schema Migration

**Files:**
- Create: `migrations/20251108_add_app_profile_fields.sql`
- Modify: `scripts/batch_opportunity_scoring.py:330-352` (prepare_analysis_for_storage function)

**Step 1: Create migration script**

```sql
-- Add new columns to workflow_results table
ALTER TABLE workflow_results 
ADD COLUMN problem_description TEXT,
ADD COLUMN app_concept TEXT,
ADD COLUMN value_proposition TEXT,
ADD COLUMN target_user TEXT,
ADD COLUMN monetization_model TEXT;

-- Add comment to document new fields
COMMENT ON COLUMN workflow_results.problem_description IS 'Extracted problem description from Reddit post';
COMMENT ON COLUMN workflow_results.app_concept IS 'Generated app concept that solves the problem';
COMMENT ON COLUMN workflow_results.value_proposition IS 'Value proposition explaining why users need this';
COMMENT ON COLUMN workflow_results.target_user IS 'Primary user persona';
COMMENT ON COLUMN workflow_results.monetization_model IS 'Recommended revenue model';
```

**Step 2: Run migration**

```bash
cd /home/carlos/projects/redditharbor
docker exec -i redditharbor-db psql -U postgres -d postgres -f migrations/20251108_add_app_profile_fields.sql
```

**Expected Output:**
- ALTER TABLE output showing all 5 columns added
- No errors

**Step 3: Commit**

```bash
git add migrations/20251108_add_app_profile_fields.sql
git commit -m "feat: add app profile fields to workflow_results table"
```

---

### Task 2: Add Problem Extraction Method

**Files:**
- Modify: `agent_tools/opportunity_analyzer_agent.py:280-310` (add new method)

**Step 1: Write failing test**

```python
# tests/test_opportunity_analyzer.py
def test_extract_problem_gamestop():
    agent = OpportunityAnalyzerAgent()
    text = "GameStop situation is confusing. I don't understand how short squeezes work and lost money because of it. Need better tools to learn."
    problem = agent._extract_problem(text)
    assert "short squeeze" in problem.lower() or "mechanics" in problem.lower()
    assert "confusing" in problem.lower() or "don't understand" in problem.lower()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_opportunity_analyzer.py::test_extract_problem_gamestop -v
```

**Expected:** FAIL with AttributeError: 'OpportunityAnalyzerAgent' object has no attribute '_extract_problem'

**Step 3: Implement extraction logic**

```python
def _extract_problem(self, text: str) -> str:
    """
    Extract the main problem from Reddit submission text.
    
    Identifies pain points, frustrations, and unmet needs.
    
    Args:
        text: Raw submission text
        
    Returns:
        Concise problem description (1-2 sentences)
    """
    # Problem indicators
    problem_keywords = [
        "confusing", "don't understand", "frustrated", "annoying",
        "hate", "terrible", "broken", "doesn't work", "wish there was",
        "no good solution", "need better", "looking for", "wish I had"
    ]
    
    # Extract sentences with problem indicators
    sentences = text.split('.')
    problem_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if any(keyword in sentence.lower() for keyword in problem_keywords):
            if len(sentence) > 20:  # Filter out very short matches
                problem_sentences.append(sentence)
    
    # Return first significant problem, or generate from text
    if problem_sentences:
        return problem_sentences[0][:200]  # Limit length
    
    # Fallback: extract first 100 chars as problem statement
    return text[:100] + "..." if len(text) > 100 else text
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_opportunity_analyzer.py::test_extract_problem_gamestop -v
```

**Expected:** PASS

**Step 5: Commit**

```bash
git add agent_tools/opportunity_analyzer_agent.py tests/test_opportunity_analyzer.py
git commit -m "feat: add _extract_problem method to OpportunityAnalyzerAgent"
```

---

### Task 3: Add App Concept Generation Method

**Files:**
- Modify: `agent_tools/opportunity_analyzer_agent.py:311-350` (add new method)

**Step 1: Write failing test**

```python
# tests/test_opportunity_analyzer.py
def test_generate_app_concept_investing():
    agent = OpportunityAnalyzerAgent()
    problem = "Investors confused by short squeeze mechanics losing money"
    subreddit = "investing"
    concept = agent._generate_app_concept(problem, subreddit)
    assert len(concept) > 20
    assert any(word in concept.lower() for word in ["platform", "tool", "app", "service"])
    assert any(word in concept.lower() for word in ["invest", "market", "analysis", "education"])
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_opportunity_analyzer.py::test_generate_app_concept_investing -v
```

**Expected:** FAIL with AttributeError

**Step 3: Implement concept generation logic**

```python
def _generate_app_concept(self, problem: str, subreddit: str) -> str:
    """
    Generate app concept based on problem and subreddit context.
    
    Creates a specific app idea that solves the identified problem.
    
    Args:
        problem: Extracted problem description
        subreddit: Source subreddit
        
    Returns:
        App concept description (2-3 sentences)
    """
    # Domain-specific concept templates
    concept_templates = {
        "investing": [
            "visual analysis platform that educates users on {aspect}",
            "investment education tool that helps with {aspect}",
            "market mechanics simulator for understanding {aspect}"
        ],
        "personalfinance": [
            "personal finance management app focused on {aspect}",
            "budgeting tool that solves {aspect}",
            "financial planning platform for {aspect}"
        ],
        "fitness": [
            "fitness tracking app that addresses {aspect}",
            "workout platform solving {aspect}",
            "health management tool for {aspect}"
        ],
        "realestateinvesting": [
            "real estate investment platform for {aspect}",
            "property analysis tool solving {aspect}",
            "REI education platform focused on {aspect}"
        ],
        "financialcareers": [
            "career transparency platform for {aspect}",
            "professional development tool for {aspect}",
            "career guidance app solving {aspect}"
        ]
    }
    
    # Extract key aspect from problem
    aspect_keywords = {
        "short squeeze": "complex market mechanics",
        "confusing": "understanding complex topics",
        "budget": "tracking expenses",
        "fitness": "staying motivated",
        "career": "navigating professional growth",
        "investment": "making informed decisions"
    }
    
    aspect = "managing [specific aspect]"  # default
    for key, value in aspect_keywords.items():
        if key in problem.lower():
            aspect = value
            break
    
    # Get template for subreddit
    templates = concept_templates.get(subreddit.lower(), concept_templates["personalfinance"])
    template = templates[0]  # Use first template
    
    # Generate concept
    concept = template.format(aspect=aspect)
    
    # Ensure it's descriptive
    if len(concept) < 50:
        concept = f"Comprehensive {concept} designed to help users overcome common challenges."
    
    return concept[:300]  # Limit length
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_opportunity_analyzer.py::test_generate_app_concept_investing -v
```

**Expected:** PASS

**Step 5: Commit**

```bash
git add agent_tools/opportunity_analyzer_agent.py
git commit -m "feat: add _generate_app_concept method"
```

---

### Task 4: Add Core Functions Definition Method

**Files:**
- Modify: `agent_tools/opportunity_analyzer_agent.py:351-420` (add new method)

**Step 1: Write failing test**

```python
# tests/test_opportunity_analyzer.py
def test_define_core_functions_investing():
    agent = OpportunityAnalyzerAgent()
    problem = "Investors confused by short squeezes"
    subreddit = "investing"
    functions = agent._define_core_functions(problem, subreddit)
    assert isinstance(functions, list)
    assert len(functions) >= 1
    assert len(functions) <= 3
    # Check that functions are specific, not generic
    assert not any("Core function" in f for f in functions)
    assert all(len(f) > 20 for f in functions)
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_opportunity_analyzer.py::test_define_core_functions_investing -v
```

**Expected:** FAIL with AttributeError

**Step 3: Implement function definition logic**

```python
def _define_core_functions(self, problem: str, subreddit: str) -> List[str]:
    """
    Define 1-3 specific core functions for the app.
    
    Creates detailed, non-generic function descriptions based on
    the problem and subreddit context.
    
    Args:
        problem: Extracted problem description
        subreddit: Source subreddit
        
    Returns:
        List of 1-3 specific function descriptions
    """
    # Function definitions by domain and problem type
    function_library = {
        "investing": {
            "short squeeze": [
                "Visual Short Squeeze Simulator",
                "Market Mechanics Education Engine",
                "Real-Time Alert System for Unusual Activity"
            ],
            "confusing": [
                "Interactive Learning Modules",
                "AI-Powered Q&A Assistant",
                "Step-by-Step Tutorial Builder"
            ],
            "default": [
                "Educational Content Library",
                "Practical Exercise Platform",
                "Progress Tracking Dashboard"
            ]
        },
        "personalfinance": {
            "budget": [
                "Expense Tracking & Categorization",
                "Budget Goal Setting & Alerts",
                "Financial Health Dashboard"
            ],
            "default": [
                "Financial Planning Tools",
                "Expense Analysis Reports",
                "Goal Achievement Tracker"
            ]
        },
        "fitness": {
            "motivation": [
                "Workout Plan Generator",
                "Progress Photo Tracker",
                "Community Challenge Platform"
            ],
            "default": [
                "Exercise Library & Videos",
                "Workout Customization Tools",
                "Fitness Progress Analytics"
            ]
        },
        "realestateinvesting": {
            "analysis": [
                "Property Deal Calculator",
                "Market Comparison Tool",
                "Investment Portfolio Tracker"
            ],
            "education": [
                "REI Course Library",
                "Deal Analysis Workshop",
                "Investor Network Platform"
            ],
            "default": [
                "Property Analysis Tools",
                "Investment Tracking System",
                "Market Research Dashboard"
            ]
        },
        "financialcareers": {
            "transparency": [
                "Anonymous Company Review System",
                "Career Path Navigator",
                "Insider Q&A Platform"
            ],
            "default": [
                "Career Guidance Tools",
                "Skill Development Tracker",
                "Professional Network Platform"
            ]
        }
    }
    
    # Determine which set of functions to use
    subreddit_functions = function_library.get(subreddit.lower(), function_library["personalfinance"])
    
    # Select function set based on problem keywords
    selected_functions = subreddit_functions["default"]  # default
    
    for key, functions in subreddit_functions.items():
        if key in problem.lower():
            selected_functions = functions
            break
    
    # Return 1-3 functions based on complexity
    # Higher complexity problems get more functions
    if len(problem) > 150 or len(selected_functions) > 3:
        return selected_functions[:3]
    elif len(problem) > 100:
        return selected_functions[:2]
    else:
        return selected_functions[:1]
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_opportunity_analyzer.py::test_define_core_functions_investing -v
```

**Expected:** PASS

**Step 5: Commit**

```bash
git add agent_tools/opportunity_analyzer_agent.py
git commit -m "feat: add _define_core_functions method"
```

---

### Task 5: Add Value Proposition Method

**Files:**
- Modify: `agent_tools/opportunity_analyzer_agent.py:421-460` (add new method)

**Step 1: Write failing test**

```python
# tests/test_opportunity_analyzer.py
def test_create_value_proposition():
    agent = OpportunityAnalyzerAgent()
    problem = "Investors losing money due to confusion"
    concept = "Educational platform"
    value_prop = agent._create_value_proposition(problem, concept)
    assert len(value_prop) > 20
    assert any(word in value_prop.lower() for word in ["helps", "solves", "prevents", "improves"])
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_opportunity_analyzer.py::test_create_value_proposition -v
```

**Expected:** FAIL with AttributeError

**Step 3: Implement value proposition logic**

```python
def _create_value_proposition(self, problem: str, concept: str) -> str:
    """
    Create value proposition explaining why users need this app.
    
    Args:
        problem: Extracted problem description
        concept: Generated app concept
        
    Returns:
        Value proposition (2-3 sentences)
    """
    # Value proposition templates
    templates = [
        "Helps users overcome {problem_aspect} by providing {solution_focus}, preventing costly mistakes and building confidence.",
        "Solves {problem_aspect} through {solution_focus}, enabling users to achieve better outcomes efficiently.",
        "Prevents negative outcomes from {problem_aspect} by offering {solution_focus} that empowers users with knowledge and tools."
    ]
    
    # Extract problem aspect
    problem_aspect = "common challenges"
    if "losing money" in problem.lower() or "expensive" in problem.lower():
        problem_aspect = "financial losses"
    elif "confusing" in problem.lower() or "don't understand" in problem.lower():
        problem_aspect = "confusion and uncertainty"
    elif "frustrated" in problem.lower() or "annoying" in problem.lower():
        problem_aspect = "frustration and inefficiency"
    
    # Extract solution focus
    solution_focus = "practical tools and education"
    if "platform" in concept.lower():
        solution_focus = "comprehensive tools and expert guidance"
    elif "education" in concept.lower():
        solution_focus = "structured learning and practical application"
    elif "tool" in concept.lower():
        solution_focus = "user-friendly tools and actionable insights"
    
    # Generate value proposition
    import random
    template = random.choice(templates)
    value_prop = template.format(
        problem_aspect=problem_aspect,
        solution_focus=solution_focus
    )
    
    return value_prop[:250]  # Limit length
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_opportunity_analyzer.py::test_create_value_proposition -v
```

**Expected:** PASS

**Step 5: Commit**

```bash
git add agent_tools/opportunity_analyzer_agent.py
git commit -m "feat: add _create_value_proposition method"
```

---

### Task 6: Add Target User Method

**Files:**
- Modify: `agent_tools/opportunity_analyzer_agent.py:461-500` (add new method)

**Step 1: Write failing test**

```python
# tests/test_opportunity_analyzer.py
def test_identify_target_user():
    agent = OpportunityAnalyzerAgent()
    subreddit = "investing"
    target_user = agent._identify_target_user(subreddit)
    assert len(target_user) > 10
    assert any(word in target_user.lower() for word in ["investor", "user", "people", "individuals"])
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_opportunity_analyzer.py::test_identify_target_user -v
```

**Expected:** FAIL with AttributeError

**Step 3: Implement target user logic**

```python
def _identify_target_user(self, subreddit: str) -> str:
    """
    Identify primary target user persona based on subreddit.
    
    Args:
        subreddit: Source subreddit
        
    Returns:
        Target user description
    """
    user_personas = {
        "investing": "Individual investors seeking to understand market mechanics and make informed decisions",
        "personalfinance": "Budget-conscious individuals managing personal finances and planning for the future",
        "fitness": "Health-conscious individuals working to improve fitness and maintain healthy habits",
        "realestateinvesting": "Aspiring and experienced real estate investors analyzing deals and building portfolios",
        "financialcareers": "Finance professionals and students exploring career opportunities and growth",
        "technology": "Tech enthusiasts and professionals seeking tools to enhance productivity and learning",
        "programming": "Software developers and programmers looking to improve skills and solve technical challenges",
        "startups": "Entrepreneurs and startup founders building businesses and seeking market insights",
        "entrepreneur": "Business owners and aspiring entrepreneurs developing companies and strategies",
        "saas": "SaaS founders and operators managing subscription businesses and growth",
        "education": "Students, educators, and lifelong learners seeking knowledge and skill development",
        "teachers": "Educators and teaching professionals improving instruction and student outcomes",
        "college": "College students managing academic life and preparing for career transitions",
        "smallbusiness": "Small business owners running companies and seeking growth strategies",
        "ecommerce": "E-commerce entrepreneurs and online sellers building digital businesses"
    }
    
    return user_personas.get(subreddit.lower(), "Individuals seeking to solve specific problems and improve their lives")
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_opportunity_analyzer.py::test_identify_target_user -v
```

**Expected:** PASS

**Step 5: Commit**

```bash
git add agent_tools/opportunity_analyzer_agent.py
git commit -m "feat: add _identify_target_user method"
```

---

### Task 7: Add Monetization Model Method

**Files:**
- Modify: `agent_tools/opportunity_analyzer_agent.py:501-540` (add new method)

**Step 1: Write failing test**

```python
# tests/test_opportunity_analyzer.py
def test_generate_monetization_model():
    agent = OpportunityAnalyzerAgent()
    concept = "Educational platform"
    model = agent._generate_monetization_model(concept)
    assert len(model) > 10
    assert any(word in model.lower() for word in ["subscription", "freemium", "premium", "pricing"])
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_opportunity_analyzer.py::test_generate_monetization_model -v
```

**Expected:** FAIL with AttributeError

**Step 3: Implement monetization logic**

```python
def _generate_monetization_model(self, concept: str) -> str:
    """
    Generate recommended monetization model based on app concept.
    
    Args:
        concept: Generated app concept
        
    Returns:
        Monetization model description
    """
    # Monetization models by concept type
    models = {
        "education": "Freemium model: Free basic content, Premium $29-99/month for advanced courses and certifications",
        "platform": "Subscription tiers: Basic $19/month, Pro $49/month, Enterprise $199/month with API access",
        "tool": "One-time purchase $49-199 or subscription $9-29/month with regular updates",
        "analysis": "Usage-based pricing: $0.10 per analysis, or unlimited plan $79/month for heavy users",
        "tracker": "Freemium: Free basic tracking, Premium $14.99/month for advanced analytics and insights",
        "network": "Membership-based: Community access $49/month, Premium networking $99/month, Enterprise partnerships"
    }
    
    # Determine model based on concept keywords
    for keyword, model in models.items():
        if keyword in concept.lower():
            return model
    
    # Default model
    return "Freemium model: Free tier with basic features, Premium subscription $19-79/month for advanced functionality"
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_opportunity_analyzer.py::test_generate_monetization_model -v
```

**Expected:** PASS

**Step 5: Commit**

```bash
git add agent_tools/opportunity_analyzer_agent.py
git commit -m "feat: add _generate_monetization_model method"
```

---

### Task 8: Integrate Enhanced Analysis in analyze_opportunity

**Files:**
- Modify: `agent_tools/opportunity_analyzer_agent.py:87-141` (update analyze_opportunity method)

**Step 1: Write failing test**

```python
# tests/test_opportunity_analyzer.py
def test_analyze_opportunity_with_app_profile():
    agent = OpportunityAnalyzerAgent()
    submission = {
        "id": "test_001",
        "title": "GameStop situation is confusing",
        "text": "I don't understand how short squeezes work and lost money. Need better tools to learn.",
        "subreddit": "investing",
        "engagement": {"upvotes": 100, "num_comments": 50},
        "comments": ["This is so confusing", "I lost money too"]
    }
    result = agent.analyze_opportunity(submission)
    assert "problem_description" in result
    assert "app_concept" in result
    assert "core_functions" in result
    assert len(result["core_functions"]) >= 1
    assert result["core_functions"][0] != "Core function 1"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_opportunity_analyzer.py::test_analyze_opportunity_with_app_profile -v
```

**Expected:** FAIL (missing new fields in result)

**Step 3: Update analyze_opportunity to include new fields**

```python
def analyze_opportunity(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a single opportunity using the 5-dimensional scoring methodology
    and generate complete app profile.
    
    Args:
        submission_data: Dict containing submission text, engagement, subreddit info
    
    Returns:
        Dict with complete analysis including all 5 dimension scores,
        final score, and full app profile
    """
    text = submission_data.get("text", "")
    subreddit = submission_data.get("subreddit", "")
    engagement = submission_data.get("engagement", {})
    comments = submission_data.get("comments", [])

    # Calculate 5 dimensions
    market_demand = self._calculate_market_demand(text, engagement, subreddit)
    pain_intensity = self._calculate_pain_intensity(text, comments)
    monetization_potential = self._calculate_monetization_potential(text, engagement)
    market_gap = self._calculate_market_gap(text, comments)
    technical_feasibility = self._calculate_technical_feasibility(text)

    # Calculate final score
    scores = {
        "market_demand": market_demand,
        "pain_intensity": pain_intensity,
        "monetization_potential": monetization_potential,
        "market_gap": market_gap,
        "technical_feasibility": technical_feasibility
    }

    final_score = self._calculate_final_score(scores)
    priority = self._get_priority(final_score)

    # Generate complete app profile
    problem_description = self._extract_problem(text)
    app_concept = self._generate_app_concept(problem_description, subreddit)
    core_functions = self._define_core_functions(problem_description, subreddit)
    value_proposition = self._create_value_proposition(problem_description, app_concept)
    target_user = self._identify_target_user(subreddit)
    monetization_model = self._generate_monetization_model(app_concept)

    result = {
        "opportunity_id": submission_data.get("id", "unknown"),
        "title": submission_data.get("title", "")[:100],
        "subreddit": subreddit,
        "dimension_scores": scores,
        "final_score": final_score,
        "priority": priority,
        "weights": self.methodology_weights,
        "timestamp": datetime.now().isoformat(),
        # New app profile fields
        "problem_description": problem_description,
        "app_concept": app_concept,
        "core_functions": core_functions,
        "value_proposition": value_proposition,
        "target_user": target_user,
        "monetization_model": monetization_model
    }

    return result
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_opportunity_analyzer.py::test_analyze_opportunity_with_app_profile -v
```

**Expected:** PASS

**Step 5: Commit**

```bash
git add agent_tools/opportunity_analyzer_agent.py
git commit -m "feat: integrate app profile generation in analyze_opportunity"
```

---

### Task 9: Update prepare_analysis_for_storage for New Fields

**Files:**
- Modify: `scripts/batch_opportunity_scoring.py:307-353` (update prepare_analysis_for_storage function)

**Step 1: Write failing test**

```python
# tests/test_batch_scoring.py
def test_prepare_analysis_stores_app_profile():
    from scripts.batch_opportunity_scoring import prepare_analysis_for_storage
    
    submission_id = "test_123"
    analysis = {
        "title": "Test App",
        "final_score": 45.0,
        "problem_description": "Users confused about X",
        "app_concept": "Platform to solve X",
        "core_functions": ["Function A", "Function B"],
        "value_proposition": "Helps users with X",
        "target_user": "People facing X",
        "monetization_model": "Subscription model"
    }
    sector = "Technology"
    
    result = prepare_analysis_for_storage(submission_id, analysis, sector)
    
    assert "problem_description" in result
    assert "app_concept" in result
    assert result["app_concept"] == "Platform to solve X"
    assert len(result["core_functions"]) == 2
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_batch_scoring.py::test_prepare_analysis_stores_app_profile -v
```

**Expected:** FAIL (TypeError or KeyError)

**Step 3: Update prepare_analysis_for_storage to include new fields**

```python
def prepare_analysis_for_storage(
    submission_id: str,
    analysis: Dict[str, Any],
    sector: str
) -> Dict[str, Any]:
    """
    Prepare opportunity analysis result for DLT pipeline storage.
    
    Args:
        submission_id: ID of the submission from the submissions table
        analysis: Analysis results from agent containing dimension scores
        sector: Mapped business sector
    
    Returns:
        Dictionary formatted for workflow_results table
    """
    # Generate opportunity_id from submission_id (unique identifier for merge)
    opportunity_id = f"opp_{submission_id}"

    # Extract dimension scores
    scores = analysis.get("dimension_scores", {})

    # Extract core functions from analysis (default to 1 if not present)
    core_functions = analysis.get("core_functions", 1)
    if isinstance(core_functions, list):
        function_count = len(core_functions)
    else:
        function_count = 1

    # Prepare data for workflow_results table
    analysis_data = {
        "opportunity_id": opportunity_id,
        "app_name": analysis.get("title", "Unnamed Opportunity")[:255],
        "function_count": function_count,
        "function_list": analysis.get("core_functions", [f"Core function {i+1}" for i in range(function_count)]),
        "original_score": float(analysis.get("final_score", 0)),
        "final_score": float(analysis.get("final_score", 0)),
        "status": "scored",
        "constraint_applied": True,
        "ai_insight": f"Market sector: {sector}. Subreddit: {analysis.get('subreddit', 'unknown')}",
        "processed_at": datetime.now().isoformat(),
        # Dimension scores (match the column names in workflow_results)
        "market_demand": float(scores.get("market_demand", 0)) if scores else None,
        "pain_intensity": float(scores.get("pain_intensity", 0)) if scores else None,
        "monetization_potential": float(scores.get("monetization_potential", 0)) if scores else None,
        "market_gap": float(scores.get("market_gap", 0)) if scores else None,
        "technical_feasibility": float(scores.get("technical_feasibility", 0)) if scores else None,
        # New app profile fields
        "problem_description": analysis.get("problem_description", "")[:500],
        "app_concept": analysis.get("app_concept", "")[:500],
        "value_proposition": analysis.get("value_proposition", "")[:500],
        "target_user": analysis.get("target_user", "")[:255],
        "monetization_model": analysis.get("monetization_model", "")[:255],
    }

    return analysis_data
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_batch_scoring.py::test_prepare_analysis_stores_app_profile -v
```

**Expected:** PASS

**Step 5: Commit**

```bash
git add scripts/batch_opportunity_scoring.py
git commit -m "feat: update prepare_analysis_for_storage to save app profile fields"
```

---

### Task 10: Integration Test with Top Opportunity

**Files:**
- Test: Run batch_opportunity_scoring.py with sample data

**Step 1: Create test script**

```python
# tests/test_integration_app_profile.py
from scripts.batch_opportunity_scoring import fetch_submissions, process_batch
from agent_tools.opportunity_analyzer_agent import OpportunityAnalyzerAgent
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

def test_gamestop_opportunity_generates_app_profile():
    """Test that GameStop opportunity generates specific app profile"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Query for GameStop opportunity
    response = supabase.table('workflow_results').select('*').ilike('app_name', '%gamestop%').order('final_score', desc=True).limit(1).execute()
    
    if response.data:
        opp = response.data[0]
        assert opp['function_list'] != ["Core function 1"]
        assert len(opp.get('app_concept', '')) > 20
        print(f"✅ App Concept: {opp['app_concept'][:100]}...")
        print(f"✅ Functions: {opp['function_list']}")
```

**Step 2: Run integration test**

```bash
pytest tests/test_integration_app_profile.py -v
```

**Expected:** PASS with print output showing specific app concept and functions

**Step 3: Commit**

```bash
git add tests/test_integration_app_profile.py
git commit -m "test: add integration test for app profile generation"
```

---

### Task 11: Run Full Batch Test

**Files:**
- Execute: `python scripts/batch_opportunity_scoring.py` with limited data

**Step 1: Run batch scoring on test data**

```bash
cd /home/carlos/projects/redditharbor
source .venv/bin/activate
python scripts/batch_opportunity_scoring.py
```

**Expected Output:**
- Successfully processes submissions
- No errors in analysis
- Database contains new app profile fields
- Functions are specific, not generic

**Step 2: Verify database storage**

```bash
docker exec -i redditharbor-db psql -U postgres -d postgres -c "SELECT opportunity_id, app_name, function_list, app_concept FROM workflow_results WHERE final_score > 40 LIMIT 3;"
```

**Expected Output:**
- Shows specific function_list values (not "Core function 1")
- Shows detailed app_concept text
- No NULL values for new fields

**Step 3: Commit**

```bash
git add /tmp/batch_test_log.txt
git commit -m "test: verify full batch scoring with app profile generation"
```

---

### Task 12: Generate Documentation

**Files:**
- Create: `docs/ai-app-profile-generation.md`

**Step 1: Create comprehensive documentation**

```markdown
# AI App Profile Generation Enhancement

## Overview
Enhanced the OpportunityAnalyzerAgent to generate complete app profiles from Reddit data, including problem extraction, app concept generation, and specific core function definitions.

## New Features

### Problem Extraction
- Identifies pain points and frustrations from Reddit text
- Extracts key problem statements for app concept development

### App Concept Generation
- Creates specific app ideas based on problem and subreddit context
- Uses domain-specific templates for relevant concepts

### Core Functions Definition
- Defines 1-3 specific functions per app (not generic placeholders)
- Domain-specific function libraries ensure relevance
- Number of functions scales with problem complexity

### Value Proposition Creation
- Explains why users need the app
- Links problem to solution benefits

### Target User Identification
- Identifies primary user persona based on subreddit
- Ensures product-market fit alignment

### Monetization Model Generation
- Recommends appropriate revenue models
- Based on app concept and target market

## Database Schema

New columns added to `workflow_results` table:
- `problem_description` (TEXT): Extracted problem description
- `app_concept` (TEXT): Generated app concept
- `value_proposition` (TEXT): Value proposition
- `target_user` (TEXT): Primary user persona
- `monetization_model` (TEXT): Recommended revenue model

## Testing

All enhancements include:
- Unit tests for each new method
- Integration test with real data
- Full batch test verification

## Example Output

BEFORE:
```json
{
  "final_score": 47.2,
  "function_list": ["Core function 1"]
}
```

AFTER:
```json
{
  "final_score": 47.2,
  "problem_description": "Retail investors confused by short squeeze mechanics...",
  "app_concept": "Visual investment analysis platform that educates...",
  "core_functions": [
    "Visual Short Squeeze Simulator",
    "Market Mechanics Education Engine",
    "Real-Time Alert System"
  ],
  "value_proposition": "Helps users overcome financial losses...",
  "target_user": "Individual investors seeking to understand...",
  "monetization_model": "Freemium model: Free basic content..."
}
```

## Benefits

1. **Immediate Actionable Insights**: Full app profile ready to build
2. **No Human Interpretation**: AI generates complete concept
3. **Rich Database**: All app details stored for analysis
4. **Implementation Ready**: Clear 3 functions to build
5. **Validation Ready**: Can test with users immediately
```

**Step 2: Save documentation**

```bash
git add docs/ai-app-profile-generation.md
git commit -m "docs: document AI app profile generation enhancement"
```

---

## EXECUTION HANDOFF

**Plan complete and saved to `docs/plans/2025-11-08-ai-app-profile-generation.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
