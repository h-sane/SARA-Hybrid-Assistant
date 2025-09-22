# host_agent.py

import json
import time
from threading import Thread

# --- Local Component Imports ---
from llm_service import get_intent, get_automation_plan, online_llm_text
from knowledge_base_manager import MemoryStream # Importing your advanced memory class
from desktop_automation import launch_and_focus, type_text, press_key, hotkey
from screen_perception import get_screen_text_with_ocr

# --- AppAgent Classes (Application Specialists) ---

class AppAgent:
    """Base class for all specialized application agents."""
    def execute_action(self, action_type: str, kwargs: dict):
        action_map = {"type_text": type_text, "press_key": press_key, "hotkey": hotkey}
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
                self.execute_action("hotkey", {"keys": ['ctrl', 's']})
                time.sleep(1)
                self.execute_action("type_text", {"text": filename})
                time.sleep(0.5)
                self.execute_action("press_key", {"key": 'enter'})
                time.sleep(1)
        return True

# --- HostAgent Class (The Central Orchestrator) ---

class HostAgent:
    def __init__(self):
        """Initializes the HostAgent and its memory systems."""
        self.app_agent_map = {"notepad": NotepadAgent}
        # UPGRADE: Initialize an instance of the advanced MemoryStream
        self.memory = MemoryStream()
        print("HostAgent initialized with advanced MemoryStream.")

    def _execute_automation_plan(self, plan: dict):
        """The private 'worker' function that runs an automation plan."""
        application_name = plan.get("application")
        if not application_name:
            print("Automation plan is missing an application.")
            return

        app_connection = launch_and_focus(application_name=application_name)

        if app_connection:
            time.sleep(1)
            agent_class = self.app_agent_map.get(application_name.lower())
            if agent_class:
                agent = agent_class()
                agent.handle_subtask(plan.get("sub_actions", []))
                
                # UPGRADE: SARA now remembers what it did.
                action_summary = f"I successfully performed an action in {application_name}."
                self.memory.add_memory(action_summary)
            else:
                print(f"No specific agent for '{application_name}'.")
        else:
            print(f"Could not continue automation because app launch/focus failed.")
        
        print(f"BACKGROUND THREAD: Automation for '{application_name}' finished.")

    def process_user_command(self, command: str) -> dict:
        """The main router logic that uses memory to enrich its decisions."""
        print(f"\nHostAgent: Processing command: '{command}'")
        
        # UPGRADE: Recall relevant memories before making a decision.
        recalled_memories = self.memory.recall_memories(command, num_results=2)
        print(f"HostAgent: Recalled memories: {recalled_memories}")

        intent = get_intent(command)
        print(f"HostAgent: Intent classified as '{intent}'")

        if intent == 'conversation':
            # UPGRADE: Enrich the prompt with recalled memories for context.
            prompt = f"""
            Based on this relevant context from my memory: {recalled_memories}
            Please provide a helpful and conversational response to the following user command: "{command}"
            """
            response = online_llm_text(prompt)
            return {"type": "sync", "response": response}

        elif intent == 'screen_read':
            text = get_screen_text_with_ocr()
            prompt = f"""
            Based on this relevant context from my memory: {recalled_memories}
            And the following text I found on the screen: "{text[:2000]}"
            Please provide a helpful summary and suggest a next action.
            """
            summary = online_llm_text(prompt)
            return {"type": "sync", "response": summary}

        elif intent == 'automation':
            # For automation, we currently don't enrich the planning prompt,
            # but this is where we would add context for multi-step tasks in the future.
            plan = get_automation_plan(command)
            print(f"HostAgent: Automation plan created: {plan}")

            if plan.get("action") == "error":
                return {"type": "sync", "response": plan.get("message")}

            thread = Thread(target=self._execute_automation_plan, args=(plan,))
            thread.start()
            
            return {"type": "async", "response": "Acknowledged, Master. Starting your task."}
        
        else:
            return {"type": "sync", "response": "I'm not sure how to handle that intent."}