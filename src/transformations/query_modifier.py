"""
Query Modifier - Adjust query complexity levels.

Complexity Levels:
- Q-: Simplified (beginner-friendly)
- Q: Original (as-is)
- Q+: Complex (advanced, multi-part)
"""

from typing import Dict, List
from ..utils import get_logger

logger = get_logger(__name__)


class QueryModifier:
    """Modify query complexity levels."""
    
    COMPLEXITY_LEVELS = {
        "Q-": {
            "name": "Simplified",
            "description": "Break down into simpler terms, beginner-friendly",
            "guidance": "Use everyday language, shorter sentences, avoid jargon"
        },
        "Q": {
            "name": "Original",
            "description": "Keep as-is",
            "guidance": "No modification needed"
        },
        "Q+": {
            "name": "Complex",
            "description": "Make more sophisticated, multi-faceted",
            "guidance": "Add nuance, multiple aspects, technical depth"
        }
    }
    
    def __init__(self, bedrock_provider):
        """Initialize query modifier."""
        self.provider = bedrock_provider
        logger.info(f"Initialized QueryModifier with {len(self.COMPLEXITY_LEVELS)} levels")
    
    def transform(self, query: str, complexity: str = None) -> Dict[str, str]:
        """
        Transform query to different complexity levels.
        
        Args:
            query: Original query
            complexity: Specific level (Q-, Q, Q+) or None for all
            
        Returns:
            Dictionary mapping complexity -> transformed_query
        """
        if complexity:
            levels_to_transform = [complexity]
        else:
            levels_to_transform = list(self.COMPLEXITY_LEVELS.keys())
        
        results = {}
        
        for level in levels_to_transform:
            if level == "Q":
                # Original - no transformation
                results[level] = query
            else:
                transformed = self._transform_for_complexity(query, level)
                results[level] = transformed
        
        logger.info(f"Transformed query to {len(results)} complexity levels")
        return results
    
    def _transform_for_complexity(self, query: str, complexity: str) -> str:
        """Transform query for specific complexity level."""
        
        level = self.COMPLEXITY_LEVELS[complexity]
        
        if complexity == "Q-":
            # Simplify
            prompt = f"""Simplify this query to make it more beginner-friendly:

ORIGINAL QUERY:
{query}

REQUIREMENTS:
- Use everyday, non-technical language
- Break complex ideas into simpler terms
- Keep it short and direct (1-2 sentences)
- Maintain the core question/intent
- Make it accessible to someone new to the topic

EXAMPLES:

Original: "What's the optimal Sharpe ratio for my risk-adjusted portfolio?"
Simplified: "How can I get good returns without taking too much risk?"

Original: "Analyze the correlation between my equity exposure and volatility."
Simplified: "Are my stocks making my portfolio too risky?"

YOUR SIMPLIFIED QUERY:"""
            
        else:  # Q+
            # Make more complex
            prompt = f"""Make this query more sophisticated and detailed:

ORIGINAL QUERY:
{query}

REQUIREMENTS:
- Add analytical depth and nuance
- Include multiple aspects or considerations
- Use precise technical terminology where appropriate
- Make it multi-faceted but still coherent (2-3 sentences)
- Show advanced understanding of the topic

EXAMPLES:

Original: "How should I diversify my portfolio?"
Complex: "What diversification strategy would optimize my risk-adjusted returns across multiple asset classes while considering my time horizon, tax implications, and current market correlations?"

Original: "Is my portfolio too risky?"
Complex: "Based on historical volatility metrics, Value at Risk calculations, and stress testing against market downturns, how does my current portfolio risk profile compare to optimal risk levels for my investment horizon and objectives?"

YOUR COMPLEX QUERY:"""
        
        response = self.provider.generate_text(
            prompt=prompt,
            max_tokens=250,
            temperature=0.7
        )
        
        # Clean up
        transformed = response.strip().strip('"').strip("'")
        
        logger.debug(f"{complexity}: {transformed}")
        
        return transformed
    
    def get_expansion_factor(self) -> int:
        """Get expansion factor (number of complexity levels)."""
        return len(self.COMPLEXITY_LEVELS)
    
    def __repr__(self) -> str:
        return f"QueryModifier(levels={len(self.COMPLEXITY_LEVELS)})"
