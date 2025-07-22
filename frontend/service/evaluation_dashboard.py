"""
Evaluation Dashboard Page for PsyTech Child Wellness Companion
Displays progress metrics, insights, and analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.navigation import navigate_to_page, show_breadcrumb
from utils.styling import create_dashboard_metric_html
from utils.json_database_adapter import get_user_statistics, get_user_progress, get_user_activity_history

def show_evaluation_dashboard_page():
    """Display the evaluation dashboard page"""
    
    # Check if feedback has been given
    if not st.session_state.get('feedback_given', False):
        st.warning("⚠️ Please provide activity feedback first to see your progress dashboard.")
        if st.button("Go to Feedback"):
            navigate_to_page('feedback')
            st.rerun()
        return
    
    # Show breadcrumb navigation
    show_breadcrumb()
    
    # Page header
    profile = st.session_state.get('user_profile', {})
    child_name = profile.get('name', 'Your Child')
    
    st.markdown(f"""
    <div class="main-header">
        <h1>📊 Progress Dashboard for {child_name}</h1>
        <p>Track development, celebrate achievements, and plan next steps</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load user data
    if 'user_profile' in st.session_state and 'user_id' in st.session_state.user_profile:
        user_id = st.session_state.user_profile['user_id']
    elif 'user_id' in st.session_state:
        user_id = st.session_state.user_id
    else:
        st.error("Please complete your profile first.")
        return
    
    # Get data from database
    user_stats = get_user_statistics(user_id)
    user_progress = get_user_progress(user_id)
    activity_history = get_user_activity_history(user_id)
    
    # Dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🎯 Skills Progress", "📊 Activity Analytics", "🏆 Achievements"])
    
    with tab1:
        show_overview_dashboard(user_stats, user_progress, activity_history)
    
    with tab2:
        show_skills_progress_dashboard(user_progress, activity_history)
    
    with tab3:
        show_activity_analytics_dashboard(activity_history, user_stats)
    
    with tab4:
        show_achievements_dashboard(user_stats, user_progress, activity_history)
    
    # Mark dashboard as viewed
    st.session_state.dashboard_viewed = True
    
    # Navigation to next step
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("📚 Explore Learning Resources", key="go_to_articles", use_container_width=True):
            navigate_to_page('articles')
            st.rerun()

def show_overview_dashboard(user_stats, user_progress, activity_history):
    """Show overview dashboard with key metrics"""
    
    st.markdown("### 🌟 Progress Overview")
    
    # Key metrics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_activities = user_stats.get('total_activities', 0)
        st.markdown(create_dashboard_metric_html(
            total_activities, 
            "Activities Completed",
            "success"
        ), unsafe_allow_html=True)
    
    with col2:
        avg_rating = user_stats.get('average_rating', 0)
        st.markdown(create_dashboard_metric_html(
            f"{avg_rating}/5", 
            "Average Rating",
            "primary"
        ), unsafe_allow_html=True)
    
    with col3:
        total_hours = user_stats.get('total_hours', 0)
        st.markdown(create_dashboard_metric_html(
            f"{total_hours}h", 
            "Time Invested",
            "accent"
        ), unsafe_allow_html=True)
    
    with col4:
        this_week = user_stats.get('activities_this_week', 0)
        st.markdown(create_dashboard_metric_html(
            this_week, 
            "This Week",
            "secondary"
        ), unsafe_allow_html=True)
    
    # Progress summary
    st.markdown("### 📈 Development Summary")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if user_progress:
            # Create skills radar chart
            skills_data = []
            for skill, data in user_progress.items():
                skills_data.append({
                    'skill': skill,
                    'progress': data['score']
                })
            
            if skills_data:
                df_skills = pd.DataFrame(skills_data)
                
                # Create radar chart
                fig = go.Figure()
                
                fig.add_trace(go.Scatterpolar(
                    r=df_skills['progress'],
                    theta=df_skills['skill'],
                    fill='toself',
                    name='Current Progress',
                    line_color='rgb(74, 144, 226)'
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100]
                        )),
                    showlegend=True,
                    title="Skills Development Radar",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Complete more activities to see your skills progress chart!")
    
    with col2:
        st.markdown("#### 🎯 Current Focus Areas")
        
        # Show top skills being worked on
        top_skills = user_stats.get('top_skills', [])
        if top_skills:
            for skill_data in top_skills:
                skill = skill_data['skill']
                score = skill_data['score']
                progress_bar_value = score / 100
                
                st.markdown(f"**{skill}**")
                st.progress(progress_bar_value)
                st.caption(f"{score:.1f}% progress")
        else:
            st.info("Start completing activities to see your focus areas!")
    
    # Recent activity timeline
    st.markdown("### ⏰ Recent Activity Timeline")
    
    if activity_history:
        # Show last 5 activities
        recent_activities = activity_history[:5]
        
        for activity in recent_activities:
            try:
                # Check if completion_date exists and convert it safely
                if 'completion_date' in activity and activity['completion_date']:
                    completion_date = pd.to_datetime(activity['completion_date'])
                    days_ago = (datetime.now() - completion_date).days
                else:
                    # Use current date if completion_date is missing
                    completion_date = datetime.now()
                    days_ago = 0
            except (ValueError, TypeError):
                # Handle invalid date format
                completion_date = datetime.now()
                days_ago = 0
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**{activity['name']}**")
                st.caption(f"{days_ago} days ago")
            
            with col2:
                if activity['rating']:
                    stars = "⭐" * activity['rating']
                    st.markdown(stars)
                else:
                    st.markdown("No rating")
            
            with col3:
                status_emoji = {
                    'completed': '✅',
                    'partial': '🔄',
                    'started': '🟡'
                }.get(activity['status'], '❓')
                st.markdown(f"{status_emoji} {activity['status'].title()}")
    else:
        st.info("No activities completed yet. Start with some activities to see your timeline!")

def show_skills_progress_dashboard(user_progress, activity_history):
    """Show detailed skills progress dashboard"""
    
    st.markdown("### 🎯 Skills Development Tracking")
    
    if not user_progress:
        st.info("Complete activities and provide feedback to see your skills progress!")
        return
    
    # Skills progress overview
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Create progress bars for each skill
        st.markdown("#### 📊 Current Progress by Skill")
        
        for skill, data in user_progress.items():
            score = data['score']
            last_updated = data['last_updated']
            
            # Progress bar with custom styling
            progress_percentage = score / 100
            
            # Color coding based on progress
            if score >= 80:
                color = "🟢"
                status = "Excellent"
            elif score >= 60:
                color = "🟡"
                status = "Good Progress"
            elif score >= 40:
                color = "🟠"
                status = "Developing"
            else:
                color = "🔴"
                status = "Getting Started"
            
            st.markdown(f"**{skill}** {color}")
            st.progress(progress_percentage)
            
            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.caption(f"{score:.1f}% - {status}")
            with col_b:
                st.caption(f"Last updated: {last_updated[:10] if last_updated else 'N/A'}")
            
            st.markdown("---")
    
    with col2:
        st.markdown("#### 🏆 Progress Levels")
        
        # Show progress level definitions
        levels = [
            ("🔴 Getting Started", "0-39%", "Building foundation"),
            ("🟠 Developing", "40-59%", "Making progress"),
            ("🟡 Good Progress", "60-79%", "Strong development"),
            ("🟢 Excellent", "80-100%", "Mastery level")
        ]
        
        for level, range_text, description in levels:
            st.markdown(f"**{level}**")
            st.caption(f"{range_text}: {description}")
            st.markdown("")
    
    # Skills progress over time
    st.markdown("### 📈 Progress Trends")
    
    # This would ideally show progress over time
    # For now, show a simplified view
    if activity_history:
        # Group activities by skill areas
        skill_activity_count = {}
        
        for activity in activity_history:
            # Extract skills from activity data
            activity_skills = activity.get('data', {}).get('skills', [])
            for skill in activity_skills:
                if skill not in skill_activity_count:
                    skill_activity_count[skill] = 0
                skill_activity_count[skill] += 1
        
        if skill_activity_count:
            # Create bar chart of activity count by skill
            skills_df = pd.DataFrame([
                {'Skill': skill, 'Activities': count}
                for skill, count in skill_activity_count.items()
            ])
            
            fig = px.bar(
                skills_df, 
                x='Skill', 
                y='Activities',
                title="Activities Completed by Skill Area",
                color='Activities',
                color_continuous_scale='Blues'
            )
            
            fig.update_layout(
                xaxis_tickangle=-45,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Goal setting section
    st.markdown("### 🎯 Set New Goals")
    
    with st.expander("Set Progress Goals"):
        st.markdown("Set targets for skill development:")
        
        available_skills = list(user_progress.keys()) if user_progress else [
            "Fine motor skills", "Gross motor skills", "Communication skills",
            "Social skills", "Problem-solving", "Attention and focus"
        ]
        
        selected_skill = st.selectbox("Choose a skill to focus on:", available_skills)
        
        current_score = user_progress.get(selected_skill, {}).get('score', 0) if user_progress else 0
        target_score = st.slider(
            f"Target progress for {selected_skill}:",
            min_value=int(current_score),
            max_value=100,
            value=min(int(current_score) + 20, 100),
            step=5
        )
        
        target_date = st.date_input(
            "Target date:",
            value=datetime.now() + timedelta(days=30)
        )
        
        if st.button("Set Goal"):
            # Save goal (would be implemented in database)
            st.success(f"✅ Goal set: Reach {target_score}% in {selected_skill} by {target_date}")

def show_activity_analytics_dashboard(activity_history, user_stats):
    """Show activity analytics and patterns"""
    
    st.markdown("### 📊 Activity Analytics")
    
    if not activity_history:
        st.info("Complete some activities to see analytics!")
        return
    
    # Activity completion patterns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📅 Activity Completion Over Time")
        
        # Create timeline chart
        df_activities = pd.DataFrame(activity_history)
        
        # Safely convert completion_date to datetime
        try:
            # First ensure the completion_date column exists and has valid values
            df_activities['completion_date'] = df_activities['completion_date'].fillna(pd.Timestamp.now())
            df_activities['completion_date'] = pd.to_datetime(df_activities['completion_date'], errors='coerce')
            # Replace any NaT values with current time
            df_activities['completion_date'] = df_activities['completion_date'].fillna(pd.Timestamp.now())
            df_activities['date'] = df_activities['completion_date'].dt.date
        except Exception as e:
            # If there's any error, create a default date column with today's date
            st.warning(f"Error processing dates: {e}. Using current date for missing values.")
            df_activities['date'] = pd.Timestamp.now().date()
        
        # Group by date
        daily_counts = df_activities.groupby('date').size().reset_index(name='count')
        
        fig = px.line(
            daily_counts,
            x='date',
            y='count',
            title="Daily Activity Completion",
            markers=True
        )
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### ⭐ Rating Distribution")
        
        # Rating distribution
        ratings = [activity['rating'] for activity in activity_history if activity['rating']]
        
        if ratings:
            rating_counts = pd.Series(ratings).value_counts().sort_index()
            
            fig = px.bar(
                x=rating_counts.index,
                y=rating_counts.values,
                title="Activity Ratings Distribution",
                labels={'x': 'Rating (Stars)', 'y': 'Number of Activities'}
            )
            
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No ratings available yet!")
    
    # Activity preferences analysis
    st.markdown("#### 🎨 Activity Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Most completed activity types
        activity_names = [activity['name'] for activity in activity_history]
        activity_types = []
        
        # Categorize activities by type
        for name in activity_names:
            if any(word in name.lower() for word in ['paint', 'draw', 'art']):
                activity_types.append('Arts & Crafts')
            elif any(word in name.lower() for word in ['puzzle', 'match', 'sort']):
                activity_types.append('Cognitive')
            elif any(word in name.lower() for word in ['physical', 'motor', 'movement']):
                activity_types.append('Physical')
            elif any(word in name.lower() for word in ['story', 'read', 'write']):
                activity_types.append('Language')
            else:
                activity_types.append('Other')
        
        if activity_types:
            type_counts = pd.Series(activity_types).value_counts()
            
            fig = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Activity Types Completed"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Success rate analysis
        st.markdown("**Success Patterns:**")
        
        completed_count = len([a for a in activity_history if a['status'] == 'completed'])
        total_count = len(activity_history)
        success_rate = (completed_count / total_count * 100) if total_count > 0 else 0
        
        st.metric("Completion Rate", f"{success_rate:.1f}%")
        
        # Average rating
        avg_rating = user_stats.get('average_rating', 0)
        st.metric("Average Rating", f"{avg_rating}/5 ⭐")
        
        # Most productive day
        if len(activity_history) > 0:
            try:
                df_activities = pd.DataFrame(activity_history)
                # Safely convert completion_date to datetime
                df_activities['completion_date'] = df_activities['completion_date'].fillna(pd.Timestamp.now())
                df_activities['completion_date'] = pd.to_datetime(df_activities['completion_date'], errors='coerce')
                # Replace any NaT values with current time
                df_activities['completion_date'] = df_activities['completion_date'].fillna(pd.Timestamp.now())
                df_activities['day_of_week'] = df_activities['completion_date'].dt.day_name()
                
                most_active_day = df_activities['day_of_week'].mode().iloc[0] if not df_activities['day_of_week'].mode().empty else "N/A"
                st.metric("Most Active Day", most_active_day)
            except Exception as e:
                st.metric("Most Active Day", "N/A")
                st.caption("Error processing date information")

def show_achievements_dashboard(user_stats, user_progress, activity_history):
    """Show achievements and milestones"""
    
    st.markdown("### 🏆 Achievements & Milestones")
    
    # Calculate achievements
    achievements = calculate_achievements(user_stats, user_progress, activity_history)
    
    # Display achievement badges
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 🎖️ Earned Badges")
        
        if achievements['earned']:
            # Display earned achievements in a grid
            achievement_cols = st.columns(3)
            
            for i, achievement in enumerate(achievements['earned']):
                with achievement_cols[i % 3]:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 1rem; border: 2px solid #4A90E2; border-radius: 10px; margin: 0.5rem;">
                        <div style="font-size: 2rem;">{achievement['emoji']}</div>
                        <div style="font-weight: bold;">{achievement['name']}</div>
                        <div style="font-size: 0.8rem; color: #666;">{achievement['description']}</div>
                        <div style="font-size: 0.7rem; color: #999;">Earned: {achievement['date']}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Complete more activities to earn your first achievement badge!")
    
    with col2:
        st.markdown("#### 🎯 Next Milestones")
        
        if achievements['next']:
            for achievement in achievements['next'][:3]:
                progress = achievement.get('progress', 0)
                target = achievement.get('target', 100)
                progress_pct = (progress / target) * 100 if target > 0 else 0
                
                st.markdown(f"**{achievement['emoji']} {achievement['name']}**")
                st.progress(progress_pct / 100)
                st.caption(f"{progress}/{target} - {achievement['description']}")
                st.markdown("")
    
    # Celebration section
    if achievements['earned']:
        st.markdown("### 🎉 Celebrate Your Progress!")
        
        latest_achievement = achievements['earned'][-1]
        st.success(f"🎊 Congratulations! You recently earned: **{latest_achievement['name']}**")
        
        if st.button("🎈 Celebrate!", key="celebrate"):
            st.balloons()
            st.success("🌟 Amazing work! Keep up the great progress!")
    
    # Progress insights
    st.markdown("### 💡 Progress Insights")
    
    insights = generate_progress_insights(user_stats, user_progress, activity_history)
    
    for insight in insights:
        st.info(f"💡 **{insight['title']}**: {insight['message']}")

def calculate_achievements(user_stats, user_progress, activity_history):
    """Calculate earned and next achievements"""
    
    earned = []
    next_milestones = []
    
    total_activities = user_stats.get('total_activities', 0)
    avg_rating = user_stats.get('average_rating', 0)
    total_hours = user_stats.get('total_hours', 0)
    
    # Activity completion achievements
    activity_milestones = [
        (1, "🌟", "First Steps", "Completed your first activity!"),
        (5, "🎯", "Getting Started", "Completed 5 activities"),
        (10, "🚀", "Building Momentum", "Completed 10 activities"),
        (25, "⭐", "Dedicated Learner", "Completed 25 activities"),
        (50, "🏆", "Achievement Master", "Completed 50 activities")
    ]
    
    for threshold, emoji, name, desc in activity_milestones:
        if total_activities >= threshold:
            earned.append({
                'emoji': emoji,
                'name': name,
                'description': desc,
                'date': 'Recently'  # Would be actual date from database
            })
        else:
            next_milestones.append({
                'emoji': emoji,
                'name': name,
                'description': desc,
                'progress': total_activities,
                'target': threshold
            })
            break  # Only show next milestone
    
    # Rating achievements
    if avg_rating >= 4.5:
        earned.append({
            'emoji': '⭐',
            'name': 'Excellence Seeker',
            'description': 'Maintained high activity ratings',
            'date': 'Recently'
        })
    elif avg_rating >= 4.0:
        next_milestones.append({
            'emoji': '⭐',
            'name': 'Excellence Seeker',
            'description': 'Maintain 4.5+ average rating',
            'progress': avg_rating,
            'target': 4.5
        })
    
    # Time investment achievements
    time_milestones = [
        (5, "⏰", "Time Investor", "Spent 5+ hours in activities"),
        (20, "📚", "Dedicated Student", "Spent 20+ hours learning"),
        (50, "🎓", "Learning Champion", "Spent 50+ hours developing skills")
    ]
    
    for threshold, emoji, name, desc in time_milestones:
        if total_hours >= threshold:
            earned.append({
                'emoji': emoji,
                'name': name,
                'description': desc,
                'date': 'Recently'
            })
        else:
            next_milestones.append({
                'emoji': emoji,
                'name': name,
                'description': desc,
                'progress': total_hours,
                'target': threshold
            })
            break
    
    # Skills progress achievements
    if user_progress:
        high_progress_skills = [skill for skill, data in user_progress.items() if data['score'] >= 80]
        
        if len(high_progress_skills) >= 3:
            earned.append({
                'emoji': '🎯',
                'name': 'Multi-Skill Master',
                'description': 'Achieved 80%+ progress in 3+ skills',
                'date': 'Recently'
            })
        elif len(high_progress_skills) >= 1:
            next_milestones.append({
                'emoji': '🎯',
                'name': 'Multi-Skill Master',
                'description': 'Achieve 80%+ in 3 different skills',
                'progress': len(high_progress_skills),
                'target': 3
            })
    
    return {
        'earned': earned,
        'next': next_milestones
    }

def generate_progress_insights(user_stats, user_progress, activity_history):
    """Generate personalized progress insights"""
    
    insights = []
    
    total_activities = user_stats.get('total_activities', 0)
    avg_rating = user_stats.get('average_rating', 0)
    this_week = user_stats.get('activities_this_week', 0)
    
    # Activity frequency insights
    if this_week >= 3:
        insights.append({
            'title': 'Great Consistency',
            'message': f'You\'ve completed {this_week} activities this week! Consistent practice leads to better outcomes.'
        })
    elif this_week == 0 and total_activities > 0:
        insights.append({
            'title': 'Time for Practice',
            'message': 'It\'s been a while since your last activity. Regular practice helps maintain progress!'
        })
    
    # Rating insights
    if avg_rating >= 4.0:
        insights.append({
            'title': 'High Engagement',
            'message': f'Your average rating of {avg_rating}/5 shows great engagement with activities!'
        })
    elif avg_rating < 3.0 and total_activities >= 5:
        insights.append({
            'title': 'Activity Adjustment',
            'message': 'Consider trying different types of activities to find what works best for your child.'
        })
    
    # Progress insights
    if user_progress:
        top_skill = max(user_progress.items(), key=lambda x: x[1]['score'])
        insights.append({
            'title': 'Strength Area',
            'message': f'{top_skill[0]} is your strongest area with {top_skill[1]["score"]:.1f}% progress!'
        })
        
        lowest_skill = min(user_progress.items(), key=lambda x: x[1]['score'])
        if lowest_skill[1]['score'] < 30:
            insights.append({
                'title': 'Growth Opportunity',
                'message': f'Consider focusing more activities on {lowest_skill[0]} to build this skill area.'
            })
    
    # Motivational insights
    if total_activities >= 10:
        insights.append({
            'title': 'Milestone Achievement',
            'message': f'Amazing! You\'ve completed {total_activities} activities. You\'re building great learning habits!'
        })
    
    return insights
