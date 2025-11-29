"""Test core components."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils import setup_logger, load_config, get_logger
from src.core import BedrockProvider, ChromaDBManager


def test_bedrock():
    """Test Bedrock provider."""
    print("\n" + "="*60)
    print("TEST 1: Bedrock Provider")
    print("="*60)
    
    try:
        config = load_config()
        
        provider = BedrockProvider(
            model_id=config.bedrock.model_id,
            embedding_model_id=config.bedrock.embedding_model_id,
            region=config.bedrock.region
        )
        
        print(f"✅ BedrockProvider initialized: {provider}")
        
        # Test text generation
        print("\nTesting text generation...")
        response = provider.generate_text(
            prompt="Say 'Hello from Claude!' and nothing else.",
            max_tokens=50,
            temperature=0.7
        )
        print(f"✅ Response: {response[:100]}...")
        
        # Test embedding
        print("\nTesting embedding generation...")
        embedding = provider.generate_embedding("Test text for embedding")
        print(f"✅ Embedding dimension: {len(embedding)}")
        
        print("\n✅ Bedrock test passed\n")
        return provider
        
    except Exception as e:
        print(f"\n❌ Bedrock test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return None


def test_chromadb(provider):
    """Test ChromaDB manager."""
    print("="*60)
    print("TEST 2: ChromaDB Manager")
    print("="*60)
    
    if not provider:
        print("⚠️  Skipping ChromaDB test (Bedrock not available)\n")
        return None
    
    try:
        config = load_config()
        
        # Initialize manager
        manager = ChromaDBManager(
            persist_directory=config.chromadb.persist_directory,
            collection_name="test_collection",
            distance_metric=config.chromadb.distance_metric
        )
        
        print(f"✅ ChromaDBManager initialized: {manager}")
        
        # Add test documents
        print("\nAdding test documents...")
        test_docs = [
            "Artificial intelligence is transforming technology.",
            "Machine learning enables computers to learn from data.",
            "Deep learning uses neural networks for complex tasks."
        ]
        
        embeddings = [provider.generate_embedding(doc) for doc in test_docs]
        metadatas = [{"source": "test", "id": i} for i in range(len(test_docs))]
        
        ids = manager.add_documents(
            documents=test_docs,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        print(f"✅ Added {len(ids)} documents")
        
        # Test query
        print("\nQuerying collection...")
        query_text = "What is machine learning?"
        query_emb = provider.generate_embedding(query_text)
        
        results = manager.query(
            query_embeddings=[query_emb],
            n_results=2
        )
        
        print(f"✅ Query returned {len(results['documents'][0])} results")
        print(f"   Top result: {results['documents'][0][0][:60]}...")
        
        # Get stats
        stats = manager.get_stats()
        print(f"\n✅ Collection stats: {stats}")
        
        print("\n✅ ChromaDB test passed\n")
        return manager
        
    except Exception as e:
        print(f"\n❌ ChromaDB test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    setup_logger("INFO", "logs/test_core.log")
    
    print("\n🧪 TESTING CORE COMPONENTS")
    print("="*60)
    print("Note: This requires AWS credentials configured")
    print("="*60)
    
    provider = test_bedrock()
    manager = test_chromadb(provider)
    
    if provider and manager:
        print("\n" + "="*60)
        print("✅ ALL CORE TESTS PASSED!")
        print("="*60 + "\n")
    else:
        print("\n" + "="*60)
        print("⚠️  SOME TESTS SKIPPED (AWS not configured)")
        print("="*60)
        print("\nTo enable full testing:")
        print("1. Configure AWS credentials: aws configure")
        print("2. Ensure Bedrock access enabled in AWS Console")
        print("3. Run test again")
        print("="*60 + "\n")
