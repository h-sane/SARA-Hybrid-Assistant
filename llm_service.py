# llm_service.py

import google.generativeai as genai
import ollama
import json
from config import GOOGLE_API_KEY, OFFLINE_MODEL

# --- Model Configuration ---
try:
    # Configure the online model (Gemini)
    genai.configure(api_key=GOOGLE_API_KEY)
    online_model = genai.GenerativeModel('gemini-1.5-flash-latest')
    print("Online model (Gemini Pro) configured successfully.")
except Exception as e:
    print(f"Error configuring online model: {e}")
    online_model = None

# --- Core LLM Interaction Functions ---

def online_llm_text(prompt: str) -> str:
    """Sends a prompt to the powerful online model (Gemini) for complex tasks."""
    if not online_model:
        return "Error: Online model is not configured."
    try:
        response = online_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error communicating with online model: {e}")
        return f"Error: Could not get a response from the online model. Details: {e}"

def offline_llm_text(prompt: str) -> str:
    """Sends a prompt to the local, private model (Ollama) for sensitive tasks."""
    try:
        response = ollama.chat(model=OFFLINE_MODEL, messages=[{'role': 'user', 'content': prompt}])
        return response['message']['content']
    except Exception as e:
        print(f"Error communicating with offline model: {e}")
        return f"Error: Could not get a response from the offline model. Is Ollama running? Details: {e}"

# --- Router and Planner Functions ---

def get_intent(user_command: str) -> str:
    """
    The Router: Final version with four intents, including 'remember'.
    """
    prompt = f"""
    You are an intent router. Classify the user's command into ONE of the following four categories:
    'automation', 'screen_read', 'conversation', or 'remember'.

    - 'automation': Controlling an application like opening files, typing text, or saving.
    - 'screen_read': Seeing, capturing, reading, or analyzing the screen's content.
    - 'remember': The user explicitly asks the assistant to remember a piece of information for later.
    - 'conversation': All other general questions, greetings, or chat.

    Here are some examples:
    - User command: "open notepad and write a new story" -> automation
    - User command: "what is on my screen right now?" -> screen_read
    - User command: "Remember that my project deadline is October 25th" -> remember
    - User command: "what is the capital of india?" -> conversation

    Now, classify the following command:
    User command: "{user_command}"
    """
    try:
        response = online_llm_text(prompt).strip().lower()
        print(f"LLM Intent Raw Response: '{response}'")

        if 'automation' in response:
            return 'automation'
        elif 'screen_read' in response:
            return 'screen_read'
        elif 'remember' in response:
            return 'remember'
        else:
            return 'conversation'
            
    except Exception as e:
        print(f"Error classifying intent: {e}")
        return 'conversation'

def get_automation_plan(user_command: str) -> dict:
    """
    The Planner: Uses the powerful online model to create a structured JSON plan for automation.
    """
    prompt = f"""
    You are an automation planner. Convert the user's request into a structured JSON object.
    The JSON object MUST have these top-level keys: "application", "action", "sub_actions".
    - "application": The name of the application to be used (e.g., "notepad").
    - "action": A brief description of the overall goal (e.g., "create and save a file").
    - "sub_actions": A list of specific steps, which can be "type_text" or "save_file".

    Example: User command: 'in notepad, write "hello" and save it as my_file.txt'
    {{
        "application": "notepad",
        "action": "create and save a file",
        "sub_actions": [
            {{"type": "type_text", "text": "hello"}},
            {{"type": "save_file", "filename": "my_file.txt"}}
        ]
    }}

    Now, create the JSON plan for the following user command. Respond with ONLY the JSON object.
    User command: "{user_command}"
    """
    try:
        response_str = online_llm_text(prompt)
        response_str_clean = response_str.strip().replace('```json\n', '').replace('```', '')
        return json.loads(response_str_clean)
    except Exception as e:
        print(f"Error parsing automation plan: {e}")
        return {"action": "error", "message": "Failed to create a valid automation plan."}