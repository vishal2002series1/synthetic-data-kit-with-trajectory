"""CLI commands for complete pipeline and statistics."""

from pathlib import Path
from typing import Any
import json
from tqdm import tqdm

from ..core import VectorStore
from ..generators import QAGenerator, TrajectoryGeneratorMultiIter
from ..transformations import PersonaTransformer, QueryModifier, ToolDataTransformer
from ..utils import get_logger, read_json, write_jsonl

logger = get_logger(__name__)


def add_pipeline_parser(subparsers):
    """Add pipeline command parser."""
    parser = subparsers.add_parser(
        'pipeline',
        help='Run complete generation pipeline'
    )
    parser.add_argument(
        'queries_file',
        type=str,
        help='JSON file with seed queries'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/output',
        help='Output directory (default: data/output)'
    )
    parser.add_argument(
        '--skip-transform',
        action='store_true',
        help='Skip transformation step (use queries as-is)'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=3,
        help='Maximum trajectory iterations (default: 3)'
    )


def add_stats_parser(subparsers):
    """Add stats command parser."""
    parser = subparsers.add_parser(
        'stats',
        help='Show system statistics'
    )


def run_pipeline(args: Any, config: Any):
    """Run complete pipeline: transform → generate trajectories."""
    
    queries_file = Path(args.queries_file)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not queries_file.exists():
        print(f"❌ Error: Queries file not found: {queries_file}")
        return
    
    print("="*60)
    print("COMPLETE PIPELINE")
    print("="*60)
    
    # Load seed queries
    data = read_json(queries_file)
    
    if isinstance(data, list):
        seed_queries = data
    elif 'queries' in data:
        seed_queries = data['queries']
    else:
        print("❌ Error: Invalid format")
        return
    
    print(f"Loaded {len(seed_queries)} seed queries")
    
    # Initialize components
    print("\n🔧 Initializing components...")
    vector_store = VectorStore(config)
    
    # Step 1: Transform (if not skipped)
    if not args.skip_transform:
        print("\n" + "="*60)
        print("STEP 1: TRANSFORMATION (30× expansion)")
        print("="*60)
        
        persona_tx = PersonaTransformer(vector_store.provider)
        query_mod = QueryModifier(vector_store.provider)
        tool_data_tx = ToolDataTransformer(vector_store.provider)
        
        transformed_queries = []
        
        with tqdm(total=len(seed_queries), desc="Transforming", unit="query") as pbar:
            for seed_idx, seed_query in enumerate(seed_queries, 1):
                query_text = seed_query if isinstance(seed_query, str) else seed_query.get('query')
                
                persona_variants = persona_tx.transform(query_text)
                
                for persona_id, persona_query in persona_variants.items():
                    complexity_variants = query_mod.transform(persona_query)
                    
                    for complexity, complex_query in complexity_variants.items():
                        tool_variants = tool_data_tx.transform(query_text)
                        
                        for tool_variant_id, tool_metadata in tool_variants.items():
                            transformed_queries.append({
                                "seed_query": query_text,
                                "seed_id": seed_idx,
                                "persona": persona_id,
                                "complexity": complexity,
                                "transformed_query": complex_query,
                                "tool_variant": tool_variant_id
                            })
                
                pbar.update(1)
        
        # Save transformed queries
        transform_file = output_dir / "transformed_queries.jsonl"
        write_jsonl(transformed_queries, transform_file)
        
        print(f"\n✅ Generated {len(transformed_queries)} transformed queries")
        print(f"Saved to: {transform_file}")
        
        queries_for_generation = transformed_queries
    else:
        queries_for_generation = seed_queries
    
    # Step 2: Generate trajectories
    print("\n" + "="*60)
    print("STEP 2: TRAJECTORY GENERATION")
    print("="*60)
    
    traj_gen = TrajectoryGeneratorMultiIter(
        bedrock_provider=vector_store.provider,
        vector_store=vector_store,
        config=config,
        max_iterations=args.max_iterations
    )
    
    all_examples = []
    
    with tqdm(total=len(queries_for_generation), desc="Generating trajectories", unit="query") as pbar:
        for i, query_data in enumerate(queries_for_generation, 1):
            if isinstance(query_data, str):
                query = query_data
                metadata = {"query_id": i}
            else:
                query = query_data.get('transformed_query') or query_data.get('query')
                metadata = query_data.copy()
            
            examples = traj_gen.generate_trajectory(query=query, metadata=metadata)
            all_examples.extend(examples)
            
            pbar.update(1)
    
    # Save trajectories
    trajectory_file = output_dir / "trajectories.jsonl"
    traj_gen.save_training_examples(all_examples, trajectory_file)
    
    # Summary
    print("\n" + "="*60)
    print("✅ PIPELINE COMPLETE")
    print("="*60)
    print(f"Seed queries: {len(seed_queries)}")
    
    if not args.skip_transform:
        print(f"Transformed queries: {len(transformed_queries)}")
    
    print(f"Training examples: {len(all_examples)}")
    print(f"\nOutput directory: {output_dir}")
    if not args.skip_transform:
        print(f"  - {transform_file.name}")
    print(f"  - {trajectory_file.name}")
    print("="*60 + "\n")


def run_stats(args: Any, config: Any):
    """Show system statistics."""
    
    print("\n" + "="*60)
    print("📊 SYSTEM STATISTICS")
    print("="*60)
    
    # Vector store stats
    print("\n🔧 Initializing VectorStore...")
    vector_store = VectorStore(config)
    stats = vector_store.get_stats()
    
    print("\n📦 Vector Store:")
    print(f"  Collection: {stats['collection_name']}")
    print(f"  Documents: {stats['total_documents']}")
    print(f"  Distance metric: {stats['distance_metric']}")
    
    # Config info
    print("\n⚙️  Configuration:")
    print(f"  Model: {config.bedrock.model_id}")
    print(f"  Embedding: {config.bedrock.embedding_model_id}")
    print(f"  Region: {config.bedrock.region}")
    print(f"  Output format: {config.output.format}")
    print(f"  Max tokens: {config.bedrock.max_tokens}")
    
    # Check for output files
    output_dir = Path(config.output.output_dir)
    samples_dir = Path("samples")
    
    all_files = []
    if output_dir.exists():
        all_files.extend(list(output_dir.glob("*.jsonl")))
    if samples_dir.exists():
        all_files.extend(list(samples_dir.glob("*.jsonl")))
    
    if all_files:
        print(f"\n📄 Output Files ({len(all_files)}):")
        for f in sorted(all_files)[:15]:
            size = f.stat().st_size / 1024  # KB
            with open(f) as file:
                lines = sum(1 for _ in file)
            print(f"  - {f.name} ({size:.1f} KB, {lines} records)")
        
        if len(all_files) > 15:
            print(f"  ... and {len(all_files) - 15} more")
    else:
        print(f"\n📄 Output Files: None found")
    
    print("\n" + "="*60 + "\n")
