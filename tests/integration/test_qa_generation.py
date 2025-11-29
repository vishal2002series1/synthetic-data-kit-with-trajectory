"""Test Q&A generation from documents."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils import setup_logger, load_config, get_logger
from src.core import VectorStore
from src.generators import QAGenerator


def test_qa_generation():
    """Test complete Q&A generation pipeline."""
    
    print("\n" + "="*60)
    print("Q&A GENERATION TEST")
    print("="*60)
    
    setup_logger("INFO", "logs/test_qa.log")
    config = load_config()
    logger = get_logger(__name__)
    
    # Initialize vector store with FRESH collection for testing
    print("\n[1/5] Initializing VectorStore (fresh test collection)...")
    
    # Modify config to use test collection
    config.chromadb.collection_name = "qa_test_collection"
    
    vector_store = VectorStore(config)
    doc_count = vector_store.count()
    print(f"✅ VectorStore: {doc_count} documents in test collection")
    
    # Always add fresh sample documents for this test
    print("\n[2/5] Adding substantial test documents...")
    
    sample_docs = [
        """Machine learning is a method of data analysis that automates analytical model building. 
        It is a branch of artificial intelligence based on the idea that systems can learn from data, 
        identify patterns and make decisions with minimal human intervention. Machine learning algorithms 
        use computational methods to learn information directly from data without relying on a predetermined 
        equation as a model. The algorithms adaptively improve their performance as the number of samples 
        available for learning increases. Common applications include recommendation systems, fraud detection, 
        image recognition, and natural language processing.""",
        
        """Deep learning is a subset of machine learning that uses neural networks with multiple layers, 
        also known as deep neural networks. These networks can learn hierarchical representations of data, 
        making them particularly effective for complex tasks. Deep learning has revolutionized computer vision, 
        enabling facial recognition, autonomous vehicles, and medical image analysis. In natural language 
        processing, deep learning powers translation services, chatbots, and text generation systems. 
        The key advantage of deep learning is its ability to automatically discover the features needed 
        for detection or classification from raw data, eliminating the need for manual feature engineering.""",
        
        """Natural language processing (NLP) enables computers to understand, interpret, and generate human language. 
        It combines computational linguistics with statistical methods, machine learning, and deep learning models. 
        NLP powers many applications we use daily, including voice assistants like Siri and Alexa, email spam filters, 
        search engines, and language translation services. Key challenges in NLP include handling ambiguity in language, 
        understanding context and sarcasm, and processing multiple languages. Recent advances in transformer models 
        and large language models have dramatically improved NLP capabilities across various tasks.""",
        
        """Supervised learning is a type of machine learning where the algorithm learns from labeled training data. 
        In supervised learning, each training example consists of input features and a corresponding output label. 
        The algorithm learns the relationship between inputs and outputs, creating a model that can predict labels 
        for new, unseen data. Common supervised learning tasks include classification, where the output is a category 
        (like spam or not spam), and regression, where the output is a continuous value (like house prices). 
        Examples of supervised learning algorithms include decision trees, support vector machines, and neural networks.""",
        
        """Unsupervised learning works with unlabeled data to discover hidden patterns or intrinsic structures. 
        Unlike supervised learning, there are no predefined labels or target outputs. The algorithm explores 
        the data to find meaningful relationships and groupings. Common unsupervised learning techniques include 
        clustering, which groups similar data points together; dimensionality reduction, which reduces the number 
        of features while preserving important information; and association rule learning, which discovers 
        relationships between variables. Applications include customer segmentation, anomaly detection, and 
        data compression.""",
        
        """Reinforcement learning is a type of machine learning where an agent learns to make decisions by 
        interacting with an environment. The agent receives rewards or penalties based on its actions and 
        learns to maximize cumulative rewards over time. This approach is inspired by behavioral psychology 
        and how humans and animals learn from experience. Reinforcement learning has achieved remarkable 
        successes in game playing, robotics, and autonomous systems. Notable examples include AlphaGo defeating 
        world champions in the game of Go, and robots learning to walk or manipulate objects through trial and error.""",
        
        """Neural networks are computing systems inspired by the biological neural networks in animal brains. 
        They consist of interconnected nodes (neurons) organized in layers. Each connection has a weight that 
        adjusts during learning, allowing the network to recognize patterns and make predictions. The simplest 
        form is the perceptron, while more complex architectures include convolutional neural networks for 
        image processing and recurrent neural networks for sequential data. Training involves feeding the 
        network examples and adjusting weights through backpropagation to minimize prediction errors.""",
        
        """Data preprocessing is a crucial step in machine learning that involves transforming raw data into 
        a clean and usable format. This includes handling missing values through imputation or removal, 
        normalizing or scaling features to similar ranges, encoding categorical variables into numerical format, 
        and removing outliers that could skew the model. Feature engineering, creating new features from existing 
        ones, can significantly improve model performance. Proper data preprocessing can make the difference 
        between a mediocre model and an excellent one, as the quality of input data directly affects output quality."""
    ]
    
    # Clear any existing documents in test collection and add fresh ones
    try:
        vector_store.db.delete_collection()
        vector_store.db.collection = vector_store.db.client.get_or_create_collection(
            name=config.chromadb.collection_name,
            metadata={"hnsw:space": config.chromadb.distance_metric}
        )
    except:
        pass  # Collection might not exist
    
    ids = vector_store.add_chunks(sample_docs, source="test_docs")
    print(f"✅ Added {len(ids)} substantial documents ({len(sample_docs)} original)")
    
    # Verify documents
    final_count = vector_store.count()
    print(f"✅ Final document count: {final_count}")
    
    # Initialize QA generator
    print("\n[3/5] Initializing QAGenerator...")
    qa_gen = QAGenerator(
        bedrock_provider=vector_store.provider,
        vector_store=vector_store
    )
    print(f"✅ {qa_gen}")
    
    # Generate Q&A pairs
    print("\n[4/5] Generating Q&A pairs...")
    print("   This will:")
    print("   - Retrieve diverse chunks from vector store")
    print("   - Generate questions from chunks")
    print("   - Generate answers using RAG")
    print("   - Abstract away document references")
    print("\n   (This may take 1-2 minutes...)\n")
    
    qa_pairs = qa_gen.generate_qa_from_documents(
        n_pairs=10,
        complexity="all",
        questions_per_chunk=2,
        min_chunk_length=100  # Lower threshold for test
    )
    
    print(f"\n✅ Generated {len(qa_pairs)} Q&A pairs")
    
    if len(qa_pairs) == 0:
        print("\n❌ No Q&A pairs generated!")
        print("Debugging info:")
        print(f"  - Vector store docs: {vector_store.count()}")
        print(f"  - Test will show if chunks are being retrieved...")
        return
    
    # Display samples
    print("\n[5/5] Sample Q&A Pairs:")
    print("-"*60)
    
    for i, pair in enumerate(qa_pairs[:3], 1):
        print(f"\nQ&A Pair {i} ({pair['complexity']}):")
        print(f"Q: {pair['question']}")
        print(f"A: {pair['answer'][:200]}...")  # First 200 chars
        print("-"*60)
    
    # Save to file
    output_file = Path("samples/test_qa_10.jsonl")
    qa_gen.save_qa_pairs(qa_pairs, output_file)
    print(f"\n✅ Saved to: {output_file}")
    
    # Summary
    print("\n" + "="*60)
    print("✅ Q&A GENERATION TEST PASSED!")
    print("="*60)
    print(f"\nGenerated {len(qa_pairs)} Q&A pairs:")
    
    # Count by complexity
    from collections import Counter
    complexity_counts = Counter(pair['complexity'] for pair in qa_pairs)
    for comp, count in complexity_counts.items():
        print(f"  - {comp}: {count} pairs")
    
    print(f"\nOutput: {output_file}")
    print("\nSample format:")
    if qa_pairs:
        import json
        print(json.dumps({"Q": qa_pairs[0]["question"], "A": qa_pairs[0]["answer"][:100] + "..."}, indent=2))
    
    print("="*60 + "\n")


if __name__ == "__main__":
    test_qa_generation()
