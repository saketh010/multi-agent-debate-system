"""
Streamlit Web Interface for Multi-Agent Debate System

A beautiful web UI for running and visualizing AI debates in real-time.
"""

import streamlit as st
import os
from datetime import datetime
from typing import Dict, Any, Optional
import time
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from graph.debate_graph import create_debate_graph, run_debate_with_hitl
from state.debate_state import create_initial_state, HumanIntervention
from agents.scoring_agent import format_scores
from agents.judge_agent import format_final_decision
from utils.image_ingestion import upload_and_process_images

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
    s3_bucket = (
        os.getenv("S3_IMAGE_BUCKET_NAME")
        or os.getenv("S3_BUCKET_NAME")
        or os.getenv("AWS_S3_BUCKET")
        or ""
    )
    
    return {
        "aws": aws_configured,
        "tavily": tavily_configured,
        "model_id": model_id,
        "region": region,
        "s3_bucket": s3_bucket,
    }


def validate_aws_session(region: str) -> tuple[bool, str]:
    """Validate active AWS session/token by calling STS."""
    try:
        session = boto3.Session()
        sts = session.client("sts", region_name=region)
        sts.get_caller_identity()
        return True, "AWS session is valid"
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in {"ExpiredToken", "ExpiredTokenException", "RequestExpired"}:
            return False, "AWS session token expired"
        return False, f"AWS validation failed: {code or str(e)}"
    except Exception as e:
        return False, f"AWS validation failed: {str(e)}"


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
        if creds["s3_bucket"]:
            st.caption(f"S3 Bucket: {creds['s3_bucket']}")
        else:
            st.caption("S3 Bucket: not configured")
        
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
    <div style="padding: 1rem; border-left: 3px solid #FF5722; background-color: #1E1E1E; border-radius: 5px; margin: 0.5rem 0; border: 1px solid #333;">
        <strong style="color: #FF7043;">🔍 {exam['examiner'].upper()}</strong> examining 
        <strong style="color: #81C784;">{exam['target'].upper()}</strong>
        <p style="margin-top: 0.5rem; color: #E0E0E0;">{exam['critique'][:500]}{'...' if len(exam['critique']) > 500 else ''}</p>
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


def display_human_interventions(interventions: list):
    """Display human interventions and agent responses."""
    if not interventions:
        return
    
    st.markdown("## 👤 Human Interventions")
    
    for intervention in interventions:
        with st.container():
            st.markdown(f"""
            <div style="padding: 1rem; border-left: 3px solid #4A90E2; background-color: #1E1E1E; border-radius: 5px; margin: 0.5rem 0; border: 1px solid #333;">
                <strong style="color: #4A90E2;">👤 Human Feedback to {intervention['agent_name'].upper()}</strong> (Round {intervention['round_number']})
                <p style="margin-top: 0.5rem; color: #E0E0E0;">{intervention['human_feedback']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if intervention.get('agent_response'):
                decision_color = "#81C784" if intervention.get('agent_agrees') else "#FF7043"
                decision_text = "AGREES" if intervention.get('agent_agrees') else "DISAGREES"
                
                st.markdown(f"""
                <div style="padding: 1rem; border-left: 3px solid {decision_color}; background-color: #1E1E1E; border-radius: 5px; margin: 0.5rem 0 1rem 2rem; border: 1px solid #333;">
                    <strong style="color: {decision_color};">🤖 Agent {decision_text}</strong>
                    <p style="margin-top: 0.5rem; color: #E0E0E0;">{intervention['agent_response']}</p>
                    {f'<p style="margin-top: 0.5rem; color: #BBBBBB;"><strong>Revised Argument:</strong><br>{intervention["agent_revised_argument"]}</p>' if intervention.get('agent_revised_argument') else ''}
                </div>
                """, unsafe_allow_html=True)


def run_debate_with_progress(
    topic: str,
    max_rounds: int,
    enable_hitl: bool = False,
    image_context: str = "",
    image_s3_uris: Optional[list] = None,
):
    """Run debate with live progress updates and optional HITL."""
    
    # Initialize session state for HITL persistence across reruns
    if enable_hitl:
        if 'debate_graph' not in st.session_state:
            st.session_state.debate_graph = None
        if 'debate_config' not in st.session_state:
            st.session_state.debate_config = None
        if 'debate_started' not in st.session_state:
            st.session_state.debate_started = False
    
    # Create or retrieve graph and config
    if not enable_hitl or not st.session_state.debate_started:
        initial_state = create_initial_state(
            topic,
            max_rounds,
            image_context=image_context,
            image_s3_uris=image_s3_uris or [],
        )
        graph = create_debate_graph(enable_hitl=enable_hitl)
        config = {"configurable": {"thread_id": f"debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"}}
        stream_input = initial_state
        
        if enable_hitl:
            st.session_state.debate_graph = graph
            st.session_state.debate_config = config
            st.session_state.debate_started = True
    else:
        # Resuming from interrupt - graph.stream(None) continues from checkpoint
        graph = st.session_state.debate_graph
        config = st.session_state.debate_config
        stream_input = None
    
    # Create display containers
    progress_container = st.container()
    arguments_container = st.container()
    feedback_container = st.container()
    cross_exam_container = st.container()
    scores_container = st.container()
    verdict_container = st.container()
    interventions_container = st.container()
    
    # Progress tracking
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
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
        # Stream the graph - runs until interrupt (HITL) or completion
        for state_update in graph.stream(stream_input, config):
            if not isinstance(state_update, dict) or not state_update:
                continue

            node_name = list(state_update.keys())[0]
            state_data = state_update[node_name]

            # LangGraph can emit tuple payloads depending on stream mode/runtime metadata.
            # Normalize to a dict so progress calculations are safe.
            if isinstance(state_data, tuple):
                state_data = state_data[0] if state_data and isinstance(state_data[0], dict) else {}
            elif not isinstance(state_data, dict):
                state_data = {}
            
            # Update progress based on node
            phase_map = {
                "moderator": 0,
                "evidence_retrieval": 1,
                "architect": 2 if state_data.get("round", 0) <= 1 else 3,
                "performance": 2 if state_data.get("round", 0) <= 1 else 3,
                "security": 2 if state_data.get("round", 0) <= 1 else 3,
                "cross_examination": 4,
                "scoring": 5,
                "judge": 6
            }
            current_phase = phase_map.get(node_name, current_phase)
            
            with progress_container:
                progress = (current_phase + 1) / total_phases
                progress_bar.progress(progress)
                status_text.text(f"🔄 {phases[current_phase]}...")
            
            time.sleep(0.05)
        
        # Stream ended - either interrupted (HITL) or completed
        # Get the FULL accumulated state from the checkpoint
        graph_state = graph.get_state(config)
        full_state = graph_state.values
        pending_next = graph_state.next  # Non-empty if interrupted
        
        # Display all accumulated arguments
        if full_state.get("arguments"):
            with arguments_container:
                st.markdown("## 💬 Arguments")
                for arg in full_state["arguments"]:
                    display_argument(arg["agent_name"], arg, arg["round_number"])
        
        # Display cross-examinations
        if full_state.get("cross_examinations"):
            with cross_exam_container:
                st.markdown("## 🔍 Cross-Examinations")
                for exam in full_state["cross_examinations"]:
                    display_cross_examination(exam)
        
        # Display scores
        if full_state.get("scores"):
            with scores_container:
                display_scores(full_state["scores"])
        
        # Display final decision
        if full_state.get("final_decision"):
            with verdict_container:
                display_final_decision(full_state["final_decision"])
        
        # Display past interventions
        if full_state.get("human_interventions"):
            with interventions_container:
                display_human_interventions(full_state["human_interventions"])
        
        # Check if graph is paused at an interrupt (HITL waiting for feedback)
        if enable_hitl and pending_next:
            agent_name = full_state.get("pending_feedback_agent")
            round_num = full_state.get("round", 1)
            
            with progress_container:
                status_text.text(f"⏸️ Debate paused — waiting for your feedback on {agent_name.upper()}")
            
            with feedback_container:
                st.markdown("---")
                st.markdown(f"### 💬 Provide Feedback to **{agent_name.upper()}** (Round {round_num})")
                st.warning(f"⏸️ The debate is paused. Review **{agent_name.upper()}**'s argument above, then submit your feedback or skip to continue.")
                
                feedback_text = st.text_area(
                    f"Your feedback for {agent_name.upper()}:",
                    key=f"feedback_input_{agent_name}_{round_num}_{id(config)}",
                    placeholder="Share your thoughts, concerns, or alternative perspectives...",
                    height=150
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📝 Submit Feedback", key=f"submit_{agent_name}_{round_num}", type="primary", use_container_width=True):
                        if feedback_text.strip():
                            intervention = HumanIntervention(
                                agent_name=agent_name,
                                round_number=round_num,
                                human_feedback=feedback_text.strip(),
                                agent_response=None,
                                agent_revised_argument=None,
                                agent_agrees=None
                            )
                            # Use update_state with the await node so the add reducer appends
                            graph.update_state(
                                config,
                                {"human_interventions": [intervention]},
                                as_node=f"await_feedback_{agent_name}"
                            )
                            st.rerun()
                        else:
                            st.warning("Please enter feedback before submitting.")
                
                with col2:
                    if st.button("➡️ Continue Without Feedback", key=f"skip_{agent_name}_{round_num}", use_container_width=True):
                        # No state update needed - route_after_feedback will return "continue"
                        # Just resume the graph by re-running the script
                        st.rerun()
            
            # Stop script here until user interacts
            st.stop()
        
        # Debate completed normally
        with progress_container:
            progress_bar.progress(1.0)
            status_text.text("✅ Debate Complete!")
        
        # Clean up HITL session state
        if enable_hitl:
            for key in [
                'debate_graph',
                'debate_config',
                'debate_started',
                'debate_topic',
                'debate_max_rounds',
                'debate_image_context',
                'debate_image_s3_uris',
            ]:
                if key in st.session_state:
                    del st.session_state[key]
        
        return full_state
    
    except Exception as e:
        error_text = str(e)
        if "ExpiredToken" in error_text or "expired" in error_text.lower():
            st.error("❌ AWS session token expired while calling Bedrock.")
            st.info("Refresh credentials and retry. Example: `okta-aws-cli -p sandbox`")
        else:
            st.error(f"❌ Error during debate: {error_text}")
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

    aws_session_ok, aws_session_msg = validate_aws_session(creds["region"])
    if not aws_session_ok:
        st.error(f"❌ {aws_session_msg}")
        st.info("Refresh your AWS credentials and rerun the app. Example: `okta-aws-cli -p sandbox`")
        st.stop()
    
    # Main interface
    st.markdown("---")
    
    # Input section
    col1, col2, col3 = st.columns([4, 1, 1])
    
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
    
    with col3:
        enable_hitl = st.checkbox(
            "👤 HITL",
            value=False,
            help="Enable Human-in-the-Loop: Provide feedback on arguments"
        )

    uploaded_images = st.file_uploader(
        "🖼️ Upload Reference Images (optional)",
        type=["png", "jpg", "jpeg", "webp", "gif"],
        accept_multiple_files=True,
        help="Images are uploaded to S3, analyzed, and used as context for the debate."
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
    
    # Start debate button OR resume HITL debate in progress
    hitl_in_progress = st.session_state.get('debate_started', False)
    if hitl_in_progress:
        enable_hitl = True
    start_clicked = st.button("🚀 Start Debate", type="primary", use_container_width=True, disabled=hitl_in_progress)
    
    if start_clicked or hitl_in_progress:
        if not hitl_in_progress and not topic:
            st.error("Please enter a debate topic!")
            st.stop()

        image_context = ""
        image_s3_uris = []
        
        # Use stored topic for HITL reruns
        if hitl_in_progress:
            topic = st.session_state.get('debate_topic', topic)
            max_rounds = st.session_state.get('debate_max_rounds', max_rounds)
            image_context = st.session_state.get('debate_image_context', "")
            image_s3_uris = st.session_state.get('debate_image_s3_uris', [])
        elif enable_hitl:
            st.session_state.debate_topic = topic
            st.session_state.debate_max_rounds = max_rounds

        if not hitl_in_progress and uploaded_images:
            bucket_name = creds.get("s3_bucket", "")
            if not bucket_name:
                st.error("S3 image bucket is not configured. Set S3_IMAGE_BUCKET_NAME in your environment.")
                st.stop()

            with st.spinner("Uploading images to S3 and extracting technical context..."):
                try:
                    image_context, image_s3_uris = upload_and_process_images(
                        uploaded_files=uploaded_images,
                        topic=topic,
                        bucket_name=bucket_name,
                    )
                except Exception as e:
                    st.error(f"❌ Image processing failed: {str(e)}")
                    st.stop()

            if enable_hitl:
                st.session_state.debate_image_context = image_context
                st.session_state.debate_image_s3_uris = image_s3_uris
        
        st.markdown("---")
        
        # Show debate info
        st.markdown(f"### 📋 Debate Configuration")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Topic", topic[:30] + "..." if len(topic) > 30 else topic)
        with col2:
            st.metric("Rounds", max_rounds)
        with col3:
            st.metric("Agents", 3)
        with col4:
            st.metric("HITL", "✅ Enabled" if enable_hitl else "❌ Disabled")

        if image_s3_uris:
            st.markdown("**Image Sources (S3):**")
            for uri in image_s3_uris:
                st.write(f"- {uri}")

        if image_context:
            with st.expander("🧠 Extracted Image Context", expanded=False):
                st.write(image_context)
        
        st.markdown("---")
        
        # Run debate
        with st.spinner("Initializing debate system..."):
            final_state = run_debate_with_progress(
                topic,
                max_rounds,
                enable_hitl,
                image_context=image_context,
                image_s3_uris=image_s3_uris,
            )
        
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

            if image_s3_uris:
                results_text += "\nIMAGE SOURCES (S3)\n"
                results_text += f"{'-'*60}\n"
                for uri in image_s3_uris:
                    results_text += f"- {uri}\n"
                results_text += "\n"

            if image_context:
                results_text += "\nIMAGE-DERIVED CONTEXT\n"
                results_text += f"{'-'*60}\n"
                results_text += f"{image_context}\n\n"
            
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
            
            if final_state.get("human_interventions"):
                results_text += f"\n{'='*60}\nHUMAN INTERVENTIONS\n{'='*60}\n\n"
                for intervention in final_state["human_interventions"]:
                    results_text += f"Human Feedback to {intervention['agent_name'].upper()} (Round {intervention['round_number']}):\n"
                    results_text += f"{intervention['human_feedback']}\n\n"
                    if intervention.get('agent_response'):
                        response_type = "AGREES" if intervention.get('agent_agrees') else "DISAGREES"
                        results_text += f"Agent {response_type}:\n"
                        results_text += f"{intervention['agent_response']}\n\n"
                        if intervention.get('agent_revised_argument'):
                            results_text += f"Revised Argument:\n{intervention['agent_revised_argument']}\n\n"
            
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
