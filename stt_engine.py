# stt_engine.py

import speech_recognition as sr

class STTEngine:
    """Abstract base class for STT engines."""
    def transcribe(self) -> str | None:
        raise NotImplementedError("This method should be implemented by subclasses.")

class GoogleSTT(STTEngine):
    """Online STT engine using Google Web Speech API for speed and accuracy."""
    def __init__(self):
        print("Initializing Google STT Engine...")
        self.recognizer = sr.Recognizer()

    def transcribe(self) -> str | None:
        with sr.Microphone() as source:
            print("Listening for command (Google)...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                self.recognizer.pause_threshold = 2.0
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                print("Transcribing with Google...")
                text = self.recognizer.recognize_google(audio)
                print(f"Google transcribed: '{text}'")
                return text.lower()
            except sr.WaitTimeoutError:
                print("No command heard.")
                return None
            except sr.UnknownValueError:
                print("Could not understand the audio.")
                return None
            except sr.RequestError as e:
                print(f"Google API request failed; {e}")
                return None