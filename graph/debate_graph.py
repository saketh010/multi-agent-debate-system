"""
Debate Graph Module

LangGraph orchestration for the multi-agent debate workflow.
Defines nodes, edges, and flow control for the debate system.
"""

from typing import Literal, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state.debate_state import DebateState, create_initial_state, HumanIntervention
from agents.moderator_agent import moderator_node
from agents.architect_agent import architect_node
from agents.performance_agent import performance_node
from agents.security_agent import security_node
from agents.scoring_agent import scoring_node
from agents.judge_agent import judge_node
from tools.tavily_search import evidence_retrieval_node


def create_debate_graph(enable_hitl: bool = False):
    """
    Create and compile the debate workflow graph.
    
    Args:
        enable_hitl: Enable Human-in-the-Loop mode with feedback checkpoints
    
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
    
    # Add human feedback nodes if HITL is enabled
    if enable_hitl:
        workflow.add_node("await_feedback_architect", create_await_feedback_node("architect"))
        workflow.add_node("await_feedback_performance", create_await_feedback_node("performance"))
        workflow.add_node("await_feedback_security", create_await_feedback_node("security"))
        workflow.add_node("review_feedback", agent_review_node)
    
    # Add round increment node
    workflow.add_node("increment_round", increment_round_node)
    
    # Set entry point
    workflow.set_entry_point("moderator")
    
    # Define edges and flow control
    workflow.add_edge("moderator", "evidence_retrieval")
    workflow.add_edge("evidence_retrieval", "architect")
    
    if enable_hitl:
        # With HITL: agent -> await_feedback (graph interrupts here for human input)
        # After resume: conditional edge checks if feedback was given -> review or skip
        workflow.add_edge("architect", "await_feedback_architect")
        workflow.add_conditional_edges(
            "await_feedback_architect",
            route_after_feedback,
            {
                "review": "review_feedback",
                "continue": "performance"
            }
        )
        
        workflow.add_edge("performance", "await_feedback_performance")
        workflow.add_conditional_edges(
            "await_feedback_performance",
            route_after_feedback,
            {
                "review": "review_feedback",
                "continue": "security"
            }
        )
        
        workflow.add_edge("security", "await_feedback_security")
        workflow.add_conditional_edges(
            "await_feedback_security",
            route_security_with_feedback,
            {
                "review": "review_feedback",
                "continue": "increment_round",
                "cross_exam": "cross_examination"
            }
        )
        
        # After review_feedback, route to the correct next agent/phase
        workflow.add_conditional_edges(
            "review_feedback",
            route_after_review,
            {
                "performance": "performance",
                "security": "security",
                "increment_round": "increment_round",
                "cross_examination": "cross_examination"
            }
        )
    else:
        # Without HITL: standard flow
        workflow.add_edge("architect", "performance")
        workflow.add_edge("performance", "security")
        
        # Conditional edge after security - check if more rounds needed
        workflow.add_conditional_edges(
            "security",
            should_continue_debate,
            {
                "continue": "increment_round",
                "cross_exam": "cross_examination",
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
    if enable_hitl:
        # interrupt_after causes graph.stream() to pause after these nodes,
        # giving the UI a chance to collect human feedback before continuing
        return workflow.compile(
            checkpointer=memory,
            interrupt_after=["await_feedback_architect", "await_feedback_performance", "await_feedback_security"]
        )
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


def create_await_feedback_node(agent_name: str):
    """
    Create a node factory for awaiting human feedback on a specific agent.
    
    Args:
        agent_name: Name of the agent to await feedback for
    
    Returns:
        Node function that marks state as awaiting feedback
    """
    def await_feedback(state: DebateState) -> Dict[str, Any]:
        """Mark that we're awaiting human feedback for this agent."""
        return {
            "awaiting_human_feedback": True,
            "pending_feedback_agent": agent_name
        }
    return await_feedback


def route_after_feedback(state: DebateState) -> Literal["review", "continue"]:
    """
    Route based on whether human feedback was provided.
    After the graph resumes from an interrupt, check if feedback was injected.
    """
    if state.get("human_interventions"):
        last_intervention = state["human_interventions"][-1]
        pending_agent = state.get("pending_feedback_agent")
        
        # Check if this feedback is for the pending agent and hasn't been reviewed yet
        if (last_intervention["agent_name"] == pending_agent and
            last_intervention.get("agent_response") is None):
            return "review"
    
    return "continue"


def route_security_with_feedback(state: DebateState) -> Literal["review", "continue", "cross_exam"]:
    """
    Route after security agent, considering both feedback and round completion.
    """
    # First check if we need to review feedback
    if state.get("human_interventions"):
        last_intervention = state["human_interventions"][-1]
        pending_agent = state.get("pending_feedback_agent")
        
        if (last_intervention["agent_name"] == pending_agent and
            last_intervention.get("agent_response") is None):
            return "review"
    
    # Otherwise check if we should continue debate
    current_round = state["round"]
    max_rounds = state["max_rounds"]
    
    if current_round < max_rounds:
        return "continue"
    else:
        return "cross_exam"


def route_after_review(state: DebateState) -> Literal["performance", "security", "increment_round", "cross_examination"]:
    """
    Route after review_feedback to the correct next step based on which agent was reviewed.
    """
    if state.get("human_interventions"):
        last = state["human_interventions"][-1]
        agent = last["agent_name"]
        if agent == "architect":
            return "performance"
        elif agent == "performance":
            return "security"
        elif agent == "security":
            if state["round"] < state["max_rounds"]:
                return "increment_round"
            else:
                return "cross_examination"
    return "performance"


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


def human_feedback_node(state: DebateState) -> Dict[str, Any]:
    """
    Node that waits for human feedback.
    This is a checkpoint where human can intervene.
    The actual feedback is injected by the interface (CLI or Streamlit).
    
    Args:
        state: Current debate state
    
    Returns:
        Dict to signal awaiting human feedback
    """
    # This node simply marks that we're waiting for human feedback
    # The actual input will be handled by the interface layer
    return {
        "awaiting_human_feedback": True,
        "current_phase": "human_feedback"
    }


def agent_review_node(state: DebateState) -> Dict[str, Any]:
    """
    Node where agent reviews and responds to human feedback.
    
    Args:
        state: Current debate state with human feedback
    
    Returns:
        Dict with agent's response to human feedback
    """
    from utils.bedrock_client import get_bedrock_client
    
    # Get the last human intervention
    if not state.get("human_interventions"):
        return {"awaiting_human_feedback": False}
    
    last_intervention = state["human_interventions"][-1]
    agent_name = last_intervention["agent_name"]
    human_feedback = last_intervention["human_feedback"]
    round_number = last_intervention["round_number"]
    
    # Get the agent's original argument
    original_argument = None
    for arg in state["arguments"]:
        if arg["agent_name"] == agent_name and arg["round_number"] == round_number:
            original_argument = arg
            break
    
    if not original_argument:
        return {"awaiting_human_feedback": False}
    
    # Construct prompt for agent to review human feedback
    prompt = f"""You are the {agent_name.upper()} agent in a technical debate about: {state['topic']}

Your original argument was:
{original_argument['argument']}

A human observer has provided the following feedback on your argument:
{human_feedback}

Please do the following:
1. Carefully consider the human's feedback
2. Decide if you AGREE or DISAGREE with their perspective
3. If you agree, revise your argument to incorporate their points
4. If you disagree, explain why and defend your original position

Respond in the following format:
DECISION: [AGREE or DISAGREE]
RESPONSE: [Your response to the human's feedback]
REVISED_ARGUMENT: [Your revised argument if you agree, or your original argument with additional defense if you disagree]
"""
    
    # Get agent's response
    bedrock_client = get_bedrock_client()
    agent_response = bedrock_client.generate_response(prompt, max_tokens=2000)
    
    # Parse the response
    agrees = "AGREE" in agent_response.split("DECISION:")[-1].split("\n")[0].upper()
    
    response_text = ""
    if "RESPONSE:" in agent_response:
        response_text = agent_response.split("RESPONSE:")[-1].split("REVISED_ARGUMENT:")[0].strip()
    
    revised_argument = ""
    if "REVISED_ARGUMENT:" in agent_response:
        revised_argument = agent_response.split("REVISED_ARGUMENT:")[-1].strip()
    
    # Update the intervention with agent's response
    updated_intervention = HumanIntervention(
        agent_name=agent_name,
        round_number=round_number,
        human_feedback=human_feedback,
        agent_response=response_text,
        agent_revised_argument=revised_argument,
        agent_agrees=agrees
    )
    
    # Remove the last intervention and add the updated one
    interventions_list = list(state["human_interventions"][:-1])
    interventions_list.append(updated_intervention)
    
    return {
        "human_interventions": interventions_list,
        "awaiting_human_feedback": False,
        "pending_feedback_agent": None
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


def run_debate_with_hitl(topic: str, max_rounds: int = 2, human_feedback_callback=None):
    """
    Run a debate with Human-in-the-Loop capability.
    After each agent's argument, pause for human feedback if provided.
    
    Args:
        topic: The debate topic/question
        max_rounds: Maximum number of debate rounds (default: 2)
        human_feedback_callback: Callback function(state, agent_name, round_num) 
                                that returns human feedback string or None
    
    Yields:
        State updates during debate execution
    """
    # Create initial state
    current_state = create_initial_state(topic, max_rounds)
    
    # Create and compile graph with HITL enabled
    graph = create_debate_graph(enable_hitl=True)
    config = {"configurable": {"thread_id": f"debate_hitl_{id(current_state)}"}}
    
    # Stream through the debate
    for state_update in graph.stream(current_state, config):
        if isinstance(state_update, dict):
            node_name = list(state_update.keys())[0]
            current_state = state_update[node_name]
            
            # Check if we're awaiting human feedback
            if current_state.get("awaiting_human_feedback") and human_feedback_callback:
                agent_name = current_state.get("pending_feedback_agent")
                round_num = current_state.get("round", 1)
                
                # Call the callback to get human feedback
                human_feedback = human_feedback_callback(current_state, agent_name, round_num)
                
                if human_feedback and human_feedback.strip():
                    # Human provided feedback - inject it into state
                    intervention = HumanIntervention(
                        agent_name=agent_name,
                        round_number=round_num,
                        human_feedback=human_feedback,
                        agent_response=None,
                        agent_revised_argument=None,
                        agent_agrees=None
                    )
                    
                    # Update the graph state with the intervention
                    current_state["human_interventions"].append(intervention)
                    
                    # Continue execution from the current checkpoint with updated state
                    # The graph will route to review_feedback node
                    for continued_update in graph.stream(None, config):
                        if isinstance(continued_update, dict):
                            node_name = list(continued_update.keys())[0]
                            current_state = continued_update[node_name]
                            yield continued_update
                else:
                    # No feedback - clear awaiting flag and continue
                    current_state["awaiting_human_feedback"] = False
                    current_state["pending_feedback_agent"] = None
                    
                    # Update state and continue
                    for continued_update in graph.stream(None, config):
                        if isinstance(continued_update, dict):
                            node_name = list(continued_update.keys())[0]
                            current_state = continued_update[node_name]
                            yield continued_update
                            if not current_state.get("awaiting_human_feedback"):
                                break
            else:
                # Yield normal state update
                yield state_update


def get_debate_graph():
    """
    Get a compiled debate graph instance.
    
    Returns:
        Compiled LangGraph
    """
    return create_debate_graph()
