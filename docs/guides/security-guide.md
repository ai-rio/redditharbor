# RedditHarbor .gitignore Protection Guide

This document explains what your comprehensive `.gitignore` file protects and why each category is important for research projects dealing with social media data.

## 🔒 **CRITICAL SECURITY PROTECTIONS**

### **Credentials & API Keys**
```
.env, .env.local, config.py, secrets.py, *_key.*, *_secret.*
```
**Why Protected:** These files contain your Reddit API credentials and Supabase keys. Committing them would:
- Expose your API keys to anyone with repository access
- Allow unauthorized use of your Reddit API quota
- Compromise your database security
- Violate Reddit's Terms of Service

### **Research Data & Personal Information**
```
*.json, *.csv, data/, datasets/, research_data/, raw_data/
```
**Why Protected:** Reddit data contains potentially sensitive user information:
- Usernames and profile information
- Personal content shared in discussions
- Potentially identifying information in post content
- Research subject privacy must be protected

## 🛡️ **SYSTEM & ENVIRONMENT PROTECTIONS**

### **Virtual Environments**
```
.venv/, venv/, env/, pip-log.txt, .coverage/
```
**Why Protected:**
- Virtual environments are large (100MB+) and unnecessary in version control
- They contain absolute paths specific to your machine
- Can be easily regenerated from requirements.txt
- Different developers need different environment configurations

### **Database Files**
```
*.db, *.sqlite, supabase/.temp/, *.backup
```
**Why Protected:**
- Database files contain your collected Reddit research data
- They can be very large and change frequently
- May contain sensitive user information
- Should be backed up separately, not tracked in git

## 💻 **DEVELOPMENT PROTECTIONS**

### **IDE & Editor Files**
```
.vscode/, .idea/, *.swp, *.swo, .DS_Store
```
**Why Protected:**
- Personal editor preferences and configurations
- Large binary cache files
- Machine-specific settings
- Temporary editing files

### **Logs & Temporary Files**
```
*.log, logs/, tmp/, temp/, cache/
```
**Why Protected:**
- Log files can contain sensitive information
- Temporary files are by nature not needed long-term
- Cache files change frequently and bloat repository
- Debug logs may contain API responses or user data

## 📊 **RESEARCH-SPECIFIC PROTECTIONS**

### **Analysis Results & Exports**
```
exports/, analysis_results/, findings/, *.pkl, *.parquet
```
**Why Protected:**
- Research results may contain sensitive user data
- Large analysis files don't belong in version control
- Research findings should be published separately
- Intermediate analysis artifacts are not necessary for collaboration

### **Generated Documentation**
```
docs/_build/, site/, *.pdf
```
**Why Protected:**
- Generated documentation can be recreated from source
- Large PDF files and build artifacts
- Documentation builds should be part of deployment, not repository

## 🚀 **BEST PRACTICES FOR YOUR REDDITHARBOR PROJECT**

### **What SHOULD Be in Git:**
✅ Source code (Python scripts, configuration templates)
✅ Documentation (README files, setup guides)
✅ Empty directory structure
✅ Requirements and dependency files
✅ Research methodology documentation
✅ Data processing scripts (without actual data)

### **What SHOULD NOT Be in Git:**
❌ API credentials and secret keys
❌ Collected Reddit data
❌ Virtual environments
❌ Database files
❌ Analysis results with sensitive data
❌ Logs and temporary files
❌ User-generated content

## 🔧 **HOW TO USE THIS PROTECTION**

### **1. For Personal Development:**
```bash
# This .gitignore is already configured correctly
git add .
git commit -m "Initial RedditHarbor setup with comprehensive security"
```

### **2. For Collaboration:**
```bash
# Share this project safely with other researchers
# They'll need to:
# 1. Clone the repository
# 2. Create their own .env file with their API credentials
# 3. Set up their own virtual environment
# 4. Collect their own research data
```

### **3. For Publishing Research:**
```bash
# When sharing research findings:
# 1. Export aggregated/anonymized data
# 2. Create separate data distribution
# 3. Publish methodology and results separately
# 4. Never include raw Reddit data in public repositories
```

## 📋 **SECURITY CHECKLIST**

Before committing, ensure these are properly protected:

- [ ] `.env` file exists in .gitignore and contains all API keys
- [ ] No credentials hardcoded in Python files
- [ ] Database connection strings use environment variables
- [ ] No raw Reddit data in the repository
- [ ] Virtual environment directory is ignored
- [ ] Log files and temporary files are excluded
- [ ] Large analysis files are not tracked

## ⚠️ **SPECIAL CONSIDERATIONS FOR SOCIAL MEDIA RESEARCH**

### **IRB Compliance:**
This .gitignore helps maintain IRB (Institutional Review Board) compliance by:
- Protecting research subject privacy
- Preventing accidental data exposure
- Maintaining data collection transparency
- Ensuring proper data handling procedures

### **Reddit Terms of Service:**
The protection helps comply with Reddit's ToS by:
- Preventing redistribution of user content
- Protecting user privacy and identity
- Ensuring data is used only for approved research
- Maintaining proper data handling procedures

### **Research Ethics:**
This setup supports ethical research practices by:
- Defaulting to privacy protection
- Preventing accidental data leaks
- Ensuring proper consent handling
- Supporting anonymization workflows

## 🔍 **TROUBLESHOOTING**

### **If git keeps tracking files that should be ignored:**
```bash
# Remove already tracked files
git rm --cached filename
git rm --cached -r directory/

# Update git index
git add .
git commit -m "Remove sensitive files from tracking"
```

### **If you accidentally committed credentials:**
```bash
# Immediately change your API keys
# Remove the file from repository history
git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch .env' HEAD
# Rotate all exposed credentials
```

### **If you need to share configuration:**
```bash
# Create example configuration file
cp .env.example .env
# Add .env to .gitignore (already done)
# Share .env.example instead of actual .env
```

---

**Remember:** This .gitignore protects both your security and your research subjects' privacy. When in doubt, add a pattern to exclude rather than risk exposing sensitive information.