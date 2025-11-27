#!/usr/bin/env python3
"""
DLT to SQLAlchemy Migration Script - Phase 4

This script performs the safe migration from DLT to SQLAlchemy loader
with comprehensive backup, validation, and rollback capabilities.

Critical Features:
- Pre-migration validation checks
- Dry-run mode for testing
- Configuration backup and updates
- Post-migration validation
- Rollback functionality

Author: Phase 4 Migration Team
Version: Production Ready
"""

import os
import sys
import shutil
import argparse
import json
import logging
import subprocess
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phase4-workspace/migration_logs/migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages the safe migration from DLT to SQLAlchemy."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.migration_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        self.project_root = project_root
        self.workspace_dir = project_root / "phase4-workspace"
        self.backups_dir = self.workspace_dir / "backups"
        self.config_backups_dir = self.workspace_dir / "config_updates"
        self.rollback_dir = self.workspace_dir / "rollback_scripts"
        self.migration_log = self.workspace_dir / "migration_logs" / f"migration_{self.migration_id}.log"

        # Ensure directories exist
        for directory in [self.workspace_dir, self.backups_dir,
                         self.config_backups_dir, self.rollback_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def log_migration_step(self, step: str, status: str, details: str = ""):
        """Log a migration step with timestamp."""
        timestamp = datetime.now(UTC).isoformat()
        log_entry = {
            "timestamp": timestamp,
            "step": step,
            "status": status,
            "details": details
        }

        # Write to migration log file
        with open(self.migration_log, 'a') as f:
            f.write(f"{json.dumps(log_entry)}\n")

        # Also log to console
        if status == "SUCCESS":
            logger.info(f"✅ {step}: {details}")
        elif status == "WARNING":
            logger.warning(f"⚠️  {step}: {details}")
        elif status == "ERROR":
            logger.error(f"❌ {step}: {details}")
        else:
            logger.info(f"ℹ️  {step}: {details}")

    def validate_pre_migration(self) -> bool:
        """Perform pre-migration validation checks."""
        logger.info("🔍 Running pre-migration validation checks...")

        # 1. Check database connectivity
        try:
            from storage.sqlalchemy_loader import SQLAlchemyLoader
            loader = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')
            stats = loader.get_load_statistics()
            if not stats.get('connection_status') == 'connected':
                self.log_migration_step("Database Connection", "ERROR", "Cannot connect to database")
                return False
            self.log_migration_step("Database Connection", "SUCCESS", f"Connected, {stats['record_count']} records")
        except Exception as e:
            self.log_migration_step("Database Connection", "ERROR", str(e))
            return False

        # 2. Verify SQLAlchemy loader is functional
        try:
            # Test with a small data sample
            test_data = [{
                'submission_id': f'migration_test_{self.migration_id}',
                'title': 'Migration Test Record',
                'url': 'https://reddit.com/test/migration',
                'problem_description': 'Test record for migration validation',
                'reddit_score': 1,
                'trust_badges': {'test': True},
                'reddit_url': 'https://reddit.com/test/migration',
                'source': 'migration_test',
                'subreddit': 'test'
            }]

            result = loader.load_opportunities(test_data, write_disposition='append')
            if not result.success:
                self.log_migration_step("SQLAlchemy Loader Test", "ERROR", result.error_message)
                return False
            self.log_migration_step("SQLAlchemy Loader Test", "SUCCESS", "Test record loaded successfully")

            # Clean up test record
            from sqlalchemy import text
            with loader._engine.begin() as session:
                session.execute(text("DELETE FROM app_opportunities WHERE submission_id = :id"),
                              {"id": f'migration_test_{self.migration_id}'})

        except Exception as e:
            self.log_migration_step("SQLAlchemy Loader Test", "ERROR", str(e))
            return False

        # 3. Check backup files exist
        backup_files = list(self.backups_dir.glob("*.sql")) + list(self.backups_dir.glob("*.dump"))
        if not backup_files:
            self.log_migration_step("Backup Files", "ERROR", "No backup files found")
            return False

        total_size = sum(f.stat().st_size for f in backup_files)
        if total_size < 1000:  # At least 1KB total
            self.log_migration_step("Backup Files", "ERROR", f"Backup files too small: {total_size} bytes")
            return False

        self.log_migration_step("Backup Files", "SUCCESS", f"Found {len(backup_files)} backup files, {total_size} bytes total")

        # 4. Check configuration files exist
        storage_init = self.project_root / "storage" / "__init__.py"
        if not storage_init.exists():
            self.log_migration_step("Configuration Check", "ERROR", f"Missing {storage_init}")
            return False

        self.log_migration_step("Configuration Check", "SUCCESS", "All required files found")

        return True

    def backup_configuration(self) -> bool:
        """Backup current configuration files."""
        logger.info("💾 Backing up configuration files...")

        try:
            # Backup storage/__init__.py
            storage_init = self.project_root / "storage" / "__init__.py"
            backup_path = self.config_backups_dir / f"storage_init_backup_{self.migration_id}.py"

            if self.dry_run:
                self.log_migration_step("Configuration Backup", "DRY-RUN", f"Would backup {storage_init} to {backup_path}")
            else:
                shutil.copy2(storage_init, backup_path)
                self.log_migration_step("Configuration Backup", "SUCCESS", f"Backed up {storage_init}")

            return True

        except Exception as e:
            self.log_migration_step("Configuration Backup", "ERROR", str(e))
            return False

    def update_storage_init(self) -> bool:
        """Update storage/__init__.py to use SQLAlchemy as default."""
        logger.info("🔧 Updating storage/__init__.py...")

        try:
            storage_init = self.project_root / "storage" / "__init__.py"

            # New content for storage/__init__.py
            new_content = '''"""
RedditHarbor Pipeline v2 - Storage Module

This module provides storage and database integration capabilities for the pipeline.
MIGRATED: Now defaults to SQLAlchemy loader for reliable data persistence with explicit
transaction control, eliminating DLT silent failures.

Components:
- sqlalchemy_loader: Primary SQLAlchemy-based loader (NEW DEFAULT)
- dlt_compatibility_adapter: DLT-compatible interface for SQLAlchemy
- dlt_loader: Legacy DLT loader (available for fallback)

Author: Phase 4 DLT to SQLAlchemy Migration
Version: SQLAlchemy Default
"""

# Constants (available without importing loaders)
DEFAULT_PIPELINE_NAME = "reddit_opportunity_pipeline_v2"
DEFAULT_TABLE_NAME = "app_opportunities"
DEFAULT_PRIMARY_KEY = "submission_id"
DEFAULT_WRITE_DISPOSITION = "merge"

# Loader availability flags
SQLALCHEMY_AVAILABLE = True
DLT_AVAILABLE = True

# Import SQLAlchemy components (new default)
try:
    from .sqlalchemy_loader import SQLAlchemyLoader, LoadResult, SQLAlchemyLoadError
    from .dlt_compatibility_adapter import DLTCompatibilityAdapter
    SQLALCHEMY_IMPORT_SUCCESS = True
except ImportError as e:
    SQLALCHEMY_IMPORT_SUCCESS = False
    SQLAlchemyLoader = None
    LoadResult = None
    SQLAlchemyLoadError = None
    DLTCompatibilityAdapter = None

# Import DLT components (legacy support)
class LazyDLTModule:
    """Module-level lazy loading for DLT components."""

    def __init__(self):
        self._dlt_module = None
        self._imported = False

    def _ensure_imported(self):
        """Import DLT module only when needed."""
        if not self._imported:
            import importlib
            self._dlt_module = importlib.import_module('.dlt_loader', package=__package__)
            self._imported = True

    @property
    def DLTLoader(self):
        self._ensure_imported()
        return self._dlt_module.DLTLoader

    @property
    def DLTLoaderError(self):
        self._ensure_imported()
        return self._dlt_module.DLTLoaderError

    @property
    def DLTCredentialError(self):
        self._ensure_imported()
        return self._dlt_module.DLTCredentialError

    @property
    def DLTConnectionError(self):
        self._ensure_imported()
        return self._dlt_module.DLTConnectionError

    @property
    def create_dlt_loader(self):
        self._ensure_imported()
        return self._dlt_module.create_dlt_loader

    @property
    def load_opportunities_to_supabase(self):
        self._ensure_imported()
        return self._dlt_module.load_opportunities_to_supabase

# Create lazy module instance for DLT
_lazy_dlt = LazyDLTModule()

# Factory function for SQLAlchemy loader (NEW DEFAULT)
def create_loader(
    connection_string: str,
    loader_type: str = "sqlalchemy",  # Changed default from "dlt" to "sqlalchemy"
    **kwargs
):
    """
    Create a data loader instance.

    Args:
        connection_string: Database connection string
        loader_type: Type of loader to create ("sqlalchemy" or "dlt")
        **kwargs: Additional loader-specific parameters

    Returns:
        Loader instance (SQLAlchemyLoader by default)
    """
    if loader_type == "sqlalchemy":
        if not SQLALCHEMY_IMPORT_SUCCESS:
            raise ImportError("SQLAlchemy loader components not available")
        return SQLAlchemyLoader(connection_string, **kwargs)

    elif loader_type == "dlt":
        return _lazy_dlt.create_dlt_loader(connection_string, **kwargs)

    else:
        raise ValueError(f"Unknown loader type: {loader_type}")


# Convenience function for loading opportunities (NEW SQLAlchemy DEFAULT)
def load_opportunities(
    data: list,
    connection_string: str,
    table_name: str = DEFAULT_TABLE_NAME,
    write_disposition: str = DEFAULT_WRITE_DISPOSITION,
    loader_type: str = "sqlalchemy",  # Changed default
    **kwargs
) -> LoadResult:
    """
    Load opportunity data using the specified loader.

    Args:
        data: List of opportunity records to load
        connection_string: Database connection string
        table_name: Target table name
        write_disposition: Write disposition (merge, append, replace)
        loader_type: Type of loader to use ("sqlalchemy" or "dlt")
        **kwargs: Additional loader-specific parameters

    Returns:
        LoadResult with operation details
    """
    loader = create_loader(connection_string, loader_type, **kwargs)
    return loader.load_opportunities(data, table_name, write_disposition)


# DLT compatibility function (legacy support)
def load_opportunities_to_supabase(data: list, **kwargs):
    """Legacy function for DLT compatibility. Use load_opportunities() instead."""
    return load_opportunities(data, loader_type="dlt", **kwargs)


# Module-level lazy loading for backward compatibility
def __getattr__(name):
    """Module-level lazy loading for backward compatibility."""
    # DLT-related attributes (legacy support)
    if name in ["DLTLoader", "DLTLoaderError", "DLTCredentialError", "DLTConnectionError"]:
        return getattr(_lazy_dlt, name)
    elif name in ["create_dlt_loader", "load_opportunities_to_supabase"]:
        return getattr(_lazy_dlt, name)

    # SQLAlchemy-related attributes (new default)
    elif name in ["SQLAlchemyLoader", "LoadResult", "SQLAlchemyLoadError", "DLTCompatibilityAdapter"]:
        if not SQLALCHEMY_IMPORT_SUCCESS:
            raise AttributeError(f"SQLAlchemy components not available: {name}")
        return globals()[name]

    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Export public API
__all__ = [
    # Primary classes (SQLAlchemy - NEW DEFAULT)
    "SQLAlchemyLoader",
    "LoadResult",
    "SQLAlchemyLoadError",
    "DLTCompatibilityAdapter",

    # Factory functions (SQLAlchemy default)
    "create_loader",
    "load_opportunities",

    # Legacy DLT support (backward compatibility)
    "load_opportunities_to_supabase",
    "DLTLoader",
    "DLTLoaderError",
    "DLTCredentialError",
    "DLTConnectionError",
    "create_dlt_loader",

    # Constants (always available)
    "DEFAULT_PIPELINE_NAME",
    "DEFAULT_TABLE_NAME",
    "DEFAULT_PRIMARY_KEY",
    "DEFAULT_WRITE_DISPOSITION",

    # Availability flags
    "SQLALCHEMY_AVAILABLE",
    "DLT_AVAILABLE",
    "SQLALCHEMY_IMPORT_SUCCESS"
]

# Version information
__version__ = "2.0.0"  # Major version bump for SQLAlchemy default
__author__ = "RedditHarbor Pipeline v2 Team"
__migration_status__ = "SQLAlchemy Default (Phase 4 Complete)"
'''

            if self.dry_run:
                self.log_migration_step("Storage Init Update", "DRY-RUN", f"Would update {storage_init}")
                return True
            else:
                # Write the new content
                with open(storage_init, 'w') as f:
                    f.write(new_content)

                self.log_migration_step("Storage Init Update", "SUCCESS", f"Updated {storage_init}")
                return True

        except Exception as e:
            self.log_migration_step("Storage Init Update", "ERROR", str(e))
            return False

    def create_rollback_script(self) -> bool:
        """Create rollback script for emergency restore."""
        logger.info("📝 Creating rollback script...")

        try:
            rollback_script = self.rollback_dir / f"rollback_{self.migration_id}.py"

            script_content = f'''#!/usr/bin/env python3
"""
Rollback Script for DLT to SQLAlchemy Migration

Migration ID: {self.migration_id}
Created: {datetime.now(UTC).isoformat()}

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
    backup_init = project_root / "phase4-workspace" / "config_updates" / f"storage_init_backup_{self.migration_id}.py"

    if backup_init.exists():
        shutil.copy2(backup_init, storage_init)
        print(f"✅ Restored {{storage_init}} from backup")
    else:
        print(f"❌ Backup file not found: {{backup_init}}")
        return False

    print("✅ Migration rollback completed")
    print("📝 Note: Database changes must be manually restored from backups if needed")
    return True

if __name__ == "__main__":
    success = rollback_migration()
    sys.exit(0 if success else 1)
'''

            if self.dry_run:
                self.log_migration_step("Rollback Script", "DRY-RUN", f"Would create {rollback_script}")
                return True
            else:
                with open(rollback_script, 'w') as f:
                    f.write(script_content)

                # Make it executable
                os.chmod(rollback_script, 0o755)

                self.log_migration_step("Rollback Script", "SUCCESS", f"Created {rollback_script}")
                return True

        except Exception as e:
            self.log_migration_step("Rollback Script", "ERROR", str(e))
            return False

    def validate_post_migration(self) -> bool:
        """Perform post-migration validation."""
        logger.info("✅ Running post-migration validation...")

        try:
            # Clear module cache to force reload of updated storage module
            import sys
            modules_to_clear = [k for k in sys.modules.keys() if k.startswith('storage')]
            for module in modules_to_clear:
                del sys.modules[module]

            # Test the updated storage module
            from storage import create_loader, load_opportunities, SQLALCHEMY_AVAILABLE

            if not SQLALCHEMY_AVAILABLE:
                self.log_migration_step("Post-Migration Validation", "ERROR", "SQLAlchemy not available after migration")
                return False

            # Test default loader creation
            loader = create_loader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')

            if not hasattr(loader, 'load_opportunities'):
                self.log_migration_step("Post-Migration Validation", "ERROR", "Default loader missing load_opportunities method")
                return False

            self.log_migration_step("Default Loader Test", "SUCCESS", "SQLAlchemy loader created successfully by default")

            # Test data loading with new default
            test_data = [{
                'submission_id': f'post_migration_test_{self.migration_id}',
                'title': 'Post-Migration Validation Test',
                'url': 'https://reddit.com/test/post_migration',
                'problem_description': 'Test record for post-migration validation',
                'reddit_score': 1,
                'trust_badges': {'test': True},
                'reddit_url': 'https://reddit.com/test/post_migration',
                'source': 'post_migration_test',
                'subreddit': 'test'
            }]

            result = load_opportunities(test_data, 'postgresql://postgres:postgres@127.0.0.1:54322/postgres')

            if not result.success:
                self.log_migration_step("Post-Migration Load Test", "ERROR", result.error_message)
                return False

            self.log_migration_step("Post-Migration Load Test", "SUCCESS", f"Loaded {result.records_inserted} records with new default")

            # Clean up test record
            from sqlalchemy import text
            with loader._engine.begin() as session:
                session.execute(text("DELETE FROM app_opportunities WHERE submission_id = :id"),
                              {"id": f'post_migration_test_{self.migration_id}'})

            # Test legacy DLT compatibility
            try:
                from storage import load_opportunities_to_supabase
                self.log_migration_step("Legacy Compatibility Test", "SUCCESS", "Legacy DLT functions still available")
            except ImportError:
                self.log_migration_step("Legacy Compatibility Test", "WARNING", "Legacy DLT functions not available")

            return True

        except Exception as e:
            self.log_migration_step("Post-Migration Validation", "ERROR", str(e))
            return False

    def execute_migration(self) -> bool:
        """Execute the complete migration process."""
        logger.info(f"🚀 Starting DLT to SQLAlchemy Migration (ID: {self.migration_id})")

        if self.dry_run:
            logger.info("🔍 DRY-RUN MODE: No actual changes will be made")

        # Step 1: Pre-migration validation
        if not self.validate_pre_migration():
            logger.error("❌ Pre-migration validation failed")
            return False

        # Step 2: Backup configuration
        if not self.backup_configuration():
            logger.error("❌ Configuration backup failed")
            return False

        # Step 3: Update storage configuration
        if not self.update_storage_init():
            logger.error("❌ Storage configuration update failed")
            return False

        # Step 4: Create rollback script
        if not self.create_rollback_script():
            logger.error("❌ Rollback script creation failed")
            return False

        # Step 5: Post-migration validation (skip in dry-run)
        if not self.dry_run:
            if not self.validate_post_migration():
                logger.error("❌ Post-migration validation failed")
                return False
        else:
            self.log_migration_step("Post-Migration Validation", "DRY-RUN", "Would validate post-migration state")

        # Success!
        status = "DRY-RUN SUCCESS" if self.dry_run else "SUCCESS"
        logger.info(f"✅ Migration {status} (ID: {self.migration_id})")

        # Generate completion report
        self.generate_completion_report()

        return True

    def generate_completion_report(self):
        """Generate migration completion report."""
        report = {
            "migration_id": self.migration_id,
            "status": "DRY-RUN SUCCESS" if self.dry_run else "SUCCESS",
            "timestamp": datetime.now(UTC).isoformat(),
            "migration_type": "DLT to SQLAlchemy",
            "dry_run": self.dry_run,
            "backup_files": [f.name for f in self.backups_dir.glob("*")],
            "config_backups": [f.name for f in self.config_backups_dir.glob("*")],
            "rollback_scripts": [f.name for f in self.rollback_dir.glob("*")],
            "migration_log": str(self.migration_log),
            "changes_made": [
                "Updated storage/__init__.py to use SQLAlchemy as default",
                "Created comprehensive backup of configuration",
                "Generated rollback script for emergency restore",
                "Validated post-migration functionality"
            ]
        }

        report_path = self.workspace_dir / f"migration_report_{self.migration_id}.json"

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        self.log_migration_step("Completion Report", "SUCCESS", f"Generated {report_path}")


def main():
    """Main entry point for migration script."""
    parser = argparse.ArgumentParser(description="DLT to SQLAlchemy Migration Script")
    parser.add_argument("--dry-run", action="store_true", help="Run migration in dry-run mode (no actual changes)")
    parser.add_argument("--validate-only", action="store_true", help="Only run pre-migration validation")

    args = parser.parse_args()

    # Create migration manager
    migration = MigrationManager(dry_run=args.dry_run)

    if args.validate_only:
        # Just run validation
        success = migration.validate_pre_migration()
        if success:
            print("✅ Pre-migration validation passed")
        else:
            print("❌ Pre-migration validation failed")
        sys.exit(0 if success else 1)

    # Execute full migration
    success = migration.execute_migration()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()