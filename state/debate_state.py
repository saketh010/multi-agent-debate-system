"""
Debate State Module

Defines the shared state structure for the multi-agent debate system.
This state is passed between all LangGraph nodes during debate execution.
"""

from typing import TypedDict, List, Dict, Optional, Annotated
from operator import add


class AgentArgument(TypedDict):
    """Structure for an individual agent's argument."""
    agent_name: str
    argument: str
    evidence: List[str]
    sources: List[str]
    round_number: int


class CrossExamination(TypedDict):
    """Structure for cross-examination between agents."""
    examiner: str
    target: str
    critique: str
    round_number: int


class HumanIntervention(TypedDict):
    """Structure for human feedback on agent arguments."""
    agent_name: str
    round_number: int
    human_feedback: str
    agent_response: Optional[str]
    agent_revised_argument: Optional[str]
    agent_agrees: Optional[bool]


class AgentScore(TypedDict):
    """Structure for agent scoring."""
    agent_name: str
    logical_reasoning: float
    evidence_quality: float
    technical_accuracy: float
    relevance: float
    total_score: float
    feedback: str


class JudgeDecision(TypedDict):
    """Structure for final judge decision."""
    winner: str
    summary: str
    key_points: List[str]
    reasoning: str


class DebateState(TypedDict):
    """
    Complete state structure for the debate workflow.
    
    This state is shared across all LangGraph nodes and maintains
    the entire context of the debate including arguments, evidence,
    scores, and final decision.
    """
    # Core debate information
    topic: str
    round: int
    max_rounds: int
    
    # Agent arguments by round
    arguments: Annotated[List[AgentArgument], add]
    
    # Evidence collected by agents
    evidence: Annotated[List[Dict[str, any]], add]
    
    # Cross-examination exchanges
    cross_examinations: Annotated[List[CrossExamination], add]
    
    # Human interventions
    human_interventions: Annotated[List[HumanIntervention], add]
    
    # Pending human feedback flag
    awaiting_human_feedback: bool
    pending_feedback_agent: Optional[str]
    
    # Scoring results
    scores: List[AgentScore]
    
    # Final judge decision
    final_decision: Optional[JudgeDecision]
    
    # Workflow control
    current_phase: str  # moderator, evidence, debate, cross_exam, scoring, judge
    
    # Agent participation tracking
    active_agents: List[str]
    
    # Metadata
    debate_started: Optional[str]
    debate_ended: Optional[str]


def create_initial_state(topic: str, max_rounds: int = 2) -> DebateState:
    """
    Create an initial debate state with default values.
    
    Args:
        topic: The debate topic/question
        max_rounds: Maximum number of debate rounds (default: 2)
    
    Returns:
        DebateState: Initialized debate state
    """
    return DebateState(
        topic=topic,
        round=0,
        max_rounds=max_rounds,
        arguments=[],
        evidence=[],
        cross_examinations=[],
        human_interventions=[],
        awaiting_human_feedback=False,
        pending_feedback_agent=None,
        scores=[],
        final_decision=None,
        current_phase="moderator",
        active_agents=["architect", "performance", "security"],
        debate_started=None,
        debate_ended=None
    )
