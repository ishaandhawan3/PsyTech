"""
Navigation utilities for the PsyTech Child Wellness Companion
Handles page routing and navigation state management
"""

import streamlit as st

def init_navigation():
    """Initialize navigation state"""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'questionnaire'
    
    if 'navigation_history' not in st.session_state:
        st.session_state.navigation_history = ['questionnaire']

def get_current_page():
    """Get the current page"""
    return st.session_state.get('current_page', 'questionnaire')

def navigate_to_page(page_name):
    """Navigate to a specific page"""
    if page_name != st.session_state.current_page:
        # Add to navigation history
        if 'navigation_history' not in st.session_state:
            st.session_state.navigation_history = []
        
        st.session_state.navigation_history.append(page_name)
        
        # Keep only last 10 pages in history
        if len(st.session_state.navigation_history) > 10:
            st.session_state.navigation_history = st.session_state.navigation_history[-10:]
        
        st.session_state.current_page = page_name

def get_navigation_history():
    """Get navigation history"""
    return st.session_state.get('navigation_history', [])

def can_navigate_to_page(page_name):
    """Check if user can navigate to a specific page based on progress"""
    # Always allow navigation to questionnaire
    if page_name == 'questionnaire':
        return True
    
    # Check if profile is completed for other pages
    profile_completed = st.session_state.get('profile_completed', False)
    
    if page_name == 'activities':
        return profile_completed
    elif page_name == 'feedback':
        return profile_completed and st.session_state.get('activities_viewed', False)
    elif page_name == 'dashboard':
        return profile_completed and st.session_state.get('feedback_given', False)
    elif page_name == 'articles':
        return profile_completed  # Articles can be accessed once profile is complete
    
    return False

def get_next_recommended_page():
    """Get the next recommended page based on current progress"""
    if not st.session_state.get('profile_completed', False):
        return 'questionnaire'
    elif not st.session_state.get('activities_viewed', False):
        return 'activities'
    elif not st.session_state.get('feedback_given', False):
        return 'feedback'
    elif not st.session_state.get('dashboard_viewed', False):
        return 'dashboard'
    else:
        return 'articles'

def show_breadcrumb():
    """Show breadcrumb navigation"""
    current_page = get_current_page()
    
    page_names = {
        'questionnaire': 'Child Profile',
        'activities': 'Activity Recommendations',
        'feedback': 'Activity Feedback', 
        'dashboard': 'Progress Dashboard',
        'articles': 'Learning Resources'
    }
    
    # Create breadcrumb
    breadcrumb_items = []
    history = get_navigation_history()
    
    if len(history) > 1:
        for i, page in enumerate(history[-3:]):  # Show last 3 pages
            if i < len(history[-3:]) - 1:
                breadcrumb_items.append(f"[{page_names.get(page, page)}]")
            else:
                breadcrumb_items.append(f"**{page_names.get(page, page)}**")
    
    if breadcrumb_items:
        st.caption(" → ".join(breadcrumb_items))
