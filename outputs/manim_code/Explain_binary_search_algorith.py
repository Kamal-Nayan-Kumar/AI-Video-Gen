from manim import *
import numpy as np

class ExplainerScene(Scene):
    def construct(self):
        # --- Helper for array creation ---
        def create_array_mobject(numbers, colors=None, scale=1.0):
            array_elements = VGroup()
            for i, num in enumerate(numbers):
                rect = Rectangle(width=1.0 * scale, height=1.0 * scale, color=WHITE, fill_opacity=0.1)
                if colors and i < len(colors):
                    rect.set_color(colors[i])
                text = Text(str(num), font_size=28 * scale, color=WHITE)
                cell = VGroup(rect, text)
                array_elements.add(cell)
            array_elements.arrange(RIGHT, buff=0.1 * scale)
            return array_elements

        # --- Segment 1: 0.0-6.0s (Total Duration: 6.0s) ---
        title = Text("బైనరీ సెర్చ్ అల్గారిథమ్", font_size=56, color=BLUE)
        self.play(Write(title), run_time=1.5)
        self.wait(0.5)

        # Unsorted data representation
        unsorted_numbers = [12, 5, 23, 2, 16, 91, 8, 56, 38, 72]
        unsorted_array_mobj = create_array_mobject(unsorted_numbers, scale=0.7)
        unsorted_array_mobj.next_to(title, DOWN, buff=1.0)
        self.play(FadeIn(unsorted_array_mobj), run_time=1.5)
        self.wait(0.5)

        # Sorted data definition
        numbers = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]
        sorted_array_mobj = create_array_mobject(numbers, scale=0.7)
        sorted_array_mobj.move_to(unsorted_array_mobj.get_center())

        # Animate sorting: Fade out unsorted, fade in sorted
        # Also, slightly scale down and move title up for next segments
        self.play(
            FadeOut(unsorted_array_mobj),
            Transform(title, Text("బైనరీ సెర్చ్ అల్గారిథమ్", font_size=40, color=BLUE).to_edge(UP)),
            FadeIn(sorted_array_mobj),
            run_time=2.0
        )
        current_array_mobj = sorted_array_mobj # Store reference to the sorted array
        # Total for Segment 1: 1.5 + 0.5 + 1.5 + 0.5 + 2.0 = 6.0s

        # --- Segment 2: 6.0-12.5s (Total Duration: 6.5s) ---
        self.play(FadeOut(title), run_time=0.5) # 6.0 + 0.5 = 6.5s

        # Scale up and position the sorted array for clarity
        target_array_pos = current_array_mobj.get_center().copy().to_edge(UP, buff=1.0)
        target_scale_factor = 0.8 / 0.7 # Scale from initial 0.7 to desired 0.8
        
        self.play(
            current_array_mobj.animate.scale(target_scale_factor).move_to(target_array_pos),
            run_time=0.8 # 6.5 + 0.8 = 7.3s
        )

        sorted_list_text = Text("Sorted List", font_size=36, color=YELLOW)
        sorted_list_text.next_to(current_array_mobj, DOWN, buff=0.5)

        self.play(Write(sorted_list_text), run_time=1.0) # 7.3 + 1.0 = 8.3s
        self.wait(4.2) # 8.3 + 4.2 = 12.5s. Perfect.

        # --- Segment 3: 12.5-19.5s (Total Duration: 7.0s) ---
        target_value = 23
        target_text = Text(f"Target: {target_value}", font_size=40, color=BLUE)
        target_text.to_edge(LEFT).shift(UP*1.5)
        self.play(FadeIn(target_text), run_time=0.8) # 12.5 + 0.8 = 13.3s

        low_idx = 0
        high_idx = len(numbers) - 1 # 9
        mid_idx = (low_idx + high_idx) // 2 # 4 (value 16)
        
        mid_info_group = VGroup()
        mid_info_group.add(MathTex(f"\\text{{low}}={low_idx}, \\text{{high}}={high_idx}", font_size=36))
        mid_info_group.add(MathTex(f"\\text{{mid}} = (\\text{{low}} + \\text{{high}}) / 2 = {mid_idx}", font_size=36))
        mid_info_group.arrange(DOWN, buff=0.2).next_to(current_array_mobj, DOWN*1.5, buff=0.5)

        self.play(Write(mid_info_group), run_time=1.5) # 13.3 + 1.5 = 14.8s
        self.wait(0.5) # 15.3s

        mid_element_mobj = current_array_mobj[mid_idx] # This is 16
        self.play(
            mid_element_mobj.animate.set_color(YELLOW).scale(1.2),
            mid_info_group.animate.shift(UP*0.5).set_opacity(0.5), # Shrink and fade prev mid info slightly
            run_time=1.2 # 15.3 + 1.2 = 16.5s
        )
        self.wait(0.5) # 17.0s

        comparison_arrow = Arrow(target_text.get_bottom(), mid_element_mobj.get_top(), buff=0.2, color=BLUE)
        comparison_text = Text("Compare!", font_size=32, color=GREEN).next_to(comparison_arrow, UP)

        self.play(GrowArrow(comparison_arrow), Write(comparison_text), run_time=1.5) # 17.0 + 1.5 = 18.5s
        self.wait(1.0) # 18.5 + 1.0 = 19.5s. Perfect.

        # --- Segment 4: 19.5-27.0s (Total Duration: 7.5s) ---
        # Target (23) > Middle (16), so discard left half
        comparison_result_text = Text(f"{target_value} > {numbers[mid_idx]}", font_size=36, color=GREEN)
        comparison_result_text.move_to(target_text.get_center())

        self.play(
            Transform(target_text, comparison_result_text), # Transform target text to comparison result
            FadeOut(comparison_arrow, comparison_text),
            mid_info_group.animate.set_opacity(0), # Fade out old mid info completely
            run_time=1.5 # 19.5 + 1.5 = 21.0s
        )
        self.wait(0.5) # 21.5s

        # Fade out left half (indices 0 to mid_idx)
        faded_elements = VGroup(*[current_array_mobj[i] for i in range(mid_idx + 1)]) # 0 to 4
        self.play(
            faded_elements.animate.set_opacity(0.2).set_color(RED),
            run_time=2.0 # 21.5 + 2.0 = 23.5s
        )
        self.wait(0.5) # 24.0s

        # Highlight new active sub-array
        low_idx_current = mid_idx + 1 # new low is 5 (index of 23)
        high_idx_current = len(numbers) - 1 # 9 (index of 91)
        active_sub_array = VGroup(*[current_array_mobj[i] for i in range(low_idx_current, high_idx_current + 1)])
        surrounding_rect = SurroundingRectangle(active_sub_array, color=GREEN, buff=0.1)

        self.play(Create(surrounding_rect), run_time=1.5) # 24.0 + 1.5 = 25.5s
        self.wait(1.5) # 25.5 + 1.5 = 27.0s. Perfect.

        # --- Segment 5: 27.0-34.0s (Total Duration: 7.0s) ---
        # Clear previous comparison result
        self.play(FadeOut(target_text), run_time=0.5) # 27.0 + 0.5 = 27.5s

        # Iteration 2: Active sub-array [23, 38, 56, 72, 91] (indices 5 to 9)
        mid_idx_2 = (low_idx_current + high_idx_current) // 2 # (5+9)//2 = 7 (value 56)
        mid_element_mobj_2 = current_array_mobj[mid_idx_2]

        mid_info_group_2 = VGroup()
        mid_info_group_2.add(MathTex(f"\\text{{low}}={low_idx_current}, \\text{{high}}={high_idx_current}", font_size=36))
        mid_info_group_2.add(MathTex(f"\\text{{mid}} = (\\text{{low}} + \\text{{high}}) / 2 = {mid_idx_2}", font_size=36))
        mid_info_group_2.arrange(DOWN, buff=0.2).next_to(current_array_mobj, DOWN*1.5, buff=0.5)

        self.play(
            Write(mid_info_group_2),
            mid_element_mobj_2.animate.set_color(YELLOW).scale(1.2),
            run_time=1.5 # 27.5 + 1.5 = 29.0s
        )
        
        # Target (23) < Current Mid (56)
        comparison_result_text_2 = Text(f"{target_value} < {numbers[mid_idx_2]}", font_size=36, color=RED)
        comparison_result_text_2.move_to(target_text.get_center()) # Reusing target_text's last position

        self.play(Write(comparison_result_text_2), run_time=0.7) # 29.0 + 0.7 = 29.7s
        self.wait(0.3) # 30.0s

        # Fade out right half (from mid_idx_2 to high_idx_current)
        faded_elements_2 = VGroup(*[current_array_mobj[i] for i in range(mid_idx_2, high_idx_current + 1)])
        self.play(
            faded_elements_2.animate.set_opacity(0.2).set_color(RED),
            run_time=1.0 # 30.0 + 1.0 = 31.0s
        )

        # Update active sub-array for next iteration [23, 38] (indices 5 to 6)
        high_idx_new = mid_idx_2 - 1 # 6
        active_sub_array_new = VGroup(*[current_array_mobj[i] for i in range(low_idx_current, high_idx_new + 1)])
        
        self.play(
            Transform(surrounding_rect, SurroundingRectangle(active_sub_array_new, color=GREEN, buff=0.1)),
            FadeOut(mid_info_group_2), FadeOut(comparison_result_text_2),
            run_time=0.8 # 31.0 + 0.8 = 31.8s
        )
        
        # Iteration 3: Active sub-array [23, 38] (indices 5 to 6)
        low_idx_3 = low_idx_current # 5
        high_idx_3 = high_idx_new # 6
        mid_idx_3 = (low_idx_3 + high_idx_3) // 2 # (5+6)//2 = 5 (value 23) -> TARGET FOUND!
        final_mid_element_mobj = current_array_mobj[mid_idx_3]

        mid_info_group_3 = VGroup()
        mid_info_group_3.add(MathTex(f"\\text{{low}}={low_idx_3}, \\text{{high}}={high_idx_3}", font_size=36))
        mid_info_group_3.add(MathTex(f"\\text{{mid}} = (\\text{{low}} + \\text{{high}}) / 2 = {mid_idx_3}", font_size=36))
        mid_info_group_3.arrange(DOWN, buff=0.2).next_to(current_array_mobj, DOWN*1.5, buff=0.5)
        
        found_text = Text(f"Target {target_value} Found!", font_size=40, color=GREEN)
        found_text.next_to(current_array_mobj, DOWN, buff=1.5)

        self.play(
            Write(mid_info_group_3),
            final_mid_element_mobj.animate.set_color(GREEN).scale(1.5).set_opacity(1.0), # Emphasize found
            Write(found_text),
            run_time=1.7 # 31.8 + 1.7 = 33.5s
        )

        # Clean up scene for final segment
        self.play(
            FadeOut(current_array_mobj),
            FadeOut(sorted_list_text),
            FadeOut(mid_info_group_3),
            FadeOut(found_text),
            FadeOut(surrounding_rect),
            run_time=0.5 # 33.5 + 0.5 = 34.0s. Perfect.

        )

        # --- Segment 6: 34.0-39.5s (Total Duration: 5.5s) ---
        time_complexity_text = MathTex("Time Complexity: O(\\log n)", font_size=48, color=BLUE)
        self.play(Write(time_complexity_text.to_edge(UP, buff=0.5)), run_time=1.5) # 34.0 + 1.5 = 35.5s

        # Create axes
        axes = Axes(
            x_range=[0, 10, 1],
            y_range=[0, 10, 1], # Y-axis scale up to 10 for O(n) to be visible
            x_length=7,
            y_length=5,
            axis_config={"color": GRAY, "font_size": 24},
            tips=False
        ).to_edge(DOWN).shift(LEFT*1.5)
        
        labels = axes.get_axis_labels(x_label="n", y_label="Operations")
        self.play(Create(axes), Write(labels), run_time=1.0) # 35.5 + 1.0 = 36.5s

        # O(n) linear growth
        linear_func = axes.get_graph(lambda x: x, color=RED, x_range=[0.1, 10])
        linear_label = MathTex("O(n)", color=RED, font_size=32).next_to(linear_func, RIGHT, buff=0.2)
        
        # O(log n) logarithmic growth
        # Scale log2(x) for better visual comparison within the 0-10 y-range.
        # log2(10) is approx 3.32. Scaling by (10/log2(10)) makes it hit top of graph.
        log_scale_factor = 10 / np.log2(10) 
        log_func = axes.get_graph(lambda x: np.log2(x) * log_scale_factor, color=GREEN, x_range=[0.1, 10])
        log_label = MathTex("O(\\log n)", color=GREEN, font_size=32).next_to(log_func, LEFT, buff=0.2)

        self.play(
            Create(linear_func),
            Write(linear_label),
            run_time=1.0 # 36.5 + 1.0 = 37.5s
        )
        self.play(
            Create(log_func),
            Write(log_label),
            run_time=1.0 # 37.5 + 1.0 = 38.5s
        )
        self.wait(1.0) # 38.5 + 1.0 = 39.5s. Perfect.