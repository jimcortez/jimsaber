"""LED and animation management module for the lightsaber"""

import time
import neopixel
import board
import adafruit_led_animation.color as color
# LED Animation library imports
from adafruit_led_animation.animation.chase import Chase
from adafruit_led_animation.animation.solid import Solid
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.sparkle import Sparkle
from adafruit_led_animation.animation.colorcycle import ColorCycle
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.group import AnimationGroup
import config
import microcontroller
from lightsaber_state import LightsaberState
from rgb_led import RGBLED, MonochromeLED

class LEDManager:
    """Manages all LED functionality and animations for the lightsaber"""
    
    def __init__(self):
        """
        Initialize the LED manager
        """
        
        # Initialize NeoPixel strip
        self.strip = neopixel.NeoPixel(
            config.NEOPIXEL_PIN, 
            config.NUM_PIXELS, 
            brightness=config.STRIP_BRIGHTNESS, 
            auto_write=False
        )
        self.strip.fill(0)
        self.strip.show()
        
        # Built-in NeoPixel (single pixel on the board)
        self.builtin_pixel = neopixel.NeoPixel(
            config.BUILTIN_NEOPIXEL_PIN, 
            1, 
            brightness=config.BUILTIN_PIXEL_BRIGHTNESS, 
            auto_write=True  # Auto write for simpler control
        )
        self.builtin_pixel.fill(0)
        
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
        
        # Initialize builtin pixel animations for each power state
        self.builtin_pixel_animations = {}
        for state, animation_config in config.BUILTIN_PIXEL_ANIMATIONS.items():
            self.builtin_pixel_animations[state] = self._create_animation_from_config(animation_config, self.builtin_pixel)
        
        # Create default animation for fallback
        self.builtin_pixel_default_animation = self._create_animation_from_config(config.BUILTIN_PIXEL_ANIMATIONS.get('default', {
            "animation_type": "solid",
            "params": {"color": color.WHITE}
        }), self.builtin_pixel)
        
        # Initialize power button LED animations for each power state
        self.power_button_led_animations = {}
        for state, animation_config in config.POWER_BUTTON_LED_ANIMATIONS.items():
            self.power_button_led_animations[state] = self._create_animation_from_config(animation_config, self.power_button_led)
        
        # Create default animation for fallback
        self.power_button_led_default_animation = self._create_animation_from_config(config.POWER_BUTTON_LED_ANIMATIONS.get('default', {
            "animation_type": "solid",
            "params": {"color": color.WHITE}
        }), self.power_button_led)
        
        # Initialize activity button LED animations for each power state
        self.activity_button_led_animations = {}
        for state, animation_config in config.ACTIVITY_BUTTON_LED_ANIMATIONS.items():
            self.activity_button_led_animations[state] = self._create_animation_from_config(animation_config, self.activity_button_led)
        
        # Create default animation for fallback
        self.activity_button_led_default_animation = self._create_animation_from_config(config.ACTIVITY_BUTTON_LED_ANIMATIONS.get('default', {
            "animation_type": "solid",
            "params": {"color": color.WHITE}
        }), self.activity_button_led)
        
        # Initialize animations
        self._setup_animations()
        
        # Animation group tracking
        self.active_animations = []
        self.animation_group = None
    
    def _create_animation_from_config(self, animation_config, target_pixel):
        """Create an animation instance from animation config for the specified target pixel"""
        animation_type = animation_config["animation_type"]
        params = animation_config["params"]
        
        if animation_type == "solid":
            return Solid(target_pixel, color=params["color"])
        elif animation_type == "rainbow_chase":
            return RainbowChase(
                target_pixel,
                speed=params["speed"],
                size=params["size"],
                spacing=params["spacing"]
            )
        elif animation_type == "sparkle":
            return Sparkle(
                target_pixel,
                speed=params["speed"],
                color=params["color"]
            )
        elif animation_type == "colorcycle":
            return ColorCycle(
                target_pixel,
                speed=params["speed"],
                colors=params["colors"]
            )
        elif animation_type == "pulse":
            return Pulse(
                target_pixel,
                speed=params["speed"],
                color=params["color"],
                period=params.get("period", 5),
                breath=params.get("breath", 0),
                min_intensity=params.get("min_intensity", 0),
                max_intensity=params.get("max_intensity", 1)
            )
        elif animation_type == "chase":
            chase_params = {
                "speed": params["speed"],
                "size": params["size"],
                "spacing": params["spacing"],
                "color": params["color"]
            }
            # Add reverse parameter if specified
            if "reverse" in params:
                chase_params["reverse"] = params["reverse"]
            return Chase(target_pixel, **chase_params)
        else:
            raise ValueError(f"Unknown animation type: {animation_type}. Supported types: solid, rainbow_chase, sparkle, colorcycle, pulse")
    
    def _get_builtin_pixel_animation(self, state):
        """Get builtin pixel animation for the given state, falling back to default if not found"""
        return self.builtin_pixel_animations.get(state, self.builtin_pixel_default_animation)
    
    def _get_power_button_led_animation(self, state):
        """Get power button LED animation for the given state, falling back to default if not found"""
        return self.power_button_led_animations.get(state, self.power_button_led_default_animation)
    
    def _get_activity_button_led_animation(self, state):
        """Get activity button LED animation for the given state, falling back to default if not found"""
        return self.activity_button_led_animations.get(state, self.activity_button_led_default_animation)
    
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
            print(f"Updated active animations: {len(self.active_animations)} animations")
    
    def _get_current_active_animations(self, new_state, power_state_machine):
        """Determine which animations should be active based on current state"""
        active_animations = []
        
        # Add strip animation if color animation is active
        if new_state.color_animation_active:
            current_animation = self.get_current_animation(new_state)
            active_animations.append(current_animation)
        
        # Add power animation if power animation is active
        if new_state.power_animation_active:
            if new_state.has_event(new_state.POWER_OFF_PROGRESS):
                active_animations.append(self.chase_off)
            else:
                active_animations.append(self.chase_on)
        
        # Add builtin pixel animation based on power state and button press
        if new_state.power_state is not None:
            if not new_state.button_pressed:
                builtin_animation = self._get_builtin_pixel_animation_for_power_state(new_state.power_state, power_state_machine)
                if builtin_animation:
                    active_animations.append(builtin_animation)
        
        # Add power button LED animation based on power state and button press
        if new_state.power_state is not None:
            if new_state.button_pressed:
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
        
        # No animation for deep sleep
        if power_state == power_state_machine.DEEP_SLEEP:
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
    
    def _setup_animations(self):
        """Initialize LED animations from STRIP_ANIMATIONS config"""
        # Create animation list from config
        self.animations = []
        for animation_config in config.STRIP_ANIMATIONS:
            animation = self._create_animation_from_config(animation_config, self.strip)
            self.animations.append(animation)
        
        # Create Chase animations for power on/off using SABER_STATE_ANIMATIONS config
        self.chase_on = self._create_animation_from_config(
            config.SABER_STATE_ANIMATIONS['activating'], 
            self.strip
        )
        
        self.chase_off = self._create_animation_from_config(
            config.SABER_STATE_ANIMATIONS['deactivating'], 
            self.strip
        )
    
    def mix_colors(self, color1, color2, weight2):
        """
        Optimized color mixing with bounds checking.
        @param color1: first color, as an (r,g,b) tuple
        @param color2: second color, as an (r,g,b) tuple
        @param weight2: blend weight (ratio) of second color, 0.0 to 1.0
        @return: (r,g,b) tuple, blended color
        """
        weight2 = max(0.0, min(1.0, weight2))
        weight1 = 1.0 - weight2
        return (
            int(color1[0] * weight1 + color2[0] * weight2),
            int(color1[1] * weight1 + color2[1] * weight2),
            int(color1[2] * weight1 + color2[2] * weight2)
        )
    
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
    
    def get_current_animation(self, new_state):
        """Get the current animation from the animations list"""
        return self.animations[new_state.current_animation_index]
    
    
    def cycle_animation(self, new_state):
        """Cycle to the next animation in the list"""
        new_state.current_animation_index = (new_state.current_animation_index + 1) % len(self.animations)
        current_animation = self.get_current_animation(new_state)
        
        # Update idle color based on current animation config
        if new_state.current_animation_index < len(config.STRIP_ANIMATIONS):
            current_config = config.STRIP_ANIMATIONS[new_state.current_animation_index]
            if current_config["animation_type"] == "solid":
                new_color = current_config["params"]["color"]
                config.IDLE_COLOR = (
                    int(new_color[0] / 4),
                    int(new_color[1] / 4),
                    int(new_color[2] / 4)
                )
                print(f"Animation changed to solid color: {new_color}")
            else:
                # Non-solid animation - keep default idle color
                animation_name = current_config["animation_type"]
                print(f"Animation changed to {animation_name}")
        
        # Save the new animation index to NVM
        self.save_animation_index(new_state)
        
        return current_animation
    
    def save_animation_index(self, new_state):
        """Save current animation index to NVM"""
        try:
            # Store the animation index as a single byte
            microcontroller.nvm[0] = new_state.current_animation_index
            print(f"Saved animation index {new_state.current_animation_index} to NVM")
        except Exception as e:
            print(f"Failed to save animation index: {e}")
    
    def load_animation_index(self, new_state):
        """Load animation index from NVM"""
        try:
            # Read the saved animation index from NVM
            saved_index = microcontroller.nvm[0]
            # Validate the index is within bounds of STRIP_ANIMATIONS config
            if 0 <= saved_index < len(config.STRIP_ANIMATIONS):
                new_state.current_animation_index = saved_index
                print(f"Loaded animation index {saved_index} from NVM")
            else:
                print(f"Invalid saved index {saved_index}, using default 0")
                new_state.current_animation_index = 0
        except Exception as e:
            print(f"Failed to load animation index: {e}, using default 0")
            new_state.current_animation_index = 0
    
    @staticmethod
    def load_animation_index_static():
        """Load animation index from NVM during initialization"""
        try:
            # Read the saved animation index from NVM
            saved_index = microcontroller.nvm[0]
            # Validate the index is within bounds of STRIP_ANIMATIONS config
            if 0 <= saved_index < len(config.STRIP_ANIMATIONS):
                print(f"Loaded animation index {saved_index} from NVM")
                return saved_index
            else:
                print(f"Invalid saved index {saved_index}, using default 0")
                return 0
        except Exception as e:
            print(f"Failed to load animation index: {e}, using default 0")
            return 0
    
    def stop_color_animation(self, new_state):
        """Stop the current animation and return to idle color"""
        if new_state.color_animation_active:
            new_state.color_animation_active = False
            # Return to idle color
            if new_state.current == new_state.IDLE:
                self.strip.fill(config.IDLE_COLOR)
                self.strip.show()
            print("Animation stopped")
    
    
    
    def process_tick(self, old_state, new_state, power_state_machine):
        """Process one tick of LED management based on state transitions"""
        # Handle power state machine integration
        self._handle_power_state_led_behavior(new_state, power_state_machine)
        
        # Handle motion events
        if new_state.has_event(new_state.HIT_START):
            new_state.active_color = config.HIT_COLOR
            new_state.previous = new_state.current
            new_state.current = new_state.HIT
            new_state.trigger_time = time.monotonic()
        elif new_state.has_event(new_state.SWING_START):
            new_state.active_color = config.PRIMARY_COLOR
            new_state.previous = new_state.current
            new_state.current = new_state.SWING
            new_state.trigger_time = time.monotonic()
        elif new_state.has_event(new_state.IDLE_START):
            new_state.previous = new_state.current
            new_state.current = new_state.IDLE
            new_state.active_color = None
        
        # Handle button events
        if new_state.has_event(new_state.BUTTON_SHORT_PRESS):
            if not new_state.color_animation_active:
                new_state.add_event(new_state.ANIMATION_CYCLE)
        
        # Handle animation cycling
        if new_state.has_event(new_state.ANIMATION_CYCLE):
            new_state.current_animation_index = (new_state.current_animation_index + 1) % len(self.animations)
            new_state.color_animation_active = True
            new_state.animation_start_time = time.monotonic()
            self.save_animation_index(new_state)
        
        # Handle color animation
        if new_state.color_animation_active:
            elapsed = time.monotonic() - new_state.animation_start_time
            if elapsed >= config.ANIMATION_DURATION:
                new_state.color_animation_active = False
        
        # Update active animations list and create AnimationGroup
        current_active_animations = self._get_current_active_animations(new_state, power_state_machine)
        self._update_active_animations(current_active_animations)
        
        # Handle non-animation LED displays (swing/hit effects, idle state)
        if not new_state.power_animation_active and not new_state.color_animation_active:
            if new_state.current > new_state.IDLE and new_state.active_color:
                # Handle active mode (swing/hit) with color blending
                if new_state.current_sound:  # If sound is playing
                    blend = time.monotonic() - new_state.trigger_time
                    if new_state.current == new_state.SWING:
                        blend = abs(0.5 - blend) * 2.0  # ramp up, down
                    self.strip.fill(self.mix_colors(new_state.active_color, config.IDLE_COLOR, blend))
                    self.strip.show()
                else:
                    # No sound, return to idle
                    self.strip.fill(config.IDLE_COLOR)
                    self.strip.show()
                    new_state.current = new_state.IDLE
            else:
                # Idle state
                if new_state.current == new_state.IDLE:
                    self.strip.fill(config.IDLE_COLOR)
                    self.strip.show()
        
        # Animate all active animations using the AnimationGroup
        if self.animation_group:
            self.animation_group.animate()
        
        return new_state
    
    def _handle_power_state_led_behavior(self, new_state, power_state_machine):
        """Handle LED behavior based on power state machine states"""
        if not hasattr(new_state, 'power_state') or new_state.power_state is None:
            return
        
        # Handle special button press behaviors
        if new_state.button_pressed:
            # Set builtin pixel to white when button is pressed (overrides animation)
            self.set_builtin_pixel_color((255, 255, 255), new_state)
        
        if new_state.power_state == power_state_machine.SLEEPING:
            # SLEEPING: Turn off LEDs
            self.strip.fill(0)
            self.strip.show()
            
        elif new_state.power_state == power_state_machine.ACTIVATING:
            # ACTIVATING: Run power-on animation
            if not new_state.power_animation_active:
                new_state.power_animation_active = True
                new_state.power_animation_start_time = time.monotonic()
            
        elif new_state.power_state == power_state_machine.ACTIVE:
            # ACTIVE: Normal operational LEDs
            pass  # LED behavior handled by AnimationGroup system
            
        elif new_state.power_state == power_state_machine.IDLE:
            # IDLE: Dim/static LEDs
            self.strip.fill(config.IDLE_COLOR)
            self.strip.show()
            
        elif new_state.power_state == power_state_machine.DEACTIVATING:
            # DEACTIVATING: Run power-off animation
            if not new_state.power_animation_active:
                new_state.power_animation_active = True
                new_state.power_animation_start_time = time.monotonic()
            
        elif new_state.power_state == power_state_machine.DEEP_SLEEP:
            # DEEP_SLEEP: Turn off LEDs, turn off builtin pixel and power button LED
            self.strip.fill(0)
            self.strip.show()
            self.set_builtin_pixel_off(new_state)  # Off for deep sleep
            self.set_power_button_led_off()  # Off for deep sleep
            self.set_activity_button_led_off()  # Off for deep sleep
    
    
    
