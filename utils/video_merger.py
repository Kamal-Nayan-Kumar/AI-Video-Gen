from moviepy.editor import VideoFileClip, AudioFileClip
from config import Config
from pathlib import Path

class VideoMerger:
    @staticmethod
    def merge_audio_video(video_path: str, audio_path: str, topic: str) -> str:
        """Merge audio and video using moviepy"""
        
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        
        # Sync audio to video duration
        if audio.duration < video.duration:
            # Loop audio if too short
            audio = audio.audio_loop(duration=video.duration)
        else:
            # Trim audio if too long
            audio = audio.subclip(0, video.duration)
        
        # Set audio to video
        final_video = video.set_audio(audio)
        
        # Export
        output_path = Config.FINAL_DIR / f"{topic[:30].replace(' ', '_')}_final.mp4"
        final_video.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            fps=Config.MANIM_FPS
        )
        
        # Cleanup
        video.close()
        audio.close()
        final_video.close()
        
        return str(output_path)
