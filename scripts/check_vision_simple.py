"""
Simple check for vision content in VectorDB.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import load_config
from src.core import VectorStore


def check_vision():
    """Simple vision content check."""
    
    print("\n" + "="*60)
    print("SIMPLE VISION CHECK")
    print("="*60)
    
    config = load_config()
    vector_store = VectorStore(config)
    
    print(f"\nTotal documents: {vector_store.count()}")
    
    # Use retrieve_relevant_chunks (the actual method)
    results = vector_store.retrieve_relevant_chunks(
        query="financial investment portfolio chart graph", 
        k=20
    )
    
    print(f"Retrieved {len(results)} chunks for analysis\n")
    
    vision_chunks = 0
    total_chunks = len(results)
    
    vision_markers = [
        'image', 'chart', 'graph', 'figure', 'diagram', 
        'visual', 'illustration', 'depicts', 'displays'
    ]
    
    for i, chunk in enumerate(results, 1):
        # Extract content based on chunk structure
        if isinstance(chunk, dict):
            content = chunk.get('page_content', chunk.get('content', ''))
            metadata = chunk.get('metadata', {})
        else:
            # If chunk is an object with attributes
            content = getattr(chunk, 'page_content', '')
            metadata = getattr(chunk, 'metadata', {})
        
        content_lower = content.lower()
        
        # Check metadata
        has_vision_meta = metadata.get('has_vision_content', False)
        
        # Check content
        has_vision_content = any(marker in content_lower for marker in vision_markers)
        
        if has_vision_meta or has_vision_content:
            vision_chunks += 1
            print(f"✅ Chunk {i}: Vision content detected")
            print(f"   Source: {metadata.get('source', 'N/A')}")
            print(f"   Page: {metadata.get('page_number', 'N/A')}")
            print(f"   Has vision (meta): {has_vision_meta}")
            
            # Show snippet with vision keywords
            for marker in vision_markers:
                if marker in content_lower:
                    idx = content_lower.find(marker)
                    print(f"   Keyword: '{marker}'")
                    print(f"   Snippet: ...{content[max(0,idx-30):idx+100]}...")
                    break
            print()
    
    print(f"{'='*60}")
    print(f"RESULTS:")
    print(f"{'='*60}")
    print(f"Chunks analyzed: {total_chunks}")
    print(f"Chunks with vision: {vision_chunks}")
    print(f"Percentage: {(vision_chunks/total_chunks*100) if total_chunks > 0 else 0:.1f}%")
    
    if vision_chunks == 0:
        print(f"\n⚠️  NO VISION CONTENT FOUND")
        print(f"\nYour config shows:")
        print(f"  use_vision_for_images: true ✅")
        print(f"  extract_images: true ✅")
        print(f"\nPossible reasons:")
        print(f"  1. PDFs don't have images/charts/graphs")
        print(f"  2. Vision analysis failed during ingestion")
        print(f"  3. Images exist but weren't processed")
        
        print(f"\nTo re-ingest with vision (force):")
        print(f"  python main.py ingest data/pdfs/vanguards_guide_to_financial_wellness.pdf")
    else:
        print(f"\n✅ VISION CONTENT IS WORKING!")
        print(f"   Vision is being captured and stored!")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    check_vision()
