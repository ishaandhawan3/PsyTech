"""
Feed App for PsyTech Child Wellness Companion
Displays personalized parenting and child development feed
"""

import streamlit as st
import json
import time
from datetime import datetime
from pathlib import Path
import random
from utils.navigation import navigate_to_page, show_breadcrumb
from utils.json_database_adapter import save_feed_item, get_feed_items

def show_feed_app_page():
    """Display the feed app page"""
    
    # Show breadcrumb navigation
    show_breadcrumb()
    
    # Page header
    profile = st.session_state.get('user_profile', {})
    child_name = profile.get('name', 'Your Child')
    
    st.markdown(f"""
    <div class="main-header">
        <h1>🧠 Personalized Feed for {child_name}</h1>
        <p>Curated articles and resources based on your interests and profile</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Interest selection
    show_interest_selection()
    
    # Feed tabs
    tab1, tab2, tab3 = st.tabs(["🔥 For You", "🔍 Explore", "⭐ Favorites"])
    
    with tab1:
        show_personalized_feed()
    
    with tab2:
        show_explore_feed()
    
    with tab3:
        show_favorites()
    
    # Mark feed as viewed
    st.session_state.feed_viewed = True

def show_interest_selection():
    """Show interest selection interface"""
    
    st.markdown("### 🎯 Personalize Your Feed")
    
    # Get current interests from profile or session
    current_interests = st.session_state.get('feed_interests', [])
    profile = st.session_state.get('user_profile', {})
    
    # Extract interests from profile
    if not current_interests and profile:
        # Extract from various profile fields
        profile_interests = []
        
        # From challenges and diagnoses
        challenges = profile.get('selected_challenges', [])
        diagnoses = profile.get('selected_diagnoses', [])
        priority_skills = profile.get('priority_skills', [])
        
        # Map to feed categories
        interest_mapping = {
            'ADHD': ['ADHD', 'Behavioral Strategies'],
            'Autism Spectrum Disorder': ['Autism', 'Social Skills', 'Speech and Language'],
            'Anxiety Disorders': ['Anxiety', 'Emotional Regulation', 'Behavioral Strategies'],
            'Sensory Processing Disorder': ['Sensory Processing', 'Motor Skills'],
            'Fine motor skills': ['Motor Skills', 'Child Development'],
            'Gross motor skills': ['Motor Skills', 'Child Development'],
            'Communication skills': ['Speech and Language', 'Social Skills'],
            'Social skills': ['Social Skills', 'Child Development'],
            'Attention and focus': ['ADHD', 'Behavioral Strategies'],
            'Emotional regulation': ['Emotional Regulation', 'Behavioral Strategies']
        }
        
        for item in challenges + diagnoses + priority_skills:
            if item in interest_mapping:
                profile_interests.extend(interest_mapping[item])
        
        current_interests = list(set(profile_interests))
    
    # Interest categories
    available_interests = [
        "Parenting", "Autism", "ADHD", "Special Needs", "Child Development",
        "Sensory Processing", "Speech and Language", "Motor Skills",
        "Social Skills", "Emotional Regulation", "Behavioral Strategies",
        "Educational Support", "Family Activities", "Nutrition", "Sleep"
    ]
    
    # Initialize selected interests in session state if not present
    if 'feed_interests' not in st.session_state:
        st.session_state.feed_interests = current_interests
    
    # Multi-select for interests
    selected_interests = st.multiselect(
        "Select topics you're interested in:",
        options=available_interests,
        default=st.session_state.feed_interests,
        help="Choose topics to personalize your feed",
        key="feed_interests_multiselect"
    )
    
    # Update session state
    st.session_state.feed_interests = selected_interests
    
    if st.button("Update Feed", key="update_feed_interests"):
        # Save interests to user profile
        if 'user_id' in st.session_state:
            # This would update the user profile with new interests
            st.success("✅ Feed updated based on your interests!")
            st.rerun()
        else:
            st.warning("Please complete your profile first.")

def show_personalized_feed():
    """Show personalized feed based on user interests and profile"""
    
    st.markdown("### 🔥 Recommended for You")
    
    # Get user interests
    interests = st.session_state.get('feed_interests', [])
    profile = st.session_state.get('user_profile', {})
    
    if not interests:
        st.info("Select your interests above to see personalized recommendations!")
        return
    
    # Get feed items from storage
    if 'user_id' in st.session_state:
        feed_items = get_feed_items(st.session_state.user_id)
        
        if not feed_items:
            # Generate sample feed items if none exist
            feed_items = generate_sample_feed_items(interests, profile)
            
            # Save to storage
            for item in feed_items:
                save_feed_item(
                    st.session_state.user_id,
                    item['feed_type'],
                    item
                )
        
        # Display feed items
        for item in feed_items:
            display_feed_item(item)
    else:
        st.info("Complete your profile to see personalized feed items.")

def show_explore_feed():
    """Show explore feed with different categories"""
    
    st.markdown("### 🔍 Explore Topics")
    
    # Category selection
    categories = {
        "Parenting": [
            "Positive Parenting Techniques",
            "Setting Boundaries with Love",
            "Building Child Confidence",
            "Managing Challenging Behaviors",
            "Creating Supportive Routines"
        ],
        "ADHD": [
            "ADHD Management Strategies",
            "Focus Improvement Techniques",
            "ADHD and Executive Function",
            "Medication Management",
            "School Accommodations for ADHD"
        ],
        "Autism": [
            "Autism Support Techniques",
            "Sensory Processing Solutions",
            "Communication Strategies",
            "Social Skills Development",
            "Visual Supports and Schedules"
        ],
        "Child Development": [
            "Developmental Milestones",
            "Early Intervention",
            "Play-Based Learning",
            "Language Development",
            "Motor Skills Development"
        ],
        "Special Needs": [
            "IEP and 504 Plans",
            "Advocacy Skills",
            "Inclusive Education",
            "Therapy Options",
            "Community Resources"
        ]
    }
    
    selected_category = st.selectbox(
        "Choose a category to explore:",
        options=list(categories.keys())
    )
    
    if selected_category:
        st.markdown(f"#### Topics in {selected_category}")
        
        for topic in categories[selected_category]:
            # Generate a sample feed item for this topic
            feed_item = {
                "title": topic,
                "summary": f"Learn about {topic.lower()} with practical tips and expert insights.",
                "feed_type": "article",
                "source": "Explore Feed",
                "url": f"https://example.com/{topic.lower().replace(' ', '-')}",
                "categories": [selected_category],
                "created_at": datetime.now().isoformat()
            }
            
            display_feed_item(feed_item)

def show_favorites():
    """Show user's favorite feed items"""
    
    st.markdown("### ⭐ Your Favorites")
    
    if 'user_id' in st.session_state:
        # Get favorite feed items
        favorites = get_feed_items(st.session_state.user_id, feed_type="favorite")
        
        if favorites:
            for item in favorites:
                display_feed_item(item, is_favorite=True)
        else:
            st.info("No favorites yet. Star items you find helpful to save them here!")
    else:
        st.info("Complete your profile to save favorites.")

def generate_sample_feed_items(interests, profile):
    """Generate sample feed items based on user interests and profile"""
    
    feed_items = []
    
    # Sample feed items mapped to interests
    feed_templates = {
        "ADHD": [
            {
                "title": "10 Proven Strategies to Help Your ADHD Child Focus",
                "summary": "Evidence-based techniques to improve attention and reduce distractibility in children with ADHD.",
                "feed_type": "article",
                "source": "Understood.org",
                "url": "https://www.understood.org/articles/adhd-focus-strategies",
                "categories": ["ADHD", "Focus", "Attention", "Strategies"]
            },
            {
                "title": "Creating ADHD-Friendly Routines That Actually Work",
                "summary": "Step-by-step guide to building structured routines that support children with ADHD.",
                "feed_type": "article",
                "source": "ADDitude Magazine",
                "url": "https://www.additudemag.com/adhd-routines",
                "categories": ["ADHD", "Routines", "Structure", "Organization"]
            }
        ],
        "Autism": [
            {
                "title": "Understanding Sensory Needs in Autism",
                "summary": "A comprehensive guide to recognizing and supporting sensory processing differences in autistic children.",
                "feed_type": "article",
                "source": "Autism Speaks",
                "url": "https://www.autismspeaks.org/sensory-needs",
                "categories": ["Autism", "Sensory", "Processing", "Support"]
            },
            {
                "title": "Building Social Skills: A Parent's Guide",
                "summary": "Practical strategies to help autistic children develop meaningful social connections.",
                "feed_type": "article",
                "source": "Autism Parenting Magazine",
                "url": "https://www.autismparentingmagazine.com/social-skills",
                "categories": ["Autism", "Social Skills", "Communication", "Friendship"]
            }
        ],
        "Child Development": [
            {
                "title": "Developmental Milestones: What's Normal and When to Worry",
                "summary": "Understanding typical child development patterns and recognizing when to seek professional guidance.",
                "feed_type": "article",
                "source": "CDC",
                "url": "https://www.cdc.gov/developmental-milestones",
                "categories": ["Development", "Milestones", "Assessment", "Growth"]
            }
        ],
        "Sensory Processing": [
            {
                "title": "Sensory Diet Activities for Home",
                "summary": "Easy-to-implement sensory activities to help regulate your child's sensory system throughout the day.",
                "feed_type": "article",
                "source": "The OT Toolbox",
                "url": "https://www.theottoolbox.com/sensory-diet-activities",
                "categories": ["Sensory", "Activities", "Regulation", "Home"]
            }
        ],
        "Parenting": [
            {
                "title": "Positive Discipline Techniques That Build Connection",
                "summary": "Learn how to guide your child's behavior while strengthening your relationship.",
                "feed_type": "article",
                "source": "Positive Parenting Solutions",
                "url": "https://www.positiveparentingsolutions.com/discipline",
                "categories": ["Parenting", "Discipline", "Connection", "Behavior"]
            }
        ]
    }
    
    # Select feed items based on user interests
    for interest in interests:
        if interest in feed_templates:
            for item in feed_templates[interest]:
                # Add timestamp
                item["created_at"] = datetime.now().isoformat()
                feed_items.append(item)
    
    # If no specific matches, add general items
    if not feed_items:
        feed_items = [
            {
                "title": "Supporting Your Child's Unique Development Journey",
                "summary": "Every child develops at their own pace. Learn how to support and celebrate your child's individual growth.",
                "feed_type": "article",
                "source": "Child Development Institute",
                "url": "https://childdevelopmentinfo.com/development",
                "categories": ["Development", "Support", "Individual", "Growth"],
                "created_at": datetime.now().isoformat()
            }
        ]
    
    # Randomize order
    random.shuffle(feed_items)
    
    return feed_items

def display_feed_item(item, is_favorite=False):
    """Display an individual feed item"""
    
    with st.container():
        # Feed item header
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### [{item['title']}]({item['url']})")
            st.markdown(f"**{item['summary']}**")
        
        with col2:
            st.markdown(f"📰 {item['source']}")
            if 'created_at' in item:
                try:
                    created_date = datetime.fromisoformat(item['created_at']).strftime("%Y-%m-%d")
                    st.markdown(f"📅 {created_date}")
                except (ValueError, TypeError):
                    pass
        
        # Categories
        if 'categories' in item:
            categories = item['categories']
            if categories:
                tag_html = " ".join([f"<span style='background-color: #E3F2FD; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-right: 4px;'>{cat}</span>" for cat in categories])
                st.markdown(tag_html, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📖 Read", key=f"read_{item['title'][:20]}"):
                st.info(f"Opening: {item['title']}")
                # Would open article in new tab
        
        with col2:
            button_text = "⭐ Unstar" if is_favorite else "⭐ Star"
            if st.button(button_text, key=f"star_{item['title'][:20]}"):
                if 'user_id' in st.session_state:
                    if not is_favorite:
                        # Save as favorite
                        item['feed_type'] = "favorite"
                        save_feed_item(
                            st.session_state.user_id,
                            "favorite",
                            item
                        )
                        st.success("⭐ Added to favorites!")
                    else:
                        # Would remove from favorites
                        st.success("Removed from favorites!")
                else:
                    st.warning("Complete your profile to save favorites.")
        
        with col3:
            if st.button("📤 Share", key=f"share_{item['title'][:20]}"):
                st.info("Share functionality would be implemented here.")
        
        with col4:
            if st.button("💬 Discuss", key=f"discuss_{item['title'][:20]}"):
                st.info("Discussion forum would open here.")
        
        st.markdown("---")
