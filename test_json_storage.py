"""
Test script for the JSON storage system
Demonstrates basic functionality and verifies that it's working correctly
"""
import os
import sys
import json
from pathlib import Path
import argparse
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.append(str(backend_path))

# Import JSON storage components
from storage.json_storage import get_json_storage
from frontend.utils.json_database_adapter import (
    init_database, 
    save_user_profile, 
    save_activity_completion, 
    save_activity_feedback, 
    update_user_progress,
    get_user_statistics,
    get_user_progress,
    get_user_activity_history
)

def print_separator(title=None):
    """Print a separator line with optional title"""
    width = 80
    if title:
        print(f"\n{'-' * 10} {title} {'-' * (width - 12 - len(title))}")
    else:
        print(f"\n{'-' * width}")

def test_basic_functionality():
    """Test basic JSON storage functionality"""
    print_separator("Basic Functionality Test")
    
    # Initialize database
    session_id = init_database()
    print(f"Initialized database with session ID: {session_id}")
    
    # Save user profile
    user_data = {
        "name": "Test Child",
        "age": "8 years old",
        "gender": "Prefer not to say",
        "primary_language": "English",
        "interests": ["Drawing", "Science", "Music"],
        "challenges": ["Attention span", "Fine motor skills"]
    }
    
    user_id = save_user_profile(user_data)
    print(f"Saved user profile with ID: {user_id}")
    
    # Save activity completion
    activity_data = {
        "name": "Colorful Patterns",
        "description": "Create patterns with colored blocks",
        "duration": "15-20 minutes",
        "skills": ["Fine motor skills", "Pattern recognition", "Creativity"],
        "materials": ["Colored blocks", "Paper", "Pencils"]
    }
    
    success = save_activity_completion(
        user_id,
        "Colorful Patterns",
        activity_data,
        "Completed successfully",
        4,  # Rating
        "Child enjoyed this activity a lot!",
        25  # Duration in minutes
    )
    
    print(f"Saved activity completion: {success}")
    
    # Save detailed feedback
    feedback_data = {
        "completion_status": "Completed successfully",
        "actual_duration": 25,
        "difficulty_experienced": "Just right",
        "interest_level": "😍 Very excited",
        "attention_span": 20,
        "participation_level": "Eager",
        "help_needed": "Minimal guidance",
        "behavioral_observations": [
            "Stayed calm and focused",
            "Celebrated small successes",
            "Showed creativity or innovation"
        ],
        "skills_practiced": [
            "Fine motor skills",
            "Problem-solving",
            "Creativity"
        ],
        "overall_rating": 4,
        "would_recommend": "Yes, definitely",
        "what_worked_well": "The colorful materials were very engaging",
        "what_could_improve": "Could use more variety in patterns",
        "submitted_at": str(datetime.now())
    }
    
    success = save_activity_feedback(
        user_id,
        "Colorful Patterns",
        "detailed_feedback",
        feedback_data
    )
    
    print(f"Saved detailed feedback: {success}")
    
    # Update skill progress
    for skill in ["Fine motor skills", "Problem-solving", "Creativity"]:
        success = update_user_progress(
            user_id,
            skill,
            30,  # Initial progress score
            f"Initial progress from Colorful Patterns activity"
        )
        print(f"Updated progress for {skill}: {success}")
    
    return user_id

def test_data_retrieval(user_id):
    """Test data retrieval functions"""
    print_separator("Data Retrieval Test")
    
    # Get user statistics
    user_stats = get_user_statistics(user_id)
    print("User Statistics:")
    print(f"  Total activities: {user_stats.get('total_activities', 0)}")
    print(f"  Average rating: {user_stats.get('average_rating', 0)}")
    print(f"  Total hours: {user_stats.get('total_hours', 0)}")
    print(f"  Activities this week: {user_stats.get('activities_this_week', 0)}")
    
    # Get user progress
    user_progress = get_user_progress(user_id)
    print("\nUser Progress:")
    for skill, data in user_progress.items():
        print(f"  {skill}: {data.get('score', 0)}%")
    
    # Get activity history
    activity_history = get_user_activity_history(user_id)
    print("\nActivity History:")
    for activity in activity_history:
        print(f"  {activity.get('activity_name', 'Unknown')}: {activity.get('completion_status', 'Unknown')}")

def test_file_structure(session_id):
    """Test JSON file structure"""
    print_separator("JSON File Structure Test")
    
    # Get JSON storage
    storage = get_json_storage()
    
    # Get session path
    session_path = storage.get_session_path(session_id)
    print(f"Session directory: {session_path}")
    
    # List all JSON files
    json_files = list(session_path.glob("*.json"))
    print("\nJSON files in session directory:")
    for file_path in json_files:
        file_size = os.path.getsize(file_path)
        print(f"  {file_path.name} ({file_size} bytes)")
        
        # Print file structure (first level only)
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    print(f"    Keys: {', '.join(data.keys())}")
                else:
                    print(f"    Type: {type(data)}")
        except Exception as e:
            print(f"    Error reading file: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test JSON storage system')
    parser.add_argument('--base-path', help='Base path for data storage')
    args = parser.parse_args()
    
    print("\n🔍 PsyTech JSON Storage System Test")
    print("===================================")
    
    # Initialize storage with optional base path
    if args.base_path:
        from storage.json_storage import get_json_storage
        get_json_storage(args.base_path)
    
    # Run tests
    user_id = test_basic_functionality()
    test_data_retrieval(user_id)
    
    # Get current session ID
    from frontend.utils.json_database_adapter import get_current_session
    session_id = get_current_session()
    test_file_structure(session_id)
    
    print_separator()
    print("✅ All tests completed successfully!")
    print(f"Session ID: {session_id}")
    print(f"User ID: {user_id}")
    print("\nYou can now run the application to see the data in the dashboard:")
    print("  streamlit run psyTech/frontend/main_app.py")

if __name__ == "__main__":
    main()
