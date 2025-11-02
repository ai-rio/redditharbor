# RedditHarbor Multi-Project Setup

This directory contains a complete RedditHarbor setup configured for your local Supabase instance that supports multiple projects.

## 🏗️ Architecture Overview

```
Your Local Supabase Instance (http://127.0.0.1:54321)
├── Other Projects (schemas/tables)
├── redditharbor (dedicated schema)
│   ├── redditor (Reddit user data)
│   ├── submission (Reddit posts)
│   └── comment (Reddit comments)
└── Future Projects...
```

## 📁 Files Created

- `redditharbor_config.py` - Main configuration file
- `redditharbor_setup.py` - Setup and testing script
- `redditharbor_project_templates.py` - Pre-configured project templates
- `README_redditharbor_setup.md` - This documentation

## 🚀 Quick Start

### 1. Configure Reddit API Credentials

Edit `redditharbor_config.py` with your Reddit API credentials:

```python
# Get these from: https://www.reddit.com/prefs/apps
REDDIT_PUBLIC = "your-public-key"
REDDIT_SECRET = "your-secret-key"
REDDIT_USER_AGENT = "your-institution:project-name (u/your-username)"
```

### 2. Activate Virtual Environment

```bash
source .venv/bin/activate
```

### 3. Test the Setup

```bash
python redditharbor_setup.py
```

### 4. Run Project Templates

```bash
python redditharbor_project_templates.py
```

## 🗄️ Database Schema

RedditHarbor data is stored in the `redditharbor` schema:

- `redditharbor.redditor` - User information
- `redditharbor.submission` - Posts/submissions
- `redditharbor.comment` - Comments

This isolation ensures RedditHarbor doesn't interfere with your other projects.

## 📊 Available Project Templates

- `tech_research` - Academic research on programming
- `ai_ml_monitoring` - AI/ML trend monitoring
- `startup_analysis` - Startup ecosystem research
- `gaming_community` - Gaming community analysis

## 🔒 Privacy Configuration

PII anonymization is enabled by default (`ENABLE_PII_ANONYMIZATION = True`). This protects:
- Usernames and mentions
- Email addresses
- Phone numbers
- Personal identifiers
- Geographic locations

## 🌐 Access Your Data

- **Supabase Studio**: http://127.0.0.1:54323
- **API URL**: http://127.0.0.1:54321
- **Database URL**: `postgresql://postgres:postgres@127.0.0.1:54322/postgres`

## 🛠️ Managing Multiple Projects

### Adding New Projects

1. Create a new schema for each project:
```sql
CREATE SCHEMA IF NOT EXISTS your_new_project;
```

2. Modify `DB_CONFIG` in your project script:
```python
DB_CONFIG = {
    "user": "your_new_project.redditor",
    "submission": "your_new_project.submission",
    "comment": "your_new_project.comment"
}
```

### Data Isolation

Each project's data remains completely isolated in its own schema, allowing:
- Independent data management
- Project-specific access controls
- Easy backup and export
- Cross-project analysis when needed

## 🔧 Custom Collection Scripts

Create custom collection scripts by copying the template pattern:

```python
from redditharbor_setup import setup_redditharbor

pipeline = setup_redditharbor()
if pipeline:
    pipeline.subreddit_submission(
        subreddits=["your-target-subreddits"],
        sort_types=["hot", "top"],
        limit=100,
        mask_pii=True
    )
```

## 📈 Monitoring and Scaling

- Monitor API usage in your Reddit developer dashboard
- Adjust collection limits based on your needs
- Use PII anonymization for all research projects
- Regular backups recommended for important data

## 🆘 Troubleshooting

### Common Issues

1. **Docker not running**: Start Docker service
2. **Port conflicts**: Stop other Supabase projects
3. **API limits**: Reddit has rate limits - built-in handling
4. **Credential errors**: Verify Reddit API setup

### Getting Help

- RedditHarbor Documentation: https://socius-org.github.io/RedditHarbor/
- Reddit API Documentation: https://www.reddit.com/wiki/api/
- Supabase Documentation: https://supabase.com/docs

## 🎯 Next Steps

1. ✅ Configure Reddit API credentials
2. ✅ Test with sample data collection
3. ✅ Explore project templates
4. ✅ Customize for your specific research needs
5. ✅ Set up regular data collection schedules
6. ✅ Integrate with your analysis workflows