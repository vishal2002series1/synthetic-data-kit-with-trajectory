"""Generate and save complete 30× expansion from seed queries."""

import sys
from pathlib import Path
from itertools import product

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils import setup_logger, load_config, get_logger, write_jsonl
from src.core import BedrockProvider
from src.transformations import PersonaTransformer, QueryModifier, ToolDataTransformer


def test_full_expansion():
    """Generate complete 30× expansion and save to file."""
    
    print("\n" + "="*60)
    print("FULL 30× EXPANSION - GENERATE & SAVE")
    print("="*60)
    
    setup_logger("INFO", "logs/test_full_expansion.log")
    config = load_config()
    
    # Initialize
    print("\n[1/4] Initializing transformers...")
    provider = BedrockProvider(
        model_id=config.bedrock.model_id,
        embedding_model_id=config.bedrock.embedding_model_id,
        region=config.bedrock.region
    )
    
    persona_tx = PersonaTransformer(provider)
    query_mod = QueryModifier(provider)
    tool_data_tx = ToolDataTransformer(provider)
    
    print(f"✅ Transformers ready (30× expansion)")
    
    # Seed queries
    seed_queries = [
        "How should I diversify my investment portfolio?",
        "What are the risks in my current portfolio?",
        "How can I optimize my asset allocation?"
    ]
    
    print(f"\n[2/4] Processing {len(seed_queries)} seed queries...")
    print("   (This will take 2-3 minutes...)\n")
    
    all_variants = []
    
    for seed_idx, seed_query in enumerate(seed_queries, 1):
        print(f"\nSeed Query {seed_idx}: {seed_query}")
        print("-" * 60)
        
        # Step 1: Generate persona variants
        print("  [1/3] Generating 5 persona variants...")
        persona_variants = persona_tx.transform(seed_query)
        print(f"  ✅ {len(persona_variants)} persona variants")
        
        # Step 2: For each persona, generate complexity variants
        print("  [2/3] Generating 3 complexity levels per persona...")
        persona_complexity_variants = []
        
        for persona_id, persona_query in persona_variants.items():
            complexity_variants = query_mod.transform(persona_query)
            
            for complexity, complex_query in complexity_variants.items():
                persona_complexity_variants.append({
                    "seed_query": seed_query,
                    "seed_id": seed_idx,
                    "persona": persona_id,
                    "persona_name": persona_tx.PERSONAS[persona_id]['name'],
                    "complexity": complexity,
                    "complexity_name": query_mod.COMPLEXITY_LEVELS[complexity]['name'],
                    "transformed_query": complex_query
                })
        
        print(f"  ✅ {len(persona_complexity_variants)} persona×complexity variants")
        
        # Step 3: For each variant, add tool data metadata
        print("  [3/3] Adding 2 tool data variants...")
        tool_variants = tool_data_tx.transform(seed_query)
        
        for variant in persona_complexity_variants:
            for tool_variant_id, tool_metadata in tool_variants.items():
                final_variant = variant.copy()
                final_variant["tool_variant"] = tool_variant_id
                final_variant["tool_variant_description"] = tool_metadata["description"]
                all_variants.append(final_variant)
        
        print(f"  ✅ {len(all_variants) - len(all_variants) + len(persona_complexity_variants) * len(tool_variants)} final variants from this seed")
        print("-" * 60)
    
    # Save to file
    print(f"\n[3/4] Saving {len(all_variants)} variants...")
    
    output_file = Path("samples/expanded_queries_30x.jsonl")
    write_jsonl(all_variants, output_file)
    
    print(f"✅ Saved to: {output_file}")
    
    # Create summary file
    print("\n[4/4] Creating summary...")
    
    summary = {
        "total_seed_queries": len(seed_queries),
        "total_variants": len(all_variants),
        "expansion_factor": len(all_variants) // len(seed_queries),
        "breakdown": {
            "personas": len(persona_tx.PERSONAS),
            "complexity_levels": len(query_mod.COMPLEXITY_LEVELS),
            "tool_variants": 2
        },
        "seed_queries": seed_queries
    }
    
    import json
    summary_file = Path("samples/expansion_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Summary saved to: {summary_file}")
    
    # Display samples
    print("\n" + "="*60)
    print("SAMPLE TRANSFORMED QUERIES")
    print("="*60)
    
    # Show first 3 variants
    for i, variant in enumerate(all_variants[:3], 1):
        print(f"\nVariant {i}:")
        print(f"  Seed: {variant['seed_query'][:50]}...")
        print(f"  Persona: {variant['persona']} ({variant['persona_name']})")
        print(f"  Complexity: {variant['complexity']} ({variant['complexity_name']})")
        print(f"  Tool Variant: {variant['tool_variant']}")
        print(f"  Transformed: {variant['transformed_query'][:80]}...")
    
    # Summary
    print("\n" + "="*60)
    print("✅ FULL EXPANSION COMPLETE!")
    print("="*60)
    print(f"\nGenerated {len(all_variants)} training query variants")
    print(f"From {len(seed_queries)} seed queries")
    print(f"Expansion: {len(all_variants) // len(seed_queries)}× per seed")
    
    # Breakdown by category
    from collections import Counter
    
    print("\nBreakdown:")
    personas = Counter(v['persona'] for v in all_variants)
    for p, count in personas.items():
        print(f"  {p}: {count} variants")
    
    print(f"\nFiles created:")
    print(f"  📄 {output_file}")
    print(f"  📄 {summary_file}")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_full_expansion()
