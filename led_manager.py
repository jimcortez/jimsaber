"""Button LED and built-in LED state management module for the lightsaber"""

import time
import neopixel
import board
import adafruit_led_animation.color as color
import config
from lightsaber_state import LightsaberState
from rgb_led import RGBLED, OnOffLed
from led_utils import LEDAnimationManager, create_animation_from_config
from state_machines.power_state_machine import PowerStateMachineState

class LEDManager:
    """Manages button LED and built-in LED state management for the lightsaber"""
    
    def __init__(self):
        """
        Initialize the LED manager
        """
        
        # Built-in NeoPixel (single pixel on the board)
        self.builtin_pixel = neopixel.NeoPixel(
            config.BUILTIN_NEOPIXEL_PIN, 
            1, 
            brightness=config.BUILTIN_PIXEL_BRIGHTNESS, 
            auto_write=False  # Let animations control when to write
        )
        self.builtin_pixel.fill(0)
        self.builtin_pixel.show()  # Explicitly show the initial off state
        
        # Power button RGB LED (high-current MOSFET controlled)
        self.power_button_led = RGBLED(
            config.POWER_BUTTON_LED_RED,
            config.POWER_BUTTON_LED_GREEN, 
            config.POWER_BUTTON_LED_BLUE,
            brightness=config.POWER_BUTTON_LED_BRIGHTNESS,
            auto_write=True
        )
        self.power_button_led.fill((0, 0, 0))  # Start off
        
        # Activity button LED (monochrome PWM controlled)
        self.activity_button_led = OnOffLed(
            config.ACTIVITY_BUTTON_LED_PIN,
            brightness=config.ACTIVITY_BUTTON_LED_BRIGHTNESS,
            auto_write=True
        )
        self.activity_button_led.fill((0, 0, 0))  # Start off
        
        # Initialize animation managers for each LED type
        self.builtin_pixel_manager = LEDAnimationManager(self.builtin_pixel, config.BUILTIN_PIXEL_ANIMATIONS)
        self.power_button_led_manager = LEDAnimationManager(self.power_button_led, config.POWER_BUTTON_LED_ANIMATIONS)
        self.activity_button_led_manager = LEDAnimationManager(self.activity_button_led, config.ACTIVITY_BUTTON_LED_ANIMATIONS)
        
        # Individual animation tracking for each LED
        self.builtin_pixel_animation = None
        self.power_button_led_animation = None
        self.activity_button_led_animation = None
    
    def _get_builtin_pixel_animation(self, state):
        """Get builtin pixel animation for the given state, falling back to default if not found"""
        return self.builtin_pixel_manager.get_animation(state)
    
    def _get_power_button_led_animation(self, state):
        """Get power button LED animation for the given state, falling back to default if not found"""
        return self.power_button_led_manager.get_animation(state)
    
    def _get_activity_button_led_animation(self, state):
        """Get activity button LED animation for the given state, falling back to default if not found"""
        return self.activity_button_led_manager.get_animation(state)
    
    
    def _get_animation_for_power_state(self, power_state, animation_type):
        """
        Generic method to get animation for the given power state and animation type.
        Falls back to default animation if no specific animation is found.
        
        Args:
            power_state: The power state from power_state_machine
            power_state_machine: The power state machine instance
            animation_type: Type of animation ('builtin_pixel', 'power_button_led', 'activity_button_led')
        
        Returns:
            Animation object or None for DEEP_SLEEP state
        """
       
        # Get the animation key for this power state
        animation_key = PowerStateMachineState.get_state_name(power_state).lower()
        
        # Get the appropriate animation based on type
        if animation_type == 'builtin_pixel':
            return self._get_builtin_pixel_animation(animation_key)
        elif animation_type == 'power_button_led':
            return self._get_power_button_led_animation(animation_key)
        elif animation_type == 'activity_button_led':
            return self._get_activity_button_led_animation(animation_key)
        else:
            return None
    
    def process_tick(self, old_state, new_state, power_state_machine):
        """Process one tick of button LED management based on state transitions"""
        
        # Handle power button LED animation
        new_power_button_animation = None
        if new_state.power_button_pressed and old_state.power_button_pressed == False:
            new_power_button_animation = self._get_power_button_led_animation("pressed")
        else:
            new_power_button_animation = self._get_animation_for_power_state(new_state.power_state, 'power_button_led')
        
        # Check if power button animation changed
        if new_power_button_animation != self.power_button_led_animation:
            self.power_button_led_animation = new_power_button_animation
        
        # Handle activity button LED animation
        new_activity_button_animation = None
        if new_state.activity_button_pressed and old_state.activity_button_pressed == False:
            # Use pressed animation when button is pressed
            new_activity_button_animation = self._get_activity_button_led_animation('pressed')
        else:
            new_activity_button_animation = self._get_animation_for_power_state(new_state.power_state, 'activity_button_led')

        # Check if activity button animation changed
        if new_activity_button_animation != self.activity_button_led_animation:
            self.activity_button_led_animation = new_activity_button_animation

        # Handle builtin pixel animation
        new_builtin_pixel_animation = self._get_animation_for_power_state(new_state.power_state, 'builtin_pixel')
        
        # Check if builtin pixel animation changed
        if new_builtin_pixel_animation != self.builtin_pixel_animation:
            self.builtin_pixel_animation = new_builtin_pixel_animation
        
        # Animate each active animation directly
        if self.builtin_pixel_animation:
            self.builtin_pixel_animation.animate()
        if self.power_button_led_animation:
            self.power_button_led_animation.animate()
        if self.activity_button_led_animation:
            self.activity_button_led_animation.animate()
        
        return new_state
