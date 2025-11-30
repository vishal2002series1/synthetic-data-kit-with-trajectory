"""CLI commands for query transformations."""

from pathlib import Path
from typing import Any
import json
from tqdm import tqdm

from ..core import BedrockProvider
from ..transformations import PersonaTransformer, QueryModifier, ToolDataTransformer
from ..utils import get_logger, read_json, write_jsonl

logger = get_logger(__name__)


def add_transform_parser(subparsers):
    """Add transform command parser."""
    parser = subparsers.add_parser(
        'transform',
        help='Transform queries with 30× expansion'
    )
    parser.add_argument(
        'queries_file',
        type=str,
        help='JSON file with seed queries'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='samples/transformed_queries.jsonl',
        help='Output file path'
    )
    parser.add_argument(
        '--persona',
        type=str,
        choices=['P1', 'P2', 'P3', 'P4', 'P5', 'all'],
        default='all',
        help='Specific persona or all (default: all)'
    )
    parser.add_argument(
        '--complexity',
        type=str,
        choices=['Q-', 'Q', 'Q+', 'all'],
        default='all',
        help='Specific complexity or all (default: all)'
    )


def run_transform(args: Any, config: Any):
    """Run query transformation."""
    
    queries_file = Path(args.queries_file)
    
    if not queries_file.exists():
        print(f"❌ Error: Queries file not found: {queries_file}")
        return
    
    # Load seed queries
    data = read_json(queries_file)
    
    if isinstance(data, list):
        seed_queries = data
    elif 'queries' in data:
        seed_queries = data['queries']
    elif 'seed_queries' in data:
        seed_queries = data['seed_queries']
    else:
        print("❌ Error: Invalid JSON format. Expected list or {'queries': [...]}")
        return
    
    print(f"\n✅ Loaded {len(seed_queries)} seed queries")
    
    # Initialize transformers
    print("\n🔧 Initializing transformers...")
    provider = BedrockProvider(
        model_id=config.bedrock.model_id,
        embedding_model_id=config.bedrock.embedding_model_id,
        region=config.bedrock.region
    )
    
    persona_tx = PersonaTransformer(provider)
    query_mod = QueryModifier(provider)
    tool_data_tx = ToolDataTransformer(provider)
    
    expansion = persona_tx.get_expansion_factor() * query_mod.get_expansion_factor() * tool_data_tx.get_expansion_factor()
    print(f"✅ Expected expansion: {expansion}× per seed query")
    
    # Transform queries with progress bar
    all_variants = []
    
    print(f"\n🔄 Transforming {len(seed_queries)} queries...")
    print("   (This may take a few minutes...)\n")
    
    with tqdm(total=len(seed_queries), desc="Transforming", unit="query") as pbar:
        for seed_idx, seed_query in enumerate(seed_queries, 1):
            # Extract query text
            if isinstance(seed_query, str):
                query_text = seed_query
            elif isinstance(seed_query, dict):
                query_text = seed_query.get('query') or seed_query.get('Q')
            else:
                pbar.update(1)
                continue
            
            pbar.set_description(f"Query {seed_idx}/{len(seed_queries)}")
            
            # Step 1: Persona transformation
            persona_filter = None if args.persona == 'all' else args.persona
            persona_variants = persona_tx.transform(query_text, persona=persona_filter)
            
            # Step 2: Complexity transformation
            complexity_filter = None if args.complexity == 'all' else args.complexity
            
            for persona_id, persona_query in persona_variants.items():
                complexity_variants = query_mod.transform(persona_query, complexity=complexity_filter)
                
                for complexity, complex_query in complexity_variants.items():
                    # Step 3: Tool data variants
                    tool_variants = tool_data_tx.transform(query_text)
                    
                    for tool_variant_id, tool_metadata in tool_variants.items():
                        variant = {
                            "seed_query": query_text,
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
            
            pbar.update(1)
    
    # Save
    output_file = Path(args.output)
    write_jsonl(all_variants, output_file)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"✅ TRANSFORMATION COMPLETE")
    print(f"{'='*60}")
    print(f"Seed queries: {len(seed_queries)}")
    print(f"Total variants: {len(all_variants)}")
    print(f"Expansion: {len(all_variants) // len(seed_queries)}× per seed")
    print(f"Output: {output_file}")
    print(f"{'='*60}\n")
