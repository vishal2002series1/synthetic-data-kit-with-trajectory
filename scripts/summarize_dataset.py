"""
Generate comprehensive evaluation summary for entire dataset.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import read_jsonl


def summarize_dataset():
    """Generate comprehensive dataset summary."""
    
    print("\n" + "="*60)
    print("DATASET EVALUATION SUMMARY")
    print("="*60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Find all sample files
    samples_dir = Path("samples")
    
    if not samples_dir.exists():
        print("\n❌ Error: samples/ directory not found")
        return
    
    jsonl_files = sorted(samples_dir.glob("*.jsonl"))
    
    if not jsonl_files:
        print("\n❌ Error: No .jsonl files found in samples/")
        return
    
    print(f"\nFound {len(jsonl_files)} dataset files\n")
    
    # Analyze each file
    total_examples = 0
    file_summaries = []
    
    for file_path in jsonl_files:
        try:
            examples = read_jsonl(file_path)
            
            # Count decision types
            from collections import Counter
            decisions = []
            for ex in examples:
                decision = ex.get('Decision', '')
                if decision.startswith('CALL'):
                    decisions.append('CALL')
                elif decision.startswith('ASK'):
                    decisions.append('ASK')
                elif decision.startswith('ANSWER'):
                    decisions.append('ANSWER')
            
            decision_counts = Counter(decisions)
            
            file_summary = {
                'filename': file_path.name,
                'examples': len(examples),
                'size_kb': file_path.stat().st_size / 1024,
                'decisions': dict(decision_counts)
            }
            
            file_summaries.append(file_summary)
            total_examples += len(examples)
            
            print(f"📄 {file_path.name}")
            print(f"   Examples: {len(examples)}")
            print(f"   Size: {file_summary['size_kb']:.1f} KB")
            if decision_counts:
                print(f"   Decisions: {dict(decision_counts)}")
            print()
            
        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}\n")
    
    # Overall summary
    print("="*60)
    print("📊 OVERALL SUMMARY")
    print("="*60)
    print(f"\nTotal dataset files: {len(file_summaries)}")
    print(f"Total training examples: {total_examples}")
    
    total_size = sum(f['size_kb'] for f in file_summaries)
    print(f"Total size: {total_size:.1f} KB")
    
    # Aggregate decision counts
    all_decisions = Counter()
    for fs in file_summaries:
        for decision, count in fs.get('decisions', {}).items():
            all_decisions[decision] += count
    
    if all_decisions:
        print(f"\nDecision distribution across all datasets:")
        for decision, count in all_decisions.items():
            pct = (count / sum(all_decisions.values())) * 100
            print(f"  {decision}: {count} ({pct:.1f}%)")
    
    # Save summary
    summary = {
        'generated_at': datetime.now().isoformat(),
        'total_files': len(file_summaries),
        'total_examples': total_examples,
        'total_size_kb': total_size,
        'files': file_summaries,
        'decision_distribution': dict(all_decisions)
    }
    
    output_file = Path("samples/dataset_summary.json")
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 Summary saved to: {output_file}")
    print("="*60 + "\n")
    
    return summary


if __name__ == "__main__":
    summarize_dataset()
