"""Saber LED animation management module for the lightsaber strip"""

import time
import neopixel
import board
import config
from lightsaber_state import LightsaberState
from adafruit_led_animation.group import AnimationGroup
from led_utils import create_animation_from_config, mix_colors, save_animation_index_to_nvm
import microcontroller

class SaberLEDManager:
    """Manages saber LED strip animations and effects"""
    
    def __init__(self):
        """
        Initialize the saber LED manager
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
        
        # Initialize animations
        self._setup_animations()
        
        # Animation group tracking
        self.active_animations = []
        self.animation_group = None
        
        # Current animation state
        self.current_animation = None
        self.animation_active = False
        self.animation_start_time = 0.0
        
        # Power animation state
        self.power_animation_active = False
        self.power_animation_start_time = 0.0
    
    
    def _setup_animations(self):
        """Initialize LED animations from STRIP_ANIMATIONS config"""
        # Create animation list from config
        self.animations = []
        for animation_config in config.STRIP_ANIMATIONS:
            animation = create_animation_from_config(animation_config, self.strip)
            self.animations.append(animation)
        
        # Create Chase animations for power on/off using SABER_STATE_ANIMATIONS config
        self.chase_on = create_animation_from_config(
            config.SABER_STATE_ANIMATIONS['activating'], 
            self.strip
        )
        
        self.chase_off = create_animation_from_config(
            config.SABER_STATE_ANIMATIONS['deactivating'], 
            self.strip
        )
    
    
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
        save_animation_index_to_nvm(new_state.current_animation_index)
    
    def load_animation_index(self, new_state):
        """Load animation index from NVM"""
        new_state.current_animation_index = self._load_animation_index_from_nvm()
    
    def _load_animation_index_from_nvm(self):
        """Load animation index from NVM"""
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
            print(f"Updated active saber animations: {len(self.active_animations)} animations")
    
    def _get_current_active_animations(self, new_state):
        """Determine which saber animations should be active based on current state"""
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
        
        return active_animations
    
    def process_tick(self, old_state, new_state, power_state_machine=None):
        """Process one tick of saber LED management based on state transitions"""
        
        # Handle power state machine integration
        if power_state_machine:
            self.handle_power_state_behavior(new_state, power_state_machine)
        
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
        current_active_animations = self._get_current_active_animations(new_state)
        self._update_active_animations(current_active_animations)
        
        # Handle non-animation LED displays (swing/hit effects, idle state)
        if not new_state.power_animation_active and not new_state.color_animation_active:
            if new_state.current > new_state.IDLE and new_state.active_color:
                # Handle active mode (swing/hit) with color blending
                if new_state.current_sound:  # If sound is playing
                    blend = time.monotonic() - new_state.trigger_time
                    if new_state.current == new_state.SWING:
                        blend = abs(0.5 - blend) * 2.0  # ramp up, down
                    self.strip.fill(mix_colors(new_state.active_color, config.IDLE_COLOR, blend))
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
    
    def handle_power_state_behavior(self, new_state, power_state_machine):
        """Handle saber LED behavior based on power state machine states"""
        if not hasattr(new_state, 'power_state') or new_state.power_state is None:
            return
        
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
            # DEEP_SLEEP: Turn off LEDs
            self.strip.fill(0)
            self.strip.show()
