"""
Answer Generator - Generate answers grounded in document context.
"""

import re
from typing import List, Dict, Any, Optional

from ..utils import get_logger

logger = get_logger(__name__)


class AnswerGenerator:
    """Generate answers grounded in document chunks."""
    
    def __init__(self, bedrock_provider: Any):
        """
        Initialize answer generator.
        
        Args:
            bedrock_provider: BedrockProvider instance
        """
        self.provider = bedrock_provider
        logger.info("Initialized AnswerGenerator")
    
    def generate_answer(
        self,
        question: str,
        context_chunks: List[str],
        max_context_length: int = 3000
    ) -> str:
        """
        Generate answer based on question and context.
        
        Args:
            question: Question to answer
            context_chunks: Relevant document chunks
            max_context_length: Max length of context to use
            
        Returns:
            Generated answer (abstracted, no document references)
        """
        # Combine context chunks
        context = "\n\n".join(context_chunks)
        if len(context) > max_context_length:
            context = context[:max_context_length] + "..."
        
        prompt = f"""Answer the following question based on the provided context.

Context:
{context}

Question: {question}

IMPORTANT REQUIREMENTS:
- Provide a clear, informative answer based on the context
- DO NOT reference specific figures, charts, pages, or sections
- DO NOT say "according to the document" or similar phrases
- Write the answer as if you're explaining the concept directly
- If the context doesn't contain enough information, say so briefly
- Keep the answer concise but complete (2-4 sentences typically)

Answer:"""
        
        response = self.provider.generate_text(
            prompt=prompt,
            max_tokens=500,
            temperature=0.7
        )
        
        # Remove any remaining document references
        answer = self._abstract_answer(response.strip())
        
        logger.debug(f"Generated answer for: {question[:50]}...")
        return answer
    
    def generate_answers_batch(
        self,
        qa_pairs: List[Dict[str, Any]],
        vector_store: Any,
        n_context_chunks: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate answers for multiple questions using vector store.
        
        Args:
            qa_pairs: List of question dictionaries
            vector_store: VectorStore instance for retrieving context
            n_context_chunks: Number of chunks to retrieve per question
            
        Returns:
            List of complete Q&A pairs with answers
        """
        complete_pairs = []
        
        for qa in qa_pairs:
            question = qa["question"]
            
            # Retrieve relevant chunks
            results = vector_store.query(
                query_text=question,
                n_results=n_context_chunks
            )
            
            context_chunks = results['documents'][0] if results['documents'] else []
            
            if not context_chunks:
                logger.warning(f"No context found for: {question[:50]}...")
                continue
            
            # Generate answer
            answer = self.generate_answer(
                question=question,
                context_chunks=context_chunks
            )
            
            complete_pairs.append({
                "question": question,
                "answer": answer,
                "complexity": qa.get("complexity", "medium"),
                "metadata": {
                    "n_context_chunks": len(context_chunks),
                    "chunk_id": qa.get("chunk_id")
                }
            })
        
        logger.info(f"Generated {len(complete_pairs)} complete Q&A pairs")
        return complete_pairs
    
    def _abstract_answer(self, answer: str) -> str:
        """Remove document-specific references from answer."""
        # Remove "Figure X", "Page Y", etc.
        answer = re.sub(r'\b[Ff]igure\s+\d+\b', '', answer)
        answer = re.sub(r'\b[Pp]age\s+\d+\b', '', answer)
        answer = re.sub(r'\b[Tt]able\s+\d+\b', '', answer)
        answer = re.sub(r'\b[Cc]hart\s+\d+\b', '', answer)
        answer = re.sub(r'\b[Ss]ection\s+\d+\b', '', answer)
        
        # Remove document reference phrases
        answer = re.sub(r'[Aa]ccording to (the )?(document|text|passage|material)', '', answer)
        answer = re.sub(r'[Tt]he (document|text|passage) (states|shows|indicates|mentions)', '', answer)
        answer = re.sub(r'[Aa]s (stated|shown|mentioned|indicated) in (the )?(document|text|passage)', '', answer)
        
        # Clean up extra spaces
        answer = re.sub(r'\s+', ' ', answer).strip()
        
        return answer
    
    def __repr__(self) -> str:
        return "AnswerGenerator()"
