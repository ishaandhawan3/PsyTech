"""
Article Feed Page for PsyTech Child Wellness Companion
Displays personalized learning resources and articles
"""

import streamlit as st
import pandas as pd
import json
import re
from datetime import datetime, timedelta
from utils.navigation import navigate_to_page, show_breadcrumb
from utils.json_database_adapter import bookmark_article, get_bookmarked_articles

def show_article_feed_page():
    """Display the article feed page"""
    
    # Show breadcrumb navigation
    show_breadcrumb()
    
    # Page header
    profile = st.session_state.get('user_profile', {})
    child_name = profile.get('name', 'Your Child')
    
    st.markdown(f"""
    <div class="main-header">
        <h1>📚 Learning Resources for {child_name}</h1>
        <p>Curated articles and resources to support your child's development journey</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Interest selection and personalization
    show_interest_selection()
    
    # Article feed tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔥 For You", "📖 By Category", "🔖 Bookmarked", "🔍 Search"])
    
    with tab1:
        show_personalized_feed()
    
    with tab2:
        show_category_feed()
    
    with tab3:
        show_bookmarked_articles()
    
    with tab4:
        show_search_interface()
    
    # Mark articles as viewed
    st.session_state.articles_viewed = True

def show_interest_selection():
    """Show interest selection interface"""
    
    st.markdown("### 🎯 Personalize Your Feed")
    
    # Get current interests from profile or session
    current_interests = st.session_state.get('selected_interests', [])
    profile = st.session_state.get('user_profile', {})
    
    # Extract interests from profile
    if not current_interests and profile:
        # Extract from various profile fields
        profile_interests = []
        
        # From challenges and diagnoses
        challenges = profile.get('selected_challenges', [])
        diagnoses = profile.get('selected_diagnoses', [])
        priority_skills = profile.get('priority_skills', [])
        
        # Map to article categories
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
        "Child Development", "Parenting Tips", "ADHD", "Autism", "Anxiety",
        "Sensory Processing", "Speech and Language", "Motor Skills",
        "Social Skills", "Emotional Regulation", "Behavioral Strategies",
        "Educational Support", "Family Activities", "Nutrition", "Sleep",
        "Screen Time", "Sibling Relationships", "School Support",
        "Therapy Resources", "Special Needs", "Developmental Milestones"
    ]
    
    # Initialize selected interests in session state if not present
    if 'selected_interests' not in st.session_state:
        st.session_state.selected_interests = current_interests
    
    # Multi-select for interests
    selected_interests = st.multiselect(
        "Select topics you're interested in:",
        options=available_interests,
        default=st.session_state.selected_interests,
        help="Choose topics to personalize your article recommendations",
        key="selected_interests_multiselect"
    )
    
    # Update session state
    st.session_state.selected_interests = selected_interests
    
    if st.button("Update Feed", key="update_interests"):
        st.success("✅ Feed updated based on your interests!")
        st.rerun()

def show_personalized_feed():
    """Show personalized article feed based on user interests and profile"""
    
    st.markdown("### 🔥 Recommended for You")
    
    # Get user interests
    interests = st.session_state.get('selected_interests', [])
    profile = st.session_state.get('user_profile', {})
    
    if not interests:
        st.info("Select your interests above to see personalized recommendations!")
        return
    
    # Generate personalized articles
    personalized_articles = generate_personalized_articles(interests, profile)
    
    # Display articles
    for article in personalized_articles:
        display_article_card(article)

def show_category_feed():
    """Show articles organized by categories"""
    
    st.markdown("### 📖 Browse by Category")
    
    # Category selection
    categories = {
        "🧠 Development": [
            "Understanding Child Development Stages",
            "Cognitive Development in Early Years", 
            "Motor Skills Milestones",
            "Language Development Timeline",
            "Social-Emotional Growth"
        ],
        "🎯 Special Needs": [
            "ADHD Management Strategies",
            "Autism Support Techniques",
            "Sensory Processing Solutions",
            "Learning Disabilities Support",
            "Behavioral Interventions"
        ],
        "👨‍👩‍👧‍👦 Parenting": [
            "Positive Parenting Techniques",
            "Setting Boundaries with Love",
            "Building Child Confidence",
            "Managing Challenging Behaviors",
            "Creating Supportive Routines"
        ],
        "🏫 Education": [
            "School Readiness Skills",
            "Homework Help Strategies",
            "IEP and 504 Plan Guide",
            "Teacher Communication Tips",
            "Learning at Home Activities"
        ],
        "🏥 Health & Wellness": [
            "Child Nutrition Basics",
            "Sleep Strategies for Kids",
            "Physical Activity Ideas",
            "Mental Health Awareness",
            "Managing Medical Needs"
        ]
    }
    
    selected_category = st.selectbox(
        "Choose a category:",
        options=list(categories.keys())
    )
    
    if selected_category:
        st.markdown(f"#### Articles in {selected_category}")
        
        category_articles = generate_category_articles(categories[selected_category])
        
        for article in category_articles:
            display_article_card(article)

def show_bookmarked_articles():
    """Show user's bookmarked articles"""
    
    st.markdown("### 🔖 Your Bookmarked Articles")
    
    if 'user_id' in st.session_state:
        bookmarked = get_bookmarked_articles(st.session_state.user_id)
        
        if bookmarked:
            for article in bookmarked:
                display_bookmarked_article(article)
        else:
            st.info("No bookmarked articles yet. Bookmark articles you find helpful!")
    else:
        st.info("Complete your profile to save bookmarked articles.")

def show_search_interface():
    """Show article search interface"""
    
    st.markdown("### 🔍 Search Articles")
    
    # Search input
    search_query = st.text_input(
        "Search for articles:",
        placeholder="e.g., ADHD strategies, sensory activities, communication tips..."
    )
    
    # Search filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        content_type = st.selectbox(
            "Content Type:",
            options=["All", "Articles", "Guides", "Tips", "Research"]
        )
    
    with col2:
        reading_time = st.selectbox(
            "Reading Time:",
            options=["Any", "Quick (2-5 min)", "Medium (5-10 min)", "Long (10+ min)"]
        )
    
    with col3:
        recency = st.selectbox(
            "Recency:",
            options=["Any time", "Last week", "Last month", "Last 3 months"]
        )
    
    if st.button("Search", key="search_articles"):
        if search_query:
            # Perform search
            search_results = perform_article_search(search_query, content_type, reading_time, recency)
            
            st.markdown(f"#### Search Results for '{search_query}'")
            
            if search_results:
                for article in search_results:
                    display_article_card(article)
            else:
                st.info("No articles found matching your search criteria.")
        else:
            st.warning("Please enter a search query.")

def generate_personalized_articles(interests, profile):
    """Generate personalized articles based on user interests and profile"""
    
    # This would ideally connect to a real article database or API
    # For now, we'll generate sample articles based on interests
    
    articles = []
    
    # Sample articles mapped to interests
    article_templates = {
        "ADHD": [
            {
                "title": "10 Proven Strategies to Help Your ADHD Child Focus",
                "summary": "Evidence-based techniques to improve attention and reduce distractibility in children with ADHD.",
                "category": "ADHD",
                "reading_time": "7 min",
                "author": "Dr. Sarah Johnson",
                "tags": ["ADHD", "Focus", "Attention", "Strategies"],
                "url": "https://example.com/adhd-focus-strategies"
            },
            {
                "title": "Creating ADHD-Friendly Routines That Actually Work",
                "summary": "Step-by-step guide to building structured routines that support children with ADHD.",
                "category": "ADHD",
                "reading_time": "5 min",
                "author": "Lisa Martinez, OTR/L",
                "tags": ["ADHD", "Routines", "Structure", "Organization"],
                "url": "https://example.com/adhd-routines"
            }
        ],
        "Autism": [
            {
                "title": "Understanding Sensory Needs in Autism",
                "summary": "A comprehensive guide to recognizing and supporting sensory processing differences in autistic children.",
                "category": "Autism",
                "reading_time": "8 min",
                "author": "Dr. Michael Chen",
                "tags": ["Autism", "Sensory", "Processing", "Support"],
                "url": "https://example.com/autism-sensory-needs"
            },
            {
                "title": "Building Social Skills: A Parent's Guide",
                "summary": "Practical strategies to help autistic children develop meaningful social connections.",
                "category": "Autism",
                "reading_time": "6 min",
                "author": "Jennifer Adams, BCBA",
                "tags": ["Autism", "Social Skills", "Communication", "Friendship"],
                "url": "https://example.com/autism-social-skills"
            }
        ],
        "Child Development": [
            {
                "title": "Developmental Milestones: What's Normal and When to Worry",
                "summary": "Understanding typical child development patterns and recognizing when to seek professional guidance.",
                "category": "Development",
                "reading_time": "10 min",
                "author": "Dr. Emily Rodriguez",
                "tags": ["Development", "Milestones", "Assessment", "Growth"],
                "url": "https://example.com/developmental-milestones"
            }
        ],
        "Sensory Processing": [
            {
                "title": "Sensory Diet Activities for Home",
                "summary": "Easy-to-implement sensory activities to help regulate your child's sensory system throughout the day.",
                "category": "Sensory",
                "reading_time": "6 min",
                "author": "Amanda Thompson, OTR/L",
                "tags": ["Sensory", "Activities", "Regulation", "Home"],
                "url": "https://example.com/sensory-diet-activities"
            }
        ],
        "Parenting Tips": [
            {
                "title": "Positive Discipline Techniques That Build Connection",
                "summary": "Learn how to guide your child's behavior while strengthening your relationship.",
                "category": "Parenting",
                "reading_time": "8 min",
                "author": "Dr. Rachel Green",
                "tags": ["Parenting", "Discipline", "Connection", "Behavior"],
                "url": "https://example.com/positive-discipline"
            }
        ]
    }
    
    # Select articles based on user interests
    for interest in interests:
        if interest in article_templates:
            articles.extend(article_templates[interest])
    
    # If no specific matches, add general articles
    if not articles:
        articles = [
            {
                "title": "Supporting Your Child's Unique Development Journey",
                "summary": "Every child develops at their own pace. Learn how to support and celebrate your child's individual growth.",
                "category": "General",
                "reading_time": "5 min",
                "author": "Dr. Maria Santos",
                "tags": ["Development", "Support", "Individual", "Growth"],
                "url": "https://example.com/unique-development"
            }
        ]
    
    # Add metadata
    for article in articles:
        article['published_date'] = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
        article['relevance_score'] = calculate_relevance_score(article, interests, profile)
    
    # Sort by relevance
    articles.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    return articles[:10]  # Return top 10

def generate_category_articles(category_topics):
    """Generate articles for a specific category"""
    
    articles = []
    
    for i, topic in enumerate(category_topics):
        article = {
            "title": topic,
            "summary": f"Comprehensive guide covering {topic.lower()} with practical tips and expert insights.",
            "category": "Category Article",
            "reading_time": f"{random.randint(4, 12)} min",
            "author": f"Expert Author {i+1}",
            "tags": topic.split(),
            "url": f"https://example.com/{topic.lower().replace(' ', '-')}",
            "published_date": (datetime.now() - timedelta(days=random.randint(1, 60))).strftime("%Y-%m-%d"),
            "relevance_score": 0.8
        }
        articles.append(article)
    
    return articles

def perform_article_search(query, content_type, reading_time, recency):
    """Perform article search based on query and filters"""
    
    # This would connect to a real search engine
    # For now, return sample results
    
    search_results = [
        {
            "title": f"Search Result: {query} - Comprehensive Guide",
            "summary": f"Detailed information about {query} with practical applications and expert recommendations.",
            "category": "Search Result",
            "reading_time": "6 min",
            "author": "Search Expert",
            "tags": query.split(),
            "url": f"https://example.com/search/{query.replace(' ', '-')}",
            "published_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
            "relevance_score": 0.9
        },
        {
            "title": f"Advanced {query} Strategies",
            "summary": f"Advanced techniques and strategies for {query} based on latest research and clinical practice.",
            "category": "Advanced Guide",
            "reading_time": "9 min",
            "author": "Clinical Specialist",
            "tags": query.split() + ["advanced", "strategies"],
            "url": f"https://example.com/advanced/{query.replace(' ', '-')}",
            "published_date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
            "relevance_score": 0.85
        }
    ]
    
    return search_results

def calculate_relevance_score(article, interests, profile):
    """Calculate relevance score for an article"""
    
    score = 0.5  # Base score
    
    # Interest match
    for interest in interests:
        if interest.lower() in article['title'].lower() or interest.lower() in ' '.join(article['tags']).lower():
            score += 0.3
    
    # Profile match
    if profile:
        challenges = profile.get('selected_challenges', [])
        diagnoses = profile.get('selected_diagnoses', [])
        
        for item in challenges + diagnoses:
            if item.lower() in article['title'].lower() or item.lower() in article['summary'].lower():
                score += 0.2
    
    return min(score, 1.0)  # Cap at 1.0

def display_article_card(article):
    """Display an individual article card"""
    
    with st.container():
        # Article header
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### [{article['title']}]({article['url']})")
            st.markdown(f"**{article['summary']}**")
        
        with col2:
            st.markdown(f"📖 {article['reading_time']}")
            st.markdown(f"👤 {article['author']}")
            st.markdown(f"📅 {article['published_date']}")
        
        # Tags
        if article.get('tags'):
            tag_html = " ".join([f"<span style='background-color: #E3F2FD; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-right: 4px;'>{tag}</span>" for tag in article['tags']])
            st.markdown(tag_html, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📖 Read Article", key=f"read_{article['title'][:20]}"):
                st.info(f"Opening: {article['title']}")
                # Would open article in new tab
        
        with col2:
            if st.button("🔖 Bookmark", key=f"bookmark_{article['title'][:20]}"):
                if 'user_id' in st.session_state:
                    bookmark_article(
                        st.session_state.user_id,
                        article['title'],
                        article['url'],
                        article['summary']
                    )
                    st.success("✅ Bookmarked!")
                else:
                    st.warning("Complete your profile to bookmark articles.")
        
        with col3:
            if st.button("📤 Share", key=f"share_{article['title'][:20]}"):
                st.info("Share functionality would be implemented here.")
        
        with col4:
            if st.button("💬 Discuss", key=f"discuss_{article['title'][:20]}"):
                st.info("Discussion forum would open here.")
        
        st.markdown("---")

def display_bookmarked_article(article):
    """Display a bookmarked article"""
    
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### [{article['title']}]({article['url']})")
            if article['summary']:
                st.markdown(f"**{article['summary']}**")
        
        with col2:
            st.markdown(f"🔖 Bookmarked: {article['bookmarked_at'][:10]}")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📖 Read", key=f"read_bookmarked_{article['title'][:20]}"):
                st.info(f"Opening: {article['title']}")
        
        with col2:
            if st.button("🗑️ Remove", key=f"remove_{article['title'][:20]}"):
                # Would remove from bookmarks
                st.success("Removed from bookmarks!")
        
        with col3:
            if st.button("📤 Share", key=f"share_bookmarked_{article['title'][:20]}"):
                st.info("Share functionality would be implemented here.")
        
        st.markdown("---")

# Import random for demo purposes
import random
