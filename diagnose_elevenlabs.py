# diagnose_elevenlabs.py
import elevenlabs
from elevenlabs.client import ElevenLabs
import os

# A dummy key is fine for this test, as we are not making an API call,
# just inspecting the object.
DUMMY_KEY = "1234567890"

print("--- ElevenLabs Diagnostic Report ---")

# 1. Check the installed version
try:
    print(f"Installed Version: {elevenlabs.__version__}")
except Exception as e:
    print(f"Could not determine version: {e}")

# 2. Check the file location
try:
    print(f"File Location: {elevenlabs.__file__}")
except Exception as e:
    print(f"Could not determine file location: {e}")

# 3. Inspect the Client object's attributes
try:
    print("\n--- Inspecting the 'ElevenLabs' client object ---")
    client = ElevenLabs(api_key=DUMMY_KEY)
    attributes = dir(client)
    
    print("Available attributes/methods on the client object:")
    # Print attributes in columns for readability
    for i in range(0, len(attributes), 4):
        print(" | ".join(f"{attr:<30}" for attr in attributes[i:i+4]))
    
    if 'generate' in attributes:
        print("\n[SUCCESS] The '.generate()' method was found on the client object.")
    else:
        print("\n[FAILURE] The '.generate()' method was NOT found. This is the source of the error.")
except Exception as e:
    print(f"\nError during client inspection: {e}")

print("\n--- End of Report ---")