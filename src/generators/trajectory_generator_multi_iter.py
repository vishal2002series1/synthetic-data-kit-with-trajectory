"""
Multi-Iteration Trajectory Generator

Generates trajectories with CALL/ASK/ANSWER decisions.
Creates multiple training examples per query (one per iteration).

Format: {Q, COT, Tool Set, Decision}
"""

import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .decision_engine import DecisionEngine, DecisionType
from ..core.iteration_state import IterationState, StateManager, ToolResult
from ..utils import get_logger, write_jsonl

logger = get_logger(__name__)


@dataclass
class TrainingExample:
    """
    One training example: {Q, COT, Tool Set, Decision}
    """
    query: str
    chain_of_thought: str
    tool_set: List[Dict[str, Any]]
    decision: str
    context: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self, field_names: Dict[str, str]) -> Dict[str, Any]:
        """
        Convert to dictionary using configured field names.
        
        Args:
            field_names: Mapping from standard names to config names
                        {"query": "Q", "cot": "COT", ...}
        """
        result = {
            field_names.get("query", "Q"): self.query,
            field_names.get("cot", "COT"): self.chain_of_thought,
            field_names.get("tools", "Tool Set"): self.tool_set,
            field_names.get("decision", "Decision"): self.decision
        }
        
        if self.context:
            result["Context"] = self.context
        
        if self.metadata:
            result["metadata"] = self.metadata
        
        return result


class TrajectoryGeneratorMultiIter:
    """
    Generates multi-iteration trajectories with CALL/ASK/ANSWER decisions.
    
    Each query generates 1-3 training examples (one per iteration).
    
    Example trajectory:
      Iteration 0: CALL decision → Training Example 1
      Iteration 1: ANSWER decision → Training Example 2
      Total: 2 training examples from 1 query
    """
    
    def __init__(
        self,
        bedrock_provider: Any,
        vector_store: Any,
        config: Any,
        max_iterations: int = 3
    ):
        """
        Initialize multi-iteration trajectory generator.
        
        Args:
            bedrock_provider: BedrockProvider instance
            vector_store: VectorStore instance
            config: Configuration object
            max_iterations: Maximum iterations per query
        """
        self.provider = bedrock_provider
        self.vector_store = vector_store
        self.config = config
        self.max_iterations = max_iterations
        
        # Initialize decision engine and state manager
        self.decision_engine = DecisionEngine(bedrock_provider)
        self.state_manager = StateManager()
        
        # Load tool definitions
        self.tools = self._load_tool_definitions()
        
        # Get output schema from config
        self.output_schema = config.output.schema
        self.field_names = {
            "query": self.output_schema.fields.query,
            "cot": self.output_schema.fields.cot,
            "tools": self.output_schema.fields.tools,
            "decision": self.output_schema.fields.decision
        }
        
        logger.info(f"Initialized TrajectoryGeneratorMultiIter (max_iterations={max_iterations})")
    
    def _load_tool_definitions(self) -> List[Dict[str, Any]]:
        """Load tool definitions from tools.json."""
        tools_file = Path(self.config.tools.definitions_file)
        
        if not tools_file.exists():
            logger.warning(f"Tool definitions file not found: {tools_file}")
            return []
        
        try:
            with open(tools_file, 'r') as f:
                tools_data = json.load(f)
                tools = tools_data.get("tools", [])
                logger.info(f"Loaded {len(tools)} tool definitions")
                return tools
        except Exception as e:
            logger.error(f"Error loading tool definitions: {e}")
            return []
    
    def generate_trajectory(
        self,
        query: str,
        query_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TrainingExample]:
        """
        Generate multi-iteration trajectory for a query.
        
        Returns list of training examples (one per iteration).
        
        Args:
            query: User query
            query_id: Optional unique identifier
            metadata: Optional metadata
            
        Returns:
            List of TrainingExample objects
        """
        query_id = query_id or str(uuid.uuid4())
        training_examples = []
        
        logger.info(f"Generating trajectory for query_id={query_id}")
        logger.info(f"Query: {query[:100]}...")
        
        # Initialize state: S^(0) = [Q]
        state = self.state_manager.initialize(query_id, query)
        
        # Iterate up to max_iterations
        for iteration in range(self.max_iterations):
            logger.info(f"=== Iteration {iteration} ===")
            
            # Get current context
            context = state.to_context()
            
            # Make decision: CALL, ASK, or ANSWER?
            decision = self.decision_engine.decide(
                query=query,
                context=context["tool_results"],
                available_tools=self.tools,
                iteration=iteration,
                max_iterations=self.max_iterations
            )
            
            logger.info(f"Decision: {decision.type.value}")
            
            # Create training example for this iteration
            example = self._create_training_example(
                query=query,
                context=context["tool_results"],
                decision=decision,
                iteration=iteration,
                metadata=metadata
            )
            training_examples.append(example)
            
            # Execute based on decision type
            if decision.type == DecisionType.CALL:
                # Execute tools and add results to state
                tool_results = self._execute_tools(
                    tools=decision.tools,
                    query=query,
                    iteration=iteration
                )
                state.add_tool_results(tool_results)
                logger.info(f"Called {len(decision.tools)} tools, advancing to iteration {state.iteration}")
                
            elif decision.type == DecisionType.ASK:
                # Stop - waiting for user input
                logger.info(f"ASK decision: {decision.clarification[:50]}...")
                break
                
            elif decision.type == DecisionType.ANSWER:
                # Done!
                logger.info(f"ANSWER decision: {decision.answer[:50]}...")
                break
        
        # Cleanup state
        self.state_manager.delete(query_id)
        
        logger.info(f"Generated {len(training_examples)} training examples")
        return training_examples
    
    def _create_training_example(
        self,
        query: str,
        context: List[Dict[str, Any]],
        decision: Any,
        iteration: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TrainingExample:
        """
        Create one training example for current iteration.
        
        Format: {Q, COT, Tool Set, Decision}
        """
        # Format tools based on decision type
        if decision.type == DecisionType.CALL:
            tool_set = self._format_tools_for_call(decision.tools)
            decision_str = "CALL"
            
        elif decision.type == DecisionType.ASK:
            tool_set = []
            decision_str = f"ASK: {decision.clarification}"
            
        elif decision.type == DecisionType.ANSWER:
            tool_set = []
            decision_str = f"ANSWER: {decision.answer}"
        else:
            tool_set = []
            decision_str = "UNKNOWN"
        
        # Build metadata
        example_metadata = {
            "iteration": iteration,
            "decision_type": decision.type.value
        }
        if metadata:
            example_metadata.update(metadata)
        
        return TrainingExample(
            query=query,
            chain_of_thought=decision.reasoning,  # COT = the reasoning
            tool_set=tool_set,
            decision=decision_str,
            context=context if iteration > 0 else None,
            metadata=example_metadata
        )
    
    def _format_tools_for_call(self, tool_names: List[str]) -> List[Dict[str, Any]]:
        """
        Format tool names into proper tool call format.
        
        Includes tool name, parameters schema, and description.
        """
        formatted_tools = []
        
        for tool_name in tool_names:
            # Find tool definition
            tool_def = next((t for t in self.tools if t["name"] == tool_name), None)
            
            if tool_def:
                formatted_tools.append({
                    "name": tool_name,
                    "description": tool_def.get("description", ""),
                    "parameters": tool_def.get("parameters", {})
                })
            else:
                # Tool not found, add minimal info
                formatted_tools.append({
                    "name": tool_name,
                    "description": f"Tool {tool_name}",
                    "parameters": {}
                })
        
        return formatted_tools
    
    def _execute_tools(
        self,
        tools: List[str],
        query: str,
        iteration: int
    ) -> List[ToolResult]:
        """
        Execute specified tools and return results.
        
        Uses vector store for search_knowledge_base tool.
        """
        tool_results = []
        
        for tool_name in tools:
            if tool_name == "search_knowledge_base":
                # Use vector store to search
                results = self.vector_store.query(
                    query_text=query,
                    n_results=3
                )
                
                chunks = results['documents'][0] if results['documents'] else []
                
                result = ToolResult(
                    tool_name=tool_name,
                    result=f"Retrieved {len(chunks)} relevant documents: " + 
                           " | ".join([chunk[:100] + "..." for chunk in chunks[:2]]),
                    iteration=iteration,
                    metadata={"n_results": len(chunks)}
                )
                tool_results.append(result)
                
            else:
                # Other tools - return placeholder
                result = ToolResult(
                    tool_name=tool_name,
                    result=f"[Tool {tool_name} executed successfully]",
                    iteration=iteration
                )
                tool_results.append(result)
        
        return tool_results
    
    def save_training_examples(
        self,
        examples: List[TrainingExample],
        output_file: Path,
        format: str = "jsonl"
    ):
        """
        Save training examples to file.
        
        Args:
            examples: List of TrainingExample objects
            output_file: Output file path
            format: "jsonl" or "json"
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dictionaries
        examples_dict = [ex.to_dict(self.field_names) for ex in examples]
        
        if format == "jsonl":
            write_jsonl(examples_dict, output_file)
        elif format == "json":
            with open(output_file, 'w') as f:
                json.dump(examples_dict, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Saved {len(examples)} training examples to {output_file}")
    
    def __repr__(self) -> str:
        return f"TrajectoryGeneratorMultiIter(docs={self.vector_store.count()}, max_iter={self.max_iterations})"
