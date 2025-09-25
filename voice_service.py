# voice_service.py

import struct
import pyaudio
import pvporcupine
from config import (PICOVOICE_ACCESS_KEY, SARA_WAKE_WORD_PATH, STT_ENGINE, 
                    ELEVENLABS_API_KEY, ELEVENLABS_VOICES, ELEVENLABS_VOICE_NAME)
from stt_engine import WhisperSTT, GoogleSTT
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

            # --- STT Engine Selection ---
            if STT_ENGINE == "whisper":
                self.stt_engine = WhisperSTT()
            elif STT_ENGINE == "google":
                self.stt_engine = GoogleSTT()
            else:
                raise ValueError(f"Unsupported STT engine: {STT_ENGINE}")

            # --- TTS Engine Initialization ---
            self.tts_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

            print(f"VoiceService initialized. Using '{STT_ENGINE}' STT and '{ELEVENLABS_VOICE_NAME}' TTS voice. Listening for 'Hey SARA'...")

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

    def speak(self, text: str):
        """Converts text to speech using the voice selected in config.py."""
        print(f"SARA says: '{text}'")
        try:
            # --- DYNAMIC VOICE SELECTION ---
            # Look up the voice ID from our config dictionary using the selected name.
            voice_id = ELEVENLABS_VOICES.get(ELEVENLABS_VOICE_NAME)
            if not voice_id:
                print(f"Error: Voice '{ELEVENLABS_VOICE_NAME}' not found in config. Using default 'Sarah'.")
                voice_id = "EXAVITQu4vr4xnSDxMaL" # Fallback to Sarah's ID

            audio = self.tts_client.text_to_speech.convert(
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                text=text
            )
            
            # play is a module, so we call the play function within it
            play.play(audio)

        except Exception as e:
            print(f"An error occurred during TTS: {e}")

    def cleanup(self):
        if hasattr(self, 'porcupine') and self.porcupine:
            self.porcupine.delete()
        if hasattr(self, 'audio_stream') and self.audio_stream:
            self.audio_stream.close()
        if hasattr(self, 'pa') and self.pa:
            self.pa.terminate()

# --- Standalone Test ---
if __name__ == '__main__':
    print("Running VoiceService full loop test...")
    print("Say 'Hey SARA', then 'hello'. Press Ctrl+C to exit.")

    voice_service = VoiceService()
    try:
        if voice_service.porcupine:
            while True:
                if voice_service.listen_for_wake_word():
                    command = voice_service.listen_for_command()
                    if command:
                        print(f"--- Command to be processed by HostAgent: '{command}' ---")
                        if "hello" in command:
                            voice_service.speak("Hello, Master. I am ready for your command.")
                        else:
                            voice_service.speak("I have received your command.")
    except KeyboardInterrupt:
        print("\nStopping listener...")
    finally:
        voice_service.cleanup()