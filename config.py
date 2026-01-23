import os

# -----------------------------
# GOOGLE SERVICE ACCOUNT SETUP
# -----------------------------
# Full path to your JSON key file
SERVICE_ACCOUNT_PATH = r"C:\Users\husai\Desktop\CODES\Project\sara-473219-d84b1e9e5a57.json"

# Set environment variable so Google SDK can locate the service account
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_PATH

# Project ID from GCP
GCP_PROJECT_ID = "sara-473219"

# --- API Keys ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", None)
PICOVOICE_ACCESS_KEY = "9c7RE3aYRyioBNY83E44C+zQeZ7IGVT92y3kyJMnFznLLcI3WhxC8Q=="
ELEVENLABS_API_KEY = "sk_98b4aef2c5f2e9e9b60a469562c9c0304f37fee7fe66e4a1"

# --- Local Model Configuration ---
OFFLINE_MODEL = "gemma:2b-instruct"

# --- Paths ---
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
SARA_WAKE_WORD_PATH = "Hey-SARA_en_windows_v3_0_0.ppn"  # Use your exact .ppn filename

# --- Application Executables ---
APP_EXECUTABLES = {
    "notepad": "notepad.exe",
    "paint": "mspaint.exe",
    "calc": "calc.exe"
}

# --- Voice Service Configuration ---
STT_ENGINE = "google"
WHISPER_MODEL = "base.en"

# --- ElevenLabs Voice Selection ---
ELEVENLABS_VOICE_NAME = "Sarah"

ELEVENLABS_VOICES = {
    "Rachel": "21m00Tcm4TlvDq8ikWAM",
    "Clyde": "2EiwWnXFnvU5JabPnv8n",
    "Roger": "CwhRBWXzGAHq8TQ4Fs17",
    "Sarah": "EXAVITQu4vr4xnSDxMaL",
    "Laura": "FGY2WhTYpPnrIDTdsKH5",
    "Thomas": "GBv7mTt0atIp3Br8iCZE",
    "Charlie": "IKne3meq5aSn9XLyUdCD",
    "George": "JBFqnCBsd6RMkjVDRZzb",
    "Callum": "N2lVS1w4EtoT3dr4eOWO",
    "River": "SAz9YHcvj6GT2YYXdXww",
    "Harry": "SOYHLrjzK2X1ezoPC6cr",
    "Liam": "TX3LPaxmHKxFdv7VOQHJ",
    "Alice": "Xb7hH8MSUJpSbSDYk0k2",
    "Matilda": "XrExE9yKIg1WjnnlVkGX",
    "Will": "bIHbv24MWmeRgasZH58o",
    "Jessica": "cgSgspJ2msm6clMCkdW9",
    "Eric": "cjVigY5qzO86Huf0OWal",
    "Chris": "iP95p4xoKVk53GoZ742B",
    "Brian": "nPczCjzI2devNBz1zQrb",
    "Daniel": "onwK4e9ZLuTAKqWW03F9",
    "Lily": "pFZP5JQG7iQjIQuC4Bku",
    "Bill": "pqHfZKP75CvOlQylNhV4"
}
