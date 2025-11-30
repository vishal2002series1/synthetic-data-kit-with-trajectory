"""
Check diversity of training queries.

Measures:
- Unique queries
- Query similarity (simple word overlap)
- Persona distribution
- Complexity distribution
"""

import sys
from pathlib import Path
from collections import Counter

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import read_jsonl


def check_diversity(file_path: Path) -> dict:
    """Check query diversity."""
    
    print(f"\n{'='*60}")
    print(f"DIVERSITY ANALYSIS: {file_path.name}")
    print(f"{'='*60}\n")
    
    # Load data
    examples = read_jsonl(file_path)
    print(f"Analyzing {len(examples)} examples\n")
    
    # Extract queries
    queries = [ex.get('Q', '') for ex in examples]
    transformed_queries = [ex.get('transformed_query', '') for ex in examples]
    
    # Count unique
    unique_queries = set(queries)
    unique_transformed = set(transformed_queries) if any(transformed_queries) else set()
    
    # Extract metadata
    personas = []
    complexities = []
    
    for ex in examples:
        metadata = ex.get('metadata', {})
        if 'persona' in metadata or 'persona' in ex:
            personas.append(metadata.get('persona') or ex.get('persona'))
        if 'complexity' in metadata or 'complexity' in ex:
            complexities.append(metadata.get('complexity') or ex.get('complexity'))
    
    # Report
    print("🔍 DIVERSITY METRICS")
    print("-" * 60)
    
    print(f"\n📊 Query Uniqueness:")
    print(f"  Total examples: {len(examples)}")
    print(f"  Unique queries: {len(unique_queries)}")
    print(f"  Duplication rate: {(1 - len(unique_queries)/len(examples))*100:.1f}%")
    
    if unique_transformed:
        print(f"  Unique transformed queries: {len(unique_transformed)}")
    
    if personas:
        print(f"\n👥 Persona Distribution:")
        persona_counts = Counter(personas)
        for persona, count in sorted(persona_counts.items()):
            pct = (count / len(personas)) * 100
            print(f"  {persona}: {count} ({pct:.1f}%)")
    
    if complexities:
        print(f"\n📈 Complexity Distribution:")
        complexity_counts = Counter(complexities)
        for comp, count in sorted(complexity_counts.items()):
            pct = (count / len(complexities)) * 100
            print(f"  {comp}: {count} ({pct:.1f}%)")
    
    # Assessment
    print(f"\n{'='*60}")
    print("✅ DIVERSITY ASSESSMENT")
    print("="*60)
    
    if len(unique_queries) / len(examples) > 0.8:
        print("✅ High query diversity (>80% unique)")
    elif len(unique_queries) / len(examples) > 0.5:
        print("⚠️  Moderate query diversity (50-80% unique)")
    else:
        print("❌ Low query diversity (<50% unique)")
    
    if personas and len(set(personas)) >= 5:
        print("✅ Good persona coverage (5+ personas)")
    
    if complexities and len(set(complexities)) >= 3:
        print("✅ Good complexity coverage (3+ levels)")
    
    return {
        'total_examples': len(examples),
        'unique_queries': len(unique_queries),
        'diversity_rate': len(unique_queries) / len(examples),
        'persona_distribution': dict(Counter(personas)) if personas else {},
        'complexity_distribution': dict(Counter(complexities)) if complexities else {}
    }


def main():
    """Main diversity check function."""
    
    if len(sys.argv) < 2:
        print("Usage: python scripts/check_diversity.py <file.jsonl>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    check_diversity(file_path)
    print()


if __name__ == "__main__":
    main()
