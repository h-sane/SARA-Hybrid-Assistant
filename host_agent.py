# host_agent.py

import json
import time
from threading import Thread
from llm_service import get_intent, get_automation_plan, online_llm_text, extract_facts_from_text
from knowledge_base_manager import MemoryStream, get_user_details, update_user_details
from robust_notepad_helpers import (launch_and_focus, find_edit_control, get_control_text, 
                                    type_into_edit, save_notepad_file)
from screen_perception import get_screen_text_with_ocr

# --- The Definitive NotepadAgent ---
class NotepadAgent:
    """A truly robust agent that uses the new helper functions."""
    def __init__(self, app_connection, main_window):
        self.app = app_connection
        self.main_window = main_window

    def handle_subtask(self, sub_actions: list):
        print(f"Definitive NotepadAgent executing: {sub_actions}")
        try:
            edit_control = find_edit_control(self.main_window)
        except RuntimeError as e:
            print(f"Could not proceed with Notepad automation: {e}")
            return False

        for action in sub_actions:
            action_type = action.get("type")
            if action_type == "type_text":
                current_text = get_control_text(edit_control)
                if current_text.strip() != "":
                    print("Notepad already has content. Creating new file via menu.")
                    self.main_window.menu_select("File->New")
                    time.sleep(1)
                    edit_control = find_edit_control(self.main_window)
                
                text_to_type = action.get("text", "")
                print("Typing text...")
                type_into_edit(edit_control, text_to_type)
                time.sleep(0.5)

            elif action_type == "save_file":
                filename = action.get("filename", "untitled.txt")
                print(f"Saving file as {filename}...")
                save_notepad_file(self.app, self.main_window, filename)
        return True

# --- HostAgent Class ---
class HostAgent:
    def __init__(self):
        self.app_agent_map = {"notepad": NotepadAgent}
        self.memory = MemoryStream()
        print("HostAgent initialized with advanced MemoryStream.")

    def _execute_automation_plan(self, plan: dict):
        application_name = plan.get("application", "").lower()
        if not application_name: return

        app_connection, main_window = launch_and_focus(application_name=application_name)
        
        if app_connection and main_window:
            agent_class = self.app_agent_map.get(application_name)
            if agent_class:
                agent = agent_class(app_connection, main_window)
                agent.handle_subtask(plan.get("sub_actions", []))
                self.memory.add_memory(f"I successfully performed an action in {application_name}.")
            else:
                print(f"No specific agent for '{application_name}'.")
        else:
            print(f"Could not continue automation because app launch/focus failed.")
        print(f"BACKGROUND THREAD: Automation for '{application_name}' finished.")

    def process_user_command(self, command: str) -> dict:
        print(f"\nHostAgent: Processing command: '{command}'")
        recalled_memories = self.memory.recall_memories(command, num_results=2)
        print(f"HostAgent: Recalled memories: {recalled_memories}")
        intent = get_intent(command, recalled_memories)
        print(f"HostAgent: Final Intent classified as '{intent}'")

        if intent == 'remember':
            new_facts = extract_facts_from_text(command)
            if new_facts:
                update_user_details(new_facts)
                memory_summary = f"I learned new facts about the user: {list(new_facts.keys())}"
                self.memory.add_memory(memory_summary)
                response = f"Okay, I've remembered that. Details updated: {list(new_facts.keys())}"
            else:
                response = "I couldn't find any specific facts to remember."
            return {"type": "sync", "response": response}

        elif intent == 'automation':
            user_context = get_user_details()
            plan = get_automation_plan(command, context=user_context)
            print(f"HostAgent: Automation plan created with context: {plan}")
            if plan.get("action") == "error":
                return {"type": "sync", "response": plan.get("message")}
            thread = Thread(target=self._execute_automation_plan, args=(plan,))
            thread.start()
            return {"type": "async", "response": "Acknowledged, Master. Starting your task."}

        elif intent == 'screen_read':
            text = get_screen_text_with_ocr()
            prompt = f'Context: {recalled_memories}. Summarize this screen text: "{text[:2000]}"'
            summary = online_llm_text(prompt)
            return {"type": "sync", "response": summary}

        else: # conversation
            prompt = f'Context: {recalled_memories}. Respond to the user: "{command}"'
            response = online_llm_text(prompt)
            return {"type": "sync", "response": response}