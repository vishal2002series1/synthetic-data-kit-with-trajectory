"""
ChromaDB Manager for vector storage.
"""

import chromadb
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..utils import get_logger

logger = get_logger(__name__)


class ChromaDBManager:
    """Manages ChromaDB collections for vector storage."""
    
    def __init__(
        self,
        persist_directory: str,
        collection_name: str,
        distance_metric: str = "cosine"
    ):
        """
        Initialize ChromaDB manager.
        
        Args:
            persist_directory: Directory for persistent storage
            collection_name: Name of the collection
            distance_metric: Distance metric (cosine, l2, ip)
        """
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.distance_metric = distance_metric
        
        # Create persist directory
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize client
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": distance_metric}
        )
        
        logger.info(f"Initialized ChromaDB: {collection_name}")
    
    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to collection.
        
        Args:
            documents: List of document texts
            embeddings: List of embedding vectors
            metadatas: Optional metadata for each document
            ids: Optional IDs (generated if not provided)
            
        Returns:
            List of document IDs
        """
        if not ids:
            import uuid
            ids = [str(uuid.uuid4()) for _ in range(len(documents))]
        
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(documents)} documents to {self.collection_name}")
        return ids
    
    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query collection.
        
        Args:
            query_embeddings: Query embedding vectors
            n_results: Number of results to return
            where: Metadata filter
            where_document: Document content filter
            
        Returns:
            Query results
        """
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where,
            where_document=where_document
        )
        
        return results
    
    def count(self) -> int:
        """Get number of documents in collection."""
        return self.collection.count()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        return {
            "total_documents": self.count(),
            "collection_name": self.collection_name,
            "distance_metric": self.distance_metric
        }
    
    def delete_collection(self):
        """Delete the collection."""
        self.client.delete_collection(name=self.collection_name)
        logger.info(f"Deleted collection: {self.collection_name}")
    
    def __repr__(self) -> str:
        return f"ChromaDBManager(collection={self.collection_name}, docs={self.count()})"
