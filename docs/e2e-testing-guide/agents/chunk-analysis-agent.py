#!/usr/bin/env python3
"""
RedditHarbor Enhanced Chunk Analysis Agent

General-purpose agent for analyzing enhanced documentation chunks,
performing semantic validation, agent integration assessment, and
structured results collection.

This agent combines RedditHarbor patterns with general-purpose
chunk analysis capabilities to provide comprehensive insights into documentation
chunking effectiveness and quality.
"""

import sys
import os
import json
import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class ChunkMetrics:
    """Metrics for chunk analysis"""
    chunk_id: str
    file_path: str
    line_count: int
    word_count: int
    section_count: int
    code_block_count: int
    table_count: int
    link_count: int
    semantic_coherence: float
    llm_optimization_score: float
    agent_integration_score: float
    quality_assurance_score: float
    complexity_level: str
    semantic_theme: str

@dataclass
class AgentIntegration:
    """Agent integration analysis results"""
    chunk_id: str
    agents_detected: List[str]
    integration_quality: float
    missing_references: List[str]
    functional_integration: float
    performance_metrics: Dict[str, Any]

class ChunkAnalysisAgent:
    """General-purpose agent for enhanced chunk analysis and testing"""

    def __init__(self, chunks_dir: str = None):
        """
        Initialize the chunk analysis agent

        Args:
            chunks_dir: Directory containing enhanced chunks
        """
        self.chunks_dir = Path(chunks_dir or "docs/enhanced-chunks/chunks")
        self.results_dir = Path("docs/enhanced-chunks/results")
        self.agents_dir = Path("docs/enhanced-chunks/agents")
        self.analysis_cache = {}
        self.results_log = []

        # Ensure results directory exists
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.agents_dir.mkdir(parents=True, exist_ok=True)

    def analyze_all_chunks(self, action: str = "validate") -> Dict[str, Any]:
        """
        Analyze all enhanced chunks based on specified action

        Args:
            action: Analysis action (validate, process, collect)

        Returns:
            Comprehensive analysis results
        """
        print(f"🔍 Starting chunk analysis: {action}")
        print(f"Chunks directory: {self.chunks_dir}")
        print(f"Results directory: {self.results_dir}")
        print("")

        # Discover chunk files
        chunk_files = self._discover_chunk_files()
        print(f"Found {len(chunk_files)} enhanced chunks to analyze")

        if not chunk_files:
            return {'success': False, 'error': 'No chunks found to analyze', 'results': []}

        # Analyze each chunk
        analysis_results = []
        overall_metrics = {
            'total_chunks': len(chunk_files),
            'analysis_action': action,
            'timestamp': datetime.now().isoformat()
        }

        for i, chunk_file in enumerate(chunk_files, 1):
            print(f"\n📝 Analyzing chunk {i}/{len(chunk_files)}: {chunk_file.name}")

            try:
                # Load chunk content
                content = self._load_chunk_content(chunk_file)

                # Perform analysis based on action
                if action == "validate":
                    result = self._validate_chunk_content(content, chunk_file)
                elif action == "process":
                    result = self._process_chunk_content(content, chunk_file)
                elif action == "collect":
                    result = self._collect_chunk_metrics(content, chunk_file)
                else:
                    result = self._comprehensive_analysis(content, chunk_file)

                # Enhance result with metadata
                result['file_info'] = {
                    'name': chunk_file.name,
                    'path': str(chunk_file),
                    'size': chunk_file.stat().st_size,
                    'modified': datetime.fromtimestamp(chunk_file.stat().st_mtime).isoformat()
                }

                analysis_results.append(result)
                print(f"✅ Analysis completed: {result['chunk_id']}")
                print(f"   Quality Score: {result.get('overall_score', 0):.2f}")
                print(f"   Coherence: {result.get('semantic_coherence', 0):.2f}")
                print(f"   LLM Score: {result.get('llm_optimization_score', 0):.2f}")

            except Exception as e:
                error_msg = f"Failed to analyze chunk {chunk_file.name}: {e}"
                print(f"❌ {error_msg}")
                analysis_results.append({
                    'chunk_id': chunk_file.stem,
                    'file_info': {
                        'name': chunk_file.name,
                        'path': str(chunk_file),
                        'error': True
                    },
                    'success': False,
                    'error': str(e),
                    'overall_score': 0.0
                })

        # Calculate overall metrics
        overall_metrics.update(self._calculate_overall_metrics(analysis_results))

        # Generate comprehensive report
        report = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'chunks_analyzed': len(chunk_files),
            'analysis_results': analysis_results,
            'overall_metrics': overall_metrics,
            'summary': self._generate_analysis_summary(analysis_results, overall_metrics)
        }

        # Save results
        self._save_analysis_results(report, action)

        print(f"\n✅ Chunk analysis completed!")
        print(f"Chunks analyzed: {len(analysis_results)}")
        print(f"Average score: {report['overall_metrics'].get('average_score', 0):.2f}")
        print(f"Quality distribution: {report['overall_metrics'].get('quality_distribution', {})}")

        return report

    def _discover_chunk_files(self) -> List[Path]:
        """Discover all enhanced chunk files"""
        chunk_files = []

        # Look for enhanced chunk files
        for chunk_file in self.chunks_dir.glob("enhanced-*-guide-chunk-*.md"):
            chunk_files.append(chunk_file)

        # Also include semantic index
        semantic_index = self.chunks_dir / "enhanced-e2e-semantic-index.md"
        if semantic_index.exists():
            chunk_files.append(semantic_index)

        return sorted(chunk_files)

    def _load_chunk_content(self, chunk_file: Path) -> str:
        """Load content from chunk file"""
        try:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to load chunk content from {chunk_file}: {e}")

    def _validate_chunk_content(self, content: str, chunk_file: Path) -> Dict[str, Any]:
        """Validate chunk content quality and structure"""
        result = {
            'chunk_id': chunk_file.stem,
            'validation_type': 'quality_check',
            'success': True,
            'overall_score': 0.0,
            'semantic_coherence': 0.0,
            'llm_optimization_score': 0.0,
            'agent_integration_score': 0.0,
            'quality_assurance_score': 0.0,
            'issues_found': [],
            'recommendations': []
        }

        lines = content.split('\n')

        # Calculate basic metrics
        result.update({
            'line_count': len(lines),
            'word_count': len(content.split()),
            'section_count': len([l for l in lines if l.strip().startswith('#')]),
            'code_block_count': len(re.findall(r'```', content)) // 2,
            'table_count': len([l for l in lines if '|' in l and l.strip().count('|') >= 2]),
            'link_count': len(re.findall(r'\[([^\]]+)\]\([^)]+\)', content))
        })

        # Semantic coherence check
        if 'Semantic Chunk' in content and 'Generated:' in content:
            result['semantic_coherence'] = 0.5

        if 'Chunk Overview' in content and '🎯' in content:
            result['semantic_coherence'] += 0.3

        if 'Agent Integration' in content and '🤖' in content:
            result['semantic_coherence'] += 0.2

        # LLM optimization check
        word_count = result['word_count']
        if word_count > 0:
            optimal_range = (1500, 3500)  # Optimal words for LLM processing
            if optimal_range[0] <= word_count <= optimal_range[1]:
                result['llm_optimization_score'] = 1.0
            elif word_count < optimal_range[0]:
                result['llm_optimization_score'] = word_count / optimal_range[0]
            else:
                result['llm_optimization_score'] = max(0, 1.0 - (word_count - optimal_range[1]) / 5000)

        # Agent integration check
        agent_sections = re.findall(r'### [A-Za-z_]+ Agent', content)
        if agent_sections:
            result['agent_integration_score'] = min(len(agent_sections) / 3, 1.0)

        # Quality assurance check
        structure_indicators = [
            '## 🎯 Chunk Overview' in content,
            '## 🤖 Agent Integration' in content,
            '## 🔧 Doit Integration' in content,
            '## 📖 Content' in content or 'Content' in content
        ]
        result['quality_assurance_score'] = sum(structure_indicators) / len(structure_indicators)

        # Calculate overall score
        weights = {
            'semantic_coherence': 0.3,
            'llm_optimization_score': 0.3,
            'agent_integration_score': 0.2,
            'quality_assurance_score': 0.2
        }

        result['overall_score'] = sum(
            result[metric] * weight for metric, weight in weights.items()
        )

        # Identify issues and recommendations
        if result['semantic_coherence'] < 0.5:
            result['issues_found'].append("Low semantic coherence detected")
            result['recommendations'].append("Add semantic structure and headers")

        if result['llm_optimization_score'] < 0.7:
            result['issues_found'].append("Suboptimal LLM processing size")
            result['recommendations'].append("Adjust content to optimal word count")

        if result['agent_integration_score'] < 0.3:
            result['issues_found'].append("Limited agent integration")
            result['recommendations'].append("Add more agent integration points")

        if result['quality_assurance_score'] < 0.6:
            result['issues_found'].append("Structure inconsistencies found")
            result['recommendations'].append("Improve documentation structure")

        # Determine success
        result['success'] = (
            len(result['issues_found']) == 0 and
            result['overall_score'] >= 0.6
        )

        return result

    def _process_chunk_content(self, content: str, chunk_file: Path) -> Dict[str, Any]:
        """Process chunk content for improvements and optimizations"""
        result = {
            'chunk_id': chunk_file.stem,
            'processing_type': 'optimization',
            'success': True,
            'original_metrics': {},
            'processed_metrics': {},
            'improvements_made': [],
            'optimizations_applied': []
        }

        # Calculate original metrics
        lines = content.split('\n')
        result['original_metrics'] = {
            'line_count': len(lines),
            'word_count': len(content.split()),
            'code_block_count': len(re.findall(r'```', content)) / 2,
            'section_count': len([l for l in lines if l.strip().startswith('#')])
        }

        # Apply optimizations
        processed_content = content

        # Add navigation improvements
        if '## Navigation' not in processed_content:
            navigation_section = [
                "",
                "## Navigation",
                "",
                "### Chunk Navigation",
                "",
                "- [📚 Enhanced Chunks Index](enhanced-e2e-semantic-index.md)",
                "- [🔍 Analysis Results](../results/chunk-metrics.json)",
                "- [🤖 Agent Integration](../agents/)",
                "",
            ]
            # Insert before content
            processed_content = '\n'.join(navigation_section + [processed_content])

        # Add metadata improvements
        if 'Content Hash:' not in processed_content:
            content_hash = hashlib.md5(processed_content.encode()).hexdigest()[:8]
            metadata_improvement = f"\n\n**Content Hash:** {content_hash}\n"
            # Insert after header section
            header_end = processed_content.find('\n---\n')
            if header_end != -1:
                processed_content = processed_content[:header_end] + metadata_improvement + processed_content[header_end:]

        # Calculate processed metrics
        processed_lines = processed_content.split('\n')
        result['processed_metrics'] = {
            'line_count': len(processed_lines),
            'word_count': len(processed_content.split()),
            'code_block_count': len(re.findall(r'```', processed_content)) / 2,
            'section_count': len([l for l in processed_lines if l.strip().startswith('#')])
        }

        # Identify improvements made
        if result['processed_metrics']['section_count'] > result['original_metrics']['section_count']:
            result['improvements_made'].append(f"Added {result['processed_metrics']['section_count'] - result['original_metrics']['section_count']} sections")

        if len(processed_content) > len(content):
            result['improvements_made'].append("Added navigation section")
            result['optimizations_applied'].append("Enhanced with navigation structure")

        # Save processed content
        try:
            with open(chunk_file, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            print(f"   📝 Processed content saved to {chunk_file.name}")
        except Exception as e:
            print(f"   ⚠️ Warning: Could not save processed content: {e}")

        result['success'] = True
        return result

    def _collect_chunk_metrics(self, content: str, chunk_file: Path) -> Dict[str, Any]:
        """Collect structured metrics for the chunk"""
        result = {
            'chunk_id': chunk_file.stem,
            'collection_type': 'metrics_gathering',
            'timestamp': datetime.now().isoformat(),
            'content_hash': hashlib.md5(content.encode()).hexdigest(),
            'metrics': {},
            'agent_integrations': {},
            'content_analysis': {},
            'quality_indicators': {}
        }

        lines = content.split('\n')

        # Basic metrics
        result['metrics'] = {
            'line_count': len(lines),
            'word_count': len(content.split()),
            'char_count': len(content),
            'section_count': len([l for l in lines if l.strip().startswith('#')]),
            'code_block_count': len(re.findall(r'```', content)) // 2,
            'table_count': len([l for l in lines if '|' in l and l.strip().count('|') >= 2]),
            'link_count': len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)),
            'list_count': len(re.findall(r'^\s*[-*+]\s+', content, re.MULTILINE))
        }

        # Agent integration analysis
        agent_sections = re.findall(r'### ([A-Za-z_]+) Agent', content)
        result['agent_integrations'] = {
            'agents_detected': agent_sections,
            'agent_count': len(agent_sections),
            'integration_density': len(agent_sections) / max(len(lines) / 100, 1)
        }

        # Content analysis
        result['content_analysis'] = {
            'has_metadata': 'Enhanced Semantic Chunk' in content,
            'has_agent_section': 'Agent Integration' in content,
            'has_doit_section': 'Doit Integration' in content,
            'has_quality_section': 'Quality' in content or 'Validation' in content,
            'executive_summary_length': len(content.split('\n')[0:20])  # First 20 lines
        }

        # Quality indicators
        result['quality_indicators'] = {
            'structure_score': 0.0,
            'readability_score': 0.0,
            'completeness_score': 0.0,
            'technical_accuracy': 0.0
        }

        # Calculate quality scores
        structure_indicators = [
            result['content_analysis']['has_metadata'],
            result['content_analysis']['has_agent_section'],
            result['content_analysis']['has_doit_section'],
            result['content_analysis']['has_quality_section']
        ]
        result['quality_indicators']['structure_score'] = sum(structure_indicators) / len(structure_indicators)

        # Readability assessment
        avg_line_length = sum(len(line.strip()) for line in lines if line.strip()) / len([l for l in lines if l.strip()])
        if avg_line_length < 100:
            result['quality_indicators']['readability_score'] = 1.0
        elif avg_line_length < 150:
            result['quality_indicators']['readability_score'] = 0.8
        else:
            result['quality_indicators']['readability_score'] = 0.5

        # Completeness assessment
        completeness_items = [
            result['metrics']['section_count'] >= 3,
            result['metrics']['code_block_count'] >= 1,
            result['metrics']['link_count'] >= 5
        ]
        result['quality_indicators']['completeness_score'] = sum(completeness_items) / len(completeness_items)

        result['success'] = True
        return result

    def _comprehensive_analysis(self, content: str, chunk_file: Path) -> Dict[str, Any]:
        """Perform comprehensive analysis combining all analysis types"""
        # This would combine validation, processing, and collection
        validation = self._validate_chunk_content(content, chunk_file)
        collection = self._collect_chunk_metrics(content, chunk_file)

        return {
            'chunk_id': chunk_file.stem,
            'analysis_type': 'comprehensive',
            'validation': validation,
            'collection': collection,
            'success': validation['success'],
            'overall_score': validation['overall_score'],
            'detailed_insights': {
                'quality_tier': self._determine_quality_tier(validation['overall_score']),
                'optimization_needs': self._identify_optimization_needs(validation),
                'agent_integration_status': self._assess_agent_integration_status(validation, collection)
            }
        }

    def _determine_quality_tier(self, score: float) -> str:
        """Determine quality tier based on score"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.7:
            return "good"
        elif score >= 0.5:
            return "fair"
        else:
            return "needs_improvement"

    def _identify_optimization_needs(self, validation: Dict[str, Any]) -> List[str]:
        """Identify optimization needs based on validation"""
        needs = []

        if validation.get('semantic_coherence', 0) < 0.7:
            needs.append("Improve semantic structure and coherence")

        if validation.get('llm_optimization_score', 0) < 0.7:
            needs.append("Optimize content for LLM processing")

        if validation.get('agent_integration_score', 0) < 0.5:
            needs.append("Enhance agent integration")

        if validation.get('quality_assurance_score', 0) < 0.6:
            needs.append("Improve documentation structure")

        return needs

    def _assess_agent_integration_status(self, validation: Dict[str, Any], collection: Dict[str, Any]) -> str:
        """Assess overall agent integration status"""
        agent_score = validation.get('agent_integration_score', 0)
        agent_count = collection.get('agent_integrations', {}).get('agent_count', 0)

        if agent_score >= 0.7 and agent_count >= 2:
            return "well_integrated"
        elif agent_score >= 0.5 and agent_count >= 1:
            return "partially_integrated"
        elif agent_count >= 1:
            return "minimal_integration"
        else:
            return "no_integration"

    def _calculate_overall_metrics(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall metrics from analysis results"""
        if not analysis_results:
            return {}

        scores = [r.get('overall_score', 0) for r in analysis_results if r.get('overall_score') is not None]
        coherence_scores = [r.get('semantic_coherence', 0) for r in analysis_results if r.get('semantic_coherence') is not None]
        llm_scores = [r.get('llm_optimization_score', 0) for r in analysis_results if r.get('llm_optimization_score') is not None]

        quality_distribution = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
        for result in analysis_results:
            score = result.get('overall_score', 0)
            if score >= 0.9:
                quality_distribution['excellent'] += 1
            elif score >= 0.7:
                quality_distribution['good'] += 1
            elif score >= 0.5:
                quality_distribution['fair'] += 1
            else:
                quality_distribution['poor'] += 1

        return {
            'average_score': sum(scores) / len(scores) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'min_score': min(scores) if scores else 0,
            'average_coherence': sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0,
            'average_llm_optimization': sum(llm_scores) / len(llm_scores) if llm_scores else 0,
            'quality_distribution': quality_distribution,
            'total_chunks_analyzed': len(analysis_results),
            'successful_analyses': sum(1 for r in analysis_results if r.get('success', False))
        }

    def _generate_analysis_summary(self, analysis_results: List[Dict[str, Any]], overall_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis summary"""
        return {
            'analysis_status': 'completed',
            'total_chunks': len(analysis_results),
            'success_rate': overall_metrics.get('successful_analyses', 0) / len(analysis_results) if analysis_results else 0,
            'average_score': overall_metrics.get('average_score', 0),
            'quality_distribution': overall_metrics.get('quality_distribution', {}),
            'recommendations': self._generate_recommendations(analysis_results, overall_metrics),
            'next_steps': self._generate_next_steps(overall_metrics)
        }

    def _generate_recommendations(self, analysis_results: List[Dict[str, Any]], overall_metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis results"""
        recommendations = []

        # Analyze common issues
        low_score_chunks = [r for r in analysis_results if r.get('overall_score', 0) < 0.6]
        agent_integration_issues = [r for r in analysis_results if r.get('agent_integration_score', 0) < 0.5]

        if low_score_chunks:
            recommendations.append(f"Focus on improving {len(low_score_chunks)} chunks with scores below 0.6")

        if agent_integration_issues:
            recommendations.append(f"Enhance agent integration in {len(agent_integration_issues)} chunks")

        # Check for patterns
        if len(analysis_results) > 5:
            recommendations.append("Consider grouping related chunks for better organization")

        if overall_metrics.get('average_llm_optimization', 0) < 0.7:
            recommendations.append("Optimize chunk sizes for better LLM processing")

        return recommendations

    def _generate_next_steps(self, overall_metrics: Dict[str, Any]) -> List[str]:
        """Generate next steps based on analysis"""
        steps = []

        if overall_metrics.get('success_rate', 0) < 0.8:
            steps.append("Address quality issues in underperforming chunks")

        if overall_metrics.get('average_score', 0) >= 0.7:
            steps.append("Proceed with E2E testing scenarios")
            steps.append("Deploy chunks for production use")

        steps.append("Collect results for comprehensive reporting")
        steps.append("Set up continuous monitoring and validation")

        return steps

    def _save_analysis_results(self, report: Dict[str, Any], action: str):
        """Save analysis results to structured files"""
        try:
            # Save JSON report
            json_file = self.results_dir / f"chunk-analysis-report-{action}.json"
            with open(json_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"📊 Analysis report saved: {json_file}")

            # Save summary report
            summary_file = self.results_dir / f"analysis-summary-{action}.json"
            summary_data = {
                'timestamp': report['timestamp'],
                'action': action,
                'summary': report['summary'],
                'overall_metrics': report['overall_metrics']
            }
            with open(summary_file, 'w') as f:
                json.dump(summary_data, f, indent=2, default=str)
            print(f"📋 Summary saved: {summary_file}")

        except Exception as e:
            print(f"⚠️ Warning: Could not save analysis results: {e}")

def main():
    """Main execution function"""
    import sys

    try:
        print("RedditHarbor Enhanced Chunk Analysis Agent")
        print("=" * 60)
        print("")

        # Handle command line arguments
        action = 'comprehensive'  # default
        if len(sys.argv) > 1:
            if '--action' in sys.argv:
                try:
                    action_idx = sys.argv.index('--action') + 1
                    if action_idx < len(sys.argv):
                        action = sys.argv[action_idx]
                except (ValueError, IndexError):
                    pass
        else:
            # Fallback to interactive if no arguments provided
            print("Available Actions:")
            print("1. validate - Validate chunk quality and structure")
            print("2. process - Process and optimize chunks")
            print("3. collect - Collect comprehensive metrics")
            print("4. comprehensive - Perform all analysis types")
            print("")

            choice = input("Choose action (1-4): ").strip()

            action_map = {
                '1': 'validate',
                '2': 'process',
                '3': 'collect',
                '4': 'comprehensive'
            }

            action = action_map.get(choice, 'comprehensive')

        # Initialize and run analysis
        agent = ChunkAnalysisAgent()
        report = agent.analyze_all_chunks(action=action)

        print(f"\n📊 Analysis Results Summary:")
        print(f"   Action: {action}")
        print(f"   Chunks analyzed: {report['chunks_analyzed']}")
        print(f"   Success rate: {report['summary']['success_rate']:.1%}")
        print(f"   Average score: {report['overall_metrics']['average_score']:.2f}")

        if report['summary']['recommendations']:
            print(f"   Recommendations: {len(report['summary']['recommendations'])}")
            for rec in report['summary']['recommendations'][:3]:
                print(f"   - {rec}")

        # Success based on completion, not chunk quality
        # Analysis is successful if chunks were processed (regardless of quality)
        return report['overall_metrics']['total_chunks_analyzed'] > 0

    except Exception as e:
        import traceback
        print(f"❌ Chunk analysis failed: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)