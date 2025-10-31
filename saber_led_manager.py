"""Saber LED animation management module for the lightsaber strip"""

import time
import neopixel
import config
from led_utils import create_animation_from_config, save_animation_index_to_nvm
from state_machines.state_machine_base import StateLock

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
        
        # Current animation state
        self.current_animation = None
        self.animation_active = False
        self.animation_start_time = 0.0
        
        # Power animation state
        self.power_animation_active = False
        self.power_animation_start_time = 0.0
        
        # Saber effect state (hit/swing effects)
        self.saber_effect_active = False
        self.saber_effect = None
        self.saber_effect_start_time = 0.0
        
        # Current animation index
        self.current_animation_index = 0

        self.activation_lock = None
        self.deactivation_lock = None
    
    def get_animation_index(self):
        """Get the current animation index"""
        return self.current_animation_index
    
    def set_animation_index(self, index):
        """Set the current animation index"""
        if 0 <= index < len(self.animations):
            self.current_animation_index = index
        else:
            print(f"Invalid animation index {index}, keeping current value {self.current_animation_index}")
    
    
    def _setup_animations(self):
        """Initialize LED animations from STRIP_ANIMATIONS config"""
        # Create animation list from config
        self.animations = []
        for animation_config in config.STRIP_ANIMATIONS:
            animation = create_animation_from_config(animation_config, self.strip)
            self.animations.append(animation)
        
        # Create Chase animations for power on/off using SABER_STATE_ANIMATIONS config
        self.activate_state_animation = create_animation_from_config(
            config.SABER_STATE_ANIMATIONS['activating'], 
            self.strip
        )
        
        self.deactivate_state_animation = create_animation_from_config(
            config.SABER_STATE_ANIMATIONS['deactivating'], 
            self.strip
        )

        self.hit_effect_animation = create_animation_from_config(
            config.SABER_STATE_ANIMATIONS['hit'], 
            self.strip
        )

        if config.SABER_STATE_ANIMATIONS.get('swing', False):
            self.swing_effect_animation = create_animation_from_config(
                config.SABER_STATE_ANIMATIONS['swing'], 
                self.strip
            )
        else:
            self.swing_effect_animation = None
    
    
    def get_current_animation(self):
        """Get the current animation from the animations list"""
        return self.animations[self.current_animation_index]
    
    def cycle_animation(self):
        """Cycle to the next animation in the list"""
        self.current_animation_index = (self.current_animation_index + 1) % len(self.animations)
        current_animation = self.get_current_animation()
        
        # Update idle color based on current animation config
        if self.current_animation_index < len(config.STRIP_ANIMATIONS):
            current_config = config.STRIP_ANIMATIONS[self.current_animation_index]
            if current_config["animation_type"] == "solid":
                new_color = current_config["params"]["color"]
                print(f"Animation changed to solid color: {new_color}")
            else:
                # Non-solid animation - keep default idle color
                animation_name = current_config["animation_type"]
                print(f"Animation changed to {animation_name}")
        
        # Save the new animation index to NVM
        save_animation_index_to_nvm(self.current_animation_index)
        
        return current_animation
    
    def _handle_hit_state(self, new_state):
        """Handle led behavior for HIT state"""
        if not self.saber_effect_active:
            self.current_animation = self.hit_effect_animation
            self.saber_effect = 'hit'
            self.saber_effect_active = True
            self.saber_effect_start_time = time.monotonic()
            print("Started hit led effect")
        elif self.saber_effect == 'hit':
            elapsed = time.monotonic() - self.saber_effect_start_time
            if elapsed >= config.HIT_DURATION:
                self.saber_effect = None
                self.saber_effect_active = False
                print("Hit led effect completed (duration-based)")
                self.current_animation = None

    def _handle_swing_state(self, new_state):
        """Handle led behavior for SWING state"""
        if self.swing_effect_animation:
            if not self.saber_effect_active:
                self.current_animation = self.swing_effect_animation
                self.saber_effect = 'swing'
                self.saber_effect_active = True
                self.saber_effect_start_time = time.monotonic()
                print("Started swing led effect")
        elif self.saber_effect == 'swing':
            elapsed = time.monotonic() - self.saber_effect_start_time
            if elapsed >= config.SWING_DURATION:
                self.saber_effect = None
                self.saber_effect_active = False
                print("Swing led effect completed (duration-based)")
                self.current_animation = None

    def _handle_activation_state(self, new_state, power_state_machine):
        """Handle saber LED behavior for ACTIVATING state with state lock management"""
        # Get the current activation duration from the state
        activation_duration = new_state.get_current_sound_duration('activating')
        if activation_duration <= 0:
            # Fallback to first activation sound duration if state doesn't have it yet
            activation_effects = config.SOUND_EFFECTS.get('activating', [])
            if activation_effects:
                activation_duration = activation_effects[0][1]
            else:
                activation_duration = 2.0  # Default fallback
        
        # Create and add state lock for activation sound if not already created
        if self.activation_lock is None:
            self.activation_lock = StateLock(
                name="activation_saber_animation",
                blocked=True,
                timeout=activation_duration + 2.0,  # Add buffer time
                valid_states=[power_state_machine.ACTIVATING]
            )
            power_state_machine.add_state_lock(self.activation_lock)
            print("Created activation saber animation state lock")

        if self.activation_lock.blocked:
            self.current_animation = self.activate_state_animation

            if not self.power_animation_active:
                # Update animation duration with current sound duration
                self.activate_state_animation.update_duration(activation_duration)
                
                #reset the animation and set the color to the current animation color
                self.activate_state_animation.reset()
                self.strip.fill((0,0,0))
                cur_color = self.get_current_animation().color
                if cur_color is not None and cur_color != (0,0,0):
                    self.activate_state_animation.color = cur_color

                self.power_animation_active = True
                self.power_animation_start_time = time.monotonic()
                print(f"Started power-on LED animation (duration: {activation_duration:.2f}s)")
            # Check if power-on animation is complete based on current duration
            elif self.power_animation_active:
                elapsed = time.monotonic() - self.power_animation_start_time
                if elapsed >= activation_duration:
                    self.power_animation_active = False
                    self.current_animation = None
                    self.activation_lock.unlock()
    
    def _handle_deactivation_state(self, new_state, power_state_machine):
        """Handle saber LED behavior for DEACTIVATING state with state lock management"""
        # Get the current deactivation duration from the state
        deactivation_duration = new_state.get_current_sound_duration('deactivating')
        if deactivation_duration <= 0:
            # Fallback to first deactivation sound duration if state doesn't have it yet
            deactivation_effects = config.SOUND_EFFECTS.get('deactivating', [])
            if deactivation_effects:
                deactivation_duration = deactivation_effects[0][1]
            else:
                deactivation_duration = 2.0  # Default fallback
        
        # Create and add state lock for activation sound if not already created
        if self.deactivation_lock is None:
            self.deactivation_lock = StateLock(
                name="deactivation_saber_animation",
                blocked=True,
                timeout=deactivation_duration + 2.0,  # Add buffer time
                valid_states=[power_state_machine.DEACTIVATING]
            )
            power_state_machine.add_state_lock(self.deactivation_lock)
            print("Created deactivation saber animation state lock")

        if self.deactivation_lock.blocked:
            self.current_animation = self.deactivate_state_animation

            if not self.power_animation_active:
                # Update animation duration with current sound duration
                if hasattr(self.deactivate_state_animation, 'update_duration'):
                    self.deactivate_state_animation.update_duration(deactivation_duration)
                
                self.deactivate_state_animation.reset()
                self.power_animation_active = True
                self.power_animation_start_time = time.monotonic()
                print(f"Started power-off LED animation (duration: {deactivation_duration:.2f}s)")
            # Check if power-off animation is complete based on current duration
            elif self.power_animation_active:
                elapsed = time.monotonic() - self.power_animation_start_time
                if elapsed >= deactivation_duration:
                    self.power_animation_active = False
                    self.current_animation = None
                    self.deactivation_lock.unlock()

    def process_tick(self, old_state, new_state, power_state_machine=None):
        """Process one tick of saber LED management based on state transitions"""
        
        # Handle power state machine integration
        if new_state.power_state == power_state_machine.ACTIVATING:
            self._handle_activation_state(new_state, power_state_machine)
        elif (old_state.power_state == power_state_machine.ACTIVATING and 
            new_state.power_state != power_state_machine.ACTIVATING and 
            self.activation_lock):
            # Clean up activation lock if transitioning away from ACTIVATING
            print("Transitioning away from ACTIVATING - cleaning up activation lock")
            self.activation_lock.unlock()
            power_state_machine.remove_state_lock("activation_saber_animation")
            self.activation_lock = None

        if new_state.power_state == power_state_machine.DEACTIVATING:
            self._handle_deactivation_state(new_state, power_state_machine)
        elif (old_state.power_state == power_state_machine.DEACTIVATING and 
            new_state.power_state != power_state_machine.DEACTIVATING and 
            self.deactivation_lock):
            # Clean up deactivation lock if transitioning away from DEACTIVATING
            print("Transitioning away from DEACTIVATING - cleaning up deactivation lock")
            self.deactivation_lock.unlock()
            power_state_machine.remove_state_lock("deactivation_saber_animation")
            self.deactivation_lock = None

        if new_state.power_state == power_state_machine.ACTIVE:
            # Handle motion events
            if new_state.has_event(new_state.HIT_START) or self.saber_effect == 'hit':
                self._handle_hit_state(new_state)
            elif new_state.has_event(new_state.SWING_START) or self.saber_effect == 'swing':
                self._handle_swing_state(new_state)

            if not self.current_animation:
                self.current_animation = self.get_current_animation()
        
            # Handle button events
            if new_state.has_event(new_state.ACTIVITY_BUTTON_SHORT_PRESS):
                print("Activity button pressed - cycling animation")
                self.current_animation = self.cycle_animation()

            if not self.current_animation:
                self.current_animation = self.get_current_animation()

        if self.current_animation:
            # Provide the latest lightsaber state to animations that support it
            if hasattr(self.current_animation, 'lightsaber_state'):
                self.current_animation.lightsaber_state = new_state
            self.current_animation.animate()
        
        return new_state