# llm_service.py

import google.generativeai as genai
import ollama
import json
import re
from config import GOOGLE_API_KEY, OFFLINE_MODEL

# --- Model Configuration ---
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    online_model = genai.GenerativeModel('gemini-1.5-flash-latest')
    print("Online model (Gemini 1.5 Flash) configured successfully.")
except Exception as e:
    print(f"Error configuring online model: {e}")
    online_model = None

# --- Core LLM Interaction Functions ---

def online_llm_text(prompt: str) -> str:
    """Sends a prompt to the powerful online model (Gemini) for complex tasks."""
    if not online_model: return "Error: Online model is not configured."
    try:
        response = online_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error communicating with online model: {e}")
        return f"Error: Could not get a response. Details: {e}"

def get_intent(user_command: str) -> str:
    """The Router: Classifies the user's intent."""
    prompt = f"""
    Classify the user's command into ONE of the following four categories:
    'automation', 'screen_read', 'conversation', 'remember'.

    - 'automation': Controlling an application (open, type, save).
    - 'screen_read': Capturing or analyzing the screen.
    - 'remember': The user explicitly asks to remember, save, or store information.
    - 'conversation': All other general questions, greetings, or chat.

    Classify this command: "{user_command}"
    """
    try:
        response = online_llm_text(prompt).strip().lower().replace("'", "").replace('"',"")
        print(f"LLM Intent Raw Response: '{response}'")
        if 'automation' in response: return 'automation'
        if 'screen_read' in response: return 'screen_read'
        if 'remember' in response: return 'remember'
        return 'conversation'
    except Exception as e:
        print(f"Error classifying intent: {e}")
        return 'conversation'

def extract_facts_from_text(text_to_analyze: str) -> dict:
    """The Fact Extractor: Finds personal details in text."""
    prompt = f"""
    Analyze the user's statement and extract any personal facts (like name, age, college, teacher's name, phone number, email, etc.) into a JSON object.
    The keys should be snake_case (e.g., "teacher_name"). If no facts, return {{}}.
    Statement: "{text_to_analyze}"
    """
    try:
        facts_str = online_llm_text(prompt)
        match = re.search(r'\{.*\}', facts_str, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return {}
    except Exception as e:
        print(f"Error extracting facts: {e}")
        return {}

def get_automation_plan(user_command: str, context: dict = None) -> dict:
    """The Planner: Uses a strict, simple schema."""
    context_str = json.dumps(context, indent=2)
    prompt = f"""
    You are an automation planner. Create a JSON plan to control a desktop.
    User's context: {context_str}
    User's command: "{user_command}"

    You MUST create a JSON object with three top-level keys:
    1. "application": The lowercase name of the application (e.g., "notepad").
    2. "action": A brief summary of the goal.
    3. "sub_actions": A list of steps. Each step MUST be a dictionary with a "type" and its parameters.

    The ONLY valid "type" values for sub_actions are:
    - "type_text": requires a "text" parameter.
    - "save_file": requires a "filename" parameter.

    Example Plan:
    {{
        "application": "notepad",
        "action": "Draft and save a note",
        "sub_actions": [
            {{"type": "type_text", "text": "This is the content of the note."}},
            {{"type": "save_file", "filename": "note.txt"}}
        ]
    }}

    Create the JSON plan for the user's command. Respond with ONLY the JSON.
    """
    try:
        response_str = online_llm_text(prompt)
        print(f"LLM Planner Raw Response: '{response_str}'")

        match = re.search(r'\{.*\}', response_str, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            return {"action": "error", "message": "The planner did not return valid JSON."}
    except Exception as e:
        print(f"Error parsing automation plan: {e}")
        return {"action": "error", "message": "Failed to create a valid automation plan."}