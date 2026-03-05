"""
Moderator Agent Module

Controls debate flow, initializes rounds, and ensures structured outputs.
Manages the progression of the debate through different phases.
"""

from typing import Dict, Any
from datetime import datetime
from state.debate_state import DebateState
from utils.bedrock_client import get_bedrock_client


def initialize_debate(state: DebateState) -> Dict[str, Any]:
    """
    Initialize the debate with opening remarks.
    
    Args:
        state: Current debate state
    
    Returns:
        Dict with updated state fields
    """
    topic = state["topic"]
    
    prompt = f"""You are the moderator of a technical debate on the following topic:

\"{topic}\"

Provide a brief introduction to frame the debate (2-3 sentences). Explain what aspects will be examined by the three expert agents:
- Architecture Expert
- Performance Expert  
- Security Expert

Keep it professional and neutral."""
    
    client = get_bedrock_client()
    introduction = client.generate_response(
        prompt,
        system_prompt="You are a professional debate moderator.",
        max_tokens=500
    )
    
    return {
        "current_phase": "evidence",
        "round": 1,
        "debate_started": datetime.now().isoformat()
    }


def start_round(state: DebateState) -> Dict[str, Any]:
    """
    Start a new debate round.
    
    Args:
        state: Current debate state
    
    Returns:
        Dict with updated state fields
    """
    current_round = state["round"]
    
    return {
        "round": current_round + 1,
        "current_phase": "debate"
    }


def transition_to_cross_examination(state: DebateState) -> Dict[str, Any]:
    """
    Transition to cross-examination phase.
    
    Args:
        state: Current debate state
    
    Returns:
        Dict with updated state fields
    """
    return {
        "current_phase": "cross_examination"
    }


def transition_to_scoring(state: DebateState) -> Dict[str, Any]:
    """
    Transition to scoring phase.
    
    Args:
        state: Current debate state
    
    Returns:
        Dict with updated state fields
    """
    return {
        "current_phase": "scoring"
    }


def transition_to_judge(state: DebateState) -> Dict[str, Any]:
    """
    Transition to final judge phase.
    
    Args:
        state: Current debate state
    
    Returns:
        Dict with updated state fields
    """
    return {
        "current_phase": "judge"
    }


def conclude_debate(state: DebateState) -> Dict[str, Any]:
    """
    Conclude the debate.
    
    Args:
        state: Current debate state
    
    Returns:
        Dict with updated state fields
    """
    return {
        "current_phase": "completed",
        "debate_ended": datetime.now().isoformat()
    }


def moderator_node(state: DebateState) -> Dict[str, Any]:
    """
    Main node function for the moderator agent.
    
    Args:
        state: Current debate state
    
    Returns:
        Dict with updated state fields
    """
    current_phase = state.get("current_phase", "moderator")
    
    if current_phase == "moderator":
        return initialize_debate(state)
    
    return {}


def get_debate_summary(state: DebateState) -> str:
    """
    Generate a summary of the debate progress.
    
    Args:
        state: Current debate state
    
    Returns:
        str: Formatted summary
    """
    topic = state["topic"]
    round_num = state["round"]
    phase = state.get("current_phase", "unknown")
    num_arguments = len(state.get("arguments", []))
    num_examinations = len(state.get("cross_examinations", []))
    
    summary = f"""DEBATE SUMMARY
{'=' * 50}
Topic: {topic}
Round: {round_num}
Phase: {phase}
Arguments Presented: {num_arguments}
Cross-Examinations: {num_examinations}
{'=' * 50}"""
    
    return summary
