"""
Streamlit Web Interface for Multi-Agent Debate System

A beautiful web UI for running and visualizing AI debates in real-time.
"""

import streamlit as st
import os
from datetime import datetime
from typing import Dict, Any, Optional
import time
from dotenv import load_dotenv

from graph.debate_graph import create_debate_graph
from state.debate_state import create_initial_state
from agents.scoring_agent import format_scores
from agents.judge_agent import format_final_decision

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Multi-Agent Debate System",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #AAAAAA;
        margin-bottom: 2rem;
    }
    .agent-card {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        background-color: #1E1E1E;
        border: 1px solid #333;
    }
    .architect {
        border-left: 4px solid #2196F3;
    }
    .performance {
        border-left: 4px solid #4CAF50;
    }
    .security {
        border-left: 4px solid #FF9800;
    }
    .score-card {
        padding: 1rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin: 0.5rem 0;
    }
    .winner-card {
        padding: 2rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        text-align: center;
        font-size: 1.5rem;
        margin: 1rem 0;
    }
    .stProgress > div > div > div > div {
        background-color: #1E88E5;
    }
    /* Remove sidebar scrollbar and compact layout */
    section[data-testid="stSidebar"] {
        overflow-y: hidden !important;
    }
    section[data-testid="stSidebar"] > div {
        overflow-y: hidden !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    /* Reduce spacing between elements in sidebar */
    section[data-testid="stSidebar"] .element-container {
        margin-bottom: 0.3rem !important;
    }
    section[data-testid="stSidebar"] h3 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.3rem !important;
        font-size: 1.1rem !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 0.2rem !important;
    }
    section[data-testid="stSidebar"] hr {
        margin: 0.5rem 0 !important;
    }
    </style>
""", unsafe_allow_html=True)


def check_credentials():
    """Check if AWS credentials and API keys are configured."""
    aws_configured = bool(
        os.getenv("AWS_ACCESS_KEY_ID") or 
        os.getenv("AWS_SESSION_TOKEN") or 
        os.getenv("AWS_PROFILE")
    )
    
    tavily_configured = bool(os.getenv("TAVILY_API_KEY"))
    model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
    region = os.getenv("AWS_REGION", "us-east-1")
    
    return {
        "aws": aws_configured,
        "tavily": tavily_configured,
        "model_id": model_id,
        "region": region
    }


def display_sidebar():
    """Display sidebar with configuration and status."""
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        creds = check_credentials()
        
        # AWS Status
        if creds["aws"]:
            st.success("✅ AWS Configured")
            if os.getenv("AWS_PROFILE"):
                st.caption(f"Profile: {os.getenv('AWS_PROFILE')}")
        else:
            st.error("❌ AWS Not Configured")
        
        # Tavily Status
        if creds["tavily"]:
            st.success("✅ Tavily API Configured")
        else:
            st.warning("⚠️ Tavily Not Configured")
        
        # Model Info
        st.info(f"**Model:** {creds['model_id'].split('.')[-1]}")
        st.caption(f"Region: {creds['region']}")
        
        st.markdown("---")
        
        # Agent Info
        st.markdown("### 🤖 Active Agents")
        st.markdown("🏗️ **Architect**")
        st.markdown("⚡ **Performance**")
        st.markdown("🔒 **Security**")
        
        st.markdown("---")
        
        # About and Documentation
        st.markdown("### ℹ️ About")
        st.link_button("📖 Documentation", "https://github.com/saketh010/multi-agent-debate-system/tree/main")


def display_argument(agent_name: str, argument: Dict[str, Any], round_num: int):
    """Display an agent's argument in a styled card."""
    
    agent_colors = {
        "architect": ("🏗️", "architect"),
        "performance": ("⚡", "performance"),
        "security": ("🔒", "security")
    }
    
    icon, css_class = agent_colors.get(agent_name, ("🤖", ""))
    
    with st.container():
        st.markdown(f'<div class="agent-card {css_class}">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([6, 1])
        with col1:
            st.markdown(f"### {icon} {agent_name.upper()} - Round {round_num}")
        with col2:
            st.markdown(f"**Round {round_num}**")
        
        # Argument
        st.markdown("**Argument:**")
        st.write(argument['argument'])
        
        # Evidence (collapsible)
        with st.expander("📚 Evidence & Sources"):
            st.markdown("**Evidence:**")
            for i, ev in enumerate(argument.get('evidence', [])[:3], 1):
                st.markdown(f"{i}. {ev}")
            
            st.markdown("**Sources:**")
            for i, src in enumerate(argument.get('sources', [])[:3], 1):
                st.markdown(f"{i}. {src}")
        
        st.markdown('</div>', unsafe_allow_html=True)


def display_cross_examination(exam: Dict[str, Any]):
    """Display cross-examination in a formatted way."""
    st.markdown(f"""
    <div style="padding: 1rem; border-left: 3px solid #FF5722; background-color: #fff3e0; border-radius: 5px; margin: 0.5rem 0;">
        <strong style="color: #E64A19;">🔍 {exam['examiner'].upper()}</strong> examining 
        <strong style="color: #558B2F;">{exam['target'].upper()}</strong>
        <p style="margin-top: 0.5rem;">{exam['critique'][:500]}{'...' if len(exam['critique']) > 500 else ''}</p>
    </div>
    """, unsafe_allow_html=True)


def display_scores(scores: list):
    """Display scoring results."""
    st.markdown("## 📊 Argument Scores")
    
    # Sort by total score
    sorted_scores = sorted(scores, key=lambda x: x['total_score'], reverse=True)
    
    for idx, score in enumerate(sorted_scores, 1):
        with st.container():
            st.markdown(f'<div class="score-card">', unsafe_allow_html=True)
            
            st.markdown(f"### #{idx} {score['agent_name'].upper()}")
            
            # Display each criterion with score on the right
            criteria = [
                ("Logical Reasoning:", score['logical_reasoning']),
                ("Evidence Quality:", score['evidence_quality']),
                ("Technical Accuracy:", score['technical_accuracy']),
                ("Relevance:", score['relevance'])
            ]
            
            for criterion_name, criterion_score in criteria:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"**{criterion_name}**")
                with col2:
                    st.progress(criterion_score / 10)
                with col3:
                    st.markdown(f"**{criterion_score:.1f}/10**")
            
            # Total score at the bottom
            st.markdown("---")
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown("### **Total Score**")
            with col2:
                st.markdown(f"### **{score['total_score']:.1f}/40**")
            
            st.markdown(f"**Feedback:** {score['feedback']}")
            st.markdown('</div>', unsafe_allow_html=True)


def display_final_decision(decision: Dict[str, Any]):
    """Display the final judge decision."""
    st.markdown("## ⚖️ Final Verdict")
    
    st.markdown(f"""
    <div class="winner-card">
        <h1>🏆 WINNER: {decision['winner'].upper()}</h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📝 Summary")
    st.info(decision['summary'])
    
    st.markdown("### 🔑 Key Points")
    for point in decision['key_points']:
        st.markdown(f"- {point}")
    
    st.markdown("### 💭 Reasoning")
    st.write(decision['reasoning'])


def run_debate_with_progress(topic: str, max_rounds: int):
    """Run debate with live progress updates."""
    
    # Initialize state
    initial_state = create_initial_state(topic, max_rounds)
    
    # Create graph
    graph = create_debate_graph()
    
    # Create containers for different sections
    status_container = st.container()
    progress_container = st.container()
    arguments_container = st.container()
    cross_exam_container = st.container()
    scores_container = st.container()
    verdict_container = st.container()
    
    # Progress tracking
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    # Track phase
    phases = [
        "Initializing debate",
        "Gathering evidence",
        "Round 1 arguments",
        "Round 2 arguments",
        "Cross-examination",
        "Scoring arguments",
        "Final judgment"
    ]
    
    current_phase = 0
    total_phases = len(phases)
    
    try:
        # Run the graph
        config = {"configurable": {"thread_id": f"debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"}}
        
        final_state = None
        
        for state_update in graph.stream(initial_state, config):
            # Get the latest state
            node_name = list(state_update.keys())[0]
            state_data = state_update[node_name]
            
            # Update progress based on phase
            if node_name == "moderator":
                current_phase = 0
            elif node_name == "evidence_retrieval":
                current_phase = 1
            elif node_name in ["architect", "performance", "security"]:
                if state_data.get("round", 1) == 1:
                    current_phase = 2
                else:
                    current_phase = 3
            elif node_name == "cross_examination":
                current_phase = 4
            elif node_name == "scoring":
                current_phase = 5
            elif node_name == "judge":
                current_phase = 6
            
            # Update progress bar
            progress = (current_phase + 1) / total_phases
            progress_bar.progress(progress)
            status_text.text(f"🔄 {phases[current_phase]}...")
            
            # Display arguments as they come
            if "arguments" in state_data and state_data["arguments"]:
                with arguments_container:
                    st.markdown("## 💬 Arguments")
                    for arg in state_data["arguments"]:
                        display_argument(
                            arg["agent_name"],
                            arg,
                            arg["round_number"]
                        )
            
            # Display cross-examinations
            if "cross_examinations" in state_data and state_data["cross_examinations"]:
                with cross_exam_container:
                    st.markdown("## 🔍 Cross-Examinations")
                    for exam in state_data["cross_examinations"]:
                        display_cross_examination(exam)
            
            # Display scores
            if "scores" in state_data and state_data["scores"]:
                with scores_container:
                    display_scores(state_data["scores"])
            
            # Display final decision
            if "final_decision" in state_data and state_data["final_decision"]:
                with verdict_container:
                    display_final_decision(state_data["final_decision"])
            
            final_state = state_data
            time.sleep(0.1)  # Small delay for visual effect
        
        # Complete
        progress_bar.progress(1.0)
        status_text.text("✅ Debate Complete!")
        
        return final_state
    
    except Exception as e:
        st.error(f"❌ Error during debate: {str(e)}")
        st.exception(e)
        return None


def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<div class="main-header">⚖️ Multi-Agent Debate System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Technical Debates with Live Analysis</div>', unsafe_allow_html=True)
    
    # Display sidebar
    display_sidebar()
    
    # Check credentials
    creds = check_credentials()
    if not creds["aws"]:
        st.warning("⚠️ AWS credentials not configured. Please set up your credentials in `.env` file or run `okta-aws-cli -p sandbox`")
        st.info("See QUICKSTART.md for setup instructions.")
        st.stop()
    
    # Main interface
    st.markdown("---")
    
    # Input section
    col1, col2 = st.columns([4, 1])
    
    with col1:
        topic = st.text_input(
            "🎯 Enter Debate Topic",
            placeholder="e.g., Should startups adopt microservices architecture?",
            help="Enter a technical question or topic for the AI agents to debate"
        )
    
    with col2:
        max_rounds = st.selectbox(
            "🔄 Rounds",
            options=[1, 2, 3, 4, 5],
            index=1,
            help="Number of debate rounds (more rounds = deeper analysis)"
        )
    
    # Example topics
    with st.expander("💡 Example Topics"):
        st.markdown("""
        - Should startups adopt microservices architecture?
        - Is NoSQL better than SQL for social media platforms?
        - Should we use Kubernetes or serverless for production?
        - Is Test-Driven Development worth the overhead?
        - Should companies use AI code generation tools in production?
        - Is zero-trust architecture necessary for all organizations?
        """)
    
    # Start debate button
    if st.button("🚀 Start Debate", type="primary", use_container_width=True):
        if not topic:
            st.error("Please enter a debate topic!")
            st.stop()
        
        st.markdown("---")
        
        # Show debate info
        st.markdown(f"### 📋 Debate Configuration")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Topic", topic[:30] + "..." if len(topic) > 30 else topic)
        with col2:
            st.metric("Rounds", max_rounds)
        with col3:
            st.metric("Agents", 3)
        
        st.markdown("---")
        
        # Run debate
        with st.spinner("Initializing debate system..."):
            final_state = run_debate_with_progress(topic, max_rounds)
        
        if final_state:
            # Download results button
            st.markdown("---")
            
            # Create results text
            results_text = f"""MULTI-AGENT DEBATE RESULTS
{'='*60}

Topic: {topic}
Rounds: {max_rounds}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*60}
ARGUMENTS
{'='*60}

"""
            
            for arg in final_state.get("arguments", []):
                results_text += f"\n{arg['agent_name'].upper()} - Round {arg['round_number']}\n"
                results_text += f"{'-'*60}\n"
                results_text += f"Argument: {arg['argument']}\n\n"
                results_text += f"Evidence:\n"
                for ev in arg.get('evidence', []):
                    results_text += f"  - {ev}\n"
                results_text += f"\nSources:\n"
                for src in arg.get('sources', []):
                    results_text += f"  - {src}\n"
                results_text += "\n"
            
            if final_state.get("cross_examinations"):
                results_text += f"\n{'='*60}\nCROSS-EXAMINATIONS\n{'='*60}\n\n"
                for exam in final_state["cross_examinations"]:
                    results_text += f"{exam['examiner'].upper()} examining {exam['target'].upper()}:\n"
                    results_text += f"{exam['critique']}\n\n"
            
            if final_state.get("scores"):
                results_text += format_scores(final_state["scores"])
            
            if final_state.get("final_decision"):
                results_text += format_final_decision(final_state["final_decision"])
            
            st.download_button(
                label="📥 Download Results",
                data=results_text,
                file_name=f"debate_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
            
            st.success("🎉 Debate completed successfully!")


if __name__ == "__main__":
    main()
