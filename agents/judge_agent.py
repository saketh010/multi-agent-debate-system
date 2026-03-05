"""
Judge Agent Module

Analyzes all arguments and scores to produce a final verdict.
Provides comprehensive summary and reasoning for the decision.
"""

from typing import Dict, Any
from state.debate_state import DebateState, JudgeDecision
from utils.bedrock_client import get_bedrock_client


def judge_node(state: DebateState) -> Dict[str, Any]:
    """
    Main node function for the judge agent.
    
    Args:
        state: Current debate state
    
    Returns:
        Dict with final decision
    """
    topic = state["topic"]
    arguments = state.get("arguments", [])
    scores = state.get("scores", [])
    cross_examinations = state.get("cross_examinations", [])
    
    # Prepare arguments summary
    args_by_agent = {}
    for arg in arguments:
        agent_name = arg["agent_name"]
        if agent_name not in args_by_agent:
            args_by_agent[agent_name] = []
        args_by_agent[agent_name].append(arg["argument"])
    
    args_summary = "\n\n".join([
        f"{agent.upper()}:\n" + "\n".join(args)
        for agent, args in args_by_agent.items()
    ])
    
    # Prepare scores summary
    scores_summary = "\n".join([
        f"{score['agent_name'].upper()}: {score['total_score']:.1f}/40 - {score['feedback']}"
        for score in scores
    ])
    
    # Generate final decision
    prompt = f"""You are the final judge in a technical debate.

Topic: {topic}

ARGUMENTS PRESENTED:
{args_summary}

SCORES:
{scores_summary}

Based on the quality of arguments, evidence, and scores, make your final judgment.

Provide your decision in this EXACT format:

Winner: [Agent name]

Summary:
[2-3 sentence summary of the debate]

Key Points:
- [Key point 1]
- [Key point 2]
- [Key point 3]

Reasoning:
[2-3 paragraphs explaining why this agent won, what made their arguments strongest, and how the other perspectives contributed to the discussion]"""
    
    client = get_bedrock_client()
    response = client.generate_response(
        prompt,
        system_prompt="You are an impartial technical debate judge with expertise in software engineering.",
        temperature=0.3
    )
    
    # Parse decision
    decision = parse_judge_decision(response)
    
    return {
        "final_decision": decision,
        "current_phase": "completed"
    }


def parse_judge_decision(response: str) -> JudgeDecision:
    """
    Parse judge's response into structured decision.
    
    Args:
        response: Raw judge response
    
    Returns:
        JudgeDecision: Structured decision data
    """
    lines = response.strip().split("\n")
    
    winner = "architect"  # default
    summary = ""
    key_points = []
    reasoning = ""
    
    section = None
    reasoning_lines = []
    summary_lines = []
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("Winner:"):
            winner_text = line.split(":", 1)[1].strip().lower()
            # Extract agent name
            for agent in ["architect", "performance", "security"]:
                if agent in winner_text:
                    winner = agent
                    break
            continue
        elif line.startswith("Summary:"):
            section = "summary"
            continue
        elif line.startswith("Key Points:"):
            section = "key_points"
            continue
        elif line.startswith("Reasoning:"):
            section = "reasoning"
            continue
        
        if section == "summary" and line and not line.startswith(("Key", "Reasoning")):
            summary_lines.append(line)
        elif section == "key_points" and line:
            if line.startswith("-") or line.startswith("*"):
                key_points.append(line[1:].strip())
            elif line and not line.startswith(("Summary", "Reasoning")):
                key_points.append(line)
        elif section == "reasoning" and line:
            reasoning_lines.append(line)
    
    summary = " ".join(summary_lines) if summary_lines else "No summary provided."
    reasoning = " ".join(reasoning_lines) if reasoning_lines else "No reasoning provided."
    
    if not key_points:
        key_points = ["Decision based on overall argument quality"]
    
    return JudgeDecision(
        winner=winner,
        summary=summary,
        key_points=key_points,
        reasoning=reasoning
    )


def format_final_decision(decision: JudgeDecision) -> str:
    """
    Format the final decision for display.
    
    Args:
        decision: The judge's decision
    
    Returns:
        str: Formatted decision
    """
    output = "\n" + "="*60 + "\n"
    output += "FINAL VERDICT\n"
    output += "="*60 + "\n\n"
    
    output += f"🏆 WINNER: {decision['winner'].upper()}\n\n"
    
    output += f"Summary:\n{decision['summary']}\n\n"
    
    output += "Key Points:\n"
    for point in decision['key_points']:
        output += f"  • {point}\n"
    
    output += f"\nReasoning:\n{decision['reasoning']}\n"
    
    output += "\n" + "="*60 + "\n"
    
    return output
