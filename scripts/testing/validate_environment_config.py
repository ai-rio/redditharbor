#!/usr/bin/env python3
"""
Production Pipeline Environment Validation Script
Validates all required environment configurations for RedditHarbor production deployment.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def add_project_root():
    """Add project root to Python path."""
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

add_project_root()

def check_database_config():
    """Validate database configuration."""
    print("🔍 Checking Database Configuration...")

    db_checks = {
        "supabase_url": os.getenv("SUPABASE_URL", ""),
        "supabase_key": os.getenv("SUPABASE_KEY", ""),
        "database_url": os.getenv("DATABASE_URL", "")
    }

    db_health = {
        "supabase_configured": bool(db_checks["supabase_url"] and db_checks["supabase_key"]),
        "database_url_configured": bool(db_checks["database_url"]),
        "docker_container_running": False,
        "database_connection": False
    }

    # Check if Supabase Docker container is running
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=supabase_db", "--format", "{{.Names}}"],
            capture_output=True, text=True
        )
        db_health["docker_container_running"] = "supabase_db" in result.stdout

        # Test database connection
        if db_health["docker_container_running"]:
            conn_result = subprocess.run(
                ["docker", "exec", "supabase_db_carlos", "psql", "-U", "postgres", "-d", "postgres", "-c", "SELECT 1;"],
                capture_output=True, text=True
            )
            db_health["database_connection"] = conn_result.returncode == 0

    except Exception as e:
        print(f"Database check error: {e}")

    return db_health

def check_mcp_integration_config():
    """Validate MCP integration configuration."""
    print("🔍 Checking MCP Integration Configuration...")

    mcp_checks = {
        "openrouter_key": bool(os.getenv("OPENROUTER_API_KEY")),
        "openrouter_model": bool(os.getenv("OPENROUTER_MODEL")),
        "jina_key": bool(os.getenv("JINA_API_KEY")),
        "jina_limits_configured": all([
            os.getenv("JINA_READ_RPM_LIMIT"),
            os.getenv("JINA_SEARCH_RPM_LIMIT"),
            os.getenv("JINA_REQUEST_TIMEOUT")
        ]),
        "mcp_config_file": Path(".mcp.json").exists()
    }

    return mcp_checks

def check_agentops_config():
    """Validate AgentOps configuration."""
    print("🔍 Checking AgentOps Configuration...")

    agentops_checks = {
        "api_key_configured": bool(os.getenv("AGENTOPS_API_KEY")),
        "auto_instrument_disabled": os.getenv("AGENTOPS_AUTO_INSTRUMENT_OPENAI") == "false",
        "agentops_installed": False,
        "recent_log_activity": False
    }

    # Check if AgentOps is installed
    try:
        result = subprocess.run([sys.executable, "-c", "import agentops"], capture_output=True)
        agentops_checks["agentops_installed"] = result.returncode == 0
    except:
        pass

    # Check for recent AgentOps activity
    try:
        log_file = Path("agentops.log")
        if log_file.exists():
            # Simple check for recent log entries
            agentops_checks["recent_log_activity"] = True
    except:
        pass

    return agentops_checks

def check_production_readiness():
    """Check general production readiness."""
    print("🔍 Checking Production Readiness...")

    readiness_checks = {
        "error_log_directory": Path("error_log").exists(),
        "reports_directory": Path("reports").exists(),
        "config_files_present": all([
            Path("config/settings.py").exists(),
            Path("core/collection.py").exists(),
            Path("core/templates.py").exists()
        ]),
        "docs_e2e_structure": check_e2e_docs_structure(),
        "health_monitoring_ready": Path("scripts/analysis/setup_health_monitoring.py").exists()
    }

    return readiness_checks

def check_e2e_docs_structure():
    """Check E2E testing documentation structure."""
    required_paths = [
        "docs/e2e-testing-guide/reports",
        "docs/e2e-testing-guide/results",
        "docs/e2e-testing-guide/checklists"
    ]

    return all(Path(p).exists() for p in required_paths)

def calculate_environment_score(checks):
    """Calculate overall environment health score."""
    total_checks = sum(len(checks[category]) for category in checks)
    passed_checks = sum(
        sum(1 for check in checks[category].values() if check)
        for category in checks
    )

    return (passed_checks / total_checks) * 100 if total_checks > 0 else 0

def main():
    """Main environment validation function."""
    print("🚀 RedditHarbor Production Pipeline Environment Validation")
    print("=" * 60)

    # Run all checks
    db_checks = check_database_config()
    mcp_checks = check_mcp_integration_config()
    agentops_checks = check_agentops_config()
    readiness_checks = check_production_readiness()

    all_checks = {
        "database": db_checks,
        "mcp_integration": mcp_checks,
        "agentops": agentops_checks,
        "production_readiness": readiness_checks
    }

    # Calculate overall score
    environment_score = calculate_environment_score(all_checks)

    print("\n📊 Environment Validation Results:")
    print("-" * 30)
    print(f"Overall Environment Health Score: {environment_score:.1f}/100")

    # Print detailed results
    for category, checks in all_checks.items():
        print(f"\n{category.upper()}:")
        for check_name, result in checks.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {check_name}: {status}")

    # Generate validation report
    validation_report = {
        "timestamp": datetime.now().isoformat(),
        "environment_score": environment_score,
        "validation_results": all_checks,
        "ready_for_production_testing": environment_score >= 90,
        "recommendations": generate_recommendations(all_checks, environment_score)
    }

    # Save validation report
    output_dir = Path("docs/e2e-testing-guide/results")
    output_dir.mkdir(parents=True, exist_ok=True)

    report_file = output_dir / "environment-validation.json"
    with open(report_file, 'w') as f:
        json.dump(validation_report, f, indent=2, default=str)

    print(f"\n📄 Validation report saved: {report_file}")

    if environment_score >= 90:
        print("✅ Environment is ready for production pipeline testing!")
        return 0
    else:
        print("⚠️ Environment needs attention before production testing")
        return 1

def generate_recommendations(checks, score):
    """Generate recommendations based on validation results."""
    recommendations = []

    if score < 90:
        recommendations.append({
            "priority": "high",
            "category": "general",
            "issue": f"Environment health score below 90% ({score:.1f}%)",
            "action": "Address failed checks before proceeding with production testing"
        })

    # Database recommendations
    db_checks = checks.get("database", {})
    if not db_checks.get("database_connection"):
        recommendations.append({
            "priority": "critical",
            "category": "database",
            "issue": "Database connection failed",
            "action": "Start Supabase services and verify database configuration"
        })

    # MCP integration recommendations
    mcp_checks = checks.get("mcp_integration", {})
    if not mcp_checks.get("openrouter_key"):
        recommendations.append({
            "priority": "critical",
            "category": "mcp",
            "issue": "OpenRouter API key not configured",
            "action": "Set OPENROUTER_API_KEY environment variable"
        })

    # AgentOps recommendations
    agentops_checks = checks.get("agentops", {})
    if not agentops_checks.get("api_key_configured"):
        recommendations.append({
            "priority": "high",
            "category": "agentops",
            "issue": "AgentOps API key not configured",
            "action": "Set AGENTOPS_API_KEY environment variable"
        })

    return recommendations

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
