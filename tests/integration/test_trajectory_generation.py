"""Test multi-iteration trajectory generation."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils import setup_logger, load_config, get_logger
from src.core import VectorStore
from src.generators import TrajectoryGeneratorMultiIter


def test_trajectory_generation():
    """Test multi-iteration trajectory generation."""
    
    print("\n" + "="*60)
    print("MULTI-ITERATION TRAJECTORY GENERATION TEST")
    print("="*60)
    
    setup_logger("INFO", "logs/test_trajectory.log")
    config = load_config()
    logger = get_logger(__name__)
    
    # Use test collection from Q&A test (should have documents)
    print("\n[1/4] Initializing VectorStore...")
    config.chromadb.collection_name = "qa_test_collection"
    vector_store = VectorStore(config)
    print(f"✅ VectorStore: {vector_store.count()} documents")
    
    if vector_store.count() == 0:
        print("\n⚠️  No documents in vector store!")
        print("Run test_qa_generation.py first to populate documents")
        return
    
    # Initialize trajectory generator
    print("\n[2/4] Initializing TrajectoryGeneratorMultiIter...")
    traj_gen = TrajectoryGeneratorMultiIter(
        bedrock_provider=vector_store.provider,
        vector_store=vector_store,
        config=config,
        max_iterations=3
    )
    print(f"✅ {traj_gen}")
    print(f"   Loaded {len(traj_gen.tools)} tools")
    print(f"   Field names: {traj_gen.field_names}")
    
    # Test queries of different types
    print("\n[3/4] Generating trajectories...")
    print("   Testing different query types:")
    print("   - Simple query (likely 1-2 iterations)")
    print("   - Complex query (likely 2-3 iterations)")
    print("\n   (This may take 1-2 minutes...)\n")
    
    test_queries = [
        "What is machine learning?",
        "How does deep learning differ from traditional machine learning, and what makes it effective?",
        "What is my portfolio balance?",
        "I want to retire early. How can I be financial expert in that ?"

    ]
    
    all_examples = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nQuery {i}: {query}")
        print("-" * 60)
        
        examples = traj_gen.generate_trajectory(
            query=query,
            metadata={"test_query_id": i}
        )
        
        print(f"✅ Generated {len(examples)} training examples")
        
        for j, ex in enumerate(examples):
            print(f"\n  Example {j+1}:")
            print(f"    Iteration: {ex.metadata['iteration']}")
            print(f"    Decision Type: {ex.metadata['decision_type']}")
            print(f"    COT: {ex.chain_of_thought[:80]}...")
            print(f"    Tools: {len(ex.tool_set)} tools")
            print(f"    Decision: {ex.decision[:60]}...")
        
        all_examples.extend(examples)
        print("-" * 60)
    
    # Display sample output
    print("\n[4/4] Sample Training Example (Full Format):")
    print("="*60)
    
    if all_examples:
        sample = all_examples[0].to_dict(traj_gen.field_names)
        import json
        print(json.dumps(sample, indent=2))
    
    # Save examples
    output_file = Path("samples/test_trajectories_multi.jsonl")
    traj_gen.save_training_examples(all_examples, output_file)
    print(f"\n✅ Saved {len(all_examples)} examples to: {output_file}")
    
    # Summary
    print("\n" + "="*60)
    print("✅ TRAJECTORY GENERATION TEST PASSED!")
    print("="*60)
    print(f"\nGenerated {len(all_examples)} training examples from {len(test_queries)} queries")
    print(f"Average: {len(all_examples)/len(test_queries):.1f} examples per query")
    
    # Count by decision type
    from collections import Counter
    decision_types = Counter(ex.metadata['decision_type'] for ex in all_examples)
    print("\nDecision type distribution:")
    for dtype, count in decision_types.items():
        print(f"  - {dtype}: {count} examples")
    
    print(f"\nOutput: {output_file}")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_trajectory_generation()
