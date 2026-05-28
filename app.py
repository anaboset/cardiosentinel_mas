"""CardioSentinel MAS - Streamlit UI Entry Point."""

import streamlit as st
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set Streamlit page config
st.set_page_config(
    page_title="🫀 CardioSentinel",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/anaboset/cardiosentinel",
        "Report a bug": "https://github.com/anaboset/cardiosentinel/issues",
        "About": "CardioSentinel MAS - Multi-Agent Clinical Reasoning System",
    }
)

# Import UI components and styling
from pages import history, home, new_analysis, results, review
from ui.styles.theme import apply_theme, apply_custom_css
from pages import workflow

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"New session: {st.session_state.session_id}")

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

if "current_workflow" not in st.session_state:
    st.session_state.current_workflow = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

# Apply theme
apply_theme(st.session_state.theme)
apply_custom_css()

# Sidebar
with st.sidebar:
    st.markdown("# 🫀 CardioSentinel")
    st.markdown("---")
    st.markdown("### Clinical Decision Support")
    st.markdown("Multi-Agent AI System for Cardiovascular Care")
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "Navigation",
        ["Home", "New Analysis", "Active Workflow", "Review & Approve", "Results", "History"],
        label_visibility="collapsed",
        index=["Home", "New Analysis", "Active Workflow", "Review & Approve", "Results", "History"].index(st.session_state.current_page)
    )
    st.session_state.current_page = page
    
    st.markdown("---")
    
    # Settings
    with st.expander("⚙️ Settings"):
        theme = st.radio(
            "Theme",
            ["Light", "Dark", "Auto"],
            index=1,
            label_visibility="collapsed"
        )
        st.session_state.theme = theme.lower()
        
        st.checkbox("Enable Analytics", value=True)
        st.checkbox("Auto-save decisions", value=True)
    
    st.markdown("---")
    
    # Session info
    with st.expander("ℹ️ Session Info"):
        st.markdown(f"**Session ID**: `{st.session_state.session_id}`")
        st.markdown(f"**Started**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        if st.session_state.current_workflow:
            st.markdown(f"**Status**: {st.session_state.current_workflow.get('status', 'Unknown')}")

# Route to pages
if st.session_state.current_page == "Home":
    home.render()
elif st.session_state.current_page == "New Analysis":
    new_analysis.render()
elif st.session_state.current_page == "Active Workflow":
    workflow.render()
elif st.session_state.current_page == "Review & Approve":
    review.render()
elif st.session_state.current_page == "Results":
    results.render()
elif st.session_state.current_page == "History":
    history.render()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.8em;">
    <p>CardioSentinel MAS v1.0 | Phase II: Multi-Agent Reasoning</p>
    <p>⚠️ For research and demonstration purposes only. Not for clinical use.</p>
</div>
""", unsafe_allow_html=True)
