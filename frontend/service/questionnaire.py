"""
Questionnaire Page for PsyTech Child Wellness Companion
Multi-step form to collect comprehensive child profile information
"""

import streamlit as st
from utils.navigation import navigate_to_page, show_breadcrumb
from utils.styling import create_progress_indicator_html
from utils.json_database_adapter import save_user_profile, update_user_profile, get_user_profile

def show_questionnaire_page():
    """Display the questionnaire page with multi-step form"""
    
    # Show breadcrumb navigation
    show_breadcrumb()
    
    # Page header
    st.markdown("""
    <div class="main-header">
        <h1>📝 Child Profile Questionnaire</h1>
        <p>Help us understand your child better to provide personalized recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize form state
    if 'questionnaire_step' not in st.session_state:
        st.session_state.questionnaire_step = 1
    
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}
    
    # Load existing profile if available
    if 'user_id' in st.session_state and not st.session_state.form_data:
        existing_profile = get_user_profile(st.session_state.user_id)
        if existing_profile:
            st.session_state.form_data = existing_profile
    
    # Progress indicator
    steps = [
        "Basic Information",
        "Developmental Profile", 
        "Goals & Preferences",
        "Sensory & Physical",
        "Motivation & Interests"
    ]
    
    current_step = st.session_state.questionnaire_step - 1
    progress_html = create_progress_indicator_html(steps, current_step)
    # st.markdown(progress_html, unsafe_allow_html=True)
    
    # Display current step
    if st.session_state.questionnaire_step == 1:
        show_step_1_basic_info()
    elif st.session_state.questionnaire_step == 2:
        show_step_2_developmental_profile()
    elif st.session_state.questionnaire_step == 3:
        show_step_3_goals_preferences()
    elif st.session_state.questionnaire_step == 4:
        show_step_4_sensory_physical()
    elif st.session_state.questionnaire_step == 5:
        show_step_5_motivation_interests()
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.session_state.questionnaire_step > 1:
            if st.button("← Previous", key="prev_step"):
                st.session_state.questionnaire_step -= 1
                st.rerun()
    
    with col3:
        if st.session_state.questionnaire_step < 5:
            if st.button("Next →", key="next_step"):
                if validate_current_step():
                    st.session_state.questionnaire_step += 1
                    st.rerun()
        else:
            if st.button("Complete Profile ✓", key="complete_profile"):
                if validate_current_step():
                    save_profile_and_continue()

def show_step_1_basic_info():
    """Step 1: Basic Information"""
    
    st.markdown("""
    <div class="form-section">
        <h3>👶 Basic Information</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        child_name = st.text_input(
            "Child's Name *",
            value=st.session_state.form_data.get('name', ''),
            help="Enter your child's first name or preferred name"
        )
        st.session_state.form_data['name'] = child_name
        
        age = st.selectbox(
            "Child's Age *",
            options=[''] + [f"{i} years old" for i in range(2, 19)],
            index=0 if not st.session_state.form_data.get('age') else 
                  [f"{i} years old" for i in range(2, 19)].index(st.session_state.form_data.get('age', '')) + 1
        )
        st.session_state.form_data['age'] = age
    
    with col2:
        gender = st.selectbox(
            "Gender (Optional)",
            options=['Prefer not to say', 'Male', 'Female', 'Non-binary', 'Other'],
            index=['Prefer not to say', 'Male', 'Female', 'Non-binary', 'Other'].index(
                st.session_state.form_data.get('gender', 'Prefer not to say')
            )
        )
        st.session_state.form_data['gender'] = gender
        
        primary_language = st.selectbox(
            "Primary Language at Home",
            options=['English', 'Spanish', 'French', 'Mandarin', 'Hindi', 'Arabic', 'Other'],
            index=['English', 'Spanish', 'French', 'Mandarin', 'Hindi', 'Arabic', 'Other'].index(
                st.session_state.form_data.get('primary_language', 'English')
            )
        )
        st.session_state.form_data['primary_language'] = primary_language
    
    # Additional context
    st.markdown("### 📋 Additional Context")
    
    # Family structure selection
    family_structure = st.selectbox(
        "Family Structure *",
        options=['', 'Joint family', 'Nuclear family', 'Single mom', 'Single dad'],
        index=0 if not st.session_state.form_data.get('family_structure') else 
              ['', 'Joint family', 'Nuclear family', 'Single mom', 'Single dad'].index(st.session_state.form_data.get('family_structure', '')) if st.session_state.form_data.get('family_structure', '') in ['', 'Joint family', 'Nuclear family', 'Single mom', 'Single dad'] else 0,
        help="Select the family structure that best describes your household"
    )
    st.session_state.form_data['family_structure'] = family_structure
    
    # Siblings information
    col1, col2 = st.columns(2)
    
    with col1:
        has_siblings = st.selectbox(
            "Does your child have siblings?",
            options=['No', 'Yes'],
            index=['No', 'Yes'].index(st.session_state.form_data.get('has_siblings', 'No'))
        )
        st.session_state.form_data['has_siblings'] = has_siblings
    
    with col2:
        if has_siblings == 'Yes':
            num_siblings = st.selectbox(
                "Number of siblings",
                options=[1, 2, 3, 4, 5, '6 or more'],
                index=0 if not st.session_state.form_data.get('num_siblings') else 
                      [1, 2, 3, 4, 5, '6 or more'].index(st.session_state.form_data.get('num_siblings', 1)) if st.session_state.form_data.get('num_siblings', 1) in [1, 2, 3, 4, 5, '6 or more'] else 0
            )
            st.session_state.form_data['num_siblings'] = num_siblings
        else:
            st.session_state.form_data['num_siblings'] = 0

def show_step_2_developmental_profile():
    """Step 2: Developmental Profile"""
    
    st.markdown("""
    <div class="form-section">
        <h3>🧠 Developmental Profile</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Strengths
    st.markdown("#### ✨ Current Strengths")
    
    strength_options = [
        'Creative and imaginative', 'Good with numbers/math', 'Strong memory',
        'Excellent fine motor skills', 'Good gross motor skills', 'Social and friendly',
        'Independent', 'Good listener', 'Follows instructions well',
        'Problem solver', 'Artistic abilities', 'Musical abilities',
        'Good with technology', 'Empathetic', 'Curious and inquisitive'
    ]
    
    # Initialize strengths directly in session state if not present
    if 'selected_strengths_direct' not in st.session_state:
        if 'selected_strengths' in st.session_state.form_data:
            st.session_state.selected_strengths_direct = st.session_state.form_data['selected_strengths']
        else:
            st.session_state.selected_strengths_direct = []
            st.session_state.form_data['selected_strengths'] = []
    
    selected_strengths = st.multiselect(
        "Select your child's strengths:",
        options=strength_options,
        default=st.session_state.selected_strengths_direct,
        key="strengths_multiselect"
    )
    # Update both direct session state and form_data
    st.session_state.selected_strengths_direct = selected_strengths
    st.session_state.form_data['selected_strengths'] = selected_strengths
    
    additional_strengths = st.text_area(
        "Additional strengths not listed above:",
        value=st.session_state.form_data.get('additional_strengths', ''),
        placeholder="Describe any other strengths..."
    )
    st.session_state.form_data['additional_strengths'] = additional_strengths
    
    # Challenges
    st.markdown("#### 🎯 Areas of Challenge")
    
    challenge_options = [
        'Attention and focus', 'Following instructions', 'Social interactions',
        'Communication/speech', 'Fine motor skills', 'Gross motor skills',
        'Emotional regulation', 'Sensory sensitivities', 'Transitions/changes',
        'Academic skills', 'Self-care tasks', 'Behavioral issues',
        'Sleep difficulties', 'Eating/feeding issues', 'Anxiety/fears'
    ]
    
    # Initialize challenges directly in session state if not present
    if 'selected_challenges_direct' not in st.session_state:
        if 'selected_challenges' in st.session_state.form_data:
            st.session_state.selected_challenges_direct = st.session_state.form_data['selected_challenges']
        else:
            st.session_state.selected_challenges_direct = []
            st.session_state.form_data['selected_challenges'] = []
    
    selected_challenges = st.multiselect(
        "Select areas where your child faces challenges:",
        options=challenge_options,
        default=st.session_state.selected_challenges_direct,
        key="challenges_multiselect"
    )
    # Update both direct session state and form_data
    st.session_state.selected_challenges_direct = selected_challenges
    st.session_state.form_data['selected_challenges'] = selected_challenges
    
    additional_challenges = st.text_area(
        "Additional challenges not listed above:",
        value=st.session_state.form_data.get('additional_challenges', ''),
        placeholder="Describe any other challenges..."
    )
    st.session_state.form_data['additional_challenges'] = additional_challenges
    
    # Diagnoses
    st.markdown("#### 🏥 Previous Diagnoses")
    
    diagnosis_options = [
        'No formal diagnosis', 'ADHD', 'Autism Spectrum Disorder', 'Learning Disabilities',
        'Anxiety Disorders', 'Depression', 'Sensory Processing Disorder',
        'Cerebral Palsy', 'Intellectual Disabilities', 'Speech/Language Disorders',
        'Behavioral Disorders', 'Mood Disorders', 'PTSD', 'Other'
    ]
    
    # Initialize diagnoses directly in session state if not present
    if 'selected_diagnoses_direct' not in st.session_state:
        if 'selected_diagnoses' in st.session_state.form_data:
            st.session_state.selected_diagnoses_direct = st.session_state.form_data['selected_diagnoses']
        else:
            st.session_state.selected_diagnoses_direct = []
            st.session_state.form_data['selected_diagnoses'] = []
    
    selected_diagnoses = st.multiselect(
        "Select any formal diagnoses:",
        options=diagnosis_options,
        default=st.session_state.selected_diagnoses_direct,
        key="diagnoses_multiselect"
    )
    # Update both direct session state and form_data
    st.session_state.selected_diagnoses_direct = selected_diagnoses
    st.session_state.form_data['selected_diagnoses'] = selected_diagnoses
    
    if 'Other' in selected_diagnoses:
        other_diagnosis = st.text_input(
            "Please specify other diagnosis:",
            value=st.session_state.form_data.get('other_diagnosis', '')
        )
        st.session_state.form_data['other_diagnosis'] = other_diagnosis
    
    # Current interventions
    current_therapies = st.text_area(
        "Current therapies or interventions:",
        value=st.session_state.form_data.get('current_therapies', ''),
        help="e.g., Speech therapy, Occupational therapy, ABA, etc.",
        placeholder="List any current therapies or interventions..."
    )
    st.session_state.form_data['current_therapies'] = current_therapies

def show_step_3_goals_preferences():
    """Step 3: Goals & Preferences"""
    
    st.markdown("""
    <div class="form-section">
        <h3>🎯 Goals & Preferences</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Skills to improve
    st.markdown("#### 📈 Priority Skills to Improve")
    
    skill_options = [
        'Fine motor skills', 'Gross motor skills', 'Communication skills',
        'Social skills', 'Attention and focus', 'Emotional regulation',
        'Academic skills', 'Self-care skills', 'Problem-solving',
        'Creativity', 'Independence', 'Following instructions'
    ]
    
    # Priority ranking system
    st.write("Rank the skills you'd most like to improve (drag to reorder or use the selectbox):")
    
    # Initialize priority skills directly in session state if not present
    if 'priority_skills_direct' not in st.session_state:
        if 'priority_skills' in st.session_state.form_data:
            st.session_state.priority_skills_direct = st.session_state.form_data['priority_skills']
        else:
            st.session_state.priority_skills_direct = []
            st.session_state.form_data['priority_skills'] = []
    
    priority_skills = st.multiselect(
        "Select up to 5 priority skills:",
        options=skill_options,
        default=st.session_state.priority_skills_direct,
        max_selections=5,
        key="priority_skills_multiselect"
    )
    # Update both direct session state and form_data
    st.session_state.priority_skills_direct = priority_skills
    st.session_state.form_data['priority_skills'] = priority_skills
    
    # Activity preferences
    st.markdown("#### 🎨 Activity Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Initialize activity types directly in session state if not present
        if 'activity_types_direct' not in st.session_state:
            if 'activity_types' in st.session_state.form_data:
                st.session_state.activity_types_direct = st.session_state.form_data['activity_types']
            else:
                st.session_state.activity_types_direct = []
                st.session_state.form_data['activity_types'] = []
        
        activity_types = st.multiselect(
            "Preferred activity types:",
            options=['Arts and crafts', 'Physical activities', 'Puzzles and games',
                    'Music and movement', 'Cooking activities', 'Outdoor activities',
                    'Reading and stories', 'Building and construction', 'Sensory play'],
            default=st.session_state.activity_types_direct,
            key="activity_types_multiselect"
        )
        # Update both direct session state and form_data
        st.session_state.activity_types_direct = activity_types
        st.session_state.form_data['activity_types'] = activity_types
        
        setting_preference = st.selectbox(
            "Preferred setting:",
            options=['Indoor activities', 'Outdoor activities', 'Both indoor and outdoor'],
            index=['Indoor activities', 'Outdoor activities', 'Both indoor and outdoor'].index(
                st.session_state.form_data.get('setting_preference', 'Both indoor and outdoor')
            )
        )
        st.session_state.form_data['setting_preference'] = setting_preference
    
    with col2:
        social_preference = st.selectbox(
            "Social preference:",
            options=['Individual activities', 'Group activities', 'Both individual and group'],
            index=['Individual activities', 'Group activities', 'Both individual and group'].index(
                st.session_state.form_data.get('social_preference', 'Both individual and group')
            )
        )
        st.session_state.form_data['social_preference'] = social_preference
        
        attention_span = st.slider(
            "Typical attention span (minutes):",
            min_value=5, max_value=60, 
            value=st.session_state.form_data.get('attention_span', 15),
            step=5
        )
        st.session_state.form_data['attention_span'] = attention_span
    
    # Energy level
    energy_level = st.select_slider(
        "Child's typical energy level:",
        options=['Very calm', 'Calm', 'Moderate', 'High energy', 'Very high energy'],
        value=st.session_state.form_data.get('energy_level', 'Moderate')
    )
    st.session_state.form_data['energy_level'] = energy_level

def show_step_4_sensory_physical():
    """Step 4: Sensory & Physical Considerations"""
    
    st.markdown("""
    <div class="form-section">
        <h3>👂 Sensory & Physical Considerations</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Sensory sensitivities
    st.markdown("#### 🌟 Sensory Sensitivities")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Sensory Seeking Behaviors:**")
        # Initialize sensory seeking directly in session state if not present
        if 'sensory_seeking_direct' not in st.session_state:
            if 'sensory_seeking' in st.session_state.form_data:
                st.session_state.sensory_seeking_direct = st.session_state.form_data['sensory_seeking']
            else:
                st.session_state.sensory_seeking_direct = []
                st.session_state.form_data['sensory_seeking'] = []
        
        sensory_seeking = st.multiselect(
            "Child seeks out these sensory inputs:",
            options=['Loud sounds', 'Bright lights', 'Rough textures', 'Strong tastes',
                    'Movement/spinning', 'Deep pressure', 'Vibration', 'Strong smells'],
            default=st.session_state.sensory_seeking_direct,
            key="sensory_seeking_multiselect"
        )
        # Update both direct session state and form_data
        st.session_state.sensory_seeking_direct = sensory_seeking
        st.session_state.form_data['sensory_seeking'] = sensory_seeking
    
    with col2:
        st.write("**Sensory Avoidance Behaviors:**")
        # Initialize sensory avoiding directly in session state if not present
        if 'sensory_avoiding_direct' not in st.session_state:
            if 'sensory_avoiding' in st.session_state.form_data:
                st.session_state.sensory_avoiding_direct = st.session_state.form_data['sensory_avoiding']
            else:
                st.session_state.sensory_avoiding_direct = []
                st.session_state.form_data['sensory_avoiding'] = []
        
        sensory_avoiding = st.multiselect(
            "Child avoids these sensory inputs:",
            options=['Loud sounds', 'Bright lights', 'Certain textures', 'Strong tastes',
                    'Unexpected touch', 'Crowded spaces', 'Strong smells', 'Messy activities'],
            default=st.session_state.sensory_avoiding_direct,
            key="sensory_avoiding_multiselect"
        )
        # Update both direct session state and form_data
        st.session_state.sensory_avoiding_direct = sensory_avoiding
        st.session_state.form_data['sensory_avoiding'] = sensory_avoiding
    
    # Physical considerations
    st.markdown("#### 🏃 Physical Considerations")
    
    physical_limitations = st.text_area(
        "Physical limitations or considerations:",
        value=st.session_state.form_data.get('physical_limitations', ''),
        help="Include any mobility issues, medical equipment, or physical restrictions",
        placeholder="Describe any physical limitations or considerations..."
    )
    st.session_state.form_data['physical_limitations'] = physical_limitations
    
    # Preferred sensory inputs
    # Initialize preferred sensory directly in session state if not present
    if 'preferred_sensory_direct' not in st.session_state:
        if 'preferred_sensory' in st.session_state.form_data:
            st.session_state.preferred_sensory_direct = st.session_state.form_data['preferred_sensory']
        else:
            st.session_state.preferred_sensory_direct = []
            st.session_state.form_data['preferred_sensory'] = []
    
    preferred_sensory = st.multiselect(
        "Preferred sensory inputs for calming/focus:",
        options=['Soft music', 'White noise', 'Dim lighting', 'Soft textures',
                'Weighted items', 'Fidget toys', 'Visual patterns', 'Aromatherapy'],
        default=st.session_state.preferred_sensory_direct,
        key="preferred_sensory_multiselect"
    )
    # Update both direct session state and form_data
    st.session_state.preferred_sensory_direct = preferred_sensory
    st.session_state.form_data['preferred_sensory'] = preferred_sensory
    
    # Environmental preferences
    st.markdown("#### 🏠 Environmental Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        noise_level = st.select_slider(
            "Preferred noise level:",
            options=['Very quiet', 'Quiet', 'Moderate', 'Active', 'Bustling'],
            value=st.session_state.form_data.get('noise_level', 'Moderate')
        )
        st.session_state.form_data['noise_level'] = noise_level
    
    with col2:
        lighting_preference = st.selectbox(
            "Lighting preference:",
            options=['Dim lighting', 'Natural lighting', 'Bright lighting', 'Varied lighting'],
            index=['Dim lighting', 'Natural lighting', 'Bright lighting', 'Varied lighting'].index(
                st.session_state.form_data.get('lighting_preference', 'Natural lighting')
            )
        )
        st.session_state.form_data['lighting_preference'] = lighting_preference

def show_step_5_motivation_interests():
    """Step 5: Motivation & Interests"""
    
    st.markdown("""
    <div class="form-section">
        <h3>🌟 Motivation & Interests</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # What motivates the child
    st.markdown("#### 🎉 What Motivates Your Child")
    
    motivators = st.text_area(
        "What excites or motivates your child? *",
        value=st.session_state.form_data.get('motivators', ''),
        help="Include favorite characters, themes, activities, or rewards",
        placeholder="e.g., dinosaurs, princesses, building blocks, praise, stickers..."
    )
    st.session_state.form_data['motivators'] = motivators
    
    # Interests and themes
    st.markdown("#### 🎨 Favorite Interests & Themes")
    
    col1, col2 = st.columns(2)
    
    with col1:
        favorite_activities = st.text_area(
            "Favorite activities/toys:",
            value=st.session_state.form_data.get('favorite_activities', ''),
            placeholder="List favorite toys, games, or activities..."
        )
        st.session_state.form_data['favorite_activities'] = favorite_activities
        
        # Initialize favorite themes directly in session state if not present
        if 'favorite_themes_direct' not in st.session_state:
            if 'favorite_themes' in st.session_state.form_data:
                st.session_state.favorite_themes_direct = st.session_state.form_data['favorite_themes']
            else:
                st.session_state.favorite_themes_direct = []
                st.session_state.form_data['favorite_themes'] = []
        
        favorite_themes = st.multiselect(
            "Favorite themes/interests:",
            options=['Animals', 'Vehicles', 'Superheroes', 'Princesses', 'Dinosaurs',
                    'Space', 'Nature', 'Sports', 'Music', 'Art', 'Science', 'Cooking'],
            default=st.session_state.favorite_themes_direct,
            key="favorite_themes_multiselect"
        )
        # Update both direct session state and form_data
        st.session_state.favorite_themes_direct = favorite_themes
        st.session_state.form_data['favorite_themes'] = favorite_themes
    
    with col2:
        # Initialize reward preferences directly in session state if not present
        if 'reward_preferences_direct' not in st.session_state:
            if 'reward_preferences' in st.session_state.form_data:
                st.session_state.reward_preferences_direct = st.session_state.form_data['reward_preferences']
            else:
                st.session_state.reward_preferences_direct = []
                st.session_state.form_data['reward_preferences'] = []
        
        reward_preferences = st.multiselect(
            "Effective rewards/motivators:",
            options=['Verbal praise', 'Stickers/stamps', 'Extra playtime', 'Special activities',
                    'Small toys', 'Screen time', 'Favorite snacks', 'One-on-one time'],
            default=st.session_state.reward_preferences_direct,
            key="reward_preferences_multiselect"
        )
        # Update both direct session state and form_data
        st.session_state.reward_preferences_direct = reward_preferences
        st.session_state.form_data['reward_preferences'] = reward_preferences
        
        learning_style = st.selectbox(
            "Preferred learning style:",
            options=['Visual (seeing)', 'Auditory (hearing)', 'Kinesthetic (doing/moving)', 'Mixed'],
            index=['Visual (seeing)', 'Auditory (hearing)', 'Kinesthetic (doing/moving)', 'Mixed'].index(
                st.session_state.form_data.get('learning_style', 'Mixed')
            )
        )
        st.session_state.form_data['learning_style'] = learning_style
    
    # Family goals
    st.markdown("#### 👨‍👩‍👧‍👦 Family Goals & Expectations")
    
    family_goals = st.text_area(
        "What are your main goals for your child? *",
        value=st.session_state.form_data.get('family_goals', ''),
        help="What would you like to see your child achieve or improve?",
        placeholder="e.g., better communication, more independence, improved social skills..."
    )
    st.session_state.form_data['family_goals'] = family_goals
    
    additional_info = st.text_area(
        "Any other important information:",
        value=st.session_state.form_data.get('additional_info', ''),
        placeholder="Anything else you'd like us to know about your child..."
    )
    st.session_state.form_data['additional_info'] = additional_info

def validate_current_step():
    """Validate the current step before proceeding"""
    
    step = st.session_state.questionnaire_step
    
    if step == 1:
        if not st.session_state.form_data.get('name', '').strip():
            st.error("Please enter your child's name.")
            return False
        if not st.session_state.form_data.get('age', ''):
            st.error("Please select your child's age.")
            return False
        if not st.session_state.form_data.get('family_structure', ''):
            st.error("Please select your family structure.")
            return False
    
    elif step == 2:
        if not st.session_state.form_data.get('selected_strengths', []) and \
           not st.session_state.form_data.get('additional_strengths', '').strip():
            st.error("Please select at least one strength or describe additional strengths.")
            return False
        if not st.session_state.form_data.get('selected_challenges', []) and \
           not st.session_state.form_data.get('additional_challenges', '').strip():
            st.error("Please select at least one challenge or describe additional challenges.")
            return False
    
    elif step == 3:
        if not st.session_state.form_data.get('priority_skills', []):
            st.error("Please select at least one priority skill to improve.")
            return False
    
    elif step == 5:
        if not st.session_state.form_data.get('motivators', '').strip():
            st.error("Please describe what motivates your child.")
            return False
        if not st.session_state.form_data.get('family_goals', '').strip():
            st.error("Please describe your main goals for your child.")
            return False
    
    return True

def save_profile_and_continue():
    """Save the completed profile and navigate to activities"""
    
    try:
        # Save or update profile
        if 'user_id' in st.session_state:
            success = update_user_profile(st.session_state.user_id, st.session_state.form_data)
        else:
            user_id = save_user_profile(st.session_state.form_data)
            success = user_id is not None
        
        if success:
            # Update session state
            st.session_state.user_profile = st.session_state.form_data
            st.session_state.profile_completed = True
            
            # Show success message
            st.success("✅ Profile completed successfully!")
            st.balloons()
            
            # Navigate to activities page
            st.info("🎯 Redirecting to activity recommendations...")
            navigate_to_page('activities')
            st.rerun()
        else:
            st.error("❌ Error saving profile. Please try again.")
    
    except Exception as e:
        st.error(f"❌ Error saving profile: {str(e)}")
