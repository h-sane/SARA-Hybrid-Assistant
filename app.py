# app.py

# This script is now the main entry point for the SARA Voice Copilot.
# It initializes all services and runs the main voice loop.

from host_agent import HostAgent
from voice_service import VoiceService

def main():
    """The main application loop for the SARA Voice Copilot."""
    print("Initializing SARA...")
    
    # Create a single instance of the brain and the voice
    # The initialization of these classes will print status messages.
    host_agent = HostAgent()
    voice_service = VoiceService()
    
    print("\n--- SARA is now running in the background. ---")
    print("--- Say 'Hey SARA' followed by your command. ---")

    try:
        while True:
            # 1. Listen for the wake word
            if voice_service.listen_for_wake_word():
                
                # 2. Listen for the actual command and transcribe it
                command_text = voice_service.listen_for_command()

                if command_text:
                    # 3. Process the command with the agent's brain
                    response_data = host_agent.process_user_command(command_text)
                    
                    # 4. Speak the agent's response
                    response_text = response_data.get("response")
                    if response_text:
                        voice_service.speak(response_text)

    except KeyboardInterrupt:
        print("\nShutting down SARA...")
    finally:
        # Clean up all audio resources gracefully
        voice_service.cleanup()

if __name__ == '__main__':
    main()