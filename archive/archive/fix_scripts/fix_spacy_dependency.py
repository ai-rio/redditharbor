#!/usr/bin/env .venv/bin/python
"""
RedditHarbor SpaCy Dependency Fix
Automatically install the en_core_web_lg model and re-enable PII anonymization
"""

import os
import subprocess
import sys


def fix_spacy_dependency():
    """Fix the spaCy dependency issue by installing the model and updating config"""
    print("🔧 RedditHarbor SpaCy Dependency Fix")
    print("=" * 40)
    print("This script will:")
    print("1. Install updated requirements with spaCy model")
    print("2. Verify spaCy model installation")
    print("3. Re-enable PII anonymization")
    print("4. Test the research functionality")
    print()

    try:
        # Step 1: Install updated requirements
        print("📦 Step 1: Installing updated requirements...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Requirements installed successfully")
        else:
            print(f"❌ Error installing requirements: {result.stderr}")
            return False

        # Step 2: Verify spaCy model installation
        print("\n🔍 Step 2: Verifying spaCy model installation...")
        try:
            import spacy
            nlp = spacy.load("en_core_web_lg")
            print("✅ en_core_web_lg model loaded successfully")
        except Exception as e:
            print(f"❌ Error loading spaCy model: {e}")
            print("🔄 Attempting manual download...")

            # Fallback: Try manual download
            result = subprocess.run([
                sys.executable, "-m", "spacy", "download", "en_core_web_lg"
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Manual download successful")
            else:
                print(f"❌ Manual download failed: {result.stderr}")
                return False

        # Step 3: Re-enable PII anonymization
        print("\n⚙️ Step 3: Re-enabling PII anonymization...")
        config_file = "config/settings.py"

        if os.path.exists(config_file):
            with open(config_file) as f:
                content = f.read()

            # Update PII setting
            if "ENABLE_PII_ANONYMIZATION = False" in content:
                content = content.replace(
                    "ENABLE_PII_ANONYMIZATION = False  # Temporarily disabled for research data collection",
                    "ENABLE_PII_ANONYMIZATION = True   # Re-enabled for production use"
                )

                with open(config_file, 'w') as f:
                    f.write(content)

                print("✅ PII anonymization re-enabled in config")
            else:
                print("⚠️ PII anonymization setting already enabled")
        else:
            print(f"❌ Config file not found: {config_file}")
            return False

        # Step 4: Test spaCy functionality
        print("\n🧪 Step 4: Testing spaCy PII functionality...")
        try:
            # Add project root to path
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

            from redditharbor.dock.pipeline import collect


            # Initialize PII tools
            test_pipeline = collect.__new__(collect)
            test_pipeline._initialize_pii_tools()

            print("✅ PII anonymization system initialized successfully")
        except Exception as e:
            print(f"❌ Error testing PII system: {e}")
            return False

        print("\n🎉 SpaCy dependency fix completed successfully!")
        print("📋 Next steps:")
        print("   1. Run the research: python scripts/run_niche_research.py")
        print("   2. Monitor for any remaining issues")
        print("   3. Analyze the collected data")

        return True

    except Exception as e:
        print(f"❌ Unexpected error during fix: {e}")
        return False

if __name__ == "__main__":
    success = fix_spacy_dependency()
    sys.exit(0 if success else 1)
