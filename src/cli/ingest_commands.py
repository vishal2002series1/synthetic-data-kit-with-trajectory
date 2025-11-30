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


def run_ingest(args: Any, config: Any):
    """Run single PDF ingestion."""
    
    pdf_file = Path(args.pdf_file)
    
    if not pdf_file.exists():
        logger.error(f"PDF file not found: {pdf_file}")
        return
    
    logger.info(f"Ingesting PDF: {pdf_file}")
    
    # Initialize components
    vector_store = VectorStore(config)
    parser = PDFParser(
        bedrock_provider=vector_store.provider,
        chunk_size=config.pdf_processing.chunk_size,
        chunk_overlap=config.pdf_processing.chunk_overlap,
        use_vision=not args.no_vision
    )
    
    # Parse PDF
    result = parser.parse_pdf(str(pdf_file))
    
    logger.info(f"Parsed {result['total_pages']} pages into {len(result['chunks'])} chunks")
    
    # Add to vector store
    ids = vector_store.add_chunks(
        chunks=result['chunks'],
        source=pdf_file.name
    )
    
    logger.info(f"✅ Ingested {len(ids)} chunks from {pdf_file.name}")
    logger.info(f"Total documents in vector store: {vector_store.count()}")


def run_ingest_batch(args: Any, config: Any):
    """Run batch PDF ingestion."""
    
    pdf_dir = Path(args.pdf_dir)
    
    if not pdf_dir.exists():
        logger.error(f"Directory not found: {pdf_dir}")
        return
    
    # Find all PDFs
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {pdf_dir}")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files")
    
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
    
    for i, pdf_file in enumerate(pdf_files, 1):
        logger.info(f"[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
        
        try:
            result = parser.parse_pdf(str(pdf_file))
            ids = vector_store.add_chunks(
                chunks=result['chunks'],
                source=pdf_file.name
            )
            total_chunks += len(ids)
            logger.info(f"  ✅ {len(ids)} chunks")
            
        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
    
    logger.info(f"\n✅ Batch ingestion complete!")
    logger.info(f"Processed {len(pdf_files)} PDFs")
    logger.info(f"Added {total_chunks} chunks")
    logger.info(f"Total documents: {vector_store.count()}")
