# screen_perception.py

import pyautogui
import pytesseract
from config import TESSERACT_PATH

# Configure Tesseract OCR from our central config file
try:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    print("Tesseract OCR path configured successfully.")
except Exception as e:
    print(f"Error configuring Tesseract: {e}. Please check the TESSERACT_PATH in config.py")

def get_screen_text_with_ocr() -> str:
    """
    Captures the entire screen and extracts text using Tesseract OCR.
    Returns the extracted text as a string.
    """
    try:
        screenshot = pyautogui.screenshot()
        text = pytesseract.image_to_string(screenshot)
        print("Screen captured and OCR performed.")
        return text
    except FileNotFoundError:
        print("OCR Error: Tesseract executable not found. Please ensure the path in config.py is correct.")
        return "Error: Tesseract is not installed or the path is incorrect."
    except Exception as e:
        print(f"An unexpected error occurred during OCR: {e}")
        return f"Error during OCR: {e}"