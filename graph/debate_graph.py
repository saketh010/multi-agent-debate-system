"""
Debate Graph Module

LangGraph orchestration for the multi-agent debate workflow.
Defines nodes, edges, and flow control for the debate system.
"""

from typing import Literal, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state.debate_state import DebateState, create_initial_state
from agents.moderator_agent import moderator_node
from agents.architect_agent import architect_node
from agents.performance_agent import performance_node
from agents.security_agent import security_node
from agents.scoring_agent import scoring_node
from agents.judge_agent import judge_node
from tools.tavily_search import evidence_retrieval_node


def create_debate_graph():
    """
    Create and compile the debate workflow graph.
    
    Returns:
        Compiled LangGraph with checkpointer memory
    """
    # Initialize graph with state schema
    workflow = StateGraph(DebateState)
    
    # Add nodes for each phase
    workflow.add_node("moderator", moderator_node)
    workflow.add_node("evidence_retrieval", evidence_retrieval_node)
    workflow.add_node("architect", architect_node)
    workflow.add_node("performance", performance_node)
    workflow.add_node("security", security_node)
    workflow.add_node("cross_examination", cross_examination_node)
    workflow.add_node("scoring", scoring_node)
    workflow.add_node("judge", judge_node)
    
    # Set entry point
    workflow.set_entry_point("moderator")
    
    # Define edges and flow control
    workflow.add_edge("moderator", "evidence_retrieval")
    workflow.add_edge("evidence_retrieval", "architect")
    workflow.add_edge("architect", "performance")
    workflow.add_edge("performance", "security")
    
    # Add round increment node
    workflow.add_node("increment_round", increment_round_node)
    
    # Conditional edge after security - check if more rounds needed
    workflow.add_conditional_edges(
        "security",
        should_continue_debate,
        {
            "continue": "increment_round",  # Increment round and loop back
            "cross_exam": "cross_examination",  # Move to cross-examination
        }
    )
    
    # After incrementing round, go back to architect
    workflow.add_edge("increment_round", "architect")
    
    # After cross-examination, go to scoring
    workflow.add_edge("cross_examination", "scoring")
    
    # After scoring, go to judge
    workflow.add_edge("scoring", "judge")
    
    # Judge produces final verdict and ends
    workflow.add_edge("judge", END)
    
    # Compile with memory checkpointer
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


def increment_round_node(state: DebateState) -> Dict[str, Any]:
    """
    Increment the debate round counter.
    
    Args:
        state: Current debate state
    
    Returns:
        Dict with incremented round
    """
    return {
        "round": state["round"] + 1
    }


def should_continue_debate(state: DebateState) -> Literal["continue", "cross_exam"]:
    """
    Determine if debate should continue for another round or move to cross-examination.
    
    Args:
        state: Current debate state
    
    Returns:
        "continue" for another round, "cross_exam" to move to next phase
    """
    current_round = state["round"]
    max_rounds = state["max_rounds"]
    
    if current_round < max_rounds:
        return "continue"
    else:
        return "cross_exam"


def cross_examination_node(state: DebateState) -> Dict[str, Any]:
    """
    Execute cross-examination phase where agents critique each other's arguments.
    
    Args:
        state: Current debate state
    
    Returns:
        Dict with cross-examination results
    """
    from agents.architect_agent import generate_cross_examination as arch_cross
    from agents.performance_agent import generate_cross_examination as perf_cross
    from agents.security_agent import generate_cross_examination as sec_cross
    from state.debate_state import CrossExamination
    
    cross_examinations = []
    agents = state.get("active_agents", ["architect", "performance", "security"])
    
    # Each agent examines the others
    if "architect" in agents:
        # Architect examines performance
        if "performance" in agents:
            critique = arch_cross(state, "performance")
            cross_examinations.append(CrossExamination(
                examiner="architect",
                target="performance",
                critique=critique,
                round_number=state["round"]
            ))
        
        # Architect examines security
        if "security" in agents:
            critique = arch_cross(state, "security")
            cross_examinations.append(CrossExamination(
                examiner="architect",
                target="security",
                critique=critique,
                round_number=state["round"]
            ))
    
    if "performance" in agents:
        # Performance examines architect
        if "architect" in agents:
            critique = perf_cross(state, "architect")
            cross_examinations.append(CrossExamination(
                examiner="performance",
                target="architect",
                critique=critique,
                round_number=state["round"]
            ))
        
        # Performance examines security
        if "security" in agents:
            critique = perf_cross(state, "security")
            cross_examinations.append(CrossExamination(
                examiner="performance",
                target="security",
                critique=critique,
                round_number=state["round"]
            ))
    
    if "security" in agents:
        # Security examines architect
        if "architect" in agents:
            critique = sec_cross(state, "architect")
            cross_examinations.append(CrossExamination(
                examiner="security",
                target="architect",
                critique=critique,
                round_number=state["round"]
            ))
        
        # Security examines performance
        if "performance" in agents:
            critique = sec_cross(state, "performance")
            cross_examinations.append(CrossExamination(
                examiner="security",
                target="performance",
                critique=critique,
                round_number=state["round"]
            ))
    
    return {
        "cross_examinations": cross_examinations,
        "current_phase": "scoring"
    }


def run_debate(topic: str, max_rounds: int = 2) -> Dict[str, Any]:
    """
    Run a complete debate on the given topic.
    
    Args:
        topic: The debate topic/question
        max_rounds: Maximum number of debate rounds (default: 2)
    
    Returns:
        Final state after debate completion
    """
    # Create initial state
    initial_state = create_initial_state(topic, max_rounds)
    
    # Create and compile graph
    graph = create_debate_graph()
    
    # Run the workflow
    config = {"configurable": {"thread_id": "debate_1"}}
    final_state = None
    
    for state in graph.stream(initial_state, config):
        final_state = state
    
    # Extract the final state from the last step
    if final_state and isinstance(final_state, dict):
        # Get the last node's output
        last_node = list(final_state.keys())[-1]
        return final_state[last_node]
    
    return initial_state


def get_debate_graph():
    """
    Get a compiled debate graph instance.
    
    Returns:
        Compiled LangGraph
    """
    return create_debate_graph()
