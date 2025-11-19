# Agent Tools Restructuring - Detailed Guide

Extended details for Phase 2: Agent Tools Restructuring.

---

## Overview

This guide provides comprehensive details for restructuring the `agent_tools/` directory into `core/agents/` with logical grouping and file size optimization.

---

## Current Structure Analysis

### File Inventory

```bash
agent_tools/
├── llm_profiler_enhanced.py          # 37KB - AI profiling
├── llm_profiler.py                   # 15KB - Base profiler
├── market_data_validator.py          # 70KB - Market validation ⚠️ VERY LARGE
├── market_validation_integration.py  # 20KB
├── market_validation_persistence.py  # 15KB
├── monetization_agno_analyzer.py     # 63KB - Monetization ⚠️ LARGE
├── monetization_llm_analyzer.py      # 18KB
├── monetization_analyzer_factory.py  # 9KB
├── jina_hybrid_client.py            # 30KB - Search
├── jina_mcp_client.py               # 24KB
├── jina_mcp_client_simple.py        # 27KB
├── jina_reader_client.py            # 19KB
├── interactive_analyzer.py          # 7KB
├── agno_validation_converter.py     # 9KB
└── README.md

Total: 15 files, ~360KB
```

**Problems**:
- ❌ Flat structure (no logical grouping)
- ❌ 70KB file (too large)
- ❌ Multiple Jina clients (should be unified)
- ❌ Mixed concerns

---

## Target Structure

```bash
core/agents/
├── __init__.py
├── README.md
├── profiler/
│   ├── __init__.py
│   ├── enhanced_profiler.py        # From llm_profiler_enhanced.py (25KB)
│   ├── base_profiler.py            # From llm_profiler.py (15KB)
│   ├── prompt_templates.py         # Extracted (5KB)
│   └── response_parser.py          # Extracted (5KB)
├── monetization/
│   ├── __init__.py
│   ├── agno_analyzer.py            # From monetization_agno_analyzer.py (25KB)
│   ├── multi_agent_pipeline.py    # Extracted (20KB)
│   ├── pricing_calculator.py      # Extracted (15KB)
│   ├── llm_analyzer.py            # From monetization_llm_analyzer.py (18KB)
│   ├── factory.py                 # From monetization_analyzer_factory.py (9KB)
│   └── validation_converter.py    # From agno_validation_converter.py (9KB)
├── market_validation/
│   ├── __init__.py
│   ├── validator.py               # Main class (25KB)
│   ├── search_client.py           # Extracted (20KB)
│   ├── analysis_engine.py         # Extracted (20KB)
│   ├── integration.py             # From market_validation_integration.py (20KB)
│   └── persistence.py             # From market_validation_persistence.py (15KB)
├── search/
│   ├── __init__.py
│   ├── hybrid_client.py           # From jina_hybrid_client.py (30KB)
│   ├── mcp_client.py              # From jina_mcp_client.py (24KB)
│   ├── mcp_client_simple.py       # From jina_mcp_client_simple.py (27KB)
│   ├── reader_client.py           # From jina_reader_client.py (19KB)
│   └── factory.py                 # New: unified client selection
└── interactive/
    ├── __init__.py
    └── analyzer.py                # From interactive_analyzer.py (7KB)
```

**Improvements**:
- ✅ Logical grouping by functionality
- ✅ All files <30KB
- ✅ Clear module boundaries
- ✅ Easier to navigate

---

## Detailed Refactoring Steps

### Step 1: Profiler Module

**Extract Prompt Templates**:

```python
# core/agents/profiler/prompt_templates.py
"""Prompt templates for AI profiling."""

PROFILE_GENERATION_PROMPT = """
Analyze this Reddit submission and extract:
1. Proposed app/product name
2. Core functions (3-5 key features)
3. Value proposition
4. Target audience

Submission:
Title: {title}
Content: {content}
Subreddit: {subreddit}

Provide structured JSON output.
"""

CORE_FUNCTIONS_PROMPT = """
Extract 3-5 core functions from this description:
{description}

Format as JSON array.
"""
```

**Extract Response Parser**:

```python
# core/agents/profiler/response_parser.py
"""Parse LLM responses for profiling."""

import json
from typing import Dict, Any, Optional

def parse_profile_response(response: str) -> Dict[str, Any]:
    """Parse JSON response from profiler."""
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Fallback parsing logic
        return extract_fields_from_text(response)

def extract_fields_from_text(text: str) -> Dict[str, Any]:
    """Extract fields when JSON parsing fails."""
    # Implementation...
    pass
```

**Updated Enhanced Profiler**:

```python
# core/agents/profiler/enhanced_profiler.py (now 25KB)
from .prompt_templates import PROFILE_GENERATION_PROMPT
from .response_parser import parse_profile_response

class EnhancedLLMProfiler:
    def generate_profile(self, submission_title: str, ...):
        prompt = PROFILE_GENERATION_PROMPT.format(
            title=submission_title,
            ...
        )
        
        response = self.llm_client.generate(prompt)
        return parse_profile_response(response)
```

---

### Step 2: Market Validation Module

**Break up 70KB file**:

```python
# core/agents/market_validation/search_client.py (20KB)
"""Search and competitor research."""

class MarketSearchClient:
    """Handle market research and competitor search."""
    
    def __init__(self, jina_client):
        self.jina = jina_client
    
    def search_competitors(self, app_concept: str) -> List[str]:
        """Search for competing products."""
        query = f"alternatives to {app_concept}"
        return self.jina.search(query, limit=10)
    
    def analyze_competitor(self, competitor_url: str) -> Dict:
        """Analyze single competitor."""
        # Implementation...
        pass

# core/agents/market_validation/analysis_engine.py (20KB)
"""Market data analysis."""

class MarketAnalysisEngine:
    """Analyze market data and generate insights."""
    
    def analyze_market_size(self, data: Dict) -> float:
        """Estimate market size."""
        # Implementation...
        pass
    
    def calculate_competition_score(self, competitors: List) -> float:
        """Score competitive landscape."""
        # Implementation...
        pass

# core/agents/market_validation/validator.py (25KB)
"""Main market data validator using composition."""

from .search_client import MarketSearchClient
from .analysis_engine import MarketAnalysisEngine

class MarketDataValidator:
    """Orchestrate market validation."""
    
    def __init__(self, jina_client):
        self.search_client = MarketSearchClient(jina_client)
        self.analysis_engine = MarketAnalysisEngine()
    
    def validate(self, submission: Dict) -> Dict:
        """Full market validation."""
        # Use search_client and analysis_engine
        competitors = self.search_client.search_competitors(...)
        analysis = self.analysis_engine.analyze_market_size(...)
        
        return {
            'competitors': competitors,
            'market_size': analysis,
            ...
        }
```

---

### Step 3: Update All Imports

**Create import mapping**:

```python
# scripts/update_imports.py
"""Update all imports from agent_tools to core.agents."""

IMPORT_MAPPING = {
    'from agent_tools.llm_profiler_enhanced import': 'from core.agents.profiler import',
    'from agent_tools.market_data_validator import': 'from core.agents.market_validation import',
    'from agent_tools.monetization_agno_analyzer import': 'from core.agents.monetization import',
    # ... more mappings
}

def update_file_imports(filepath: str):
    """Update imports in single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    for old, new in IMPORT_MAPPING.items():
        content = content.replace(old, new)
    
    with open(filepath, 'w') as f:
        f.write(content)

# Run on all Python files
for filepath in find_all_python_files():
    update_file_imports(filepath)
```

---

## Testing Strategy

```python
# tests/test_agent_restructuring.py
"""Validate agent restructuring."""

def test_all_agents_importable():
    """Ensure all agents can be imported."""
    from core.agents.profiler import EnhancedLLMProfiler
    from core.agents.monetization import MonetizationAgnoAnalyzer
    from core.agents.market_validation import MarketDataValidator
    # All imports should work

def test_profiler_functionality_preserved():
    """Validate profiler still works identically."""
    from core.agents.profiler import EnhancedLLMProfiler
    
    profiler = EnhancedLLMProfiler(...)
    result = profiler.generate_profile(...)
    
    # Verify same output format as before
    assert 'app_name' in result
    assert 'core_functions' in result

def test_no_circular_imports():
    """Ensure no circular dependencies."""
    # Attempt to import all modules
    # Should not raise ImportError
```

---

## Benefits Achieved

1. **Improved Maintainability**: Logical grouping makes code easier to find
2. **Better Testing**: Can test modules independently
3. **Reduced Complexity**: 70KB file split into manageable pieces
4. **Clear Boundaries**: Each module has single responsibility
5. **Future-Ready**: Easy to add new agents or features

---

For execution details, see [Phase 2: Agent Tools Restructuring](../phases/phase-02-agent-restructuring.md)
