#!/usr/bin/env python3
"""
Documentation Tests for RedditHarbor DLT Activity Validation

This module tests the existence, completeness, and quality of documentation
files for the DLT Activity Validation system.

Tests verify:
- Documentation files exist and are accessible
- README.md contains DLT Activity Validation sections
- Documentation structure follows project standards
- Content quality and completeness
- Cross-references and links are valid
"""

import os
import re
import sys
import unittest
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestDocumentation(unittest.TestCase):
    """Test suite for RedditHarbor documentation."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures with file paths."""
        cls.project_root = project_root
        cls.readme_path = cls.project_root / "README.md"
        cls.dlt_guide_path = cls.project_root / "docs" / "guides" / "dlt-activity-validation.md"
        cls.dlt_examples_path = cls.project_root / "docs" / "examples" / "dlt-collection-examples.md"
        cls.docs_readme_path = cls.project_root / "docs" / "README.md"

        # CueTimer brand colors for validation
        cls.brand_colors = {
            'primary': '#FF6B35',
            'secondary': '#004E89',
            'accent': '#F7B801'
        }

    def test_project_structure_exists(self):
        """Test that the project structure is correct."""
        required_dirs = [
            "docs",
            "docs/guides",
            "docs/examples",
            "tests",
            "core",
            "scripts",
            "config"
        ]

        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            self.assertTrue(
                full_path.exists() and full_path.is_dir(),
                f"Required directory {dir_path} does not exist"
            )

    def test_readme_exists(self):
        """Test that README.md exists and is readable."""
        self.assertTrue(
            self.readme_path.exists(),
            "README.md file does not exist"
        )

        self.assertGreater(
            self.readme_path.stat().st_size,
            5000,  # README should be substantial
            "README.md appears to be too small or empty"
        )

    def test_readme_contains_dlt_section(self):
        """Test that README.md contains DLT Activity Validation section."""
        readme_content = self.readme_path.read_text(encoding='utf-8')

        # Check for key DLT sections
        required_sections = [
            "DLT Activity Validation",
            "Multi-factor Activity Scoring",
            "DLT Activity Validation System Guide",
            "Practical DLT collection examples"
        ]

        for section in required_sections:
            self.assertIn(
                section,
                readme_content,
                f"README.md missing required section: {section}"
            )

    def test_readme_contains_dlt_quick_start(self):
        """Test that README.md contains DLT quick start examples."""
        readme_content = self.readme_path.read_text(encoding='utf-8')

        # Check for DLT quick start commands
        required_commands = [
            "run_dlt_activity_collection.py",
            "--subreddits",
            "--segment",
            "--min-activity",
            "--time-filter"
        ]

        for command in required_commands:
            self.assertIn(
                command,
                readme_content,
                f"README.md missing DLT command: {command}"
            )

    def test_readme_version_information(self):
        """Test that README.md contains version information for DLT."""
        readme_content = self.readme_path.read_text(encoding='utf-8')

        # Should mention v0.4 with DLT features
        self.assertIn(
            "v0.4",
            readme_content,
            "README.md should mention v0.4 with DLT features"
        )

        # Should mention DLT performance improvements
        self.assertIn(
            "50-300% faster",
            readme_content,
            "README.md should mention DLT performance improvements"
        )

    def test_dlt_guide_exists(self):
        """Test that DLT Activity Validation guide exists."""
        self.assertTrue(
            self.dlt_guide_path.exists(),
            "DLT Activity Validation guide does not exist"
        )

        # Check file size
        self.assertGreater(
            self.dlt_guide_path.stat().st_size,
            10000,  # Should be comprehensive
            "DLT guide appears to be too short"
        )

    def test_dlt_guide_content_quality(self):
        """Test DLT guide content quality and completeness."""
        guide_content = self.dlt_guide_path.read_text(encoding='utf-8')

        # Required sections for comprehensive guide
        required_sections = [
            "Overview",
            "Key Features",
            "Architecture",
            "Quick Start",
            "Activity Scoring System",
            "Configuration Options",
            "Collection Strategies",
            "Time Filtering",
            "Monitoring & Analytics",
            "Troubleshooting",
            "Migration Guide",
            "Best Practices"
        ]

        missing_sections = []
        for section in required_sections:
            if section not in guide_content:
                missing_sections.append(section)

        self.assertEqual(
            len(missing_sections),
            0,
            f"DLT guide missing required sections: {missing_sections}"
        )

    def test_dlt_guide_technical_details(self):
        """Test that DLT guide contains necessary technical details."""
        guide_content = self.dlt_guide_path.read_text(encoding='utf-8')

        # Technical requirements
        required_technical_content = [
            "Multi-factor Scoring",
            "Comments 40%",
            "Engagement 30%",
            "Posting frequency 20%",
            "Growth rate 10%",
            "Activity score",
            "Time filter",
            "Pipeline configuration"
        ]

        for content in required_technical_content:
            self.assertIn(
                content,
                guide_content,
                f"DLT guide missing technical content: {content}"
            )

    def test_dlt_examples_exists(self):
        """Test that DLT collection examples exist."""
        self.assertTrue(
            self.dlt_examples_path.exists(),
            "DLT collection examples file does not exist"
        )

        # Should be substantial with many examples
        self.assertGreater(
            self.dlt_examples_path.stat().st_size,
            15000,  # Should contain many examples
            "DLT examples file appears too short"
        )

    def test_dlt_examples_content(self):
        """Test DLT examples content quality and variety."""
        examples_content = self.dlt_examples_path.read_text(encoding='utf-8')

        # Should contain diverse example types
        required_example_types = [
            "Quick Start",
            "Research Scenarios",
            "Business Intelligence",
            "Academic Research",
            "High-Performance",
            "Trend Analysis",
            "Industry-Specific",
            "Scheduled Collections",
            "Advanced Patterns",
            "Troubleshooting"
        ]

        for example_type in required_example_types:
            self.assertIn(
                example_type,
                examples_content,
                f"DLT examples missing: {example_type}"
            )

    def test_dlt_examples_practical_content(self):
        """Test that DLT examples contain practical, copy-paste ready code."""
        examples_content = self.dlt_examples_path.read_text(encoding='utf-8')

        # Should contain practical command examples
        required_command_patterns = [
            r"python scripts/run_dlt_activity_collection\.py",
            r"--subreddits\s+",
            r"--segment\s+",
            r"--min-activity\s+\d+",
            r"--time-filter\s+\w+",
            r"--pipeline\s+"
        ]

        for pattern in required_command_patterns:
            self.assertTrue(
                re.search(pattern, examples_content),
                f"DLT examples missing command pattern: {pattern}"
            )

    def test_brand_colors_usage(self):
        """Test that documentation uses CueTimer brand colors."""
        # Check README for brand colors
        readme_content = self.readme_path.read_text(encoding='utf-8')

        # Should contain brand color codes
        self.assertIn(
            "#FF6B35",
            readme_content,
            "README.md should use CueTimer primary color (#FF6B35)"
        )

        # Check DLT guide for brand styling
        if self.dlt_guide_path.exists():
            guide_content = self.dlt_guide_path.read_text(encoding='utf-8')
            self.assertIn(
                "#FF6B35",
                guide_content,
                "DLT guide should use CueTimer primary color (#FF6B35)"
            )

    def test_documentation_cross_references(self):
        """Test that documentation contains proper cross-references."""
        readme_content = self.readme_path.read_text(encoding='utf-8')

        # Should reference the DLT guide and examples
        required_links = [
            "docs/guides/dlt-activity-validation.md",
            "docs/examples/dlt-collection-examples.md"
        ]

        for link in required_links:
            self.assertIn(
                link,
                readme_content,
                f"README.md should reference: {link}"
            )

    def test_code_block_quality(self):
        """Test that documentation contains properly formatted code blocks."""
        if self.dlt_examples_path.exists():
            examples_content = self.dlt_examples_path.read_text(encoding='utf-8')

            # Count code blocks
            bash_code_blocks = len(re.findall(r'```bash', examples_content))
            python_code_blocks = len(re.findall(r'```python', examples_content))

            # Should have substantial number of code blocks
            self.assertGreater(
                bash_code_blocks,
                10,
                "Should have at least 10 bash code block examples"
            )

            self.assertGreater(
                python_code_blocks,
                5,
                "Should have at least 5 python code block examples"
            )

    def test_documentation_structure(self):
        """Test that documentation follows project naming conventions."""

        # Files should use kebab-case
        doc_files = []
        for file_path in self.project_root.rglob("*.md"):
            if "docs" in str(file_path):
                doc_files.append(file_path.name)

        # Check for proper kebab-case naming
        invalid_names = []
        for filename in doc_files:
            if not filename.replace('.md', '').replace('_', '-').islower():
                invalid_names.append(filename)

        self.assertEqual(
            len(invalid_names),
            0,
            f"Documentation files should use kebab-case: {invalid_names}"
        )

    def test_dlt_script_exists(self):
        """Test that the DLT collection script exists."""
        dlt_script_path = self.project_root / "scripts" / "run_dlt_activity_collection.py"

        self.assertTrue(
            dlt_script_path.exists(),
            "DLT collection script does not exist"
        )

        # Should be substantial
        self.assertGreater(
            dlt_script_path.stat().st_size,
            5000,
            "DLT collection script appears too small"
        )

    def test_dlt_configuration_exists(self):
        """Test that DLT configuration files exist."""
        dlt_config_path = self.project_root / "config" / "dlt_settings.py"
        dlt_source_path = self.project_root / "core" / "dlt_reddit_source.py"

        self.assertTrue(
            dlt_config_path.exists(),
            "DLT settings configuration does not exist"
        )

        self.assertTrue(
            dlt_source_path.exists(),
            "DLT Reddit source does not exist"
        )

    def test_documentation_completeness_score(self):
        """Calculate and validate documentation completeness score."""
        score = 0
        max_score = 10

        # README.md with DLT section (2 points)
        if self.readme_path.exists():
            readme_content = self.readme_path.read_text(encoding='utf-8')
            if "DLT Activity Validation" in readme_content:
                score += 2

        # DLT guide exists and is comprehensive (3 points)
        if self.dlt_guide_path.exists():
            guide_content = self.dlt_guide_path.read_text(encoding='utf-8')
            if len(guide_content) > 10000 and "Quick Start" in guide_content:
                score += 3

        # DLT examples exist and are practical (3 points)
        if self.dlt_examples_path.exists():
            examples_content = self.dlt_examples_path.read_text(encoding='utf-8')
            if len(examples_content) > 15000 and "```bash" in examples_content:
                score += 3

        # Documentation structure and cross-references (2 points)
        if self.docs_readme_path.exists():
            docs_content = self.docs_readme_path.read_text(encoding='utf-8')
            if "dlt-activity-validation" in docs_content.lower():
                score += 2

        # Should have at least 80% completeness
        completeness_ratio = score / max_score
        self.assertGreater(
            completeness_ratio,
            0.8,
            f"Documentation completeness score: {completeness_ratio:.1%} (should be ≥80%)"
        )

    def test_file_permissions(self):
        """Test that documentation files have appropriate permissions."""
        doc_files = [
            self.readme_path,
            self.dlt_guide_path,
            self.dlt_examples_path,
            self.docs_readme_path
        ]

        for file_path in doc_files:
            if file_path.exists():
                stat = file_path.stat()
                # Should be readable by owner and group
                readable = bool(stat.st_mode & 0o440)
                self.assertTrue(
                    readable,
                    f"Documentation file should be readable: {file_path}"
                )

    def test_readme_table_of_contents(self):
        """Test that README.md has updated table of contents."""
        readme_content = self.readme_path.read_text(encoding='utf-8')

        # Should reference DLT documentation in TOC
        toc_patterns = [
            r"## .+DLT.+",
            r"DLT Activity Validation",
            r"dlt-activity-validation\.md"
        ]

        found_patterns = 0
        for pattern in toc_patterns:
            if re.search(pattern, readme_content, re.IGNORECASE):
                found_patterns += 1

        self.assertGreater(
            found_patterns,
            1,
            "README.md table of contents should reference DLT documentation"
        )


class TestDocumentationIntegration(unittest.TestCase):
    """Integration tests for documentation with the actual system."""

    def setUp(self):
        """Set up integration test environment."""
        self.project_root = project_root

    def test_dlt_script_help_matches_documentation(self):
        """Test that DLT script help matches documented options."""
        import subprocess

        try:
            # Run help command
            result = subprocess.run([
                sys.executable,
                str(self.project_root / "scripts" / "run_dlt_activity_collection.py"),
                "--help"
            ], capture_output=True, text=True, timeout=10)

            help_output = result.stdout

            # Should include documented options
            documented_options = [
                "--subreddits",
                "--segment",
                "--min-activity",
                "--time-filter",
                "--dry-run",
                "--pipeline"
            ]

            for option in documented_options:
                self.assertIn(
                    option,
                    help_output,
                    f"Script help missing documented option: {option}"
                )

        except subprocess.TimeoutExpired:
            self.fail("DLT script help command timed out")
        except FileNotFoundError:
            # Script doesn't exist or isn't executable - this is expected in some environments
            self.skipTest("DLT script not available for integration testing")

    def test_documentation_accessibility(self):
        """Test that documentation files are accessible and readable."""
        doc_files = [
            "README.md",
            "docs/README.md",
            "docs/guides/dlt-activity-validation.md",
            "docs/examples/dlt-collection-examples.md"
        ]

        for doc_file in doc_files:
            file_path = self.project_root / doc_file

            if file_path.exists():
                try:
                    # Try to read the file
                    content = file_path.read_text(encoding='utf-8')

                    # Should have some content
                    self.assertGreater(
                        len(content),
                        100,
                        f"Documentation file should have content: {doc_file}"
                    )

                except UnicodeDecodeError:
                    self.fail(f"Documentation file should be UTF-8 encoded: {doc_file}")
                except PermissionError:
                    self.fail(f"Documentation file should be readable: {doc_file}")


def run_documentation_tests():
    """Run documentation tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestDocumentation))
    suite.addTests(loader.loadTestsFromTestCase(TestDocumentationIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return summary
    return {
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0
    }


if __name__ == "__main__":
    # Run tests and print summary
    print("🧪 Running RedditHarbor Documentation Tests")
    print("=" * 60)

    results = run_documentation_tests()

    print("\n📊 Test Results Summary:")
    print(f"  • Tests run: {results['tests_run']}")
    print(f"  • Failures: {results['failures']}")
    print(f"  • Errors: {results['errors']}")
    print(f"  • Success rate: {results['success_rate']:.1%}")

    if results['success_rate'] == 1.0:
        print("\n✅ All documentation tests passed!")
        print("🎉 Documentation is complete and ready for use!")
    else:
        print(f"\n⚠️ {results['failures'] + results['errors']} test(s) failed.")
        print("🔧 Please review and fix documentation issues.")

    # Exit with appropriate code
    sys.exit(0 if results['success_rate'] == 1.0 else 1)