#!/usr/bin/env python3
"""
LED Counter - Slowly enables each pixel on the saber strip, one every second.
Starts with the first 100 pixels enabled, then turns on the next one every second.
Uses red color to count how many LEDs there are on the strip.
"""

import time
import neopixel
import digitalio
import config

def main():
    """Main function to run the LED counter"""
    print("LED Counter - Starting...")
    print(f"Config: {config.NUM_PIXELS} pixels on pin {config.NEOPIXEL_PIN}")
    print(f"Brightness: {config.STRIP_BRIGHTNESS}")
    
    # Enable the prop wing board first
    print("Enabling prop wing board...")
    prop_wing_enable_pin = digitalio.DigitalInOut(config.PROP_WING_PIN)
    prop_wing_enable_pin.direction = digitalio.Direction.OUTPUT
    prop_wing_enable_pin.value = True
    print("Prop wing board enabled")
    
    # Initialize NeoPixel strip using config settings
    strip = neopixel.NeoPixel(
        config.NEOPIXEL_PIN, 
        config.NUM_PIXELS, 
        brightness=config.STRIP_BRIGHTNESS, 
        auto_write=False
    )
    
    # Clear the strip initially
    strip.fill(0)
    strip.show()
    
    # Red color (RGB)
    RED_COLOR = (255, 0, 0)
    
    print("Starting LED count...")
    print("First 100 pixels will be enabled immediately, then one more every second")
    
    # Enable first 100 pixels immediately
    for i in range(min(100, config.NUM_PIXELS)):
        strip[i] = RED_COLOR
    
    strip.show()
    print(f"Enabled first {min(100, config.NUM_PIXELS)} pixels")
    
    # If we have more than 100 pixels, enable one more every second
    if config.NUM_PIXELS > 100:
        print("Now enabling one pixel every second...")
        
        for pixel_num in range(100, config.NUM_PIXELS):
            # Wait 1 second
            time.sleep(1.0)
            
            # Enable the next pixel
            strip[pixel_num] = RED_COLOR
            strip.show()
            
            print(f"Pixel {pixel_num + 1}/{config.NUM_PIXELS} enabled")
    
    print(f"\nAll {config.NUM_PIXELS} pixels are now enabled!")
    print("Press Ctrl+C to exit and turn off all LEDs")
    
    try:
        # Keep the LEDs on until user interrupts
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nShutting down...")
        # Turn off all LEDs
        strip.fill(0)
        strip.show()
        # Disable the prop wing board
        prop_wing_enable_pin.value = False
        print("All LEDs turned off and prop wing board disabled. Goodbye!")

if __name__ == "__main__":
    main()
