"""State package for debate system."""

from state.debate_state import (
    DebateState,
    AgentArgument,
    CrossExamination,
    AgentScore,
    JudgeDecision,
    create_initial_state
)

__all__ = [
    'DebateState',
    'AgentArgument',
    'CrossExamination',
    'AgentScore',
    'JudgeDecision',
    'create_initial_state'
]
