"""
QA Generator - Complete Q&A generation pipeline from documents.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from .question_generator import QuestionGenerator
from .answer_generator import AnswerGenerator
from ..utils import get_logger, write_jsonl

logger = get_logger(__name__)


class QAGenerator:
    """
    Complete Q&A generation pipeline.
    
    Generates Q&A pairs from documents in ChromaDB:
    1. Retrieve chunks from vector store
    2. Generate questions from chunks
    3. Generate answers using RAG (retrieve + generate)
    4. Abstract away document references
    5. Output clean Q&A pairs for training
    """
    
    def __init__(
        self,
        bedrock_provider: Any,
        vector_store: Any
    ):
        """
        Initialize QA generator.
        
        Args:
            bedrock_provider: BedrockProvider instance
            vector_store: VectorStore instance
        """
        self.provider = bedrock_provider
        self.vector_store = vector_store
        
        self.question_gen = QuestionGenerator(bedrock_provider)
        self.answer_gen = AnswerGenerator(bedrock_provider)
        
        logger.info("Initialized QAGenerator")
    
    def generate_qa_from_documents(
        self,
        n_pairs: int = 50,
        complexity: str = "all",
        questions_per_chunk: int = 3,
        min_chunk_length: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Generate Q&A pairs from documents in vector store.
        
        Args:
            n_pairs: Target number of Q&A pairs
            complexity: Question complexity ("simple", "medium", "complex", "all")
            questions_per_chunk: Questions to generate per chunk
            min_chunk_length: Minimum chunk length to consider
            
        Returns:
            List of Q&A pair dictionaries
        """
        logger.info(f"Generating {n_pairs} Q&A pairs (complexity={complexity})")
        
        # Get document count
        total_docs = self.vector_store.count()
        logger.info(f"Vector store contains {total_docs} documents")
        
        if total_docs == 0:
            logger.error("Vector store is empty! Ingest documents first.")
            return []
        
        # Determine how many chunks we need
        chunks_needed = max(10, n_pairs // questions_per_chunk)
        chunks_needed = min(chunks_needed, total_docs)
        
        logger.info(f"Retrieving {chunks_needed} chunks for processing...")
        
        # Retrieve diverse chunks (we'll query with different terms)
        chunks = self._retrieve_diverse_chunks(chunks_needed, min_chunk_length)
        
        logger.info(f"Retrieved {len(chunks)} valid chunks")
        
        # Generate questions
        if complexity == "all":
            complexities = ["simple", "medium", "complex"]
            chunks_per_complexity = len(chunks) // 3
            
            all_questions = []
            for comp in complexities:
                comp_chunks = chunks[:chunks_per_complexity]
                questions = self.question_gen.generate_questions_batch(
                    chunks=comp_chunks,
                    n_questions_per_chunk=questions_per_chunk,
                    complexity=comp
                )
                all_questions.extend(questions)
                chunks = chunks[chunks_per_complexity:]  # Use different chunks
        else:
            all_questions = self.question_gen.generate_questions_batch(
                chunks=chunks,
                n_questions_per_chunk=questions_per_chunk,
                complexity=complexity
            )
        
        logger.info(f"Generated {len(all_questions)} questions")
        
        # Limit to target
        all_questions = all_questions[:n_pairs]
        
        # Generate answers using RAG
        logger.info("Generating answers using RAG...")
        qa_pairs = self.answer_gen.generate_answers_batch(
            qa_pairs=all_questions,
            vector_store=self.vector_store,
            n_context_chunks=3
        )
        
        logger.info(f"Generated {len(qa_pairs)} complete Q&A pairs")
        
        return qa_pairs
    
    def _retrieve_diverse_chunks(
        self,
        n_chunks: int,
        min_length: int
    ) -> List[str]:
        """
        Retrieve diverse chunks from vector store.
        
        Uses multiple queries to get diverse content.
        """
        # Query terms for diversity
        query_terms = [
            "information",
            "process",
            "method",
            "concept",
            "explanation",
            "example",
            "analysis",
            "comparison"
        ]
        
        chunks = []
        seen_chunks = set()
        chunks_per_query = (n_chunks // len(query_terms)) + 1
        
        for term in query_terms:
            if len(chunks) >= n_chunks:
                break
            
            results = self.vector_store.query(
                query_text=term,
                n_results=chunks_per_query
            )
            
            if results['documents']:
                for chunk in results['documents'][0]:
                    if len(chunk) >= min_length and chunk not in seen_chunks:
                        chunks.append(chunk)
                        seen_chunks.add(chunk)
                        
                        if len(chunks) >= n_chunks:
                            break
        
        return chunks[:n_chunks]
    
    def save_qa_pairs(
        self,
        qa_pairs: List[Dict[str, Any]],
        output_file: Path,
        format_for_training: bool = True
    ):
        """
        Save Q&A pairs to file.
        
        Args:
            qa_pairs: List of Q&A pairs
            output_file: Output file path
            format_for_training: If True, format for training (Q, A fields)
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if format_for_training:
            # Format for training: simple Q and A fields
            formatted = [
                {
                    "Q": pair["question"],
                    "A": pair["answer"],
                    "complexity": pair["complexity"]
                }
                for pair in qa_pairs
            ]
        else:
            formatted = qa_pairs
        
        write_jsonl(formatted, output_file)
        logger.info(f"Saved {len(formatted)} Q&A pairs to {output_file}")
    
    def __repr__(self) -> str:
        return f"QAGenerator(docs={self.vector_store.count()})"
