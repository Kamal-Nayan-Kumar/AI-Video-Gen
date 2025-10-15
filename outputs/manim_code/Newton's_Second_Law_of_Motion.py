from manim import *

class ExplainerScene(Scene):
    def construct(self):
        # --- Segment 1: Pebble and Boulder (0.0-6.0s) ---
        # 0.0-1.0s: Pebble and Boulder appear side-by-side
        pebble = Circle(radius=0.2, color=GRAY_A, fill_opacity=1).move_to([-3, -1, 0])
        boulder = Circle(radius=0.8, color=GRAY_D, fill_opacity=1).move_to([3, -1, 0])
        self.play(Create(pebble), Create(boulder), run_time=1.0)

        # 1.0-1.5s: Hand icon appears
        hand_icon = Text("\U0001F449", font_size=50, color=WHITE).next_to(pebble, LEFT, buff=0.2)
        self.play(FadeIn(hand_icon), run_time=0.5)

        # 1.5-3.5s: Hand attempts to push the pebble, it moves easily
        # Adjust hand position to simulate pushing from the left
        self.play(
            hand_icon.animate.move_to(pebble.get_center() + LEFT * 0.7),
            pebble.animate.shift(RIGHT * 2),
            run_time=2.0,
            rate_func=linear
        )
        # Remove and re-add hand to reset its state for the next animation
        self.remove(hand_icon)
        hand_icon = Text("\U0001F449", font_size=50, color=WHITE).next_to(boulder, LEFT, buff=0.2)
        self.add(hand_icon)

        # 3.5-4.5s: Hand moves to the boulder
        self.play(
            hand_icon.animate.move_to(boulder.get_center() + LEFT * 1.0),
            run_time=1.0
        )

        # 4.5-5.5s: Hand struggles with the boulder
        self.play(Wiggle(hand_icon, scale_value=1.1, run_time=1.0))

        # 5.5-6.0s: Question mark appears over the boulder
        question_mark = Text("?", font_size=70, color=YELLOW).next_to(boulder, UP, buff=0.5)
        self.play(FadeIn(question_mark), run_time=0.5)


        # --- Segment 2: Newton and Force-Acceleration (6.0-12.0s) ---
        # 6.0-6.5s: Fade out previous scene elements
        self.play(FadeOut(pebble, boulder, hand_icon, question_mark), run_time=0.5)

        # 6.5-7.5s: Portrait of Isaac Newton appears briefly
        newton_text = Text("Isaac Newton", font_size=30, color=BLUE_E).to_edge(UP)
        self.play(Write(newton_text), run_time=1.0)

        # 7.5-8.0s: Fade out Newton's text
        self.play(FadeOut(newton_text), run_time=0.5)

        # 8.0-8.7s: An object (block) and frictionless surface appear
        block = Square(side_length=1, color=WHITE, fill_opacity=0.8).move_to([-3, -1, 0])
        surface = Line(block.get_bottom() + LEFT*2, block.get_bottom() + RIGHT*2, color=GRAY)
        self.play(Create(block), Create(surface), run_time=0.7)

        # 8.7-10.2s: Small arrow (force) pushes it, it moves slowly
        force_s = Arrow(ORIGIN, RIGHT, color=RED, buff=0).scale(1.5).next_to(block, LEFT, buff=0.2)
        self.play(GrowArrow(force_s), block.animate.shift(RIGHT*2), run_time=1.5, rate_func=linear)
        self.remove(force_s) # Instant removal of the arrow

        # 10.2-11.7s: Larger arrow (more force) pushes it, it speeds up significantly
        # Reset block position for new push animation
        self.remove(block)
        block = Square(side_length=1, color=WHITE, fill_opacity=0.8).move_to([-3, -1, 0])
        self.add(block)
        force_l = Arrow(ORIGIN, RIGHT, color=RED, buff=0).scale(2.5).next_to(block, LEFT, buff=0.2)
        self.play(GrowArrow(force_l), block.animate.shift(RIGHT*4), run_time=1.5, rate_func=linear)
        self.remove(force_l)

        # 11.7-12.0s: "But there's a catch!" text appears
        catch_text = Text("But there's a catch!", font_size=40, color=YELLOW).to_edge(DOWN)
        self.play(Write(catch_text), run_time=0.3)


        # --- Segment 3: Mass Comparison (12.0-18.0s) ---
        # 12.0-12.5s: Fade out previous scene elements
        self.play(FadeOut(block, surface, catch_text), run_time=0.5)

        # 12.5-13.5s: Two blocks of different sizes (m1, m2) with labels
        block_m1 = Square(side_length=0.8, color=BLUE_A, fill_opacity=0.8).move_to([-3.5, 0, 0])
        label_m1 = MathTex("m_1", font_size=30, color=WHITE).next_to(block_m1, UP)
        block_m2 = Square(side_length=1.5, color=GREEN_A, fill_opacity=0.8).move_to([2.0, 0, 0])
        label_m2 = MathTex("m_2", font_size=30, color=WHITE).next_to(block_m2, UP)
        self.play(Create(block_m1), Write(label_m1), Create(block_m2), Write(label_m2), run_time=1.0)

        # 13.5-15.0s: Consistent small force pushes m1, it accelerates
        force_arrow_m1 = Arrow(ORIGIN, RIGHT, color=RED, buff=0).scale(1.2).next_to(block_m1, LEFT, buff=0.2)
        self.play(GrowArrow(force_arrow_m1), block_m1.animate.shift(RIGHT*3), run_time=1.5, rate_func=linear)
        self.remove(force_arrow_m1) # Remove the arrow after its action

        # 15.0-16.5s: The same small force pushes m2, it barely moves
        force_arrow_m2_weak = Arrow(ORIGIN, RIGHT, color=RED, buff=0).scale(1.2).next_to(block_m2, LEFT, buff=0.2)
        self.play(GrowArrow(force_arrow_m2_weak), block_m2.animate.shift(RIGHT*0.5), run_time=1.5, rate_func=linear)
        self.remove(force_arrow_m2_weak) # Remove the arrow after its action

        # 16.5-18.0s: A much larger force pushes m2, and it accelerates
        force_arrow_m2_strong = Arrow(ORIGIN, RIGHT, color=RED, buff=0).scale(2.5).next_to(block_m2, LEFT, buff=0.2)
        self.play(GrowArrow(force_arrow_m2_strong), block_m2.animate.shift(RIGHT*2.5), run_time=1.5, rate_func=linear)
        self.remove(force_arrow_m2_strong) # Remove the arrow after its action


        # --- Segment 4: The Formula F = ma (18.0-26.0s) ---
        # 18.0-18.5s: Fade out previous scene elements
        self.play(FadeOut(block_m1, label_m1, block_m2, label_m2), run_time=0.5)

        # 18.5-19.5s: The formula 'F = ma' appears prominently
        formula = MathTex("F", "=", "m", "a", font_size=96).center()
        self.play(Write(formula), run_time=1.0)

        # 19.5-21.5s: 'F' for Net Force highlighted
        f_label = Text("Net Force", color=BLUE).next_to(formula[0], UP, buff=0.5)
        f_arrow = Arrow(f_label.get_bottom(), formula[0].get_top(), color=BLUE)
        self.play(Write(f_label), GrowArrow(f_arrow), formula[0].animate.set_color(BLUE), run_time=2.0)

        # 21.5-23.5s: 'm' for Mass highlighted
        m_label = Text("Mass", color=GREEN).next_to(formula[2], UP, buff=0.5)
        m_arrow = Arrow(m_label.get_bottom(), formula[2].get_top(), color=GREEN)
        self.play(Write(m_label), GrowArrow(m_arrow), formula[2].animate.set_color(GREEN), run_time=2.0)

        # 23.5-25.5s: 'a' for Acceleration highlighted
        a_label = Text("Acceleration", color=YELLOW).next_to(formula[3], UP, buff=0.5)
        a_arrow = Arrow(a_label.get_bottom(), formula[3].get_top(), color=YELLOW)
        self.play(Write(a_label), GrowArrow(a_arrow), formula[3].animate.set_color(YELLOW), run_time=2.0)
        
        # 25.5-26.0s: Hold on the formula and labels
        self.wait(0.5)


        # --- Segment 5: Quick Cuts with F=ma (26.0-32.0s) ---
        # 26.0-26.5s: Fade out formula and labels
        all_formula_elements = VGroup(formula, f_label, f_arrow, m_label, m_arrow, a_label, a_arrow)
        self.play(FadeOut(all_formula_elements), run_time=0.5)
        
        # F=ma overlay for all quick cuts
        fma_overlay = MathTex("F=ma", font_size=30, color=RED).to_corner(UL).shift(UP*0.2 + LEFT*0.2)

        # 26.5-28.0s: Soccer ball kicked
        soccer_ball = Circle(radius=0.5, color=YELLOW, fill_opacity=1).move_to([-3, -1, 0])
        kick_force = Arrow(ORIGIN, RIGHT, color=BLUE, buff=0).scale(1.5).next_to(soccer_ball, LEFT, buff=0.2)
        soccer_text = Text("Soccer Ball", font_size=24, color=BLUE_C).next_to(soccer_ball, UP)
        self.play(Create(soccer_ball), Create(kick_force), Write(soccer_text), FadeIn(fma_overlay), run_time=0.5)
        self.play(kick_force.animate.shift(RIGHT*0.5), soccer_ball.animate.shift(RIGHT*4), run_time=1.0, rate_func=linear)

        # 28.0-29.5s: Rocket launching into space
        rocket = Triangle().scale(1).set_color(GRAY).rotate(PI/2).flip(RIGHT).move_to([0, -2, 0])
        flame = Triangle().scale(0.5).set_color(ORANGE).next_to(rocket, DOWN, buff=0)
        rocket_text = Text("Rocket Launch", font_size=24, color=YELLOW_C).next_to(rocket, UP)
        fma_overlay.set_color(YELLOW) # Change overlay color
        self.play(FadeOut(soccer_ball, kick_force, soccer_text), FadeIn(rocket, flame, rocket_text, fma_overlay), run_time=0.5)
        self.play(rocket.animate.shift(UP*3), flame.animate.shift(UP*3), run_time=1.0, rate_func=linear)

        # 29.5-31.0s: Person pushing a shopping cart
        shopping_cart_body = VGroup(Rectangle(width=1.5, height=1).set_color(BLUE_C), Circle(radius=0.2, color=BLUE_D).move_to(RIGHT*0.5+DOWN*0.5), Circle(radius=0.2, color=BLUE_D).move_to(LEFT*0.5+DOWN*0.5)).move_to([-2, -1, 0])
        person_hand = Text("\U0001F449", font_size=40).next_to(shopping_cart_body, RIGHT, buff=0.2)
        cart_text = Text("Shopping Cart", font_size=24, color=GREEN_C).next_to(shopping_cart_body, UP)
        fma_overlay.set_color(GREEN) # Change overlay color
        self.play(FadeOut(rocket, flame, rocket_text), FadeIn(shopping_cart_body, person_hand, cart_text, fma_overlay), run_time=0.5)
        self.play(shopping_cart_body.animate.shift(RIGHT*3), person_hand.animate.shift(RIGHT*3), run_time=1.0, rate_func=linear)
        
        # 31.0-32.0s: Hold on shopping cart scene
        self.wait(1.0)


        # --- Segment 6: Abstract Clockwork (32.0-37.0s) ---
        # 32.0-32.5s: Fade out previous scene elements
        self.play(FadeOut(shopping_cart_body, person_hand, cart_text, fma_overlay), run_time=0.5)

        # 32.5-33.2s: Spheres (masses) appear
        s1 = Circle(radius=0.4, color=BLUE, fill_opacity=0.7).move_to([-3, 1, 0])
        s2 = Circle(radius=0.6, color=RED, fill_opacity=0.7).move_to([0, -1, 0])
        s3 = Circle(radius=0.3, color=GREEN, fill_opacity=0.7).move_to([3, 0.5, 0])
        abstract_group = VGroup(s1, s2, s3)
        self.play(Create(abstract_group), run_time=0.7)

        # 33.2-35.2s: Abstract animation of lines and arrows (forces) interacting with spheres
        # Adding lines and animating them to move with the spheres
        l1 = Line(s1.get_center(), s2.get_center(), color=WHITE)
        l2 = Line(s2.get_center(), s3.get_center(), color=WHITE)
        self.add(l1, l2) # Add lines immediately

        # Define an updater for the lines to keep them connected to the spheres
        def update_lines(mobject):
            l1.put_start_and_end_on(s1.get_center(), s2.get_center())
            l2.put_start_and_end_on(s2.get_center(), s3.get_center())
        
        l1.add_updater(update_lines)
        l2.add_updater(update_lines)

        self.play(
            s1.animate.shift(RIGHT*1 + DOWN*0.5).set_color(YELLOW),
            s2.animate.shift(LEFT*1 + UP*0.5).set_color(BLUE),
            s3.animate.shift(DOWN*1).set_color(RED),
            run_time=2.0,
            rate_func=linear # Smooth, predictable movements
        )
        l1.clear_updaters() # Remove updaters after animation
        l2.clear_updaters()

        # 35.2-36.2s: Text 'Predictable, Measurable Dance' appears
        clockwork_text = Text("Predictable, Measurable Dance", font_size=40, color=YELLOW).to_edge(DOWN)
        self.play(Write(clockwork_text), run_time=1.0)

        # 36.2-37.0s: Hold final scene
        self.wait(0.8)