"""
JSON Storage Module for PsyTech
Handles all JSON file storage operations for the application
"""

import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JSONStorage:
    def __init__(self, base_path=None):
        """
        Initialize JSON storage with base path
        :param base_path: Base directory for storing JSON files
        """
        # Default to data/sessions if not provided
        self.base_path = base_path or Path("data/sessions")
        
        # Ensure base directory exists
        os.makedirs(self.base_path, exist_ok=True)
        logger.info(f"Initialized JSON storage at {self.base_path}")
    
    def create_session(self):
        """
        Create a new session with unique ID
        :return: Session ID string
        """
        session_id = str(uuid.uuid4())
        session_path = Path(self.base_path) / session_id
        
        # Create session directory
        os.makedirs(session_path, exist_ok=True)
        
        # Create timestamp file to mark creation time
        with open(session_path / "session_info.json", "w") as f:
            json.dump({
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }, f, indent=2)
        
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    def get_session_path(self, session_id):
        """
        Get path to session directory
        :param session_id: Session ID
        :return: Path object for session directory
        """
        return Path(self.base_path) / session_id
    
    def save_data(self, session_id, data_type, data, user_id=None):
        """
        Save data to a JSON file
        :param session_id: Session ID
        :param data_type: Type of data (e.g., 'userprofile', 'activities')
        :param data: Data to save (dictionary)
        :param user_id: Optional user ID
        :return: Tuple of (success, user_id)
        """
        session_path = self.get_session_path(session_id)
        
        # Ensure session directory exists
        if not session_path.exists():
            logger.warning(f"Session directory not found: {session_id}")
            return False, None
        
        # Add metadata
        if not isinstance(data, dict):
            data = {"data": data}
        
        # Add or use existing user_id
        if user_id:
            data["user_id"] = user_id
        elif "user_id" not in data and data_type == "userprofile":
            # Generate user_id for new user profiles
            data["user_id"] = str(uuid.uuid4())
        
        # Add timestamps
        data["updated_at"] = datetime.now().isoformat()
        if "created_at" not in data:
            data["created_at"] = datetime.now().isoformat()
        
        # Determine file path
        file_path = session_path / f"{data_type}.json"
        
        try:
            # Write data to file
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {data_type} data for session {session_id}")
            return True, data.get("user_id")
        
        except Exception as e:
            logger.error(f"Error saving {data_type} data: {str(e)}")
            return False, None
    
    def load_data(self, session_id, data_type):
        """
        Load data from a JSON file
        :param session_id: Session ID
        :param data_type: Type of data to load
        :return: Data dictionary or None if not found
        """
        session_path = self.get_session_path(session_id)
        file_path = session_path / f"{data_type}.json"
        
        if not file_path.exists():
            logger.warning(f"Data file not found: {file_path}")
            return None
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            logger.info(f"Loaded {data_type} data for session {session_id}")
            return data
        
        except Exception as e:
            logger.error(f"Error loading {data_type} data: {str(e)}")
            return None
    
    def append_data(self, session_id, data_type, new_data, key=None, user_id=None):
        """
        Append data to an existing JSON file
        :param session_id: Session ID
        :param data_type: Type of data
        :param new_data: New data to append
        :param key: Key to append under (if None, appends to root array)
        :param user_id: Optional user ID
        :return: Updated data dictionary
        """
        # Load existing data
        data = self.load_data(session_id, data_type) or {}
        
        # Add user_id if provided
        if user_id and "user_id" not in data:
            data["user_id"] = user_id
        
        # Append data
        if key:
            # Append to a specific key
            if key not in data:
                data[key] = []
            
            if not isinstance(data[key], list):
                data[key] = [data[key]]
            
            # Add timestamp to new data
            if isinstance(new_data, dict):
                new_data["added_at"] = datetime.now().isoformat()
            
            data[key].append(new_data)
        else:
            # Append to root (assuming it's a list)
            if not isinstance(data, list):
                # Convert to list if not already
                if "data" in data and isinstance(data["data"], list):
                    root_data = data["data"]
                else:
                    root_data = [data] if data else []
                
                data = {
                    "data": root_data,
                    "updated_at": datetime.now().isoformat()
                }
            
            # Add timestamp to new data
            if isinstance(new_data, dict):
                new_data["added_at"] = datetime.now().isoformat()
            
            data["data"].append(new_data)
        
        # Update timestamp
        data["updated_at"] = datetime.now().isoformat()
        
        # Save updated data
        self.save_data(session_id, data_type, data, user_id)
        
        return data
    
    def get_session_data_types(self, session_id):
        """
        Get list of data types available for a session
        :param session_id: Session ID
        :return: List of data type names
        """
        session_path = self.get_session_path(session_id)
        
        if not session_path.exists():
            logger.warning(f"Session directory not found: {session_id}")
            return []
        
        # Get all JSON files in session directory
        data_types = []
        for file_path in session_path.glob("*.json"):
            if file_path.name != "session_info.json":
                data_types.append(file_path.stem)
        
        return data_types
    
    def list_sessions(self):
        """
        List all available sessions
        :return: List of session IDs
        """
        base_path = Path(self.base_path)
        
        if not base_path.exists():
            logger.warning(f"Base path not found: {base_path}")
            return []
        
        # Get all subdirectories (sessions)
        sessions = []
        for path in base_path.iterdir():
            if path.is_dir() and (path / "session_info.json").exists():
                sessions.append(path.name)
        
        return sessions
    
    def get_storage_info(self):
        """
        Get information about the storage system
        :return: Dictionary with storage information
        """
        return {
            "type": "json",
            "status": {
                "json_enabled": True,
                "sql_enabled": False,
                "s3_enabled": False
            },
            "paths": {
                "base_path": str(self.base_path)
            },
            "sessions": self.list_sessions()
        }

# Create a singleton instance
_json_storage = None

def get_json_storage(base_path=None):
    """
    Get or create the JSON storage instance
    :param base_path: Optional base path
    :return: JSONStorage instance
    """
    global _json_storage
    
    if _json_storage is None:
        _json_storage = JSONStorage(base_path)
    
    return _json_storage
