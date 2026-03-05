"""Agents package for debate system."""

from agents.architect_agent import architect_node, generate_cross_examination as architect_cross_exam
from agents.performance_agent import performance_node, generate_cross_examination as performance_cross_exam
from agents.security_agent import security_node, generate_cross_examination as security_cross_exam
from agents.moderator_agent import (
    moderator_node,
    initialize_debate,
    start_round,
    transition_to_cross_examination,
    transition_to_scoring,
    transition_to_judge,
    conclude_debate,
    get_debate_summary
)
from agents.scoring_agent import scoring_node, format_scores
from agents.judge_agent import judge_node, format_final_decision

__all__ = [
    'architect_node',
    'performance_node',
    'security_node',
    'moderator_node',
    'scoring_node',
    'judge_node',
    'architect_cross_exam',
    'performance_cross_exam',
    'security_cross_exam',
    'initialize_debate',
    'start_round',
    'transition_to_cross_examination',
    'transition_to_scoring',
    'transition_to_judge',
    'conclude_debate',
    'get_debate_summary',
    'format_scores',
    'format_final_decision'
]
