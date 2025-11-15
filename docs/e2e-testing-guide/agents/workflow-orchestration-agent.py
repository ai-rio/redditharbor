#!/usr/bin/env python3
"""
RedditHarbor Enhanced Chunk Workflow Orchestration Agent

This agent orchestrates multi-agent workflows for comprehensive chunk analysis,
coordination between different agents, and automated pipeline execution.
"""

import json
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import argparse


@dataclass
class WorkflowStep:
    """Individual workflow step definition"""
    step_id: str
    agent_name: str
    action: str
    parameters: Dict[str, Any]
    dependencies: List[str]
    timeout: int
    retry_count: int
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class WorkflowExecution:
    """Complete workflow execution record"""
    workflow_id: str
    name: str
    timestamp: str
    steps: List[WorkflowStep]
    overall_status: str
    total_execution_time: float
    success_count: int
    failure_count: int
    summary: Dict[str, Any]


class WorkflowOrchestrationAgent:
    """Multi-agent workflow orchestration and coordination"""

    def __init__(self, agents_dir: Optional[Path] = None, results_dir: Optional[Path] = None):
        """Initialize the workflow orchestration agent"""
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.agents_dir = agents_dir or Path(__file__).parent
        self.results_dir = results_dir or Path(__file__).parent.parent / "results"

        # Ensure results directory exists
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Available agents and their capabilities
        self.available_agents = {
            'chunk-analysis-agent': {
                'path': self.agents_dir / 'chunk-analysis-agent.py',
                'actions': ['validate', 'process', 'collect', 'comprehensive'],
                'description': 'Analyzes chunk quality, structure, and metrics'
            },
            'results-collection-agent': {
                'path': self.agents_dir / 'results-collection-agent.py',
                'actions': ['comprehensive', 'metrics', 'e2e', 'basic'],
                'description': 'Collects and structures comprehensive results'
            },
            'quality-assessment-agent': {
                'path': self.agents_dir / 'quality-assessment-agent.py',
                'actions': ['assess', 'validate', 'improve'],
                'description': 'Performs quality assessment and improvement'
            }
        }

        print(f"🚀 Workflow Orchestration Agent Initialized")
        print(f"   Agents directory: {self.agents_dir}")
        print(f"   Results directory: {self.results_dir}")
        print(f"   Available agents: {len(self.available_agents)}")

    def execute_workflow(self, workflow_name: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a predefined workflow"""
        print(f"🎯 Starting workflow execution: {workflow_name}")

        # Get workflow definition
        workflow_def = self._get_workflow_definition(workflow_name)
        if not workflow_def:
            raise ValueError(f"Unknown workflow: {workflow_name}")

        # Initialize workflow execution
        workflow_id = f"{workflow_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        steps = self._create_workflow_steps(workflow_def, parameters or {})

        start_time = time.time()

        # Execute workflow steps
        executed_steps = self._execute_workflow_steps(steps, workflow_id)

        # Calculate execution metrics
        total_time = time.time() - start_time
        success_count = len([s for s in executed_steps if s.status == "completed"])
        failure_count = len([s for s in executed_steps if s.status == "failed"])

        # Determine overall status
        overall_status = "completed" if failure_count == 0 else "completed_with_errors" if success_count > 0 else "failed"

        # Generate workflow execution record
        workflow_execution = WorkflowExecution(
            workflow_id=workflow_id,
            name=workflow_name,
            timestamp=datetime.now().isoformat(),
            steps=executed_steps,
            overall_status=overall_status,
            total_execution_time=total_time,
            success_count=success_count,
            failure_count=failure_count,
            summary=self._generate_workflow_summary(executed_steps)
        )

        # Save workflow results
        self._save_workflow_results(workflow_execution)

        # Print workflow summary
        self._print_workflow_summary(workflow_execution)

        return asdict(workflow_execution)

    def _get_workflow_definition(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """Get predefined workflow definition"""
        workflows = {
            'comprehensive-analysis': {
                'description': 'Complete chunk analysis pipeline with all agents',
                'steps': [
                    {
                        'agent': 'chunk-analysis-agent',
                        'action': 'validate',
                        'parameters': {},
                        'dependencies': [],
                        'timeout': 300,
                        'retry_count': 1
                    },
                    {
                        'agent': 'results-collection-agent',
                        'action': 'comprehensive',
                        'parameters': {},
                        'dependencies': ['step-1'],
                        'timeout': 180,
                        'retry_count': 1
                    },
                    {
                        'agent': 'chunk-analysis-agent',
                        'action': 'comprehensive',
                        'parameters': {},
                        'dependencies': ['step-1'],
                        'timeout': 300,
                        'retry_count': 1
                    }
                ]
            },
            'e2e-testing': {
                'description': 'End-to-end testing workflow for chunk validation',
                'steps': [
                    {
                        'agent': 'chunk-analysis-agent',
                        'action': 'validate',
                        'parameters': {},
                        'dependencies': [],
                        'timeout': 300,
                        'retry_count': 2
                    },
                    {
                        'agent': 'results-collection-agent',
                        'action': 'e2e',
                        'parameters': {},
                        'dependencies': ['step-1'],
                        'timeout': 180,
                        'retry_count': 1
                    }
                ]
            },
            'quality-assessment': {
                'description': 'Quality assessment and improvement workflow',
                'steps': [
                    {
                        'agent': 'chunk-analysis-agent',
                        'action': 'validate',
                        'parameters': {},
                        'dependencies': [],
                        'timeout': 300,
                        'retry_count': 1
                    },
                    {
                        'agent': 'results-collection-agent',
                        'action': 'metrics',
                        'parameters': {},
                        'dependencies': ['step-1'],
                        'timeout': 180,
                        'retry_count': 1
                    }
                ]
            },
            'quick-validation': {
                'description': 'Quick validation workflow for basic checks',
                'steps': [
                    {
                        'agent': 'chunk-analysis-agent',
                        'action': 'validate',
                        'parameters': {},
                        'dependencies': [],
                        'timeout': 180,
                        'retry_count': 1
                    }
                ]
            },
            'full-pipeline': {
                'description': 'Complete pipeline with all analysis types',
                'steps': [
                    {
                        'agent': 'chunk-analysis-agent',
                        'action': 'validate',
                        'parameters': {},
                        'dependencies': [],
                        'timeout': 300,
                        'retry_count': 1
                    },
                    {
                        'agent': 'chunk-analysis-agent',
                        'action': 'process',
                        'parameters': {},
                        'dependencies': [],
                        'timeout': 300,
                        'retry_count': 1
                    },
                    {
                        'agent': 'chunk-analysis-agent',
                        'action': 'collect',
                        'parameters': {},
                        'dependencies': [],
                        'timeout': 300,
                        'retry_count': 1
                    },
                    {
                        'agent': 'results-collection-agent',
                        'action': 'comprehensive',
                        'parameters': {},
                        'dependencies': ['step-1', 'step-2', 'step-3'],
                        'timeout': 180,
                        'retry_count': 1
                    }
                ]
            }
        }

        return workflows.get(workflow_name)

    def _create_workflow_steps(self, workflow_def: Dict[str, Any], parameters: Dict[str, Any]) -> List[WorkflowStep]:
        """Create workflow step objects from definition"""
        steps = []
        for i, step_def in enumerate(workflow_def['steps'], 1):
            step = WorkflowStep(
                step_id=f"step-{i}",
                agent_name=step_def['agent'],
                action=step_def['action'],
                parameters={**step_def['parameters'], **parameters},
                dependencies=step_def['dependencies'],
                timeout=step_def['timeout'],
                retry_count=step_def['retry_count']
            )
            steps.append(step)

        return steps

    def _execute_workflow_steps(self, steps: List[WorkflowStep], workflow_id: str) -> List[WorkflowStep]:
        """Execute workflow steps with dependency resolution"""
        executed_steps = []

        for step in steps:
            # Check dependencies
            if not self._check_dependencies(step, executed_steps):
                step.status = "failed"
                step.error_message = "Dependencies not met"
                executed_steps.append(step)
                continue

            # Execute step with retries
            success = False
            for attempt in range(step.retry_count + 1):
                if attempt > 0:
                    print(f"🔄 Retrying step {step.step_id} (attempt {attempt + 1})")

                result = self._execute_agent_step(step)
                if result['success']:
                    step.status = "completed"
                    step.result = result['data']
                    step.execution_time = result['execution_time']
                    success = True
                    break
                else:
                    step.error_message = result['error']

            if not success:
                step.status = "failed"

            executed_steps.append(step)

            print(f"{'✅' if step.status == 'completed' else '❌'} Step {step.step_id}: {step.agent_name} - {step.action}")

        return executed_steps

    def _check_dependencies(self, step: WorkflowStep, executed_steps: List[WorkflowStep]) -> bool:
        """Check if step dependencies are satisfied"""
        if not step.dependencies:
            return True

        for dep in step.dependencies:
            dep_step = next((s for s in executed_steps if s.step_id == dep), None)
            if not dep_step or dep_step.status != "completed":
                return False

        return True

    def _execute_agent_step(self, step: WorkflowStep) -> Dict[str, Any]:
        """Execute a single agent step"""
        start_time = time.time()

        try:
            # Validate agent exists
            if step.agent_name not in self.available_agents:
                return {
                    'success': False,
                    'error': f"Unknown agent: {step.agent_name}",
                    'execution_time': time.time() - start_time
                }

            agent_info = self.available_agents[step.agent_name]

            # Build command
            cmd = ['python3', str(agent_info['path'])]

            # Add action-specific arguments
            if step.agent_name == 'chunk-analysis-agent':
                cmd.extend(['--action', step.action])
            elif step.agent_name == 'results-collection-agent':
                cmd.extend(['--collect', step.action])

            # Add parameters
            for param, value in step.parameters.items():
                if isinstance(value, bool):
                    if value:
                        cmd.append(f'--{param.replace("_", "-")}')
                else:
                    cmd.extend([f'--{param.replace("_", "-")}', str(value)])

            # Execute command with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=step.timeout,
                cwd=self.project_root
            )

            execution_time = time.time() - start_time

            if result.returncode == 0:
                return {
                    'success': True,
                    'data': {
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'command': ' '.join(cmd)
                    },
                    'execution_time': execution_time
                }
            else:
                return {
                    'success': False,
                    'error': f"Command failed with code {result.returncode}: {result.stderr}",
                    'execution_time': execution_time
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f"Command timed out after {step.timeout} seconds",
                'execution_time': time.time() - start_time
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Execution error: {str(e)}",
                'execution_time': time.time() - start_time
            }

    def _generate_workflow_summary(self, steps: List[WorkflowStep]) -> Dict[str, Any]:
        """Generate workflow execution summary"""
        completed_steps = [s for s in steps if s.status == "completed"]
        failed_steps = [s for s in steps if s.status == "failed"]

        return {
            'total_steps': len(steps),
            'completed_steps': len(completed_steps),
            'failed_steps': len(failed_steps),
            'success_rate': len(completed_steps) / len(steps) if steps else 0.0,
            'total_execution_time': sum(s.execution_time for s in steps),
            'agents_used': list(set(s.agent_name for s in steps)),
            'actions_executed': [f"{s.agent_name}:{s.action}" for s in steps],
            'errors': [s.error_message for s in failed_steps if s.error_message],
            'recommendations': self._generate_workflow_recommendations(steps)
        }

    def _generate_workflow_recommendations(self, steps: List[WorkflowStep]) -> List[str]:
        """Generate workflow improvement recommendations"""
        recommendations = []
        failed_steps = [s for s in steps if s.status == "failed"]

        if failed_steps:
            recommendations.append(f"Review and fix {len(failed_steps)} failed workflow steps")

        slow_steps = [s for s in steps if s.execution_time > 200]
        if slow_steps:
            recommendations.append(f"Optimize {len(slow_steps)} slow-performing steps")

        if len(steps) > 5:
            recommendations.append("Consider breaking down workflow into smaller, manageable pipelines")

        return recommendations

    def _save_workflow_results(self, workflow_execution: WorkflowExecution):
        """Save workflow execution results"""
        try:
            # Save detailed results
            results_file = self.results_dir / f"workflow-execution-{workflow_execution.workflow_id}.json"
            with open(results_file, 'w') as f:
                json.dump(asdict(workflow_execution), f, indent=2, default=str)
            print(f"📊 Workflow results saved: {results_file}")

            # Save summary
            summary_file = self.results_dir / f"workflow-summary-{workflow_execution.workflow_id}.json"
            summary_data = {
                'workflow_id': workflow_execution.workflow_id,
                'name': workflow_execution.name,
                'timestamp': workflow_execution.timestamp,
                'overall_status': workflow_execution.overall_status,
                'total_execution_time': workflow_execution.total_execution_time,
                'success_count': workflow_execution.success_count,
                'failure_count': workflow_execution.failure_count,
                'summary': workflow_execution.summary
            }
            with open(summary_file, 'w') as f:
                json.dump(summary_data, f, indent=2, default=str)
            print(f"📋 Workflow summary saved: {summary_file}")

        except Exception as e:
            print(f"⚠️ Warning: Could not save workflow results: {e}")

    def _print_workflow_summary(self, workflow_execution: WorkflowExecution):
        """Print workflow execution summary"""
        print(f"\n🎯 Workflow Execution Summary")
        print(f"=" * 50)
        print(f"Workflow ID: {workflow_execution.workflow_id}")
        print(f"Name: {workflow_execution.name}")
        print(f"Status: {workflow_execution.overall_status}")
        print(f"Total execution time: {workflow_execution.total_execution_time:.2f}s")
        print(f"Success rate: {workflow_execution.success_count}/{len(workflow_execution.steps)} steps")

        if workflow_execution.summary:
            summary = workflow_execution.summary
            print(f"\n📊 Metrics:")
            print(f"   Total steps: {summary['total_steps']}")
            print(f"   Completed: {summary['completed_steps']}")
            print(f"   Failed: {summary['failed_steps']}")
            print(f"   Success rate: {summary['success_rate']:.1%}")
            print(f"   Total time: {summary['total_execution_time']:.2f}s")

            print(f"\n🤖 Agents used: {', '.join(summary['agents_used'])}")

            if summary['errors']:
                print(f"\n⚠️ Errors encountered:")
                for error in summary['errors'][:3]:
                    print(f"   - {error}")

            if summary['recommendations']:
                print(f"\n💡 Recommendations:")
                for rec in summary['recommendations']:
                    print(f"   - {rec}")

    def list_available_workflows(self) -> List[str]:
        """List all available workflows"""
        return ['comprehensive-analysis', 'e2e-testing', 'quality-assessment', 'quick-validation', 'full-pipeline']

    def list_available_agents(self) -> Dict[str, Dict[str, Any]]:
        """List all available agents with their capabilities"""
        return self.available_agents


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='RedditHarbor Enhanced Chunk Workflow Orchestration Agent')
    parser.add_argument('workflow', nargs='?', help='Workflow name to execute')
    parser.add_argument('--list-workflows', action='store_true', help='List available workflows')
    parser.add_argument('--list-agents', action='store_true', help='List available agents')
    parser.add_argument('--agents-dir', type=str, help='Path to agents directory')
    parser.add_argument('--results-dir', type=str, help='Path to results directory')
    parser.add_argument('--param', action='append', help='Parameters in key=value format', nargs=2, metavar=('KEY', 'VALUE'))

    args = parser.parse_args()

    # Handle listing commands
    if args.list_workflows or args.list_agents:
        agent = WorkflowOrchestrationAgent()
        if args.list_workflows:
            workflows = agent.list_available_workflows()
            print("Available workflows:")
            for workflow in workflows:
                print(f"  - {workflow}")
        if args.list_agents:
            agents = agent.list_available_agents()
            print("\nAvailable agents:")
            for name, info in agents.items():
                print(f"  - {name}: {info['description']}")
        return True

    # Check if workflow is provided
    if not args.workflow:
        parser.error("workflow is required unless using --list-workflows or --list-agents")

    try:
        print("RedditHarbor Enhanced Chunk Workflow Orchestration Agent")
        print("=" * 60)
        print("")

        # Parse parameters
        parameters = {}
        if args.param:
            for key, value in args.param:
                parameters[key] = value

        # Initialize paths
        agents_dir = Path(args.agents_dir) if args.agents_dir else None
        results_dir = Path(args.results_dir) if args.results_dir else None

        # Initialize and execute workflow
        agent = WorkflowOrchestrationAgent(agents_dir=agents_dir, results_dir=results_dir)
        results = agent.execute_workflow(args.workflow, parameters)

        success = results['overall_status'] in ['completed', 'completed_with_errors']
        print(f"\n🎉 Workflow execution completed successfully!" if success else f"\n❌ Workflow execution failed!")
        return success

    except Exception as e:
        import traceback
        print(f"❌ Workflow execution failed: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)