import gradio as gr
from generators.script_generator import ScriptGenerator
from generators.manim_generator import ManimGenerator
from generators.voice_generator import VoiceGenerator
from utils.video_renderer import VideoRenderer
from utils.video_merger import VideoMerger
import traceback

# app.py (Updated error handling section)

import traceback  # Add at top of file

def generate_explainer_video(topic: str, tone: str, language: str):
    """Main pipeline for video generation"""
    
    try:
        yield "🎬 Starting video generation...", None, None
        
        # Step 1: Generate script
        yield "📝 Generating voice script with timestamps...", None, None
        script_gen = ScriptGenerator()
        script_data = script_gen.generate_script(topic, tone, language)
        script_text = f"✅ Generated {len(script_data['segments'])} segments\n⏱️ Duration: {script_data['total_duration']}s"
        
        # Step 2: Generate Manim code
        yield "🎨 Generating Manim animation code...", script_text, None
        manim_gen = ManimGenerator()
        code_path = manim_gen.generate_manim_code(script_data)
        
        # Step 3: Render video
        yield "🎥 Rendering Manim video (1-3 minutes, please wait)...", script_text, None
        renderer = VideoRenderer()
        video_path = renderer.render_manim(code_path)
        
        # Step 4: Generate voice
        yield "🎤 Generating multilingual voice narration...", script_text, None
        voice_gen = VoiceGenerator()
        audio_path = voice_gen.generate_voice(script_data, language)
        
        # Step 5: Merge audio and video
        yield "🎬 Synchronizing audio and video...", script_text, None
        merger = VideoMerger()
        final_path = merger.merge_audio_video(video_path, audio_path, topic)
        
        success_msg = f"✅ Video generation complete!\n📹 Duration: {script_data['total_duration']}s\n🎯 Segments: {len(script_data['segments'])}"
        yield success_msg, script_text, final_path
        
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}\n\n💡 Tip: Try a simpler topic or check API keys in .env file"
        print(f"\n🔴 Full error:\n{traceback.format_exc()}")
        yield error_msg, None, None

# Gradio Interface
with gr.Blocks(title="Manim Explainer Video Generator", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🎬 Manim Explainer Video Generator")
    gr.Markdown("Generate educational animation videos with AI-generated voiceovers")
    
    with gr.Row():
        with gr.Column():
            topic_input = gr.Textbox(
                label="Topic",
                placeholder="e.g., Explain Pythagoras theorem",
                lines=2
            )
            
            tone_input = gr.Dropdown(
                label="Tone Style",
                choices=["formal", "funny", "storytelling"],
                value="formal"
            )
            
            language_input = gr.Dropdown(
                label="Language",
                choices=["english", "hindi", "kannada", "telugu"],
                value="english"
            )
            
            generate_btn = gr.Button("🎬 Generate Video", variant="primary", size="lg")
        
        with gr.Column():
            status_output = gr.Textbox(label="Status", lines=3)
            script_output = gr.Textbox(label="Generated Script Info", lines=5)
    
    with gr.Row():
        video_output = gr.Video(label="Final Video")
    
    generate_btn.click(
        fn=generate_explainer_video,
        inputs=[topic_input, tone_input, language_input],
        outputs=[status_output, script_output, video_output]
    )
    
    gr.Markdown("""
    ### 📋 Examples:
    - "Explain the Pythagorean theorem with visual proof"
    - "How does photosynthesis work?"
    - "What is Newton's second law of motion?"
    - "Explain binary search algorithm"
    """)

if __name__ == "__main__":
    app.launch(share=True, server_port=7860)
