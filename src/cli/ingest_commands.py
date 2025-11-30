"""CLI commands for PDF ingestion."""

from pathlib import Path
from typing import Any

from ..core import PDFParser, VectorStore
from ..utils import get_logger

logger = get_logger(__name__)


def add_ingest_parser(subparsers):
    """Add ingest command parser."""
    parser = subparsers.add_parser(
        'ingest',
        help='Ingest a single PDF file'
    )
    parser.add_argument(
        'pdf_file',
        type=str,
        help='Path to PDF file'
    )
    parser.add_argument(
        '--no-vision',
        action='store_true',
        help='Disable vision analysis for images'
    )


def add_ingest_batch_parser(subparsers):
    """Add ingest-batch command parser."""
    parser = subparsers.add_parser(
        'ingest-batch',
        help='Ingest all PDFs from a directory'
    )
    parser.add_argument(
        'pdf_dir',
        type=str,
        help='Directory containing PDF files'
    )
    parser.add_argument(
        '--no-vision',
        action='store_true',
        help='Disable vision analysis for images'
    )
    parser.add_argument(
        '--skip-errors',
        action='store_true',
        help='Skip PDFs that fail to parse'
    )


def run_ingest(args: Any, config: Any):
    """Run single PDF ingestion."""
    
    pdf_file = Path(args.pdf_file)
    
    if not pdf_file.exists():
        print(f"❌ Error: PDF file not found: {pdf_file}")
        return
    
    print(f"\n🔄 Ingesting PDF: {pdf_file.name}")
    
    # Initialize components
    vector_store = VectorStore(config)
    parser = PDFParser(
        bedrock_provider=vector_store.provider,
        chunk_size=config.pdf_processing.chunk_size,
        chunk_overlap=config.pdf_processing.chunk_overlap,
        use_vision=not args.no_vision
    )
    
    # Parse PDF
    try:
        result = parser.parse_pdf(str(pdf_file))
        
        print(f"✅ Parsed {result['total_pages']} pages into {len(result['chunks'])} chunks")
        
        # Add to vector store
        ids = vector_store.add_chunks(
            chunks=result['chunks'],
            source=pdf_file.name
        )
        
        print(f"✅ Ingested {len(ids)} chunks from {pdf_file.name}")
        print(f"Total documents in vector store: {vector_store.count()}\n")
        
    except Exception as e:
        print(f"❌ Error ingesting {pdf_file.name}: {e}\n")


def run_ingest_batch(args: Any, config: Any):
    """Run batch PDF ingestion."""
    
    pdf_dir = Path(args.pdf_dir)
    
    if not pdf_dir.exists():
        print(f"❌ Error: Directory not found: {pdf_dir}")
        return
    
    # Find all PDFs
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"⚠️  Warning: No PDF files found in {pdf_dir}")
        return
    
    print(f"\n{'='*60}")
    print(f"BATCH PDF INGESTION")
    print(f"{'='*60}")
    print(f"Found {len(pdf_files)} PDF files in {pdf_dir}")
    print(f"{'='*60}\n")
    
    # Initialize components
    vector_store = VectorStore(config)
    parser = PDFParser(
        bedrock_provider=vector_store.provider,
        chunk_size=config.pdf_processing.chunk_size,
        chunk_overlap=config.pdf_processing.chunk_overlap,
        use_vision=not args.no_vision
    )
    
    # Process each PDF
    total_chunks = 0
    successful = 0
    failed = 0
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
        
        try:
            result = parser.parse_pdf(str(pdf_file))
            ids = vector_store.add_chunks(
                chunks=result['chunks'],
                source=pdf_file.name
            )
            total_chunks += len(ids)
            successful += 1
            print(f"  ✅ {len(ids)} chunks added\n")
            
        except Exception as e:
            failed += 1
            error_msg = str(e)
            
            # Provide helpful error messages
            if "cryptography" in error_msg:
                print(f"  ❌ Encryption error: PDF may be password-protected")
                print(f"     Install: pip install cryptography\n")
            elif "wrong pointing object" in error_msg:
                print(f"  ❌ Corrupted PDF structure")
            else:
                print(f"  ❌ Error: {error_msg}\n")
            
            if not args.skip_errors:
                print(f"\n⚠️  Stopping due to error. Use --skip-errors to continue.")
                print(f"   Failed on: {pdf_file.name}\n")
                break
            else:
                print(f"  ⏭️  Skipping {pdf_file.name} (--skip-errors enabled)\n")
    
    # Summary
    print(f"{'='*60}")
    print(f"BATCH INGESTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total PDFs found: {len(pdf_files)}")
    print(f"Successfully processed: {successful}")
    print(f"Failed: {failed}")
    print(f"Total chunks added: {total_chunks}")
    print(f"Total documents in VectorDB: {vector_store.count()}")
    print(f"{'='*60}\n")
