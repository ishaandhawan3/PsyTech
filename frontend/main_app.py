"""
PsyTech Child Wellness Companion - Main Application
Multi-page Streamlit application for child development and wellness tracking
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add the current directory and parent directory to Python path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent  # This is the psyTech directory
sys.path.append(str(current_dir))
sys.path.append(str(parent_dir))  # Add parent directory to path

# Import page modules
from service.questionnaire import show_questionnaire_page
from service.activity_recommendations import show_activity_recommendations_page
from service.feedback_collection import show_feedback_collection_page
from service.evaluation_dashboard import show_evaluation_dashboard_page
from service.article_feed import show_article_feed_page
from utils.navigation import init_navigation, get_current_page, navigate_to_page
from utils.styling import apply_custom_css
from utils.json_database_adapter import init_database

# Page configuration
st.set_page_config(
    page_title="Wellness Companion",
    page_icon="👨‍⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application entry point"""
    
    # Initialize database
    init_database()
    
    # Apply custom styling
    apply_custom_css()
    
    # Initialize navigation
    init_navigation()
    
    # Get current page
    current_page = get_current_page()
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🚸 Wellness Companion")
        st.markdown("---")
        
        # Navigation menu
        service = {
            "questionnaire": "📝 Child Profile",
            "activities": "🎯 Activity Recommendations", 
            "feedback": "💭 Activity Feedback",
            "dashboard": "📊 Progress Dashboard",
            "articles": "📚 Learning Resources"
        }
        
        # Show navigation based on progress
        for page_key, page_name in service.items():
            if st.button(page_name, key=f"nav_{page_key}", use_container_width=True):
                navigate_to_page(page_key)
                st.rerun()
        
        st.markdown("---")
        
        # Progress indicator
        if 'user_profile' in st.session_state:
            st.markdown("### 📈 Your Progress")
            progress_steps = {
                'questionnaire': st.session_state.get('profile_completed', False),
                'activities': st.session_state.get('activities_viewed', False),
                'feedback': st.session_state.get('feedback_given', False),
                'dashboard': st.session_state.get('dashboard_viewed', False),
                'articles': st.session_state.get('articles_viewed', False)
            }
            
            completed_steps = sum(progress_steps.values())
            total_steps = len(progress_steps)
            progress_percentage = (completed_steps / total_steps) * 100
            
            st.progress(progress_percentage / 100)
            st.caption(f"{completed_steps}/{total_steps} steps completed")
    
        # st.markdown("---")
        # if st.button("🔍 Data Inspector", use_container_width=True):
        #     # Import and run inspector
        #     from utils.json_database_adapter import run_inspector
        #     run_inspector()
    # Main content area
    if current_page == "questionnaire":
        show_questionnaire_page()
    elif current_page == "activities":
        show_activity_recommendations_page()
    elif current_page == "feedback":
        show_feedback_collection_page()
    elif current_page == "dashboard":
        show_evaluation_dashboard_page()
    elif current_page == "articles":
        show_article_feed_page()
    else:
        # Default to questionnaire page
        navigate_to_page("questionnaire")
        st.rerun()

if __name__ == "__main__":
    main()
