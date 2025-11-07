# Research Scripts

This directory contains research framework and analysis scripts that were part of the original RedditHarbor research capabilities. These scripts provided template-based research workflows before the DLT integration.

## Scripts

### research.py
- **Purpose:** Core research framework with template support
- **Status:** Archived - superseded by DLT-based workflows
- **Reason:** Research capabilities now integrated into production pipeline
- **Context:** Original research framework using legacy data collection

### research_monetizable_opportunities.py
- **Purpose:** Research workflow for monetizable opportunity discovery
- **Status:** Archived - replaced by automated collector
- **Reason:** Functionality integrated into `automated_opportunity_collector.py`
- **Context:** Manual research workflow, now fully automated

### intelligent_research_analyzer.py
- **Purpose:** AI-powered research analyzer for insights
- **Status:** Archived - superseded by OpenRouter integration
- **Reason:** Replaced by `generate_opportunity_insights_openrouter.py`
- **Context:** Earlier implementation without OpenRouter API

## Research Templates

The original research templates from these scripts included:
1. **Monetizable App Discovery** (subreddits: r/SideProject, r/SaaS)
2. **Problem Frequency Analysis** (subreddits: r/techsupport, r/sysadmin)
3. **Feature Request Mining** (subreddits: r/feature_requests, r/AppIdeas)
4. **Sentiment Trend Analysis** (subreddits: r/technology, r/gadgets)
5. **Competitive Intelligence** (subreddits: r/Entrepreneur, r/startups)
6. **User Pain Point Discovery** (subreddits: r/mildlyinfuriating, r/CrappyDesign)

## Production Replacement

| Archived Script | Production Replacement |
|----------------|----------------------|
| `research.py` | `automated_opportunity_collector.py` |
| `research_monetizable_opportunities.py` | `automated_opportunity_collector.py` |
| `intelligent_research_analyzer.py` | `generate_opportunity_insights_openrouter.py` |

## Key Improvements in Production

The archived research scripts were replaced with:
- **Automated scheduling:** No manual execution needed
- **DLT integration:** Incremental loading and state management
- **OpenRouter AI:** Advanced insights with GPT-4 and Claude
- **Batch processing:** Efficient scoring and analysis
- **Real-time monitoring:** Built-in logging and error handling

## Architecture Evolution

**Legacy (Archived):**
```
research.py → collect data → analyze → manual insights
```

**Production (Current):**
```
automated_opportunity_collector.py → DLT pipeline → batch_opportunity_scoring.py → generate_opportunity_insights_openrouter.py
```

## Usage

These scripts are preserved for:
- Understanding original research methodology
- Template structure reference
- Comparison with production implementation
- Historical context of research capabilities

To reactivate for reference:
```bash
cp /home/carlos/projects/redditharbor/archive/archive/research/[script_name] /home/carlos/projects/redditharbor/scripts/
```
