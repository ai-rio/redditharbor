# Evidence-Based Profiling Testing

<div style="text-align: center; margin: 20px 0;">
  <h1 style="color: #FF6B35;">🧠 Evidence-Based Profiling Testing</h1>
  <p style="color: #004E89; font-size: 1.2em;">AI profiling with market validation and evidence alignment scoring</p>
</div>

---

## 📋 Overview

This **Evidence-Based Profiling Testing** guide provides comprehensive testing scenarios for RedditHarbor's AI profiling system that integrates multi-agent evidence with market validation. The testing validates evidence alignment scoring, cost tracking accuracy, and ROI analysis capabilities.

**What you'll test:**
1. 🧠 **AI Profile Generation** - Enhanced LLM profiling with evidence integration
2. 📊 **Evidence Alignment Scoring** - Quality metrics for evidence utilization
3. 🌐 **Market Validation Integration** - Jina MCP market research validation
4. 💰 **Cost Tracking Accuracy** - Precise cost attribution and ROI analysis
5. 🎯 **Quality Assurance** - Profile completeness and accuracy validation

**Time Investment:** 15 minutes
**Expected Performance:** $0.0035 per profile, >60% evidence alignment
**Success Threshold:** 90% profile generation success with cost tracking

---

## 🚀 Quick Start Evidence-Based Profiling Testing

### **Step 1: Enhanced LLM Profiler Validation (4 minutes)**

```bash
# Test Enhanced LLM Profiler initialization and basic functionality
source .venv/bin/activate && python -c "
import asyncio
import os
from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler

async def test_enhanced_profiler():
    print('🧠 Enhanced LLM Profiler Validation')
    print('=' * 40)

    # Check required environment variables
    required_vars = ['OPENROUTER_API_KEY', 'MONETIZATION_LLM_ENABLED']
    configured_vars = [var for var in required_vars if os.getenv(var)]

    print(f'Environment Configuration: {len(configured_vars)}/{len(required_vars)} variables')
    if len(configured_vars) < len(required_vars):
        missing = set(required_vars) - set(configured_vars)
        print(f'❌ Missing: {missing}')
        return

    try:
        # Initialize enhanced profiler
        profiler = EnhancedLLMProfiler(
            model='anthropic/claude-haiku-4.5',
            enable_market_validation=True
        )

        print('✅ Enhanced LLM Profiler initialized successfully')
        print(f'   Model: {profiler.model}')
        print(f'   Market Validation: {getattr(profiler, \"enable_market_validation\", False)}')

        # Test basic profiling without market validation
        print('\\n--- Testing Basic Profile Generation ---')

        test_opportunity = {
            'title': 'Looking for expense tracking software for small business',
            'text': 'Our consulting firm needs an expense tracking solution. Budget around \$150/month.',
            'subreddit': 'smallbusiness',
            'url': 'https://reddit.com/r/example'
        }

        try:
            # Generate basic profile
            profile_result = await profiler.generate_app_profile_with_costs(
                opportunity_data=test_opportunity
            )

            # Validate profile structure
            required_fields = ['app_concept', 'target_market', 'key_features', 'monetization_model', 'estimated_cost', 'token_usage']
            missing_fields = [field for field in required_fields if not hasattr(profile_result, field)]

            if not missing_fields:
                print('✅ Profile Structure: Complete')
                print(f'   App Concept: {getattr(profile_result, \"app_concept\", \"N/A\")[:50]}...')
                print(f'   Token Usage: {getattr(profile_result, \"token_usage\", 0)}')
                print(f'   Estimated Cost: \${getattr(profile_result, \"estimated_cost\", 0):.6f}')
            else:
                print(f'❌ Profile Structure: Missing {missing_fields}')

        except Exception as e:
            print(f'❌ Profile Generation Failed: {e}')

        # Test cost tracking
        print('\\n--- Testing Cost Tracking ---')
        if hasattr(profile_result, 'total_cost') and profile_result.total_cost > 0:
            print(f'✅ Cost Tracking: \${profile_result.total_cost:.6f}')
            if hasattr(profile_result, 'token_usage'):
                cost_per_token = profile_result.total_cost / profile_result.token_usage if profile_result.token_usage > 0 else 0
                print(f'   Cost per Token: \${cost_per_token:.8f}')
        else:
            print('❌ Cost Tracking: Not working')

    except ImportError as e:
        print(f'❌ Enhanced Profiler Import Error: {e}')
        print('   Ensure agent_tools.llm_profiler_enhanced is available')
    except Exception as e:
        print(f'❌ Enhanced Profiler Error: {e}')

# Run the test
asyncio.run(test_enhanced_profiler())
"
```

### **Step 2: Evidence Integration Testing (5 minutes)**

```bash
# Test evidence integration with multi-agent analysis results
source .venv/bin/activate && python -c "
import asyncio
from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler
from agent_tools.market_data_validator import MarketDataValidator

async def test_evidence_integration():
    print('🔗 Evidence Integration Testing')
    print('=' * 35)

    # Initialize components
    profiler = EnhancedLLMProfiler(
        model='anthropic/claude-haiku-4.5',
        enable_market_validation=True
    )

    market_validator = MarketDataValidator(
        model='anthropic/claude-haiku-4.5',
        enable_market_validation=True
    )

    print('✅ Components initialized successfully')

    # Test evidence-based profiling with mock Agno results
    print('\\n--- Testing Evidence-Based Profiling ---')

    test_opportunity = {
        'title': 'Freelancer needs better project management tool',
        'text': 'As a freelance designer, I need project management software under \$50/month that integrates with QuickBooks for invoicing.',
        'subreddit': 'freelance',
        'url': 'https://reddit.com/r/freelance/comments/example'
    }

    # Mock Agno multi-agent evidence
    mock_agno_evidence = {
        'willingness_to_pay_score': 65.0,
        'customer_segment': 'B2C',
        'price_sensitivity': 'medium',
        'monetization_potential': 'high',
        'competitor_analysis': 'freshbooks, wave, quickbooks',
        'confidence_score': 0.85,
        'agents_consensus': 'Strong opportunity with clear monetization path',
        'risk_factors': ['Price sensitive market', 'Competition from established players'],
        'opportunity_factors': ['QuickBooks integration need', 'Freelancer market growth']
    }

    try:
        # Generate evidence-based profile
        profile_result = await profiler.generate_app_profile_with_costs(
            opportunity_data=test_opportunity,
            agno_analysis=mock_agno_evidence
        )

        print('✅ Evidence-based profile generated')

        # Test evidence alignment scoring
        if hasattr(profile_result, 'evidence_alignment_score'):
            alignment_score = profile_result.evidence_alignment_score
            print(f'📊 Evidence Alignment Score: {alignment_score:.1f}%')

            if alignment_score >= 60:
                print('✅ Evidence Alignment: Good utilization of multi-agent evidence')
            else:
                print('⚠️  Evidence Alignment: Could be improved')
        else:
            print('❌ Evidence Alignment Score: Not available')

        # Test market validation integration
        print('\\n--- Testing Market Validation Integration ---')

        market_validation = await market_validator.validate_opportunity(
            app_concept=test_opportunity['title'],
            target_market='individual freelancers',
            problem_statement=test_opportunity['text']
        )

        if market_validation:
            validation_score = market_validation.get('validation_score', 0)
            print(f'🌐 Market Validation Score: {validation_score:.1f}%')
            print(f'   Market Size: {market_validation.get(\"market_size_estimate\", \"N/A\")}')
            print(f'   Competition Level: {market_validation.get(\"competition_level\", \"N/A\")}')
            print(f'   Validation Cost: \${market_validation.get(\"total_cost\", 0):.6f}')
        else:
            print('❌ Market Validation: Failed')

    except Exception as e:
        print(f'❌ Evidence Integration Error: {e}')

# Run the test
asyncio.run(test_evidence_integration())
"
```

### **Step 3: Quality and Accuracy Validation (3 minutes)**

```bash
# Test profile quality and accuracy metrics
source .venv/bin/activate && python -c "
import asyncio
from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler

async def test_profile_quality():
    print('📊 Profile Quality and Accuracy Validation')
    print('=' * 45)

    profiler = EnhancedLLMProfiler(
        model='anthropic/claude-haiku-4.5',
        enable_market_validation=True
    )

    # Test cases with expected quality indicators
    quality_test_cases = [
        {
            'name': 'Clear B2B Opportunity',
            'opportunity': {
                'title': 'Enterprise CRM solution needed',
                'text': 'Fortune 500 company needs comprehensive CRM for 1000+ employees. Budget \$5000/month for enterprise features.',
                'subreddit': 'sysadmin'
            },
            'expected_indicators': {
                'target_market_should_be': 'enterprise',
                'monetization_model_should_be': 'subscription',
                'min_features_count': 3
            }
        },
        {
            'name': 'Clear B2C Opportunity',
            'opportunity': {
                'title': 'Personal budget tracking app',
                'text': 'Individual user needs simple expense tracking app. Free tier with premium features at \$5/month.',
                'subreddit': 'personalfinance'
            },
            'expected_indicators': {
                'target_market_should_be': 'consumers',
                'monetization_model_should_be': 'freemium',
                'min_features_count': 3
            }
        }
    ]

    quality_results = []

    for test_case in quality_test_cases:
        print(f'\\n--- Quality Test: {test_case[\"name\"]} ---')

        try:
            # Generate profile
            profile = await profiler.generate_app_profile_with_costs(
                opportunity_data=test_case['opportunity']
            )

            # Quality assessment
            quality_score = 0
            max_score = 3

            # Check target market
            if hasattr(profile, 'target_market'):
                target_market = profile.target_market.lower()
                expected_market = test_case['expected_indicators']['target_market_should_be']
                if expected_market in target_market:
                    quality_score += 1
                    print(f'✅ Target Market: {profile.target_market}')
                else:
                    print(f'⚠️  Target Market: {profile.target_market} (expected: {expected_market})')

            # Check monetization model
            if hasattr(profile, 'monetization_model'):
                monetization = profile.monetization_model.lower()
                expected_model = test_case['expected_indicators']['monetization_model_should_be']
                if expected_model in monetization:
                    quality_score += 1
                    print(f'✅ Monetization: {profile.monetization_model}')
                else:
                    print(f'⚠️  Monetization: {profile.monetization_model} (expected: {expected_model})')

            # Check features completeness
            if hasattr(profile, 'key_features'):
                features_count = len(profile.key_features) if profile.key_features else 0
                min_features = test_case['expected_indicators']['min_features_count']
                if features_count >= min_features:
                    quality_score += 1
                    print(f'✅ Features: {features_count} features identified')
                else:
                    print(f'⚠️  Features: {features_count} features (min: {min_features})')

            quality_percentage = (quality_score / max_score) * 100
            quality_results.append({
                'name': test_case['name'],
                'score': quality_percentage,
                'quality_score': quality_score,
                'max_score': max_score
            })

            print(f'📊 Quality Score: {quality_percentage:.1f}% ({quality_score}/{max_score})')

        except Exception as e:
            print(f'❌ Quality Test Failed: {e}')
            quality_results.append({
                'name': test_case['name'],
                'score': 0,
                'error': str(e)
            })

    # Overall quality assessment
    print('\\n📊 Overall Quality Assessment:')
    if quality_results:
        avg_quality = sum(r['score'] for r in quality_results if 'score' in r) / len(quality_results)
        print(f'   Average Quality Score: {avg_quality:.1f}%')

        for result in quality_results:
            status = '✅' if result.get('score', 0) >= 70 else '⚠️' if result.get('score', 0) >= 50 else '❌'
            print(f'   {status} {result[\"name\"]}: {result.get(\"score\", 0):.1f}%')

        if avg_quality >= 80:
            print('\\n🎉 Profile Quality: Excellent')
        elif avg_quality >= 70:
            print('\\n👍 Profile Quality: Good')
        elif avg_quality >= 50:
            print('\\n⚠️  Profile Quality: Acceptable')
        else:
            print('\\n❌ Profile Quality: Needs Improvement')

# Run the test
asyncio.run(test_profile_quality())
"
```

### **Step 4: Cost Efficiency and ROI Analysis (3 minutes)**

```bash
# Test cost efficiency and ROI analysis capabilities
source .venv/bin/activate && python -c "
import asyncio
from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler
from agent_tools.market_data_validator import MarketDataValidator

async def test_cost_efficiency():
    print('💰 Cost Efficiency and ROI Analysis')
    print('=' * 40)

    profiler = EnhancedLLMProfiler(
        model='anthropic/claude-haiku-4.5',
        enable_market_validation=True
    )

    market_validator = MarketDataValidator(
        model='anthropic/claude-haiku-4.5',
        enable_market_validation=True
    )

    # Test cost efficiency with batch processing
    print('\\n--- Testing Cost Efficiency ---')

    batch_opportunities = [
        {
            'title': 'Time tracking for consultants',
            'text': 'Billable hours tracking needed for consulting business.',
            'subreddit': 'consulting'
        },
        {
            'title': 'Inventory management for retail',
            'text': 'Small retail store needs inventory tracking software.',
            'subreddit': 'smallbusiness'
        }
    ]

    total_cost = 0
    total_tokens = 0
    successful_profiles = 0

    for i, opportunity in enumerate(batch_opportunities, 1):
        try:
            print(f'\\nProcessing opportunity {i}/{len(batch_opportunities)}...')

            # Generate profile
            profile = await profiler.generate_app_profile_with_costs(
                opportunity_data=opportunity
            )

            if profile:
                profile_cost = getattr(profile, 'total_cost', 0)
                profile_tokens = getattr(profile, 'token_usage', 0)

                total_cost += profile_cost
                total_tokens += profile_tokens
                successful_profiles += 1

                print(f'   Profile {i}: \${profile_cost:.6f}, {profile_tokens} tokens')

                # Generate market validation
                market_validation = await market_validator.validate_opportunity(
                    app_concept=opportunity['title'],
                    target_market='small business',
                    problem_statement=opportunity['text']
                )

                if market_validation:
                    validation_cost = market_validation.get('total_cost', 0)
                    total_cost += validation_cost
                    print(f'   Market Validation: \${validation_cost:.6f}')

        except Exception as e:
            print(f'   ❌ Failed: {e}')

    # Cost efficiency analysis
    print('\\n📊 Cost Efficiency Analysis:')
    if successful_profiles > 0:
        avg_cost_per_profile = total_cost / successful_profiles
        avg_tokens_per_profile = total_tokens / successful_profiles

        print(f'   Total Profiles Generated: {successful_profiles}')
        print(f'   Total Cost: \${total_cost:.6f}')
        print(f'   Average Cost per Profile: \${avg_cost_per_profile:.6f}')
        print(f'   Average Tokens per Profile: {avg_tokens_per_profile:.0f}')
        print(f'   Cost per Token: \${total_cost/total_tokens:.8f}' if total_tokens > 0 else '   Cost per Token: N/A')

        # Cost efficiency rating
        target_cost_per_profile = 0.005  # \$0.005 per profile target
        efficiency_score = min(100, (target_cost_per_profile / avg_cost_per_profile) * 100) if avg_cost_per_profile > 0 else 0

        print(f'   Cost Efficiency Score: {efficiency_score:.1f}%')

        if efficiency_score >= 90:
            print('   ✅ Cost Efficiency: Excellent')
        elif efficiency_score >= 75:
            print('   👍 Cost Efficiency: Good')
        elif efficiency_score >= 50:
            print('   ⚠️  Cost Efficiency: Acceptable')
        else:
            print('   ❌ Cost Efficiency: Needs Optimization')

    # ROI simulation
    print('\\n💰 ROI Analysis (Simulation):')
    if successful_profiles > 0 and avg_cost_per_profile > 0:
        # Simulate potential value
        avg_wtp_score = 60  # Simulated average willingness to pay score
        conversion_rate = 0.02  # 2% conversion simulation
        avg_ltv = 1000  # \$1000 lifetime value per conversion

        expected_revenue_per_profile = avg_wtp_score * conversion_rate * avg_ltv / 100
        roi_ratio = expected_revenue_per_profile / avg_cost_per_profile

        print(f'   Expected Revenue per Profile: \${expected_revenue_per_profile:.2f}')
        print(f'   Cost per Profile: \${avg_cost_per_profile:.6f}')
        print(f'   Estimated ROI Ratio: {roi_ratio:.1f}x')
        print(f'   ROI Assessment: {\"Excellent\" if roi_ratio > 100 else \"Good\" if roi_ratio > 50 else \"Acceptable\" if roi_ratio > 10 else \"Low\"}')

# Run the test
asyncio.run(test_cost_efficiency())
"
```

---

## 📊 Advanced Evidence-Based Testing

### **Scenario 1: Evidence Quality Assessment**

```bash
# Test evidence quality from different multi-agent configurations
source .venv/bin/activate && python -c "
import asyncio
from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler

async def test_evidence_quality():
    print('🔍 Evidence Quality Assessment')
    print('=' * 35)

    profiler = EnhancedLLMProfiler(
        model='anthropic/claude-haiku-4.5',
        enable_market_validation=True
    )

    # Test different evidence quality scenarios
    evidence_scenarios = [
        {
            'name': 'High-Quality Evidence',
            'opportunity': {
                'title': 'Startup needs collaboration tools',
                'text': 'Tech startup with 20 employees needs project management and team collaboration software.',
                'subreddit': 'startups'
            },
            'evidence': {
                'willingness_to_pay_score': 75.0,
                'customer_segment': 'B2B',
                'price_sensitivity': 'low',
                'monetization_potential': 'very_high',
                'competitor_analysis': 'slack, microsoft teams, asana',
                'confidence_score': 0.95,
                'agents_consensus': 'Strong unanimous agreement',
                'detailed_analysis': True
            }
        },
        {
            'name': 'Medium-Quality Evidence',
            'opportunity': {
                'title': 'Personal productivity app',
                'text': 'Looking for better way to organize daily tasks and reminders.',
                'subreddit': 'productivity'
            },
            'evidence': {
                'willingness_to_pay_score': 45.0,
                'customer_segment': 'B2C',
                'price_sensitivity': 'high',
                'monetization_potential': 'medium',
                'competitor_analysis': 'todoist, things, notion',
                'confidence_score': 0.70,
                'agents_consensus': 'Moderate agreement with some uncertainty'
            }
        },
        {
            'name': 'Low-Quality Evidence',
            'opportunity': {
                'title': 'General software solution',
                'text': 'Need some kind of software for business use.',
                'subreddit': 'general'
            },
            'evidence': {
                'willingness_to_pay_score': 25.0,
                'customer_segment': 'unknown',
                'price_sensitivity': 'unknown',
                'monetization_potential': 'low',
                'competitor_analysis': 'unknown',
                'confidence_score': 0.40,
                'agents_consensus': 'Low confidence, insufficient data'
            }
        }
    ]

    for scenario in evidence_scenarios:
        print(f'\\n--- Testing {scenario[\"name\"]} ---')

        try:
            # Generate profile with evidence
            profile = await profiler.generate_app_profile_with_costs(
                opportunity_data=scenario['opportunity'],
                agno_analysis=scenario['evidence']
            )

            # Assess evidence utilization
            evidence_quality_score = 0
            max_quality_score = 4

            # Check alignment score
            if hasattr(profile, 'evidence_alignment_score'):
                alignment = profile.evidence_alignment_score
                if alignment >= 80:
                    evidence_quality_score += 1
                    print(f'✅ Evidence Alignment: {alignment:.1f}% (Excellent)')
                elif alignment >= 60:
                    evidence_quality_score += 0.75
                    print(f'👍 Evidence Alignment: {alignment:.1f}% (Good)')
                elif alignment >= 40:
                    evidence_quality_score += 0.5
                    print(f'⚠️  Evidence Alignment: {alignment:.1f}% (Fair)')
                else:
                    print(f'❌ Evidence Alignment: {alignment:.1f}% (Poor)')

            # Check profile completeness
            completeness_indicators = ['app_concept', 'target_market', 'key_features', 'monetization_model']
            completeness_score = sum(1 for indicator in completeness_indicators if hasattr(profile, indicator) and getattr(profile, indicator))
            completeness_percentage = (completeness_score / len(completeness_indicators)) * 100

            if completeness_percentage >= 90:
                evidence_quality_score += 1
                print(f'✅ Profile Completeness: {completeness_percentage:.1f}%')
            elif completeness_percentage >= 75:
                evidence_quality_score += 0.75
                print(f'👍 Profile Completeness: {completeness_percentage:.1f}%')
            elif completeness_percentage >= 50:
                evidence_quality_score += 0.5
                print(f'⚠️  Profile Completeness: {completeness_percentage:.1f}%')
            else:
                print(f'❌ Profile Completeness: {completeness_percentage:.1f}%')

            # Check evidence incorporation in analysis
            if hasattr(profile, 'evidence_incorporated') and profile.evidence_incorporated:
                evidence_quality_score += 1
                print('✅ Evidence Incorporation: Detected in analysis')
            else:
                print('⚠️  Evidence Incorporation: Not clearly detected')

            # Check logical consistency
            consistency_score = self._check_profile_consistency(profile, scenario['evidence'])
            evidence_quality_score += consistency_score
            print(f'{'✅' if consistency_score >= 0.75 else '👍' if consistency_score >= 0.5 else '⚠️'} Logical Consistency: {consistency_score*100:.1f}%')

            # Calculate overall evidence quality
            overall_quality = (evidence_quality_score / max_quality_score) * 100
            print(f'📊 Evidence Quality Score: {overall_quality:.1f}%')

        except Exception as e:
            print(f'❌ Evidence Quality Test Failed: {e}')

def _check_profile_consistency(profile, evidence):
    '''Helper function to check logical consistency'''
    consistency_score = 0

    # Check WTP alignment
    if hasattr(profile, 'target_market') and hasattr(profile, 'monetization_model'):
        if evidence['willingness_to_pay_score'] > 60 and 'enterprise' in str(profile.target_market).lower():
            consistency_score += 0.5
        elif evidence['willingness_to_pay_score'] < 40 and 'freemium' in str(profile.monetization_model).lower():
            consistency_score += 0.5

    # Check segment alignment
    if hasattr(profile, 'target_market'):
        if evidence['customer_segment'] == 'B2B' and 'business' in str(profile.target_market).lower():
            consistency_score += 0.5
        elif evidence['customer_segment'] == 'B2C' and ('consumer' in str(profile.target_market).lower() or 'personal' in str(profile.target_market).lower()):
            consistency_score += 0.5

    return min(consistency_score, 1.0)

# Run the test
asyncio.run(test_evidence_quality())
"
```

### **Scenario 2: Market Validation Integration Testing**

```bash
# Test comprehensive market validation integration
source .venv/bin/activate && python -c "
import asyncio
from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler
from agent_tools.market_data_validator import MarketDataValidator

async def test_market_validation_integration():
    print('🌐 Market Validation Integration Testing')
    print('=' * 45)

    profiler = EnhancedLLMProfiler(
        model='anthropic/claude-haiku-4.5',
        enable_market_validation=True
    )

    market_validator = MarketDataValidator(
        model='anthropic/claude-haiku-4.5',
        enable_market_validation=True
    )

    # Test market validation for different opportunity types
    market_validation_tests = [
        {
            'name': 'SaaS B2B Opportunity',
            'opportunity': {
                'title': 'B2B Scheduling Software for Service Businesses',
                'text': 'Service businesses need automated scheduling and client management. Willing to pay \$100/month for comprehensive solution.',
                'subreddit': 'smallbusiness'
            },
            'target_market': 'service businesses (salons, consultants, contractors)',
            'expected_validation_aspects': ['market_size', 'competition', 'pricing_validation']
        },
        {
            'name': 'Consumer Mobile App',
            'opportunity': {
                'title': 'Fitness Tracking Mobile App',
                'text': 'Individuals want personalized fitness tracking with social features. Free app with premium subscription at \$10/month.',
                'subreddit': 'fitness'
            },
            'target_market': 'health-conscious individuals',
            'expected_validation_aspects': ['user_base_size', 'app_store_competition', 'freemium_viability']
        }
    ]

    for test in market_validation_tests:
        print(f'\\n--- Testing {test[\"name\"]} ---')

        try:
            # Generate profile
            print('1. Generating AI profile...')
            profile = await profiler.generate_app_profile_with_costs(
                opportunity_data=test['opportunity']
            )

            if profile:
                print(f'   ✅ Profile generated: {getattr(profile, \"app_concept\", \"N/A\")[:50]}...')
                profile_cost = getattr(profile, 'total_cost', 0)
                print(f'   💰 Profile Cost: \${profile_cost:.6f}')

            # Perform market validation
            print('2. Performing market validation...')
            market_validation = await market_validator.validate_opportunity(
                app_concept=test['opportunity']['title'],
                target_market=test['target_market'],
                problem_statement=test['opportunity']['text']
            )

            if market_validation:
                validation_score = market_validation.get('validation_score', 0)
                market_size = market_validation.get('market_size_estimate', 'Unknown')
                competition = market_validation.get('competition_level', 'Unknown')
                validation_cost = market_validation.get('total_cost', 0)

                print(f'   📊 Validation Score: {validation_score:.1f}%')
                print(f'   🌍 Market Size: {market_size}')
                print(f'   ⚔️  Competition: {competition}')
                print(f'   💰 Validation Cost: \${validation_cost:.6f}')

                # Check expected validation aspects
                validation_details = market_validation.get('validation_details', {})
                for aspect in test['expected_validation_aspects']:
                    if aspect in validation_details:
                        print(f'   ✅ {aspect.replace(\"_\", \" \").title()}: Available')
                    else:
                        print(f'   ⚠️  {aspect.replace(\"_\", \" \").title()}: Not detailed')

                # Integration quality assessment
                print('\\n3. Integration Quality Assessment:')
                total_cost = profile_cost + validation_cost
                combined_score = (validation_score + (getattr(profile, 'evidence_alignment_score', 50) if hasattr(profile, 'evidence_alignment_score') else 50)) / 2

                print(f'   📈 Combined Quality Score: {combined_score:.1f}%')
                print(f'   💸 Total Analysis Cost: \${total_cost:.6f}')
                print(f'   🎯 Cost Efficiency: {\"Good\" if total_cost < 0.01 else \"Acceptable\" if total_cost < 0.02 else \"High\"}')

            else:
                print('   ❌ Market validation failed')

        except Exception as e:
            print(f'   ❌ Integration Test Failed: {e}')

# Run the test
asyncio.run(test_market_validation_integration())
"
```

### **Scenario 3: Scalability and Performance Testing**

```bash
# Test scalability and performance of evidence-based profiling
source .venv/bin/activate && python -c "
import asyncio
import time
from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler

async def test_scalability_performance():
    print('📈 Scalability and Performance Testing')
    print('=' * 40)

    profiler = EnhancedLLMProfiler(
        model='anthropic/claude-haiku-4.5',
        enable_market_validation=True
    )

    # Test different batch sizes
    batch_sizes = [1, 3, 5]
    scalability_results = []

    for batch_size in batch_sizes:
        print(f'\\n--- Testing Batch Size: {batch_size} ---')

        # Create test batch
        test_batch = [
            {
                'title': f'Opportunity {i+1}',
                'text': f'Test opportunity {i+1} for scalability testing with business use case.',
                'subreddit': 'business'
            }
            for i in range(batch_size)
        ]

        try:
            # Performance tracking
            start_time = time.time()
            total_tokens = 0
            total_cost = 0
            successful_profiles = 0

            # Process batch
            for i, opportunity in enumerate(test_batch):
                profile_start = time.time()

                try:
                    profile = await profiler.generate_app_profile_with_costs(
                        opportunity_data=opportunity
                    )

                    profile_time = time.time() - profile_start
                    profile_cost = getattr(profile, 'total_cost', 0)
                    profile_tokens = getattr(profile, 'token_usage', 0)

                    total_cost += profile_cost
                    total_tokens += profile_tokens
                    successful_profiles += 1

                    print(f'   Profile {i+1}: {profile_time:.2f}s, \${profile_cost:.6f}, {profile_tokens} tokens')

                except Exception as e:
                    print(f'   Profile {i+1}: Failed - {e}')

            # Calculate batch metrics
            total_time = time.time() - start_time
            avg_time_per_profile = total_time / successful_profiles if successful_profiles > 0 else 0
            avg_cost_per_profile = total_cost / successful_profiles if successful_profiles > 0 else 0

            scalability_results.append({
                'batch_size': batch_size,
                'total_time': total_time,
                'successful_profiles': successful_profiles,
                'avg_time_per_profile': avg_time_per_profile,
                'total_cost': total_cost,
                'avg_cost_per_profile': avg_cost_per_profile,
                'throughput': successful_profiles / total_time if total_time > 0 else 0
            })

            print(f'\\n📊 Batch {batch_size} Results:')
            print(f'   Total Time: {total_time:.2f}s')
            print(f'   Success Rate: {successful_profiles}/{batch_size} ({successful_profiles/batch_size*100:.1f}%)')
            print(f'   Throughput: {successful_profiles/total_time:.2f} profiles/second')
            print(f'   Average Cost: \${avg_cost_per_profile:.6f} per profile')

        except Exception as e:
            print(f'   ❌ Batch Test Failed: {e}')

    # Scalability analysis
    print('\\n📈 Scalability Analysis:')
    if len(scalability_results) > 1:
        print(f'   Performance degradation: {self._calculate_performance_degradation(scalability_results):.1f}%')
        print(f'   Cost efficiency: {\"Consistent\" if self._check_cost_consistency(scalability_results) else \"Variable\"}')

        for result in scalability_results:
            efficiency_score = min(100, (1.0 / result['avg_time_per_profile']) * 10) if result['avg_time_per_profile'] > 0 else 0
            print(f'   Batch {result[\"batch_size\"]}: {efficiency_score:.1f}% efficiency')

def _calculate_performance_degradation(results):
    '''Calculate performance degradation as batch size increases'''
    if len(results) < 2:
        return 0

    first_result = results[0]
    last_result = results[-1]

    time_per_profile_first = first_result['avg_time_per_profile']
    time_per_profile_last = last_result['avg_time_per_profile']

    if time_per_profile_first > 0:
        degradation = ((time_per_profile_last - time_per_profile_first) / time_per_profile_first) * 100
        return max(0, degradation)  # Only consider degradation, not improvement
    return 0

def _check_cost_consistency(results):
    '''Check if cost per profile remains consistent across batch sizes'''
    if len(results) < 2:
        return True

    costs = [r['avg_cost_per_profile'] for r in results if r['avg_cost_per_profile'] > 0]
    if len(costs) < 2:
        return True

    avg_cost = sum(costs) / len(costs)
    variance = sum((c - avg_cost) ** 2 for c in costs) / len(costs)
    std_dev = variance ** 0.5

    # Consider consistent if standard deviation is less than 20% of average
    return (std_dev / avg_cost) < 0.2 if avg_cost > 0 else False

# Run the test
asyncio.run(test_scalability_performance())
"
```

---

## 📈 Evidence-Based Profiling Performance Analysis

### **Quality Metrics Dashboard**

```bash
# Create quality metrics monitoring function
monitor_profiling_quality() {
    echo "🧠 Evidence-Based Profiling Quality Monitor"
    echo "=========================================="

    source .venv/bin/activate && python -c "
import asyncio
import json
import time
from datetime import datetime
from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler
from agent_tools.market_data_validator import MarketDataValidator

async def quality_monitoring_dashboard():
    print('📊 Profiling Quality Metrics Dashboard')
    print(f'Started at: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')
    print('=' * 50)

    # Initialize components
    profiler = EnhancedLLMProfiler(
        model='anthropic/claude-haiku-4.5',
        enable_market_validation=True
    )

    market_validator = MarketDataValidator(
        model='anthropic/claude-haiku-4.5',
        enable_market_validation=True
    )

    # Quality test suite
    quality_test_opportunity = {
        'title': 'Comprehensive Business Management Solution',
        'text': 'Small manufacturing business needs integrated solution for inventory, payroll, and customer management. Budget \$200/month for all-in-one platform.',
        'subreddit': 'smallbusiness'
    }

    # Mock evidence for testing
    test_evidence = {
        'willingness_to_pay_score': 70.0,
        'customer_segment': 'B2B',
        'price_sensitivity': 'medium',
        'monetization_potential': 'high',
        'competitor_analysis': 'quickbooks, sap, oracle',
        'confidence_score': 0.85
    }

    try:
        # Run quality tests
        print('\\nRunning comprehensive quality tests...')

        start_time = time.time()

        # Generate profile
        profile = await profiler.generate_app_profile_with_costs(
            opportunity_data=quality_test_opportunity,
            agno_analysis=test_evidence
        )

        profile_time = time.time() - start_time

        # Generate market validation
        validation_start = time.time()
        market_validation = await market_validator.validate_opportunity(
            app_concept=quality_test_opportunity['title'],
            target_market='small manufacturing businesses',
            problem_statement=quality_test_opportunity['text']
        )
        validation_time = time.time() - validation_start

        # Quality metrics calculation
        if profile and market_validation:
            print('\\n📊 Quality Metrics Results:')

            # Performance metrics
            total_time = profile_time + validation_time
            profile_cost = getattr(profile, 'total_cost', 0)
            validation_cost = market_validation.get('total_cost', 0)
            total_cost = profile_cost + validation_cost

            print(f'⏱️  Performance:')
            print(f'   Profile Generation: {profile_time:.2f}s')
            print(f'   Market Validation: {validation_time:.2f}s')
            print(f'   Total Processing: {total_time:.2f}s')

            print(f'💰 Cost Analysis:')
            print(f'   Profile Cost: \${profile_cost:.6f}')
            print(f'   Validation Cost: \${validation_cost:.6f}')
            print(f'   Total Cost: \${total_cost:.6f}')
            print(f'   Cost per Second: \${total_cost/total_time:.8f}' if total_time > 0 else '   Cost per Second: N/A')

            # Quality metrics
            alignment_score = getattr(profile, 'evidence_alignment_score', 0)
            validation_score = market_validation.get('validation_score', 0)
            overall_quality = (alignment_score + validation_score) / 2

            print(f'📈 Quality Scores:')
            print(f'   Evidence Alignment: {alignment_score:.1f}%')
            print(f'   Market Validation: {validation_score:.1f}%')
            print(f'   Overall Quality: {overall_quality:.1f}%')

            # Completeness check
            required_fields = ['app_concept', 'target_market', 'key_features', 'monetization_model']
            completeness = sum(1 for field in required_fields if hasattr(profile, field) and getattr(profile, field))
            completeness_percentage = (completeness / len(required_fields)) * 100

            print(f'📋 Profile Completeness: {completeness_percentage:.1f}% ({completeness}/{len(required_fields)} fields)')

            # Overall assessment
            print(f'\\n🎯 Overall Assessment:')

            performance_grade = 'A' if total_time < 30 else 'B' if total_time < 60 else 'C'
            cost_grade = 'A' if total_cost < 0.01 else 'B' if total_cost < 0.02 else 'C'
            quality_grade = 'A' if overall_quality >= 80 else 'B' if overall_quality >= 70 else 'C'

            print(f'   Performance Grade: {performance_grade}')
            print(f'   Cost Efficiency Grade: {cost_grade}')
            print(f'   Quality Grade: {quality_grade}')

            # Recommendations
            print(f'\\n💡 Recommendations:')
            if total_time > 60:
                print('   ⚠️  Consider optimizing processing time')
            if total_cost > 0.02:
                print('   ⚠️  Review cost efficiency')
            if overall_quality < 70:
                print('   ⚠️  Improve evidence integration')
            if completeness_percentage < 80:
                print('   ⚠️  Enhance profile completeness')

        else:
            print('❌ Quality tests failed - unable to generate profile or validation')

    except Exception as e:
        print(f'❌ Quality monitoring error: {e}')

# Run quality monitoring
asyncio.run(quality_monitoring_dashboard())
"
}

# Usage: monitor_profiling_quality
```

### **Continuous Quality Tracking**

```bash
# Create continuous quality tracking system
setup_quality_tracking() {
    echo "📈 Setting up Continuous Quality Tracking"
    echo "======================================="

    # Create quality tracking configuration
    cat > scripts/config/profiling_quality_config.json << 'EOF'
{
  "quality_tracking": {
    "enabled": true,
    "tracking_interval_hours": 1,
    "quality_thresholds": {
      "min_evidence_alignment": 60,
      "min_market_validation": 50,
      "min_profile_completeness": 80,
      "max_processing_time_seconds": 90,
      "max_cost_per_profile": 0.01
    },
    "alerting": {
      "quality_degradation_threshold": 15,
      "cost_spike_threshold": 0.02,
      "performance_degradation_threshold": 2.0
    },
    "metrics_collection": {
      "store_historical_data": true,
      "retention_days": 30,
      "generate_reports": true
    }
  }
}
EOF

    echo "✅ Quality tracking configuration created"
    echo "📁 Config file: scripts/config/profiling_quality_config.json"
}

# Usage: setup_quality_tracking
```

---

## 🎯 Success Indicators

### **When Evidence-Based Profiling Testing is Successful:**

1. **✅ Profile Generation**: 90%+ success rate with comprehensive app concepts
2. **✅ Evidence Integration**: >60% evidence alignment with multi-agent results
3. **✅ Market Validation**: Successful integration with real market research
4. **✅ Cost Tracking**: Accurate cost attribution with <\$0.01 per analysis
5. **✅ Quality Assurance**: 80%+ profile completeness and accuracy

### **Expected Performance Baselines:**

| Metric | Target | Acceptable Range |
|--------|--------|------------------|
| **Profile Generation Success** | 95% | 90-100% |
| **Evidence Alignment Score** | >60% | 50-80% |
| **Market Validation Score** | >50% | 40-70% |
| **Cost per Profile** | <\$0.01 | \$0.005-\$0.02 |
| **Processing Time** | <60s | 30-90s |
| **Profile Completeness** | >80% | 70-90% |

### **Troubleshooting Common Issues:**

#### **❌ Profile Generation Fails**
```bash
# Check environment variables
echo "OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:0:10}... (${#OPENROUTER_API_KEY} characters)"
echo "MONETIZATION_LLM_ENABLED: ${MONETIZATION_LLM_ENABLED:-false}"

# Test basic LLM profiler
python -c "
from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler
print('✅ Enhanced profiler imported successfully')
"
```

#### **❌ Evidence Alignment Score Missing**
```bash
# Test evidence integration
python -c "
import asyncio
from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler

async def test_evidence():
    profiler = EnhancedLLMProfiler()
    evidence = {'willingness_to_pay_score': 60, 'customer_segment': 'B2B'}
    result = await profiler.generate_app_profile_with_costs(
        opportunity_data={'title': 'test', 'text': 'test', 'subreddit': 'test'},
        agno_analysis=evidence
    )
    print(f'Alignment Score: {getattr(result, \"evidence_alignment_score\", \"Missing\")}')

asyncio.run(test_evidence())
"
```

#### **❌ Market Validation Not Working**
```bash
# Check Jina MCP integration
python -c "
from agent_tools.market_data_validator import MarketDataValidator
print('✅ Market validator imported')

# Check if market validation is enabled
import os
print(f'Market Validation Enabled: {os.getenv(\"MONETIZATION_LLM_ENABLED\", \"false\")}')
"
```

---

## 📚 Additional Resources

### **Related Documentation:**
- **[Integration Validation Quickstart](./integration-validation-quickstart.md)** - Basic integration testing
- **[Multi-Agent Workflow Testing](./multi-agent-workflow-testing.md)** - Agno framework testing
- **[MCP Integration Testing](./mcp-integration-testing.md)** - Jina hybrid client testing
- **[Production Pipeline Testing](./production-pipeline-testing.md)** - End-to-end production testing

### **Quick Reference Commands:**
```bash
# Quality monitoring
monitor_profiling_quality

# Setup quality tracking
setup_quality_tracking

# Quick evidence test
python -c "
import asyncio
from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler
async def test():
    profiler = EnhancedLLMProfiler()
    print('✅ Evidence-based profiling ready')
asyncio.run(test())
"
```

---

<div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #F5F5F5;">
  <p style="color: #666; font-size: 0.9em;">
    Continue with <a href="./production-pipeline-testing.md" style="color: #004E89; font-weight: bold;">Production Pipeline Testing</a> to validate complete end-to-end workflows! 🏭
  </p>
</div>