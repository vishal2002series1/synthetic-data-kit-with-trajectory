"""
Analyze training data quality.

Metrics:
- COT length distribution
- Decision type distribution
- Tool usage patterns
- Iteration distribution
- Query complexity
"""

import sys
import json
from pathlib import Path
from collections import Counter
import statistics

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import read_jsonl


def analyze_quality(file_path: Path) -> dict:
    """Analyze training data quality metrics."""
    
    print(f"\n{'='*60}")
    print(f"QUALITY ANALYSIS: {file_path.name}")
    print(f"{'='*60}\n")
    
    # Load data
    examples = read_jsonl(file_path)
    print(f"Analyzing {len(examples)} examples\n")
    
    # Extract metrics
    cot_lengths = []
    decision_types = []
    tool_counts = []
    iterations = []
    query_lengths = []
    
    for ex in examples:
        # COT length
        cot = ex.get('COT', '')
        cot_lengths.append(len(cot))
        
        # Decision type
        decision = ex.get('Decision', '')
        if decision.startswith('CALL'):
            decision_types.append('CALL')
        elif decision.startswith('ASK'):
            decision_types.append('ASK')
        elif decision.startswith('ANSWER'):
            decision_types.append('ANSWER')
        else:
            decision_types.append('UNKNOWN')
        
        # Tool count
        tools = ex.get('Tool Set', [])
        tool_counts.append(len(tools))
        
        # Iteration
        metadata = ex.get('metadata', {})
        iterations.append(metadata.get('iteration', 0))
        
        # Query length
        query = ex.get('Q', '')
        query_lengths.append(len(query))
    
    # Calculate statistics
    report = {
        'total_examples': len(examples),
        'cot_length': {
            'mean': statistics.mean(cot_lengths) if cot_lengths else 0,
            'median': statistics.median(cot_lengths) if cot_lengths else 0,
            'min': min(cot_lengths) if cot_lengths else 0,
            'max': max(cot_lengths) if cot_lengths else 0
        },
        'decision_distribution': dict(Counter(decision_types)),
        'tool_usage': {
            'mean_tools_per_example': statistics.mean(tool_counts) if tool_counts else 0,
            'max_tools': max(tool_counts) if tool_counts else 0,
            'examples_with_tools': sum(1 for t in tool_counts if t > 0)
        },
        'iteration_distribution': dict(Counter(iterations)),
        'query_length': {
            'mean': statistics.mean(query_lengths) if query_lengths else 0,
            'median': statistics.median(query_lengths) if query_lengths else 0
        }
    }
    
    # Print report
    print("📊 QUALITY METRICS")
    print("-" * 60)
    
    print(f"\n📝 Chain of Thought (COT):")
    print(f"  Mean length: {report['cot_length']['mean']:.0f} chars")
    print(f"  Median: {report['cot_length']['median']:.0f} chars")
    print(f"  Range: {report['cot_length']['min']}-{report['cot_length']['max']} chars")
    
    print(f"\n🎯 Decision Types:")
    for dtype, count in report['decision_distribution'].items():
        pct = (count / len(examples)) * 100
        print(f"  {dtype}: {count} ({pct:.1f}%)")
    
    print(f"\n🔧 Tool Usage:")
    print(f"  Mean tools per example: {report['tool_usage']['mean_tools_per_example']:.2f}")
    print(f"  Max tools in example: {report['tool_usage']['max_tools']}")
    print(f"  Examples with tools: {report['tool_usage']['examples_with_tools']} ({report['tool_usage']['examples_with_tools']/len(examples)*100:.1f}%)")
    
    print(f"\n🔄 Iteration Distribution:")
    for iter_num in sorted(report['iteration_distribution'].keys()):
        count = report['iteration_distribution'][iter_num]
        pct = (count / len(examples)) * 100
        print(f"  Iteration {iter_num}: {count} ({pct:.1f}%)")
    
    print(f"\n❓ Query Complexity:")
    print(f"  Mean length: {report['query_length']['mean']:.0f} chars")
    print(f"  Median: {report['query_length']['median']:.0f} chars")
    
    # Quality assessment
    print(f"\n{'='*60}")
    print("✅ QUALITY ASSESSMENT")
    print("="*60)
    
    issues = []
    
    # Check COT length
    if report['cot_length']['mean'] < 50:
        issues.append("⚠️  COT is too short (should be >50 chars for good reasoning)")
    else:
        print("✅ COT length is good (sufficient reasoning)")
    
    # Check decision distribution
    if report['decision_distribution'].get('CALL', 0) == 0:
        issues.append("⚠️  No CALL decisions (should demonstrate tool usage)")
    else:
        print("✅ CALL decisions present (demonstrates tool usage)")
    
    # Check iterations
    max_iter = max(report['iteration_distribution'].keys()) if report['iteration_distribution'] else 0
    if max_iter > 0:
        print(f"✅ Multi-iteration examples present (up to iteration {max_iter})")
    else:
        issues.append("⚠️  No multi-iteration examples")
    
    if issues:
        print("\n⚠️  Issues found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n🎉 All quality checks passed!")
    
    return report


def main():
    """Main analysis function."""
    
    if len(sys.argv) < 2:
        print("Usage: python scripts/analyze_quality.py <file.jsonl>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    # Analyze
    report = analyze_quality(file_path)
    
    # Save report
    output_file = file_path.parent / f"{file_path.stem}_quality_report.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: {output_file}\n")


if __name__ == "__main__":
    main()
