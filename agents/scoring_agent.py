"""
Scoring Agent Module

Evaluates all arguments based on multiple criteria and assigns scores.
Provides detailed feedback on argument quality.
"""

from typing import Dict, Any, List
from state.debate_state import DebateState, AgentScore
from utils.bedrock_client import get_bedrock_client


def evaluate_argument(agent_name: str, argument: str, evidence: List[str]) -> Dict[str, Any]:
    """
    Evaluate a single agent's argument.
    
    Args:
        agent_name: Name of the agent
        argument: The argument text
        evidence: List of evidence items
    
    Returns:
        Dict with scoring details
    """
    prompt = f"""Evaluate the following technical argument on these criteria:

1. Logical Reasoning (0-10): Coherence, structure, and logical flow
2. Evidence Quality (0-10): Strength and relevance of citations
3. Technical Accuracy (0-10): Correctness of technical claims
4. Relevance (0-10): How well it addresses the debate topic

Agent: {agent_name.upper()}

Argument:
{argument}

Evidence:
{chr(10).join(evidence)}

Provide your evaluation in this EXACT format:

Logical Reasoning: [score]
Evidence Quality: [score]
Technical Accuracy: [score]
Relevance: [score]

Feedback:
[2-3 sentences explaining the scores]"""
    
    client = get_bedrock_client()
    response = client.generate_response(
        prompt,
        system_prompt="You are an expert debate judge focused on technical accuracy and argumentation quality.",
        temperature=0.3
    )
    
    return parse_evaluation(response)


def parse_evaluation(response: str) -> Dict[str, Any]:
    """
    Parse evaluation response into structured scores.
    
    Args:
        response: Raw evaluation response
    
    Returns:
        Dict with parsed scores and feedback
    """
    scores = {
        "logical_reasoning": 7.0,
        "evidence_quality": 7.0,
        "technical_accuracy": 7.0,
        "relevance": 7.0,
        "feedback": ""
    }
    
    lines = response.strip().split("\n")
    feedback_started = False
    feedback_lines = []
    
    for line in lines:
        line = line.strip()
        
        if "Logical Reasoning:" in line:
            try:
                score = float(line.split(":")[1].strip())
                scores["logical_reasoning"] = min(max(score, 0), 10)
            except:
                pass
        elif "Evidence Quality:" in line:
            try:
                score = float(line.split(":")[1].strip())
                scores["evidence_quality"] = min(max(score, 0), 10)
            except:
                pass
        elif "Technical Accuracy:" in line:
            try:
                score = float(line.split(":")[1].strip())
                scores["technical_accuracy"] = min(max(score, 0), 10)
            except:
                pass
        elif "Relevance:" in line:
            try:
                score = float(line.split(":")[1].strip())
                scores["relevance"] = min(max(score, 0), 10)
            except:
                pass
        elif "Feedback:" in line:
            feedback_started = True
            continue
        elif feedback_started and line:
            feedback_lines.append(line)
    
    scores["feedback"] = " ".join(feedback_lines) if feedback_lines else "No feedback provided."
    
    return scores


def scoring_node(state: DebateState) -> Dict[str, Any]:
    """
    Main node function for the scoring agent.
    
    Args:
        state: Current debate state
    
    Returns:
        Dict with updated state fields containing scores
    """
    arguments = state.get("arguments", [])
    
    # Group arguments by agent
    agent_arguments = {}
    for arg in arguments:
        agent_name = arg["agent_name"]
        if agent_name not in agent_arguments:
            agent_arguments[agent_name] = []
        agent_arguments[agent_name].append(arg)
    
    # Score each agent's overall performance
    scores = []
    
    for agent_name, args in agent_arguments.items():
        # Combine all arguments for this agent
        combined_argument = " ".join([a["argument"] for a in args])
        combined_evidence = []
        for a in args:
            combined_evidence.extend(a.get("evidence", []))
        
        # Evaluate
        evaluation = evaluate_argument(agent_name, combined_argument, combined_evidence)
        
        # Calculate total score
        total = (
            evaluation["logical_reasoning"] +
            evaluation["evidence_quality"] +
            evaluation["technical_accuracy"] +
            evaluation["relevance"]
        )
        
        score = AgentScore(
            agent_name=agent_name,
            logical_reasoning=evaluation["logical_reasoning"],
            evidence_quality=evaluation["evidence_quality"],
            technical_accuracy=evaluation["technical_accuracy"],
            relevance=evaluation["relevance"],
            total_score=total,
            feedback=evaluation["feedback"]
        )
        
        scores.append(score)
    
    return {
        "scores": scores,
        "current_phase": "judge"
    }


def format_scores(scores: List[AgentScore]) -> str:
    """
    Format scores for display.
    
    Args:
        scores: List of agent scores
    
    Returns:
        str: Formatted scores
    """
    output = "\n" + "="*60 + "\n"
    output += "ARGUMENT SCORES\n"
    output += "="*60 + "\n\n"
    
    # Sort by total score
    sorted_scores = sorted(scores, key=lambda x: x["total_score"], reverse=True)
    
    for score in sorted_scores:
        output += f"Agent: {score['agent_name'].upper()}\n"
        output += f"  Logical Reasoning:   {score['logical_reasoning']:.1f}/10\n"
        output += f"  Evidence Quality:    {score['evidence_quality']:.1f}/10\n"
        output += f"  Technical Accuracy:  {score['technical_accuracy']:.1f}/10\n"
        output += f"  Relevance:           {score['relevance']:.1f}/10\n"
        output += f"  TOTAL SCORE:         {score['total_score']:.1f}/40\n"
        output += f"\n  Feedback: {score['feedback']}\n"
        output += "\n" + "-"*60 + "\n\n"
    
    return output
