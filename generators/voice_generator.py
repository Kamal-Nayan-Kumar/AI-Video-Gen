from elevenlabs import ElevenLabs
from config import Config
from typing import Dict
import os

class VoiceGenerator:
    def __init__(self):
        self.client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)
    
    def generate_voice(self, script_data: Dict, language: str) -> str:
        """Generate voice audio from script"""
        
        # Combine all text segments
        full_text = " ".join([seg['text'] for seg in script_data['segments']])
        
        # Get voice ID
        voice_id = Config.VOICE_MAP.get(language.lower(), Config.VOICE_MAP["english"])
        
        # Generate audio
        audio = self.client.text_to_speech.convert(
            voice_id=voice_id,
            output_format="mp3_44100_128",
            text=full_text,
            model_id="eleven_multilingual_v2"
        )
        
        # Save audio
        topic_name = script_data['topic'][:30].replace(' ', '_')
        audio_path = Config.AUDIO_DIR / f"{topic_name}.mp3"
        
        with open(audio_path, 'wb') as f:
            for chunk in audio:
                f.write(chunk)
        
        return str(audio_path)
