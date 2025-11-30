"""
Test if PDF vision analysis is actually happening.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import load_config
from src.core import PDFParser, VectorStore


def test_pdf_vision():
    """Test PDF vision analysis."""
    
    print("\n" + "="*60)
    print("PDF VISION ANALYSIS TEST")
    print("="*60)
    
    config = load_config()
    vector_store = VectorStore(config)
    
    # Create parser WITH vision explicitly enabled
    parser = PDFParser(
        bedrock_provider=vector_store.provider,
        chunk_size=config.pdf_processing.chunk_size,
        chunk_overlap=config.pdf_processing.chunk_overlap,
        use_vision=True
    )
    
    print(f"\nParser configuration:")
    print(f"  use_vision: {parser.use_vision}")
    print(f"  chunk_size: {parser.chunk_size}")
    print(f"  chunk_overlap: {parser.chunk_overlap}")
    
    # Test on one PDF
    pdf_path = "data/pdfs/vanguards_guide_to_financial_wellness.pdf"
    
    print(f"\nParsing: {pdf_path}")
    print("(Watch for vision API calls...)\n")
    
    result = parser.parse_pdf(pdf_path)
    
    print(f"\n{'='*60}")
    print(f"PARSING RESULTS")
    print(f"{'='*60}")
    print(f"Total pages: {result['total_pages']}")
    print(f"Total chunks: {len(result['chunks'])}")
    
    # Check for vision content
    vision_chunks = 0
    for chunk in result['chunks']:
        if chunk.metadata.get('has_vision_content'):
            vision_chunks += 1
    
    print(f"Chunks with vision metadata: {vision_chunks}/{len(result['chunks'])}")
    
    if vision_chunks == 0:
        print(f"\n⚠️  NO VISION METADATA FOUND")
        print(f"\nThis means either:")
        print(f"  1. PDF has no images/charts")
        print(f"  2. Vision API is not being called")
        print(f"  3. Vision content isn't being flagged in metadata")
    else:
        print(f"\n✅ Vision metadata found in {vision_chunks} chunks!")
        
        # Show a sample
        for chunk in result['chunks']:
            if chunk.metadata.get('has_vision_content'):
                print(f"\nSample vision chunk:")
                print(f"  Page: {chunk.metadata.get('page_number', 'N/A')}")
                print(f"  Content preview: {chunk.page_content[:300]}...")
                break
    
    # Check if page numbers are being captured
    pages_with_numbers = sum(1 for c in result['chunks'] 
                            if c.metadata.get('page_number') is not None)
    
    print(f"\nPage number tracking:")
    print(f"  Chunks with page numbers: {pages_with_numbers}/{len(result['chunks'])}")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    test_pdf_vision()
