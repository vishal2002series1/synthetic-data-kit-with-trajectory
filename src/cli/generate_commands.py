"""CLI commands for Q&A and trajectory generation."""

from pathlib import Path
from typing import Any
import json
from tqdm import tqdm

from ..core import VectorStore
from ..generators import QAGenerator, TrajectoryGeneratorMultiIter
from ..utils import get_logger, read_json

logger = get_logger(__name__)


def add_generate_qa_parser(subparsers):
    """Add generate-qa command parser."""
    parser = subparsers.add_parser(
        'generate-qa',
        help='Generate Q&A pairs from documents'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Number of Q&A pairs to generate (default: 50)'
    )
    parser.add_argument(
        '--complexity',
        type=str,
        default='all',
        choices=['simple', 'medium', 'complex', 'all'],
        help='Question complexity (default: all)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='samples/generated_qa.jsonl',
        help='Output file path'
    )


def add_generate_trajectories_parser(subparsers):
    """Add generate command parser for trajectories."""
    parser = subparsers.add_parser(
        'generate',
        help='Generate multi-iteration trajectories'
    )
    parser.add_argument(
        'queries_file',
        type=str,
        help='JSON file with queries or transformed queries'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='samples/trajectories.jsonl',
        help='Output file path'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=3,
        help='Maximum iterations per trajectory (default: 3)'
    )


def run_generate_qa(args: Any, config: Any):
    """Run Q&A generation."""
    
    print(f"\n🔄 Generating {args.limit} Q&A pairs...")
    
    # Initialize components
    print("\n🔧 Initializing VectorStore...")
    vector_store = VectorStore(config)
    
    if vector_store.count() == 0:
        print("\n❌ Error: Vector store is empty! Ingest documents first.")
        print("Run: python main.py ingest-batch data/pdfs/")
        return
    
    print(f"✅ VectorStore ready ({vector_store.count()} documents)")
    
    qa_gen = QAGenerator(
        bedrock_provider=vector_store.provider,
        vector_store=vector_store
    )
    
    # Generate Q&A pairs (with progress indication)
    print(f"\n🔄 Generating Q&A pairs (complexity: {args.complexity})...")
    print("   (This may take a few minutes...)\n")
    
    qa_pairs = qa_gen.generate_qa_from_documents(
        n_pairs=args.limit,
        complexity=args.complexity
    )
    
    # Save
    output_file = Path(args.output)
    qa_gen.save_qa_pairs(qa_pairs, output_file)
    
    print(f"\n{'='*60}")
    print(f"✅ Q&A GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"Generated: {len(qa_pairs)} Q&A pairs")
    print(f"Output: {output_file}")
    print(f"{'='*60}\n")


def run_generate_trajectories(args: Any, config: Any):
    """Run trajectory generation."""
    
    queries_file = Path(args.queries_file)
    
    if not queries_file.exists():
        print(f"\n❌ Error: Queries file not found: {queries_file}")
        return
    
    # Load queries
    if queries_file.suffix == '.json':
        data = read_json(queries_file)
        if isinstance(data, list):
            queries = data
        elif 'queries' in data:
            queries = data['queries']
        else:
            print("\n❌ Error: Invalid JSON format. Expected list or {'queries': [...]}")
            return
    else:
        # Try JSONL
        from ..utils import read_jsonl
        queries = read_jsonl(queries_file)
    
    print(f"\n✅ Loaded {len(queries)} queries")
    
    # Initialize components
    print("\n�� Initializing VectorStore and TrajectoryGenerator...")
    vector_store = VectorStore(config)
    
    traj_gen = TrajectoryGeneratorMultiIter(
        bedrock_provider=vector_store.provider,
        vector_store=vector_store,
        config=config,
        max_iterations=args.max_iterations
    )
    
    print(f"✅ Ready to generate (max {args.max_iterations} iterations per query)")
    
    # Generate trajectories with progress bar
    all_examples = []
    
    print(f"\n🔄 Generating trajectories for {len(queries)} queries...")
    print("   (This may take a few minutes...)\n")
    
    with tqdm(total=len(queries), desc="Generating trajectories", unit="query") as pbar:
        for i, query_data in enumerate(queries, 1):
            # Extract query text
            if isinstance(query_data, str):
                query = query_data
                metadata = {"query_id": i}
            elif isinstance(query_data, dict):
                query = query_data.get('transformed_query') or query_data.get('query') or query_data.get('Q')
                metadata = query_data.copy()
                metadata['query_id'] = i
            else:
                pbar.update(1)
                continue
            
            pbar.set_description(f"Query {i}/{len(queries)}")
            
            # Generate trajectory
            examples = traj_gen.generate_trajectory(
                query=query,
                metadata=metadata
            )
            
            all_examples.extend(examples)
            pbar.set_postfix({"examples": len(all_examples)})
            pbar.update(1)
    
    # Save
    output_file = Path(args.output)
    traj_gen.save_training_examples(all_examples, output_file)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"✅ TRAJECTORY GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"Input queries: {len(queries)}")
    print(f"Training examples: {len(all_examples)}")
    print(f"Avg examples per query: {len(all_examples)/len(queries):.1f}")
    print(f"Output: {output_file}")
    print(f"{'='*60}\n")
