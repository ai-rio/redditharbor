#!/usr/bin/env python3
"""
Empty Opportunities Cleanup Script
Automatically removes opportunities with empty/invalid concepts from the database
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY

def cleanup_empty_opportunities(dry_run=True, min_concept_length=10):
    """
    Remove opportunities with empty or too-short concepts

    Args:
        dry_run: If True, show what would be deleted without actually deleting
        min_concept_length: Minimum length for a concept to be considered valid
    """
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    print('🧹 EMPTY OPPORTUNITIES CLEANUP')
    print('=' * 60)
    print(f'Mode: {"DRY RUN - No changes will be made" if dry_run else "LIVE - Will delete records"}')
    print(f'Minimum concept length: {min_concept_length} characters')
    print('')

    # First, count all opportunities
    total_result = supabase.table('workflow_results').select('count', count='exact').execute()
    total_count = total_result.count if total_result.count else 0

    # Find opportunities with empty/short concepts
    all_result = supabase.table('workflow_results').select('opportunity_id, final_score, app_concept').execute()

    empty_opps = []
    valid_opps = []

    if all_result.data:
        for opp in all_result.data:
            concept = opp.get('app_concept', '').strip()
            opp_id = opp.get('opportunity_id')
            score = opp.get('final_score', 0)

            if len(concept) < min_concept_length:
                empty_opps.append({
                    'opportunity_id': opp_id,
                    'final_score': score,
                    'concept_length': len(concept),
                    'concept_preview': concept[:50] + '...' if len(concept) > 50 else concept
                })
            else:
                valid_opps.append(opp)

    print(f'📊 DATABASE STATUS:')
    print(f'   Total opportunities: {total_count}')
    print(f'   Valid opportunities: {len(valid_opps)}')
    print(f'   Empty/invalid opportunities: {len(empty_opps)}')
    print(f'   Cleanup ratio: {len(empty_opps)/total_count*100:.1f}% will be removed')
    print('')

    if empty_opps:
        print(f'🗑️  OPPORTUNITIES TO REMOVE:')
        print(f'   Score distribution:')

        # Group by score for analysis
        score_groups = {}
        for opp in empty_opps:
            score = opp.get('final_score', 0)
            score_key = f'{int(score)}'
            if score_key not in score_groups:
                score_groups[score_key] = 0
            score_groups[score_key] += 1

        for score in sorted(score_groups.keys(), reverse=True):
            count = score_groups[score]
            print(f'      Score {score}: {count} opportunities')

        print(f'\\n   Sample records:')
        for i, opp in enumerate(empty_opps[:5], 1):
            print(f'      {i}. ID: {opp["opportunity_id"][:8]}... | Score: {opp["final_score"]} | Length: {opp["concept_length"]}')
            print(f'         Concept: "{opp["concept_preview"]}"')

        if len(empty_opps) > 5:
            print(f'      ... and {len(empty_opps) - 5} more')

        if not dry_run:
            print(f'\\n🚨 DELETING {len(empty_opps)} EMPTY OPPORTUNITIES...')

            # Delete in batches to avoid timeout
            batch_size = 100
            deleted_count = 0

            for i in range(0, len(empty_opps), batch_size):
                batch = empty_opps[i:i + batch_size]
                opp_ids = [opp['opportunity_id'] for opp in batch]

                try:
                    delete_result = supabase.table('workflow_results').delete().in_('opportunity_id', opp_ids).execute()
                    batch_deleted = len(delete_result.data) if delete_result.data else 0
                    deleted_count += batch_deleted

                    print(f'   Batch {i//batch_size + 1}: Deleted {batch_deleted} records')

                except Exception as e:
                    print(f'   ❌ Error in batch {i//batch_size + 1}: {e}')

            print(f'\\n✅ CLEANUP COMPLETE: Deleted {deleted_count} empty opportunities')

            # Verify cleanup
            remaining_result = supabase.table('workflow_results').select('count', count='exact').execute()
            remaining_count = remaining_result.count if remaining_result.count else 0

            print(f'\\n📊 POST-CLEANUP STATUS:')
            print(f'   Opportunities before: {total_count}')
            print(f'   Opportunities after: {remaining_count}')
            print(f'   Actually deleted: {total_count - remaining_count}')

        else:
            print(f'\\n🔍 DRY RUN COMPLETE: Would delete {len(empty_opps)} empty opportunities')
            print(f'   Run with --execute to perform actual deletion')

    else:
        print('✅ No empty opportunities found - database is clean!')

    return {
        'total_count': total_count,
        'valid_count': len(valid_opps),
        'empty_count': len(empty_opps),
        'deleted_count': len(empty_opps) if not dry_run else 0
    }

def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Clean up empty opportunities from database')
    parser.add_argument('--execute', action='store_true', help='Actually delete records (default is dry run)')
    parser.add_argument('--min-length', type=int, default=10, help='Minimum concept length to consider valid')

    args = parser.parse_args()

    try:
        results = cleanup_empty_opportunities(
            dry_run=not args.execute,
            min_concept_length=args.min_length
        )

        if results['empty_count'] > 0 and not args.execute:
            print(f'\\n💡 To execute cleanup, run: python {__file__} --execute')

        return 0

    except Exception as e:
        print(f'❌ Cleanup failed: {e}')
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())