"""
Direct ChromaDB inspection to check vision content.
"""

import sys
from pathlib import Path
import chromadb

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import load_config


def check_chromadb_direct():
    """Direct ChromaDB inspection."""
    
    print("\n" + "="*60)
    print("DIRECT CHROMADB INSPECTION")
    print("="*60)
    
    config = load_config()
    
    # Connect to ChromaDB
    client = chromadb.PersistentClient(
        path=config.chromadb.persist_directory
    )
    
    collection = client.get_collection(
        name=config.chromadb.collection_name
    )
    
    total = collection.count()
    print(f"\nTotal documents: {total}")
    
    # Get sample chunks
    results = collection.get(
        limit=50,
        include=['documents', 'metadatas']
    )
    
    print(f"Retrieved {len(results['documents'])} chunks\n")
    
    vision_chunks = 0
    vision_markers = [
        'image', 'chart', 'graph', 'figure', 'diagram',
        'visual', 'illustration', 'depicts', 'shows'
    ]
    
    for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas']), 1):
        has_vision_meta = meta.get('has_vision_content', False)
        has_vision_text = any(marker in doc.lower() for marker in vision_markers)
        
        if has_vision_meta or has_vision_text:
            vision_chunks += 1
            print(f"✅ Chunk {i} has vision:")
            print(f"   Source: {meta.get('source', 'N/A')}")
            print(f"   Page: {meta.get('page_number', 'N/A')}")
            print(f"   Vision meta: {has_vision_meta}")
            
            if has_vision_text:
                for marker in vision_markers:
                    if marker in doc.lower():
                        idx = doc.lower().find(marker)
                        print(f"   Contains: '{marker}'")
                        print(f"   Text: ...{doc[max(0,idx-20):idx+80]}...")
                        break
            print()
    
    print(f"{'='*60}")
    print(f"SUMMARY:")
    print(f"{'='*60}")
    print(f"Total chunks: {total}")
    print(f"Sampled: {len(results['documents'])}")
    print(f"With vision: {vision_chunks}")
    print(f"Vision rate: {(vision_chunks/len(results['documents'])*100):.1f}%")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    check_chromadb_direct()
