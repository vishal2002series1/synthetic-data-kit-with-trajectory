"""
Iteration state management for multi-iteration trajectories.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class DecisionType(Enum):
    """Types of decisions in trajectory."""
    CALL = "CALL"
    ASK = "ASK"
    ANSWER = "ANSWER"


@dataclass
class ToolResult:
    """Result from a tool execution."""
    tool_name: str
    result: Any
    iteration: int
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class IterationState:
    """State for one trajectory iteration."""
    query_id: str
    query: str
    iteration: int = 0
    tool_results: List[ToolResult] = field(default_factory=list)
    
    def add_tool_results(self, results: List[ToolResult]):
        """Add tool results and increment iteration."""
        self.tool_results.extend(results)
        self.iteration += 1
    
    def to_context(self) -> Dict[str, Any]:
        """Convert state to context for decision making."""
        return {
            "query": self.query,
            "iteration": self.iteration,
            "tool_results": [
                {
                    "tool": r.tool_name,
                    "result": r.result,
                    "iteration": r.iteration
                }
                for r in self.tool_results
            ]
        }


class StateManager:
    """Manages iteration states for multiple trajectories."""
    
    def __init__(self):
        self.states: Dict[str, IterationState] = {}
    
    def initialize(self, query_id: str, query: str) -> IterationState:
        """Initialize state for a new trajectory."""
        state = IterationState(
            query_id=query_id,
            query=query,
            iteration=0
        )
        self.states[query_id] = state
        return state
    
    def get(self, query_id: str) -> Optional[IterationState]:
        """Get state by query ID."""
        return self.states.get(query_id)
    
    def delete(self, query_id: str):
        """Delete state."""
        if query_id in self.states:
            del self.states[query_id]
    
    def clear(self):
        """Clear all states."""
        self.states.clear()
