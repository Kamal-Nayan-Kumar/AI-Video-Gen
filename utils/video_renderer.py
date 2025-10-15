# utils/video_renderer.py

import sys
import traceback
from pathlib import Path
from config import Config

class VideoRenderer:
    @staticmethod
    def render_manim(code_path: str, retry_with_fallback: bool = True) -> str:
        """Render Manim code to video programmatically with error handling"""
        
        code_path = Path(code_path)
        
        try:
            # Import the generated Manim code
            import importlib.util
            spec = importlib.util.spec_from_file_location("generated_scene", code_path)
            scene_module = importlib.util.module_from_spec(spec)
            sys.modules["generated_scene"] = scene_module
            spec.loader.exec_module(scene_module)
            
            # Get the ExplainerScene class
            if not hasattr(scene_module, 'ExplainerScene'):
                raise AttributeError("Generated code must contain 'ExplainerScene' class")
            
            ExplainerScene = scene_module.ExplainerScene
            
            # Configure and render
            from manim import config, tempconfig
            
            quality_map = {
                "l": "low_quality",
                "m": "medium_quality", 
                "h": "high_quality"
            }
            
            output_file = Config.VIDEOS_DIR / f"{code_path.stem}.mp4"
            
            print(f"🎬 Rendering Manim scene...")
            
            with tempconfig({
                "quality": quality_map.get(Config.MANIM_QUALITY, "medium_quality"),
                "output_file": str(output_file),
                "media_dir": str(Config.OUTPUT_DIR / "media"),
                "write_to_movie": True,
                "save_last_frame": False,
                "preview": False,
                "disable_caching": True,
                "fps": Config.MANIM_FPS,
                "pixel_height": 720,
                "pixel_width": 1280,
                "frame_rate": Config.MANIM_FPS
            }):
                scene = ExplainerScene()
                scene.render()
                
                # Get the actual output path
                output_path = scene.renderer.file_writer.movie_file_path
                
                # Ensure video exists
                if not Path(output_path).exists():
                    raise FileNotFoundError(f"Rendered video not found at: {output_path}")
                
                print(f"✅ Video rendered successfully: {output_path}")
                return str(output_path)
                
        except Exception as e:
            error_msg = f"Manim rendering error: {str(e)}\n{traceback.format_exc()}"
            print(f"❌ {error_msg}")
            
            # If this was the fallback already, don't retry
            if "_fallback" in code_path.stem or not retry_with_fallback:
                raise Exception(error_msg)
            
            # Try generating and rendering fallback code
            print("\n🔄 Attempting fallback with simple animation...")
            
            # Import script data from saved file
            import json
            script_path = Config.SCRIPTS_DIR / f"{code_path.stem.replace('_fallback', '')}.json"
            
            if script_path.exists():
                with open(script_path, 'r') as f:
                    script_data = json.load(f)
                
                from generators.manim_generator import ManimGenerator
                manim_gen = ManimGenerator()
                fallback_path = manim_gen.generate_simple_fallback(script_data)
                
                # Retry with fallback (no further retries)
                return VideoRenderer.render_manim(fallback_path, retry_with_fallback=False)
            else:
                raise Exception(f"Cannot generate fallback: script file not found at {script_path}")
