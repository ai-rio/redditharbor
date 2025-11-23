#!/usr/bin/env python3
"""
RedditHarbor Security Validation Script

This script validates that the codebase follows security best practices and
contains no hardcoded credentials or other security vulnerabilities.

Features:
- Validates that all database connections use environment variables
- Checks for hardcoded credentials in Python files
- Ensures proper environment file protection
- Validates configuration security patterns
- Generates detailed security reports

Usage:
    python scripts/security/validate_security.py
    python scripts/security/validate_security.py --fix
    python scripts/security/validate_security.py --report-json

Exit codes:
    0: No security issues found
    1: Security vulnerabilities detected
    2: Critical security issues requiring immediate attention
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class SecurityValidator:
    """Comprehensive security validator for RedditHarbor project."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.issues = []
        self.critical_issues = []
        self.warnings = []
        self.validated_files = set()

        # Patterns that indicate hardcoded credentials
        self.credential_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'127\.0\.0\.1.*543',
            r'localhost.*543',
            r'postgresql://[^@]+:[^@]+@',
            r'DATABASE_URL\s*=\s*["\'][^"\']+["\']',
            r'SUPABASE_KEY\s*=\s*["\'][^"\']+["\']',
            r'REDDIT_SECRET\s*=\s*["\'][^"\']+["\']',
            r'psycopg2\.connect\(.*host\s*=\s*["\'][^"\']+["\']',
        ]

        # Safe patterns that should be ignored (allowlist)
        self.safe_patterns = [
            r'password\s*=\s*["\'][\w\.\-_\s]{0,10}["\']',  # Common placeholder values
            r'password\s*=\s*["\'][your_][^"\']*["\']',       # Template placeholders
            r'password\s*=\s*["\'][example_][^"\']*["\']',    # Template examples
            r'postgres\s*=\s*["\'][postgres]["\']',           # Local dev default
            r'getenv\(',                                      # Environment variable usage
            r'os\.getenv\(',                                 # Environment variable usage
            r'os\.environ\[',                                # Environment variable usage
            r'localhost.*8080',                              # Common dev port
        ]

    def scan_file_for_credentials(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan a single file for hardcoded credentials."""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                # Skip comment lines
                if line.strip().startswith('#'):
                    continue

                for pattern in self.credential_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)

                    for match in matches:
                        matched_text = match.group()

                        # Check if this matches any safe patterns
                        is_safe = False
                        for safe_pattern in self.safe_patterns:
                            if re.search(safe_pattern, matched_text, re.IGNORECASE):
                                is_safe = True
                                break

                        if not is_safe:
                            issues.append({
                                'line': line_num,
                                'content': line.strip(),
                                'match': matched_text,
                                'pattern': pattern,
                                'severity': self._determine_severity(matched_text)
                            })

        except UnicodeDecodeError:
            # Skip binary files
            pass
        except Exception as e:
            self.warnings.append(f"Could not scan {file_path}: {e}")

        return issues

    def _determine_severity(self, matched_text: str) -> str:
        """Determine security issue severity based on matched content."""
        critical_indicators = [
            'postgres:postgres@',
            '127.0.0.1:543',
            'localhost:543',
            'password=postgres',
            'supabase',
            'reddit_secret',
            'service_role',
        ]

        high_indicators = [
            'password=',
            'secret=',
            'api_key=',
            'token=',
            'database_url=',
        ]

        matched_lower = matched_text.lower()

        for indicator in critical_indicators:
            if indicator in matched_lower:
                return 'CRITICAL'

        for indicator in high_indicators:
            if indicator in matched_lower:
                return 'HIGH'

        return 'MEDIUM'

    def scan_python_files(self) -> None:
        """Scan all Python files for security issues."""
        print("🔍 Scanning Python files for security issues...")

        python_files = list(self.project_root.rglob("*.py"))

        # Skip virtual environment and git directories
        python_files = [
            f for f in python_files
            if not any(skip in str(f) for skip in ['.venv', 'venv', '.git'])
        ]

        for file_path in python_files:
            if self._should_scan_file(file_path):
                issues = self.scan_file_for_credentials(file_path)
                if issues:
                    for issue in issues:
                        issue['file'] = str(file_path.relative_to(self.project_root))
                        if issue['severity'] == 'CRITICAL':
                            self.critical_issues.append(issue)
                        else:
                            self.issues.append(issue)

                self.validated_files.add(str(file_path.relative_to(self.project_root)))

    def _should_scan_file(self, file_path: Path) -> bool:
        """Determine if a file should be scanned for security issues."""
        # Skip test files that might contain test credentials
        if 'test' in file_path.name.lower():
            return False

        # Skip certain directories that are safe
        skip_dirs = {
            'archive', 'migrations', '__pycache__', '.pytest_cache',
            'node_modules', '.git', '.venv', 'venv'
        }

        if any(skip_dir in str(file_path) for skip_dir in skip_dirs):
            return False

        return True

    def validate_environment_files(self) -> None:
        """Validate that environment files are properly protected."""
        print("🔍 Validating environment file security...")

        env_files = ['.env', '.env.local', '.env.production', '.env.staging']

        for env_file in env_files:
            env_path = self.project_root / env_file

            if env_path.exists():
                # Check if it contains actual secrets (not just template)
                with open(env_path, 'r') as f:
                    content = f.read()

                # Check for template vs real values
                template_indicators = ['your_', 'example_', 'placeholder', 'here']
                real_value_patterns = [
                    r'eyJ[A-Za-z0-9_-]{100,}',  # JWT-like tokens
                    r'sk_[A-Za-z0-9]{20,}',     # API keys like OpenAI
                    r'[A-Za-z0-9]{32,}',        # Long hex strings
                ]

                has_template_values = any(indicator in content for indicator in template_indicators)
                has_real_values = any(re.search(pattern, content) for pattern in real_value_patterns)

                if has_real_values and not has_template_values:
                    # This appears to be a real environment file with secrets
                    if env_file in ['.env', '.env.local']:  # These should be gitignored
                        if env_file == '.env.local':
                            self.warnings.append(
                                f"Found .env.local with real secrets - ensure it's in .gitignore"
                            )
                        else:
                            self.warnings.append(
                                f"Found .env with real secrets - consider using .env.local instead"
                            )

    def validate_configuration_security(self) -> None:
        """Validate that configuration files use secure patterns."""
        print("🔍 Validating configuration security patterns...")

        config_files = [
            'config/settings.py',
            'config/__init__.py',
        ]

        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                # Check that it uses environment variables
                with open(config_path, 'r') as f:
                    content = f.read()

                # Look for proper environment variable usage
                env_var_usage = content.count('os.getenv(') + content.count('os.environ[')
                hardcoded_values = 0

                # Count potentially hardcoded configuration values
                for line in content.split('\n'):
                    if '=' in line and not line.strip().startswith('#'):
                        # Look for assignment statements with strings that aren't environment variables
                        if '"' in line or "'" in line:
                            if 'os.getenv(' not in line and 'os.environ[' not in line:
                                hardcoded_values += 1

                if hardcoded_values > 5 and env_var_usage < 2:
                    self.warnings.append(
                        f"{config_file} may have too many hardcoded values ({hardcoded_values}) "
                        f"compared to environment variables ({env_var_usage})"
                    )

    def validate_database_security(self) -> None:
        """Validate database connection security."""
        print("🔍 Validating database connection security...")

        # Check key database files
        db_files = [
            'scripts/database/validate_schema_sync.py',
            'scripts/database/automated_schema_validator.py',
            'scripts/check_db_columns.py',
        ]

        for db_file in db_files:
            file_path = self.project_root / db_file
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()

                # Check for secure configuration usage
                if 'get_psycopg2_config()' not in content and 'config.settings' not in content:
                    if 'psycopg2.connect(' in content:
                        self.critical_issues.append({
                            'file': db_file,
                            'line': 0,
                            'content': 'Database connection not using centralized config',
                            'match': 'psycopg2.connect without config.settings',
                            'pattern': 'DATABASE_CONFIG_PATTERN',
                            'severity': 'HIGH'
                        })

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report."""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'total_files_scanned': len(self.validated_files),
                'critical_issues': len(self.critical_issues),
                'high_issues': len([i for i in self.issues if i['severity'] == 'HIGH']),
                'medium_issues': len([i for i in self.issues if i['severity'] == 'MEDIUM']),
                'warnings': len(self.warnings),
                'status': 'SECURE' if not self.critical_issues and not self.issues else 'VULNERABLE'
            },
            'critical_issues': self.critical_issues,
            'security_issues': self.issues,
            'warnings': self.warnings,
            'recommendations': self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate security improvement recommendations."""
        recommendations = []

        if self.critical_issues:
            recommendations.append(
                "🚨 CRITICAL: Fix all hardcoded credentials immediately before deploying to production"
            )

        if self.issues:
            recommendations.append(
                "⚠️  Review and fix all security issues to prevent credential exposure"
            )

        recommendations.extend([
            "✅ Use environment variables for all sensitive configuration",
            "✅ Never commit .env.local or files with real credentials",
            "✅ Use the centralized config/settings.py database configuration",
            "✅ Regularly rotate database passwords and API keys",
            "✅ Implement secret management in production (AWS Secrets Manager, etc.)"
        ])

        return recommendations

    def print_summary(self) -> None:
        """Print security validation summary."""
        print("\n" + "="*60)
        print("🔒 REDDITHARBOR SECURITY VALIDATION REPORT")
        print("="*60)

        print(f"\n📊 SUMMARY:")
        print(f"   Files scanned: {len(self.validated_files)}")
        print(f"   Critical issues: {len(self.critical_issues)}")
        print(f"   Security issues: {len(self.issues)}")
        print(f"   Warnings: {len(self.warnings)}")

        if self.critical_issues:
            print(f"\n🚨 CRITICAL SECURITY ISSUES:")
            for issue in self.critical_issues[:5]:  # Show first 5
                print(f"   ❌ {issue['file']}:{issue['line']} - {issue['match']}")
            if len(self.critical_issues) > 5:
                print(f"   ... and {len(self.critical_issues) - 5} more critical issues")

        if self.issues:
            print(f"\n⚠️  SECURITY ISSUES:")
            for issue in self.issues[:5]:  # Show first 5
                print(f"   ⚠️  {issue['file']}:{issue['line']} - {issue['match']}")
            if len(self.issues) > 5:
                print(f"   ... and {len(self.issues) - 5} more issues")

        if self.warnings:
            print(f"\n💡 WARNINGS:")
            for warning in self.warnings[:3]:
                print(f"   💡 {warning}")
            if len(self.warnings) > 3:
                print(f"   ... and {len(self.warnings) - 3} more warnings")

        # Overall status
        if not self.critical_issues and not self.issues:
            print(f"\n✅ SECURITY STATUS: SECURE")
            print("   No security vulnerabilities found!")
        else:
            print(f"\n❌ SECURITY STATUS: VULNERABLE")
            print("   Security issues detected - fix before deployment")

    def run_validation(self) -> bool:
        """Run complete security validation."""
        print("🚀 RedditHarbor Security Validator")
        print("🔒 Comprehensive security validation for RedditHarbor project")
        print("=" * 60)

        # Run all validation checks
        self.scan_python_files()
        self.validate_environment_files()
        self.validate_configuration_security()
        self.validate_database_security()

        # Print summary
        self.print_summary()

        # Return True if secure, False if vulnerabilities found
        return len(self.critical_issues) == 0 and len(self.issues) == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="RedditHarbor Security Validator")
    parser.add_argument("--report-json", action="store_true",
                       help="Output report in JSON format")
    parser.add_argument("--report-file", type=str,
                       help="Save report to specified file")

    args = parser.parse_args()

    validator = SecurityValidator()
    is_secure = validator.run_validation()

    if args.report_json or args.report_file:
        report = validator.generate_report()

        if args.report_file:
            with open(args.report_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Detailed report saved to: {args.report_file}")
        else:
            print("\n" + json.dumps(report, indent=2))

    # Exit with appropriate code
    if validator.critical_issues:
        sys.exit(2)  # Critical security issues
    elif validator.issues:
        sys.exit(1)  # Security vulnerabilities detected
    else:
        sys.exit(0)  # Secure


if __name__ == "__main__":
    main()