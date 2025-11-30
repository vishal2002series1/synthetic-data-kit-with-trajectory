"""
PDF Parser with multi-modal support (text + vision).
"""

import base64
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pypdf import PdfReader
from PIL import Image
import io

from ..utils import get_logger

logger = get_logger(__name__)


@dataclass
class PDFChunk:
    """Represents a chunk of PDF content."""
    text: str
    page_number: int
    chunk_id: int
    metadata: Dict[str, Any]
    image_analysis: Optional[str] = None


class PDFParser:
    """Parse PDFs with text extraction and vision analysis."""
    
    def __init__(
        self,
        bedrock_provider: Any,
        chunk_size: int = 4000,
        chunk_overlap: int = 200,
        use_vision: bool = True
    ):
        """
        Initialize PDF parser.
        
        Args:
            bedrock_provider: BedrockProvider instance for vision
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            use_vision: Whether to use vision for images
        """
        self.provider = bedrock_provider
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.use_vision = use_vision
        
        logger.info(f"Initialized PDFParser (chunk_size={chunk_size}, vision={use_vision})")
    
    def parse_pdf(
        self,
        pdf_path: str,
        analyze_images: bool = None
    ) -> Dict[str, Any]:
        """
        Parse PDF file.
        
        Args:
            pdf_path: Path to PDF file
            analyze_images: Override use_vision setting
            
        Returns:
            Dictionary with chunks and metadata
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        analyze_images = analyze_images if analyze_images is not None else self.use_vision
        
        logger.info(f"Parsing PDF: {pdf_path.name}")
        
        # Extract text
        reader = PdfReader(str(pdf_path))
        
        all_text = []
        page_metadata = []
        
        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            all_text.append(text)
            page_metadata.append({
                "page": page_num,
                "char_count": len(text)
            })
        
        # Create chunks
        chunks = self._create_chunks(
            all_text,
            source=pdf_path.name
        )
        
        logger.info(f"Created {len(chunks)} chunks from {len(reader.pages)} pages")
        
        return {
            "chunks": chunks,
            "total_pages": len(reader.pages),
            "source": pdf_path.name,
            "page_metadata": page_metadata
        }
    
    def _create_chunks(
        self,
        pages: List[str],
        source: str
    ) -> List[PDFChunk]:
        """
        Create overlapping chunks from pages.
        
        Args:
            pages: List of page texts
            source: Source filename
            
        Returns:
            List of PDFChunk objects
        """
        chunks = []
        chunk_id = 0
        
        for page_num, page_text in enumerate(pages, 1):
            # Split page into chunks
            words = page_text.split()
            
            for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
                chunk_words = words[i:i + self.chunk_size]
                chunk_text = ' '.join(chunk_words)
                
                if len(chunk_text.strip()) < 50:  # Skip tiny chunks
                    continue
                
                chunk = PDFChunk(
                    text=chunk_text,
                    page_number=page_num,
                    chunk_id=chunk_id,
                    metadata={
                        "source": source,
                        "page": page_num,
                        "chunk_id": chunk_id,
                        "char_count": len(chunk_text)
                    }
                )
                
                chunks.append(chunk)
                chunk_id += 1
        
        return chunks
    
    def chunks_to_documents(
        self,
        chunks: List[PDFChunk]
    ) -> tuple[List[str], List[Dict[str, Any]]]:
        """
        Convert chunks to documents and metadata for ChromaDB.
        
        Args:
            chunks: List of PDFChunk objects
            
        Returns:
            Tuple of (documents, metadatas)
        """
        documents = [chunk.text for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        return documents, metadatas
    
    def __repr__(self) -> str:
        return f"PDFParser(chunk_size={self.chunk_size}, vision={self.use_vision})"
