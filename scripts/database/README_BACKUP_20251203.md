# RedditHarbor Database Backup Documentation

**Generated:** 2025-12-03 19:01:41
**Database:** reddit_harbor (localhost:54322)
**Purpose:** Complete database backup and restoration procedures

## 📁 Backup Files Created

### 1. Schema Backup
- **File:** `schema_20251203_190141.sql`
- **Size:** ~45KB
- **Contents:** Complete database structure (tables, indexes, constraints)
- **Purpose:** Recreate database schema without data

### 2. Complete Backup Script
- **File:** `complete_backup_20251203_190141.sh`
- **Executable:** ✅
- **Purpose:** Automated full database backup with reporting
- **Features:** Schema, data, key tables, compression, cleanup

### 3. Database Structure Dump
- **File:** `backup_schema_20251203_190141.sql`
- **Contents:** PostgreSQL dump commands for schema extraction

## 🗄️ Database Overview

### **Total Tables:** 27
- **Public Schema:** 10 tables (core RedditHarbor data)
- **Auth Schema:** 13 tables (Supabase authentication)
- **Storage Schema:** 7 tables (file storage system)

### **Key Tables by Size:**
1. `app_opportunities_backup_20251127_154500` - 536KB
2. `opportunities` - 224KB
3. `submissions` - 96KB
4. `users` - 96KB
5. `objects` - 64KB

### **Data Volume Analysis:**
- **Current state:** Most tables appear to be empty (0 live rows)
- **Exceptions:** Backup table contains historical opportunity data
- **Total estimated size:** ~1.2MB (excluding indexes)

## 🚀 Usage Instructions

### **Run Complete Backup:**
```bash
cd /home/carlos/projects/redditharbor-core-functions-fix/scripts/database
./complete_backup_20251203_190141.sh
```

### **Manual Backup Options:**

#### Schema Only:
```bash
pg_dump -h 127.0.0.1 -p 54322 -U postgres -d reddit_harbor \
  --schema=public --schema=auth --schema=storage \
  --schema-only --no-owner --no-privileges \
  --file=reddit_harbor_schema.sql
```

#### Data Only:
```bash
pg_dump -h 127.0.0.1 -p 54322 -U postgres -d reddit_harbor \
  --data-only --no-owner --no-privileges \
  --file=reddit_harbor_data.sql
```

#### Complete Compressed:
```bash
pg_dump -h 127.0.0.1 -p 54322 -U postgres -d reddit_harbor \
  --format=custom --compress=9 \
  --file=reddit_harbor_complete.dump
```

## 🔄 Restoration Procedures

### **Restore Schema Only:**
```bash
psql -h 127.0.0.1 -p 54322 -U postgres -d reddit_harbor < schema_20251203_190141.sql
```

### **Restore Data Only:**
```bash
psql -h 127.0.0.1 -p 54322 -U postgres -d reddit_harbor < reddit_harbor_data_20251203_190141.sql
```

### **Restore Complete Backup:**
```bash
pg_restore -h 127.0.0.1 -p 54322 -U postgres -d reddit_harbor reddit_harbor_complete_20251203_190141.dump
```

### **Restore to New Database:**
```bash
# Create new database
createdb -h 127.0.0.1 -p 54322 -U postgres reddit_harbor_restored

# Restore
pg_restore -h 127.0.0.1 -p 54322 -U postgres -d reddit_harbor_restored reddit_harbor_complete_20251203_190141.dump
```

## 📊 Backup Strategy Recommendations

### **Automated Backup Schedule:**
1. **Daily:** Schema + key tables backup
2. **Weekly:** Full database backup
3. **Monthly:** Archive to external storage

### **Backup Retention:**
- **Local:** Keep last 7 days
- **Weekly:** Keep last 4 weeks
- **Monthly:** Keep last 12 months

### **Critical Tables Priority:**
1. `opportunities` - Core opportunity data
2. `submissions` - Reddit submission data
3. `competitive_landscape` - Market analysis
4. `market_validations` - Validation results
5. `monetization_patterns` - Revenue models

## 🔧 Backup Script Features

### **Automated Script Capabilities:**
- ✅ Database connectivity check
- ✅ Size estimation and reporting
- ✅ Schema-only backup
- ✅ Data-only backup
- ✅ Key tables focused backup
- ✅ Complete compressed backup
- ✅ Automated cleanup (7-day retention)
- ✅ Comprehensive report generation
- ✅ Error handling and logging

### **Generated Reports Include:**
- Backup file locations and sizes
- Database statistics
- Table row counts
- Restoration commands
- Backup summary

## ⚠️ Important Notes

### **Database Characteristics:**
- **Empty Tables:** Most tables currently contain no data
- **Supabase Integration:** Heavy use of Supabase auth/storage schemas
- **Vector Extension:** Uses pgvector for embeddings
- **JSONB Fields:** Extensive use of JSON for flexible data storage

### **Backup Considerations:**
- **Exclusions:** Temporary tables and session data excluded from backups
- **Compression:** Full backups use gzip compression (level 9)
- **Privileges:** Backups exclude owner/privilege information for portability

### **Security:**
- **Local Access:** All backups use localhost connections
- **No Credentials:** Script assumes trusted connection
- **File Permissions:** Backup files inherit default umask

## 🎯 Next Steps

### **Immediate:**
1. Test restoration procedure on development database
2. Set up automated backup cron job
3. Configure external storage archiving

### **Long-term:**
1. Implement backup verification
2. Add point-in-time recovery capability
3. Set up monitoring and alerts

---

**Backup Location:** `/home/carlos/projects/redditharbor-core-functions-fix/scripts/database/`
**Contact:** Database Administrator
**Last Updated:** 2025-12-03 19:01:41