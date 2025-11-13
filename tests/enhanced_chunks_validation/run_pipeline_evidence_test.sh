#!/bin/bash
# Pipeline Evidence Test Runner
# Runs comprehensive evidence-based validation of DLT trust pipeline
# Maps enhanced chunks documentation requirements to actual implementation

set -e  # Exit on any failure

echo "🚀 REDDITHARBOR PIPELINE EVIDENCE TEST"
echo "Mapping Enhanced Chunks Documentation → DLT Trust Pipeline"
echo "=================================================================="

# Create results directory
RESULTS_DIR="pipeline_evidence_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "📁 Results directory: $RESULTS_DIR"

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Verify environment
echo "🔍 Verifying environment..."
python -c "
import sys
print(f'Python: {sys.version}')
try:
    import dlt
    print(f'DLT: {dlt.__version__}')
except ImportError as e:
    print(f'DLT import failed: {e}')
    sys.exit(1)

try:
    from agent_tools.llm_profiler import LLMProfiler
    print('✅ LLM Profiler available')
except ImportError as e:
    print(f'LLM Profiler import failed: {e}')
    sys.exit(1)

try:
    from core.trust_layer import TrustLayerValidator
    print('✅ Trust Layer available')
except ImportError as e:
    print(f'Trust Layer import failed: {e}')
    sys.exit(1)
"

echo ""
echo "🧪 Running Evidence-Based Pipeline Validation..."
echo "Testing against Enhanced Chunks Documentation Requirements"
echo ""

# Run the comprehensive evidence validator
python tests/enhanced_chunks_validation/enhanced_chunks_to_pipeline_validator.py \
    --strict-mode \
    --output "$RESULTS_DIR/validation_results.json" \
    --evidence-report "$RESULTS_DIR/evidence_report.json" \
    2>&1 | tee "$RESULTS_DIR/validation_log.txt"

VALIDATION_EXIT_CODE=$?

echo ""
echo "=================================================================="
if [ $VALIDATION_EXIT_CODE -eq 0 ]; then
    echo "🎉 PIPELINE VALIDATION: PASSED"
    echo "✅ Production readiness approved with concrete evidence"
else
    echo "❌ PIPELINE VALIDATION: FAILED"
    echo "🚨 Critical issues found - review evidence report"
fi

echo "=================================================================="

# Run additional targeted tests for specific validation areas

echo ""
echo "🔍 Running Targeted Cost Optimization Test..."
# Test cost optimization specifically
python -c "
from tests.enhanced_chunks_validation.enhanced_chunks_to_pipeline_validator import PipelineEvidenceValidator
validator = PipelineEvidenceValidator(strict_mode=True)
cost_pass, cost_result = validator.validate_cost_optimization()
print(f'Cost Optimization: {\"✅ PASS\" if cost_pass else \"❌ FAIL\"}')
print(f'Cost Savings: {cost_result.get(\"cost_savings_percent\", 0):.1f}%')
print(f'Estimated Monthly Savings: \${cost_result.get(\"estimated_monthly_savings\", 0):.2f}')
" 2>&1 | tee "$RESULTS_DIR/cost_test.txt"

echo ""
echo "🔍 Running Targeted Score Distribution Test..."
# Test score distribution specifically
python -c "
from tests.enhanced_chunks_validation.enhanced_chunks_to_pipeline_validator import PipelineEvidenceValidator
validator = PipelineEvidenceValidator(strict_mode=True)
dist_pass, dist_result = validator.validate_realistic_score_distribution()
print(f'Score Distribution: {\"✅ PASS\" if dist_pass else \"❌ FAIL\"}')
print(f'70+ Score Rate: {dist_result.get(\"high_score_rate_70\", 0):.1f}% (should be ≤3%)')
print(f'Average Score: {dist_result.get(\"average_score\", 0):.1f}')
print(f'Total Scores Analyzed: {dist_result.get(\"total_scores\", 0)}')
" 2>&1 | tee "$RESULTS_DIR/distribution_test.txt"

echo ""
echo "🔍 Running Targeted Trust Layer Separation Test..."
# Test trust layer separation specifically
python -c "
from tests.enhanced_chunks_validation.enhanced_chunks_to_pipeline_validator import PipelineEvidenceValidator
validator = PipelineEvidenceValidator(strict_mode=True)
trust_pass, trust_result = validator.validate_trust_layer_separation()
print(f'Trust Layer Separation: {\"✅ PASS\" if trust_pass else \"❌ FAIL\"}')
print(f'Independence Rate: {trust_result.get(\"independence_rate\", 0):.1f}%')
print(f'High AI/Low Trust: {trust_result.get(\"high_ai_low_trust\", 0)}')
print(f'Low AI/High Trust: {trust_result.get(\"low_ai_high_trust\", 0)}')
" 2>&1 | tee "$RESULTS_DIR/trust_test.txt"

echo ""
echo "📊 Generating Production Readiness Evidence Report..."

# Generate final evidence summary
python -c "
import json
from pathlib import Path

# Load validation results
results_file = Path('$RESULTS_DIR/validation_results.json')
if results_file.exists():
    with open(results_file) as f:
        results = json.load(f)

    production_ready = results.get('production_ready', False)
    compliance_score = results.get('compliance_score', 0)
    critical_failures = results.get('critical_failures', [])

    print('PRODUCTION READINESS EVIDENCE SUMMARY:')
    print('=====================================')
    print(f'Production Ready: {\"✅ YES\" if production_ready else \"❌ NO\"}')
    print(f'Compliance Score: {compliance_score:.1f}/100')
    print(f'Critical Failures: {len(critical_failures)}')

    if critical_failures:
        print('\\n🚨 Critical Issues:')
        for i, failure in enumerate(critical_failures, 1):
            print(f'  {i}. {failure}')

    # Evidence by category
    evidence_log = results.get('evidence_log', [])
    categories = {}
    for evidence in evidence_log:
        category = evidence.get('category', 'Unknown')
        if category not in categories:
            categories[category] = []
        categories[category].append(evidence)

    print(f'\\n📊 Evidence Collected: {len(evidence_log)} measurements')
    print(f'📋 Evidence Categories: {len(categories)}')

    for category, items in categories.items():
        passed = sum(1 for item in items if item.get('pass_fail') is True)
        failed = sum(1 for item in items if item.get('pass_fail') is False)
        print(f'  {category}: {passed} passed, {failed} failed')

    # Cost analysis
    cost_result = results.get('cost_optimization', {})
    if cost_result.get('estimated_monthly_savings'):
        print(f'\\n💰 Cost Analysis:')
        print(f'  Filtering Rate: {cost_result.get(\"filtering_rate\", 0):.1f}%')
        print(f'  Estimated Monthly Savings: \${cost_result.get(\"estimated_monthly_savings\", 0):.2f}')

    # Performance analysis
    perf_result = results.get('pipeline_performance', {})
    if perf_result.get('time_per_post'):
        print(f'\\n⚡ Performance Analysis:')
        print(f'  Time per Post: {perf_result.get(\"time_per_post\", 0):.2f}s')
        print(f'  Performance Target Met: {\"✅ YES\" if perf_result.get(\"performance_acceptable\") else \"❌ NO\"}')

else:
    print('❌ Validation results file not found')
" 2>&1 | tee "$RESULTS_DIR/evidence_summary.txt"

echo ""
echo "📋 VALIDATION COMPLETE"
echo "======================"
echo "Results saved in: $RESULTS_DIR"
echo ""
echo "Generated files:"
echo "  - validation_results.json: Complete validation data"
echo "  - evidence_report.json: Detailed evidence log"
echo "  - validation_log.txt: Full validation log"
echo "  - cost_test.txt: Cost optimization test"
echo "  - distribution_test.txt: Score distribution test"
echo "  - trust_test.txt: Trust layer separation test"
echo "  - evidence_summary.txt: Production readiness summary"
echo ""

if [ $VALIDATION_EXIT_CODE -eq 0 ]; then
    echo "🎯 NEXT STEPS:"
    echo "  ✅ Pipeline is production ready"
    echo "  ✅ All critical validations passed"
    echo "  ✅ Evidence supports deployment decision"
    echo ""
    echo "💡 Recommendations:"
    echo "  - Review evidence_summary.txt for key metrics"
    echo "  - Monitor cost savings in production"
    echo "  - Validate score distribution over time"
else
    echo "🛠️  REQUIRED ACTIONS:"
    echo "  ❌ Critical failures must be addressed"
    echo "  ❌ Review evidence_report.json for specific issues"
    echo "  ❌ Fix failures before production deployment"
    echo ""
    echo "🔧 Immediate Actions Required:"
    echo "  1. Address each critical failure listed above"
    echo "  2. Re-run validation after fixes"
    echo "  3. Ensure evidence supports production readiness"
fi

exit $VALIDATION_EXIT_CODE