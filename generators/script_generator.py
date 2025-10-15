import json
from typing import Dict, List
import google.generativeai as genai
from pydantic import BaseModel, Field
from config import Config

genai.configure(api_key=Config.GEMINI_API_KEY)

class TimestampedSegment(BaseModel):
    start_time: float = Field(description="Start time in seconds")
    end_time: float = Field(description="End time in seconds")
    text: str = Field(description="Voice script text for this segment")
    scene_description: str = Field(description="What should be animated in this segment")

class VoiceScript(BaseModel):
    topic: str
    total_duration: float
    segments: List[TimestampedSegment]

class ScriptGenerator:
    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name=Config.GEMINI_MODEL,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": VoiceScript
            }
        )
    
    def generate_script(self, topic: str, tone: str, language: str) -> Dict:
        """Generate voice script with timestamps"""
        
        tone_instructions = {
            "formal": "Use formal, academic language. Be precise and technical.",
            "funny": "Use casual language with humor, analogies, and fun examples.",
            "storytelling": "Use narrative style, build suspense, use metaphors and engaging storytelling."
        }
        
        prompt = f"""Generate an educational video script for: "{topic}"

Language: {language}
Tone: {tone} - {tone_instructions.get(tone, '')}

Create a 30-45 second script divided into 5-7 segments with timestamps.
Each segment should have:
1. start_time and end_time (in seconds)
2. text: What the narrator says (in {language})
3. scene_description: What animation should appear (in English for Manim code generation)

Make segments logical and flow naturally. Time segments appropriately for smooth narration.

For math topics, include specific formulas and equations to animate.
For science topics, include visual phenomena and processes.
"""
        
        response = self.model.generate_content(prompt)
        script_data = json.loads(response.text)
        
        # Save script
        script_path = Config.SCRIPTS_DIR / f"{topic[:30].replace(' ', '_')}.json"
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, indent=2, ensure_ascii=False)
        
        return script_data
