# host_agent.py

import json
import time
from threading import Thread
from llm_service import get_intent, get_automation_plan, online_llm_text, extract_facts_from_text
from knowledge_base_manager import MemoryStream, get_user_details, update_user_details, update_contact
from desktop_automation import launch_and_focus, type_text, press_key, hotkey
from screen_perception import get_screen_text_with_ocr

# --- AppAgent Classes ---
class AppAgent:
    def execute_action(self, action_type: str, kwargs: dict):
        action_map = {"type_text": type_text, "press_key": press_key, "hotkey": hotkey}
        func = action_map.get(action_type)
        if func: return func(**kwargs)
        return False

class NotepadAgent(AppAgent):
    """An agent that is now perfectly synced with the planner's simple schema."""
    def handle_subtask(self, sub_actions: list):
        print(f"NotepadAgent executing simple sub_actions: {sub_actions}")
        for action in sub_actions:
            action_type = action.get("type")
            if action_type == "type_text":
                self.execute_action("type_text", {"text": action.get("text", "")})
                time.sleep(0.5)
            elif action_type == "save_file":
                filename = action.get("filename", "untitled.txt")
                self.execute_action("hotkey", {"keys": ['ctrl', 's']})
                time.sleep(1.5)
                self.execute_action("type_text", {"text": filename})
                time.sleep(0.5)
                self.execute_action("press_key", {"key": 'enter'})
                time.sleep(1)
        return True

# --- HostAgent Class ---
class HostAgent:
    def __init__(self):
        self.app_agent_map = {"notepad": NotepadAgent}
        self.memory = MemoryStream()
        print("HostAgent initialized with advanced MemoryStream.")

    def _execute_automation_plan(self, plan: dict):
        application_name = plan.get("application", "").lower()
        if not application_name:
            print("Automation plan is missing an application.")
            return

        app_connection = launch_and_focus(application_name=application_name)
        if app_connection:
            time.sleep(1)
            agent_class = self.app_agent_map.get(application_name)
            if agent_class:
                agent = agent_class()
                agent.handle_subtask(plan.get("sub_actions", []))
                action_summary = f"I successfully performed an action in {application_name}."
                self.memory.add_memory(action_summary)
            else:
                print(f"No specific agent for '{application_name}'.")
        else:
            print(f"Could not continue automation because app launch/focus failed.")
        print(f"BACKGROUND THREAD: Automation for '{application_name}' finished.")

    def process_user_command(self, command: str) -> dict:
        print(f"\nHostAgent: Processing command: '{command}'")
        recalled_memories = self.memory.recall_memories(command, num_results=2)
        print(f"HostAgent: Recalled memories: {recalled_memories}")
        intent = get_intent(command)
        print(f"HostAgent: Intent classified as '{intent}'")

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