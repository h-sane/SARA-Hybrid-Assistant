# host_agent.py

import json
import time
from threading import Thread

# --- Local Component Imports ---
from llm_service import get_intent, get_automation_plan, online_llm_text
from knowledge_base_manager import get_user_details
from desktop_automation import launch_and_focus, type_text, press_key, hotkey
from screen_perception import get_screen_text_with_ocr

# --- AppAgent Classes (Application Specialists) ---

class AppAgent:
    """Base class for all specialized application agents."""
    def execute_action(self, action_type: str, kwargs: dict):
        action_map = {
            "type_text": type_text,
            "press_key": press_key,
            "hotkey": hotkey
        }
        func = action_map.get(action_type)
        if func:
            return func(**kwargs)
        else:
            print(f"Unknown action type for AppAgent: {action_type}")
            return False

class NotepadAgent(AppAgent):
    """An agent that specializes in controlling Notepad."""
    def handle_subtask(self, sub_actions: list):
        print(f"NotepadAgent received sub_actions: {sub_actions}")
        for action in sub_actions:
            action_type = action.get("type")
            if action_type == "type_text":
                self.execute_action("type_text", {"text": action.get("text", "")})
                time.sleep(0.5)
            elif action_type == "save_file":
                filename = action.get("filename", "untitled.txt")
                print(f"NotepadAgent: Saving file as {filename}...")
                self.execute_action("hotkey", {"keys": ['ctrl', 's']})
                time.sleep(1) # Wait for save dialog
                self.execute_action("type_text", {"text": filename})
                time.sleep(0.5)
                self.execute_action("press_key", {"key": 'enter'})
                time.sleep(1)
        return True

# --- HostAgent Class (The Central Orchestrator) ---

class HostAgent:
    def __init__(self):
        self.app_agent_map = {
            "notepad": NotepadAgent
        }
        print("HostAgent initialized and ready.")

    def _execute_automation_plan(self, plan: dict):
        """
        The private 'worker' function that runs an automation plan
        using the new direct launch and focus method.
        """
        application_name = plan.get("application")
        if not application_name:
            print("Automation plan is missing an application.")
            return

        print(f"HostAgent: Initiating automation for '{application_name}'...")
        
        # Use our new, reliable launch_and_focus function
        app_connection = launch_and_focus(application_name=application_name)

        if app_connection:
            time.sleep(1) # Small delay after focusing
            
            agent_class = self.app_agent_map.get(application_name.lower())
            if agent_class:
                agent = agent_class()
                # Pass the direct app_connection to the agent if needed in the future
                agent.handle_subtask(plan.get("sub_actions", []))
            else:
                print(f"No specific agent for '{application_name}'. Cannot execute sub-actions.")
        else:
            print(f"Could not continue automation because app launch/focus failed.")
        
        print(f"BACKGROUND THREAD: Automation for '{application_name}' finished.")

    def process_user_command(self, command: str) -> dict:
        """
        The main router logic that classifies intent and delegates tasks.
        """
        print(f"\nHostAgent: Processing command: '{command}'")
        
        # Step 1: Use the Router to classify the user's intent.
        intent = get_intent(command)
        print(f"HostAgent: Intent classified as '{intent}'")

        # Step 2: Route the command based on its classified intent.
        if intent == 'conversation':
            response = online_llm_text(command)
            return {"type": "sync", "response": response}

        elif intent == 'screen_read':
            text = get_screen_text_with_ocr()
            summary_prompt = f"Summarize the following text from my screen in a helpful way:\n\n{text[:2000]}"
            summary = online_llm_text(summary_prompt)
            return {"type": "sync", "response": f"Here's what I see on your screen: {summary}"}

        elif intent == 'automation':
            plan = get_automation_plan(command)
            print(f"HostAgent: Automation plan created: {plan}")

            if plan.get("action") == "error":
                return {"type": "sync", "response": plan.get("message")}

            # Launch the automation in a separate, non-blocking thread
            thread = Thread(target=self._execute_automation_plan, args=(plan,))
            thread.start()
            
            return {"type": "async", "response": "Acknowledged, Master. I'm starting your automation task."}
        
        else:
            return {"type": "sync", "response": "I'm not sure how to handle that intent."}