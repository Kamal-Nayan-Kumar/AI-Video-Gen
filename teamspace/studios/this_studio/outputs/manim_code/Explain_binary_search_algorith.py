from manim import *

class Explain_binary_search_algorith(Scene):
    def construct(self):
        # Title of the algorithm
        title = Text("Binary Search Algorithm").to_edge(UP)
        self.play(Write(title))
        self.wait(1)

        # Introduction text
        intro_text = Text(
            "An efficient algorithm for finding an item from a sorted list of items.",
            font_size=28
        ).next_to(title, DOWN, buff=0.5)
        self.play(Write(intro_text))
        self.wait(2)

        # Example sorted array
        array_values = [5, 12, 18, 25, 33, 40, 56, 71, 88, 92]
        array_text = [Text(str(val)) for val in array_values]
        current_array_mobj = VGroup(*array_text).arrange(RIGHT, buff=0.7).scale(0.7)
        array_rects = VGroup(*[
            Rectangle(width=current_array_mobj[i].width + 0.4, height=current_array_mobj[i].height + 0.4)
            .set_color(BLUE_D).move_to(current_array_mobj[i])
            for i in range(len(array_values))
        ])
        current_array_mobj = VGroup(*[
            VGroup(array_rects[i], array_text[i]) for i in range(len(array_values))
        ]).move_to(ORIGIN)

        self.play(FadeIn(current_array_mobj))
        self.wait(1)

        # Target value
        target_value = 71
        target_text = Text(f"Target: {target_value}").to_corner(UL)
        # Fix: instead of calling to_edge on a numpy array, define a position based on scene dimensions
        # if target_array_pos is meant to be a coordinate, you should define it as such.
        # here, i'm defining it as a point at the top edge for the text that refers to the array.
        target_array_pos = (config.frame_x_radius * LEFT * 0.8) + (config.frame_y_radius * UP * 0.8) 
        
        target_array_label = Text("Array:").next_to(current_array_mobj, UP, buff=1.0)
        self.play(Write(target_text), Write(target_array_label))
        self.wait(1)

        self.play(
            FadeOut(intro_text),
            current_array_mobj.animate.scale(0.8).next_to(title, DOWN, buff=1.0)
        )
        self.wait(1)

        # Binary Search Steps (Simplified for brevity)
        low_idx = 0
        high_idx = len(array_values) - 1

        low_marker = Triangle(fill_opacity=1, color=GREEN).scale(0.15).next_to(current_array_mobj[low_idx], DOWN, buff=0.2)
        high_marker = Triangle(fill_opacity=1, color=RED).scale(0.15).next_to(current_array_mobj[high_idx], DOWN, buff=0.2)

        low_label = Text("Low").next_to(low_marker, DOWN, buff=0.1)
        high_label = Text("High").next_to(high_marker, DOWN, buff=0.1)

        self.play(FadeIn(low_marker, low_label), FadeIn(high_marker, high_label))
        self.wait(1)

        while low_idx <= high_idx:
            mid_idx = (low_idx + high_idx) // 2
            mid_marker = Triangle(fill_opacity=1, color=YELLOW).scale(0.15).next_to(current_array_mobj[mid_idx], DOWN, buff=0.2)
            mid_label = Text("Mid").next_to(mid_marker, DOWN, buff=0.1)

            self.play(FadeIn(mid_marker, mid_label))
            self.wait(1)

            current_array_mobj[mid_idx].animate.set_color(YELLOW)
            self.play(FadeOut(mid_marker, mid_label)) # Fade out for re-drawing if loop continues

            if array_values[mid_idx] == target_value:
                found_text = Text(f"Found {target_value} at index {mid_idx}!").next_to(title, DOWN, buff=0.5)
                self.play(Write(found_text))
                self.wait(2)
                break
            elif array_values[mid_idx] < target_value:
                low_idx = mid_idx + 1
                self.play(low_marker.animate.next_to(current_array_mobj[low_idx], DOWN, buff=0.2))
            else:
                high_idx = mid_idx - 1
                self.play(high_marker.animate.next_to(current_array_mobj[high_idx], DOWN, buff=0.2))

            self.wait(1)

        if low_idx > high_idx:
            not_found_text = Text(f"{target_value} not found in the array.").next_to(title, DOWN, buff=0.5)
            self.play(Write(not_found_text))
            self.wait(2)

        self.play(FadeOut(title, target_text, current_array_mobj, low_marker, high_marker, low_label, high_label, target_array_label))
        self.wait(1)