#!/usr/bin/env python3
"""
Debug script to understand import issues between pytest and standalone execution
"""
import sys
import os

print("=== IMPORT DEBUG ===")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")

# Try to import SQLAlchemy
print("\n=== SQLALCHEMY IMPORT TEST ===")
try:
    from sqlalchemy import create_engine, text
    import sqlalchemy
    print("✅ SQLAlchemy import successful")
    print(f"SQLAlchemy version: {sqlalchemy.__version__}")
except ImportError as e:
    print(f"❌ SQLAlchemy import failed: {e}")

# Check site-packages
print("\n=== SITE PACKAGES CHECK ===")
site_packages = [
    '/home/carlos/projects/redditharbor-core-functions-fix/.venv/lib/python3.12/site-packages',
    '/usr/lib/python3.12/site-packages',
    '/usr/local/lib/python3.12/site-packages'
]

for site in site_packages:
    if os.path.exists(site):
        sqlalchemy_path = os.path.join(site, 'sqlalchemy')
        if os.path.exists(sqlalchemy_path):
            print(f"✅ SQLAlchemy found in: {site}")
        else:
            print(f"❌ SQLAlchemy NOT found in: {site}")
    else:
        print(f"❌ Path does not exist: {site}")

# Test in current directory context
print("\n=== CURRENT CONTEXT IMPORT ===")
try:
    import sqlalchemy
    print(f"✅ SQLAlchemy imported from: {sqlalchemy.__file__}")
    print(f"   Version: {sqlalchemy.__version__}")
except ImportError as e:
    print(f"❌ SQLAlchemy import failed in current context: {e}")

# Test with manual path addition (same as debug scripts)
print("\n=== MANUAL PATH ADDITION TEST ===")
sys.path.insert(0, '/home/carlos/projects/redditharbor-core-functions-fix/.venv/lib/python3.12/site-packages')
try:
    from sqlalchemy import create_engine, text
    print("✅ SQLAlchemy import successful after manual path addition")
except ImportError as e:
    print(f"❌ SQLAlchemy import still failed: {e}")

# Test our loader import
print("\n=== SQLALCHEMY LOADER IMPORT TEST ===")
sys.path.insert(0, os.path.dirname(__file__))
try:
    from storage.sqlalchemy_loader import SQLAlchemyLoader
    print("✅ SQLAlchemyLoader import successful")

    # Try to create loader
    try:
        loader = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')
        print("✅ SQLAlchemyLoader creation successful")
    except Exception as e:
        print(f"❌ SQLAlchemyLoader creation failed: {e}")

except ImportError as e:
    print(f"❌ SQLAlchemyLoader import failed: {e}")

# Check pytest environment variables
print("\n=== PYTEST ENVIRONMENT CHECK ===")
pytest_vars = {k: v for k, v in os.environ.items() if 'PYTEST' in k.upper() or 'PYTHONPATH' in k.upper()}
print(f"Pytest-related environment variables: {pytest_vars}")