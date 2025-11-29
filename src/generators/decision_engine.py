"""
Decision Engine - Makes CALL/ASK/ANSWER decisions for trajectories.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..utils import get_logger

logger = get_logger(__name__)


class DecisionType(Enum):
    """Types of decisions in trajectory."""
    CALL = "CALL"
    ASK = "ASK"
    ANSWER = "ANSWER"


@dataclass
class Decision:
    """Represents a decision with reasoning."""
    type: DecisionType
    reasoning: str
    tools: Optional[List[str]] = None
    clarification: Optional[str] = None
    answer: Optional[str] = None


class DecisionEngine:
    """Makes decisions about whether to CALL tools, ASK for clarification, or ANSWER."""
    
    def __init__(self, bedrock_provider: Any):
        """Initialize decision engine."""
        self.provider = bedrock_provider
        logger.info("Initialized DecisionEngine")
    
    def decide(
        self,
        query: str,
        context: List[Dict[str, Any]],
        available_tools: List[Dict[str, Any]],
        iteration: int,
        max_iterations: int = 3
    ) -> Decision:
        """Decide whether to CALL, ASK, or ANSWER."""
        logger.debug(f"Making decision for iteration {iteration}")
        
        # Build decision prompt
        prompt = self._build_decision_prompt(
            query=query,
            context=context,
            available_tools=available_tools,
            iteration=iteration,
            max_iterations=max_iterations
        )
        
        # Get decision from LLM
        response = self.provider.generate_text(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7
        )
        
        # Parse decision
        decision = self._parse_decision(response, query, context)
        
        logger.info(f"Decision: {decision.type.value}")
        return decision
    
    def _build_decision_prompt(
        self,
        query: str,
        context: List[Dict[str, Any]],
        available_tools: List[Dict[str, Any]],
        iteration: int,
        max_iterations: int
    ) -> str:
        """Build prompt for decision making."""
        
        # Format available tools
        tools_desc = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in available_tools
        ])
        
        # Format context
        if context:
            context_desc = "\n".join([
                f"Iteration {r['iteration']}: Called {r['tool']}, got: {str(r['result'])[:100]}..."
                for r in context
            ])
        else:
            context_desc = "No previous tool results yet."
        
        prompt = f"""You are an AI assistant deciding the next step in answering a user query.

User Query: {query}

Current Iteration: {iteration} (max: {max_iterations})

Available Tools:
{tools_desc}

Previous Tool Results:
{context_desc}

Your task: Decide whether to:
1. CALL - Call one or more tools to get more information
2. ASK - Ask the user for clarification (if query is ambiguous)
3. ANSWER - Provide the final answer (if you have enough information)

CRITICAL DECISION RULES:
- **Iteration 0 with NO context**: You should almost ALWAYS use CALL to gather information from available tools
- **search_knowledge_base is available**: Use it to retrieve relevant information from documents
- **PREFER using tools over relying on general knowledge** - The goal is to generate training data that demonstrates tool usage
- **Only ANSWER without tools if**:
  - Query is about client-specific information you don't have (then ASK instead)
  - Query is completely outside the domain of available tools
  - You already have sufficient context from previous tool calls
- **At max iterations**: Must provide an ANSWER even if incomplete

EXAMPLES OF GOOD DECISIONS:

Query: "How do neural networks work?"
Available: search_knowledge_base
Decision: CALL search_knowledge_base
Reasoning: Even though I know about neural networks, I should search documents to provide a grounded answer based on available information.

Query: "What are the differences between supervised and unsupervised learning?"
Available: search_knowledge_base
Decision: CALL search_knowledge_base
Reasoning: The query asks about concepts that likely exist in the knowledge base. I should retrieve this information rather than rely on general knowledge.

Query: "What is my account balance?"
Available: search_knowledge_base, get_account_info
Decision: ASK
Reasoning: The query requires specific client information I don't have. I need clarification on which account or client ID.

Provide your response in this format:

DECISION: [CALL/ASK/ANSWER]

REASONING: [Explain why you made this decision in 2-3 sentences. Think step by step about what information you have and what you need.]

[If CALL]
TOOLS: [comma-separated list of tool names to call]

[If ASK]
CLARIFICATION: [What specific clarification do you need from the user?]

[If ANSWER]
ANSWER: [Your complete answer to the user's query based on the context]

Your response:"""
        
        return prompt
    
    def _parse_decision(
        self,
        response: str,
        query: str,
        context: List[Dict[str, Any]]
    ) -> Decision:
        """Parse decision from LLM response."""
        
        lines = response.strip().split('\n')
        
        decision_type = None
        reasoning = ""
        tools = []
        clarification = ""
        answer = ""
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("DECISION:"):
                decision_text = line.replace("DECISION:", "").strip().upper()
                if "CALL" in decision_text:
                    decision_type = DecisionType.CALL
                elif "ASK" in decision_text:
                    decision_type = DecisionType.ASK
                elif "ANSWER" in decision_text:
                    decision_type = DecisionType.ANSWER
                current_section = "decision"
                
            elif line.startswith("REASONING:"):
                current_section = "reasoning"
                reasoning = line.replace("REASONING:", "").strip()
                
            elif line.startswith("TOOLS:"):
                current_section = "tools"
                tools_text = line.replace("TOOLS:", "").strip()
                tools = [t.strip() for t in tools_text.split(",")]
                
            elif line.startswith("CLARIFICATION:"):
                current_section = "clarification"
                clarification = line.replace("CLARIFICATION:", "").strip()
                
            elif line.startswith("ANSWER:"):
                current_section = "answer"
                answer = line.replace("ANSWER:", "").strip()
                
            elif line and current_section:
                if current_section == "reasoning":
                    reasoning += " " + line
                elif current_section == "clarification":
                    clarification += " " + line
                elif current_section == "answer":
                    answer += " " + line
        
        # Default to ANSWER if parsing failed
        if decision_type is None:
            logger.warning("Could not parse decision, defaulting to ANSWER")
            decision_type = DecisionType.ANSWER
            if not answer:
                answer = "I apologize, but I need more information to answer your query properly."
            if not reasoning:
                reasoning = "Decision parsing failed, providing default response."
        
        return Decision(
            type=decision_type,
            reasoning=reasoning.strip(),
            tools=tools if decision_type == DecisionType.CALL else None,
            clarification=clarification.strip() if decision_type == DecisionType.ASK else None,
            answer=answer.strip() if decision_type == DecisionType.ANSWER else None
        )
    
    def __repr__(self) -> str:
        return "DecisionEngine()"
