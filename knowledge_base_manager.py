# knowledge_base_manager.py

import json
import os
import chromadb
from sentence_transformers import SentenceTransformer

# --- Configuration ---
KB_FILE = "knowledge_base.json"
DB_PATH = "./chroma_db"
COLLECTION_NAME = "sara_memory_stream"

# --- Fact Store (JSON) Functions ---

def load_knowledge_base() -> dict:
    """Loads the fact store from the JSON file."""
    if not os.path.exists(KB_FILE):
        return {"user_details": {}, "contacts": {}}
    try:
        with open(KB_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading knowledge base: {e}")
        return {"user_details": {}, "contacts": {}}

def save_knowledge_base(data: dict):
    """Saves the provided dictionary to the fact store JSON file."""
    try:
        with open(KB_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"Error saving knowledge base: {e}")

def get_user_details() -> dict:
    """A helper function to quickly get the user_details section."""
    kb = load_knowledge_base()
    return kb.get("user_details", {})

def update_contact(name: str, details: dict):
    """Adds or updates a contact in the knowledge base fact store."""
    kb = load_knowledge_base()
    if "contacts" not in kb:
        kb["contacts"] = {}
    kb["contacts"][name] = details
    save_knowledge_base(kb)
    print(f"Knowledge base (Fact Store) updated for contact: {name}")

def update_user_details(details_to_update: dict):
    """Adds or updates details in the user_details section of the fact store."""
    kb = load_knowledge_base()
    if "user_details" not in kb:
        kb["user_details"] = {}
    
    kb["user_details"].update(details_to_update)
    save_knowledge_base(kb)
    print(f"Knowledge base (User Details) updated with: {details_to_update.keys()}")

# --- Memory Stream (Vector DB) Class ---

class MemoryStream:
    def __init__(self):
        """
        Initializes the Memory Stream, setting up the vector database
        and loading the embedding model.
        """
        try:
            print("Loading embedding model... (This may take a moment on first run)")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            print("Embedding model loaded successfully.")

            self.client = chromadb.PersistentClient(path=DB_PATH)
            self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)
            self.memory_id_counter = self.collection.count()
            print(f"Memory Stream initialized. Found {self.memory_id_counter} existing memories.")

        except Exception as e:
            print(f"FATAL: Could not initialize MemoryStream: {e}")
            self.model = None
            self.collection = None

    def add_memory(self, text: str):
        """
        Adds a new memory to the vector database.
        It converts the text to a vector (embedding) and stores it.
        """
        if not self.collection or not self.model:
            print("Cannot add memory, MemoryStream not initialized correctly.")
            return

        try:
            embedding = self.model.encode(text).tolist()
            self.memory_id_counter += 1
            memory_id = str(self.memory_id_counter)

            self.collection.add(
                embeddings=[embedding],
                documents=[text],
                metadatas=[{"source": "user_command"}],
                ids=[memory_id]
            )
            print(f"Added new memory (ID: {memory_id}): '{text}'")
        except Exception as e:
            print(f"Error adding memory: {e}")

    def recall_memories(self, query_text: str, num_results: int = 3) -> list:
        """
        Recalls the most relevant memories based on a query.
        Performs a semantic search in the vector database.
        """
        if not self.collection or not self.model:
            print("Cannot recall memories, MemoryStream not initialized correctly.")
            return []

        try:
            query_embedding = self.model.encode(query_text).tolist()
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=num_results
            )
            return results.get('documents', [[]])[0]
        except Exception as e:
            print(f"Error recalling memories: {e}")
            return []