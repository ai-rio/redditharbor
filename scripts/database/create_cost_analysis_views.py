#!/usr/bin/env python3
"""
Cost Analysis Views Creator
Creates comprehensive database views for cost tracking and analysis
"""

import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import psycopg2
    from psycopg2.extras import DictCursor
except ImportError:
    print("Installing psycopg2-binary...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2
    from psycopg2.extras import DictCursor

from dotenv import load_dotenv


def get_database_connection():
    """Get database connection using Supabase credentials."""
    load_dotenv(project_root / '.env.local')

    db_url = os.getenv("SUPABASE_DB_URL")
    if db_url:
        return psycopg2.connect(db_url)

    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("Missing database credentials")

    # Parse Supabase URL for local development
    if "http://127.0.0.1" in supabase_url:
        # Extract host from URL like http://127.0.0.1:54321
        host = "127.0.0.1"
        port = "54322"
        # For local development, the password is 'postgres'
        password = "postgres"
    elif "https://" in supabase_url:
        # Remove https:// and any path
        host = supabase_url.replace("https://", "").split("/")[0]
        port = "5432"  # Default PostgreSQL port for production
        password = supabase_key
    else:
        # Assume it's already a hostname
        host = supabase_url
        port = "5432"
        password = supabase_key

    # Construct connection string
    conn_string = f"postgresql://postgres:{password}@{host}:{port}/postgres"
    return psycopg2.connect(conn_string)


def create_cost_analysis_views(conn) -> Dict[str, Any]:
    """
    Create comprehensive cost analysis views.

    Args:
        conn: Database connection

    Returns:
        View creation results
    """
    views = [
        {
            'name': 'cost_tracking_summary',
            'description': 'Daily cost tracking summary by model',
            'category': 'Summary',
            'sql': '''
                CREATE OR REPLACE VIEW cost_tracking_summary AS
                SELECT
                    DATE_TRUNC('day', llm_timestamp) as analysis_date,
                    llm_model_used,
                    llm_provider,
                    COUNT(*) as opportunities_processed,
                    SUM(llm_total_cost_usd) as total_cost_usd,
                    AVG(llm_total_cost_usd) as avg_cost_per_opportunity,
                    SUM(llm_total_tokens) as total_tokens,
                    AVG(llm_total_tokens) as avg_tokens_per_opportunity,
                    AVG(llm_latency_seconds) as avg_latency_seconds,
                    MAX(llm_total_cost_usd) as max_cost_per_opportunity,
                    MIN(llm_total_cost_usd) as min_cost_per_opportunity
                FROM workflow_results
                WHERE cost_tracking_enabled = true
                    AND llm_timestamp IS NOT NULL
                GROUP BY DATE_TRUNC('day', llm_timestamp), llm_model_used, llm_provider
                ORDER BY analysis_date DESC, total_cost_usd DESC;
            '''
        },
        {
            'name': 'cost_tracking_model_performance',
            'description': 'Model performance comparison',
            'category': 'Performance',
            'sql': '''
                CREATE OR REPLACE VIEW cost_tracking_model_performance AS
                SELECT
                    llm_model_used,
                    llm_provider,
                    COUNT(*) as total_requests,
                    SUM(llm_total_cost_usd) as total_cost_usd,
                    AVG(llm_total_cost_usd) as avg_cost_per_request,
                    SUM(llm_total_tokens) as total_tokens,
                    AVG(llm_total_tokens) as avg_tokens_per_request,
                    AVG(llm_latency_seconds) as avg_latency_seconds,
                    AVG(final_score) as avg_opportunity_score,
                    COUNT(*) FILTER (WHERE final_score >= 70) as high_score_count,
                    COUNT(*) FILTER (WHERE final_score >= 50 AND final_score < 70) as medium_score_count,
                    COUNT(*) FILTER (WHERE final_score < 50) as low_score_count,
                    MIN(llm_timestamp) as first_used,
                    MAX(llm_timestamp) as last_used,
                    (MAX(llm_timestamp) - MIN(llm_timestamp)) as usage_span_days
                FROM workflow_results
                WHERE cost_tracking_enabled = true
                    AND llm_model_used IS NOT NULL
                GROUP BY llm_model_used, llm_provider
                ORDER BY total_cost_usd DESC;
            '''
        },
        {
            'name': 'cost_tracking_efficiency_analysis',
            'description': 'Cost efficiency analysis by score ranges',
            'category': 'Efficiency',
            'sql': '''
                CREATE OR REPLACE VIEW cost_tracking_efficiency_analysis AS
                SELECT
                    CASE
                        WHEN final_score >= 80 THEN 'High Impact (80+)'
                        WHEN final_score >= 60 THEN 'Medium Impact (60-79)'
                        WHEN final_score >= 40 THEN 'Low Impact (40-59)'
                        ELSE 'Minimal Impact (<40)'
                    END as impact_category,
                    COUNT(*) as opportunity_count,
                    SUM(llm_total_cost_usd) as total_cost_usd,
                    AVG(llm_total_cost_usd) as avg_cost_per_opportunity,
                    SUM(llm_total_tokens) as total_tokens,
                    AVG(llm_total_tokens) as avg_tokens_per_opportunity,
                    AVG(final_score) as avg_score,
                    MAX(final_score) as max_score,
                    MIN(final_score) as min_score,
                    SUM(llm_total_cost_usd) / COUNT(*) as cost_per_score_point,
                    COUNT(*) * AVG(final_score) / 100 as roi_estimate
                FROM workflow_results
                WHERE cost_tracking_enabled = true
                    AND final_score IS NOT NULL
                GROUP BY
                    CASE
                        WHEN final_score >= 80 THEN 1
                        WHEN final_score >= 60 THEN 2
                        WHEN final_score >= 40 THEN 3
                        ELSE 4
                    END,
                    CASE
                        WHEN final_score >= 80 THEN 'High Impact (80+)'
                        WHEN final_score >= 60 THEN 'Medium Impact (60-79)'
                        WHEN final_score >= 40 THEN 'Low Impact (40-59)'
                        ELSE 'Minimal Impact (<40)'
                    END
                ORDER BY avg_score DESC;
            '''
        },
        {
            'name': 'cost_tracking_daily_trends',
            'description': 'Daily cost and usage trends',
            'category': 'Trends',
            'sql': '''
                CREATE OR REPLACE VIEW cost_tracking_daily_trends AS
                SELECT
                    DATE_TRUNC('day', llm_timestamp) as analysis_date,
                    COUNT(*) as total_opportunities,
                    COUNT(*) FILTER (WHERE cost_tracking_enabled = true) as with_cost_tracking,
                    SUM(llm_total_cost_usd) as total_cost_usd,
                    AVG(llm_total_cost_usd) as avg_cost_per_opportunity,
                    SUM(llm_total_tokens) as total_tokens,
                    AVG(llm_total_tokens) as avg_tokens_per_opportunity,
                    AVG(llm_latency_seconds) as avg_latency_seconds,
                    AVG(final_score) as avg_opportunity_score,
                    COUNT(DISTINCT llm_model_used) as models_used,
                    LAG(SUM(llm_total_cost_usd)) OVER (ORDER BY DATE_TRUNC('day', llm_timestamp)) as previous_day_cost,
                    SUM(llm_total_cost_usd) - LAG(SUM(llm_total_cost_usd)) OVER (ORDER BY DATE_TRUNC('day', llm_timestamp)) as cost_change
                FROM workflow_results
                WHERE llm_timestamp IS NOT NULL
                GROUP BY DATE_TRUNC('day', llm_timestamp)
                ORDER BY analysis_date DESC;
            '''
        },
        {
            'name': 'cost_tracking_budget_monitor',
            'description': 'Budget monitoring and alerts',
            'category': 'Budget',
            'sql': '''
                CREATE OR REPLACE VIEW cost_tracking_budget_monitor AS
                WITH daily_costs AS (
                    SELECT
                        DATE_TRUNC('day', llm_timestamp) as cost_date,
                        SUM(llm_total_cost_usd) as daily_cost
                    FROM workflow_results
                    WHERE cost_tracking_enabled = true
                        AND llm_timestamp >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY DATE_TRUNC('day', llm_timestamp)
                ),
                budget_metrics AS (
                    SELECT
                        CURRENT_DATE - INTERVAL '7 days' as week_start,
                        CURRENT_DATE as week_end,
                        SUM(daily_cost) as weekly_cost,
                        AVG(daily_cost) as avg_daily_cost,
                        MAX(daily_cost) as max_daily_cost
                    FROM daily_costs
                    WHERE cost_date >= CURRENT_DATE - INTERVAL '7 days'
                )
                SELECT
                    'Weekly Budget Status' as metric_type,
                    weekly_cost as current_spend,
                    weekly_cost as weekly_spend,
                    avg_daily_cost as daily_average,
                    max_daily_cost as peak_daily,
                    CASE
                        WHEN weekly_cost > 10.0 THEN 'OVER BUDGET'
                        WHEN weekly_cost > 7.5 THEN 'NEAR LIMIT'
                        ELSE 'WITHIN BUDGET'
                    END as budget_status,
                    ROUND((weekly_cost / 10.0) * 100, 1) as budget_percentage_used,
                    10.0 as weekly_budget_limit
                FROM budget_metrics;
            '''
        },
        {
            'name': 'cost_tracking_roi_analysis',
            'description': 'ROI analysis for AI profiling',
            'category': 'ROI',
            'sql': '''
                CREATE OR REPLACE VIEW cost_tracking_roi_analysis AS
                SELECT
                    DATE_TRUNC('month', llm_timestamp) as analysis_month,
                    llm_model_used,
                    COUNT(*) as opportunities_analyzed,
                    SUM(llm_total_cost_usd) as total_investment_usd,
                    AVG(final_score) as avg_opportunity_score,
                    COUNT(*) FILTER (WHERE final_score >= 70) as high_value_opportunities,
                    COUNT(*) FILTER (WHERE final_score >= 50) as viable_opportunities,
                    SUM(llm_total_cost_usd) / COUNT(*) FILTER (WHERE final_score >= 70) as cost_per_high_value_opp,
                    (COUNT(*) FILTER (WHERE final_score >= 70) * 100.0) / COUNT(*) as high_value_percentage,
                    CASE
                        WHEN COUNT(*) FILTER (WHERE final_score >= 70) > 0 THEN
                            (COUNT(*) FILTER (WHERE final_score >= 70) * 50.0) / SUM(llm_total_cost_usd)
                        ELSE 0
                    END as estimated_roi_multiplier
                FROM workflow_results
                WHERE cost_tracking_enabled = true
                    AND final_score IS NOT NULL
                GROUP BY DATE_TRUNC('month', llm_timestamp), llm_model_used
                ORDER BY analysis_month DESC, estimated_roi_multiplier DESC;
            '''
        },
        {
            'name': 'cost_tracking_token_efficiency',
            'description': 'Token usage efficiency analysis',
            'category': 'Efficiency',
            'sql': '''
                CREATE OR REPLACE VIEW cost_tracking_token_efficiency AS
                SELECT
                    llm_model_used,
                    llm_provider,
                    COUNT(*) as total_requests,
                    SUM(llm_prompt_tokens) as total_prompt_tokens,
                    SUM(llm_completion_tokens) as total_completion_tokens,
                    SUM(llm_total_tokens) as total_tokens,
                    AVG(llm_prompt_tokens) as avg_prompt_tokens,
                    AVG(llm_completion_tokens) as avg_completion_tokens,
                    AVG(llm_total_tokens) as avg_total_tokens,
                    SUM(llm_total_cost_usd) as total_cost_usd,
                    ROUND((SUM(llm_total_cost_usd) / SUM(llm_total_tokens)) * 1000, 6) as cost_per_1k_tokens,
                    AVG(final_score) as avg_score_per_request,
                    ROUND(AVG(final_score) / (SUM(llm_total_cost_usd) / COUNT(*)), 2) as score_per_dollar,
                    ROUND(AVG(final_score) / AVG(llm_total_tokens), 6) as score_per_token
                FROM workflow_results
                WHERE cost_tracking_enabled = true
                    AND llm_model_used IS NOT NULL
                GROUP BY llm_model_used, llm_provider
                ORDER BY cost_per_1k_tokens ASC;
            '''
        },
        {
            'name': 'cost_tracking_anomaly_detection',
            'description': 'Detect cost anomalies and outliers',
            'category': 'Monitoring',
            'sql': '''
                CREATE OR REPLACE VIEW cost_tracking_anomaly_detection AS
                WITH model_stats AS (
                    SELECT
                        llm_model_used,
                        AVG(llm_total_cost_usd) as avg_cost,
                        STDDEV(llm_total_cost_usd) as cost_stddev,
                        AVG(llm_total_tokens) as avg_tokens,
                        STDDEV(llm_total_tokens) as token_stddev
                    FROM workflow_results
                    WHERE cost_tracking_enabled = true
                    GROUP BY llm_model_used
                )
                SELECT
                    wr.opportunity_id,
                    wr.app_name,
                    wr.llm_model_used,
                    wr.llm_total_cost_usd,
                    wr.llm_total_tokens,
                    wr.final_score,
                    wr.llm_timestamp,
                    ms.avg_cost as model_avg_cost,
                    ms.cost_stddev as model_cost_stddev,
                    CASE
                        WHEN ABS(wr.llm_total_cost_usd - ms.avg_cost) > (2 * ms.cost_stddev) THEN 'COST ANOMALY'
                        WHEN ABS(wr.llm_total_tokens - ms.avg_tokens) > (2 * ms.token_stddev) THEN 'TOKEN ANOMALY'
                        ELSE 'NORMAL'
                    END as anomaly_type,
                    ROUND(ABS(wr.llm_total_cost_usd - ms.avg_cost) / NULLIF(ms.cost_stddev, 0), 2) as cost_z_score,
                    ROUND(ABS(wr.llm_total_tokens - ms.avg_tokens) / NULLIF(ms.token_stddev, 0), 2) as token_z_score
                FROM workflow_results wr
                JOIN model_stats ms ON wr.llm_model_used = ms.llm_model_used
                WHERE wr.cost_tracking_enabled = true
                    AND wr.llm_model_used IS NOT NULL
                ORDER BY
                    CASE
                        WHEN ABS(wr.llm_total_cost_usd - ms.avg_cost) > (2 * ms.cost_stddev) THEN 1
                        WHEN ABS(wr.llm_total_tokens - ms.avg_tokens) > (2 * ms.token_stddev) THEN 2
                        ELSE 3
                    END,
                    wr.llm_timestamp DESC;
            '''
        }
    ]

    results = {
        'views_created': [],
        'view_details': [],
        'errors': [],
        'success': False
    }

    try:
        with conn.cursor() as cursor:
            for view in views:
                try:
                    # Drop view if exists to ensure fresh creation
                    cursor.execute(f"DROP VIEW IF EXISTS {view['name']} CASCADE")

                    # Create the view
                    cursor.execute(view['sql'])

                    results['views_created'].append(view['name'])
                    results['view_details'].append({
                        'name': view['name'],
                        'description': view['description'],
                        'category': view['category']
                    })

                    print(f"✓ Created view: {view['name']} ({view['category']})")

                except Exception as e:
                    error_msg = f"Failed to create view {view['name']}: {e}"
                    results['errors'].append(error_msg)
                    print(f"❌ {error_msg}")

            conn.commit()
            results['success'] = len(results['views_created']) > 0

    except Exception as e:
        conn.rollback()
        results['errors'].append(f"Failed to create views: {e}")
        print(f"❌ View creation failed: {e}")

    return results


def create_cost_aggregation_queries(conn) -> Dict[str, Any]:
    """
    Create stored procedures for cost aggregation queries.

    Args:
        conn: Database connection

    Returns:
        Procedure creation results
    """
    procedures = [
        {
            'name': 'get_cost_summary',
            'description': 'Get cost summary for date range',
            'sql': '''
                CREATE OR REPLACE FUNCTION get_cost_summary(
                    start_date DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
                    end_date DATE DEFAULT CURRENT_DATE
                )
                RETURNS TABLE (
                    total_opportunities BIGINT,
                    opportunities_with_costs BIGINT,
                    total_cost_usd DECIMAL(12,6),
                    avg_cost_per_opportunity DECIMAL(10,6),
                    total_tokens BIGINT,
                    avg_tokens_per_opportunity DECIMAL(10,2),
                    models_used INTEGER,
                    daily_avg_cost DECIMAL(10,6),
                    peak_daily_cost DECIMAL(10,6)
                ) AS $$
                BEGIN
                    RETURN QUERY
                    SELECT
                        COUNT(*) as total_opportunities,
                        COUNT(*) FILTER (WHERE cost_tracking_enabled = true) as opportunities_with_costs,
                        COALESCE(SUM(llm_total_cost_usd), 0) as total_cost_usd,
                        COALESCE(AVG(llm_total_cost_usd), 0) as avg_cost_per_opportunity,
                        COALESCE(SUM(llm_total_tokens), 0) as total_tokens,
                        COALESCE(AVG(llm_total_tokens), 0) as avg_tokens_per_opportunity,
                        COUNT(DISTINCT llm_model_used) as models_used,
                        COALESCE(AVG(daily_total), 0) as daily_avg_cost,
                        COALESCE(MAX(daily_total), 0) as peak_daily_cost
                    FROM workflow_results w
                    LEFT JOIN (
                        SELECT
                            DATE_TRUNC('day', llm_timestamp) as cost_date,
                            SUM(llm_total_cost_usd) as daily_total
                        FROM workflow_results
                        WHERE cost_tracking_enabled = true
                            AND llm_timestamp IS NOT NULL
                        GROUP BY DATE_TRUNC('day', llm_timestamp)
                    ) daily ON w.llm_timestamp IS NOT NULL
                    WHERE w.llm_timestamp >= start_date
                        AND w.llm_timestamp <= end_date + INTERVAL '1 day'
                        OR w.llm_timestamp IS NULL;
                END;
                $$ LANGUAGE plpgsql;
            '''
        },
        {
            'name': 'get_model_cost_comparison',
            'description': 'Compare costs between different models',
            'sql': '''
                CREATE OR REPLACE FUNCTION get_model_cost_comparison(
                    days_back INTEGER DEFAULT 30
                )
                RETURNS TABLE (
                    model_name TEXT,
                    provider TEXT,
                    request_count BIGINT,
                    total_cost_usd DECIMAL(12,6),
                    avg_cost_per_request DECIMAL(10,6),
                    total_tokens BIGINT,
                    avg_tokens_per_request DECIMAL(10,2),
                    cost_per_1k_tokens DECIMAL(8,6),
                    avg_latency_seconds DECIMAL(8,3),
                    avg_score DECIMAL(5,2),
                    usage_percentage DECIMAL(5,2)
                ) AS $$
                DECLARE
                    total_requests BIGINT;
                BEGIN
                    -- Get total requests for percentage calculation
                    SELECT COUNT(*) INTO total_requests
                    FROM workflow_results
                    WHERE cost_tracking_enabled = true
                        AND llm_timestamp >= CURRENT_DATE - INTERVAL '1 day' * days_back;

                    RETURN QUERY
                    SELECT
                        llm_model_used as model_name,
                        llm_provider as provider,
                        COUNT(*) as request_count,
                        SUM(llm_total_cost_usd) as total_cost_usd,
                        AVG(llm_total_cost_usd) as avg_cost_per_request,
                        SUM(llm_total_tokens) as total_tokens,
                        AVG(llm_total_tokens) as avg_tokens_per_request,
                        ROUND((SUM(llm_total_cost_usd) / SUM(llm_total_tokens)) * 1000, 6) as cost_per_1k_tokens,
                        AVG(llm_latency_seconds) as avg_latency_seconds,
                        AVG(final_score) as avg_score,
                        ROUND((COUNT(*)::DECIMAL / NULLIF(total_requests, 0)) * 100, 2) as usage_percentage
                    FROM workflow_results
                    WHERE cost_tracking_enabled = true
                        AND llm_model_used IS NOT NULL
                        AND llm_timestamp >= CURRENT_DATE - INTERVAL '1 day' * days_back
                    GROUP BY llm_model_used, llm_provider
                    ORDER BY total_cost_usd DESC;
                END;
                $$ LANGUAGE plpgsql;
            '''
        },
        {
            'name': 'calculate_cost_forecast',
            'description': 'Forecast costs based on historical trends',
            'sql': '''
                CREATE OR REPLACE FUNCTION calculate_cost_forecast(
                    forecast_days INTEGER DEFAULT 7
                )
                RETURNS TABLE (
                    forecast_date DATE,
                    predicted_cost_usd DECIMAL(10,6),
                    confidence_level TEXT,
                    trend_direction TEXT
                ) AS $$
                DECLARE
                    avg_daily_cost DECIMAL(10,6);
                    cost_stddev DECIMAL(10,6);
                    trend_slope DECIMAL(10,6);
                BEGIN
                    -- Calculate historical averages and trends
                    SELECT
                        AVG(daily_cost),
                        STDDEV(daily_cost),
                        CASE
                            WHEN COUNT(*) >= 7 THEN
                                (CORR(daily_cost, day_number) * STDDEV(daily_cost) / STDDEV(day_number))
                            ELSE 0
                        END
                    INTO avg_daily_cost, cost_stddev, trend_slope
                    FROM (
                        SELECT
                            SUM(llm_total_cost_usd) as daily_cost,
                            ROW_NUMBER() OVER (ORDER BY DATE_TRUNC('day', llm_timestamp)) as day_number
                        FROM workflow_results
                        WHERE cost_tracking_enabled = true
                            AND llm_timestamp >= CURRENT_DATE - INTERVAL '14 days'
                        GROUP BY DATE_TRUNC('day', llm_timestamp)
                    ) historical_data;

                    -- Generate forecast
                    RETURN QUERY
                    SELECT
                        CURRENT_DATE + x.day_offset as forecast_date,
                        GREATEST(0, avg_daily_cost + (trend_slope * x.day_offset)) as predicted_cost_usd,
                        CASE
                            WHEN ABS(x.day_offset * trend_slope) > cost_stddev THEN 'LOW'
                            WHEN ABS(x.day_offset * trend_slope) > (cost_stddev * 0.5) THEN 'MEDIUM'
                            ELSE 'HIGH'
                        END as confidence_level,
                        CASE
                            WHEN trend_slope > 0.001 THEN 'INCREASING'
                            WHEN trend_slope < -0.001 THEN 'DECREASING'
                            ELSE 'STABLE'
                        END as trend_direction
                    FROM generate_series(1, forecast_days) AS x(day_offset)
                    ORDER BY forecast_date;
                END;
                $$ LANGUAGE plpgsql;
            '''
        }
    ]

    results = {
        'procedures_created': [],
        'procedure_details': [],
        'errors': [],
        'success': False
    }

    try:
        with conn.cursor() as cursor:
            for procedure in procedures:
                try:
                    # Drop procedure if exists
                    cursor.execute(f"DROP FUNCTION IF EXISTS {procedure['name']}() CASCADE")

                    # Create the procedure
                    cursor.execute(procedure['sql'])

                    results['procedures_created'].append(procedure['name'])
                    results['procedure_details'].append({
                        'name': procedure['name'],
                        'description': procedure['description']
                    })

                    print(f"✓ Created procedure: {procedure['name']}")

                except Exception as e:
                    error_msg = f"Failed to create procedure {procedure['name']}: {e}"
                    results['errors'].append(error_msg)
                    print(f"❌ {error_msg}")

            conn.commit()
            results['success'] = len(results['procedures_created']) > 0

    except Exception as e:
        conn.rollback()
        results['errors'].append(f"Failed to create procedures: {e}")
        print(f"❌ Procedure creation failed: {e}")

    return results


def test_cost_tracking_views(conn) -> Dict[str, Any]:
    """
    Test the created cost tracking views.

    Args:
        conn: Database connection

    Returns:
        Test results
    """
    test_results = {
        'views_tested': [],
        'view_data_counts': {},
        'errors': [],
        'success': False
    }

    views_to_test = [
        'cost_tracking_summary',
        'cost_tracking_model_performance',
        'cost_tracking_efficiency_analysis',
        'cost_tracking_daily_trends',
        'cost_tracking_budget_monitor'
    ]

    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            for view_name in views_to_test:
                try:
                    # Test if view exists and can be queried
                    cursor.execute(f"SELECT COUNT(*) as row_count FROM {view_name}")
                    result = cursor.fetchone()

                    row_count = result['row_count'] if result else 0
                    test_results['view_data_counts'][view_name] = row_count
                    test_results['views_tested'].append(view_name)

                    print(f"✓ Tested view {view_name}: {row_count} rows")

                except Exception as e:
                    error_msg = f"Failed to test view {view_name}: {e}"
                    test_results['errors'].append(error_msg)
                    print(f"❌ {error_msg}")

            # Test stored procedures
            procedures_to_test = [
                ('get_cost_summary', 'SELECT * FROM get_cost_summary()'),
                ('get_model_cost_comparison', 'SELECT * FROM get_model_cost_comparison(7)')
            ]

            for proc_name, test_query in procedures_to_test:
                try:
                    cursor.execute(test_query)
                    result = cursor.fetchone()

                    if result:
                        test_results['views_tested'].append(f"procedure_{proc_name}")
                        print(f"✓ Tested procedure {proc_name}: OK")

                except Exception as e:
                    error_msg = f"Failed to test procedure {proc_name}: {e}"
                    test_results['errors'].append(error_msg)
                    print(f"❌ {error_msg}")

            test_results['success'] = len(test_results['views_tested']) > 0

    except Exception as e:
        test_results['errors'].append(f"View testing failed: {e}")
        print(f"❌ View testing failed: {e}")

    return test_results


def main():
    """
    Main execution function for creating cost analysis views.
    """
    print("=" * 80)
    print("COST ANALYSIS VIEWS CREATOR")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    conn = None

    try:
        # Connect to database
        print("Connecting to database...")
        conn = get_database_connection()
        print("✓ Database connection established")

        # Create cost analysis views
        print("\n" + "=" * 50)
        print("CREATING COST ANALYSIS VIEWS")
        print("=" * 50)
        view_results = create_cost_analysis_views(conn)

        if view_results['success']:
            print(f"\n✓ Created {len(view_results['views_created'])} cost analysis views")

            # Group views by category
            categories = {}
            for detail in view_results['view_details']:
                category = detail['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(detail['name'])

            for category, views in categories.items():
                print(f"\n📊 {category}:")
                for view in views:
                    print(f"  - {view}")
        else:
            print("\n❌ View creation failed")
            for error in view_results['errors']:
                print(f"  - {error}")

        # Create stored procedures
        print("\n" + "=" * 50)
        print("CREATING STORED PROCEDURES")
        print("=" * 50)
        proc_results = create_cost_aggregation_queries(conn)

        if proc_results['success']:
            print(f"\n✓ Created {len(proc_results['procedures_created'])} stored procedures")
            for detail in proc_results['procedure_details']:
                print(f"  - {detail['name']}: {detail['description']}")
        else:
            print("\n❌ Procedure creation failed")
            for error in proc_results['errors']:
                print(f"  - {error}")

        # Test views and procedures
        print("\n" + "=" * 50)
        print("TESTING VIEWS AND PROCEDURES")
        print("=" * 50)
        test_results = test_cost_tracking_views(conn)

        if test_results['success']:
            print(f"\n✓ Tested {len(test_results['views_tested'])} database objects")

            print("\n📈 Current data availability:")
            for view, count in test_results['view_data_counts'].items():
                print(f"  - {view}: {count} rows")
        else:
            print("\n⚠️  Some tests failed")
            for error in test_results['errors']:
                print(f"  - {error}")

        # Final summary
        print("\n" + "=" * 80)
        print("COST ANALYSIS SETUP COMPLETE")
        print("=" * 80)

        if view_results['success'] and proc_results['success']:
            print("✅ COST ANALYSIS INFRASTRUCTURE READY")
            print("\n🔍 Available views for analysis:")
            print("  • cost_tracking_summary - Daily cost summary by model")
            print("  • cost_tracking_model_performance - Model comparison")
            print("  • cost_tracking_efficiency_analysis - Cost vs score analysis")
            print("  • cost_tracking_daily_trends - Usage trends over time")
            print("  • cost_tracking_budget_monitor - Budget tracking")
            print("  • cost_tracking_roi_analysis - Return on investment")
            print("  • cost_tracking_token_efficiency - Token cost efficiency")
            print("  • cost_tracking_anomaly_detection - Anomaly detection")

            print("\n🛠️  Available stored procedures:")
            print("  • get_cost_summary(start_date, end_date) - Cost summary")
            print("  • get_model_cost_comparison(days_back) - Model comparison")
            print("  • calculate_cost_forecast(days) - Cost forecasting")

            print("\n📊 Sample queries:")
            print("  SELECT * FROM cost_tracking_summary WHERE analysis_date >= CURRENT_DATE - INTERVAL '7 days';")
            print("  SELECT * FROM get_model_cost_comparison(14);")
            print("  SELECT * FROM cost_tracking_budget_monitor;")

        else:
            print("❌ SETUP INCOMPLETE")
            print("\n🔧 Troubleshooting:")
            print("  1. Check database connection permissions")
            print("  2. Verify cost tracking migration completed")
            print("  3. Review error messages above")

        print("=" * 80)
        return 0

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        if conn:
            conn.close()
            print("\n📌 Database connection closed")


if __name__ == "__main__":
    sys.exit(main())