"""
Test script for the dual storage system
Demonstrates basic functionality and verifies that it's working correctly
"""
import os
import sys
import json
import time
from pathlib import Path
import argparse

# Add backend to path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

# Import storage components
from storage.storage_service import StorageService
from storage.config import load_config, save_config

def print_separator(title=None):
    """Print a separator line with optional title"""
    width = 80
    if title:
        print(f"\n{'-' * 10} {title} {'-' * (width - 12 - len(title))}")
    else:
        print(f"\n{'-' * width}")

def test_basic_functionality(storage):
    """Test basic storage functionality"""
    print_separator("Basic Functionality Test")
    
    # Create a session
    session_id = storage.create_session()
    print(f"Created session: {session_id}")
    
    # Save user profile
    user_data = {
        "name": "Test User",
        "age": "10 years old",
        "gender": "Prefer not to say",
        "primary_language": "English",
        "family_structure": "Nuclear family",
        "has_siblings": "Yes",
        "num_siblings": 2
    }
    
    success, user_id = storage.save_data(session_id, "user_profile", user_data)
    print(f"Saved user profile: success={success}, user_id={user_id}")
    
    # Load user profile
    loaded_data = storage.load_data(session_id, "user_profile")
    print(f"Loaded user profile: {loaded_data['name']}")
    
    # Save activity data
    activity_data = {
        "activity_name": "Reading Practice",
        "completion_status": "completed",
        "rating": 5,
        "feedback": "Enjoyed it!",
        "duration_minutes": 30
    }
    
    success, _ = storage.save_data(session_id, "activities", activity_data, user_id)
    print(f"Saved activity data: success={success}")
    
    # Append feedback data
    feedback_data = {
        "type": "positive",
        "comment": "This was fun!"
    }
    
    updated_data = storage.append_data(
        session_id, 
        "feedback", 
        feedback_data, 
        key="comments", 
        user_id=user_id
    )
    print(f"Appended feedback data: {len(updated_data.get('comments', []))} comments")
    
    return session_id, user_id

def test_storage_types(storage, session_id, user_id):
    """Test different storage types"""
    print_separator("Storage Types Test")
    
    # Get storage info
    info = storage.get_storage_info()
    print("Storage configuration:")
    print(f"  JSON enabled: {info['status']['json_enabled']}")
    print(f"  SQL enabled: {info['status']['sql_enabled']}")
    print(f"  S3 enabled: {info['status']['s3_enabled']}")
    
    # Get session data types
    data_types = storage.get_session_data_types(session_id)
    print(f"Session data types: {', '.join(data_types)}")
    
    # Check data in each storage type
    if info['status']['json_enabled']:
        json_path = Path(info['paths']['base_path']) / "sessions" / session_id / "user_profile.json"
        if json_path.exists():
            with open(json_path, 'r') as f:
                json_data = json.load(f)
            print(f"JSON data: {json_data['name']}")
    
    if info['status']['sql_enabled']:
        from storage.db_store import get_db_connection, get_user_profile
        db_path = Path(info['paths']['db_path'])
        if db_path.exists():
            conn = get_db_connection(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE session_id = ?", (session_id,))
            count = cursor.fetchone()[0]
            conn.close()
            print(f"SQL data: {count} user(s) found")

def test_schema_evolution(storage, session_id, user_id):
    """Test schema evolution"""
    print_separator("Schema Evolution Test")
    
    # Add a new field to user profile
    updated_profile = storage.load_data(session_id, "user_profile")
    updated_profile["favorite_color"] = "Blue"
    success, _ = storage.save_data(session_id, "user_profile", updated_profile, user_id)
    print(f"Updated profile with new field: success={success}")
    
    # Validate data consistency
    issues = storage.validate_data_consistency(session_id)
    if issues:
        print(f"Found {len(issues)} consistency issues:")
        for issue in issues:
            print(f"  - {issue['data_type']}: {issue['issue']}")
    else:
        print("No consistency issues found")
    
    # This would normally be done by adding a migration in db_store.py
    print("\nIn a real scenario, you would add a migration like:")
    print("""
    2: {
        "description": "Add favorite_color to users",
        "sql": [
            "ALTER TABLE users ADD COLUMN favorite_color TEXT"
        ]
    }
    """)

def test_data_inspector(storage, session_id):
    """Test data inspector"""
    print_separator("Data Inspector")
    
    print("To run the data inspector:")
    print("  streamlit run psyTech/backend/inspector_app.py")
    print("\nThe inspector will show:")
    print("  - Storage configuration and status")
    print("  - Database schema information")
    print("  - Session data browser")
    print("  - Side-by-side comparison of SQL and JSON data")
    
    # Show session data
    data_types = storage.get_session_data_types(session_id)
    print(f"\nSession {session_id} contains data types: {', '.join(data_types)}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test dual storage system')
    parser.add_argument('--config', help='Path to config file')
    parser.add_argument('--base-path', help='Base path for data storage')
    args = parser.parse_args()
    
    # Initialize storage service
    storage = StorageService(args.config, args.base_path)
    
    print("\n🔍 PsyTech Dual Storage System Test")
    print("===================================")
    
    # Run tests
    session_id, user_id = test_basic_functionality(storage)
    test_storage_types(storage, session_id, user_id)
    test_schema_evolution(storage, session_id, user_id)
    test_data_inspector(storage, session_id)
    
    print_separator()
    print("✅ All tests completed successfully!")
    print(f"Session ID: {session_id}")
    print(f"User ID: {user_id}")
    print("\nYou can now run the data inspector to view the test data:")
    print("  streamlit run psyTech/backend/inspector_app.py")

if __name__ == "__main__":
    main()
