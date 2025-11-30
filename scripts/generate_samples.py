"""
Generate comprehensive sample datasets for evaluation and demonstration.

Generates:
1. Q&A samples (from documents)
2. Transformed queries (30× expansion)
3. Trajectory samples (multi-iteration)
4. Complete pipeline output
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import setup_logger, load_config, write_json
from src.core import VectorStore
from src.generators import QAGenerator, TrajectoryGeneratorMultiIter
from src.transformations import PersonaTransformer, QueryModifier, ToolDataTransformer


def generate_comprehensive_samples():
    """Generate comprehensive sample datasets."""
    
    print("\n" + "="*60)
    print("COMPREHENSIVE SAMPLE GENERATION")
    print("="*60)
    
    setup_logger("INFO", "logs/generate_samples.log")
    config = load_config()
    
    # Initialize components
    print("\n[1/4] Initializing components...")
    vector_store = VectorStore(config)
    
    if vector_store.count() == 0:
        print("⚠️  Warning: Vector store is empty!")
        print("   Some samples will be skipped.")
        print("   Run: python main.py ingest-batch data/pdfs/")
    else:
        print(f"✅ VectorStore ready ({vector_store.count()} documents)")
    
    # Sample 1: Q&A Generation (if documents available)
    if vector_store.count() > 0:
        print("\n[2/4] Generating Q&A samples...")
        
        qa_gen = QAGenerator(
            bedrock_provider=vector_store.provider,
            vector_store=vector_store
        )
        
        # Generate by complexity
        for complexity in ['simple', 'medium', 'complex']:
            print(f"  Generating {complexity} Q&A pairs...")
            qa_pairs = qa_gen.generate_qa_from_documents(
                n_pairs=5,
                complexity=complexity
            )
            
            output_file = Path(f"samples/qa_{complexity}_5.jsonl")
            qa_gen.save_qa_pairs(qa_pairs, output_file)
            print(f"  ✅ Saved {len(qa_pairs)} pairs to {output_file.name}")
    else:
        print("\n[2/4] Skipping Q&A generation (no documents)")
    
    # Sample 2: Query Transformations
    print("\n[3/4] Generating transformation samples...")
    
    provider = vector_store.provider
    persona_tx = PersonaTransformer(provider)
    query_mod = QueryModifier(provider)
    tool_data_tx = ToolDataTransformer(provider)
    
    # Seed queries for demonstration
    seed_queries = [
        "How should I diversify my portfolio?",
        "What's the best retirement savings strategy?",
    ]
    
    all_variants = []
    
    for seed_idx, seed_query in enumerate(seed_queries, 1):
        print(f"  Transforming seed {seed_idx}/{len(seed_queries)}...")
        
        # Generate all variants
        persona_variants = persona_tx.transform(seed_query)
        
        for persona_id, persona_query in persona_variants.items():
            complexity_variants = query_mod.transform(persona_query)
            
            for complexity, complex_query in complexity_variants.items():
                tool_variants = tool_data_tx.transform(seed_query)
                
                for tool_variant_id, tool_metadata in tool_variants.items():
                    variant = {
                        "seed_query": seed_query,
                        "seed_id": seed_idx,
                        "persona": persona_id,
                        "persona_name": persona_tx.PERSONAS[persona_id]['name'],
                        "complexity": complexity,
                        "complexity_name": query_mod.COMPLEXITY_LEVELS[complexity]['name'],
                        "transformed_query": complex_query,
                        "tool_variant": tool_variant_id,
                        "tool_variant_description": tool_metadata["description"]
                    }
                    all_variants.append(variant)
    
    from src.utils import write_jsonl
    output_file = Path("samples/transformations_demo_60.jsonl")
    write_jsonl(all_variants, output_file)
    print(f"  ✅ Saved {len(all_variants)} variants to {output_file.name}")
    
    # Sample 3: Trajectory Generation
    print("\n[4/4] Generating trajectory samples...")
    
    traj_gen = TrajectoryGeneratorMultiIter(
        bedrock_provider=vector_store.provider,
        vector_store=vector_store,
        config=config,
        max_iterations=3
    )
    
    # Use financial queries that trigger multi-iteration
    trajectory_queries = [
        "Analyze my portfolio risk and suggest rebalancing",
        "How can I optimize my asset allocation for retirement?",
        "What's the tax impact of my investment strategy?"
    ]
    
    all_examples = []
    
    for i, query in enumerate(trajectory_queries, 1):
        print(f"  Generating trajectory {i}/{len(trajectory_queries)}...")
        examples = traj_gen.generate_trajectory(
            query=query,
            metadata={"demo_query_id": i}
        )
        all_examples.extend(examples)
    
    output_file = Path("samples/trajectories_demo.jsonl")
    traj_gen.save_training_examples(all_examples, output_file)
    print(f"  ✅ Saved {len(all_examples)} examples to {output_file.name}")
    
    # Summary
    print("\n" + "="*60)
    print("✅ SAMPLE GENERATION COMPLETE")
    print("="*60)
    print("\nGenerated samples:")
    
    samples_dir = Path("samples")
    sample_files = sorted(samples_dir.glob("*.jsonl"))
    
    for f in sample_files:
        size = f.stat().st_size / 1024
        with open(f) as file:
            lines = sum(1 for _ in file)
        print(f"  📄 {f.name} ({lines} records, {size:.1f} KB)")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    generate_comprehensive_samples()
