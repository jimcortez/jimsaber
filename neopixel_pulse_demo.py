"""Standalone demonstration of NeoPixel red pulse animation using Adafruit libraries

This file demonstrates how to use the adafruit_led_animation library to create
a pulsing red LED animation on a NeoPixel strip. This is a sample file for
bug reporting purposes.
"""

import time
import board
import neopixel
import adafruit_led_animation.color as color
from adafruit_led_animation.animation.pulse import Pulse

def main():
    """Main demonstration function"""
    
    # Initialize NeoPixel strip
    # Using a single pixel for simplicity (like the builtin pixel in led_manager.py)
    pixel = neopixel.NeoPixel(
        board.NEOPIXEL,  # Use built-in NeoPixel pin
        1,               # Single pixel
        brightness=0.5,  # Moderate brightness
        auto_write=False # Let animation control when to write
    )
    
    # Create a red pulse animation
    # This matches the configuration used in config.py for sleeping state
    red_pulse = Pulse(
        pixel,           # Target pixel object
        speed=0.01,       # Animation speed (1.0 is moderate)
        color=color.RED  # Red color for pulsing
    )
    
    print("Starting red pulse animation...")
    print("Press Ctrl+C to stop")
    
    try:
        # Run the animation for demonstration
        # In a real application, this would be in a main loop
        while True:
            # Animate one frame
            red_pulse.animate()
            
            # Small delay to prevent overwhelming the system
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nStopping animation...")
        
    finally:
        # Clean up - turn off the LED
        pixel.fill((0, 0, 0))
        pixel.show()
        print("LED turned off")

if __name__ == "__main__":
    main()
