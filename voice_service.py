# voice_service.py

import struct
import pyaudio
import pvporcupine
from config import PICOVOICE_ACCESS_KEY, SARA_WAKE_WORD_PATH, ELEVENLABS_API_KEY, ELEVENLABS_VOICES, ELEVENLABS_VOICE_NAME
from stt_engine import GoogleSTT # UPDATED: We only need to import GoogleSTT now
from elevenlabs import play
from elevenlabs.client import ElevenLabs

class VoiceService:
    def __init__(self):
        try:
            # --- Wake Word Initialization ---
            self.porcupine = pvporcupine.create(
                access_key=PICOVOICE_ACCESS_KEY,
                keyword_paths=[SARA_WAKE_WORD_PATH]
            )
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )

            # --- STT Engine Selection (Simplified) ---
            # We now exclusively use the reliable Google STT engine.
            self.stt_engine = GoogleSTT()

            # --- TTS Engine Initialization ---
            self.tts_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

            print(f"VoiceService initialized. Using 'Google' STT and '{ELEVENLABS_VOICE_NAME}' TTS voice. Listening for 'Hey SARA'...")

        except Exception as e:
            print(f"Error initializing VoiceService: {e}")
            self.porcupine = None

    def listen_for_wake_word(self) -> bool:
        if not self.porcupine:
            return False
        try:
            pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
            audio_frame = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            keyword_index = self.porcupine.process(audio_frame)
            if keyword_index >= 0:
                print("\n--- Wake word detected! ---")
                return True
        except (IOError, struct.error):
            pass
        return False

    def listen_for_command(self) -> str | None:
        if self.stt_engine:
            return self.stt_engine.transcribe()
        return None

def speak(text: str, tts_client=None, voice_name=ELEVENLABS_VOICE_NAME, voices=ELEVENLABS_VOICES):
    """Converts text to speech using the specified voice.
    
    Args:
        text: The text to be spoken
        tts_client: Optional ElevenLabs client instance. If not provided, a new one will be created.
        voice_name: Name of the voice to use (default: from config)
        voices: Dictionary of available voices (default: from config)
    """
    print(f"SARA says: '{text}'")
    try:
        if tts_client is None:
            tts_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            
        voice_id = voices.get(voice_name)
        if not voice_id:
            print(f"Error: Voice '{voice_name}' not found. Using default 'Sarah'.")
            voice_id = "EXAVITQu4vr4xnSDxMaL"

        audio = tts_client.text_to_speech.convert(
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            text=text
        )
        
        play.play(audio)

    except Exception as e:
        print(f"An error occurred during TTS: {e}")

class VoiceService:

    def run_loop(self, host_agent):
        """Continuously listen for wake word, then command, and route to HostAgent."""
        try:
            while True:
                if self.listen_for_wake_word():
                    command = self.listen_for_command()
                    if command:
                        response_data = host_agent.process_user_command(command)
                        response_text = response_data.get("response") if isinstance(response_data, dict) else None
                        if response_text:
                            speak(response_text, self.tts_client)
        except KeyboardInterrupt:
            print("\nStopping listener...")
        finally:
            self.cleanup()

    def cleanup(self):
        if hasattr(self, 'porcupine') and self.porcupine:
            self.porcupine.delete()
        if hasattr(self, 'audio_stream') and self.audio_stream:
            self.audio_stream.close()
        if hasattr(self, 'pa') and self.pa:
            self.pa.terminate()