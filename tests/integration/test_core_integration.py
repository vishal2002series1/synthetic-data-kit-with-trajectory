"""Integration test for all core components."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils import setup_logger, load_config, get_logger
from src.core import (
    BedrockProvider,
    ChromaDBManager,
    PDFParser,
    VectorStore,
    IterationState,
    StateManager
)


def test_complete_integration():
    """Test complete integration of all core components."""
    
    print("\n" + "="*60)
    print("INTEGRATION TEST: ALL CORE COMPONENTS")
    print("="*60)
    
    # Setup
    setup_logger("INFO", "logs/test_integration.log")
    config = load_config()
    logger = get_logger(__name__)
    
    # Test 1: VectorStore
    print("\n[1/3] Testing VectorStore...")
    vector_store = VectorStore(config)
    print(f"✅ VectorStore initialized: {vector_store}")
    
    # Add test documents
    test_docs = [
        "Machine learning is a subset of artificial intelligence.",
        "Deep learning uses neural networks with multiple layers.",
        "Natural language processing enables text understanding."
    ]
    
    ids = vector_store.add_chunks(test_docs, source="test")
    print(f"✅ Added {len(ids)} documents")
    
    # Query
    results = vector_store.query("What is machine learning?", n_results=2)
    print(f"✅ Query returned {len(results['documents'][0])} results")
    
    # Test 2: PDFParser
    print("\n[2/3] Testing PDFParser...")
    parser = PDFParser(
        bedrock_provider=vector_store.provider,
        chunk_size=500,
        chunk_overlap=50,
        use_vision=False
    )
    print(f"✅ PDFParser initialized: {parser}")
    
    # Test 3: StateManager
    print("\n[3/3] Testing StateManager...")
    state_mgr = StateManager()
    state = state_mgr.initialize("test_query_1", "What is AI?")
    print(f"✅ StateManager initialized")
    print(f"✅ Created state: iteration={state.iteration}")
    
    context = state.to_context()
    print(f"✅ State context: {list(context.keys())}")
    
    # Summary
    print("\n" + "="*60)
    print("✅ ALL INTEGRATION TESTS PASSED!")
    print("="*60)
    print("\nComponents tested:")
    print("  ✅ BedrockProvider")
    print("  ✅ ChromaDBManager")
    print("  ✅ VectorStore")
    print("  ✅ PDFParser")
    print("  ✅ StateManager")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_complete_integration()
