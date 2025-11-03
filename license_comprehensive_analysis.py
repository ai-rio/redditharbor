#!/usr/bin/env python3
"""
Comprehensive License Compliance Analysis for RedditHarbor
Analyzes Python packages using PyPI API for accurate license information
"""

import urllib.request
import json
import sys
import subprocess
from typing import Dict, List, Tuple, Optional

def get_pypi_package_info(package_name: str) -> Dict:
    """Get detailed package information from PyPI API"""
    try:
        # URL encode the package name
        encoded_name = urllib.parse.quote(package_name)
        url = f"https://pypi.org/pypi/{encoded_name}/json"

        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        print(f"Error fetching {package_name}: {e}")
        return None

def extract_license_from_pypi(info: Dict) -> str:
    """Extract license information from PyPI data"""
    if not info:
        return "Unknown"

    package_info = info.get('info', {})

    # First try the license field
    license_field = package_info.get('license', '')
    if license_field and license_field.lower() not in ['unknown', '']:
        return license_field

    # Try classifiers
    classifiers = package_info.get('classifiers', [])
    for classifier in classifiers:
        if classifier.startswith('License ::'):
            # Extract the last part after ::
            parts = classifier.split('::')
            if len(parts) > 1:
                license_name = parts[-1].strip()
                if license_name and license_name.lower() not in ['osi approved', '']:
                    return license_name

    return "Not specified"

def get_installed_version(package_name: str) -> str:
    """Get installed version using uv pip"""
    try:
        result = subprocess.run(
            ['uv', 'pip', 'show', package_name],
            capture_output=True, text=True, cwd='/home/carlos/projects/redditharbor'
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(':')[1].strip()
        return "Not installed"
    except:
        return "Not installed"

def analyze_license_compatibility(license_name: str) -> Dict:
    """Analyze license compatibility with MIT license"""
    license_lower = license_name.lower()

    # License categorization
    permissive_licenses = ['mit', 'bsd', 'apache', 'isc', 'unlicense']
    weak_copyleft = ['lgpl', 'mpl']
    strong_copyleft = ['gpl', 'agpl']

    viral_risk = any(copyleft in license_lower for copyleft in strong_copyleft)

    # Commercial use - most licenses allow it except specific ones
    commercial_prohibited = any(term in license_lower for term in ['non-commercial', 'nc', 'educational only'])
    commercial_allowed = not commercial_prohibited

    # Distribution rights
    distribution_allowed = 'no distribution' not in license_lower

    # MIT compatibility assessment
    mit_compatible = True
    if any(restricted in license_lower for restricted in ['agpl', 'gplv3']):
        mit_compatible = False

    # Attribution requirements
    attribution_required = True  # Most licenses require attribution

    return {
        'commercial_allowed': commercial_allowed,
        'distribution_allowed': distribution_allowed,
        'viral_risk': viral_risk,
        'attribution_required': attribution_required,
        'mit_compatible': mit_compatible,
        'license_type': 'Permissive' if not viral_risk else ('Weak Copyleft' if 'lgpl' in license_lower else 'Strong Copyleft')
    }

def main():
    """Main analysis function"""

    # Key packages to analyze
    packages = [
        'praw',
        'supabase',
        'spacy',
        'pandas',
        'requests',
        'python-dotenv',
        'pydantic',
        'cryptography',
        'pillow'
    ]

    print('🔍 RedditHarbor License Compliance Analysis')
    print('=' * 90)
    print('Project License: MIT (confirmed from README.md)')
    print('Analysis Date:', subprocess.run(['date'], capture_output=True, text=True).stdout.strip())
    print()

    print('📦 Package License Analysis')
    print('-' * 90)
    print(f'{"Package":<20} {"Version":<12} {"License":<30} {"Type":<15} {"MIT Comp":<8} {"Commercial"}')
    print('-' * 90)

    detailed_results = []

    for package_name in packages:
        print(f"🔍 Analyzing {package_name}...")

        # Get installed version
        version = get_installed_version(package_name)

        # Get PyPI info
        pypi_info = get_pypi_package_info(package_name)
        license_info = extract_license_from_pypi(pypi_info) if pypi_info else "Unknown"

        # Analyze compatibility
        compatibility = analyze_license_compatibility(license_info)

        # Display summary
        mit_icon = "✅" if compatibility['mit_compatible'] else "⚠️"
        commercial_icon = "✅" if compatibility['commercial_allowed'] else "❌"

        print(f'{package_name:<20} {version:<12} {license_info:<30} {compatibility["license_type"]:<15} {mit_icon:<8} {commercial_icon}')

        detailed_results.append({
            'package': package_name,
            'version': version,
            'license': license_info,
            'compatibility': compatibility,
            'pypi_info': pypi_info
        })

    print()
    print('🔒 Detailed License Assessment')
    print('=' * 90)

    for result in detailed_results:
        pkg = result['package']
        comp = result['compatibility']

        print(f'\n📦 {pkg} v{result["version"]}')
        print(f'   License: {result["license"]}')
        print(f'   Type: {comp["license_type"]}')
        print(f'   Commercial Use: {"✅ Allowed" if comp["commercial_allowed"] else "❌ Restricted"}')
        print(f'   Distribution: {"✅ Allowed" if comp["distribution_allowed"] else "❌ Restricted"}')
        print(f'   MIT Compatible: {"✅ Compatible" if comp["mit_compatible"] else "⚠️  Review needed"}')
        print(f'   Viral License Risk: {"⚠️  Yes - Strong Copyleft" if comp["viral_risk"] else "✅ None"}')
        print(f'   Attribution Required: {"✅ Yes" if comp["attribution_required"] else "❌ No"}')

    print()
    print('⚖️  License Risk Assessment')
    print('=' * 90)

    viral_packages = [r for r in detailed_results if r['compatibility']['viral_risk']]
    incompatible_packages = [r for r in detailed_results if not r['compatibility']['mit_compatible']]

    if viral_packages:
        print(f'⚠️  Packages with Strong Copyleft (Viral) Licenses: {len(viral_packages)}')
        for pkg in viral_packages:
            print(f'   - {pkg["package"]}: {pkg["license"]}')
            print(f'     Risk: May require source code disclosure if distributed')

    if incompatible_packages:
        print(f'❌ Packages potentially incompatible with MIT: {len(incompatible_packages)}')
        for pkg in incompatible_packages:
            print(f'   - {pkg["package"]}: {pkg["license"]}')
            print(f'     Issue: License conflicts with MIT terms')

    if not viral_packages and not incompatible_packages:
        print('✅ All analyzed packages are MIT compatible with no viral license risks!')

    print()
    print('📋 Commercial Use Compliance')
    print('=' * 90)

    commercial_restricted = [r for r in detailed_results if not r['compatibility']['commercial_allowed']]

    if commercial_restricted:
        print(f'⚠️  Packages with commercial use restrictions: {len(commercial_restricted)}')
        for pkg in commercial_restricted:
            print(f'   - {pkg["package"]}: {pkg["license"]}')
    else:
        print('✅ All packages allow commercial use!')

    print()
    print('📄 Compliance Recommendations')
    print('=' * 90)

    print('🔧 Immediate Actions Required:')
    print('   1. Create a LICENSE file with MIT license text')
    print('   2. Add third-party license notices in documentation')
    print('   3. Include attribution statements for all packages')

    if viral_packages:
        print()
        print('⚠️  Due to Strong Copyleft licenses:')
        print('   1. Consider providing source code if distributing commercially')
        print('   2. Document these dependencies in your application')
        print('   3. Review GPL/AGPL compliance requirements')

    print()
    print('🔄 Ongoing Compliance:')
    print('   1. Use automated license scanning tools (e.g., pip-audit, safety)')
    print('   2. Monitor dependency updates for license changes')
    print('   3. Keep documentation of all third-party licenses')
    print('   4. Review new dependencies before adding them')
    print('   5. Consider legal review for commercial distribution')

    print()
    print('📊 License Summary Statistics:')
    print(f'   Total Packages Analyzed: {len(detailed_results)}')
    print(f'   MIT Compatible: {len([r for r in detailed_results if r["compatibility"]["mit_compatible"]])}')
    print(f'   Commercial Use Allowed: {len([r for r in detailed_results if r["compatibility"]["commercial_allowed"]])}')
    print(f'   Viral License Risk: {len(viral_packages)}')
    print(f'   Requires Attribution: {len([r for r in detailed_results if r["compatibility"]["attribution_required"]])}')

if __name__ == '__main__':
    main()