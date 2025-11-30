"""
Tool Data Transformer - Create variants with correct/incorrect tool data.

Variants:
- correct: Normal tool execution with valid data
- incorrect: Tool returns wrong/mismatched data (for error handling training)
"""

from typing import Dict, List, Any
from enum import Enum
from ..utils import get_logger

logger = get_logger(__name__)


class DataVariant(Enum):
    """Types of data variants."""
    CORRECT = "correct"
    INCORRECT = "incorrect"


class ToolDataTransformer:
    """Transform tool data to create training variants."""
    
    def __init__(self, bedrock_provider):
        """Initialize tool data transformer."""
        self.provider = bedrock_provider
        logger.info("Initialized ToolDataTransformer")
    
    def transform(self, query: str) -> Dict[str, Dict[str, Any]]:
        """
        Create variants with different tool data scenarios.
        
        Args:
            query: Original query
            
        Returns:
            Dictionary mapping variant -> metadata
        """
        variants = {
            "correct": {
                "type": "correct",
                "description": "Normal tool execution with valid data"
            },
            "incorrect": {
                "type": "incorrect", 
                "description": "Tool returns mismatched or wrong data"
            }
        }
        
        logger.info(f"Created {len(variants)} tool data variants")
        return variants
    
    def get_expansion_factor(self) -> int:
        """Get expansion factor (number of variants)."""
        return 2
    
    def __repr__(self) -> str:
        return "ToolDataTransformer(variants=2)"
