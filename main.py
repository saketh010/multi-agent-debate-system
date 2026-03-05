"""
Multi-Agent Debate System - Main Entry Point

CLI interface for running multi-agent debates using LangGraph, AWS Bedrock, and Tavily.
"""

import os
import sys
from datetime import datetime
from typing import Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for better CLI experience: pip install rich")

from dotenv import load_dotenv

from graph.debate_graph import run_debate
from agents.moderator_agent import get_debate_summary
from agents.scoring_agent import format_scores
from agents.judge_agent import format_final_decision

# Load environment variables
load_dotenv()

# Initialize Rich console if available
console = Console() if RICH_AVAILABLE else None


def print_header(text: str):
    """Print a formatted header."""
    if RICH_AVAILABLE:
        console.print(Panel(f"[bold cyan]{text}[/bold cyan]", expand=False))
    else:
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}\n")


def print_section(title: str, content: str):
    """Print a formatted section."""
    if RICH_AVAILABLE:
        console.print(f"\n[bold yellow]{title}[/bold yellow]")
        console.print(content)
    else:
        print(f"\n{title}")
        print("-" * len(title))
        print(content)


def print_argument(agent_name: str, argument: dict):
    """Print a formatted argument."""
    if RICH_AVAILABLE:
        table = Table(title=f"{agent_name.upper()} - Round {argument['round_number']}")
        table.add_column("Field", style="cyan")
        table.add_column("Content", style="white")
        
        table.add_row("Argument", argument['argument'][:500] + "..." if len(argument['argument']) > 500 else argument['argument'])
        table.add_row("Evidence", "\n".join(argument['evidence'][:2]))
        table.add_row("Sources", "\n".join(argument['sources'][:2]))
        
        console.print(table)
    else:
        print(f"\n{agent_name.upper()} - Round {argument['round_number']}")
        print("-" * 60)
        print(f"Argument: {argument['argument'][:500]}..." if len(argument['argument']) > 500 else f"Argument: {argument['argument']}")
        print(f"\nEvidence:")
        for ev in argument['evidence'][:2]:
            print(f"  - {ev}")
        print(f"\nSources:")
        for src in argument['sources'][:2]:
            print(f"  - {src}")
        print("-" * 60)


def print_cross_examination(exam: dict):
    """Print a formatted cross-examination."""
    if RICH_AVAILABLE:
        console.print(f"\n[bold red]{exam['examiner'].upper()}[/bold red] examining [bold green]{exam['target'].upper()}[/bold green]:")
        console.print(exam['critique'][:400] + "..." if len(exam['critique']) > 400 else exam['critique'])
    else:
        print(f"\n{exam['examiner'].upper()} examining {exam['target'].upper()}:")
        print(exam['critique'][:400] + "..." if len(exam['critique']) > 400 else exam['critique'])
        print("-" * 60)


def check_aws_credentials() -> bool:
    """Check if AWS credentials are available."""
    # Check for direct credentials
    if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
        return True
    
    # Check for AWS session credentials (set by okta-aws-cli)
    if os.getenv("AWS_SESSION_TOKEN"):
        return True
    
    # Check for AWS profile
    if os.getenv("AWS_PROFILE"):
        return True
    
    return False


def display_startup_info():
    """Display startup information and configuration."""
    print_header("Multi-Agent Debate System")
    
    if RICH_AVAILABLE:
        console.print("[green]✓[/green] Rich formatting enabled")
    else:
        print("✓ Basic formatting mode")
    
    # Check AWS configuration
    if check_aws_credentials():
        if RICH_AVAILABLE:
            console.print("[green]✓[/green] AWS credentials detected")
        else:
            print("✓ AWS credentials detected")
        
        # Show which credential method is being used
        if os.getenv("AWS_SESSION_TOKEN"):
            if RICH_AVAILABLE:
                console.print("  [dim]Using AWS session credentials (Okta-based)[/dim]")
            else:
                print("  Using AWS session credentials (Okta-based)")
        elif os.getenv("AWS_PROFILE"):
            if RICH_AVAILABLE:
                console.print(f"  [dim]Using AWS profile: {os.getenv('AWS_PROFILE')}[/dim]")
            else:
                print(f"  Using AWS profile: {os.getenv('AWS_PROFILE')}")
    else:
        if RICH_AVAILABLE:
            console.print("[yellow]![/yellow] No AWS credentials found")
            console.print("  [dim]If using Okta: Run 'okta-aws-cli -p sandbox' first[/dim]")
        else:
            print("! No AWS credentials found")
            print("  If using Okta: Run 'okta-aws-cli -p sandbox' first")
    
    # Check Tavily API key
    if os.getenv("TAVILY_API_KEY"):
        if RICH_AVAILABLE:
            console.print("[green]✓[/green] Tavily API key configured")
        else:
            print("✓ Tavily API key configured")
    else:
        if RICH_AVAILABLE:
            console.print("[yellow]![/yellow] No Tavily API key found (will use mock data)")
        else:
            print("! No Tavily API key found (will use mock data)")
    
    print("")


def get_topic_from_user() -> Optional[str]:
    """Get debate topic from user input."""
    if RICH_AVAILABLE:
        console.print("\n[bold]Enter a debate topic[/bold] (or press Ctrl+C to exit):")
        console.print("[dim]Example: Should startups adopt microservices architecture?[/dim]")
    else:
        print("\nEnter a debate topic (or press Ctrl+C to exit):")
        print("Example: Should startups adopt microservices architecture?")
    
    try:
        topic = input("\n> ").strip()
        if not topic:
            print("Error: Topic cannot be empty")
            return None
        return topic
    except KeyboardInterrupt:
        print("\n\nExiting...")
        return None
    except EOFError:
        return None


def run_interactive_debate():
    """Run an interactive debate session."""
    display_startup_info()
    
    # Get topic from user
    topic = get_topic_from_user()
    if not topic:
        return
    
    # Ask for number of rounds
    try:
        if RICH_AVAILABLE:
            console.print("\n[bold]Number of debate rounds[/bold] [dim](default: 2)[/dim]:")
        else:
            print("\nNumber of debate rounds (default: 2):")
        
        rounds_input = input("> ").strip()
        max_rounds = int(rounds_input) if rounds_input else 2
        max_rounds = max(1, min(max_rounds, 5))  # Limit to 1-5 rounds
    except (ValueError, KeyboardInterrupt, EOFError):
        max_rounds = 2
    
    print_header(f"Starting Debate: {max_rounds} Rounds")
    
    if RICH_AVAILABLE:
        console.print(f"[bold cyan]Topic:[/bold cyan] {topic}")
        console.print(f"[bold cyan]Rounds:[/bold cyan] {max_rounds}")
        console.print("\n[yellow]Running debate workflow...[/yellow]\n")
    else:
        print(f"Topic: {topic}")
        print(f"Rounds: {max_rounds}")
        print("\nRunning debate workflow...\n")
    
    try:
        # Run the debate
        final_state = run_debate(topic, max_rounds)
        
        # Display results
        display_debate_results(final_state)
        
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"\n[bold red]Error during debate:[/bold red] {str(e)}")
        else:
            print(f"\nError during debate: {str(e)}")
        
        import traceback
        if RICH_AVAILABLE:
            console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        else:
            print(f"\n{traceback.format_exc()}")


def display_debate_results(state: dict):
    """Display the complete debate results."""
    print_header("DEBATE RESULTS")
    
    # Display arguments
    print_section("📝 ARGUMENTS", "")
    arguments = state.get("arguments", [])
    for arg in arguments:
        print_argument(arg["agent_name"], arg)
    
    # Display cross-examinations
    if state.get("cross_examinations"):
        print_section("🔍 CROSS-EXAMINATIONS", "")
        for exam in state["cross_examinations"]:
            print_cross_examination(exam)
    
    # Display scores
    if state.get("scores"):
        print_section("📊 SCORES", "")
        scores_text = format_scores(state["scores"])
        print(scores_text)
    
    # Display final decision
    if state.get("final_decision"):
        print_section("⚖️ FINAL VERDICT", "")
        decision_text = format_final_decision(state["final_decision"])
        print(decision_text)
    
    # Save results to file
    save_results(state)


def save_results(state: dict):
    """Save debate results to a file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"debate_result_{timestamp}.txt"
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"DEBATE RESULTS\n")
            f.write(f"{'='*60}\n\n")
            f.write(f"Topic: {state.get('topic', 'Unknown')}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Rounds: {state.get('max_rounds', 2)}\n\n")
            
            # Arguments
            f.write(f"\n{'='*60}\nARGUMENTS\n{'='*60}\n")
            for arg in state.get("arguments", []):
                f.write(f"\n{arg['agent_name'].upper()} - Round {arg['round_number']}\n")
                f.write(f"{'-'*60}\n")
                f.write(f"Argument: {arg['argument']}\n\n")
                f.write(f"Evidence:\n")
                for ev in arg['evidence']:
                    f.write(f"  - {ev}\n")
                f.write(f"\nSources:\n")
                for src in arg['sources']:
                    f.write(f"  - {src}\n")
                f.write(f"\n")
            
            # Cross-examinations
            if state.get("cross_examinations"):
                f.write(f"\n{'='*60}\nCROSS-EXAMINATIONS\n{'='*60}\n")
                for exam in state["cross_examinations"]:
                    f.write(f"\n{exam['examiner'].upper()} examining {exam['target'].upper()}:\n")
                    f.write(f"{exam['critique']}\n\n")
            
            # Scores
            if state.get("scores"):
                f.write(format_scores(state["scores"]))
            
            # Final decision
            if state.get("final_decision"):
                f.write(format_final_decision(state["final_decision"]))
        
        if RICH_AVAILABLE:
            console.print(f"\n[green]✓[/green] Results saved to: [bold]{filename}[/bold]")
        else:
            print(f"\n✓ Results saved to: {filename}")
    
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"\n[yellow]![/yellow] Could not save results: {str(e)}")
        else:
            print(f"\n! Could not save results: {str(e)}")


def main():
    """Main entry point."""
    try:
        run_interactive_debate()
    except KeyboardInterrupt:
        print("\n\nDebate interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
