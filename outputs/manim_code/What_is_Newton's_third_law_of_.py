from manim import *

class ExplainerScene(Scene):
    def construct(self):
        self.camera.background_color = BLACK

        # Segment 1: Hand and Wall (0.0-5.0s)
        self.segment1_hand_wall()
        self.wait_until(5.0)

        # Segment 2: Title and Colliding Spheres (5.0-10.5s)
        self.segment2_title_spheres()
        self.wait_until(10.5)

        # Segment 3: Action/Reaction Arrows and Text (10.5-17.5s)
        self.segment3_action_reaction()
        self.wait_until(17.5)

        # Segment 4: Handshake and Force Vectors (17.5-25.5s)
        self.segment4_handshake()
        self.wait_until(25.5)

        # Segment 5: Rocket Launch (25.5-33.5s)
        self.segment5_rocket_launch()
        self.wait_until(33.5)

        # Segment 6: Montage (33.5-41.5s)
        self.segment6_montage()
        self.wait_until(41.5)

    def wait_until(self, target_time):
        """Helper to ensure the total time for a segment matches the timeline."""
        current_time = self.renderer.time
        if target_time > current_time:
            self.wait(target_time - current_time)

    def segment1_hand_wall(self):
        wall = Rectangle(width=8, height=4, color=GRAY_B, fill_opacity=0.8, stroke_width=2).shift(RIGHT * 2)
        hand_repr = Circle(radius=0.5, color=TEAL_A, fill_opacity=1).move_to(LEFT * 4 + UP * 0.5)

        self.play(FadeIn(wall, shift=RIGHT), FadeIn(hand_repr, shift=LEFT), run_time=1)
        self.play(hand_repr.animate.move_to(wall.get_left() + LEFT * 0.2), run_time=1) # Hand approaches
        self.play(
            hand_repr.animate.move_to(wall.get_left()),
            wall.animate.scale(1.01).set_color(GRAY_C).set_stroke(GRAY_D, width=3), # Subtle deformation
            run_time=0.5
        )
        self.play(
            hand_repr.animate.move_to(wall.get_left() + LEFT * 0.2), # Hand recoils
            wall.animate.scale(1/1.01).set_color(GRAY_B).set_stroke(GRAY_B, width=2), # Wall restores
            run_time=0.5
        )
        self.wait(1) # Hold for a moment

        self.play(FadeOut(wall, shift=RIGHT), FadeOut(hand_repr, shift=LEFT), run_time=1)

    def segment2_title_spheres(self):
        self.clear() # Clear previous elements

        title = Text("Newton's Third Law of Motion", font_size=55).set_color(YELLOW).scale(0.1)
        self.play(GrowFromCenter(title, run_time=1))
        self.play(title.animate.scale(1.2).shift(UP * 2), run_time=0.7) # Grow and move up

        sphere1 = Circle(radius=0.5, color=RED, fill_opacity=0.8).shift(LEFT * 3 + DOWN * 0.5)
        sphere2 = Circle(radius=0.5, color=BLUE, fill_opacity=0.8).shift(RIGHT * 3 + DOWN * 0.5)

        # Add subtle glow effect
        sphere1.set_stroke(RED_E, width=3, opacity=0.8)
        sphere2.set_stroke(BLUE_E, width=3, opacity=0.8)

        self.play(FadeIn(sphere1), FadeIn(sphere2), run_time=0.3)
        self.play(
            sphere1.animate.shift(RIGHT * 2.5),
            sphere2.animate.shift(LEFT * 2.5),
            run_time=1.5,
            rate_func=linear # Collide
        )
        self.play(
            sphere1.animate.shift(LEFT * 0.5),
            sphere2.animate.shift(RIGHT * 0.5),
            run_time=0.7,
            rate_func=rate_functions.ease_out_bounce # Bounce back slightly
        )
        self.wait(0.3)
        self.play(FadeOut(title, shift=UP), FadeOut(sphere1, shift=LEFT), FadeOut(sphere2, shift=RIGHT), run_time=1)

    def segment3_action_reaction(self):
        self.clear() # Clear previous elements

        action_arrow = Arrow(start=ORIGIN, end=RIGHT * 3, color=RED, buff=0, tip_length=0.3)
        action_label = Text("Action", font_size=36).next_to(action_arrow, UP, buff=0.2).set_color(RED)
        action_group = VGroup(action_arrow, action_label)

        reaction_arrow = Arrow(start=ORIGIN, end=LEFT * 3, color=BLUE, buff=0, tip_length=0.3)
        reaction_label = Text("Reaction", font_size=36).next_to(reaction_arrow, UP, buff=0.2).set_color(BLUE)
        reaction_group = VGroup(reaction_arrow, reaction_label)

        self.play(
            GrowArrow(action_arrow), Write(action_label),
            GrowArrow(reaction_arrow), Write(reaction_label),
            run_time=1.5
        )
        self.wait(0.5)

        law_text = Text("For every action, there is an equal and opposite reaction.", font_size=40).next_to(action_group, DOWN, buff=1)
        law_text.set_color(GREEN)
        
        self.play(Write(law_text), run_time=1.5)
        self.wait(2.5)

        self.play(FadeOut(action_group, shift=UP), FadeOut(reaction_group, shift=UP), FadeOut(law_text, shift=DOWN), run_time=1)

    def segment4_handshake(self):
        self.clear() # Clear previous elements

        # Stylized hands using Polygons
        hand1_shape = [
            [-2.5, 0.5, 0], [-1.5, 1.2, 0], [0, 0.8, 0], [0, -0.8, 0], [-1.5, -1.2, 0], [-2.5, -0.5, 0]
        ]
        hand1 = Polygon(*hand1_shape, color=TEAL_A, fill_opacity=0.8, stroke_width=2).scale(0.8).rotate(PI/6).shift(LEFT*4)
        hand2 = Polygon(*hand1_shape, color=TEAL_A, fill_opacity=0.8, stroke_width=2).scale(0.8).rotate(-PI/6).flip(LEFT).shift(RIGHT*4)

        self.play(FadeIn(hand1, shift=LEFT), FadeIn(hand2, shift=RIGHT), run_time=1)
        self.play(
            hand1.animate.shift(RIGHT * 2.5),
            hand2.animate.shift(LEFT * 2.5),
            run_time=1.5
        ) # Hands meet in the center

        contact_point = ORIGIN
        force_right = Arrow(contact_point, contact_point + RIGHT * 0.7, color=RED, buff=0, tip_length=0.2)
        force_left = Arrow(contact_point, contact_point + LEFT * 0.7, color=BLUE, buff=0, tip_length=0.2)
        
        # Position arrows slightly above/below contact for clarity
        force_right.shift(UP * 0.3)
        force_left.shift(DOWN * 0.3)

        self.play(GrowArrow(force_right), GrowArrow(force_left), run_time=1.5)
        self.wait(3) # Hold handshake with forces
        self.play(FadeOut(hand1, shift=LEFT), FadeOut(hand2, shift=RIGHT), FadeOut(force_right), FadeOut(force_left), run_time=1)

    def segment5_rocket_launch(self):
        self.clear() # Clear previous elements

        # Rocket body components
        body_base = Rectangle(width=1.5, height=4, color=GRAY_C, fill_opacity=0.9)
        nose_cone = Triangle(color=RED_E).scale_to_fit_width(1.5).scale_to_fit_height(1.5).flip(UP).next_to(body_base, UP, buff=0)
        fin1 = Triangle(color=GRAY_D).scale_to_fit_width(0.8).scale_to_fit_height(1.5).rotate(DEGREES * 180).next_to(body_base.get_bottom(), RIGHT, buff=0.1).shift(DOWN * 0.5)
        fin2 = fin1.copy().flip(LEFT)
        
        rocket = VGroup(body_base, nose_cone, fin1, fin2).move_to(DOWN * 2)

        launchpad = Rectangle(width=5, height=0.5, color=GRAY_B, fill_opacity=0.8).next_to(rocket, DOWN, buff=0.1)

        # Flames (start small, grow)
        flames_shape = VGroup(
            Triangle(color=ORANGE, fill_opacity=0.9).scale(0.5),
            Triangle(color=YELLOW_E, fill_opacity=0.7).scale(0.4).rotate(PI/8).shift(LEFT*0.1),
            Triangle(color=RED_A, fill_opacity=0.6).scale(0.4).rotate(-PI/8).shift(RIGHT*0.1)
        ).arrange(DOWN, buff=0.1).next_to(rocket.get_bottom(), DOWN, buff=0.1).scale(0.01) # Start very small

        self.play(Create(launchpad), FadeIn(rocket), run_time=1)
        self.add(flames_shape) # Add flames to scene, hidden initially by scale 0.01

        # Force of Exhaust - originates from rocket's initial bottom, stays fixed
        initial_exhaust_point = rocket.get_bottom() + DOWN*0.1 # slightly below rocket
        force_exhaust_arrow = Arrow(initial_exhaust_point, initial_exhaust_point + DOWN * 1.5, color=RED, buff=0, tip_length=0.3)
        exhaust_label = Text("Force of Exhaust", font_size=30).next_to(force_exhaust_arrow, LEFT, buff=0.1).set_color(RED)
        force_exhaust_group = VGroup(force_exhaust_arrow, exhaust_label)

        # Force on Rocket - originates from rocket's center, moves with rocket
        force_rocket_arrow = Arrow(rocket.get_center(), rocket.get_center() + UP * 1.5, color=BLUE, buff=0, tip_length=0.3)
        rocket_label = Text("Force on Rocket", font_size=30).next_to(force_rocket_arrow, RIGHT, buff=0.1).set_color(BLUE)
        force_rocket_group = VGroup(force_rocket_arrow, rocket_label)
        
        # Rocket and its upward force move together
        rocket_and_upward_force = VGroup(rocket, force_rocket_group)

        # Launch animation
        self.play(
            AnimationGroup(
                flames_shape.animate.scale(20).shift(DOWN*0.5).set_opacity(1), # Flames grow and glow
                rocket_and_upward_force.animate.shift(UP * 7),
                GrowArrow(force_exhaust_arrow),
                Write(exhaust_label),
                run_time=4,
                rate_func=rate_functions.ease_in_quad,
                lag_ratio=0.1,
            )
        )
        self.play(FadeOut(flames_shape, shift=DOWN), run_time=0.5) # Flames disappear as rocket leaves frame
        self.wait(1) # Hold rocket in sky

        self.play(
            FadeOut(rocket_and_upward_force), 
            FadeOut(force_exhaust_group), 
            FadeOut(launchpad), 
            run_time=1.5
        )

    def segment6_montage(self):
        self.clear() # Clear previous elements

        # Part 1: Stick figure walking (2.0s)
        head = Circle(radius=0.3, color=WHITE).shift(UP * 1.5)
        body = Line(UP * 1.2, DOWN * 0.5, color=WHITE)
        arm1 = Line(UP * 0.8 + LEFT * 0.2, UP * 0.2 + LEFT * 0.5, color=WHITE)
        arm2 = Line(UP * 0.8 + RIGHT * 0.2, UP * 0.2 + RIGHT * 0.5, color=WHITE)
        leg1 = Line(DOWN * 0.5 + LEFT * 0.1, DOWN * 1.5 + LEFT * 0.5, color=WHITE)
        leg2 = Line(DOWN * 0.5 + RIGHT * 0.1, DOWN * 1.5 + RIGHT * 0.5, color=WHITE)
        stick_figure = VGroup(head, body, arm1, arm2, leg1, leg2).scale(0.7).move_to(LEFT * 4 + DOWN * 1.5)

        ground = Line(LEFT * 6, RIGHT * 6, color=GRAY_B).move_to(DOWN * 2)

        self.play(Create(VGroup(stick_figure, ground)), run_time=0.5)

        # Force arrows at contact point for walking
        # Position arrows relative to the stick figure's foot during the 'walk' animation
        foot_pos_during_walk = stick_figure.get_bottom() + RIGHT * 1.5 + DOWN * 0.2 # Approximate mid-walk foot position
        ground_push_arrow = Arrow(foot_pos_during_walk, foot_pos_during_walk + LEFT * 0.5, color=RED, buff=0, tip_length=0.2)
        foot_push_arrow = Arrow(foot_pos_during_walk, foot_pos_during_walk + RIGHT * 0.5, color=BLUE, buff=0, tip_length=0.2)
        
        self.play(
            stick_figure.animate.shift(RIGHT * 2), # Simple walk animation
            GrowArrow(ground_push_arrow), GrowArrow(foot_push_arrow), # Forces appear during the walk
            run_time=1.0
        )
        self.play(FadeOut(stick_figure, ground, ground_push_arrow, foot_push_arrow), run_time=0.5)

        # Part 2: Simplified solar system (3.0s)
        sun = Circle(radius=0.8, color=YELLOW, fill_opacity=1).move_to(LEFT * 2)
        planet = Circle(radius=0.3, color=BLUE_C, fill_opacity=1).move_to(LEFT * 2 + UP * 2.5)
        orbit_path = Ellipse(width=5, height=3, color=GRAY_D).move_to(LEFT * 2)

        # Gravitational arrows
        arrow_sun_planet = Arrow(sun.get_center(), planet.get_center(), buff=0.1, color=GREEN, tip_length=0.2)
        arrow_planet_sun = Arrow(planet.get_center(), sun.get_center(), buff=0.1, color=GREEN, tip_length=0.2)
        
        # Add updater to arrows so they follow the planet
        def update_arrows(mobject):
            arrow_sun_planet.put_start_and_end_on(sun.get_center(), planet.get_center())
            arrow_planet_sun.put_start_and_end_on(planet.get_center(), sun.get_center())
        
        self.play(FadeIn(sun, orbit_path), Create(planet), run_time=0.7)
        
        # Add arrows and their updaters before playing the orbit animation
        self.add(arrow_sun_planet, arrow_planet_sun)
        arrow_sun_planet.add_updater(update_arrows)
        arrow_planet_sun.add_updater(update_arrows)
        
        self.play(FadeIn(arrow_sun_planet), FadeIn(arrow_planet_sun), run_time=0.5)
        self.play(MoveAlongPath(planet, orbit_path, run_time=1.3, rate_func=linear))
        
        # Remove updaters before fading out to prevent errors
        arrow_sun_planet.remove_updater(update_arrows)
        arrow_planet_sun.remove_updater(update_arrows)
        
        self.play(FadeOut(sun, planet, orbit_path, arrow_sun_planet, arrow_planet_sun), run_time=0.5)

        # Part 3: Final text (3.0s)
        final_text = Text("A continuous cosmic ballet of forces.", font_size=45).set_color(GREEN)
        self.play(Write(final_text), run_time=2)
        self.wait(1)