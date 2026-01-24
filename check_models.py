import google.generativeai as genai
import os
from config import SERVICE_ACCOUNT_PATH

# Set environment variable so Google SDK can locate the service account
# Creating a fresh setup to match what the app does
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_PATH

print(f"Using Service Account: {SERVICE_ACCOUNT_PATH}")

try:
    genai.configure()
    print("Listing available models that support generateContent:")
    found_any = False
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
            found_any = True
    
    if not found_any:
        print("No models found that support generateContent.")

except Exception as e:
    print(f"Error listing models: {e}")
