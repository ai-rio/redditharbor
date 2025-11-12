# 🚀 RedditHarbor Clean Pipeline Scripts

<div style="display: flex; gap: 10px; margin-bottom: 20px;">
  <span style="background-color: #FF6B35; color: white; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold;">CLEAN PIPELINE</span>
  <span style="background-color: #004E89; color: white; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold;">4-SCRIPT ARCHITECTURE</span>
  <span style="background-color: #F7B801; color: #1A1A1A; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold;">PRODUCTION READY</span>
</div>

**Updated:** 2025-11-11
**Architecture:** Clean 4-Script Pipeline
**Status:** ✅ Production Ready

---

## 🎯 **Pipeline Overview**

RedditHarbor's clean pipeline architecture provides a streamlined, maintainable approach to Reddit data collection and AI opportunity analysis. Each script has a single responsibility and clear data flow.

### **Data Flow Architecture**
```
Reddit API → collect_reddit_data.py → Database submissions table → analyze_opportunities.py → Database app_opportunities table → generate_reports.py → Clean reports output → run_pipeline.py (orchestrates all)
```

---

## 📋 **Core Scripts**

### **1. collect_reddit_data.py** - `Script 1 of 4`
**Purpose:** Reddit API → Database submissions table
**Single Responsibility:** Collect and store Reddit submission data

```bash
# Collect data from default subreddits
python scripts/run_pipeline.py --stage collection

# Collect with custom limits
python scripts/run_pipeline.py --stage collection --collection-limit 25
```

**Key Features:**
- Rate limiting and error recovery
- PII anonymization compliance
- Configurable subreddit targeting
- Metadata enrichment (upvotes, comments, timestamps)

---

### **2. analyze_opportunities.py** - `Script 2 of 4`
**Purpose:** Database submissions → LLM profiler → Database app_opportunities table
**Single Responsibility:** AI-powered opportunity analysis

```bash
# Analyze submissions with AI
python scripts/run_pipeline.py --stage analysis

# Custom analysis parameters
python scripts/run_pipeline.py --stage analysis --analysis-limit 50 --min-score 40.0
```

**Key Features:**
- Claude Haiku AI analysis via OpenRouter
- High-quality app concept generation
- Structured opportunity scoring (0-100)
- Specific function identification (1-3 core functions)

---

### **3. generate_reports.py** - `Script 3 of 4`
**Purpose:** Database app_opportunities → Clean reports output
**Single Responsibility:** Generate comprehensive AI opportunity reports

```bash
# Generate reports from AI profiles
python scripts/run_pipeline.py --stage reporting

# Custom report generation
python scripts/run_pipeline.py --stage reporting --reporting-limit 10 --min-score 50.0
```

**Key Features:**
- Financial projections and market analysis
- Reddit evidence integration
- Investment readiness assessment
- Professional report formatting

---

### **4. run_pipeline.py** - `Script 4 of 4`
**Purpose:** Pipeline orchestration and coordination
**Single Responsibility:** Execute complete end-to-end pipeline

```bash
# Run full pipeline
python scripts/run_pipeline.py

# Run with custom configuration
python scripts/run_pipeline.py \
  --collection-limit 100 \
  --analysis-limit 50 \
  --reporting-limit 25
```

**Key Features:**
- Individual stage execution
- Comprehensive error handling
- Progress tracking and reporting
- Configurable parameters per stage

---

## 🛠️ **Utility Scripts**

### **clean_database_slate.py**
**Purpose:** Database maintenance and cleanup
**Usage:** `python scripts/clean_database_slate.py`

**Features:**
- Clear data while preserving table structure
- Safe database reset functionality
- Development and testing support

---

## ⚙️ **Configuration**

### **Default Pipeline Settings**
```python
{
    'collection': {
        'target_subreddits': [
            'productivity', 'selfimprovement', 'entrepreneur',
            'startups', 'personalfinance', 'technology', 'programming'
        ],
        'submissions_per_subreddit': 50
    },
    'analysis': {
        'limit': 100,
        'min_score_threshold': 30.0
    },
    'reporting': {
        'limit': 25,
        'min_score': 35.0
    }
}
```

### **Environment Requirements**
- Reddit API credentials (REDDIT_PUBLIC, REDDIT_SECRET)
- Supabase configuration (SUPABASE_URL, SUPABASE_KEY)
- OpenRouter API key for AI analysis (OPENROUTER_API_KEY)

---

## 📊 **Quality Metrics**

The clean pipeline consistently produces:
- ✅ **High-Quality AI Profiles:** Specific app concepts (72-78/100 scores)
- ✅ **Real Reddit Evidence:** Actual engagement signals and validation
- ✅ **Financial Projections:** Conservative, data-backed revenue estimates
- ✅ **Market Analysis:** Target market sizing and competitive landscape

---

## 🔄 **Usage Examples**

### **Development Workflow**
```bash
# 1. Test individual stages
python scripts/run_pipeline.py --stage collection --collection-limit 5
python scripts/run_pipeline.py --stage analysis --analysis-limit 3
python scripts/run_pipeline.py --stage reporting --reporting-limit 2

# 2. Full pipeline with small sample
python scripts/run_pipeline.py --collection-limit 10 --analysis-limit 5 --reporting-limit 3

# 3. Production pipeline
python scripts/run_pipeline.py
```

### **Monitoring**
- **Progress Tracking:** Real-time stage completion updates
- **Error Handling:** Comprehensive error reporting and recovery
- **Performance Metrics:** Execution time and data processing statistics

---

## 📁 **Output Locations**

| Stage | Output Location | Description |
|-------|-----------------|-------------|
| Collection | `submissions` table | Reddit submission data |
| Analysis | `app_opportunities` table | AI-generated app profiles |
| Reporting | `reports/` directory | Markdown opportunity reports |

---

## 🎯 **Benefits of Clean Architecture**

- **Maintainability:** 4 focused scripts vs. 50+ scattered scripts
- **Clarity:** Linear data flow with single responsibilities
- **Testability:** Each stage can be tested independently
- **Scalability:** Easy to extend and modify individual components
- **Documentation:** Clear purpose and usage for each script

---

## 🔗 **Related Documentation**

- [Database Schema](../supabase/migrations/) - Database structure and migrations
- [Clean Pipeline Architecture](../CLEAN_PIPELINE_ARCHITECTURE.md) - Complete architecture documentation
- [AI Profiler](../agent_tools/llm_profiler.py) - LLM-powered analysis engine
- [Archived Scripts](../archive/archive/scripts-2025-11-11/) - Legacy script archive

---

<div style="margin-top: 30px; padding: 15px; background-color: #F5F5F5; border-left: 4px solid #FF6B35; border-radius: 4px;">
  <strong>🎉 Success Story:</strong> The clean pipeline has eliminated script sprawl, reduced complexity from 50+ scripts to 4 focused components, and significantly improved code quality and maintainability while generating higher-quality AI app opportunities.
</div>