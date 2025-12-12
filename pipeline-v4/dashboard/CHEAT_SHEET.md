# Dashboard Cheat Sheet

Quick reference for the RedditHarbor Pipeline-V4 Dashboard.

---

## 🚀 Launch Commands

```bash
# Quick start (recommended)
./run_dashboard.sh

# Direct command
streamlit run dashboard/app.py

# Alternative port
streamlit run dashboard/app.py --server.port 8502

# With browser auto-open disabled
streamlit run dashboard/app.py --server.headless true
```

---

## 📂 File Locations

```
pipeline-v4/
├── dashboard/
│   ├── app.py                    # Home page
│   ├── pages/
│   │   ├── 1_overview.py         # Table view
│   │   ├── 2_detailed_view.py    # Single opportunity
│   │   └── 3_comparison.py       # Side-by-side
│   └── README.md                 # Full docs
├── run_dashboard.sh              # Launch script
├── test_dashboard_setup.py       # Verification
└── requirements.txt              # Dependencies
```

---

## 🎯 Page Navigation

| Page | Purpose | Key Features |
|------|---------|-------------|
| **Home** | Overview & stats | Quick metrics, progress tracker |
| **Overview** | Browse all opportunities | Filters, table, export |
| **Detailed View** | Deep dive single item | 5 tabs, full data |
| **Comparison** | Compare 2-3 items | Side-by-side, recommendation |

---

## 🔍 Common Tasks

### View High-Scoring Opportunities
```
1. Go to: Overview
2. Filter: Min score = 70
3. Sort: Final Score (descending)
4. Review: Top results
```

### Check Compliance
```
1. Go to: Overview
2. Look at: "Function Compliance" metric
3. Filter: Core Functions Count = [1, 2, 3]
4. Check: "Functions" column
```

### Compare Top 3
```
1. Go to: Comparison
2. Select: 3 highest scores
3. Review: Side-by-side details
4. Check: Recommendation section
5. Export: If needed
```

### Export Filtered Data
```
1. Go to: Overview
2. Apply: Desired filters
3. Scroll: To "Export Data"
4. Click: "Download as CSV/JSON"
```

### View Full Details
```
1. Note: Opportunity ID from Overview
2. Go to: Detailed View
3. Select: From dropdown
4. Explore: All 5 tabs
```

---

## 🎛️ Filters Quick Reference

### Score Range
- **Location:** Overview sidebar
- **Type:** Dual slider
- **Range:** 0-100
- **Default:** 70-100

### Function Count
- **Location:** Overview sidebar
- **Type:** Multi-select
- **Options:** 1, 2, 3
- **Default:** All selected

### Subreddit
- **Location:** Overview sidebar
- **Type:** Multi-select
- **Options:** From database
- **Default:** All selected

### Date Range
- **Location:** Overview sidebar
- **Type:** Date pickers
- **Default:** Disabled (checkbox)

### High-Scoring Only
- **Location:** Detailed View / Comparison sidebar
- **Type:** Checkbox
- **Default:** Enabled (70+)

---

## 📊 Metrics Explained

| Metric | Range | Meaning |
|--------|-------|---------|
| **Final Score** | 0-100 | Overall opportunity score |
| **WTP Score** | 0-100 | Willingness-to-pay score |
| **Confidence** | 0-100 | Analysis confidence level |
| **Market Demand** | 0-100 | Market demand strength |
| **Pain Intensity** | 0-100 | Pain point severity |
| **Monetization** | 0-100 | Revenue potential |
| **Tech Feasibility** | 0-100 | Implementation difficulty |
| **Competition** | 0-100 | 0=high, 100=low competition |

---

## 🎨 Color Codes

### Score Colors
- 🟢 **Green:** 85-100 (Excellent)
- 🟡 **Yellow:** 70-84 (Good)
- 🔴 **Red:** 0-69 (Review needed)

### Trust Levels
- 🟢 **HIGH:** Highest confidence
- 🟡 **MEDIUM:** Moderate confidence
- 🔴 **LOW:** Lower confidence

### Compliance Status
- ✓ **Compliant:** 1-3 core functions
- ✗ **Non-compliant:** Outside 1-3 range

---

## 📤 Export Formats

### CSV Format
- **Use for:** Excel, Google Sheets, data analysis
- **Contains:** Summary data with key fields
- **Fields:** ID, Title, Scores, Functions, Trust, Date

### JSON Format
- **Use for:** Programming, API integration, archiving
- **Contains:** Complete data with all nested fields
- **Structure:** Full opportunity object with analysis

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+C` | Stop dashboard (terminal) |
| `R` | Rerun dashboard (browser) |
| `C` | Clear cache (browser menu) |
| `?` | Show shortcuts (browser) |

---

## 🐛 Troubleshooting

### Dashboard Won't Start
```bash
# Check installation
pip list | grep streamlit

# Check port
lsof -i :8501

# Try different port
streamlit run dashboard/app.py --server.port 8502
```

### No Data Displayed
```bash
# Check database
python3 database.py

# Check opportunity count
python3 -c "from database import get_db_session; from models.analysis import Opportunity; from sqlmodel import select, func; session = next(get_db_session()); print(session.exec(select(func.count(Opportunity.id))).one())"
```

### Import Errors
```bash
# Verify location
pwd  # Should be in pipeline-v4/

# Check Python path
python3 -c "import sys; print('\n'.join(sys.path))"

# Run from correct location
cd /path/to/pipeline-v4
streamlit run dashboard/app.py
```

### Database Connection Error
```bash
# Check .env file
cat .env | grep DATABASE_URL

# Test connection
python3 database.py

# Verify PostgreSQL is running
pg_isready
```

---

## 🔧 Configuration

### Database URL
```bash
# In .env or .env.local
DATABASE_URL=postgresql://user:pass@host:port/database
```

### Streamlit Config
```bash
# Create ~/.streamlit/config.toml
[server]
port = 8501
address = "localhost"

[browser]
gatherUsageStats = false
```

---

## 📊 SQL Queries (Direct Database)

### Count Opportunities
```sql
SELECT COUNT(*) FROM opportunities;
```

### High-Scoring Count
```sql
SELECT COUNT(*) FROM opportunities WHERE final_score >= 70;
```

### Average Score
```sql
SELECT AVG(final_score) FROM opportunities;
```

### Compliance Check
```sql
SELECT
  submission_id,
  jsonb_array_length(analysis->'app_idea'->'core_functions') as func_count
FROM opportunities;
```

---

## 💡 Tips & Tricks

### Performance
- Use high-scoring filter (70+) for faster loading
- Apply subreddit filters to reduce result set
- Close unused tabs to free memory

### Comparison
- Compare opportunities with similar scores
- Focus on metrics with largest differences
- Check compliance status across all

### Export
- Export filtered data before changing filters
- Use CSV for spreadsheets, JSON for code
- Download before closing browser

### Navigation
- Use browser back button to return to filters
- Bookmark specific pages for quick access
- Keep multiple tabs open for parallel work

---

## 📚 Documentation Links

| Document | Purpose |
|----------|---------|
| `QUICK_START.md` | 5-minute setup guide |
| `README.md` | Comprehensive documentation |
| `FEATURES.md` | Feature showcase with examples |
| `IMPLEMENTATION_COMPLETE.md` | Implementation details |
| `CHEAT_SHEET.md` | This file |

---

## 🆘 Quick Help

### Installation Issues
→ Read `QUICK_START.md` section "Troubleshooting"

### Usage Questions
→ Read `README.md` section "Usage"

### Feature Details
→ Read `FEATURES.md` for visual examples

### Database Setup
→ Check `database.py` and `.env` configuration

### Code Understanding
→ Review inline comments in Python files

---

## 🎓 Learning Path

1. **Start here:** `QUICK_START.md` (5 min)
2. **Explore:** Launch dashboard, click around
3. **Deep dive:** Read `README.md` sections
4. **Reference:** Use this cheat sheet
5. **Customize:** Modify code in `dashboard/`

---

## ⚡ Quick Install

```bash
# One-liner install and run
cd /path/to/pipeline-v4 && \
pip install streamlit pandas && \
python3 test_dashboard_setup.py && \
./run_dashboard.sh
```

---

## 📞 Support Flow

```
Issue
  ↓
Check CHEAT_SHEET.md (this file)
  ↓
Still stuck?
  ↓
Check QUICK_START.md "Troubleshooting"
  ↓
Still stuck?
  ↓
Check README.md "Troubleshooting"
  ↓
Still stuck?
  ↓
Review database.py and models/analysis.py
  ↓
Still stuck?
  ↓
Check Streamlit logs in terminal
```

---

## ✅ Verification

```bash
# Run full verification
python3 test_dashboard_setup.py

# Quick check
streamlit run dashboard/app.py --help
```

---

*Keep this cheat sheet handy for quick reference!*

**Version:** 1.0.0
**Last Updated:** 2025-12-12
