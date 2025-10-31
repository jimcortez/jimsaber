"""
SaberActivate - Duration-based animation for saber activation effects.

This module provides a custom animation class that creates a solid color
wave effect that advances across the LED strip in a specified duration,
regardless of the frame rate. Uses a nonlinear curve for more dynamic animation.
"""

import math
from lib.adafruit_led_animation.animation import Animation
from lib.adafruit_led_animation.color import BLACK
from lib.adafruit_led_animation import monotonic_ms


class SaberActivate(Animation):
    """
    A duration-based animation for saber activation effects.
    
    This class creates a "turning on" effect where each LED turns on in sequence
    during the specified duration and stays on once activated. Only changes colors
    of LEDs being activated, preserving any existing patterns on the strip.
    
    :param pixel_object: The initialised LED object.
    :param float speed: Animation speed in seconds, e.g. ``0.1``.
    :param color: Animation color in ``(r, g, b)`` tuple, or ``0x000000`` hex format.
    :param float duration: Target duration for the complete animation in seconds.
    :param background_color: Background color in ``(r, g, b)`` tuple, or ``0x000000`` hex format.
                             Defaults to BLACK.
    :param bool reverse: Animates the wave in the reverse order. Defaults to ``False``.
    :param Optional[string] name: A human-readable name for the Animation.
                                  Used by the to string function.
    """

    def __init__(
        self,
        pixel_object,
        speed,
        color,
        duration,
        background_color=BLACK,
        reverse=False,
        name=None,
    ):
        # Initialize base Animation class
        super().__init__(pixel_object, speed, color, name=name)
        
        # Animation parameters
        self.duration = duration
        self.background_color = background_color
        self.reverse = reverse
        
        # Animation state
        self._animation_start_time = None
        self._num_pixels = len(pixel_object)

    def draw(self):
        """
        Draw the duration-based animation.
        Each LED turns on in sequence during the duration and stays on.
        Uses a nonlinear curve for more dynamic animation similar to the original implementation.
        Only changes colors of LEDs being activated, preserving existing patterns.
        """
        # Initialize start time on first draw
        if self._animation_start_time is None:
            self._animation_start_time = monotonic_ms()
        
        # Calculate elapsed time and progress
        elapsed_ms = monotonic_ms() - self._animation_start_time
        elapsed_seconds = elapsed_ms / 1000.0
        
        # Calculate how far along the animation should be
        fraction = min(elapsed_seconds / self.duration, 1.0)
        
        # Apply nonlinear curve for more dynamic animation (similar to original implementation)
        # Using power of 0.5 creates a curve that starts fast and slows down
        if self.reverse:
            # For reverse, invert the fraction first, then apply curve
            fraction = 1.0 - fraction
            fraction = math.pow(fraction, 0.5)
            fraction = 1.0 - fraction  # Invert back for reverse direction
        else:
            # For forward, apply the nonlinear curve directly
            fraction = math.pow(fraction, 0.5)
        
        # Calculate how many LEDs should be on based on nonlinear progress
        threshold = int(self._num_pixels * fraction + 0.5)
        
        # Calculate how many LEDs should be on based on progress
        if self.reverse:
            # For reverse, count from the end
            leds_to_turn_on = threshold
            start_index = self._num_pixels - leds_to_turn_on
            end_index = self._num_pixels
        else:
            # For forward, count from the beginning
            leds_to_turn_on = threshold
            start_index = 0
            end_index = leds_to_turn_on
        
        # Only change colors of LEDs that are being activated
        # This preserves existing patterns and only updates LEDs as they're activated
        pixels = self.pixel_object
        for i in range(start_index, end_index):
            if 0 <= i < self._num_pixels:
                pixels[i] = self._color

        # Check if animation is complete
        if elapsed_seconds >= self.duration:
            # Reset for next cycle
            self.reset()
            self.cycle_complete = True

    def reset(self):
        """
        Resets to the first state and clears the start time.
        """
        self._animation_start_time = None
    
    def update_duration(self, new_duration):
        """
        Update the animation duration dynamically.
        This allows the animation to adapt to different sound effect durations.
        
        :param float new_duration: New duration for the animation in seconds.
        """
        self.duration = new_duration
        # Reset the animation if it's currently running to use the new duration
        if self._animation_start_time is not None:
            self.reset()