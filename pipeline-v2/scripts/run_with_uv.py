#!/usr/bin/env python3
"""
UV Environment Wrapper for Pipeline v2
Ensures pipeline runs with correct UV-managed dependencies
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run pipeline using UV to manage dependencies"""

    # Get project root (parent of pipeline-v2)
    script_dir = Path(__file__).parent
    pipeline_dir = script_dir.parent
    project_root = pipeline_dir.parent

    # Path to main.py
    main_script = pipeline_dir / "main.py"

    if not main_script.exists():
        print(f"❌ Error: main.py not found at {main_script}")
        sys.exit(1)

    # Build UV command with --no-sync to use existing environment
    cmd = [
        "uv", "run",
        "--no-sync",  # Don't sync dependencies, use what's installed
        "--directory", str(project_root),
        "python", str(main_script)
    ]

    # Add all command-line arguments
    cmd.extend(sys.argv[1:])

    print("🚀 Running Pipeline v2 with UV-managed environment")
    print(f"📂 Project root: {project_root}")
    print(f"🐍 Python script: {main_script}")
    print(f"⚙️  Command: {' '.join(cmd)}")
    print("=" * 60)
    print()

    # Execute with UV
    try:
        result = subprocess.run(cmd, cwd=project_root)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error running pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
