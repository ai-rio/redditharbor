# Scoring Metrics Validation

This directory contains documentation for validating RedditHarbor's opportunity scoring metrics using web research and empirical data.

## Overview

RedditHarbor's pipeline uses LLM-based analysis to score opportunities on five key dimensions:
- Market Demand
- Pain Intensity
- Monetization Potential
- Technical Feasibility
- Competition Level

These scores need validation against real-world data to ensure accuracy and confidence.

## Contents

### 📄 [WEB_RESEARCH_VALIDATION_SUMMARY.md](WEB_RESEARCH_VALIDATION_SUMMARY.md)

Complete test results of using crawl4ai to validate scoring metrics against web data sources.

**Key findings:**
- ✅ crawl4ai successfully crawled 90% of validation URLs
- ❌ All 5 scoring metrics are LLM-generated without empirical backing
- ✅ Feasible to implement data-driven validation

**Metrics tested:**
1. Market Demand (70/100) - Needs Wikipedia, Reddit, Statista data
2. Pain Intensity (80/100) - Needs r/modhelp discussions, GitHub issues
3. Monetization Potential (75/100) - Needs competitor pricing analysis
4. Technical Feasibility (85/100) - Needs ML library verification
5. Competition Level (60/100) - Needs GitHub and AlternativeTo analysis

## Validation Sources

### By Metric

| Metric | Primary Sources |
|--------|-----------------|
| **Market Demand** | Wikipedia (moderation), Reddit docs, Statista |
| **Pain Intensity** | r/modhelp, GitHub issues, Reddit threads |
| **Monetization Potential** | ProductHunt, competitor sites, SaaS pricing DB |
| **Technical Feasibility** | spaCy, NLTK, GitHub projects, Reddit API |
| **Competition Level** | GitHub topics, AlternativeTo, ProductHunt |

## Implementation Roadmap

### Phase 1: Data Collection
- [ ] Configure crawl4ai extraction patterns
- [ ] Identify and validate all data sources
- [ ] Build crawl pipeline

### Phase 2: Data Processing
- [ ] Extract structured metrics from raw web data
- [ ] Create data mapping functions
- [ ] Validate extraction accuracy

### Phase 3: Score Validation
- [ ] Compare LLM scores vs. web research findings
- [ ] Calculate validation confidence scores
- [ ] Generate validation reports

### Phase 4: Continuous Updates
- [ ] Schedule periodic crawls
- [ ] Track metric changes over time
- [ ] Update scores with new data

## Tools Used

- **crawl4ai**: Web crawling and data extraction (Docker instance on port 11235)
- **Claude**: LLM-based data extraction and analysis
- **PostgreSQL/Supabase**: Data storage

## Quick Links

- [crawl4ai Documentation](/home/carlos/.claude/skills/crawl4ai/SKILL.md)
- [Main RedditHarbor Docs](../README.md)
- [Database Schema](../database/)
- [Architecture](../architecture/)

## Key Insights

### Current State (LLM-Generated)
```
Market Demand:           70/100 (no data)
Pain Intensity:          80/100 (inferred from text)
Monetization Potential:  75/100 (guessed)
Technical Feasibility:   85/100 (assumed)
Competition Level:       60/100 (generated)
```

### Validated State (Data-Backed)
```
Market Demand:           ??? (needs Wikipedia + Reddit stats)
Pain Intensity:          ??? (needs r/modhelp analysis)
Monetization Potential:  ??? (needs competitor pricing)
Technical Feasibility:   ??? (needs ML library check)
Competition Level:       ??? (needs GitHub analysis)
+ validation_confidence: % of sources supporting the score
```

## Testing Notes

Test date: 2025-12-10  
Test tool: crawl4ai Docker instance  
Success rate: 90% (9/10 URLs successfully crawled)

All 5 metrics have identifiable validation sources. Next step: implement full data extraction pipeline.

