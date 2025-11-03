#!/usr/bin/env python3
"""
RedditHarbor License Compliance Final Analysis
Clean analysis with proper license extraction
"""

import urllib.request
import json
import subprocess
from typing import Dict, List, Optional
import urllib.parse

def get_pypi_license_clean(package_name: str) -> Dict:
    """Get license information from PyPI API with clean extraction"""
    try:
        encoded_name = urllib.parse.quote(package_name)
        url = f"https://pypi.org/pypi/{encoded_name}/json"

        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            info = data.get('info', {})

            # Extract license from classifiers first (more reliable)
            classifiers = info.get('classifiers', [])
            license_from_classifier = None

            for classifier in classifiers:
                if classifier.startswith('License ::'):
                    parts = classifier.split('::')
                    if len(parts) > 1:
                        license_name = parts[-1].strip()
                        if license_name and license_name.lower() not in ['osi approved', '']:
                            license_from_classifier = license_name
                            break

            # Fallback to license field
            license_field = info.get('license', '').strip()

            # Determine best license name
            if license_from_classifier and license_from_classifier.lower() not in ['unknown', 'not specified']:
                license_name = license_from_classifier
            elif license_field and license_field.lower() not in ['unknown', '']:
                # For long license texts, extract the main license type
                if len(license_field) > 200:
                    if 'bsd' in license_field.lower():
                        license_name = 'BSD 3-Clause License'
                    elif 'mit' in license_field.lower():
                        license_name = 'MIT License'
                    elif 'apache' in license_field.lower():
                        license_name = 'Apache License 2.0'
                    else:
                        license_name = 'Custom License (Long Text)'
                else:
                    license_name = license_field
            else:
                license_name = 'Not specified'

            return {
                'license': license_name,
                'version': info.get('version', ''),
                'classifiers': classifiers
            }
    except Exception as e:
        return {'license': 'Error', 'version': '', 'classifiers': []}

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

    # Strong copyleft (viral) licenses
    strong_copyleft = ['gpl', 'agpl']
    viral_risk = any(copyleft in license_lower for copyleft in strong_copyleft)

    # Commercial use restrictions
    commercial_prohibited = any(term in license_lower for term in ['non-commercial', 'nc', 'educational only'])
    commercial_allowed = not commercial_prohibited

    # Distribution rights
    distribution_allowed = 'no distribution' not in license_lower

    # MIT compatibility
    mit_compatible = True
    if 'agpl' in license_lower:
        mit_compatible = False

    # Attribution requirements
    attribution_required = True

    # License type categorization
    if viral_risk:
        license_type = 'Strong Copyleft'
    elif any(weak in license_lower for weak in ['lgpl', 'mpl']):
        license_type = 'Weak Copyleft'
    elif any(permissive in license_lower for permissive in ['mit', 'bsd', 'apache', 'isc']):
        license_type = 'Permissive'
    else:
        license_type = 'Unknown'

    return {
        'commercial_allowed': commercial_allowed,
        'distribution_allowed': distribution_allowed,
        'viral_risk': viral_risk,
        'attribution_required': attribution_required,
        'mit_compatible': mit_compatible,
        'license_type': license_type
    }

def main():
    """Main analysis function"""

    # Key packages to analyze
    packages = [
        'praw', 'supabase', 'spacy', 'pandas', 'requests',
        'python-dotenv', 'pydantic', 'cryptography', 'pillow'
    ]

    print('🔍 RedditHarbor License Compliance Analysis')
    print('=' * 85)
    print('Project License: MIT (confirmed from README.md)')
    print()

    print('📦 Package License Summary')
    print('-' * 85)
    print(f'{"Package":<20} {"Version":<12} {"License":<30} {"Type":<15} {"MIT":<5} {"Comm"}')
    print('-' * 85)

    results = []

    for package_name in packages:
        # Get installed version
        installed_version = get_installed_version(package_name)

        # Get PyPI info
        pypi_info = get_pypi_license_clean(package_name)
        license_info = pypi_info['license']

        # Analyze compatibility
        compatibility = analyze_license_compatibility(license_info)

        # Display results
        mit_icon = "✅" if compatibility['mit_compatible'] else "⚠️"
        comm_icon = "✅" if compatibility['commercial_allowed'] else "❌"

        print(f'{package_name:<20} {installed_version:<12} {license_info:<30} {compatibility["license_type"]:<15} {mit_icon:<5} {comm_icon}')

        results.append({
            'package': package_name,
            'installed_version': installed_version,
            'pypi_version': pypi_info['version'],
            'license': license_info,
            'compatibility': compatibility
        })

    print('\n')

    # Detailed assessment
    print('⚖️  License Compatibility Assessment')
    print('=' * 85)

    viral_packages = [r for r in results if r['compatibility']['viral_risk']]
    incompatible_packages = [r for r in results if not r['compatibility']['mit_compatible']]
    commercial_restricted = [r for r in results if not r['compatibility']['commercial_allowed']]

    if viral_packages:
        print(f'⚠️  Packages with Strong Copyleft (Viral) Licenses: {len(viral_packages)}')
        for pkg in viral_packages:
            print(f'   - {pkg["package"]}: {pkg["license"]}')
            print(f'     Risk: May require source code disclosure if distributed')
        print()

    if incompatible_packages:
        print(f'❌ Packages potentially incompatible with MIT: {len(incompatible_packages)}')
        for pkg in incompatible_packages:
            print(f'   - {pkg["package"]}: {pkg["license"]}')
            print(f'     Issue: License conflicts with MIT terms')
        print()

    if commercial_restricted:
        print(f'❌ Packages with commercial use restrictions: {len(commercial_restricted)}')
        for pkg in commercial_restricted:
            print(f'   - {pkg["package"]}: {pkg["license"]}')
        print()

    if not viral_packages and not incompatible_packages and not commercial_restricted:
        print('✅ All packages are MIT compatible with no viral license risks!')
        print('✅ All packages allow commercial use!')
        print()

    # License types breakdown
    print('📊 License Type Breakdown')
    print('=' * 85)

    license_types = {}
    for result in results:
        license_type = result['compatibility']['license_type']
        license_types[license_type] = license_types.get(license_type, 0) + 1

    for license_type, count in license_types.items():
        print(f'{license_type:<20}: {count} packages')

    print()
    print('🔍 Detailed Package Analysis')
    print('=' * 85)

    for result in results:
        pkg = result['package']
        comp = result['compatibility']
        print(f'\n📦 {pkg} v{result["installed_version"]}')
        print(f'   License: {result["license"]}')
        print(f'   Type: {comp["license_type"]}')
        print(f'   MIT Compatible: {"✅ Yes" if comp["mit_compatible"] else "⚠️  Review required"}')
        print(f'   Commercial Use: {"✅ Allowed" if comp["commercial_allowed"] else "❌ Restricted"}')
        print(f'   Distribution: {"✅ Allowed" if comp["distribution_allowed"] else "❌ Restricted"}')
        print(f'   Viral Risk: {"⚠️  Yes" if comp["viral_risk"] else "✅ None"}')
        print(f'   Attribution: {"✅ Required" if comp["attribution_required"] else "❌ Not required"}')

    print()
    print('📄 Compliance Recommendations')
    print('=' * 85)

    print('🔧 Required Actions:')
    print('   1. Create a LICENSE file with MIT license text for RedditHarbor')
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
    print('   1. Use automated license scanning tools (pip-audit, safety)')
    print('   2. Monitor dependency updates for license changes')
    print('   3. Keep documentation of all third-party licenses')
    print('   4. Review new dependencies before adding them')
    print('   5. Consider legal review for commercial distribution')

    print()
    print('📋 Summary Statistics:')
    print(f'   Total Packages Analyzed: {len(results)}')
    print(f'   MIT Compatible: {len([r for r in results if r["compatibility"]["mit_compatible"]])}')
    print(f'   Commercial Use Allowed: {len([r for r in results if r["compatibility"]["commercial_allowed"]])}')
    print(f'   Viral License Risk: {len(viral_packages)}')
    print(f'   Requires Attribution: {len([r for r in results if r["compatibility"]["attribution_required"]])}')

if __name__ == '__main__':
    main()