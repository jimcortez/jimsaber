"""Logging management module for the lightsaber"""

import time
import math
import config
from lightsaber_state import LightsaberState

class LoggingManager:
    """Manages all logging functionality including state transitions and periodic reporting"""
    
    def __init__(self):
        """
        Initialize the logging manager
        """
        
        # Initialize logging state
        self.last_state_log_time = time.monotonic()
        self.last_power_state = 0
        self.last_mode = None
        
        # State transition tracking
        self.state_transitions = []
        self.max_transition_history = 10  # Keep last 10 transitions
    
    def log_state_transition(self, old_state, new_state, power_state_machine=None):
        """Log state transitions for debugging and monitoring"""
        try:
            # Check for power state transitions
            if (power_state_machine and 
                hasattr(new_state, 'power_state') and 
                new_state.power_state != self.last_power_state):
                
                old_power_name = power_state_machine.get_state_name(self.last_power_state) if self.last_power_state is not None else "UNKNOWN"
                new_power_name = power_state_machine.get_state_name(new_state.power_state)
                
                print(f"Power state transition: {old_power_name} -> {new_power_name}")
                
                # Record transition
                self.state_transitions.append({
                    'timestamp': time.monotonic(),
                    'type': 'power_state',
                    'from': old_power_name,
                    'to': new_power_name
                })
                
                self.last_power_state = new_state.power_state
            
            # Check for mode transitions
            if new_state.swing_hit_state != self.last_mode:
                mode_names = ["OFF", "IDLE", "SWING", "HIT"]
                old_mode_name = mode_names[self.last_mode] if self.last_mode is not None and self.last_mode < len(mode_names) else "UNKNOWN"
                new_mode_name = mode_names[new_state.swing_hit_state] if new_state.swing_hit_state < len(mode_names) else "UNKNOWN"
                
                print(f"Mode transition: {old_mode_name} -> {new_mode_name}")
                
                # Record transition
                self.state_transitions.append({
                    'timestamp': time.monotonic(),
                    'type': 'mode',
                    'from': old_mode_name,
                    'to': new_mode_name
                })
                
                self.last_mode = new_state.swing_hit_state
            
            # Keep only recent transitions
            if len(self.state_transitions) > self.max_transition_history:
                self.state_transitions = self.state_transitions[-self.max_transition_history:]
                
        except Exception as e:
            print(f"Failed to log state transition: {e}")
    
    def log_periodic_state(self, old_state, new_state, power_state_machine, sound_manager=None, saber_led_manager=None):
        """Log comprehensive state information periodically"""
        try:
            # Get current mode name
            mode_names = ["OFF", "IDLE", "SWING", "HIT"]
            current_mode = mode_names[new_state.swing_hit_state] if new_state.swing_hit_state < len(mode_names) else "UNKNOWN"
            
            # Get accelerometer values
            acceleration = new_state.cached_acceleration
            if acceleration is not None:
                x, y, z = acceleration
                accel_magnitude = math.sqrt(x*x + y*y + z*z)
            else:
                x, y, z, accel_magnitude = 0, 0, 0, 0
            
            # Get battery voltage
            battery_voltage = getattr(new_state, 'battery_voltage', 0.0)

            # Get audio state from sound manager
            if sound_manager:
                effect_sound = sound_manager.effect_sound
                effect_playing = effect_sound is not None and effect_sound[1] if effect_sound else False
                effect_name = effect_sound[0] if effect_sound else 'None'
                idle_sound_open = sound_manager.idle_sound is not None
                audio_playing = sound_manager.is_playing()
            else:
                effect_playing = False
                effect_name = 'None'
                idle_sound_open = False
                audio_playing = False
            
            # Print comprehensive state information
            # Get animation index from saber LED manager
            animation_index = saber_led_manager.get_animation_index() if saber_led_manager else "N/A"
            
            print("=" * 60)
            print("LIGHTSABER PERIODIC STATE REPORT")
            print("=" * 60)
            print(f"Current Mode: {current_mode}")
            print(f"Power State: {power_state_machine.get_state_name(new_state.power_state)}")
            print(f"Animation Index: {animation_index}")
            print(f"Battery Voltage: {battery_voltage:.2f}V")
            print(f"Accelerometer - X: {x:.2f}, Y: {y:.2f}, Z: {z:.2f}")
            print(f"Accelerometer Magnitude: {accel_magnitude:.2f}")
            print(f"Effect Playing: {effect_playing}")
            if effect_playing:
                print(f"Effect Sound: {effect_name}")
            print(f"Audio Hardware Playing: {audio_playing}")
            print(f"Idle Sound File Open: {idle_sound_open}")
            
            # Show recent state transitions
            if self.state_transitions:
                print("\nRecent State Transitions:")
                for transition in self.state_transitions[-5:]:  # Show last 5 transitions
                    elapsed = time.monotonic() - transition['timestamp']
                    print(f"  {elapsed:.1f}s ago: {transition['type']} {transition['from']} -> {transition['to']}")
            
            print("=" * 60)
            
        except Exception as e:
            print(f"Failed to log periodic state: {e}")
    
    def check_periodic_logging(self, old_state, new_state, power_state_machine, sound_manager=None, saber_led_manager=None):
        """Check if it's time to log periodic state information"""
        now = time.monotonic()
        if now - self.last_state_log_time >= config.STATE_LOG_INTERVAL:
            self.log_periodic_state(old_state, new_state, power_state_machine, sound_manager, saber_led_manager)
            self.last_state_log_time = now
    
    def log_event(self, event_name, details=None):
        """Log a specific event with optional details"""
        try:
            timestamp = time.monotonic()
            if details:
                print(f"[{timestamp:.2f}] Event: {event_name} - {details}")
            else:
                print(f"[{timestamp:.2f}] Event: {event_name}")
        except Exception as e:
            print(f"Failed to log event: {e}")
    
    def log_animation_event(self, animation_type, complete):
        """Log animation completion events"""
        try:
            timestamp = time.monotonic()
            print(f"[{timestamp:.2f}] Animation: {animation_type} complete: {complete}")
        except Exception as e:
            print(f"Failed to log animation event: {e}")
    
    def log_animation_reset(self):
        """Log animation flags reset"""
        try:
            timestamp = time.monotonic()
            print(f"[{timestamp:.2f}] Animation: Flags reset")
        except Exception as e:
            print(f"Failed to log animation reset: {e}")
    
    def log_error(self, error_message, exception=None):
        """Log an error with optional exception details"""
        try:
            timestamp = time.monotonic()
            if exception:
                print(f"[{timestamp:.2f}] ERROR: {error_message} - {exception}")
            else:
                print(f"[{timestamp:.2f}] ERROR: {error_message}")
        except Exception as e:
            print(f"Failed to log error: {e}")
    
    def process_tick(self, old_state, new_state, power_state_machine=None, sound_manager=None, saber_led_manager=None):
        """Process one tick of logging management - called at end of main loop"""
        # Log state transitions
        self.log_state_transition(old_state, new_state, power_state_machine)
        
        # Check for periodic logging
        self.check_periodic_logging(old_state, new_state, power_state_machine, sound_manager, saber_led_manager)
        
        return new_state
