# stt_engine.py

import os
import time
import tempfile
import speech_recognition as sr
import warnings
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime

# Import moonshine_onnx module-level transcribe function
try:
    import moonshine_onnx
except ImportError:
    print("Warning: useful-moonshine-onnx not installed.")
    moonshine_onnx = None

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)

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
    """Online STT engine using Google Web Speech API."""
    def __init__(self):
        print("Initializing Google STT Engine...")
        self.recognizer = sr.Recognizer()

    def transcribe(self) -> tuple[str | None, STTMetrics | None]:
        with sr.Microphone() as source:
            print("Listening for command (Google)...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                # 5 second pause threshold
                self.recognizer.pause_threshold = 5.0
                
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                
                audio_duration = len(audio.frame_data) / (audio.sample_rate * audio.sample_width)
                print(f"Transcribing with Google... (Audio: {audio_duration:.2f}s)")
                
                start_time = time.time()
                response = self.recognizer.recognize_google(audio, show_all=True)
                end_time = time.time()
                
                processing_time = end_time - start_time
                rtf = processing_time / audio_duration if audio_duration > 0 else 0
                
                text = ""
                confidence = None
                
                if isinstance(response, dict) and 'alternative' in response:
                    best = response['alternative'][0]
                    text = best.get('transcript', "")
                    confidence = best.get('confidence')

                if text:
                    print(f"Google: '{text}' (RTF: {rtf:.2f})")
                    metrics = STTMetrics("google_web_speech", audio_duration, processing_time, rtf, confidence)
                    return text.lower(), metrics
                
                return None, None

            except Exception as e:
                print(f"Google STT Error: {e}")
                return None, None


class MoonshineSTT(STTEngine):
    """Offline STT using Moonshine (Tiny) via ONNX.
    
    Uses moonshine_onnx.transcribe(audio_path, model_name) function.
    """
    def __init__(self):
        print("Initializing Moonshine STT (Tiny)...")
        if moonshine_onnx is None:
            raise ImportError("useful-moonshine-onnx is not installed.")
        
        self.model_name = "moonshine/tiny"
        self.recognizer = sr.Recognizer()
        print("Moonshine STT ready.")

    def transcribe(self) -> tuple[str | None, STTMetrics | None]:
        with sr.Microphone() as source:
            print("Listening for command (Moonshine)...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                # 5 second pause threshold
                self.recognizer.pause_threshold = 5.0
                
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=20)
                
                audio_duration = len(audio.frame_data) / (audio.sample_rate * audio.sample_width)
                print(f"Transcribing with Moonshine... (Audio: {audio_duration:.2f}s)")
                
                # Save audio to temporary WAV file (required by moonshine_onnx.transcribe)
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                    tmp_filename = tmp_file.name
                
                with open(tmp_filename, "wb") as f:
                    f.write(audio.get_wav_data())
                
                start_time = time.time()
                
                # Official API: moonshine_onnx.transcribe(audio_path, model_name)
                # Returns a list of strings
                result = moonshine_onnx.transcribe(tmp_filename, self.model_name)
                
                end_time = time.time()
                
                # Cleanup temp file
                try:
                    os.remove(tmp_filename)
                except:
                    pass
                
                processing_time = end_time - start_time
                rtf = processing_time / audio_duration if audio_duration > 0 else 0
                
                # Result is a list, get first element
                text = result[0] if result else ""
                
                if text:
                    text = text.strip()
                    print(f"Moonshine: '{text}' (RTF: {rtf:.2f})")
                    metrics = STTMetrics("moonshine_tiny", audio_duration, processing_time, rtf, None)
                    return text.lower(), metrics
                
                return None, None
                
            except Exception as e:
                print(f"Moonshine Error: {e}")
                # Cleanup on error
                try:
                    if 'tmp_filename' in locals() and os.path.exists(tmp_filename):
                        os.remove(tmp_filename)
                except:
                    pass
                return None, None
