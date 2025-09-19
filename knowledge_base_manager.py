# knowledge_base_manager.py

import json
import os

# Define the path to the knowledge base file
KB_FILE = "knowledge_base.json"

def load_knowledge_base() -> dict:
    """
    Loads the knowledge base from the JSON file.
    Returns an empty dictionary if the file doesn't exist or is invalid.
    """
    if not os.path.exists(KB_FILE):
        return {}  # Return empty dict if file doesn't exist
    try:
        with open(KB_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading knowledge base: {e}")
        return {} # Return empty dict on error

def save_knowledge_base(data: dict):
    """
    Saves the provided dictionary to the knowledge base JSON file.
    """
    try:
        with open(KB_FILE, 'w') as f:
            # indent=4 makes the JSON file human-readable
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"Error saving knowledge base: {e}")

def get_user_details() -> dict:
    """A helper function to quickly get the user_details section."""
    kb = load_knowledge_base()
    return kb.get("user_details", {})

def update_contact(name: str, details: dict):
    """
    Adds or updates a contact in the knowledge base.
    This is how SARA will learn and remember new people.
    """
    kb = load_knowledge_base()
    # Initialize 'contacts' dictionary if it doesn't exist
    if "contacts" not in kb:
        kb["contacts"] = {}
    
    # Add or update the contact's details
    kb["contacts"][name] = details
    
    save_knowledge_base(kb)
    print(f"Knowledge base updated for contact: {name}")