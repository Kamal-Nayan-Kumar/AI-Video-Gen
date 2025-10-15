from manim import *

class ExplainerScene(Scene):
    def construct(self):
        # --- Configuration for triangle and squares ---
        a_len = 3  # Side 'a' length
        b_len = 4  # Side 'b' length
        c_len = np.sqrt(a_len**2 + b_len**2) # Hypotenuse 'c' length (should be 5 for 3-4-5)

        # Base triangle for drawing and reference
        # Vertices: C (origin), B (right), A (up)
        # So AC is side 'a', CB is side 'b', AB is side 'c'
        point_C = ORIGIN
        point_B = RIGHT * b_len
        point_A = UP * a_len

        right_triangle = Polygon(point_C, point_B, point_A, color=BLUE, stroke_width=6)
        right_triangle.move_to(ORIGIN + LEFT*1.5 + DOWN*0.5) # Center triangle slightly left and down

        # Labels for sides (defined here to calculate positions of squares later)
        label_a = MathTex("a", color=YELLOW).next_to(right_triangle.get_points()[2], LEFT, buff=0.1) # Side AC
        label_b = MathTex("b", color=GREEN).next_to(right_triangle.get_points()[1], DOWN, buff=0.1) # Side CB
        label_c = MathTex("c", color=RED) # Side AB
        
        # Position label_c carefully on the hypotenuse
        hypotenuse_center_pt = (right_triangle.get_points()[1] + right_triangle.get_points()[2]) / 2
        hypotenuse_vector = right_triangle.get_points()[2] - right_triangle.get_points()[1]
        normal_vector_hyp = rotate_vector(normalize(hypotenuse_vector), PI/2) # Outwards normal for label
        label_c.move_to(hypotenuse_center_pt + normal_vector_hyp * 0.5) # Adjust position
        
        # --- Segment 1 (0.0-6.0s): Character and Title Card ---
        # Character
        head = Circle(radius=0.7, color=YELLOW_E, fill_opacity=1)
        eye_left = Ellipse(width=0.2, height=0.3, color=BLACK, fill_opacity=1).shift(LEFT * 0.2 + UP * 0.1)
        eye_right = eye_left.copy().shift(RIGHT * 0.4)
        mouth = Arc(start_angle=PI + PI/4, end_angle=2*PI - PI/4, radius=0.3, color=BLACK, stroke_width=4).shift(DOWN * 0.2)
        
        character = VGroup(head, eye_left, eye_right, mouth).scale(0.8).to_corner(DR).shift(UP*0.5 + LEFT*0.5)
        
        # Title Card
        title_telugu = Text("పైథాగరస్ సిద్ధాంతం", font="Noto Sans Telugu", font_size=60, color=BLUE)
        title_english = Text("Pythagorean Theorem", font_size=48, color=GREEN).next_to(title_telugu, DOWN)
        question_mark = Text("?", font_size=72, color=RED).next_to(title_english, RIGHT, buff=0.2)
        
        title_card = VGroup(title_telugu, title_english, question_mark).move_to(UP*0.5)
        title_card.move_to(title_card.get_center() + LEFT * FRAME_WIDTH/2 - title_card.get_width()/2) # Start off-screen left

        self.play(FadeIn(character, shift=UP), run_time=1.5) # 0.0-1.5s
        self.play(
            title_card.animate.move_to(ORIGIN),
            run_time=2.5, # 1.5-4.0s
            rate_func=EaseOutQuad
        )
        self.wait(2.0) # 4.0-6.0s (Total Segment 1: 6.0s)

        # --- Segment 2 (6.0-12.5s): Right-angled triangle drawing & labeling ---
        self.play(
            FadeOut(title_card, shift=RIGHT),
            character.animate.scale(0.8).to_corner(DR).shift(UP*0.5 + LEFT*0.5), # Keep character small
            run_time=1.0 # 6.0-7.0s
        )
        
        self.play(Create(right_triangle), run_time=2.0) # 7.0-9.0s

        # 90-degree angle symbol
        square_symbol = Square(side_length=0.4, color=YELLOW, fill_opacity=0.5)
        square_symbol.move_to(right_triangle.get_points()[0]).shift(RIGHT * 0.2 + UP * 0.2)
        
        self.play(FadeIn(square_symbol, scale=0.8), run_time=0.5) # 9.0-9.5s

        self.play(
            Write(label_a),
            Write(label_b),
            Write(label_c),
            run_time=1.5 # 9.5-11.0s
        )
        self.wait(1.5) # 11.0-12.5s (Total Segment 2: 6.5s)

        # Group triangle and labels for easy manipulation later
        triangle_group = VGroup(right_triangle, square_symbol, label_a, label_b, label_c)

        # --- Segment 3 (12.5-20.0s): The equation a² + b² = c² ---
        self.play(FadeOut(triangle_group, shift=UP), run_time=1.0) # 12.5-13.5s

        equation = MathTex("a^2", "+", "b^2", "=", "c^2", color=BLUE)
        equation.scale(2)
        equation.move_to(ORIGIN)

        self.play(Write(equation), run_time=2.0) # 13.5-15.5s

        # Pop effect for a^2, b^2, c^2
        part_a2 = equation.get_parts_by_tex("a^2")
        part_b2 = equation.get_parts_by_tex("b^2")
        part_c2 = equation.get_parts_by_tex("c^2")

        self.play(Flash(part_a2, color=YELLOW, flash_radius=0.7), run_time=1.0) # 15.5-16.5s
        self.play(Flash(part_b2, color=GREEN, flash_radius=0.7), run_time=1.0) # 16.5-17.5s
        self.play(Flash(part_c2, color=RED, flash_radius=0.7), run_time=1.0) # 17.5-18.5s
        
        self.wait(1.5) # 18.5-20.0s (Total Segment 3: 7.5s)

        # --- Segment 4 (20.0-25.5s): Triangle reappears, squares drawn outwards ---
        self.play(FadeOut(equation, shift=DOWN), run_time=1.0) # 20.0-21.0s

        self.play(FadeIn(triangle_group, shift=DOWN), run_time=1.0) # 21.0-22.0s
        
        # Squares on sides
        # Square on side 'a' (AC)
        sq_a = Square(side_length=a_len, color=YELLOW, fill_opacity=0.4)
        sq_a.next_to(right_triangle.get_points()[0], LEFT, buff=0).align_to(right_triangle.get_points()[2], UP)

        # Square on side 'b' (CB)
        sq_b = Square(side_length=b_len, color=GREEN, fill_opacity=0.4)
        sq_b.next_to(right_triangle.get_points()[0], DOWN, buff=0).align_to(right_triangle.get_points()[1], RIGHT)

        # Square on side 'c' (AB)
        sq_c = Square(side_length=c_len, color=RED, fill_opacity=0.4)
        
        hypotenuse_line = Line(right_triangle.get_points()[1], right_triangle.get_points()[2])
        hypotenuse_center_line = hypotenuse_line.get_center()
        normal_vector_out = rotate_vector(hypotenuse_line.get_unit_vector(), -PI/2) # Rotate clockwise for outwards
        
        sq_c.move_to(hypotenuse_center_line + normal_vector_out * c_len / 2)
        sq_c.rotate(hypotenuse_line.get_angle()) 

        self.play(Create(sq_a), run_time=0.8) # 22.0-22.8s
        self.play(Create(sq_b), run_time=0.8) # 22.8-23.6s
        self.play(Create(sq_c), run_time=0.8) # 23.6-24.4s
        
        self.wait(1.1) # 24.4-25.5s (Total Segment 4: 5.5s)

        # --- Segment 5 (25.5-33.5s): Visual Proof Animation ---
        # This segment shows a conceptual "dissection" where pieces representing a^2 and b^2
        # rearrange to fill the area of c^2.
        
        # Fade out triangle and labels, only keep squares visible for the proof
        self.play(FadeOut(triangle_group), run_time=1.0) # 25.5-26.5s
        
        # Copies for animation to avoid altering original squares
        sq_a_anim = sq_a.copy()
        sq_b_anim = sq_b.copy()
        sq_c_anim = sq_c.copy()

        # Target position for the rearrangement to be centered
        proof_center = ORIGIN # Center the proof animation

        # Move the squares away from the triangle's initial position for clear rearrangement
        self.play(
            sq_a_anim.animate.move_to(proof_center + LEFT*2.5 + UP*0.5), # Reposition for better visual flow
            sq_b_anim.animate.move_to(proof_center + LEFT*2.5 + DOWN*1.5), # Stacked below sq_a
            sq_c_anim.animate.move_to(proof_center + RIGHT*2.5),
            run_time=1.5 # 26.5-28.0s
        )

        # Create "pieces" from sq_a and sq_b. 
        # For simplicity, we create representative pieces that animate the "filling" effect.
        # sq_b will act as one large piece. sq_a will be "split" into two rectangles for animation.
        
        piece_b = sq_b_anim.copy().set_color(GREEN_E).set_fill(GREEN_E, opacity=0.7)
        piece_a1 = Rectangle(width=a_len, height=a_len/2, color=YELLOW_E, fill_opacity=0.7).move_to(sq_a_anim.get_center() + UP * a_len/4)
        piece_a2 = Rectangle(width=a_len, height=a_len/2, color=YELLOW_E, fill_opacity=0.7).move_to(sq_a_anim.get_center() + DOWN * a_len/4)

        # Hide original squares and show the 'pieces'
        self.play(
            FadeOut(sq_a_anim), FadeOut(sq_b_anim),
            FadeIn(piece_b),
            FadeIn(piece_a1),
            FadeIn(piece_a2),
            run_time=0.5 # 28.0-28.5s
        )

        # Animate the pieces sliding and rearranging to fill sq_c_anim
        # This will be a conceptual "fill" rather than precise polygon matching due to complexity.
        
        # Step 1: Move pieces towards the target square c, with rotation
        self.play(
            piece_b.animate.move_to(sq_c_anim.get_center() + LEFT*0.5 + UP*0.5),
            piece_a1.animate.move_to(sq_c_anim.get_center() + RIGHT*0.5 + DOWN*0.5).rotate(PI/2),
            piece_a2.animate.move_to(sq_c_anim.get_center() + RIGHT*0.5 + UP*0.5).rotate(PI/2),
            run_time=2.0 # 28.5-30.5s
        )
        # Step 2: Transform the pieces into sq_c_anim, showing they fill its area
        self.play(
            Transform(piece_b, sq_c_anim),
            Transform(piece_a1, sq_c_anim),
            Transform(piece_a2, sq_c_anim),
            run_time=1.5 # 30.5-32.0s
        )
        # All pieces have transformed into sq_c_anim. We can then show a clean sq_c_anim.
        self.play(FadeIn(sq_c_anim.set_opacity(1), scale=1.1), run_time=0.5) # Emphasize filled C. # 32.0-32.5s
        self.play(FadeOut(piece_b), FadeOut(piece_a1), FadeOut(piece_a2), run_time=0.0) # Remove temporary pieces

        # Re-show the formula after the proof
        equation_recap = MathTex("a^2 + b^2 = c^2", color=BLUE).scale(1.5).to_edge(UP)
        self.play(FadeIn(equation_recap, shift=UP), run_time=1.0) # 32.5-33.5s (Total Segment 5: 8.0s)

        # --- Segment 6 (33.5-43.5s): Recap & Examples & Character Wink ---
        self.play(
            FadeOut(sq_c_anim), # Fade out the filled square
            FadeIn(triangle_group.move_to(LEFT * 3)), # Bring back triangle and labels
            run_time=1.0 # 33.5-34.5s
        )
        self.wait(0.5) # 34.5-35.0s
        
        # Examples
        # Builder example
        builder_body = Line(DOWN*0.5, UP*0.5, stroke_width=4, color=BLUE) # Body
        builder_head = Circle(radius=0.2, color=YELLOW, fill_opacity=1).shift(UP*0.7) # Head
        builder_arms = VGroup(Line(ORIGIN, LEFT*0.5).shift(UP*0.2), Line(ORIGIN, RIGHT*0.5).shift(UP*0.2)) # Arms
        builder_legs = VGroup(Line(DOWN*0.5, DOWN*0.8 + LEFT*0.2), Line(DOWN*0.5, DOWN*0.8 + RIGHT*0.2)) # Legs
        builder_icon = VGroup(builder_body, builder_head, builder_arms, builder_legs).scale(0.8)
        builder_icon.next_to(triangle_group, RIGHT, buff=2).shift(LEFT*0.5) # Position builder next to triangle

        square_tool = VGroup(
            Line(ORIGIN, UP*0.5), Line(ORIGIN, RIGHT*0.5), # Right angle tool
        ).set_color(RED).next_to(builder_icon, DOWN, buff=0.1)
        
        builder_text = Text("Construction", font_size=28, color=GREEN).next_to(builder_icon, UP, buff=0.5)
        
        self.play(
            FadeIn(builder_icon, shift=UP),
            FadeIn(square_tool, shift=UP),
            Write(builder_text),
            run_time=2.0 # 35.0-37.0s
        )
        self.wait(1.0) # 37.0-38.0s

        # Map example
        map_outline = Polygon(
            ORIGIN, RIGHT*2, RIGHT*2 + UP*1, RIGHT*1 + UP*1, RIGHT*1 + UP*2, UP*2, ORIGIN,
            stroke_width=3, color=BLUE_B
        ).scale(0.8).next_to(builder_icon, RIGHT, buff=2).shift(LEFT*0.5)
        
        path1 = Line(map_outline.get_corner(UL), map_outline.get_corner(UR) + DOWN*0.5, color=RED)
        path2 = Line(map_outline.get_corner(UR) + DOWN*0.5, map_outline.get_corner(DR), color=RED)
        path3 = Line(map_outline.get_corner(UL), map_outline.get_corner(DR), color=RED, stroke_dasharray=[5, 5])
        
        map_text = Text("Navigation", font_size=28, color=GREEN).next_to(map_outline, UP, buff=0.5)
        
        self.play(
            FadeOut(builder_icon), FadeOut(square_tool), FadeOut(builder_text),
            FadeIn(map_outline),
            Create(path1), Create(path2), Create(path3),
            Write(map_text),
            run_time=2.0 # 38.0-40.0s
        )
        self.wait(1.0) # 40.0-41.0s

        # Character wink
        # Restore character to its original size for wink
        self.play(
            FadeOut(triangle_group), FadeOut(equation_recap),
            FadeOut(map_outline), FadeOut(path1), FadeOut(path2), FadeOut(path3), FadeOut(map_text),
            character.animate.scale(1/0.8).move_to(ORIGIN+DOWN*1.5), # Make character prominent again
            run_time=1.0 # 41.0-42.0s
        )

        wink_eye = eye_left # Use the pre-defined eye_left object
        original_eye_shape = wink_eye.copy()
        winked_eye_shape = Line(wink_eye.get_left(), wink_eye.get_right(), color=BLACK, stroke_width=4).move_to(wink_eye.get_center())
        
        self.play(Transform(wink_eye, winked_eye_shape), run_time=0.3) # 42.0-42.3s
        self.wait(0.2) # 42.3-42.5s
        self.play(Transform(wink_eye, original_eye_shape), run_time=0.3) # 42.5-42.8s
        
        self.wait(0.7) # 42.8-43.5s (Total Segment 6: 10.0s)