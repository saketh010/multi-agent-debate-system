"""
Architect Agent Module

Focuses on scalability, system architecture design, and structural considerations.
Provides architecture-focused arguments with evidence and citations.
"""

from typing import Dict, Any
from state.debate_state import DebateState, AgentArgument
from utils.bedrock_client import get_bedrock_client
from tools.tavily_search import search_evidence


AGENT_NAME = "architect"


def get_system_prompt() -> str:
    """Get the system prompt for the architect agent."""
    return """You are an expert software architect specializing in system design, scalability, and architectural patterns.

Your role in this debate is to provide insights focused on:
- System architecture and design patterns
- Scalability considerations
- Component organization and modularity
- Architectural trade-offs
- Long-term maintainability from an architectural perspective

Provide well-reasoned arguments backed by evidence and real-world examples.
Be technical, precise, and cite specific architectural principles."""


def generate_opening_argument(state: DebateState) -> str:
    """Generate an opening argument for the architect agent."""
    topic = state["topic"]
    evidence_items = [e for e in state.get("evidence", []) if e.get("agent") == AGENT_NAME]
    
    evidence_text = "\n".join([f"- {e.get('summary', '')}" for e in evidence_items[:3]])
    
    prompt = f"""Topic: {topic}

You are presenting your opening argument as the Architecture expert in a structured debate.

Relevant Evidence:
{evidence_text if evidence_text else 'No specific evidence available.'}

Provide your architectural perspective on this topic.

Format your response EXACTLY as follows:

Argument:
[Your main architectural argument here - 3-4 sentences]

Key Points:
- [Point 1]
- [Point 2]
- [Point 3]

Evidence:
[Cite specific evidence, examples, or case studies]

Sources:
[List any frameworks, systems, or documented patterns referenced]"""
    
    client = get_bedrock_client()
    response = client.generate_response(prompt, system_prompt=get_system_prompt())
    return response


def generate_counter_argument(state: DebateState) -> str:
    """Generate a counter-argument responding to other agents."""
    topic = state["topic"]
    other_arguments = [arg for arg in state.get("arguments", []) 
                      if arg["agent_name"] != AGENT_NAME and arg["round_number"] == state["round"]]
    
    other_args_text = "\n\n".join([
        f"{arg['agent_name'].upper()}:\n{arg['argument'][:300]}..."
        for arg in other_arguments[:2]
    ])
    
    prompt = f"""Topic: {topic}

You are in Round {state['round']} of the debate. Review the arguments from other perspectives:

{other_args_text if other_args_text else 'No other arguments available yet.'}

Provide a counter-argument from your architectural perspective. Address specific points raised by others and explain architectural considerations they may have overlooked.

Format your response EXACTLY as follows:

Argument:
[Your counter-argument addressing other perspectives - 3-4 sentences]

Key Points:
- [Point 1]
- [Point 2]
- [Point 3]

Evidence:
[Supporting evidence for your counter-argument]

Sources:
[Referenced materials]"""
    
    client = get_bedrock_client()
    response = client.generate_response(prompt, system_prompt=get_system_prompt())
    return response


def generate_cross_examination(state: DebateState, target_agent: str) -> str:
    """Generate a cross-examination critique of another agent's argument."""
    target_arguments = [arg for arg in state.get("arguments", []) 
                       if arg["agent_name"] == target_agent]
    
    if not target_arguments:
        return f"No arguments found from {target_agent} to examine."
    
    latest_arg = target_arguments[-1]
    
    prompt = f"""You are cross-examining the {target_agent.upper()} agent's argument.

Their argument:
{latest_arg['argument']}

From your architectural expertise, identify:
1. Potential weaknesses in their reasoning
2. Overlooked architectural implications
3. Questions that challenge their assumptions

Provide a constructive but critical analysis (2-3 paragraphs)."""
    
    client = get_bedrock_client()
    response = client.generate_response(prompt, system_prompt=get_system_prompt())
    return response


def architect_node(state: DebateState) -> Dict[str, Any]:
    """
    Main node function for the architect agent.
    
    Args:
        state: Current debate state
    
    Returns:
        Dict with updated state fields
    """
    current_round = state["round"]
    current_phase = state.get("current_phase", "debate")
    
    # Generate appropriate response based on phase
    if current_phase == "debate":
        if current_round == 1:
            response = generate_opening_argument(state)
        else:
            response = generate_counter_argument(state)
        
        # Parse response to extract structured data
        argument_data = parse_argument_response(response, current_round)
        
        return {
            "arguments": [argument_data]
        }
    
    return {}


def parse_argument_response(response: str, round_number: int) -> AgentArgument:
    """
    Parse the formatted response into structured argument data.
    
    Args:
        response: Raw response from LLM
        round_number: Current debate round
    
    Returns:
        AgentArgument: Structured argument data
    """
    lines = response.strip().split("\n")
    
    argument = ""
    evidence = []
    sources = []
    
    section = None
    for line in lines:
        line = line.strip()
        if line.startswith("Argument:"):
            section = "argument"
            continue
        elif line.startswith("Evidence:"):
            section = "evidence"
            continue
        elif line.startswith("Sources:"):
            section = "sources"
            continue
        elif line.startswith("Key Points:"):
            section = "argument"  # Include key points in argument
            continue
        
        if section == "argument" and line:
            argument += line + " "
        elif section == "evidence" and line:
            evidence.append(line)
        elif section == "sources" and line:
            if line.startswith("-") or line.startswith("*"):
                sources.append(line[1:].strip())
            else:
                sources.append(line)
    
    return AgentArgument(
        agent_name=AGENT_NAME,
        argument=argument.strip() or response[:500],
        evidence=evidence if evidence else ["No specific evidence cited"],
        sources=sources if sources else ["General architectural principles"],
        round_number=round_number
    )
