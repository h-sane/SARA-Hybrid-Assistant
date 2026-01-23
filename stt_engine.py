# stt_engine.py

import os
import tempfile
import speech_recognition as sr
import whisper
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)

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
                self.recognizer.pause_threshold = 1.0  # Slightly faster response
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                print("Transcribing with Google...")
                text = self.recognizer.recognize_google(audio)
                print(f"Google transcribed: '{text}'")
                return text.lower()
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                return None
            except sr.RequestError as e:
                print(f"Google API request failed; {e}")
                return None

class WhisperSTT(STTEngine):
    """Offline STT engine using OpenAI Whisper (Small model) for accent robustness."""
    def __init__(self):
        print("Initializing Whisper STT Engine (Loading 'small' model)...")
        # Load the model. 'small' fits in ~2GB VRAM/RAM and is good for accents.
        self.model = whisper.load_model("small")
        self.recognizer = sr.Recognizer()
        print("Whisper Model loaded successfully.")

    def transcribe(self) -> str | None:
        with sr.Microphone() as source:
            print("Listening for command (Whisper)...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                # Capture audio using SpeechRecognition
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=20)
                
                # Save to a temporary wav file because Whisper expects a file path or array
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                    tmp_filename = tmp_file.name
                
                with open(tmp_filename, "wb") as f:
                    f.write(audio.get_wav_data())

                # Transcribe using Whisper
                print("Transcribing with Whisper (Local)...")
                result = self.model.transcribe(tmp_filename, fp16=False) # fp16=False for CPU safety
                text = result["text"].strip()
                
                if text:
                    print(f"Whisper transcribed: '{text}'")
                    # Cleanup
                    os.remove(tmp_filename)
                    return text.lower()
                
                os.remove(tmp_filename)
                return None

            except sr.WaitTimeoutError:
                return None
            except Exception as e:
                print(f"Whisper Transcription Error: {e}")
                # Try to clean up if error occurred before cleanup
                try:
                    if 'tmp_filename' in locals() and os.path.exists(tmp_filename):
                        os.remove(tmp_filename)
                except:
                    pass
                return None