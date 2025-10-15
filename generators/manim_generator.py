import json
import google.generativeai as genai
from typing import Dict
import re # import re for regex operations
from config import Config

genai.configure(api_key=Config.GEMINI_API_KEY)

class ManimGenerator:
    def __init__(self):
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
    
    def generate_manim_code(self, script_data: Dict, retry_count: int = 0) -> str:
        """Generate Manim code from script with retry on errors"""
        
        segments_text = "\n".join([
            f"- Time {seg['start_time']}-{seg['end_time']}s: {seg['scene_description']}"
            for seg in script_data['segments']
        ])
        
        prompt = f"""Generate Manim Community Edition Python code for this educational video:

Topic: {script_data['topic']}
Total Duration: {script_data['total_duration']} seconds

Scene Timeline:
{segments_text}

CRITICAL SYNTAX RULES:
1. Arc(start_angle=X, angle=Y, radius=Z) - Use 'angle' NOT 'end_angle'
2. Circle(radius=X, color=Y, fill_opacity=Z)
3. Text("text", font_size=X) - Use font_size, not size
4. MathTex(r"\\formula") - Always use raw strings for LaTeX
5. self.play() for animations, self.wait() for pauses
6. Import: from manim import *
7. Colors: BLUE, RED, GREEN, YELLOW, WHITE, BLACK (uppercase)
8. Directions: UP, DOWN, LEFT, RIGHT

CORRECT EXAMPLES:

from manim import *

class ExplainerScene(Scene):
    def construct(self):
        # Text example
        title = Text("Pythagorean Theorem", font_size=48, color=BLUE)
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))
        
        # Math example
        formula = MathTex(r"a^2 + b^2 = c^2", font_size=60)
        self.play(Write(formula))
        self.wait(2)
        
        # Shapes example
        triangle = Polygon(
            ORIGIN, RIGHT * 3, RIGHT * 3 + UP * 4,
            color=YELLOW, fill_opacity=0.3
        )
        self.play(Create(triangle))
        
        # Arc example (CORRECT)
        arc = Arc(start_angle=0, angle=PI/2, radius=1, color=GREEN)
        self.play(Create(arc))
        
        # Animation timing
        self.wait(2)  # Match segment duration

REQUIREMENTS:
1. Class name MUST be 'ExplainerScene'
2. Total duration should match {script_data['total_duration']}s using wait() calls
3. Use simple, reliable shapes: Text, MathTex, Circle, Square, Polygon, Arrow, Line
4. AVOID complex shapes that might have syntax errors
5. Keep animations smooth: FadeIn, FadeOut, Write, Create, Transform
6. Add colors for visual appeal
7. Use .animate.shift(), .animate.scale(), .animate.rotate() for movements
8. Synchronize timing with script segments

Generate ONLY executable Python code. No explanations. Start with 'from manim import *'"""
        
        try:
            response = self.model.generate_content(prompt)
            code = response.text.strip()
            
            # Use regex to robustly extract code blocks
            # This looks for content between ```python or ``` and the next ```
            match = re.search(r"```(?:python\n)?(.*?)```", code, re.DOTALL)
            if match:
                code = match.group(1).strip()
            else:
                # If no code block found, assume the entire response is code.
                # This could happen if the model doesn't wrap its code.
                pass
            
            # Basic validation
            required_elements = [
                "from manim import",
                "class ExplainerScene",
                "def construct(self):",
                "self.play(",
                "self.wait("
            ]
            
            for element in required_elements:
                if element not in code:
                    raise ValueError(f"Generated code missing required element: {element}")
            
            # Check for common syntax errors
            forbidden_patterns = [
                ("end_angle=", "use 'angle=' instead of 'end_angle='"),
                ("size=", "use 'font_size=' for text objects"),
                ("mobject(", "don't use mobject directly")
            ]
            
            for pattern, error_msg in forbidden_patterns:
                if pattern in code:
                    raise ValueError(f"syntax error: {error_msg}")
            
            # Save code
            topic_name = script_data['topic'][:30].replace(' ', '_')
            code_path = Config.MANIM_CODE_DIR / f"{topic_name}.py"
            with open(code_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            print(f"✅ generated manim code saved to: {code_path}")
            return str(code_path)
            
        except Exception as e:
            if retry_count < 2:
                print(f"⚠️ code generation error (attempt {retry_count + 1}): {str(e)}")
                print("🔄 retrying with simplified prompt...")
                # on failure, try generating a simpler fallback code
                return self.generate_simple_fallback(script_data)
            else:
                raise Exception(f"failed to generate valid manim code after {retry_count + 1} attempts: {str(e)}")
    
    def generate_simple_fallback(self, script_data: Dict) -> str:
        """Generate simple, guaranteed-to-work Manim code"""
        
        topic = script_data['topic']
        segments = script_data['segments']
        
        # Create simple text-based animation code
        code = f'''from manim import *

class ExplainerScene(Scene):
    def construct(self):
        # Title
        title = Text("{topic[:40]}", font_size=42, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
'''
        
        # Add segments as simple text animations
        for i, seg in enumerate(segments, 1):
            duration = seg['end_time'] - seg['start_time']
            description = seg['scene_description'][:60].replace('"', "'")
            
            code += f'''        # Segment {i}: {description}
        seg{i} = Text("{description[:40]}", font_size=32)
        self.play(FadeIn(seg{i}))
        self.wait({duration:.1f})
        self.play(FadeOut(seg{i}))
        
'''
        
        code += '''        # Ending
        thanks = Text("Thank You!", font_size=48, color=GREEN)
        self.play(Write(thanks))
        self.wait(2)
'''
        
        # Save fallback code
        topic_name = topic[:30].replace(' ', '_')
        code_path = Config.MANIM_CODE_DIR / f"{topic_name}_fallback.py"
        with open(code_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        print(f"✅ generated fallback manim code: {code_path}")
        return str(code_path)