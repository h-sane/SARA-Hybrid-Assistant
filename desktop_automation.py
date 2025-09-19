# desktop_automation.py

import pyautogui
import time
import subprocess
from pywinauto import Application

# A dictionary to map simple names to executable names
APP_EXECUTABLES = {
    "notepad": "notepad.exe",
    "chrome": "chrome.exe",
    "calculator": "calc.exe"
}

def launch_and_focus(application_name: str) -> Application:
    """
    Launches an application and connects to it using its process path.
    This is the most robust method for handling modern applications.
    """
    exe = APP_EXECUTABLES.get(application_name.lower(), f"{application_name}.exe")
    
    try:
        # Step 1: Launch the application using the most basic method.
        subprocess.Popen([exe])
        print(f"Successfully launched process for '{exe}'")
        time.sleep(2) # Give it a solid 2 seconds to initialize

        # Step 2: Connect to the application using the UIA backend and the executable path.
        # This is more reliable than searching for a window title.
        app = Application(backend="uia").connect(path=exe, timeout=10)
        
        # Step 3: Find the top window and set focus.
        main_window = app.top_window()
        main_window.set_focus()
        
        print(f"Successfully connected to and focused '{application_name}'")
        return app
        
    except Exception as e:
        print(f"Error launching or focusing '{application_name}': {e}")
        return None

def type_text(text: str, interval: float = 0.05) -> bool:
    """Simulates typing text using the keyboard."""
    try:
        pyautogui.write(text, interval=interval)
        print(f"Typed: '{text}'")
        return True
    except Exception as e:
        print(f"Error typing text: {e}")
        return False

def press_key(key: str) -> bool:
    """Simulates pressing a single key."""
    try:
        pyautogui.press(key)
        print(f"Pressed key: '{key}'")
        return True
    except Exception as e:
        print(f"Error pressing key '{key}': {e}")
        return False

def hotkey(keys: list) -> bool:
    """Simulates pressing a combination of keys."""
    try:
        pyautogui.hotkey(*keys)
        print(f"Pressed hotkey: {keys}")
        return True
    except Exception as e:
        print(f"Error pressing hotkey {keys}: {e}")
        return False