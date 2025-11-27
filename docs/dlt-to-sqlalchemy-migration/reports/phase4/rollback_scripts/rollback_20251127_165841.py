#!/usr/bin/env python3
"""
Rollback Script for DLT to SQLAlchemy Migration

Migration ID: 20251127_165841
Created: 2025-11-27T16:58:44.581990+00:00

Use this script to rollback the SQLAlchemy migration if needed.
"""

import os
import sys
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def rollback_migration():
    """Rollback the SQLAlchemy migration."""
    print("🔄 Rolling back DLT to SQLAlchemy migration...")

    # Restore original storage/__init__.py
    storage_init = project_root / "storage" / "__init__.py"
    backup_init = project_root / "phase4-workspace" / "config_updates" / f"storage_init_backup_20251127_165841.py"

    if backup_init.exists():
        shutil.copy2(backup_init, storage_init)
        print(f"✅ Restored {storage_init} from backup")
    else:
        print(f"❌ Backup file not found: {backup_init}")
        return False

    print("✅ Migration rollback completed")
    print("📝 Note: Database changes must be manually restored from backups if needed")
    return True

if __name__ == "__main__":
    success = rollback_migration()
    sys.exit(0 if success else 1)
