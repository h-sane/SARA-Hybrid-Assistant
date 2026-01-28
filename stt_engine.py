# stt_engine.py

import speech_recognition as sr
from dataclasses import dataclass, field
from datetime import datetime
import time

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
                self.recognizer.pause_threshold = 2.0
                # Capture audio
                start_listen = time.time()
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                # end_listen = time.time() # Not used for processing metrics directly, but useful context
                
                # Calculate Audio Duration
                # frame_data is bytes, sample_width is bytes per sample, sample_rate is samples per second
                audio_duration = len(audio.frame_data) / (audio.sample_rate * audio.sample_width)
                
                print(f"Transcribing with Google... (Audio duration: {audio_duration:.2f}s)")
                
                start_process = time.time()
                # Use show_all=True to get structure with confidence if available
                # Note: recognize_google with show_all=True returns dict or list
                response = self.recognizer.recognize_google(audio, show_all=True)
                end_process = time.time()
                
                processing_time = end_process - start_process
                rtf = processing_time / audio_duration if audio_duration > 0 else 0
                
                text = None
                confidence = None
                
                if isinstance(response, dict):
                    # dict format: {'alternative': [{'transcript': '...', 'confidence': 0.9}, ...], 'final': True}
                    alternatives = response.get('alternative', [])
                    if alternatives:
                        best_match = alternatives[0]
                        text = best_match.get('transcript')
                        confidence = best_match.get('confidence')
                elif isinstance(response, list) and len(response) > 0:
                     # older versions might return list
                     # just in case usually it's dict
                     pass
                else: 
                     # Sometimes it returns empty list [] if no speech found
                     pass

                # If show_all=True returns None or empty, or we failed to parse
                if not text and not isinstance(response, (dict, list)):
                    # Fallback or maybe it was just raw string if show_all was False (but we set True)
                    # Actually if show_all=True and it fails to recognize, it usually throws UnknownValueError or returns []
                    pass

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
                    print("Google returned no text.")
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