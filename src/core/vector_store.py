"""
VectorStore - Unified interface for ChromaDB + Bedrock.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from .chromadb_manager import ChromaDBManager
from .bedrock_provider import BedrockProvider
from ..utils import get_logger

logger = get_logger(__name__)


class VectorStore:
    """
    High-level vector store combining ChromaDB and Bedrock embeddings.
    """
    
    def __init__(self, config: Any):
        """
        Initialize VectorStore.
        
        Args:
            config: Configuration object
        """
        self.config = config
        
        # Initialize ChromaDB
        self.db = ChromaDBManager(
            persist_directory=config.chromadb.persist_directory,
            collection_name=config.chromadb.collection_name,
            distance_metric=config.chromadb.distance_metric
        )
        
        # Initialize Bedrock for embeddings
        self.provider = BedrockProvider(
            model_id=config.bedrock.model_id,
            embedding_model_id=config.bedrock.embedding_model_id,
            region=config.bedrock.region
        )
        
        logger.info("Initialized VectorStore")
    
    def add_chunks(
        self,
        chunks: List[Any],
        source: str = "unknown"
    ) -> List[str]:
        """
        Add document chunks with automatic embedding generation.
        
        Args:
            chunks: List of PDFChunk objects or text strings
            source: Source identifier
            
        Returns:
            List of document IDs
        """
        if not chunks:
            logger.warning("No chunks to add")
            return []
        
        logger.info(f"Adding {len(chunks)} chunks from {source}")
        
        # Extract texts and metadatas
        texts = []
        metadatas = []
        
        for chunk in chunks:
            if isinstance(chunk, str):
                texts.append(chunk)
                metadatas.append({"source": source})
            else:
                texts.append(chunk.text)
                metadatas.append(chunk.metadata)
        
        # Deduplication: Track seen texts
        seen_texts = set()
        unique_texts = []
        unique_metadatas = []
        duplicates_removed = 0
        
        for text, metadata in zip(texts, metadatas):
            if text not in seen_texts:
                seen_texts.add(text)
                unique_texts.append(text)
                unique_metadatas.append(metadata)
            else:
                duplicates_removed += 1
        
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate chunks")
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(unique_texts)} unique chunks...")
        embeddings = self.provider.generate_embeddings_batch(unique_texts)
        
        # Add to ChromaDB
        ids = self.db.add_documents(
            documents=unique_texts,
            embeddings=embeddings,
            metadatas=unique_metadatas
        )
        
        logger.info(f"Added {len(ids)} chunks to vector store")
        return ids
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query vector store by text.
        
        Args:
            query_text: Search query
            n_results: Number of results
            where: Metadata filter
            
        Returns:
            Query results
        """
        # Generate query embedding
        query_embedding = self.provider.generate_embedding(query_text)
        
        # Query ChromaDB
        results = self.db.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        return results
    
    def count(self) -> int:
        """Get number of documents in store."""
        return self.db.count()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return self.db.get_stats()
    
    def __repr__(self) -> str:
        return f"VectorStore(docs={self.count()}, collection={self.config.chromadb.collection_name})"
