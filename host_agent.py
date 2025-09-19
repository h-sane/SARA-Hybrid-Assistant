# host_agent.py

import json
import time
from threading import Thread

# --- Local Component Imports ---
from llm_service import get_intent, get_automation_plan, online_llm_text
from knowledge_base_manager import MemoryStream, get_user_details, update_contact
from desktop_automation import launch_and_focus, type_text, press_key, hotkey
from screen_perception import get_screen_text_with_ocr

# --- AppAgent Classes (Remain the same) ---
class AppAgent:
    def execute_action(self, action_type: str, kwargs: dict):
        action_map = {"type_text": type_text, "press_key": press_key, "hotkey": hotkey}
        func = action_map.get(action_type)
        if func: return func(**kwargs)
        else: print(f"Unknown action type for AppAgent: {action_type}"); return False

class NotepadAgent(AppAgent):
    def handle_subtask(self, sub_actions: list):
        for action in sub_actions:
            action_type = action.get("type")
            if action_type == "type_text":
                self.execute_action("type_text", {"text": action.get("text", "")}); time.sleep(0.5)
            elif action_type == "save_file":
                filename = action.get("filename", "untitled.txt")
                self.execute_action("hotkey", {"keys": ['ctrl', 's']}); time.sleep(1)
                self.execute_action("type_text", {"text": filename}); time.sleep(0.5)
                self.execute_action("press_key", {"key": 'enter'}); time.sleep(1)
        return True

# --- HostAgent Class (The Central Orchestrator) ---
class HostAgent:
    def __init__(self):
        self.app_agent_map = {"notepad": NotepadAgent}
        # Activate SARA's memory on startup
        self.memory_stream = MemoryStream()
        print("HostAgent initialized and ready with active Memory Stream.")

    def _execute_automation_plan(self, plan: dict):
        application_name = plan.get("application")
        if not application_name: print("Automation plan is missing an application."); return

        app_connection = launch_and_focus(application_name=application_name)
        if app_connection:
            time.sleep(1)
            agent_class = self.app_agent_map.get(application_name.lower())
            if agent_class:
                agent = agent_class()
                agent.handle_subtask(plan.get("sub_actions", []))
            # After a successful action, create a memory of it.
            self.memory_stream.add_memory(f"I recently performed the action '{plan.get('action')}' in the application '{application_name}'.")
        else:
            print(f"Could not continue automation because app launch/focus failed.")
        print(f"BACKGROUND THREAD: Automation for '{application_name}' finished.")

    def process_user_command(self, command: str) -> dict:
        print(f"\nHostAgent: Processing command: '{command}'")
        
        # Step 1: Recall relevant memories before doing anything else.
        recalled_memories = self.memory_stream.recall_memories(query_text=command, num_results=1)
        context_string = " ".join(recalled_memories)
        print(f"HostAgent: Recalled context: '{context_string}'")

        # Step 2: Use the recalled context to get a more accurate intent.
        intent_command = f"Relevant context: {context_string}\n\nUser command: {command}"
        intent = get_intent(intent_command)
        print(f"HostAgent: Intent classified as '{intent}'")

        # Step 3: Route the command based on its classified intent.
        if intent == 'remember':
            self.memory_stream.add_memory(command)
            return {"type": "sync", "response": "OK, I will remember that."}

        elif intent == 'conversation':
            prompt = f"Based on this context: '{context_string}', answer the user's question: '{command}'"
            response = online_llm_text(prompt)
            return {"type": "sync", "response": response}

        elif intent == 'screen_read':
            text = get_screen_text_with_ocr()
            prompt = f"Based on this context: '{context_string}' and the following text from my screen, provide a helpful summary. Screen text: \n\n{text[:2000]}"
            summary = online_llm_text(prompt)
            return {"type": "sync", "response": f"Here's what I see: {summary}"}

        elif intent == 'automation':
            plan_command = f"Relevant context: {context_string}\n\nUser command: {command}"
            plan = get_automation_plan(plan_command)
            print(f"HostAgent: Automation plan created: {plan}")

            if plan.get("action") == "error": return {"type": "sync", "response": plan.get("message")}
            
            thread = Thread(target=self._execute_automation_plan, args=(plan,))
            thread.start()
            return {"type": "async", "response": "Acknowledged, Master. I'm starting your automation task."}
        
        else:
            return {"type": "sync", "response": "I'm not sure how to handle that intent."}