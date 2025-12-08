#!/usr/bin/env python3
"""
Install dependencies for Claude Code hooks
"""

import subprocess
import sys


def install_hook_dependencies():
    """Install required dependencies for hooks using uv."""
    dependencies = [
        'click>=8.0.0',
        'watchfiles>=0.20.0',
        'jsonschema>=4.0.0',
        'path>=2.0.0',
    ]

    try:
        # Use uv to install dependencies
        cmd = ['uv', 'add'] + dependencies
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Hook dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install hook dependencies: {e}")
        print(f"Stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ uv not found. Please install uv first.")
        return False

if __name__ == '__main__':
    success = install_hook_dependencies()
    sys.exit(0 if success else 1)
