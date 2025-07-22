"""
Styling utilities for the PsyTech Child Wellness Companion
Custom CSS and styling functions
"""

import streamlit as st

def apply_custom_css():
    """Apply custom CSS styling to the application"""
    
    custom_css = """
    <style>
    /* Main app styling */
    .main {
        padding-top: 2rem;
    }
    
    /* Custom color scheme */
    :root {
        --primary-color: #4A90E2;
        --secondary-color: #7ED321;
        --accent-color: #F5A623;
        --danger-color: #D0021B;
        --success-color: #50E3C2;
        --warning-color: #F8E71C;
        --text-color: #333333;
        --light-gray: #F8F9FA;
        --medium-gray: #E9ECEF;
        --dark-gray: #6C757D;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* Activity card styling */
    .activity-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 5px solid var(--primary-color);
        transition: all 0.3s ease;
    }
    
    .activity-card:hover {
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }
    
    .activity-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .activity-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: var(--text-color);
        margin: 0;
    }
    
    .activity-badges {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    
    .badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-difficulty-beginner {
        background-color: var(--success-color);
        color: white;
    }
    
    .badge-difficulty-intermediate {
        background-color: var(--warning-color);
        color: var(--text-color);
    }
    
    .badge-difficulty-advanced {
        background-color: var(--danger-color);
        color: white;
    }
    
    .badge-duration {
        background-color: var(--medium-gray);
        color: var(--text-color);
    }
    
    .badge-skill {
        background-color: var(--primary-color);
        color: white;
    }
    
    /* Form styling */
    .form-section {
        background: var(--light-gray);
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .form-section h3 {
        color: var(--primary-color);
        margin-top: 0;
        margin-bottom: 1.5rem;
        font-size: 1.3rem;
        font-weight: 600;
    }
    
    /* Progress indicator */
    .progress-container {
        background: var(--light-gray);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .progress-step {
        display: flex;
        align-items: center;
        margin: 0.5rem 0;
    }
    
    .progress-step-completed {
        color: var(--success-color);
    }
    
    .progress-step-current {
        color: var(--primary-color);
        font-weight: 600;
    }
    
    .progress-step-pending {
        color: var(--dark-gray);
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 25px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Primary button */
    .btn-primary {
        background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
        color: white;
    }
    
    /* Secondary button */
    .btn-secondary {
        background: var(--medium-gray);
        color: var(--text-color);
    }
    
    /* Success button */
    .btn-success {
        background: var(--success-color);
        color: white;
    }
    
    /* Danger button */
    .btn-danger {
        background: var(--danger-color);
        color: white;
    }
    
    /* Feedback section */
    .feedback-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    
    .feedback-section h3 {
        color: white;
        margin-top: 0;
    }
    
    /* Dashboard cards */
    .dashboard-card {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    
    .dashboard-metric {
        font-size: 3rem;
        font-weight: 700;
        color: var(--primary-color);
        margin: 0;
    }
    
    .dashboard-label {
        font-size: 1.1rem;
        color: var(--dark-gray);
        margin: 0.5rem 0 0 0;
    }
    
    /* Article card styling */
    .article-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid var(--accent-color);
    }
    
    .article-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--text-color);
        margin: 0 0 0.5rem 0;
    }
    
    .article-summary {
        color: var(--dark-gray);
        line-height: 1.6;
        margin: 0.5rem 0;
    }
    
    .article-tags {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-top: 1rem;
    }
    
    .article-tag {
        background: var(--light-gray);
        color: var(--text-color);
        padding: 0.25rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        
        .main-header p {
            font-size: 1rem;
        }
        
        .activity-card {
            padding: 1rem;
        }
        
        .activity-card-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 1rem;
        }
        
        .dashboard-card {
            padding: 1.5rem;
        }
        
        .dashboard-metric {
            font-size: 2rem;
        }
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--light-gray);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--secondary-color);
    }
    </style>
    """
    
    st.markdown(custom_css, unsafe_allow_html=True)

def create_activity_card_html(activity_data, card_id):
    """Create HTML for an activity card"""
    
    difficulty_class = f"badge-difficulty-{activity_data.get('difficulty', 'beginner').lower()}"
    
    html = f"""
    <div class="activity-card" id="card-{card_id}">
        <div class="activity-card-header">
            <h3 class="activity-title">{activity_data.get('name', 'Activity')}</h3>
            <div class="activity-badges">
                <span class="badge {difficulty_class}">{activity_data.get('difficulty', 'Beginner')}</span>
                <span class="badge badge-duration">{activity_data.get('duration', '15 min')}</span>
            </div>
        </div>
        <p>{activity_data.get('description', 'Activity description')}</p>
        <div class="activity-badges">
    """
    
    # Add skill badges
    skills = activity_data.get('skills', [])
    for skill in skills:
        html += f'<span class="badge badge-skill">{skill}</span>'
    
    html += """
        </div>
    </div>
    """
    
    return html

def create_dashboard_metric_html(value, label, color="primary"):
    """Create HTML for a dashboard metric card"""
    
    html = f"""
    <div class="dashboard-card">
        <div class="dashboard-metric" style="color: var(--{color}-color);">{value}</div>
        <div class="dashboard-label">{label}</div>
    </div>
    """
    
    return html

def create_progress_indicator_html(steps, current_step):
    """Create HTML for progress indicator"""
    
    html = '<div class="progress-container">'
    
    for i, step in enumerate(steps):
        if i < current_step:
            status_class = "progress-step-completed"
            icon = "✅"
        elif i == current_step:
            status_class = "progress-step-current"
            icon = "🔄"
        else:
            status_class = "progress-step-pending"
            icon = "⏳"
        
        html += f"""
        <div class="progress-step {status_class}">
            <span style="margin-right: 0.5rem;">{icon}</span>
            <span>{step}</span>
        </div>
        """
    
    html += '</div>'
    
    return html
