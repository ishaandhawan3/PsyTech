"""
Feedback Collection Page for PsyTech Child Wellness Companion
Collects detailed feedback after activity completion
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.navigation import navigate_to_page, show_breadcrumb
from utils.json_database_adapter import save_activity_completion, save_activity_feedback, update_user_progress

def show_feedback_collection_page():
    """Display the feedback collection page"""
    
    # Check if activities have been viewed
    if not st.session_state.get('activities_viewed', False):
        st.warning("⚠️ Please view activity recommendations first.")
        if st.button("Go to Activities"):
            navigate_to_page('activities')
            st.rerun()
        return
    
    # Show breadcrumb navigation
    show_breadcrumb()
    
    # Page header
    st.markdown("""
    <div class="main-header">
        <h1>💭 Activity Feedback</h1>
        <p>Share your experience to help us provide better recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if there's a selected activity from the previous page
    if 'selected_activity' in st.session_state:
        show_activity_specific_feedback()
    else:
        show_general_feedback_collection()
    
    # Mark feedback as given
    st.session_state.feedback_given = True

def show_activity_specific_feedback():
    """Show feedback form for a specific activity that was selected"""
    
    activity = st.session_state.selected_activity
    start_time = st.session_state.get('activity_start_time')
    
    st.markdown(f"""
    <div class="feedback-section">
        <h3>🎯 Feedback for: {activity['name']}</h3>
        <p>Please share how the activity went with your child</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Activity completion form
    with st.form("activity_feedback_form"):
        st.markdown("### 📊 Activity Completion")
        
        # Completion status
        completion_status = st.radio(
            "Did your child complete the activity?",
            options=[
                "Completed successfully",
                "Partially completed", 
                "Started but didn't finish",
                "Child refused to participate",
                "Haven't tried it yet"
            ],
            help="Select the option that best describes what happened"
        )
        
        # Duration tracking
        col1, col2 = st.columns(2)
        
        with col1:
            if start_time:
                # Calculate elapsed time
                elapsed = datetime.now() - start_time.to_pydatetime()
                suggested_duration = max(5, int(elapsed.total_seconds() / 60))
            else:
                suggested_duration = 15
            
            actual_duration = st.number_input(
                "How long did the activity take? (minutes)",
                min_value=1,
                max_value=120,
                value=suggested_duration,
                help="Include setup and cleanup time"
            )
        
        with col2:
            difficulty_experienced = st.select_slider(
                "How difficult was it for your child?",
                options=["Too easy", "A bit easy", "Just right", "A bit hard", "Too hard"],
                value="Just right"
            )
        
        # Engagement assessment
        st.markdown("### 🌟 Engagement & Interest")
        
        col1, col2 = st.columns(2)
        
        with col1:
            interest_level = st.select_slider(
                "Child's interest level:",
                options=["😴 Not interested", "😐 Neutral", "😊 Interested", "😍 Very excited", "🤩 Absolutely loved it"],
                value="😊 Interested"
            )
            
            attention_span = st.slider(
                "How long did they stay focused?",
                min_value=1,
                max_value=60,
                value=15,
                step=5,
                format="%d minutes"
            )
        
        with col2:
            participation_level = st.select_slider(
                "Level of participation:",
                options=["Refused", "Reluctant", "Willing", "Eager", "Initiated more"],
                value="Willing"
            )
            
            help_needed = st.select_slider(
                "How much help did they need?",
                options=["None - independent", "Minimal guidance", "Some help", "Lots of help", "Full assistance"],
                value="Some help"
            )
        
        # Behavioral observations
        st.markdown("### 🎭 Behavioral Observations")
        
        # Initialize behavioral observations in session state if not present
        if 'behavioral_observations' not in st.session_state:
            st.session_state.behavioral_observations = []
        
        behavioral_observations = st.multiselect(
            "What did you observe during the activity?",
            options=[
                "Stayed calm and focused",
                "Showed frustration when challenged", 
                "Asked for help appropriately",
                "Tried multiple approaches",
                "Celebrated small successes",
                "Wanted to quit when it got hard",
                "Showed creativity or innovation",
                "Followed instructions well",
                "Had difficulty with fine motor aspects",
                "Had difficulty with gross motor aspects",
                "Showed social engagement",
                "Demonstrated problem-solving",
                "Expressed emotions appropriately",
                "Needed frequent breaks",
                "Showed sensory sensitivities"
            ],
            default=st.session_state.behavioral_observations,
            key="behavioral_observations_multiselect"
        )
        st.session_state.behavioral_observations = behavioral_observations
        
        # Skill development
        st.markdown("### 📈 Skill Development")
        
        # Get activity skills and normalize them to match options
        activity_skills = activity.get('skills', [])
        
        # Define skill mapping to handle case mismatches
        skill_mapping = {
            'Fine Motor': 'Fine motor skills',
            'Gross Motor': 'Gross motor skills',
            'Communication': 'Communication skills',
            'Social': 'Social skills',
            'Problem Solving': 'Problem-solving',
            'Instructions': 'Following instructions',
            'Attention': 'Attention and focus',
            'Emotional': 'Emotional regulation',
            'Creative': 'Creativity',
            'Independence': 'Independence',
            'Academic': 'Academic skills',
            'Self Care': 'Self-care skills'
        }
        
        # Normalize default values to match options
        normalized_defaults = []
        for skill in activity_skills:
            if skill in skill_mapping:
                normalized_defaults.append(skill_mapping[skill])
            elif skill in [
                "Fine motor skills", "Gross motor skills", "Communication skills",
                "Social skills", "Problem-solving", "Following instructions",
                "Attention and focus", "Emotional regulation", "Creativity",
                "Independence", "Academic skills", "Self-care skills"
            ]:
                normalized_defaults.append(skill)
        
        # Initialize skills practiced in session state if not present
        if 'skills_practiced' not in st.session_state:
            st.session_state.skills_practiced = normalized_defaults
        
        skills_practiced = st.multiselect(
            "Which skills did your child practice?",
            options=[
                "Fine motor skills",
                "Gross motor skills", 
                "Communication skills",
                "Social skills",
                "Problem-solving",
                "Following instructions",
                "Attention and focus",
                "Emotional regulation",
                "Creativity",
                "Independence",
                "Academic skills",
                "Self-care skills"
            ],
            default=st.session_state.skills_practiced,
            key="skills_practiced_multiselect"
        )
        st.session_state.skills_practiced = skills_practiced
        
        improvements_noticed = st.text_area(
            "Any improvements or breakthroughs noticed?",
            placeholder="Describe any positive changes, new skills demonstrated, or breakthrough moments..."
        )
        
        # Overall rating
        st.markdown("### ⭐ Overall Rating")
        
        col1, col2 = st.columns(2)
        
        with col1:
            overall_rating = st.slider(
                "Overall activity rating:",
                min_value=1,
                max_value=5,
                value=3,
                help="1 = Poor, 5 = Excellent"
            )
        
        with col2:
            would_recommend = st.radio(
                "Would you recommend this activity to other parents?",
                options=["Yes, definitely", "Yes, with modifications", "Maybe", "Probably not", "No"]
            )
        
        # Additional feedback
        st.markdown("### 💬 Additional Comments")
        
        what_worked_well = st.text_area(
            "What worked well?",
            placeholder="What aspects of the activity were successful?"
        )
        
        what_could_improve = st.text_area(
            "What could be improved?",
            placeholder="How could this activity be better suited for your child?"
        )
        
        additional_comments = st.text_area(
            "Any other comments or observations?",
            placeholder="Share any other thoughts about the activity..."
        )
        
        # Photo upload (optional)
        st.markdown("### 📸 Share Your Experience (Optional)")
        
        uploaded_photo = st.file_uploader(
            "Upload a photo of the activity result or your child engaged in the activity",
            type=['png', 'jpg', 'jpeg'],
            help="Photos help us understand how activities work in real families"
        )
        
        # Submit button
        submitted = st.form_submit_button("Submit Feedback", use_container_width=True)
        
        if submitted:
            # Collect all feedback data
            feedback_data = {
                'completion_status': completion_status,
                'actual_duration': actual_duration,
                'difficulty_experienced': difficulty_experienced,
                'interest_level': interest_level,
                'attention_span': attention_span,
                'participation_level': participation_level,
                'help_needed': help_needed,
                'behavioral_observations': behavioral_observations,
                'skills_practiced': skills_practiced,
                'improvements_noticed': improvements_noticed,
                'overall_rating': overall_rating,
                'would_recommend': would_recommend,
                'what_worked_well': what_worked_well,
                'what_could_improve': what_could_improve,
                'additional_comments': additional_comments,
                'has_photo': uploaded_photo is not None,
                'submitted_at': str(datetime.now())
            }
            
            # Save to database
            if 'user_id' in st.session_state:
                # Save activity completion
                save_activity_completion(
                    st.session_state.user_id,
                    activity['name'],
                    activity,
                    completion_status,
                    overall_rating,
                    additional_comments,
                    actual_duration
                )
                
                # Save detailed feedback
                save_activity_feedback(
                    st.session_state.user_id,
                    activity['name'],
                    'detailed_feedback',
                    feedback_data
                )
                
                # Update progress for practiced skills
                for skill in skills_practiced:
                    # Simple progress calculation based on rating and completion
                    progress_increment = calculate_progress_increment(
                        completion_status, overall_rating, difficulty_experienced
                    )
                    update_skill_progress(skill, progress_increment)
            
            # Show success message
            st.success("✅ Thank you for your detailed feedback!")
            st.balloons()
            
            # Set flag to show navigation button
            st.session_state.feedback_submitted = True
            
            # Clear the selected activity
            if 'selected_activity' in st.session_state:
                del st.session_state.selected_activity
            if 'activity_start_time' in st.session_state:
                del st.session_state.activity_start_time
            
            # Navigate to dashboard
            st.info("🎯 Let's see how this contributes to your child's progress!")
    
    # Move the navigation button outside the form
    if st.session_state.get('feedback_submitted', False):
        if st.button("View Progress Dashboard"):
            navigate_to_page('dashboard')
            st.session_state.feedback_submitted = False  # Reset the flag
            st.rerun()

def show_general_feedback_collection():
    """Show general feedback collection for multiple activities"""
    
    st.markdown("### 🎯 Activity Feedback Center")
    
    # Check if there are any saved activities to give feedback on
    saved_activities = st.session_state.get('saved_activities', [])
    recommended_activities = st.session_state.get('recommended_activities', [])
    
    if not saved_activities and not recommended_activities:
        st.info("No activities to provide feedback on. Please visit the Activity Recommendations page first.")
        if st.button("Go to Activity Recommendations"):
            navigate_to_page('activities')
            st.rerun()
        return
    
    # Activity selection
    all_activities = []
    if saved_activities:
        all_activities.extend([(act, "Saved") for act in saved_activities])
    if recommended_activities:
        all_activities.extend([(act, "Recommended") for act in recommended_activities])
    
    if all_activities:
        st.markdown("### 📝 Select an Activity to Provide Feedback")
        
        activity_options = [f"{act[0]['name']} ({act[1]})" for act in all_activities]
        selected_option = st.selectbox(
            "Choose an activity you've tried:",
            options=["Select an activity..."] + activity_options
        )
        
        if selected_option != "Select an activity...":
            # Find the selected activity
            selected_index = activity_options.index(selected_option)
            selected_activity = all_activities[selected_index][0]
            
            # Store in session state and show feedback form
            st.session_state.selected_activity = selected_activity
            st.session_state.activity_start_time = pd.Timestamp.now() - pd.Timedelta(minutes=30)  # Estimate
            st.rerun()
    
    # Quick feedback section for multiple activities
    st.markdown("---")
    st.markdown("### ⚡ Quick Feedback")
    st.markdown("Rate activities you've tried recently:")
    
    # Show quick rating interface
    show_quick_rating_interface()
    
    # Navigation buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Back to Activities"):
            navigate_to_page('activities')
            st.rerun()
    
    with col3:
        if st.button("View Progress →"):
            navigate_to_page('dashboard')
            st.rerun()

def show_quick_rating_interface():
    """Show quick rating interface for multiple activities"""
    
    # Get activities that might have been tried
    recommended_activities = st.session_state.get('recommended_activities', [])
    
    if not recommended_activities:
        st.info("No activities to rate. Please visit Activity Recommendations first.")
        return
    
    st.markdown("Rate any activities you've tried:")
    
    for i, activity in enumerate(recommended_activities[:3]):  # Show top 3 for quick rating
        with st.expander(f"Rate: {activity['name']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                tried = st.checkbox(
                    "We tried this activity",
                    key=f"tried_{i}_{activity['name']}"
                )
            
            if tried:
                with col2:
                    rating = st.slider(
                        "Rating (1-5 stars)",
                        min_value=1,
                        max_value=5,
                        value=3,
                        key=f"rating_{i}_{activity['name']}"
                    )
                
                with col3:
                    completion = st.selectbox(
                        "Completion",
                        options=["Completed", "Partial", "Started only"],
                        key=f"completion_{i}_{activity['name']}"
                    )
                
                # Quick comment
                quick_comment = st.text_input(
                    "Quick comment (optional)",
                    placeholder="How did it go?",
                    key=f"comment_{i}_{activity['name']}"
                )
                
                if st.button(f"Save Rating for {activity['name']}", key=f"save_{i}"):
                    # Save quick feedback
                    quick_feedback_data = {
                        'rating': rating,
                        'completion': completion,
                        'comment': quick_comment,
                        'feedback_type': 'quick_rating',
                        'submitted_at': str(datetime.now())
                    }
                    
                    if 'user_id' in st.session_state:
                        save_activity_feedback(
                            st.session_state.user_id,
                            activity['name'],
                            'quick_rating',
                            quick_feedback_data
                        )
                        
                        # Update progress
                        progress_increment = rating * 0.2  # Simple calculation
                        for skill in activity.get('skills', []):
                            update_skill_progress(skill, progress_increment)
                    
                    st.success(f"✅ Rating saved for {activity['name']}!")

def calculate_progress_increment(completion_status, rating, difficulty):
    """Calculate progress increment based on feedback"""
    
    base_increment = 0
    
    # Base increment from completion
    completion_multipliers = {
        "Completed successfully": 1.0,
        "Partially completed": 0.6,
        "Started but didn't finish": 0.3,
        "Child refused to participate": 0.1,
        "Haven't tried it yet": 0.0
    }
    
    base_increment = completion_multipliers.get(completion_status, 0.5)
    
    # Adjust for rating (1-5 scale)
    rating_multiplier = rating / 5.0
    
    # Adjust for difficulty
    difficulty_multipliers = {
        "Too easy": 0.8,
        "A bit easy": 0.9,
        "Just right": 1.0,
        "A bit hard": 1.2,
        "Too hard": 0.7  # Less progress if too hard
    }
    
    difficulty_multiplier = difficulty_multipliers.get(difficulty, 1.0)
    
    # Calculate final increment (0-10 scale)
    final_increment = base_increment * rating_multiplier * difficulty_multiplier * 10
    
    return min(final_increment, 10)  # Cap at 10

def update_skill_progress(skill, increment):
    """Update progress for a specific skill"""
    
    if 'user_id' not in st.session_state:
        return
    
    # Get current progress
    from utils.json_database_adapter import get_user_progress, update_user_progress
    
    current_progress = get_user_progress(st.session_state.user_id)
    current_score = current_progress.get(skill, {}).get('score', 0)
    
    # Calculate new score (0-100 scale)
    new_score = min(current_score + increment, 100)
    
    # Update in database
    update_user_progress(
        st.session_state.user_id,
        skill,
        new_score,
        f"Updated from activity feedback: +{increment:.1f}"
    )

def show_feedback_history():
    """Show history of feedback given"""
    
    st.markdown("### 📊 Your Feedback History")
    
    if 'user_id' in st.session_state:
        from utils.json_database_adapter import get_activity_feedback
        
        feedback_history = get_activity_feedback(st.session_state.user_id)
        
        if feedback_history:
            for feedback in feedback_history[-5:]:  # Show last 5
                with st.expander(f"{feedback['activity_name']} - {feedback['created_at'][:10]}"):
                    st.json(feedback['data'])
        else:
            st.info("No feedback history yet. Complete some activities to see your progress!")
    else:
        st.info("Please complete your profile to see feedback history.")
