#!/usr/bin/env python3
"""
Real-time KPI monitoring script for Phase 2 Quality Validation
Tracks Tier 1 Business Value KPIs with alerting thresholds
"""

import psycopg2
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import os

class Phase2KpiMonitor:
    """Monitor Phase 2 KPIs in real-time"""

    def __init__(self):
        self.db_config = {
            'host': '127.0.0.1',
            'port': 54322,
            'user': 'postgres',
            'password': 'postgres',
            'database': 'postgres'
        }

        # KPI Thresholds
        self.kpi_thresholds = {
            'HIGH_SCORE_RATE': {
                'target': 30.0,
                'warning': 25.0,
                'critical': 20.0
            },
            'FUNCTION_COMPLIANCE': {
                'target': 100.0,
                'warning': 95.0,
                'critical': 90.0
            },
            'MARKET_VALIDATION': {
                'target': 90.0,
                'warning': 85.0,
                'critical': 80.0
            }
        }

        # Status colors for console output
        self.colors = {
            'PASS': '\033[92m',    # Green
            'WARNING': '\033[93m', # Yellow
            'FAIL': '\033[91m',    # Red
            'INFO': '\033[94m',    # Blue
            'RESET': '\033[0m'     # Reset
        }

    def get_db_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            print(f"{self.colors['FAIL']}ERROR: Could not connect to database: {e}{self.colors['RESET']}")
            return None

    def calculate_kpi_status(self, current_value: float, thresholds: Dict) -> Tuple[str, str]:
        """Calculate KPI status and color"""
        if current_value >= thresholds['target']:
            return 'PASS', self.colors['PASS']
        elif current_value >= thresholds['warning']:
            return 'WARNING', self.colors['WARNING']
        elif current_value >= thresholds['critical']:
            return 'WARNING', self.colors['WARNING']
        else:
            return 'FAIL', self.colors['FAIL']

    def get_high_score_rate(self, conn, time_hours: int = 24) -> Dict:
        """Calculate high-score rate KPI"""
        query = f"""
        SELECT
          COUNT(*) as total_opportunities,
          COUNT(CASE WHEN final_score >= 70 THEN 1 END) as high_score_count,
          CASE
            WHEN COUNT(*) > 0 THEN ROUND(COUNT(CASE WHEN final_score >= 70 THEN 1 END) * 100.0 / COUNT(*), 2)
            ELSE 0
          END as high_score_rate
        FROM opportunities
        WHERE created_at >= NOW() - INTERVAL '{time_hours} hours';
        """

        with conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchone()

            total, high_count, rate = result
            status, color = self.calculate_kpi_status(rate, self.kpi_thresholds['HIGH_SCORE_RATE'])

            return {
                'kpi': 'HIGH_SCORE_RATE',
                'total_opportunities': total,
                'high_score_count': high_count,
                'rate': rate,
                'status': status,
                'color': color,
                'target': self.kpi_thresholds['HIGH_SCORE_RATE']['target'],
                'threshold': self.kpi_thresholds['HIGH_SCORE_RATE']['warning']
            }

    def get_function_compliance(self, conn, time_hours: int = 24) -> Dict:
        """Calculate function compliance KPI"""
        query = f"""
        SELECT
          COUNT(*) as total_opportunities,
          COUNT(CASE WHEN jsonb_array_length(core_functions) <= 3 THEN 1 END) as compliant_count,
          CASE
            WHEN COUNT(*) > 0 THEN ROUND(COUNT(CASE WHEN jsonb_array_length(core_functions) <= 3 THEN 1 END) * 100.0 / COUNT(*), 2)
            ELSE 0
          END as compliance_rate
        FROM opportunities
        WHERE created_at >= NOW() - INTERVAL '{time_hours} hours'
          AND core_functions IS NOT NULL;
        """

        with conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchone()

            total, compliant, rate = result
            status, color = self.calculate_kpi_status(rate, self.kpi_thresholds['FUNCTION_COMPLIANCE'])

            return {
                'kpi': 'FUNCTION_COMPLIANCE',
                'total_opportunities': total,
                'compliant_count': compliant,
                'rate': rate,
                'status': status,
                'color': color,
                'target': self.kpi_thresholds['FUNCTION_COMPLIANCE']['target'],
                'threshold': self.kpi_thresholds['FUNCTION_COMPLIANCE']['warning']
            }

    def get_market_validation(self, conn, time_hours: int = 24) -> Dict:
        """Calculate market validation KPI"""
        query = f"""
        SELECT
          COUNT(*) as total_opportunities,
          COUNT(CASE WHEN jina_validation_status = 'completed' THEN 1 END) as validated_count,
          CASE
            WHEN COUNT(*) > 0 THEN ROUND(COUNT(CASE WHEN jina_validation_status = 'completed' THEN 1 END) * 100.0 / COUNT(*), 2)
            ELSE 0
          END as validation_rate
        FROM opportunities
        WHERE created_at >= NOW() - INTERVAL '{time_hours} hours'
          AND jina_validation_status IS NOT NULL;
        """

        with conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchone()

            total, validated, rate = result
            status, color = self.calculate_kpi_status(rate, self.kpi_thresholds['MARKET_VALIDATION'])

            return {
                'kpi': 'MARKET_VALIDATION',
                'total_opportunities': total,
                'validated_count': validated,
                'rate': rate,
                'status': status,
                'color': color,
                'target': self.kpi_thresholds['MARKET_VALIDATION']['target'],
                'threshold': self.kpi_thresholds['MARKET_VALIDATION']['warning']
            }

    def get_processing_metrics(self, conn, time_hours: int = 24) -> Dict:
        """Get processing performance metrics"""
        query = f"""
        SELECT
          COUNT(*) as opp_count,
          EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at))) as elapsed_seconds,
          COALESCE(SUM(jina_api_cost_usd), 0) as total_cost
        FROM opportunities
        WHERE created_at >= NOW() - INTERVAL '{time_hours} hours';
        """

        with conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchone()

            count, elapsed, cost = result
            throughput = round(count / elapsed * 3600, 2) if elapsed > 0 else 0

            return {
                'opportunities_processed': count,
                'elapsed_seconds': elapsed,
                'throughput_per_hour': throughput,
                'total_cost_usd': float(cost) if cost else 0.0,
                'avg_cost_per_opportunity': float(cost) / count if count > 0 and cost else 0.0
            }

    def get_pipeline_health(self, conn, time_hours: int = 24) -> Dict:
        """Get pipeline health metrics"""
        query = f"""
        SELECT
          phase,
          COUNT(*) as executions,
          AVG(duration_seconds) as avg_duration,
          COUNT(CASE WHEN success = false THEN 1 END) as errors,
          CASE
            WHEN COUNT(*) > 0 THEN ROUND(COUNT(CASE WHEN success = false THEN 1 END) * 100.0 / COUNT(*), 2)
            ELSE 0
          END as error_rate
        FROM pipeline_metrics
        WHERE created_at >= NOW() - INTERVAL '{time_hours} hours'
        GROUP BY phase
        ORDER BY executions DESC;
        """

        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()

            health_data = {}
            for phase, exec_count, avg_duration, errors, error_rate in results:
                health_data[phase] = {
                    'executions': exec_count,
                    'avg_duration': avg_duration,
                    'errors': errors,
                    'error_rate': error_rate,
                    'status': 'PASS' if error_rate < 5 else 'WARNING' if error_rate < 10 else 'FAIL'
                }

            return health_data

    def display_kpi_dashboard(self, kpis: List[Dict], metrics: Dict, health: Dict):
        """Display KPI dashboard in console"""
        print(f"\n{self.colors['INFO']}=== PHASE 2 QUALITY VALIDATION - REAL-TIME KPI DASHBOARD ==={self.colors['RESET']}")
        print(f"{self.colors['INFO']}Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{self.colors['RESET']}")
        print(f"{self.colors['INFO']}Time Window: Last 24 hours{self.colors['RESET']}")

        print(f"\n{self.colors['INFO']}--- TIER 1 BUSINESS VALUE KPIS ---{self.colors['RESET']}")
        print(f"{'KPI':<20} {'Current':<10} {'Target':<10} {'Status':<10} {'Details'}")
        print("-" * 70)

        for kpi in kpis:
            color = kpi['color']
            reset = self.colors['RESET']
            print(f"{color}{kpi['kpi']:<20}{reset} {color}{kpi['rate']:<10}{reset} {kpi['target']:<10} {color}{kpi['status']:<10}{reset} {kpi.get('total_opportunities', 0)} opportunities processed")

        print(f"\n{self.colors['INFO']}--- PROCESSING METRICS ---{self.colors['RESET']}")
        print(f"Throughput: {metrics['throughput_per_hour']:.2f} opportunities/hour")
        print(f"Total Cost: ${metrics['total_cost_usd']:.6f}")
        print(f"Avg Cost/Opportunity: ${metrics['avg_cost_per_opportunity']:.8f}")

        print(f"\n{self.colors['INFO']}--- PIPELINE HEALTH ---{self.colors['RESET']}")
        for phase, data in health.items():
            status_color = self.colors['PASS'] if data['status'] == 'PASS' else self.colors['WARNING'] if data['status'] == 'WARNING' else self.colors['FAIL']
            print(f"{phase:<12} - {status_color}{data['status']}{self.colors['RESET']} ({data['error_rate']:.1f}% error rate, {data['executions']} executions)")

        # Alert summary
        failed_kpis = [kpi for kpi in kpis if kpi['status'] == 'FAIL']
        warning_kpis = [kpi for kpi in kpis if kpi['status'] == 'WARNING']

        if failed_kpis:
            print(f"\n{self.colors['FAIL']}🚨 CRITICAL ALERTS:{self.colors['RESET']}")
            for kpi in failed_kpis:
                print(f"  • {kpi['kpi']}: {kpi['rate']}% (threshold: {kpi['threshold']}%)")

        if warning_kpis:
            print(f"\n{self.colors['WARNING']}⚠️  WARNINGS:{self.colors['RESET']}")
            for kpi in warning_kpis:
                print(f"  • {kpi['kpi']}: {kpi['rate']}% (target: {kpi['target']}%)")

        if not failed_kpis and not warning_kpis:
            print(f"\n{self.colors['PASS']}✅ ALL KPIS WITHIN ACCEPTABLE RANGES{self.colors['RESET']}")

    def monitor_loop(self, interval_minutes: int = 5):
        """Continuous monitoring loop"""
        print(f"{self.colors['INFO']}Starting Phase 2 KPI monitoring (refresh every {interval_minutes} minutes){self.colors['RESET']}")
        print(f"{self.colors['INFO']}Press Ctrl+C to stop{self.colors['RESET']}")

        try:
            while True:
                conn = self.get_db_connection()
                if conn:
                    try:
                        # Collect KPIs
                        kpis = [
                            self.get_high_score_rate(conn),
                            self.get_function_compliance(conn),
                            self.get_market_validation(conn)
                        ]

                        # Collect metrics
                        metrics = self.get_processing_metrics(conn)
                        health = self.get_pipeline_health(conn)

                        # Display dashboard
                        os.system('clear' if os.name == 'posix' else 'cls')
                        self.display_kpi_dashboard(kpis, metrics, health)

                    finally:
                        conn.close()
                else:
                    print(f"{self.colors['FAIL']}ERROR: Could not establish database connection{self.colors['RESET']}")

                # Wait for next iteration
                import time
                time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            print(f"\n{self.colors['INFO']}Monitoring stopped by user{self.colors['RESET']}")

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Monitor Phase 2 Quality Validation KPIs')
    parser.add_argument('--interval', type=int, default=5, help='Monitoring interval in minutes (default: 5)')
    parser.add_argument('--single', action='store_true', help='Run single check instead of continuous monitoring')

    args = parser.parse_args()

    monitor = Phase2KpiMonitor()

    if args.single:
        # Single run
        conn = monitor.get_db_connection()
        if conn:
            try:
                kpis = [
                    monitor.get_high_score_rate(conn),
                    monitor.get_function_compliance(conn),
                    monitor.get_market_validation(conn)
                ]
                metrics = monitor.get_processing_metrics(conn)
                health = monitor.get_pipeline_health(conn)
                monitor.display_kpi_dashboard(kpis, metrics, health)
            finally:
                conn.close()
        else:
            print("ERROR: Could not connect to database")
            sys.exit(1)
    else:
        # Continuous monitoring
        monitor.monitor_loop(args.interval)

if __name__ == '__main__':
    main()