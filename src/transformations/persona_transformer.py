"""
Persona Transformer - Transform queries based on user personas.

Personas:
- P1: First-time investor (simple language, uncertain)
- P2: Experienced professional (direct, efficient)
- P3: Technical analyst (data-driven, precise)
- P4: Anxious investor (risk-averse, cautious)
- P5: Directive executive (assertive, time-conscious)
"""

from typing import Dict, List
from ..utils import get_logger

logger = get_logger(__name__)


class PersonaTransformer:
    """Transform queries based on user personas."""
    
    PERSONAS = {
        "P1": {
            "name": "First-time Investor",
            "description": "New to investing, uses simple language, asks basic questions",
            "style": "Simple, conversational, may be uncertain or ask for explanations"
        },
        "P2": {
            "name": "Experienced Professional",
            "description": "Familiar with investment concepts, direct and efficient",
            "style": "Professional, concise, uses standard industry terminology"
        },
        "P3": {
            "name": "Technical Analyst",
            "description": "Data-driven, wants specific metrics and numbers",
            "style": "Analytical, precise, requests quantitative details"
        },
        "P4": {
            "name": "Anxious Investor",
            "description": "Risk-averse, concerned about losses, seeks reassurance",
            "style": "Cautious, uncertain, multiple questions, risk-focused"
        },
        "P5": {
            "name": "Directive Executive",
            "description": "Time-conscious, assertive, expects quick answers",
            "style": "Direct commands, minimal details, action-oriented"
        }
    }
    
    def __init__(self, bedrock_provider):
        """Initialize persona transformer."""
        self.provider = bedrock_provider
        logger.info(f"Initialized PersonaTransformer with {len(self.PERSONAS)} personas")
    
    def transform(self, query: str, persona: str = None) -> Dict[str, str]:
        """
        Transform query for different personas.
        
        Args:
            query: Original query
            persona: Specific persona (P1-P5) or None for all
            
        Returns:
            Dictionary mapping persona_id -> transformed_query
        """
        if persona:
            personas_to_transform = [persona]
        else:
            personas_to_transform = list(self.PERSONAS.keys())
        
        results = {}
        
        for p_id in personas_to_transform:
            transformed = self._transform_for_persona(query, p_id)
            results[p_id] = transformed
        
        logger.info(f"Transformed query for {len(results)} personas")
        return results
    
    def _transform_for_persona(self, query: str, persona_id: str) -> str:
        """Transform query for a specific persona."""
        
        persona = self.PERSONAS[persona_id]
        
        prompt = f"""Transform the following query to match the style and tone of this user persona:

PERSONA: {persona['name']}
Description: {persona['description']}
Style: {persona['style']}

ORIGINAL QUERY:
{query}

REQUIREMENTS:
- Maintain the core meaning and intent of the original query
- Adapt the language, tone, and phrasing to match the persona
- Keep the query concise (1-3 sentences)
- Make it sound natural for this type of user
- Do NOT add extra questions or change the fundamental ask

EXAMPLES:

Original: "How should I allocate my portfolio?"

P1 (First-time): "I'm new to investing and wondering how I should split up my money across different investments?"

P2 (Professional): "What's the recommended asset allocation for my portfolio?"

P3 (Technical): "Can you provide the optimal allocation percentages by asset class for portfolio optimization?"

P4 (Anxious): "I'm worried about losing money... how should I carefully distribute my investments to minimize risk?"

P5 (Directive): "Show me the allocation breakdown now."

YOUR TRANSFORMED QUERY (for {persona['name']}):"""
        
        response = self.provider.generate_text(
            prompt=prompt,
            max_tokens=200,
            temperature=0.7
        )
        
        # Clean up response
        transformed = response.strip()
        
        # Remove any quotation marks
        transformed = transformed.strip('"').strip("'")
        
        logger.debug(f"{persona_id}: {transformed}")
        
        return transformed
    
    def get_expansion_factor(self) -> int:
        """Get expansion factor (number of personas)."""
        return len(self.PERSONAS)
    
    def __repr__(self) -> str:
        return f"PersonaTransformer(personas={len(self.PERSONAS)})"
