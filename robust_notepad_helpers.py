# robust_notepad_helpers.py
import time
import subprocess
from pywinauto import Application, Desktop
import pyautogui
import win32clipboard as clipboard
import win32con
from config import APP_EXECUTABLES

def launch_and_focus(application_name: str, timeout: int = 15):
    """Launches an app and connects to it by its process ID for reliability."""
    exe = APP_EXECUTABLES.get(application_name.lower(), f"{application_name}.exe")
    try:
        backend = "uia"
        name_lower = application_name.lower()

        # 0) If the app is already open, try to attach first (helps Notepad/UWP cases)
        try:
            if name_lower == "notepad":
                app = Application(backend=backend).connect(title_re=".*Notepad.*", timeout=2)
            else:
                app = Application(backend=backend).connect(path=exe, timeout=2)
            main_window = app.top_window()
            main_window.wait("ready", timeout=5)
            main_window.set_focus()
            print(f"Attached to existing '{application_name}' window: {main_window.window_text()}")
            return app, main_window
        except Exception:
            app = None  # proceed to launch

        # 1) Launch with pywinauto so it can track UI process properly
        print(f"Launching {application_name}...")
        app = Application(backend=backend).start(exe)
        print(f"Successfully launched process for '{exe}', pid={app.process}")

        # 2) Patiently wait for the window to appear (retry loop)
        total_wait = 0.0
        main_window = None
        while total_wait < timeout:
            try:
                if name_lower == "notepad":
                    # Prefer explicit Notepad window selection
                    main_window = app.window(title_re=".*Notepad.*")
                    if main_window.exists() and main_window.is_visible():
                        break
                # Generic fallback to whatever top window the app reports
                main_window = app.top_window()
                if main_window.exists() and main_window.is_visible():
                    break
            except Exception:
                pass
            time.sleep(0.5)
            total_wait += 0.5

        # 3) One more fallback: search all UI windows on the desktop (helps in multi-process cases)
        if not main_window or not (main_window.exists() and main_window.is_visible()):
            try:
                if name_lower == "notepad":
                    main_window = Desktop(backend=backend).window(title_re=".*Notepad.*")
                    main_window.wait("visible", timeout=5)
                else:
                    # As a last resort, pick the active window
                    main_window = Desktop(backend=backend).active()
            except Exception:
                main_window = None

        if not main_window:
            raise RuntimeError("No windows for that process could be found after waiting.")

        # 4) Finalize focus
        try:
            main_window.wait("ready", timeout=5)
        except Exception:
            # If 'ready' state isn't reliable, at least ensure it's visible
            main_window.wait("visible", timeout=5)
        main_window.set_focus()
        print(f"Connected to and focused window: {main_window.window_text()}")
        return app, main_window
    except Exception as e:
        print(f"Error launching/focusing '{application_name}': {e}")
        return None, None

def find_edit_control(window):
    """Robustly finds an Edit control on the provided window wrapper."""
    try:
        return window.child_window(control_type="Document").wrapper_object()
    except Exception:
        pass
    try:
        return window.child_window(class_name="RichEditD2DPT").wrapper_object()
    except Exception:
        pass
    try:
        return window.child_window(control_type="Edit").wrapper_object()
    except Exception:
        pass
    try:
        return window.child_window(class_name="Edit").wrapper_object()
    except Exception:
        pass
    raise RuntimeError("Could not locate an Edit control on the target window.")

def get_control_text(edit_wrapper):
    """Safely reads text from a control wrapper with fallbacks."""
    try:
        texts = edit_wrapper.texts()
        return "\n".join("".join(line) for line in texts)
    except Exception:
        return ""

def type_into_edit(edit_wrapper, text: str):
    """Types text using the most reliable method available."""
    print(f"Attempting to type/paste text into edit control. Text length: {len(text)} characters.")
    
    # 0) Preferred path: use the Windows clipboard (lossless), then paste
    try:
        print("Trying clipboard paste method...")
        # Put text on clipboard
        clipboard.OpenClipboard()
        clipboard.EmptyClipboard()
        clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
        clipboard.CloseClipboard()

        # Focus the target and paste
        try:
            edit_wrapper.set_focus()
            print("Edit control focused. Pasting via Ctrl+V...")
        except Exception as e:
            print(f"Could not focus edit control: {e}")
            pass
        time.sleep(0.1)
        edit_wrapper.type_keys('^v')  # Ctrl+V
        print("Clipboard paste completed successfully.")
        return True
    except Exception as e:
        print(f"Clipboard paste failed: {e}")
        # Ensure clipboard is closed if an error occurred
        try:
            clipboard.CloseClipboard()
        except Exception:
            pass

    # 1) Try direct set (fast and reliable when supported)
    try:
        print("Trying set_edit_text method...")
        if hasattr(edit_wrapper, "set_edit_text"):
            edit_wrapper.set_edit_text("")  # clear first to avoid mixing
            time.sleep(0.1)
            edit_wrapper.set_edit_text(text)
            print("set_edit_text completed successfully.")
            return True
    except Exception as e:
        print(f"set_edit_text failed: {e}")
        pass

    # 2) Try controlled typing via UIA with a small pause to avoid dropped characters
    try:
        print("Trying UIA type_keys method...")
        edit_wrapper.type_keys(text, with_spaces=True, with_newlines=True, pause=0.03)
        print("UIA type_keys completed successfully.")
        return True
    except Exception as e:
        print(f"UIA type_keys failed: {e}")
        pass

    # 3) Last resort: pyautogui typing with a slower interval
    try:
        print("Trying pyautogui write method...")
        pyautogui.write(text, interval=0.05)
        print("pyautogui write completed successfully.")
        return True
    except Exception as e:
        print(f"pyautogui write failed: {e}")
        return False

def save_notepad_file(app, window, filename: str):
    """Uses keyboard shortcut and handles the 'Save As' dialog robustly."""
    try:
        # Use Ctrl+S to open Save As dialog (more reliable than menu_select)
        window.type_keys('^s')
        time.sleep(1.5)  # Increased wait for dialog to appear

        # Try multiple strategies to locate the Save As dialog
        save_dialog = None
        try:
            save_dialog = app.window(title_re=r".*Save As.*")
            save_dialog.wait('visible', timeout=15)  # Increased timeout
        except Exception:
            try:
                from pywinauto import Desktop
                save_dialog = Desktop(backend="uia").window(title_re=r".*Save As.*")
                save_dialog.wait('visible', timeout=15)
            except Exception:
                save_dialog = None

        # Fallback: if Ctrl+S didn't work, try menu_select
        if not save_dialog:
            print("Ctrl+S failed to open dialog, trying menu_select...")
            try:
                window.menu_select("File->Save As...")
                time.sleep(1.5)
                save_dialog = app.window(title_re=r".*Save As.*")
                save_dialog.wait('visible', timeout=15)
            except Exception:
                try:
                    from pywinauto import Desktop
                    save_dialog = Desktop(backend="uia").window(title_re=r".*Save As.*")
                    save_dialog.wait('visible', timeout=15)
                except Exception:
                    save_dialog = None

        # Fallback: check if the active window is the Save As dialog
        if not save_dialog:
            try:
                from pywinauto import Desktop
                active_window = Desktop(backend="uia").active()
                if "save" in active_window.window_text().lower() or "as" in active_window.window_text().lower():
                    print(f"Using active window as Save As dialog: {active_window.window_text()}")
                    save_dialog = active_window
                else:
                    save_dialog = None
            except Exception:
                save_dialog = None

        if not save_dialog:
            # Debug: list all windows
            print("Available windows:")
            try:
                from pywinauto import Desktop
                for w in Desktop(backend="uia").windows():
                    try:
                        print(f"  - {w.window_text()}")
                    except Exception:
                        pass
            except Exception:
                pass
            raise RuntimeError("'Save As' dialog not found")

        # Locate the filename edit control robustly
        file_edit = None
        try:
            file_edit = save_dialog.child_window(control_type="Edit")
        except Exception:
            try:
                file_edit = save_dialog.child_window(class_name="Edit")
            except Exception:
                file_edit = None

        if not file_edit:
            raise RuntimeError("Filename edit control not found in 'Save As' dialog")

        # Set the filename
        try:
            file_edit.set_text(filename)
        except Exception:
            # Fallback to typing into the edit box
            file_edit.set_focus()
            time.sleep(0.2)
            pyautogui.write(filename, interval=0.05)

        time.sleep(0.4)

        # Click the Save button (try by control_type first, then class name)
        try:
            save_button = save_dialog.child_window(title="Save", control_type="Button")
        except Exception:
            save_button = save_dialog.child_window(title="Save", class_name="Button")
        try:
            save_button.click_input()
            print(f"Save command sent for {filename}.")
            return True
        except Exception:
            print("Button click failed, trying Enter key...")
            save_dialog.type_keys('{ENTER}')
            print(f"Save command sent for {filename} via Enter.")
            return True
    except Exception as e:
        print(f"Could not control the 'Save As' dialog. Error: {e}")
        return False