"""Test multi-iteration trajectories with CALL decisions."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils import setup_logger, load_config, get_logger
from src.core import VectorStore
from src.generators import TrajectoryGeneratorMultiIter


def test_multi_call_trajectories():
    """Test trajectories that should trigger CALL→ANSWER patterns."""
    
    print("\n" + "="*60)
    print("MULTI-CALL TRAJECTORY TEST")
    print("="*60)
    
    setup_logger("INFO", "logs/test_multi_call.log")
    config = load_config()
    
    # Use test collection with ML documents
    print("\n[1/3] Initializing VectorStore...")
    config.chromadb.collection_name = "qa_test_collection"
    vector_store = VectorStore(config)
    print(f"✅ VectorStore: {vector_store.count()} documents")
    
    if vector_store.count() == 0:
        print("\n⚠️  Run test_qa_generation.py first to populate documents")
        return
    
    # Initialize trajectory generator
    print("\n[2/3] Initializing TrajectoryGeneratorMultiIter...")
    traj_gen = TrajectoryGeneratorMultiIter(
        bedrock_provider=vector_store.provider,
        vector_store=vector_store,
        config=config,
        max_iterations=3
    )
    print(f"✅ {traj_gen}")
    
    # Test queries that SHOULD trigger CALL decisions
    print("\n[3/3] Generating trajectories with document-grounded queries...")
    print("   These queries require searching documents:")
    print("\n   (This may take 1-2 minutes...)\n")
    
    test_queries = [
        "Based on the available information, explain how neural networks work and their key components.",
        "What are the main differences between supervised and unsupervised learning according to the documentation?",
        "Describe the preprocessing steps mentioned for machine learning data.",
    ]

    test_queries = [
    "What would be a good asset allocation strategy for a conservative investor?",
    "How can I optimize my portfolio to reduce risk?",
    "What are the key steps in rebalancing a portfolio?",
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
            print(f"\n  Example {j+1} (Iteration {ex.metadata['iteration']}):")
            print(f"    Decision Type: {ex.metadata['decision_type']}")
            print(f"    COT: {ex.chain_of_thought[:100]}...")
            print(f"    Tools Called: {len(ex.tool_set)} tools")
            if ex.tool_set:
                print(f"    Tool Names: {[t['name'] for t in ex.tool_set]}")
            print(f"    Decision: {ex.decision[:80]}...")
        
        all_examples.extend(examples)
        print("-" * 60)
    
    # Save
    output_file = Path("samples/test_multi_call_trajectories.jsonl")
    traj_gen.save_training_examples(all_examples, output_file)
    print(f"\n✅ Saved {len(all_examples)} examples to: {output_file}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"\nTotal training examples: {len(all_examples)}")
    print(f"From {len(test_queries)} queries")
    print(f"Average: {len(all_examples)/len(test_queries):.1f} examples per query")
    
    # Count by decision type
    from collections import Counter
    decision_types = Counter(ex.metadata['decision_type'] for ex in all_examples)
    print("\nDecision type distribution:")
    for dtype, count in decision_types.items():
        print(f"  - {dtype}: {count} examples")
    
    # Count iterations
    iterations = Counter(ex.metadata['iteration'] for ex in all_examples)
    print("\nIteration distribution:")
    for iter_num, count in sorted(iterations.items()):
        print(f"  - Iteration {iter_num}: {count} examples")
    
    print(f"\nOutput: {output_file}")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_multi_call_trajectories()
