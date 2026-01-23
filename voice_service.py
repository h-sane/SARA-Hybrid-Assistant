# voice_service.py

import os
import time
from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_NAME, ELEVENLABS_VOICES
from stt_engine import GoogleSTT
from elevenlabs import play
from elevenlabs.client import ElevenLabs
from gtts import gTTS
import pygame

class VoiceService:
    def __init__(self):
        try:
            # --- STT Engine ---
            self.stt_engine = GoogleSTT()

            # --- TTS Clients ---
            self.elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            
            # Initialize pygame mixer for gTTS playback
            pygame.mixer.init()

            print(f"VoiceService initialized.")

        except Exception as e:
            print(f"Error initializing VoiceService: {e}")

    def listen(self) -> str | None:
        """Directly listens for a command using Google STT."""
        if self.stt_engine:
            return self.stt_engine.transcribe()
        return None

    def speak(self, text: str, engine: str = "google"):
        """
        Speaks the text using the specified engine.
        :param text: Text to speak
        :param engine: 'google' or 'elevenlabs'
        """
        print(f"SARA ({engine}) says: '{text}'")
        
        if engine == "elevenlabs":
            self._speak_elevenlabs(text)
        else:
            self._speak_google(text)

    def _speak_elevenlabs(self, text: str):
        try:
            voice_id = ELEVENLABS_VOICES.get(ELEVENLABS_VOICE_NAME, "EXAVITQu4vr4xnSDxMaL")
            audio = self.elevenlabs_client.text_to_speech.convert(
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                text=text
            )
            play(audio)
        except Exception as e:
            print(f"ElevenLabs TTS Error: {e}")
            print("Falling back to Google TTS...")
            self._speak_google(text)

    def _speak_google(self, text: str):
        try:
            tts = gTTS(text=text, lang='en')
            filename = "temp_speech.mp3"
            tts.save(filename)
            
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            pygame.mixer.music.unload()
            os.remove(filename)
        except Exception as e:
            print(f"Google TTS Error: {e}")

    def cleanup(self):
        pygame.mixer.quit()