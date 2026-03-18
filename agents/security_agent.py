"""
Security Agent Module

Focuses on vulnerabilities, attack surface, system safety, and security best practices.
Provides security-focused arguments with evidence and citations.
"""

from typing import Dict, Any
from state.debate_state import DebateState, AgentArgument
from utils.bedrock_client import get_bedrock_client
from tools.tavily_search import search_evidence


AGENT_NAME = "security"


def get_system_prompt() -> str:
    """Get the system prompt for the security agent."""
    return """You are an expert security engineer specializing in system security, vulnerability assessment, and threat mitigation.

Your role in this debate is to provide insights focused on:
- Security vulnerabilities and risks
- Attack surface and threat vectors
- Security best practices and standards
- Data protection and privacy
- Security trade-offs and implications

Provide well-reasoned arguments backed by security research, vulnerability data, and real-world incidents.
Be technical, precise, and cite specific security concerns and mitigations."""


def generate_opening_argument(state: DebateState) -> str:
    """Generate an opening argument for the security agent."""
    topic = state["topic"]
    image_context = state.get("image_context", "")
    evidence_items = [e for e in state.get("evidence", []) if e.get("agent") == AGENT_NAME]
    
    evidence_text = "\n".join([f"- {e.get('summary', '')}" for e in evidence_items[:3]])
    
    image_block = f"\nImage-derived context:\n{image_context}\n" if image_context else ""

    prompt = f"""Topic: {topic}
{image_block}

You are presenting your opening argument as the Security expert in a structured debate.

Relevant Evidence:
{evidence_text if evidence_text else 'No specific evidence available.'}

Provide your security-focused perspective on this topic.

Format your response EXACTLY as follows:

Argument:
[Your main security argument here - 3-4 sentences]

Key Points:
- [Point 1]
- [Point 2]
- [Point 3]

Evidence:
[Cite specific vulnerabilities, incidents, or security research]

Sources:
[List any security standards, frameworks, or documented incidents referenced]"""
    
    client = get_bedrock_client()
    response = client.generate_response(prompt, system_prompt=get_system_prompt())
    return response


def generate_counter_argument(state: DebateState) -> str:
    """Generate a counter-argument responding to other agents."""
    topic = state["topic"]
    image_context = state.get("image_context", "")
    other_arguments = [arg for arg in state.get("arguments", []) 
                      if arg["agent_name"] != AGENT_NAME and arg["round_number"] == state["round"]]
    
    other_args_text = "\n\n".join([
        f"{arg['agent_name'].upper()}:\n{arg['argument'][:300]}..."
        for arg in other_arguments[:2]
    ])
    
    image_block = f"\nImage-derived context:\n{image_context}\n" if image_context else ""

    prompt = f"""Topic: {topic}
{image_block}

You are in Round {state['round']} of the debate. Review the arguments from other perspectives:

{other_args_text if other_args_text else 'No other arguments available yet.'}

Provide a counter-argument from your security perspective. Address specific points raised by others and explain security implications they may have overlooked.

Format your response EXACTLY as follows:

Argument:
[Your counter-argument addressing other perspectives - 3-4 sentences]

Key Points:
- [Point 1]
- [Point 2]
- [Point 3]

Evidence:
[Supporting security evidence]

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

From your security expertise, identify:
1. Security risks they haven't addressed
2. Potential vulnerabilities in their approach
3. Questions about threat mitigation and security posture

Provide a constructive but critical analysis (2-3 paragraphs)."""
    
    client = get_bedrock_client()
    response = client.generate_response(prompt, system_prompt=get_system_prompt())
    return response


def security_node(state: DebateState) -> Dict[str, Any]:
    """
    Main node function for the security agent.
    
    Args:
        state: Current debate state
    
    Returns:
        Dict with updated state fields
    """
    current_round = state["round"]
    current_phase = state.get("current_phase", "debate")
    
    if current_phase == "debate":
        if current_round == 1:
            response = generate_opening_argument(state)
        else:
            response = generate_counter_argument(state)
        
        argument_data = parse_argument_response(response, current_round)
        
        return {
            "arguments": [argument_data]
        }
    
    return {}


def parse_argument_response(response: str, round_number: int) -> AgentArgument:
    """Parse the formatted response into structured argument data."""
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
            section = "argument"
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
        sources=sources if sources else ["General security principles"],
        round_number=round_number
    )
