"""
Question Generator - Generate questions from document chunks.
"""

import re
from typing import List, Dict, Any, Optional

from ..utils import get_logger

logger = get_logger(__name__)


class QuestionGenerator:
    """Generate questions from document chunks."""
    
    def __init__(self, bedrock_provider: Any):
        """
        Initialize question generator.
        
        Args:
            bedrock_provider: BedrockProvider instance
        """
        self.provider = bedrock_provider
        logger.info("Initialized QuestionGenerator")
    
    def generate_questions(
        self,
        chunk: str,
        n_questions: int = 3,
        complexity: str = "medium"
    ) -> List[str]:
        """
        Generate questions from a document chunk.
        
        Args:
            chunk: Document text chunk
            n_questions: Number of questions to generate
            complexity: Question complexity (simple, medium, complex)
            
        Returns:
            List of generated questions
        """
        # Complexity guidance
        complexity_map = {
            "simple": "Generate simple, straightforward questions that can be answered directly from the text. Use simple language.",
            "medium": "Generate questions that require understanding of the main concepts and relationships in the text.",
            "complex": "Generate analytical questions that require synthesis of multiple concepts and deeper understanding."
        }
        
        guidance = complexity_map.get(complexity, complexity_map["medium"])
        
        prompt = f"""Based on the following text, generate {n_questions} questions.

Text:
{chunk[:2000]}

{guidance}

IMPORTANT REQUIREMENTS:
- Questions should be natural and realistic
- DO NOT reference specific figures, charts, or page numbers
- Ask about concepts, relationships, and information
- Make questions generally applicable, not document-specific
- Avoid phrases like "according to the document" or "the text states"

Output format:
1. [Question 1]
2. [Question 2]
3. [Question 3]

Questions:"""
        
        response = self.provider.generate_text(
            prompt=prompt,
            max_tokens=400,
            temperature=0.7
        )
        
        # Parse questions
        questions = self._parse_questions(response)
        
        logger.info(f"Generated {len(questions)} {complexity} questions")
        return questions
    
    def generate_questions_batch(
        self,
        chunks: List[str],
        n_questions_per_chunk: int = 3,
        complexity: str = "medium"
    ) -> List[Dict[str, Any]]:
        """
        Generate questions from multiple chunks.
        
        Args:
            chunks: List of document chunks
            n_questions_per_chunk: Questions per chunk
            complexity: Question complexity
            
        Returns:
            List of question dictionaries with metadata
        """
        all_questions = []
        
        for i, chunk in enumerate(chunks):
            questions = self.generate_questions(
                chunk=chunk,
                n_questions=n_questions_per_chunk,
                complexity=complexity
            )
            
            for q in questions:
                all_questions.append({
                    "question": q,
                    "source_chunk": chunk[:200] + "...",
                    "chunk_id": i,
                    "complexity": complexity
                })
        
        logger.info(f"Generated {len(all_questions)} total questions from {len(chunks)} chunks")
        return all_questions
    
    def _parse_questions(self, response: str) -> List[str]:
        """Parse questions from numbered list."""
        questions = []
        
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Match numbered questions (1. , 2. , etc.)
            match = re.match(r'^\d+\.\s*(.+)$', line)
            if match:
                question = match.group(1).strip()
                # Remove any remaining document references
                question = self._remove_document_references(question)
                questions.append(question)
        
        return questions
    
    def _remove_document_references(self, text: str) -> str:
        """Remove document-specific references from text."""
        # Remove "Figure X", "Page Y", "Table Z" references
        text = re.sub(r'\b[Ff]igure\s+\d+\b', '', text)
        text = re.sub(r'\b[Pp]age\s+\d+\b', '', text)
        text = re.sub(r'\b[Tt]able\s+\d+\b', '', text)
        text = re.sub(r'\b[Cc]hart\s+\d+\b', '', text)
        
        # Remove phrases like "according to the document"
        text = re.sub(r'according to (the )?(document|text|passage)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(the )?(document|text|passage) (states|shows|indicates)', '', text, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def __repr__(self) -> str:
        return "QuestionGenerator()"
