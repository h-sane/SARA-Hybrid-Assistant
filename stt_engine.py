# stt_engine.py

import speech_recognition as sr
from dataclasses import dataclass, field
from datetime import datetime
import time
import os
import requests
from config import DEEPGRAM_API_KEY, SARVAM_API_KEY

metric_imports_success = True
try:
    from deepgram import DeepgramClient
except ImportError:
    print("Warning: deepgram-sdk not installed. DeepgramSTT will not work.")
    metric_imports_success = False

@dataclass
class STTMetrics:
    model_name: str
    audio_duration: float  # seconds
    processing_time: float # seconds
    rtf: float            # Real-Time Factor
    confidence: float | None
    timestamp: datetime = field(default_factory=datetime.now)

class STTEngine:
    """Abstract base class for STT engines."""
    def transcribe(self) -> tuple[str | None, STTMetrics | None]:
        raise NotImplementedError("This method should be implemented by subclasses.")

class GoogleSTT(STTEngine):
    """Online STT engine using Google Web Speech API for speed and accuracy."""
    def __init__(self):
        print("Initializing Google STT Engine...")
        self.recognizer = sr.Recognizer()

    def transcribe(self) -> tuple[str | None, STTMetrics | None]:
        with sr.Microphone() as source:
            print("Listening for command (Google)...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                self.recognizer.pause_threshold = 5.0
                # Capture audio
                start_listen = time.time()
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                
                # Calculate Audio Duration
                audio_duration = len(audio.frame_data) / (audio.sample_rate * audio.sample_width)
                
                print(f"Transcribing with Google... (Audio duration: {audio_duration:.2f}s)")
                
                start_process = time.time()
                # Use show_all=True to get structure with confidence if available
                response = self.recognizer.recognize_google(audio, show_all=True)
                end_process = time.time()
                
                processing_time = end_process - start_process
                rtf = processing_time / audio_duration if audio_duration > 0 else 0
                
                text = None
                confidence = None
                
                if isinstance(response, dict):
                    alternatives = response.get('alternative', [])
                    if alternatives:
                        best_match = alternatives[0]
                        text = best_match.get('transcript')
                        confidence = best_match.get('confidence')
                
                # If we got text, return it
                if text:
                    print(f"Google transcribed: '{text}' (Confidence: {confidence}, Time: {processing_time:.2f}s, RTF: {rtf:.2f})")
                    metrics = STTMetrics(
                        model_name="google_web_speech",
                        audio_duration=audio_duration,
                        processing_time=processing_time,
                        rtf=rtf,
                        confidence=confidence
                    )
                    return text.lower(), metrics
                else:
                    return None, None

            except sr.WaitTimeoutError:
                print("No command heard.")
                return None, None
            except sr.UnknownValueError:
                print("Could not understand the audio.")
                return None, None
            except sr.RequestError as e:
                print(f"Google API request failed; {e}")
                return None, None

class DeepgramSTT(STTEngine):
    """Deepgram Nova 3 STT Engine."""
    def __init__(self):
        print("Initializing Deepgram Nova 3 Engine...")
        if not DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY not found in config.")
        self.recognizer = sr.Recognizer()
        try:
             self.deepgram = DeepgramClient(api_key=DEEPGRAM_API_KEY)
             # Alternatively, if env var is set, just DeepgramClient() works too.
        except Exception as e:
            print(f"Failed to initialize Deepgram Client: {e}")
            self.deepgram = None

    def transcribe(self) -> tuple[str | None, STTMetrics | None]:
        if not self.deepgram:
            print("Deepgram client not initialized.")
            return None, None

        with sr.Microphone() as source:
            print("Listening for command (Deepgram Nova 3)...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                self.recognizer.pause_threshold = 5.0
                
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                audio_data = audio.get_wav_data()
                
                # Calculate Audio Duration
                audio_duration = len(audio.frame_data) / (audio.sample_rate * audio.sample_width)
                
                print(f"Transcribing with Deepgram Nova 3... (Audio duration: {audio_duration:.2f}s)")
                
                start_process = time.time()
                
                payload = {
                    "buffer": audio_data,
                }
                
                # Correct payload: Raw bytes, not a dictionary wrapper.
                # Verified via verify_payload_simple.py and signature inspection.
                response = self.deepgram.listen.v1.media.transcribe_file(
                    request=audio_data,
                    model="nova-3",
                    smart_format=True,
                    language="en",
                    punctuate=True
                )
                end_process = time.time()
                
                processing_time = end_process - start_process
                rtf = processing_time / audio_duration if audio_duration > 0 else 0
                
                # Extract transcript
                # Response structure: response.results.channels[0].alternatives[0].transcript
                transcript = response.results.channels[0].alternatives[0].transcript
                confidence = response.results.channels[0].alternatives[0].confidence
                
                if transcript:
                     print(f"Deepgram transcribed: '{transcript}' (Confidence: {confidence}, Time: {processing_time:.2f}s, RTF: {rtf:.2f})")
                     metrics = STTMetrics(
                        model_name="deepgram_nova_3",
                        audio_duration=audio_duration,
                        processing_time=processing_time,
                        rtf=rtf,
                        confidence=confidence
                     )
                     return transcript.lower(), metrics
                else:
                     print("Deepgram returned empty transcript.")
                     return None, None

            except sr.WaitTimeoutError:
                print("No command heard.")
                return None, None
            except Exception as e:
                print(f"Deepgram Error: {e}")
                return None, None

class SarvamSTT(STTEngine):
    """Sarvam AI STT Engine."""
    def __init__(self):
        print("Initializing Sarvam AI STT Engine...")
        if not SARVAM_API_KEY:
            raise ValueError("SARVAM_API_KEY not found in config.")
        self.api_key = SARVAM_API_KEY
        self.recognizer = sr.Recognizer()
        self.url = "https://api.sarvam.ai/speech-to-text"

    def transcribe(self) -> tuple[str | None, STTMetrics | None]:
        with sr.Microphone() as source:
            print("Listening for command (Sarvam AI)...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                self.recognizer.pause_threshold = 5.0
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                
                # Convert to WAV bytes
                audio_data = audio.get_wav_data()
                audio_duration = len(audio.frame_data) / (audio.sample_rate * audio.sample_width)
                
                print(f"Transcribing with Sarvam AI... (Audio duration: {audio_duration:.2f}s)")
                
                start_process = time.time()
                
                files = {
                    'file': ('speech.wav', audio_data, 'audio/wav')
                }
                data = {
                    'model': 'saarika:v2.5', 
                    # 'language_code': 'hi-IN' 
                }
                headers = {
                    'api-subscription-key': self.api_key
                }
                
                response = requests.post(self.url, files=files, data=data, headers=headers)
                end_process = time.time()
                
                processing_time = end_process - start_process
                rtf = processing_time / audio_duration if audio_duration > 0 else 0
                
                if response.status_code == 200:
                    result = response.json()
                    transcript = result.get('transcript', '')
                    
                    if transcript:
                        print(f"Sarvam transcribed: '{transcript}' (Time: {processing_time:.2f}s, RTF: {rtf:.2f})")
                        metrics = STTMetrics(
                            model_name="sarvam_ai",
                            audio_duration=audio_duration,
                            processing_time=processing_time,
                            rtf=rtf,
                            confidence=None 
                        )
                        return transcript.lower(), metrics
                    else:
                        print(f"Sarvam returned empty transcript. Response: {result}")
                        return None, None
                else:
                    print(f"Sarvam API Error: {response.status_code} - {response.text}")
                    return None, None

            except sr.WaitTimeoutError:
                print("No command heard.")
                return None, None
            except Exception as e:
                print(f"Sarvam Error: {e}")
                return None, None