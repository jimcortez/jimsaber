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
import config
import microcontroller
from lightsaber_state import LightsaberState
from rgb_led import RGBLED

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
        
        # Initialize animations
        self._setup_animations()
    
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
        else:
            raise ValueError(f"Unknown animation type: {animation_type}. Supported types: solid, rainbow_chase, sparkle, colorcycle, pulse")
    
    def _get_builtin_pixel_animation(self, state):
        """Get builtin pixel animation for the given state, falling back to default if not found"""
        return self.builtin_pixel_animations.get(state, self.builtin_pixel_default_animation)
    
    def _get_power_button_led_animation(self, state):
        """Get power button LED animation for the given state, falling back to default if not found"""
        return self.power_button_led_animations.get(state, self.power_button_led_default_animation)
    
    def _setup_animations(self):
        """Initialize LED animations from STRIP_ANIMATIONS config"""
        # Create animation list from config
        self.animations = []
        for animation_config in config.STRIP_ANIMATIONS:
            animation = self._create_animation_from_config(animation_config, self.strip)
            self.animations.append(animation)
        
        # Create Chase animations for power on/off
        self.chase_on = Chase(
            self.strip,
            speed=config.CHASE_SPEED,
            size=config.CHASE_SIZE,
            spacing=config.CHASE_SPACING,
            color=config.PRIMARY_COLOR
        )
        
        self.chase_off = Chase(
            self.strip,
            speed=config.CHASE_SPEED,
            size=config.CHASE_SIZE,
            spacing=config.CHASE_SPACING,
            color=color.BLACK,  # Black for power off
            reverse=True  # Reverse direction for power off
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
    
    def set_status_indicators(self, mode, new_state):
        """Set status indicators based on current mode
        
        Note: Built-in pixel color is now controlled by power state machine
        in _handle_power_state_led_behavior method.
        
        Power state builtin pixel colors:
        - DEEP_SLEEP: Off (black)
        - SLEEPING: Red
        - IDLE: Yellow  
        - ACTIVE: Green
        """
        # Built-in pixel color is handled by power state machine
        pass
    
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
        
        # Update LED displays based on current state
        if new_state.power_animation_active:
            # Handle power animation
            chase_animation = self.chase_off if new_state.has_event(new_state.POWER_OFF_PROGRESS) else self.chase_on
            chase_animation.animate()
        elif new_state.color_animation_active:
            # Handle color animation
            current_animation = self.get_current_animation(new_state)
            current_animation.animate()
        elif new_state.current > new_state.IDLE and new_state.active_color:
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
        
        # Update status indicators
        self.set_status_indicators(new_state.current, new_state)
        
        return new_state
    
    def _handle_power_state_led_behavior(self, new_state, power_state_machine):
        """Handle LED behavior based on power state machine states"""
        if not hasattr(new_state, 'power_state') or new_state.power_state is None:
            return
        
        # Handle power button LED and builtin pixel based on button press state
        if new_state.button_pressed:
            # Turn power button LED white when pressed (overrides power state animation)
            self.set_power_button_led_color((255, 255, 255))
            # Set builtin pixel to white when button is pressed (overrides animation)
            self.set_builtin_pixel_color((255, 255, 255), new_state)
        
        if new_state.power_state == power_state_machine.SLEEPING:
            # SLEEPING: Turn off LEDs, run sleeping animation on builtin pixel and power button LED
            self.strip.fill(0)
            self.strip.show()
            if not new_state.button_pressed:
                self._get_builtin_pixel_animation('sleeping').animate()
                self._get_power_button_led_animation('sleeping').animate()
            
        elif new_state.power_state == power_state_machine.ACTIVATING:
            # ACTIVATING: Run power-on animation
            if not new_state.power_animation_active:
                new_state.power_animation_active = True
                new_state.power_animation_start_time = time.monotonic()
            
            # Run chase animation for power on
            self.chase_on.animate()
            # Run activating animation on builtin pixel and power button LED
            if not new_state.button_pressed:
                self._get_builtin_pixel_animation('activating').animate()
                self._get_power_button_led_animation('activating').animate()
            
        elif new_state.power_state == power_state_machine.ACTIVE:
            # ACTIVE: Normal operational LEDs, run active animation on builtin pixel and power button LED
            if not new_state.button_pressed:
                self._get_builtin_pixel_animation('active').animate()
                self._get_power_button_led_animation('active').animate()
            if not new_state.power_animation_active:
                # Handle normal operational LED behavior
                if new_state.current > new_state.IDLE and new_state.active_color:
                    # Active mode (swing/hit) with color blending
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
                    self.strip.fill(config.IDLE_COLOR)
                    self.strip.show()
            
        elif new_state.power_state == power_state_machine.IDLE:
            # IDLE: Dim/static LEDs, run idle animation on builtin pixel and power button LED
            self.strip.fill(config.IDLE_COLOR)
            self.strip.show()
            if not new_state.button_pressed:
                self._get_builtin_pixel_animation('idle').animate()
                self._get_power_button_led_animation('idle').animate()
            
        elif new_state.power_state == power_state_machine.DEACTIVATING:
            # DEACTIVATING: Run power-off animation
            if not new_state.power_animation_active:
                new_state.power_animation_active = True
                new_state.power_animation_start_time = time.monotonic()
            
            # Run chase animation for power off
            self.chase_off.animate()
            # Run deactivating animation on builtin pixel and power button LED
            if not new_state.button_pressed:
                self._get_builtin_pixel_animation('deactivating').animate()
                self._get_power_button_led_animation('deactivating').animate()
            
        elif new_state.power_state == power_state_machine.DEEP_SLEEP:
            # DEEP_SLEEP: Turn off LEDs, turn off builtin pixel and power button LED
            self.strip.fill(0)
            self.strip.show()
            self.set_builtin_pixel_off(new_state)  # Off for deep sleep
            self.set_power_button_led_off()  # Off for deep sleep
    
    
    
