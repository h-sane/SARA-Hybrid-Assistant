# app.py

import os
import json
import warnings
import tensorflow as tf

from host_agent import HostAgent
from voice_service import VoiceService
from llm_service import online_llm_text, offline_llm_text, get_intent, extract_facts_from_text, get_automation_plan

# Suppress TensorFlow logging
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
warnings.filterwarnings("ignore", category=FutureWarning)

def load_service_account():
    """Load Google service account key for Vertex AI"""
    service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not service_account_path or not os.path.exists(service_account_path):
        raise FileNotFoundError("Google service account JSON path not set or invalid.")
    return service_account_path

def main():
    print("Initializing SARA...")

    # Load Google credentials
    service_account_path = load_service_account()
    print(f"Using Google service account: {service_account_path}")

    # Initialize Host Agent
    host_agent = HostAgent()
    print("HostAgent initialized with advanced MemoryStream.")

    # Initialize voice service (Google STT + Sarah TTS)
    voice_service = VoiceService()
    print("VoiceService initialized. Using 'Google' STT and 'Sarah' TTS voice.")

    print("\n--- SARA is now running in the background. ---")
    print("--- Say 'Hey SARA' followed by your command. ---\n")

    voice_service.run_loop(host_agent)

if __name__ == "__main__":
    main()
