# Function-Count Bias: Code References & Exact Locations

**Quick lookup:** Find exact file:line references for all components in the diagnosis.

---

## 🎯 LLM Profiler (Prompt Bias)

### File: `agent_tools/llm_profiler.py`

**Prompt Definition (Lines 70–105):**
```
📍 Line 70:   def _build_prompt(self, text, title, subreddit, score) -> str
📍 Line 99:   "- 1 function apps get 100 simplicity points (PREFERRED)"
📍 Line 100:  "- 2 function apps get 85 simplicity points (GOOD)"     ← BIAS HERE
📍 Line 101:  "- 3 function apps get 70 simplicity points (ACCEPTABLE)"
📍 Line 102:  "- ALWAYS prefer 1-2 functions over 3 when possible"
```

**Temperature (Deterministic Output):**
```
📍 Line 124: "temperature": 0.3,  # Lower temp for consistent output
```

**Parse Response (Function Validation):**
```
📍 Line 149: def _parse_response(self, response: str) -> dict[str, Any]
📍 Line 179: if not isinstance(profile["core_functions"], list):
📍 Line 183: if len(profile["core_functions"]) == 0:
📍 Line 185: elif len(profile["core_functions"]) > 3:
📍 Line 186:     profile["core_functions"] = profile["core_functions"][:3]
```

**Error Handling (Fallback):**
```
📍 Line 64: "core_functions": ["Manual analysis needed"],
```

---

## ✅ Constraint Validator (Counting Logic)

### File: `core/dlt/constraint_validator.py`

**DLT Resource Definition:**
```
📍 Line 14:  @dlt.resource(
📍 Line 15:  table_name="workflow_results",  ← WRITES TO workflow_results
📍 Line 16:  write_disposition="merge",
📍 Line 17:  columns={...}
```

**Schema Definition (Column Types):**
```
📍 Line 33: "core_functions": {"data_type": "bigint", "nullable": True},  ← INTEGER!
📍 Line 44: "function_list": {"data_type": "json", "nullable": True},
```

**Main Validation Function:**
```
📍 Line 42:  def app_opportunities_with_constraint(opportunities: List[Dict])
📍 Line 56:  for opportunity in opportunities:
📍 Line 58:  core_functions = _extract_core_functions(opportunity)
📍 Line 59:  function_count = len(core_functions)
📍 Line 62:  simplicity_score = _calculate_simplicity_score(function_count)
📍 Line 65:  opportunity["core_functions"] = function_count  ← CONVERTS TO INTEGER
📍 Line 67:  opportunity["is_disqualified"] = function_count >= 4
```

**Extract Core Functions (Extraction Priority):**
```
📍 Line 83:  def _extract_core_functions(opportunity: Dict) -> List[str]
📍 Line 98:  if "function_list" in opportunity and isinstance(..., list):
📍 Line 99:    return opportunity["function_list"]  ← PRIMARY PATH
📍 Line 100: elif "core_functions" in opportunity and isinstance(..., int):
📍 Line 102:   return [f"function_{i+1}" for i in range(...)]  ← FALLBACK 1
📍 Line 105: return _parse_functions_from_text(text)  ← FALLBACK 2
```

**Simplicity Scoring:**
```
📍 Line 109: def _calculate_simplicity_score(function_count: int) -> float
📍 Line 125: if function_count == 1: return 100.0
📍 Line 127: elif function_count == 2: return 85.0
📍 Line 129: elif function_count == 3: return 70.0
📍 Line 131: else: return 0.0  # AUTOMATIC DISQUALIFICATION
```

**Text Parsing (Regex patterns for extraction):**
```
📍 Line 135: def _parse_functions_from_text(text: str) -> List[str]
📍 Line 154: patterns = [...]  ← Multiple regex patterns
📍 Line 189: return functions[:3]  ← CLIPPED TO 3
```

---

## 📊 Schema Definitions

### File: `core/dlt/schemas/app_opportunities_schema.py`

**app_opportunities Table (Profiling Data):**
```
📍 Line 23:  app_opportunities_schema.add_table(
📍 Line 24:      table_name="app_opportunities",
📍 Line 43:      {"name": "core_functions", "type": "bigint", "nullable": True},  ← INTEGER!
📍 Line 53:      {"name": "function_list", "type": "json", "nullable": True},  ← JSON ARRAY
```

**Constraint Violations Table:**
```
📍 Line 74:  app_opportunities_schema.add_table(
📍 Line 75:      table_name="constraint_violations",
📍 Line 80:      {"name": "function_count", "type": "bigint", ...},
```

**Schema Documentation:**
```
📍 Line 127: SCHEMA_DOCUMENTATION = {...}
📍 Line 131: "core_functions: Number of core functions (0-10, max allowed is 3)",
```

---

### File: `core/dlt_app_opportunities.py`

**DLT Resource (Separate Definition):**
```
📍 Line 37:  @dlt.resource(
📍 Line 38:      name="app_opportunities",
📍 Line 39:      write_disposition="merge",
📍 Line 44:      "core_functions": {"data_type": "json", "nullable": False},  ← JSON!
```

**Schema Mismatch Summary:**
```
Validator (constraint_validator.py:33)    → INTEGER
Resource (dlt_app_opportunities.py:44)    → JSON
Database (workflow_results)               → BIGINT
Database (app_opportunities schema)       → BIGINT
Actual table (app_opportunities)          → varies (see migration)
```

---

## 🗄️ Database Migrations

### File: `supabase/migrations/20251108000001_workflow_results_table.sql`

**Table Creation:**
```sql
📍 Line 4:   CREATE TABLE IF NOT EXISTS workflow_results (
📍 Line 8:   function_count INTEGER NOT NULL,
📍 Line 9:   function_list TEXT[] DEFAULT '{}',
```

**Problem:** 
- `function_count` is INTEGER (stores count like 2)
- `function_list` is TEXT[] (stores array, but not used by validator)
- Constraint validator overwrites with `core_functions` BIGINT (line 33 of schema)

---

## 📤 Batch Processing Pipeline

### File: `scripts/batch_opportunity_scoring.py`

**Data Preparation:**
```
📍 Line 308: def prepare_analysis_for_storage(submission_id, analysis, sector)
📍 Line 330: core_functions = analysis.get("core_functions", [])
📍 Line 331: if isinstance(core_functions, list):
📍 Line 332:     function_count = len(core_functions)
📍 Line 333:     function_list = core_functions
📍 Line 334: else:
📍 Line 335:     function_count = core_functions if isinstance(..., int) else 1
📍 Line 338:     function_list = [f"Core function {i+1}" for i in range(...)]
📍 Line 341: analysis_data = {
📍 Line 345:     "function_count": function_count,
📍 Line 346:     "function_list": function_list,
```

**DLT Loading (Constraint Validation):**
```
📍 Line 370: def load_scores_to_supabase_via_dlt(scored_opportunities)
📍 Line 399: validated_opportunities = list(app_opportunities_with_constraint(...))
📍 Line 424: load_info = pipeline.run(
📍 Line 425:     app_opportunities_with_constraint(scored_opportunities),
```

**AI Profile Storage (Separate Path):**
```
📍 Line 451: def store_ai_profiles_to_app_opportunities_via_dlt(scored_opportunities)
📍 Line 478:     "core_functions": opp.get("function_list", []),  ← ARRAY, NOT COUNT
📍 Line 493: success = load_app_opportunities(ai_profiles)
```

---

## 🎯 Where Data Diverges (Two Paths)

### Path A: Validation (Constraint Validator)
```
batch_opportunity_scoring.py:399
    ↓
app_opportunities_with_constraint() [constraint_validator.py:42]
    ↓
DLT resource writes to: workflow_results
    ↓
workflow_results.core_functions = 2 (INTEGER count)
```

### Path B: Profiling (AI Profiles)
```
batch_opportunity_scoring.py:451
    ↓
store_ai_profiles_to_app_opportunities_via_dlt()
    ↓
load_app_opportunities() [core/dlt_app_opportunities.py:72]
    ↓
DLT resource writes to: app_opportunities
    ↓
app_opportunities.core_functions = ["Track", "Log"] (JSON array)
```

---

## 🔍 Opportunity Analyzer (Missing Step)

### File: `agent_tools/opportunity_analyzer_agent.py`

**Main Analysis Function:**
```
📍 Line 89: def analyze_opportunity(self, submission_data: Dict) -> Dict
📍 Line 120: scores = {
📍 Line 121:     "market_demand": market_demand,
📍 Line 122:     ...
📍 Line 126:     "simplicity_score": 70.0  # Default: Will be updated by constraint validator
📍 Line 127: }
📍 Line 132: result = {
📍 Line 135:     "dimension_scores": scores,
         ← NO core_functions here!
```

**Finding:** OpportunityAnalyzer does NOT generate functions; only LLMProfiler does.

---

## 🧪 Test Locations

### File: `tests/test_function_count_bias.py`

**Diagnostic Tests:**
```
📍 Line 19:  def test_function_count_distribution_shows_bias(self)
📍 Line 38:  def test_all_opportunities_have_function_data(self)
📍 Line 72:  def test_function_count_consistency_in_workflow_results(self)
```

**Unit Tests:**
```
📍 Line 104: def test_llm_profiler_respects_constraint(self)
📍 Line 124: def test_constraint_validator_counts_correctly(self)
```

**Acceptance Tests:**
```
📍 Line 250: def test_acceptance_function_count_distribution(self)
📍 Line 280: def test_acceptance_no_nulls(self)
📍 Line 304: def test_acceptance_all_in_range(self)
```

---

## 📋 Summary Table: Code Locations

| Component | File | Lines | Issue |
|-----------|------|-------|-------|
| **LLM Prompt Bias** | agent_tools/llm_profiler.py | 99–102 | Prefers 2 (INTENTIONAL) |
| **Temperature** | agent_tools/llm_profiler.py | 124 | 0.3 = deterministic |
| **Validator** | core/dlt/constraint_validator.py | 42–80 | Counts correctly, but... |
| **Validator Schema** | core/dlt/constraint_validator.py | 33 | Stores as INTEGER |
| **Analyzer Missing** | agent_tools/opportunity_analyzer_agent.py | 89–143 | No functions returned |
| **Data Prep** | scripts/batch_opportunity_scoring.py | 308–368 | Correctly extracts |
| **DLT Load (Path A)** | scripts/batch_opportunity_scoring.py | 370–449 | workflow_results |
| **AI Profiles (Path B)** | scripts/batch_opportunity_scoring.py | 451–494 | app_opportunities |
| **Schema A** | core/dlt/schemas/app_opportunities_schema.py | 43 | INTEGER type |
| **Schema B** | core/dlt_app_opportunities.py | 44 | JSON type |
| **Migration** | supabase/migrations/20251108000001...sql | 4–9 | TEXT[] vs INTEGER |

---

## 🔗 Reference Navigation

**Questions?**
- "Where does the bias come from?" → agent_tools/llm_profiler.py:99–102
- "How is it validated?" → core/dlt/constraint_validator.py:42–80
- "Where does it get stored?" → workflow_results + app_opportunities (two tables!)
- "Why are there two paths?" → scripts/batch_opportunity_scoring.py:370 vs 451
- "What's the schema mismatch?" → app_opportunities_schema.py:43 vs dlt_app_opportunities.py:44
- "What's missing?" → Post-profiling validation step

---

**All file references verified as of 2025-11-10**
**No files have been modified—all proposals only**

