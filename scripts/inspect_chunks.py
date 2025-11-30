"""
Inspect VectorDB chunks to verify vision content.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import load_config
from src.core import VectorStore


def inspect_chunks(limit: int = 5):
    """Inspect recent chunks from VectorDB."""
    
    print("\n" + "="*60)
    print("VECTORDB CHUNK INSPECTION")
    print("="*60)
    
    config = load_config()
    vector_store = VectorStore(config)
    
    print(f"\nTotal documents: {vector_store.count()}")
    print(f"\nInspecting {limit} sample chunks...\n")
    
    # Use search with a generic query to get sample chunks
    sample_query = "investment portfolio financial planning"
    results = vector_store.search(sample_query, k=limit)
    
    if not results:
        print("❌ No results found. VectorDB might be empty.")
        return
    
    for i, result in enumerate(results, 1):
        print(f"\n{'='*60}")
        print(f"CHUNK {i}")
        print(f"{'='*60}")
        
        # Metadata
        metadata = result.get('metadata', {})
        print(f"\n📋 Metadata:")
        print(f"  Source: {metadata.get('source', 'N/A')}")
        print(f"  Page: {metadata.get('page_number', 'N/A')}")
        print(f"  Chunk ID: {metadata.get('chunk_id', 'N/A')}")
        print(f"  Has vision: {metadata.get('has_vision_content', False)}")
        
        # Content
        content = result.get('content', '')
        
        # Content preview
        print(f"\n📄 Content Preview (first 300 chars):")
        print(f"  {content[:300]}...")
        
        # Check for vision markers
        vision_markers = [
            'image description:',
            'image analysis:',
            'chart shows',
            'chart depicts',
            'graph shows',
            'graph depicts',
            'visual analysis:',
            '[vision]',
            'figure shows',
            'diagram illustrates',
            'the image shows',
            'the chart displays'
        ]
        
        has_vision_markers = any(marker in content.lower() for marker in vision_markers)
        
        if has_vision_markers:
            print(f"\n  ✅ VISION CONTENT DETECTED in text!")
            # Find and show the vision content
            for marker in vision_markers:
                if marker in content.lower():
                    idx = content.lower().find(marker)
                    print(f"\n  📸 Vision snippet:")
                    print(f"  {content[max(0, idx-50):idx+200]}...")
                    break
        elif metadata.get('has_vision_content'):
            print(f"\n  ⚠️  Metadata says has_vision=True but no vision markers found")
        
        # Full content length
        print(f"\n  Total length: {len(content)} characters")
        
        # Score
        if 'score' in result:
            print(f"  Similarity score: {result['score']:.3f}")


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    inspect_chunks(limit)
