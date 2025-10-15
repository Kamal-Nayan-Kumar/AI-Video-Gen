from manim import *

class ExplainerScene(Scene):
    def construct(self):
        # Title
        title = Text("How does photosynthesis work", font_size=42, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Segment 1: Animation of a lush green plant with a subtle glowing aura, 
        seg1 = Text("Animation of a lush green plant with a s", font_size=32)
        self.play(FadeIn(seg1))
        self.wait(7.0)
        self.play(FadeOut(seg1))
        
        # Segment 2: Sun shining brightly with rays. Water droplets rising from r
        seg2 = Text("Sun shining brightly with rays. Water dr", font_size=32)
        self.play(FadeIn(seg2))
        self.wait(8.0)
        self.play(FadeOut(seg2))
        
        # Segment 3: Close-up on a leaf, zooming into chloroplasts within plant c
        seg3 = Text("Close-up on a leaf, zooming into chlorop", font_size=32)
        self.play(FadeIn(seg3))
        self.wait(8.0)
        self.play(FadeOut(seg3))
        
        # Segment 4: Animated chemical reaction inside the chloroplast: Water (H2
        seg4 = Text("Animated chemical reaction inside the ch", font_size=32)
        self.play(FadeIn(seg4))
        self.wait(8.0)
        self.play(FadeOut(seg4))
        
        # Segment 5: Glucose molecules flowing through the plant for energy. Oxyg
        seg5 = Text("Glucose molecules flowing through the pl", font_size=32)
        self.play(FadeIn(seg5))
        self.wait(7.0)
        self.play(FadeOut(seg5))
        
        # Ending
        thanks = Text("Thank You!", font_size=48, color=GREEN)
        self.play(Write(thanks))
        self.wait(2)
