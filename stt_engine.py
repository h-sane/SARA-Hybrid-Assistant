# stt_engine.py

import speech_recognition as sr
import whisper
from config import WHISPER_MODEL
import tempfile
import os

class STTEngine:
    """Abstract base class for all STT engines."""
    def transcribe(self) -> str | None:
        raise NotImplementedError("This method should be implemented by subclasses.")

class WhisperSTT(STTEngine):
    """Offline STT engine using OpenAI's Whisper."""
    def __init__(self):
        print("Initializing Whisper STT Engine...")
        try:
            self.model = whisper.load_model(WHISPER_MODEL)
            self.recognizer = sr.Recognizer()
            print(f"Whisper model '{WHISPER_MODEL}' loaded successfully.")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            self.model = None

    def transcribe(self) -> str | None:
        if not self.model:
            return "Error: Whisper model not loaded."
        
        with sr.Microphone() as source:
            print("Listening for command (Whisper)...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                # Save audio to a temporary file for Whisper to process
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio_file:
                    tmp_audio_file.write(audio.get_wav_data())
                    tmp_audio_path = tmp_audio_file.name

                print("Transcribing with Whisper...")
                result = self.model.transcribe(tmp_audio_path, fp16=False)
                os.remove(tmp_audio_path) # Clean up the temporary file
                
                transcribed_text = result['text'].strip()
                print(f"Whisper transcribed: '{transcribed_text}'")
                return transcribed_text

            except sr.WaitTimeoutError:
                print("No command heard.")
                return None
            except Exception as e:
                print(f"An error occurred during Whisper transcription: {e}")
                if 'tmp_audio_path' in locals() and os.path.exists(tmp_audio_path):
                    os.remove(tmp_audio_path)
                return None

class GoogleSTT(STTEngine):
    """Online STT engine using Google Web Speech API."""
    def __init__(self):
        print("Initializing Google STT Engine...")
        self.recognizer = sr.Recognizer()

    def transcribe(self) -> str | None:
        with sr.Microphone() as source:
            print("Listening for command (Google)...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
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