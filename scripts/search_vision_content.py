"""
Search for vision-related content in VectorDB.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import load_config
from src.core import VectorStore


def search_vision_content():
    """Search for chunks with vision content."""
    
    config = load_config()
    vector_store = VectorStore(config)
    
    print("\n" + "="*60)
    print("SEARCHING FOR VISION CONTENT")
    print("="*60)
    print(f"Total documents: {vector_store.count()}")
    
    # Search for vision-related queries
    test_queries = [
        "chart graph image visual",
        "asset allocation diagram",
        "investment returns chart",
        "portfolio performance graph"
    ]
    
    vision_found = False
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        results = vector_store.search(query, k=5)
        
        for i, result in enumerate(results, 1):
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            
            # Check for vision markers
            vision_markers = [
                'image description', 'image analysis', 'chart shows', 
                'chart depicts', 'graph shows', 'graph depicts',
                'visual analysis', 'figure shows', 'diagram illustrates',
                'the image', 'the chart', 'the graph'
            ]
            
            has_vision = any(marker in content.lower() for marker in vision_markers)
            
            if has_vision or metadata.get('has_vision_content'):
                vision_found = True
                print(f"\n  ✅ Result {i} HAS VISION:")
                print(f"     Source: {metadata.get('source', 'N/A')}")
                print(f"     Page: {metadata.get('page_number', 'N/A')}")
                print(f"     Preview: {content[:250]}...")
        
        if not vision_found:
            print(f"  ❌ No vision content found for this query")
    
    if not vision_found:
        print(f"\n{'='*60}")
        print("⚠️  WARNING: NO VISION CONTENT DETECTED")
        print("="*60)
        print("\nPossible reasons:")
        print("  1. PDFs don't contain images/charts")
        print("  2. Vision analysis was disabled during ingestion")
        print("  3. Vision content wasn't captured in chunks")
        print("\nTo re-ingest with vision enabled:")
        print("  python main.py ingest-batch data/pdfs/")
    else:
        print(f"\n{'='*60}")
        print("✅ VISION CONTENT FOUND!")
        print("="*60)


if __name__ == "__main__":
    search_vision_content()
