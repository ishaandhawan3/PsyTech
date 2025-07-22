"""
Activity Recommendations Page for PsyTech Child Wellness Companion
Displays personalized activity cards with interactive feedback options
"""

import streamlit as st
import pandas as pd
import re
import json
import random
from pathlib import Path
from utils.navigation import navigate_to_page, show_breadcrumb
from utils.styling import create_activity_card_html
from utils.json_database_adapter import save_activity_feedback, get_user_profile

def show_activity_recommendations_page():
    """Display the activity recommendations page"""
    
    # Check if profile is completed
    if not st.session_state.get('profile_completed', False):
        st.warning("⚠️ Please complete your child's profile first to get personalized recommendations.")
        if st.button("Go to Profile"):
            navigate_to_page('questionnaire')
            st.rerun()
        return
    
    # Show breadcrumb navigation
    show_breadcrumb()
    
    # Page header
    profile = st.session_state.get('user_profile', {})
    child_name = profile.get('name', 'Your Child')
    
    st.markdown(f"""
    <div class="main-header">
        <h1>🎯 Activity Recommendations for {child_name}</h1>
        <p>Personalized activities based on your child's profile and goals</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load activities data
    activities_df = load_activities_data()
    
    if activities_df is None or activities_df.empty:
        st.error("❌ Unable to load activities data. Please check the data file.")
        return
    
    # Generate recommendations
    if 'recommended_activities' not in st.session_state:
        st.session_state.recommended_activities = generate_activity_recommendations(profile, activities_df)
    
    # Display filter options
    show_activity_filters()
    
    # Display activity cards
    display_activity_cards(st.session_state.recommended_activities)
    
    # Mark activities as viewed
    st.session_state.activities_viewed = True
    
    # Navigation to next step
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🎯 Try Activities & Give Feedback", key="go_to_feedback", use_container_width=True):
            navigate_to_page('feedback')
            st.rerun()
    
    with col3:
        if st.button("🔄 Get New Recommendations", key="refresh_recommendations"):
            st.session_state.recommended_activities = generate_activity_recommendations(profile, activities_df, refresh=True)
            st.rerun()

def load_activities_data():
    """Load activities data from CSV file"""
    try:
        data_path = Path(__file__).parent.parent / "data" / "activities.csv"
        
        # Try different encodings
        for encoding in ['utf-8', 'latin1', 'cp1252']:
            try:
                df = pd.read_csv(data_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            st.error("Unable to read activities file with any encoding")
            return None
        
        # Clean the dataframe
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        df = df[df["Activity Name"].astype(str).str.strip() != ""]
        df = df.drop_duplicates(subset=["Activity Name"]).reset_index(drop=True)
        
        # Ensure numeric age columns where possible
        for col in ["Age Min", "Age Max"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        return df
        
    except Exception as e:
        st.error(f"Error loading activities data: {e}")
        return None

def generate_activity_recommendations(profile, activities_df, refresh=False):
    """Generate personalized activity recommendations"""
    
    if not refresh and 'cached_recommendations' in st.session_state:
        return st.session_state.cached_recommendations
    
    recommendations = []
    
    # Extract profile information
    child_age = extract_age_from_profile(profile)
    priority_skills = profile.get('priority_skills', [])
    selected_challenges = profile.get('selected_challenges', [])
    selected_diagnoses = profile.get('selected_diagnoses', [])
    activity_types = profile.get('activity_types', [])
    attention_span = profile.get('attention_span', 15)
    energy_level = profile.get('energy_level', 'Moderate')
    
    # Score and rank activities
    scored_activities = []
    
    for _, row in activities_df.iterrows():
        activity_data = extract_activity_data(row)
        score = calculate_activity_score(activity_data, profile, child_age)
        
        if score > 0:
            activity_data['score'] = score
            scored_activities.append(activity_data)
    
    # Sort by score and select top activities
    scored_activities.sort(key=lambda x: x['score'], reverse=True)
    
    # Select diverse set of activities
    selected_activities = select_diverse_activities(scored_activities, 6)
    
    # Cache recommendations
    st.session_state.cached_recommendations = selected_activities
    
    return selected_activities

def extract_age_from_profile(profile):
    """Extract numeric age from profile"""
    age_str = profile.get('age', '')
    try:
        # Extract number from "X years old" format
        age_match = re.search(r'(\d+)', age_str)
        if age_match:
            return int(age_match.group(1))
    except:
        pass
    return None

def extract_activity_data(row):
    """Extract structured data from activity row"""
    
    def clean_text(text):
        if pd.isna(text) or str(text).strip().lower() in {"", "nan", "none", "—"}:
            return ""
        return str(text).strip()
    
    # Determine difficulty level
    difficulty = "Beginner"
    if "Advanced" in str(row.get("Activity Name", "")):
        difficulty = "Advanced"
    elif "Intermediate" in str(row.get("Activity Name", "")):
        difficulty = "Intermediate"
    
    # Estimate duration based on activity type
    duration = estimate_activity_duration(row)
    
    # Extract skills/focus areas
    focus_areas = clean_text(row.get("Focus Area(s)", ""))
    skills = [skill.strip() for skill in focus_areas.split(",") if skill.strip()]
    
    return {
        'name': clean_text(row.get("Activity Name")),
        'description': generate_activity_description(row),
        'focus_areas': focus_areas,
        'skills': skills,
        'conditions': clean_text(row.get("Conditions", "")),
        'keywords': clean_text(row.get("Other Keywords", "")),
        'difficulty': difficulty,
        'duration': duration,
        'materials': extract_materials_needed(row),
        'instructions': generate_instructions(row),
        'age_min': row.get("Age Min") if pd.notna(row.get("Age Min")) else None,
        'age_max': row.get("Age Max") if pd.notna(row.get("Age Max")) else None,
        'delivery': clean_text(row.get("Delivery", "")),
        'parent_description': clean_text(row.get("Parent Description", ""))
    }

def calculate_activity_score(activity_data, profile, child_age):
    """Calculate relevance score for an activity"""
    
    score = 0
    
    # Age appropriateness (high weight)
    if child_age and activity_data['age_min'] and activity_data['age_max']:
        if activity_data['age_min'] <= child_age <= activity_data['age_max']:
            score += 10
        elif abs(child_age - activity_data['age_min']) <= 2 or abs(child_age - activity_data['age_max']) <= 2:
            score += 5
    
    # Priority skills match (high weight)
    priority_skills = profile.get('priority_skills', [])
    for skill in priority_skills:
        if skill.lower() in activity_data['focus_areas'].lower():
            score += 8
    
    # Challenge areas match (medium weight)
    challenges = profile.get('selected_challenges', [])
    for challenge in challenges:
        if challenge.lower() in activity_data['focus_areas'].lower() or \
           challenge.lower() in activity_data['keywords'].lower():
            score += 6
    
    # Diagnosis relevance (medium weight)
    diagnoses = profile.get('selected_diagnoses', [])
    for diagnosis in diagnoses:
        if diagnosis.lower() in activity_data['conditions'].lower():
            score += 6
    
    # Activity type preference (low weight)
    activity_types = profile.get('activity_types', [])
    for activity_type in activity_types:
        if activity_type.lower() in activity_data['name'].lower() or \
           activity_type.lower() in activity_data['keywords'].lower():
            score += 3
    
    # Attention span compatibility (medium weight)
    attention_span = profile.get('attention_span', 15)
    estimated_duration = parse_duration(activity_data['duration'])
    if estimated_duration:
        if estimated_duration <= attention_span:
            score += 5
        elif estimated_duration <= attention_span + 10:
            score += 2
    
    # Energy level match (low weight)
    energy_level = profile.get('energy_level', 'Moderate')
    if 'physical' in activity_data['focus_areas'].lower() or 'gross motor' in activity_data['focus_areas'].lower():
        if energy_level in ['High energy', 'Very high energy']:
            score += 3
    elif 'fine motor' in activity_data['focus_areas'].lower() or 'cognitive' in activity_data['focus_areas'].lower():
        if energy_level in ['Calm', 'Very calm', 'Moderate']:
            score += 3
    
    return score

def select_diverse_activities(scored_activities, count=6):
    """Select diverse set of activities to avoid repetition"""
    
    selected = []
    used_focus_areas = set()
    
    # First pass: select highest scoring activities with different focus areas
    for activity in scored_activities:
        if len(selected) >= count:
            break
        
        focus_area_key = activity['focus_areas'].lower()
        if focus_area_key not in used_focus_areas:
            selected.append(activity)
            used_focus_areas.add(focus_area_key)
    
    # Second pass: fill remaining slots with highest scoring activities
    for activity in scored_activities:
        if len(selected) >= count:
            break
        
        if activity not in selected:
            selected.append(activity)
    
    return selected[:count]

def estimate_activity_duration(row):
    """Estimate activity duration based on type and complexity"""
    
    activity_name = str(row.get("Activity Name", "")).lower()
    
    # Quick activities (5-10 minutes)
    if any(word in activity_name for word in ['bubble', 'sticker', 'simple', 'quick']):
        return "5-10 min"
    
    # Medium activities (15-30 minutes)
    elif any(word in activity_name for word in ['puzzle', 'drawing', 'sorting', 'matching']):
        return "15-30 min"
    
    # Longer activities (30+ minutes)
    elif any(word in activity_name for word in ['cooking', 'gardening', 'building', 'story']):
        return "30-45 min"
    
    # Default
    return "15-20 min"

def parse_duration(duration_str):
    """Parse duration string to minutes"""
    try:
        # Extract first number from duration string
        match = re.search(r'(\d+)', duration_str)
        if match:
            return int(match.group(1))
    except:
        pass
    return None

def generate_activity_description(row):
    """Generate engaging activity description"""
    
    activity_name = str(row.get("Activity Name", ""))
    focus_areas = str(row.get("Focus Area(s)", ""))
    parent_desc = str(row.get("Parent Description", ""))
    
    # Use parent description if available
    if parent_desc and parent_desc.lower() not in ["", "nan", "none"]:
        return parent_desc
    
    # Generate description based on activity name and focus areas
    descriptions = {
        'story': "Engage your child's imagination and language skills through creative storytelling and narrative building.",
        'painting': "Explore creativity and sensory experiences through colorful painting activities that develop fine motor skills.",
        'sorting': "Build cognitive skills and attention to detail through fun sorting and categorization games.",
        'puzzle': "Challenge problem-solving abilities and visual perception with age-appropriate puzzles.",
        'cooking': "Develop life skills and following instructions through safe, no-fire cooking activities.",
        'gardening': "Connect with nature while building responsibility and observational skills through plant care.",
        'building': "Enhance spatial reasoning and creativity through construction and building activities.",
        'sensory': "Provide calming or stimulating sensory experiences tailored to your child's needs."
    }
    
    # Find matching description
    for key, desc in descriptions.items():
        if key in activity_name.lower():
            return desc
    
    # Default description
    return f"A {focus_areas.lower()} activity designed to support your child's development in a fun and engaging way."

def extract_materials_needed(row):
    """Extract or estimate materials needed for activity"""
    
    activity_name = str(row.get("Activity Name", "")).lower()
    
    materials_map = {
        'painting': ['Paint', 'Brushes', 'Paper', 'Water cup', 'Apron'],
        'story': ['Paper', 'Pencils/crayons', 'Imagination'],
        'sorting': ['Various small objects', 'Containers/bowls'],
        'puzzle': ['Age-appropriate puzzle'],
        'cooking': ['Ingredients (see recipe)', 'Mixing bowls', 'Measuring cups'],
        'gardening': ['Seeds/small plants', 'Soil', 'Small pots', 'Watering can'],
        'building': ['Building blocks/Legos', 'Flat surface'],
        'sensory': ['Sensory materials (playdough, rice, etc.)']
    }
    
    for key, materials in materials_map.items():
        if key in activity_name:
            return materials
    
    return ['Basic household items', 'Adult supervision']

def generate_instructions(row):
    """Generate basic instructions for the activity"""
    
    activity_name = str(row.get("Activity Name", ""))
    
    # This would ideally come from a more detailed database
    # For now, provide general guidance
    return [
        "Set up a comfortable workspace",
        "Gather all materials before starting",
        "Explain the activity to your child",
        "Provide support as needed",
        "Celebrate efforts and progress",
        "Clean up together when finished"
    ]

def show_activity_filters():
    """Display activity filtering options"""
    
    st.markdown("### 🔍 Filter Activities")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        duration_filter = st.selectbox(
            "Duration",
            options=["All", "Quick (5-15 min)", "Medium (15-30 min)", "Long (30+ min)"],
            key="duration_filter"
        )
    
    with col2:
        difficulty_filter = st.selectbox(
            "Difficulty",
            options=["All", "Beginner", "Intermediate", "Advanced"],
            key="difficulty_filter"
        )
    
    with col3:
        skill_filter = st.selectbox(
            "Focus Area",
            options=["All", "Fine Motor", "Gross Motor", "Cognitive", "Social", "Sensory"],
            key="skill_filter"
        )
    
    with col4:
        if st.button("Apply Filters", key="apply_filters"):
            # Apply filters to recommendations
            filtered_activities = apply_activity_filters(
                st.session_state.recommended_activities,
                duration_filter, difficulty_filter, skill_filter
            )
            st.session_state.filtered_activities = filtered_activities
            st.rerun()

def apply_activity_filters(activities, duration_filter, difficulty_filter, skill_filter):
    """Apply filters to activity list"""
    
    filtered = activities.copy()
    
    # Duration filter
    if duration_filter != "All":
        if "Quick" in duration_filter:
            filtered = [a for a in filtered if parse_duration(a['duration']) and parse_duration(a['duration']) <= 15]
        elif "Medium" in duration_filter:
            filtered = [a for a in filtered if parse_duration(a['duration']) and 15 < parse_duration(a['duration']) <= 30]
        elif "Long" in duration_filter:
            filtered = [a for a in filtered if parse_duration(a['duration']) and parse_duration(a['duration']) > 30]
    
    # Difficulty filter
    if difficulty_filter != "All":
        filtered = [a for a in filtered if a['difficulty'] == difficulty_filter]
    
    # Skill filter
    if skill_filter != "All":
        filtered = [a for a in filtered if skill_filter.lower() in a['focus_areas'].lower()]
    
    return filtered

def display_activity_cards(activities):
    """Display activity cards with interactive elements"""
    
    # Use filtered activities if available
    display_activities = st.session_state.get('filtered_activities', activities)
    
    if not display_activities:
        st.info("No activities match your current filters. Try adjusting the filter settings.")
        return
    
    st.markdown("### 🎯 Recommended Activities")
    
    for i, activity in enumerate(display_activities):
        display_single_activity_card(activity, i)

def display_single_activity_card(activity, card_index):
    """Display a single activity card with all interactive elements"""
    
    # Create unique key for this card
    card_key = f"card_{card_index}_{activity['name'].replace(' ', '_')}"
    
    # Card container
    with st.container():
        # Activity header with badges
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### {activity['name']}")
            st.markdown(f"**Description:** {activity['description']}")
        
        with col2:
            # Difficulty badge
            difficulty_color = {
                'Beginner': '🟢',
                'Intermediate': '🟡', 
                'Advanced': '🔴'
            }
            st.markdown(f"{difficulty_color.get(activity['difficulty'], '⚪')} **{activity['difficulty']}**")
            st.markdown(f"⏱️ **{activity['duration']}**")
        
        # Skills and focus areas
        if activity['skills']:
            st.markdown("**Skills Developed:**")
            skill_badges = " ".join([f"`{skill}`" for skill in activity['skills']])
            st.markdown(skill_badges)
        
        # Materials needed (expandable)
        with st.expander("📋 Materials Needed"):
            for material in activity['materials']:
                st.markdown(f"• {material}")
        
        # Instructions (expandable)
        with st.expander("📝 Step-by-Step Instructions"):
            for i, instruction in enumerate(activity['instructions'], 1):
                st.markdown(f"{i}. {instruction}")
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🎯 Try This Activity", key=f"try_{card_key}"):
                handle_try_activity(activity, card_index)
        
        with col2:
            if st.button("💾 Save for Later", key=f"save_{card_key}"):
                handle_save_activity(activity, card_index)
        
        with col3:
            if st.button("👎 Skip This", key=f"skip_{card_key}"):
                handle_skip_activity(activity, card_index)
        
        with col4:
            if st.button("🔄 Similar Activities", key=f"similar_{card_key}"):
                handle_similar_activities(activity, card_index)
        
        # Quick feedback section
        show_quick_feedback_section(activity, card_index)
        
        st.markdown("---")

def show_quick_feedback_section(activity, card_index):
    """Show quick feedback options for the activity"""
    
    card_key = f"feedback_{card_index}_{activity['name'].replace(' ', '_')}"
    
    with st.expander("💭 Quick Feedback"):
        col1, col2 = st.columns(2)
        
        with col1:
            interest_level = st.select_slider(
                "How interested is your child likely to be?",
                options=["😴 Not interested", "😐 Neutral", "😊 Interested", "😍 Very excited"],
                key=f"interest_{card_key}"
            )
            
            difficulty_perception = st.select_slider(
                "How difficult does this look?",
                options=["Too easy", "Just right", "Challenging", "Too hard"],
                key=f"difficulty_{card_key}"
            )
        
        with col2:
            material_availability = st.radio(
                "Do you have the materials?",
                options=["Have everything", "Have most", "Need to buy some", "Don't have materials"],
                key=f"materials_{card_key}"
            )
            
            time_availability = st.selectbox(
                "How much time do you have?",
                options=["5-10 minutes", "15-30 minutes", "30+ minutes", "Not sure"],
                key=f"time_{card_key}"
            )
        
        if st.button("Submit Quick Feedback", key=f"submit_feedback_{card_key}"):
            feedback_data = {
                'interest_level': interest_level,
                'difficulty_perception': difficulty_perception,
                'material_availability': material_availability,
                'time_availability': time_availability
            }
            
            # Save feedback to database
            if 'user_id' in st.session_state:
                save_activity_feedback(
                    st.session_state.user_id,
                    activity['name'],
                    'quick_feedback',
                    feedback_data
                )
            
            st.success("✅ Feedback saved! This helps us improve recommendations.")

def handle_try_activity(activity, card_index):
    """Handle when user clicks 'Try This Activity'"""
    
    # Store selected activity in session state
    st.session_state.selected_activity = activity
    st.session_state.activity_start_time = pd.Timestamp.now()
    
    # Show pre-activity modal
    st.success(f"🎯 Great choice! You've selected: **{activity['name']}**")
    st.info("💡 **Tip:** Take note of how your child responds during the activity. You'll be able to provide feedback afterward.")
    
    # Save activity selection
    if 'user_id' in st.session_state:
        save_activity_feedback(
            st.session_state.user_id,
            activity['name'],
            'activity_selected',
            {'selected_at': str(pd.Timestamp.now())}
        )

def handle_save_activity(activity, card_index):
    """Handle when user clicks 'Save for Later'"""
    
    # Add to saved activities
    if 'saved_activities' not in st.session_state:
        st.session_state.saved_activities = []
    
    if activity not in st.session_state.saved_activities:
        st.session_state.saved_activities.append(activity)
        st.success(f"💾 Saved **{activity['name']}** for later!")
        
        # Save to database
        if 'user_id' in st.session_state:
            save_activity_feedback(
                st.session_state.user_id,
                activity['name'],
                'activity_saved',
                {'saved_at': str(pd.Timestamp.now())}
            )
    else:
        st.info("This activity is already saved!")

def handle_skip_activity(activity, card_index):
    """Handle when user clicks 'Skip This'"""
    
    # Show skip reason modal
    skip_reasons = [
        "Not interested in this type of activity",
        "Too difficult for current level", 
        "Too easy for current level",
        "Don't have required materials",
        "Not enough time right now",
        "Child has done this recently",
        "Other"
    ]
    
    with st.form(f"skip_form_{card_index}"):
        st.markdown(f"**Why are you skipping '{activity['name']}'?**")
        skip_reason = st.selectbox("Select reason:", skip_reasons)
        
        if skip_reason == "Other":
            other_reason = st.text_input("Please specify:")
        else:
            other_reason = ""
        
        if st.form_submit_button("Submit"):
            # Save skip feedback
            feedback_data = {
                'skip_reason': skip_reason,
                'other_reason': other_reason,
                'skipped_at': str(pd.Timestamp.now())
            }
            
            if 'user_id' in st.session_state:
                save_activity_feedback(
                    st.session_state.user_id,
                    activity['name'],
                    'activity_skipped',
                    feedback_data
                )
            
            st.success("✅ Thanks for the feedback! We'll use this to improve future recommendations.")

def handle_similar_activities(activity, card_index):
    """Handle when user requests similar activities"""
    
    st.info(f"🔄 Finding activities similar to **{activity['name']}**...")
    
    # This would ideally trigger a new recommendation based on the current activity
    # For now, show a message
    st.markdown("**Similar activities will be shown in future recommendations based on:**")
    st.markdown(f"• Same focus areas: {activity['focus_areas']}")
    st.markdown(f"• Similar difficulty: {activity['difficulty']}")
    st.markdown(f"• Comparable duration: {activity['duration']}")
    
    # Save preference
    if 'user_id' in st.session_state:
        save_activity_feedback(
            st.session_state.user_id,
            activity['name'],
            'similar_requested',
            {'requested_at': str(pd.Timestamp.now())}
        )
