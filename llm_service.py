# llm_service.py

import google.generativeai as genai
import ollama
import json
import re
from config import OFFLINE_MODEL

# Configure the online model (uses service account from config.py)
try:
    genai.configure() 
    online_model = genai.GenerativeModel("gemini-1.5-flash-latest")
    print("Online model (Gemini 1.5 Flash) configured successfully.")
except Exception as e:
    print(f"Error configuring online model: {e}")
    online_model = None

def online_llm_text(prompt: str) -> str:
    if not online_model: return "Error: Online model is not configured."
    try:
        response = online_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error communicating with online model: {e}")
        return f"Error: Could not get a response. Details: {e}"

def get_intent(user_command: str, recalled_memories: list) -> str:
    prompt = f"""
    You are an expert intent router. Based on the user's command AND their recent memory,
    classify the command into ONE category: 'automation', 'screen_read', 'conversation', 'remember'.
    Recent Memory: {recalled_memories}
    User Command: "{user_command}"
    Respond with ONLY the single-word category name.
    """
    try:
        response = online_llm_text(prompt).strip().lower().replace("'", "").replace('"',"")
        print(f"Online LLM Intent Raw Response: '{response}'")
        if 'automation' in response: return 'automation'
        if 'screen_read' in response: return 'screen_read'
        if 'remember' in response: return 'remember'
        return 'conversation'
    except Exception as e:
        print(f"Error classifying intent online: {e}")
        return 'conversation'

def extract_facts_from_text(text_to_analyze: str) -> dict:
    prompt = f"""
    Analyze the user's statement and extract any personal facts (like name, age, college, etc.) into a JSON object.
    The keys should be snake_case. If no facts, return {{}}.
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
    context_str = json.dumps(context, indent=2)
    prompt = f"""
    You are an automation planner. Create a JSON plan.
    User's context: {context_str}
    User's command: "{user_command}"

    You MUST create a JSON object with "application", "action", and "sub_actions" keys.
    "application" MUST be lowercase.
    "sub_actions" MUST be a list of dictionaries with a "type" key.
    Valid "type" values are "type_text" and "save_file".
    Respond with ONLY the JSON.
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