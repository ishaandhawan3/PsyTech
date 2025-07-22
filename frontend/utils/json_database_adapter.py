"""
JSON Database Adapter for PsyTech
Provides database-like interface using JSON storage
"""

import sys
import os
from pathlib import Path
import json
import uuid
from datetime import datetime
import pandas as pd

# Add backend to path for imports
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.append(str(backend_path))

# Import JSON storage
from storage.json_storage import get_json_storage

# Global session ID (will be set during initialization)
_current_session_id = None

def init_database(base_path=None):
    """
    Initialize the JSON storage system
    :param base_path: Optional base path for data storage
    """
    global _current_session_id
    
    # Get or create JSON storage
    storage = get_json_storage(base_path)
    
    # Check if we have an active session
    if _current_session_id is None:
        # Get existing sessions
        sessions = storage.list_sessions()
        
        if sessions:
            # Use the most recent session
            _current_session_id = sessions[-1]
        else:
            # Create a new session
            _current_session_id = storage.create_session()
    
    return _current_session_id

def get_current_session():
    """
    Get the current session ID
    :return: Session ID string
    """
    global _current_session_id
    
    if _current_session_id is None:
        _current_session_id = init_database()
    
    return _current_session_id

def save_user_profile(user_data):
    """
    Save user profile data
    :param user_data: User profile data dictionary
    :return: User ID
    """
    storage = get_json_storage()
    session_id = get_current_session()
    
    # Add user ID if not present
    if "user_id" not in user_data:
        user_data["user_id"] = str(uuid.uuid4())
    
    # Save to JSON
    success, user_id = storage.save_data(session_id, "userprofile", user_data)
    
    return user_id if success else None

def get_user_profile(user_id=None):
    """
    Get user profile data
    :param user_id: Optional user ID (uses current session if not provided)
    :return: User profile data dictionary
    """
    storage = get_json_storage()
    session_id = get_current_session()
    
    # Load from JSON
    profile_data = storage.load_data(session_id, "userprofile")
    
    # Check if user_id matches if provided
    if user_id and profile_data and profile_data.get("user_id") != user_id:
        return None
    
    return profile_data

def save_activity_completion(user_id, activity_name, activity_data, completion_status, rating, comments, duration):
    """
    Save activity completion data
    :param user_id: User ID
    :param activity_name: Name of the activity
    :param activity_data: Full activity data
    :param completion_status: Completion status string
    :param rating: Rating (1-5)
    :param comments: Comments text
    :param duration: Duration in minutes
    :return: Success boolean
    """
    storage = get_json_storage()
    session_id = get_current_session()
    
    # Create activity completion record
    completion_data = {
        "user_id": user_id,
        "activity_name": activity_name,
        "completion_status": completion_status,
        "rating": rating,
        "comments": comments,
        "duration_minutes": duration,
        "completion_date": datetime.now().isoformat(),
        "data": activity_data  # Store full activity data
    }
    
    # Load existing activities or create new
    activities = storage.load_data(session_id, "activities")
    
    if activities is None:
        # First activity
        activities = {
            "user_id": user_id,
            "activities": [completion_data]
        }
        success, _ = storage.save_data(session_id, "activities", activities)
    else:
        # Append to existing activities
        updated_data = storage.append_data(
            session_id, 
            "activities", 
            completion_data, 
            key="activities", 
            user_id=user_id
        )
        success = updated_data is not None
    
    return success

def save_activity_feedback(user_id, activity_name, feedback_type, feedback_data):
    """
    Save detailed activity feedback
    :param user_id: User ID
    :param activity_name: Name of the activity
    :param feedback_type: Type of feedback (e.g., 'detailed_feedback', 'quick_rating')
    :param feedback_data: Feedback data dictionary
    :return: Success boolean
    """
    storage = get_json_storage()
    session_id = get_current_session()
    
    # Create feedback record
    feedback_record = {
        "user_id": user_id,
        "activity_name": activity_name,
        "feedback_type": feedback_type,
        "feedback_data": feedback_data,
        "submitted_at": datetime.now().isoformat()
    }
    
    # Load existing feedback or create new
    feedback = storage.load_data(session_id, "feedback")
    
    if feedback is None:
        # First feedback
        feedback = {
            "user_id": user_id,
            "feedback_entries": [feedback_record]
        }
        success, _ = storage.save_data(session_id, "feedback", feedback)
    else:
        # Append to existing feedback
        updated_data = storage.append_data(
            session_id, 
            "feedback", 
            feedback_record, 
            key="feedback_entries", 
            user_id=user_id
        )
        success = updated_data is not None
    
    return success

def get_user_progress(user_id):
    """
    Get user progress data
    :param user_id: User ID
    :return: Dictionary of skill progress data
    """
    storage = get_json_storage()
    session_id = get_current_session()
    
    # Load progress data
    progress_data = storage.load_data(session_id, "progress")
    
    if progress_data is None or progress_data.get("user_id") != user_id:
        return {}
    
    # Return skills progress
    return progress_data.get("skills", {})

def update_user_progress(user_id, skill, score, notes=None):
    """
    Update progress for a specific skill
    :param user_id: User ID
    :param skill: Skill name
    :param score: Progress score (0-100)
    :param notes: Optional notes about the update
    :return: Success boolean
    """
    storage = get_json_storage()
    session_id = get_current_session()
    
    # Load existing progress data
    progress_data = storage.load_data(session_id, "progress")
    
    if progress_data is None:
        # Initialize progress data
        progress_data = {
            "user_id": user_id,
            "skills": {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    # Ensure skills dictionary exists
    if "skills" not in progress_data:
        progress_data["skills"] = {}
    
    # Update skill progress
    if skill not in progress_data["skills"]:
        progress_data["skills"][skill] = {
            "score": score,
            "history": [],
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
    else:
        # Add to history
        if "history" not in progress_data["skills"][skill]:
            progress_data["skills"][skill]["history"] = []
        
        progress_data["skills"][skill]["history"].append({
            "previous_score": progress_data["skills"][skill].get("score", 0),
            "new_score": score,
            "date": datetime.now().isoformat(),
            "notes": notes
        })
        
        # Update current score
        progress_data["skills"][skill]["score"] = score
        progress_data["skills"][skill]["last_updated"] = datetime.now().isoformat()
    
    # Update timestamp
    progress_data["updated_at"] = datetime.now().isoformat()
    
    # Save updated progress
    success, _ = storage.save_data(session_id, "progress", progress_data, user_id)
    
    return success

def get_user_statistics(user_id):
    """
    Calculate user statistics from activity and progress data
    :param user_id: User ID
    :return: Dictionary of statistics
    """
    storage = get_json_storage()
    session_id = get_current_session()
    
    # Initialize statistics
    stats = {
        "total_activities": 0,
        "average_rating": 0,
        "total_hours": 0,
        "activities_this_week": 0,
        "top_skills": []
    }
    
    # Load activities data
    activities_data = storage.load_data(session_id, "activities")
    
    if activities_data and activities_data.get("user_id") == user_id:
        activities = activities_data.get("activities", [])
        
        if activities:
            # Count total activities
            stats["total_activities"] = len(activities)
            
            # Calculate average rating
            ratings = [a.get("rating", 0) for a in activities if a.get("rating")]
            if ratings:
                stats["average_rating"] = sum(ratings) / len(ratings)
            
            # Calculate total hours
            durations = [a.get("duration_minutes", 0) for a in activities]
            stats["total_hours"] = sum(durations) / 60
            
            # Count activities this week
            now = datetime.now()
            one_week_ago = now.timestamp() - (7 * 24 * 60 * 60)
            
            this_week = 0
            for activity in activities:
                try:
                    completion_date = activity.get("completion_date")
                    if completion_date:
                        completion_timestamp = datetime.fromisoformat(completion_date).timestamp()
                        if completion_timestamp >= one_week_ago:
                            this_week += 1
                except (ValueError, TypeError):
                    pass
            
            stats["activities_this_week"] = this_week
    
    # Get top skills from progress data
    progress_data = storage.load_data(session_id, "progress")
    
    if progress_data and progress_data.get("user_id") == user_id:
        skills = progress_data.get("skills", {})
        
        # Sort skills by score
        sorted_skills = sorted(
            [{"skill": k, "score": v.get("score", 0)} for k, v in skills.items()],
            key=lambda x: x["score"],
            reverse=True
        )
        
        stats["top_skills"] = sorted_skills[:5]  # Top 5 skills
    
    return stats

def get_user_activity_history(user_id):
    """
    Get user activity history
    :param user_id: User ID
    :return: List of activity records
    """
    storage = get_json_storage()
    session_id = get_current_session()
    
    # Load activities data
    activities_data = storage.load_data(session_id, "activities")
    
    if activities_data and activities_data.get("user_id") == user_id:
        activities = activities_data.get("activities", [])
        
        # Sort by completion date (newest first)
        try:
            sorted_activities = sorted(
                activities,
                key=lambda x: datetime.fromisoformat(x.get("completion_date", "2000-01-01T00:00:00")),
                reverse=True
            )
        except (ValueError, TypeError):
            # If sorting fails, return unsorted
            sorted_activities = activities
        
        return sorted_activities
    
    return []

def get_activity_feedback(user_id):
    """
    Get all feedback for a user
    :param user_id: User ID
    :return: List of feedback entries
    """
    storage = get_json_storage()
    session_id = get_current_session()
    
    # Load feedback data
    feedback_data = storage.load_data(session_id, "feedback")
    
    if feedback_data and feedback_data.get("user_id") == user_id:
        return feedback_data.get("feedback_entries", [])
    
    return []

def save_feed_item(user_id, feed_type, content):
    """
    Save a feed item
    :param user_id: User ID
    :param feed_type: Type of feed item (e.g., 'article', 'tip')
    :param content: Feed item content
    :return: Success boolean
    """
    storage = get_json_storage()
    session_id = get_current_session()
    
    # Create feed item
    feed_item = {
        "user_id": user_id,
        "feed_type": feed_type,
        "content": content,
        "created_at": datetime.now().isoformat(),
        "read": False
    }
    
    # Load existing feed or create new
    feed_data = storage.load_data(session_id, "feed")
    
    if feed_data is None:
        # First feed item
        feed_data = {
            "user_id": user_id,
            "feed_items": [feed_item]
        }
        success, _ = storage.save_data(session_id, "feed", feed_data)
    else:
        # Append to existing feed
        updated_data = storage.append_data(
            session_id, 
            "feed", 
            feed_item, 
            key="feed_items", 
            user_id=user_id
        )
        success = updated_data is not None
    
    return success

def get_feed_items(user_id, feed_type=None, limit=10):
    """
    Get feed items for a user
    :param user_id: User ID
    :param feed_type: Optional filter by feed type
    :param limit: Maximum number of items to return
    :return: List of feed items
    """
    storage = get_json_storage()
    session_id = get_current_session()
    
    # Load feed data
    feed_data = storage.load_data(session_id, "feed")
    
    if feed_data and feed_data.get("user_id") == user_id:
        feed_items = feed_data.get("feed_items", [])
        
        # Filter by type if specified
        if feed_type:
            feed_items = [item for item in feed_items if item.get("feed_type") == feed_type]
        
        # Sort by creation date (newest first)
        try:
            sorted_items = sorted(
                feed_items,
                key=lambda x: datetime.fromisoformat(x.get("created_at", "2000-01-01T00:00:00")),
                reverse=True
            )
        except (ValueError, TypeError):
            # If sorting fails, return unsorted
            sorted_items = feed_items
        
        return sorted_items[:limit]
    
    return []

def bookmark_article(user_id, title, url, summary=None):
    """
    Bookmark an article for a user
    :param user_id: User ID
    :param title: Article title
    :param url: Article URL
    :param summary: Optional article summary
    :return: Success boolean
    """
    storage = get_json_storage()
    session_id = get_current_session()
    
    # Create bookmark record
    bookmark = {
        "user_id": user_id,
        "title": title,
        "url": url,
        "summary": summary,
        "bookmarked_at": datetime.now().isoformat()
    }
    
    # Load existing bookmarks or create new
    bookmarks_data = storage.load_data(session_id, "bookmarks")
    
    if bookmarks_data is None:
        # First bookmark
        bookmarks_data = {
            "user_id": user_id,
            "bookmarks": [bookmark]
        }
        success, _ = storage.save_data(session_id, "bookmarks", bookmarks_data)
    else:
        # Check if already bookmarked
        existing_bookmarks = bookmarks_data.get("bookmarks", [])
        for existing in existing_bookmarks:
            if existing.get("url") == url:
                # Already bookmarked
                return True
        
        # Append to existing bookmarks
        updated_data = storage.append_data(
            session_id, 
            "bookmarks", 
            bookmark, 
            key="bookmarks", 
            user_id=user_id
        )
        success = updated_data is not None
    
    return success

def get_bookmarked_articles(user_id):
    """
    Get bookmarked articles for a user
    :param user_id: User ID
    :return: List of bookmarked articles
    """
    storage = get_json_storage()
    session_id = get_current_session()
    
    # Load bookmarks data
    bookmarks_data = storage.load_data(session_id, "bookmarks")
    
    if bookmarks_data and bookmarks_data.get("user_id") == user_id:
        bookmarks = bookmarks_data.get("bookmarks", [])
        
        # Sort by bookmark date (newest first)
        try:
            sorted_bookmarks = sorted(
                bookmarks,
                key=lambda x: datetime.fromisoformat(x.get("bookmarked_at", "2000-01-01T00:00:00")),
                reverse=True
            )
        except (ValueError, TypeError):
            # If sorting fails, return unsorted
            sorted_bookmarks = bookmarks
        
        return sorted_bookmarks
    
    return []

def update_user_profile(user_id, profile_data):
    """
    Update user profile data
    :param user_id: User ID
    :param profile_data: Updated profile data
    :return: Success boolean
    """
    storage = get_json_storage()
    session_id = get_current_session()
    
    # Ensure user_id is in profile data
    profile_data["user_id"] = user_id
    
    # Add updated timestamp
    profile_data["updated_at"] = datetime.now().isoformat()
    
    # Save to JSON
    success, _ = storage.save_data(session_id, "userprofile", profile_data, user_id)
    
    return success

def run_inspector():
    """
    Run the data inspector app
    """
    # This would launch a Streamlit app for inspecting the data
    # For now, just print a message
    print("Data inspector not implemented for JSON storage yet")
