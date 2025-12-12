# RedditHarbor Pipeline-V4 Dashboard

A comprehensive Streamlit dashboard for analyzing and tracking high-scoring opportunities from the RedditHarbor pipeline-v4 data collection system.

## Features

### Multi-Page Application

The dashboard consists of three main pages:

1. **Overview Page** - High-level metrics and opportunities table
2. **Detailed View** - Deep dive into individual opportunity details
3. **Comparison** - Side-by-side comparison of 2-3 opportunities

### Key Capabilities

- View all high-scoring opportunities (70+ score threshold)
- Filter by score range, subreddit, function count, and date range
- Click to see FULL details of any opportunity (all fields, core functions, analysis results)
- Select multiple opportunities to compare side-by-side
- Export capabilities (CSV, JSON)
- Real-time metrics:
  - Total high-scoring opportunities
  - Quarterly progress (X/50 target)
  - Function compliance rate (1-3 functions rule)
  - Score distribution

## Installation

### Prerequisites

- Python 3.12+
- PostgreSQL database with pipeline-v4 schema
- RedditHarbor pipeline-v4 environment configured

### Setup

1. Install dependencies:

```bash
# From pipeline-v4 root directory
pip install -r requirements.txt

# Or with uv
uv pip install -r requirements.txt
```

2. Ensure your `.env` file is configured with database credentials:

```bash
# Example .env configuration
DATABASE_URL=postgresql://user:password@localhost:5432/redditharbor
```

3. Verify database connection:

```bash
python -c "from database import get_db_session; print('✓ Database connection successful')"
```

## Usage

### Running the Dashboard

From the `pipeline-v4` directory:

```bash
streamlit run dashboard/app.py
```

The dashboard will open in your default browser at `http://localhost:8501`.

### Navigation

Use the sidebar to navigate between pages:
- Home page provides quick stats and overview
- **Overview** - Browse all opportunities with filters
- **Detailed View** - Explore individual opportunities in depth
- **Comparison** - Compare opportunities side-by-side

## Page Details

### 1. Overview Page

**Purpose:** Browse and filter all high-scoring opportunities

**Features:**
- Adjustable score range filters (min/max)
- Subreddit filter (multi-select)
- Core functions count filter (1-3 compliance check)
- Date range filter
- Sortable table with color-coded scores
- Export to CSV/JSON
- Key metrics dashboard

**Metrics Displayed:**
- Total opportunities count
- Function compliance rate
- Average final score
- Average WTP score
- Score distribution chart

### 2. Detailed View Page

**Purpose:** Deep dive into a single opportunity's complete data

**Features:**
- Select from dropdown of all opportunities
- Filter to show only high-scoring (70+)
- Tabbed interface for organized information:
  - **App Idea Tab:** Title, concept, problem statement, core functions, target audience
  - **Metrics Tab:** Market demand, pain intensity, monetization potential, technical feasibility, competition level
  - **Analysis Tab:** Reddit source info, opportunity summary, content quality, spam analysis
  - **Pain Points Tab:** All identified pain points
  - **Raw Data Tab:** Complete JSON data with export functionality

**Data Displayed:**
- All Opportunity model fields
- Analysis JSON structure
- Metrics JSON structure
- Function compliance check
- Score badges with visual indicators

### 3. Comparison Page

**Purpose:** Side-by-side comparison of 2-3 opportunities

**Features:**
- Multi-select dropdown (2-3 opportunities)
- Filter to show only high-scoring (70+)
- Side-by-side column layout
- Comparison sections:
  - Header scores and trust levels
  - App idea details
  - Core functions with compliance check
  - Market metrics table and chart
  - Pain points overview
  - Source information
  - Summary comparison table
- Automatic recommendation (highest compliant score)
- Export summary as CSV or detailed JSON

**Comparison Highlights:**
- Visual indicators for differences
- Compliance status for all opportunities
- Bar charts for metrics comparison
- Best option recommendation

## Data Model

The dashboard works with the `Opportunity` model from `models/analysis.py`:

### Core Fields
- `id` - Primary key
- `submission_id` - Reddit submission ID
- `subreddit` - Subreddit name
- `title` - Submission title
- `wtp_score` - Willingness-to-pay score (0-100)
- `final_score` - Final opportunity score (0-100)
- `confidence_score` - Confidence score (0-100)
- `trust_level` - LOW, MEDIUM, HIGH

### JSON Fields
- `analysis` - Contains:
  - `app_idea` - App title, concept, problem, core functions, target audience
  - `pain_points` - List of identified pain points
  - `opportunity_summary` - Summary text
  - `spam_analysis` - Spam detection results
  - `content_quality_score` - Quality metrics
- `metrics` - Contains:
  - `market_demand` - Market demand score
  - `pain_intensity` - Pain point intensity
  - `monetization_potential` - Monetization potential
  - `technical_feasibility` - Technical feasibility
  - `competition_level` - Competition level (0=high, 100=low)

### Timestamps
- `created_at` - Record creation timestamp
- `updated_at` - Last update timestamp

## Filters and Options

### Score Filters
- Min/Max score sliders (0-100 range)
- Default: 70-100 (high-scoring only)

### Function Count Filter
- 1, 2, or 3 core functions
- Validates compliance with 1-3 function rule

### Subreddit Filter
- Multi-select from all subreddits in database
- Default: All selected

### Date Range Filter
- Optional start/end date filters
- Filter by creation date

### Sorting Options
- Sort by: Final Score, WTP Score, Created, Subreddit
- Order: Ascending or Descending

## Styling and Branding

The dashboard uses CueTimer brand colors consistently:
- Primary: `#FF6B35` (Orange)
- Secondary: `#004E89` (Blue)
- Accent: `#F7B801` (Yellow)

### Score Color Coding
- **Green (High):** Score >= 85
- **Yellow (Medium):** Score >= 70
- **Red (Low):** Score < 70

### Trust Level Indicators
- 🟢 GREEN - HIGH trust
- 🟡 YELLOW - MEDIUM trust
- 🔴 RED - LOW trust

## Export Formats

### CSV Export
- Summary data with key metrics
- Compatible with Excel and data analysis tools
- Includes: ID, App Title, Submission Title, Subreddit, Scores, Functions, Trust Level, Date

### JSON Export
- Complete opportunity data
- Includes all analysis and metrics fields
- Nested structure preserved
- ISO format timestamps

## Database Requirements

The dashboard requires a PostgreSQL database with:
- `opportunities` table (managed by SQLModel)
- Proper indexes on: `submission_id`, `subreddit`, `final_score`
- Valid JSON data in `analysis` and `metrics` columns

### Database Connection
Uses `database.py` module:
```python
from database import get_db_session

with get_db_session() as session:
    # Query opportunities
    pass
```

## Troubleshooting

### Dashboard Won't Start
```bash
# Check database connection
python database.py

# Verify requirements installed
pip list | grep streamlit

# Check for port conflicts
lsof -i :8501
```

### No Data Displayed
```bash
# Verify database has data
python -c "from database import get_db_session; from models.analysis import Opportunity; from sqlmodel import select, func; session = next(get_db_session()); print(f'Opportunities: {session.exec(select(func.count(Opportunity.id))).one()}')"

# Check database URL in .env
cat .env | grep DATABASE_URL
```

### Import Errors
```bash
# Ensure running from pipeline-v4 directory
cd /path/to/pipeline-v4
streamlit run dashboard/app.py

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Performance Issues
- Index database on frequently queried columns
- Limit date range filters for large datasets
- Use high-scoring filter (70+) to reduce result set

## Development

### Adding New Features

1. **New Metrics:** Edit the metrics display sections in each page
2. **New Filters:** Add to sidebar filter section
3. **New Visualizations:** Use Streamlit chart components (st.bar_chart, st.line_chart)
4. **New Pages:** Add to `dashboard/pages/` with number prefix (e.g., `4_new_page.py`)

### Code Structure

```
dashboard/
├── app.py              # Main entry point and home page
├── pages/
│   ├── 1_overview.py   # Opportunities table and filters
│   ├── 2_detailed_view.py  # Single opportunity details
│   └── 3_comparison.py # Side-by-side comparison
└── README.md           # This file
```

### Style Guidelines

- Use CueTimer brand colors
- Follow Streamlit best practices
- Add type hints for all functions
- Include docstrings for complex logic
- Handle database errors gracefully
- Validate user input

## Future Enhancements

Potential features to add:
- [ ] Time series charts for trend analysis
- [ ] Advanced search with text matching
- [ ] Batch export of multiple opportunities
- [ ] Custom score calculations
- [ ] User preferences and saved filters
- [ ] Real-time data refresh
- [ ] Email/Slack notifications for new high-scoring opportunities
- [ ] AI-powered opportunity recommendations
- [ ] Collaborative annotations and notes

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review database schema in `models/analysis.py`
3. Verify database connection in `database.py`
4. Check Streamlit logs in terminal

## License

Part of the RedditHarbor project. See main project LICENSE file.

## Version

Dashboard Version: 1.0.0
Compatible with: Pipeline-V4
Last Updated: 2025-12-12
