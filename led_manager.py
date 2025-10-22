"""Button LED and built-in LED state management module for the lightsaber"""

import time
import neopixel
import board
import adafruit_led_animation.color as color
import config
from adafruit_led_animation.group import AnimationGroup
from lightsaber_state import LightsaberState
from rgb_led import RGBLED, MonochromeLED
from led_utils import LEDAnimationManager, create_animation_from_config

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
        self.activity_button_led = MonochromeLED(
            config.ACTIVITY_BUTTON_LED_PIN,
            brightness=config.ACTIVITY_BUTTON_LED_BRIGHTNESS,
            auto_write=True
        )
        self.activity_button_led.fill((0, 0, 0))  # Start off
        
        # Initialize animation managers for each LED type
        self.builtin_pixel_manager = LEDAnimationManager(self.builtin_pixel, config.BUILTIN_PIXEL_ANIMATIONS)
        self.power_button_led_manager = LEDAnimationManager(self.power_button_led, config.POWER_BUTTON_LED_ANIMATIONS)
        self.activity_button_led_manager = LEDAnimationManager(self.activity_button_led, config.ACTIVITY_BUTTON_LED_ANIMATIONS)
        
        
        # Animation group tracking
        self.active_animations = []
        self.animation_group = None
    
    def _get_builtin_pixel_animation(self, state):
        """Get builtin pixel animation for the given state, falling back to default if not found"""
        return self.builtin_pixel_manager.get_animation(state)
    
    def _get_power_button_led_animation(self, state):
        """Get power button LED animation for the given state, falling back to default if not found"""
        return self.power_button_led_manager.get_animation(state)
    
    def _get_activity_button_led_animation(self, state):
        """Get activity button LED animation for the given state, falling back to default if not found"""
        return self.activity_button_led_manager.get_animation(state)
    
    def _update_active_animations(self, animations_list):
        """Update the list of active animations and recreate the AnimationGroup if needed"""
        # Check if the animations list has changed
        if animations_list != self.active_animations:
            self.active_animations = animations_list
            # Create new AnimationGroup with the current active animations
            if self.active_animations:
                
                self.animation_group = AnimationGroup(*self.active_animations)
            else:
                self.animation_group = None
    
    def _get_current_active_animations(self, new_state, power_state_machine):
        """Determine which button LED animations should be active based on current state"""
        active_animations = []
        
        # Add builtin pixel animation based on power state and button press
        if new_state.power_state is not None:
            if not new_state.power_button_pressed:
                builtin_animation = self._get_builtin_pixel_animation_for_power_state(new_state.power_state, power_state_machine)
                if builtin_animation:
                    active_animations.append(builtin_animation)
        
        # Add power button LED animation based on power state and button press
        if new_state.power_state is not None:
            if new_state.power_button_pressed:
                # Use pressed animation when button is pressed
                power_animation = self._get_power_button_led_animation('pressed')
            else:
                power_animation = self._get_power_button_led_animation_for_power_state(new_state.power_state, power_state_machine)
            if power_animation:
                active_animations.append(power_animation)
        
        # Add activity button LED animation based on power state and button press
        if new_state.power_state is not None:
            if new_state.activity_button_pressed:
                # Use pressed animation when button is pressed
                activity_animation = self._get_activity_button_led_animation('pressed')
            else:
                activity_animation = self._get_activity_button_led_animation_for_power_state(new_state.power_state, power_state_machine)
            if activity_animation:
                active_animations.append(activity_animation)
        
        return active_animations
    
    def _get_animation_for_power_state(self, power_state, power_state_machine, animation_type):
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
        # Map power states to animation keys
        power_state_mapping = {
            power_state_machine.SLEEPING: 'sleeping',
            power_state_machine.ACTIVATING: 'activating', 
            power_state_machine.ACTIVE: 'active',
            power_state_machine.IDLE: 'idle',
            power_state_machine.DEACTIVATING: 'deactivating'
        }
        
        # No animation for light or deep sleep
        if power_state == power_state_machine.DEEP_SLEEP or power_state == power_state_machine.LIGHT_SLEEP:
            return None
        
        # Get the animation key for this power state
        animation_key = power_state_mapping.get(power_state)
        if animation_key is None:
            return None
        
        # Get the appropriate animation based on type
        if animation_type == 'builtin_pixel':
            return self._get_builtin_pixel_animation(animation_key)
        elif animation_type == 'power_button_led':
            return self._get_power_button_led_animation(animation_key)
        elif animation_type == 'activity_button_led':
            return self._get_activity_button_led_animation(animation_key)
        else:
            return None
    
    def _get_builtin_pixel_animation_for_power_state(self, power_state, power_state_machine):
        """Get builtin pixel animation for the given power state"""
        return self._get_animation_for_power_state(power_state, power_state_machine, 'builtin_pixel')
    
    def _get_power_button_led_animation_for_power_state(self, power_state, power_state_machine):
        """Get power button LED animation for the given power state"""
        return self._get_animation_for_power_state(power_state, power_state_machine, 'power_button_led')
    
    def _get_activity_button_led_animation_for_power_state(self, power_state, power_state_machine):
        """Get activity button LED animation for the given power state"""
        return self._get_animation_for_power_state(power_state, power_state_machine, 'activity_button_led')
    
    
    
    def set_builtin_pixel_color(self, color, new_state):
        """Set the built-in NeoPixel color"""
        try:
            self.builtin_pixel[0] = color
            new_state.builtin_pixel_color = color
        except Exception as e:
            print(f"Failed to set built-in pixel color: {e}")
    
    def set_builtin_pixel_off(self, new_state):
        """Turn off the built-in NeoPixel"""
        self.set_builtin_pixel_color((0, 0, 0), new_state)
    
    def set_power_button_led_color(self, color):
        """Set the power button RGB LED color"""
        try:
            self.power_button_led[0] = color
        except Exception as e:
            print(f"Failed to set power button LED color: {e}")
    
    def set_power_button_led_off(self):
        """Turn off the power button RGB LED"""
        self.set_power_button_led_color((0, 0, 0))
    
    def set_activity_button_led_color(self, color):
        """Set the activity button LED color (converted to brightness)"""
        try:
            self.activity_button_led[0] = color
        except Exception as e:
            print(f"Failed to set activity button LED color: {e}")
    
    def set_activity_button_led_off(self):
        """Turn off the activity button LED"""
        self.set_activity_button_led_color((0, 0, 0))
    
    
    
    
    def process_tick(self, old_state, new_state, power_state_machine):
        """Process one tick of button LED management based on state transitions"""
        # Handle power state machine integration
        self._handle_power_state_led_behavior(new_state, power_state_machine)
        
        # Update active animations list and create AnimationGroup
        current_active_animations = self._get_current_active_animations(new_state, power_state_machine)
        self._update_active_animations(current_active_animations)
        
        # Animate all active animations using the AnimationGroup
        if self.animation_group:
            self.animation_group.animate()
        
        return new_state
    
    def _handle_power_state_led_behavior(self, new_state, power_state_machine):
        """Handle button LED behavior based on power state machine states"""
        if not hasattr(new_state, 'power_state') or new_state.power_state is None:
            return
        
        if new_state.power_state == power_state_machine.DEEP_SLEEP:
            # DEEP_SLEEP: Turn off builtin pixel and power button LED
            self.set_builtin_pixel_off(new_state)  # Off for deep sleep
            self.set_power_button_led_off()  # Off for deep sleep
            self.set_activity_button_led_off()  # Off for deep sleep
    
    
    
