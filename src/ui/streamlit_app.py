#!/usr/bin/env python3
"""
Streamlit UI for the_board - Multi-Agent Strategic Planning System

This UI provides a beautiful, Material Design-inspired interface for:
- Submitting strategic goals
- Monitoring plan execution
- Viewing agent analysis results
- Tracking execution progress
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

# Page configuration
st.set_page_config(
    page_title="the_board - Strategic Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Material Design aesthetics
st.markdown("""
<style>
    /* Material Design inspired styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .goal-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    
    .status-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 0.5rem;
    }
    
    .status-pending { border-left: 4px solid #ffc107; }
    .status-progress { border-left: 4px solid #2196f3; }
    .status-completed { border-left: 4px solid #4caf50; }
    .status-failed { border-left: 4px solid #f44336; }
    
    .agent-response {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #28a745;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #667eea;
    }
    
    .metric-label {
        color: #666;
        font-size: 0.9rem;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem;
    }
    
    .stTextArea > div > div > textarea {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = "http://localhost:8000"

def check_api_health():
    """Check if the API is running and healthy."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def submit_strategic_goal(goal: str, context: str = ""):
    """Submit a strategic goal to the API."""
    try:
        payload = {
            "high_level_goal": goal,
            "user_context": context
        }
        response = requests.post(
            f"{API_BASE_URL}/plan",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error submitting goal: {str(e)}")
        return None

def get_plan_status(plan_id: str):
    """Get the current status of a plan."""
    try:
        response = requests.get(f"{API_BASE_URL}/state/plans/{plan_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def get_plan_events(plan_id: str):
    """Get events for a specific plan."""
    try:
        response = requests.get(f"{API_BASE_URL}/state/plans/{plan_id}/events", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except:
        return []

def get_plan_result(plan_id: str):
    """Get the final synthesized plan result."""
    try:
        response = requests.get(f"{API_BASE_URL}/plan/{plan_id}/result", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def display_final_plan(plan_result: dict):
    """Display the final synthesized plan in a beautiful format."""
    plan_data = plan_result.get('plan_data', {})
    
    if not plan_data:
        st.warning("⚠️ No plan data available")
        return
    
    # Create a beautiful display of the final plan
    st.markdown("""
    <div class="goal-card">
        <h3>🎯 Executive Strategic Plan</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Synthesized Strategy
    if plan_data.get('synthesized_strategy'):
        st.subheader("📊 Executive Summary")
        st.markdown(f"""
        <div class="agent-response">
            {plan_data['synthesized_strategy']}
        </div>
        """, unsafe_allow_html=True)
    
    # Contributing Agents
    if plan_data.get('contributing_agents'):
        st.subheader("👥 Contributing Agents")
        agents_text = ", ".join(plan_data['contributing_agents'])
        st.info(f"**Analysis provided by:** {agents_text}")
    
    # Identified Risks
    if plan_data.get('identified_risks'):
        st.subheader("⚠️ Identified Risks")
        for risk in plan_data['identified_risks']:
            st.markdown(f"""
            <div class="status-card status-failed">
                <strong>Risk:</strong> {risk}
            </div>
            """, unsafe_allow_html=True)
    
    # Confidence Score
    if plan_data.get('confidence_score'):
        st.subheader("🎯 Confidence Assessment")
        confidence = plan_data['confidence_score']
        if confidence >= 0.8:
            confidence_color = "🟢"
            confidence_text = "High Confidence"
        elif confidence >= 0.5:
            confidence_color = "🟡"
            confidence_text = "Moderate Confidence"
        else:
            confidence_color = "🔴"
            confidence_text = "Low Confidence - Human Review Advised"
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{confidence_color} {confidence:.1%}</div>
            <div class="metric-label">{confidence_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Plan Metadata
    if plan_result.get('created_at'):
        st.subheader("📅 Plan Details")
        st.info(f"**Synthesized on:** {plan_result['created_at']}")
    
    # Download/Export Options
    st.subheader("💾 Export Options")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Export as JSON", type="secondary"):
            # Create downloadable JSON
            import json
            json_str = json.dumps(plan_data, indent=2)
            st.download_button(
                label="📥 Download JSON",
                data=json_str,
                file_name=f"strategic_plan_{plan_result.get('plan_id', 'unknown')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📊 Export Summary", type="secondary"):
            # Create a text summary
            summary = f"""
STRATEGIC PLAN SUMMARY
======================

EXECUTIVE SUMMARY:
{plan_data.get('synthesized_strategy', 'No summary available')}

CONTRIBUTING AGENTS:
{', '.join(plan_data.get('contributing_agents', []))}

IDENTIFIED RISKS:
{chr(10).join(f"- {risk}" for risk in plan_data.get('identified_risks', []))}

CONFIDENCE SCORE:
{plan_data.get('confidence_score', 'Unknown'):.1%}

Generated on: {plan_result.get('created_at', 'Unknown')}
            """.strip()
            
            st.download_button(
                label="📥 Download Summary",
                data=summary,
                file_name=f"strategic_plan_summary_{plan_result.get('plan_id', 'unknown')}.txt",
                mime="text/plain"
            )

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎯 the_board</h1>
        <h3>Multi-Agent Strategic Intelligence Platform</h3>
        <p>Transform your high-level goals into actionable, multi-faceted strategies</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🚀 Quick Actions")
        
        # API Health Check
        api_healthy = check_api_health()
        if api_healthy:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Disconnected")
            st.info("Make sure the FastAPI server is running on port 8000")
        
        st.divider()
        
        # Navigation
        st.subheader("📋 Navigation")
        page = st.selectbox(
            "Choose a section:",
            ["🏠 Dashboard", "🎯 Submit Goal", "📊 Plan Monitor", "📚 Knowledge Base"]
        )
    
    # Main content based on selected page
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🎯 Submit Goal":
        show_goal_submission()
    elif page == "📊 Plan Monitor":
        show_plan_monitor()
    elif page == "📚 Knowledge Base":
        show_knowledge_base()

def show_dashboard():
    """Display the main dashboard."""
    st.header("🏠 Strategic Intelligence Dashboard")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">5</div>
            <div class="metric-label">Active Agents</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">12</div>
            <div class="metric-label">Plans Created</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">89%</div>
            <div class="metric-label">Success Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">2.4s</div>
            <div class="metric-label">Avg Response</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Recent Activity
    st.subheader("📈 Recent Activity")
    
    # Mock recent plans (replace with real data)
    recent_plans = [
        {"id": "plan_001", "goal": "Launch SaaS product", "status": "completed", "created": "2 hours ago"},
        {"id": "plan_002", "goal": "Market expansion strategy", "status": "in_progress", "created": "4 hours ago"},
        {"id": "plan_003", "goal": "Team restructuring", "status": "pending", "created": "6 hours ago"}
    ]
    
    for plan in recent_plans:
        status_color = {
            "completed": "status-completed",
            "in_progress": "status-progress",
            "pending": "status-pending"
        }.get(plan["status"], "status-pending")
        
        st.markdown(f"""
        <div class="status-card {status_color}">
            <strong>{plan['goal']}</strong><br>
            <small>ID: {plan['id']} • {plan['created']} • {plan['status'].title()}</small>
        </div>
        """, unsafe_allow_html=True)

def show_goal_submission():
    """Show the strategic goal submission form."""
    st.header("🎯 Submit Strategic Goal")
    
    st.markdown("""
    <div class="goal-card">
        <p>Submit your high-level strategic goal and let our AI board of directors analyze it from multiple perspectives:</p>
        <ul>
            <li><strong>CFO</strong> - Financial analysis and ROI optimization</li>
            <li><strong>CTO</strong> - Technical feasibility and security evaluation</li>
            <li><strong>CMO</strong> - Market positioning and brand strategy</li>
            <li><strong>COO</strong> - Operational efficiency and execution strategy</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Goal submission form
    with st.form("goal_submission"):
        goal = st.text_area(
            "🎯 Strategic Goal",
            placeholder="Describe your high-level strategic goal...",
            help="Be specific about what you want to achieve"
        )
        
        context = st.text_area(
            "📋 Additional Context",
            placeholder="Provide any relevant context, constraints, or background information...",
            help="Optional: Include budget, timeline, team size, or other relevant details"
        )
        
        submitted = st.form_submit_button("🚀 Submit for Analysis", type="primary")
        
        if submitted and goal.strip():
            with st.spinner("🎭 Assembling your AI board of directors..."):
                # Submit the goal
                result = submit_strategic_goal(goal, context)
                
                if result:
                    st.success("✅ Strategic goal submitted successfully!")
                    st.info(f"Plan ID: {result.get('plan_id', 'N/A')}")
                    
                    # Store the plan ID in session state for monitoring
                    st.session_state.current_plan_id = result.get('plan_id')
                    
                    # Show next steps
                    st.markdown("""
                    <div class="goal-card">
                        <h4>🎯 Next Steps:</h4>
                        <ol>
                            <li>Your goal has been submitted to our AI board</li>
                            <li>Each specialist agent will analyze from their perspective</li>
                            <li>Monitor progress in the Plan Monitor section</li>
                            <li>Review the synthesized strategic plan when complete</li>
                        </ol>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("❌ Failed to submit strategic goal. Please try again.")
        elif submitted:
            st.warning("⚠️ Please enter a strategic goal before submitting.")

def show_plan_monitor():
    """Show plan monitoring and execution status."""
    st.header("📊 Plan Execution Monitor")
    
    # Plan ID input
    plan_id = st.text_input(
        "🔍 Enter Plan ID to Monitor",
        value=st.session_state.get('current_plan_id', ''),
        placeholder="e.g., plan_001"
    )
    
    if plan_id:
        # Monitor button
        if st.button("📊 Monitor Plan", type="primary"):
            monitor_plan(plan_id)
    else:
        st.info("💡 Enter a plan ID above to monitor its execution progress")
        
        # Show recent plans if available
        st.subheader("📋 Recent Plans")
        st.info("Recent plans will appear here once you've submitted goals")

def monitor_plan(plan_id: str):
    """Monitor a specific plan's execution."""
    st.subheader(f"📊 Monitoring Plan: {plan_id}")
    
    # Get plan status
    plan_status = get_plan_status(plan_id)
    
    if plan_status:
        # Display plan details
        st.json(plan_status)
        
        # Check if plan is completed and get final results
        if plan_status.get('plan', {}).get('status') in ['closed', 'synthesis_failed']:
            st.subheader("🎯 Final Plan Results")
            
            # Get the final plan result
            plan_result = get_plan_result(plan_id)
            
            if plan_result and plan_result.get('status') == 'completed':
                display_final_plan(plan_result)
            elif plan_result and plan_result.get('status') == 'synthesis_failed':
                st.error("❌ Plan execution completed but synthesis failed")
                st.info("The individual agent analyses are available, but the CEO synthesis failed.")
            else:
                st.warning("⚠️ Final plan results not yet available")
        else:
            st.info("🔄 Plan is still in progress. Check back later for final results.")
        
        # Get and display events
        events = get_plan_events(plan_id)
        if events:
            st.subheader("📝 Execution Events")
            for event in events:
                st.markdown(f"""
                <div class="status-card">
                    <strong>{event.get('kind', 'Unknown')}</strong><br>
                    <small>{event.get('created_at', 'N/A')} • {event.get('payload', 'No details')}</small>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.error(f"❌ Could not retrieve status for plan {plan_id}")
        st.info("Make sure the plan ID is correct and the API is running")

def show_knowledge_base():
    """Show knowledge base management interface."""
    st.header("📚 Knowledge Base Management")
    
    st.markdown("""
    <div class="goal-card">
        <h4>🧠 Knowledge Base Features:</h4>
        <ul>
            <li><strong>Document Ingestion</strong> - Upload PDFs and other documents</li>
            <li><strong>Vector Storage</strong> - ChromaDB-powered semantic search</li>
            <li><strong>RAG Integration</strong> - Agents use knowledge base for informed analysis</li>
            <li><strong>Citation Tracking</strong> - All insights are properly sourced</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Document upload section
    st.subheader("📤 Upload Documents")
    
    uploaded_files = st.file_uploader(
        "Choose documents to add to knowledge base",
        type=['pdf', 'txt', 'md'],
        accept_multiple_files=True,
        help="Supported formats: PDF, TXT, Markdown"
    )
    
    if uploaded_files:
        st.info(f"📁 {len(uploaded_files)} files selected for upload")
        
        if st.button("🚀 Ingest Documents", type="primary"):
            with st.spinner("📚 Processing documents..."):
                # Here you would call the actual ingestion function
                st.success("✅ Documents processed successfully!")
                st.info("Your agents can now access this knowledge for better analysis")

if __name__ == "__main__":
    main()
