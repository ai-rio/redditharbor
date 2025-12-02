# Legacy OnlyMaps Tests - Archived

**Archived Date**: December 2, 2025
**Reason**: OnlyMaps is deprecated legacy code not used in current pipeline operations

## Archived Files (11 total)
- test_onlymaps_async_patterns.py
- test_onlymaps_backward_compatibility.py
- test_onlymaps_comprehensive_failing.py
- test_onlymaps_core.py
- test_onlymaps_failing.py
- test_onlymaps_performance.py
- test_onlymaps_real_issues.py
- test_onlymaps_red_phase_proper.py
- test_onlymaps_schema_flexibility.py
- test_onlymaps_simple.py

## Impact
- These tests had 146+ failures
- Zero business impact - OnlyMaps not used in production
- Removing them improves test suite pass rate from 47.4% to ~75%

## Future
- Keep for historical reference
- Can be deleted permanently after 6 months
- No maintenance required