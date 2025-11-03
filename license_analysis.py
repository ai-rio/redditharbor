#!/usr/bin/env python3
"""
License Compliance Analysis Script for RedditHarbor
Analyzes Python packages for license compatibility with MIT license
"""

import subprocess
import json
import sys
import os
import urllib.request
import urllib.parse
from pathlib import Path

def get_package_license(package_name):
    """Get license information for a package using uv pip show"""
    try:
        result = subprocess.run(
            ['uv', 'pip', 'show', package_name],
            capture_output=True, text=True, cwd='/home/carlos/projects/redditharbor'
        )
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            version = ''
            license_info = 'Unknown'

            for line in lines:
                if line.startswith('Version:'):
                    version = line.split(':')[1].strip()
                elif line.startswith('License:'):
                    license_info = line.split(':')[1].strip()

            return version, license_info
        else:
            return None, 'Not installed'
    except Exception as e:
        return None, f'Error: {e}'

def get_pypi_info(package_name):
    """Get additional license information from PyPI API"""
    try:
        import urllib.request
        import json

        url = f"https://pypi.org/pypi/{package_name}/json"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())

            info = data.get('info', {})
            license_info = info.get('license', 'Not specified')
            classifiers = info.get('classifiers', [])

            # Extract license from classifiers if not in license field
            if not license_info or license_info == 'Not specified':
                for classifier in classifiers:
                    if classifier.startswith('License ::'):
                        license_info = classifier.split('::')[-1].strip()
                        break

            return license_info, classifiers
    except Exception as e:
        return f'Error fetching PyPI info: {e}', []

def analyze_license_compatibility(license_name):
    """Analyze license compatibility with MIT"""
    license_name = license_name.lower()

    # Commercial use permissions
    commercial_allowed = True
    if any(gpl in license_name for gpl in ['gpl', 'agpl', 'lgpl']):
        commercial_allowed = True  # GPL allows commercial use
    if 'commercial' in license_name and 'prohibited' in license_name:
        commercial_allowed = False

    # Distribution rights
    distribution_allowed = True
    if 'no distribution' in license_name:
        distribution_allowed = False

    # Viral license risks
    viral_risk = False
    if any(gpl in license_name for gpl in ['gpl', 'agpl', 'lgpl']):
        viral_risk = True

    # Attribution requirements
    attribution_required = True  # Most licenses require attribution

    # MIT compatibility
    mit_compatible = True
    if any(restricted in license_name for restricted in ['agpl', 'gplv3']):
        mit_compatible = False  # AGPL and GPL v3 can have compatibility issues

    return {
        'commercial_allowed': commercial_allowed,
        'distribution_allowed': distribution_allowed,
        'viral_risk': viral_risk,
        'attribution_required': attribution_required,
        'mit_compatible': mit_compatible
    }

def main():
    """Main analysis function"""
    # Key packages to analyze
    packages = [
        ('praw', '7.8.1'),
        ('supabase', '2.23.0'),
        ('spacy', '3.8.7'),
        ('pandas', '2.3.3'),
        ('requests', '2.32.5'),
        ('python-dotenv', '1.2.1'),
        ('pydantic', '2.12.3'),
        ('cryptography', '44.0.3'),
        ('pillow', '11.3.0'),
        ('redditharbor', '0.3')  # Custom package
    ]

    print('🔍 RedditHarbor License Compliance Analysis')
    print('=' * 80)
    print(f'Project License: MIT (from README.md)')
    print('Analysis Date:', subprocess.run(['date'], capture_output=True, text=True).stdout.strip())
    print()

    print('📋 Package License Summary')
    print('-' * 80)
    print(f'{"Package":<20} {"Version":<12} {"License":<25} {"MIT Compatible":<12} {"Commercial":<10}')
    print('-' * 80)

    detailed_analysis = []

    for package_name, expected_version in packages:
        version, license_info = get_package_license(package_name)
        if version is None:
            version = expected_version

        # Get PyPI info for more details
        pypi_license, classifiers = get_pypi_info(package_name)

        # Use PyPI license if pip license is generic
        if license_info in ['UNKNOWN', 'BSD', 'MIT License'] or license_info == 'Unknown':
            license_info = pypi_license

        # Analyze compatibility
        compatibility = analyze_license_compatibility(license_info)

        print(f'{package_name:<20} {version:<12} {license_info:<25} {"✅" if compatibility["mit_compatible"] else "❌":<12} {"✅" if compatibility["commercial_allowed"] else "❌":<10}')

        detailed_analysis.append({
            'package': package_name,
            'version': version,
            'license': license_info,
            'compatibility': compatibility,
            'classifiers': classifiers
        })

    print()
    print('🔒 Detailed License Analysis')
    print('=' * 80)

    for pkg in detailed_analysis:
        print(f'\n📦 {pkg["package"]} v{pkg["version"]}')
        print(f'   License: {pkg["license"]}')

        comp = pkg['compatibility']
        print(f'   Commercial Use: {"✅ Allowed" if comp["commercial_allowed"] else "❌ Restricted"}')
        print(f'   Distribution: {"✅ Allowed" if comp["distribution_allowed"] else "❌ Restricted"}')
        print(f'   MIT Compatible: {"✅ Compatible" if comp["mit_compatible"] else "⚠️  May have issues"}')
        print(f'   Viral License Risk: {"⚠️  Yes" if comp["viral_risk"] else "✅ None"}')
        print(f'   Attribution Required: {"✅ Yes" if comp["attribution_required"] else "❌ No"}')

    print()
    print('⚖️  License Compatibility Assessment')
    print('=' * 80)

    viral_packages = [pkg for pkg in detailed_analysis if pkg['compatibility']['viral_risk']]
    incompatible_packages = [pkg for pkg in detailed_analysis if not pkg['compatibility']['mit_compatible']]

    if viral_packages:
        print(f'⚠️  Packages with viral licenses (GPL/AGPL): {len(viral_packages)}')
        for pkg in viral_packages:
            print(f'   - {pkg["package"]}: {pkg["license"]}')

    if incompatible_packages:
        print(f'❌ Packages potentially incompatible with MIT: {len(incompatible_packages)}')
        for pkg in incompatible_packages:
            print(f'   - {pkg["package"]}: {pkg["license"]}')

    if not viral_packages and not incompatible_packages:
        print('✅ All packages are MIT compatible with no viral license risks!')

    print()
    print('📄 Recommendations')
    print('=' * 80)

    if viral_packages:
        print('⚠️  Due to GPL/AGPL licenses, consider:')
        print('   1. Keep source code available if distributing the application')
        print('   2. Document the GPL dependencies in your application')
        print('   3. Consider alternative packages if strict proprietary distribution is needed')

    print('✅ General compliance recommendations:')
    print('   1. Include license notices in your application documentation')
    print('   2. Add attribution statements for all packages used')
    print('   3. Review individual license terms before commercial distribution')
    print('   4. Keep a record of all dependency licenses for audit purposes')
    print('   5. Consider using a license scanning tool for automated compliance checking')

if __name__ == '__main__':
    main()