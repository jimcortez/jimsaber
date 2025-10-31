"""Lightsaber state management module"""

class LightsaberState:
    """Comprehensive state management for lightsaber and all subsystems"""
    
    # Define slots for memory efficiency and faster attribute access
    __slots__ = (
        'swing_hit_state', 'previous', 'trigger_time', 'last_state_log_time',
        'events', 'current_event',
        'last_accel_read', 'cached_acceleration',
        'activity_button_pressed', 'long_press_triggered', 'battery_voltage', 'last_battery_read',
        'power_state', 'power_state_name',
        'power_button_pressed',
        'sound_effect_indices', 'sound_effect_durations'
    )
    
    # Main modes
    OFF = 0
    IDLE = 1
    SWING = 2
    HIT = 3
    
    # Events
    NO_EVENT = 0
    POWER_ON_START = 1
    POWER_ON_PROGRESS = 2
    POWER_ON_STOP = 3
    POWER_OFF_START = 4
    POWER_OFF_PROGRESS = 5
    POWER_OFF_STOP = 6
    HIT_START = 7
    HIT_IN_PROGRESS = 8
    HIT_STOP = 9
    SWING_START = 10
    SWING_IN_PROGRESS = 11
    SWING_STOP = 12
    IDLE_START = 13
    IDLE_IN_PROGRESS = 14
    ANIMATION_CYCLE = 15
    BUTTON_LONG_PRESS = 16
    BUTTON_SHORT_PRESS = 17
    POWER_BUTTON_SHORT_PRESS = 18
    POWER_BUTTON_LONG_PRESS = 19
    ACTIVITY_BUTTON_SHORT_PRESS = 20
    ACTIVITY_BUTTON_LONG_PRESS = 21
    
    def __init__(self):
        # Main lightsaber state
        self.swing_hit_state = self.OFF
        self.previous = self.OFF
        self.trigger_time = 0.0
        self.last_state_log_time = 0.0
        
        # Event system
        self.events = []  # List of events that occurred this tick
        self.current_event = self.NO_EVENT
        
        # Sensor state
        self.last_accel_read = 0.0
        self.cached_acceleration = None
        self.long_press_triggered = False
        
        # Power and battery state
        self.battery_voltage = 0.0
        self.last_battery_read = 0.0
        
        # Power state machine integration
        self.power_state = None  # Will be set by PowerManager
        self.power_state_name = "UNKNOWN"
        
        # Button states
        self.power_button_pressed = False
        self.activity_button_pressed = False
        
        # Sound effect playlist tracking
        self.sound_effect_indices = {}  # Dictionary to track indices for each sound effect type
        self.sound_effect_durations = {}  # Dictionary to track durations for each sound effect type
    
    def copy(self, clear_events=True):
        """Create a deep copy of the current state - optimized for performance"""
        new_state = LightsaberState()
        
        # Copy all attributes efficiently
        new_state.swing_hit_state = self.swing_hit_state
        new_state.previous = self.previous
        new_state.trigger_time = self.trigger_time
        new_state.last_state_log_time = self.last_state_log_time
        
        # Optimize event handling - reuse list if not clearing
        if clear_events:
            new_state.clear_events() # Empty list, no copying needed
        else:
            new_state.events = self.events[:]  # Shallow copy is sufficient for immutable events
            new_state.current_event = self.current_event
        
        # Copy sensor state
        new_state.last_accel_read = self.last_accel_read
        new_state.cached_acceleration = self.cached_acceleration
        new_state.activity_button_pressed = self.activity_button_pressed
        new_state.long_press_triggered = self.long_press_triggered
        
        # Copy power and battery state
        new_state.battery_voltage = self.battery_voltage
        new_state.last_battery_read = self.last_battery_read
        new_state.power_state = self.power_state
        new_state.power_state_name = self.power_state_name
        
        # Copy button states
        new_state.power_button_pressed = self.power_button_pressed
        new_state.activity_button_pressed = self.activity_button_pressed
        
        # Copy sound effect playlist tracking
        new_state.sound_effect_indices = self.sound_effect_indices.copy()
        new_state.sound_effect_durations = self.sound_effect_durations.copy()
        
        return new_state
    
    def add_event(self, event):
        """Add an event to the current tick"""
        self.events.append(event)
        self.current_event = event
    
    def clear_events(self):
        """Clear all events for the next tick"""
        self.events = []
        self.current_event = self.NO_EVENT
    
    def has_event(self, event):
        """Check if a specific event occurred this tick"""
        return event in self.events
    
    def set_power_state(self, power_state, power_state_name):
        """Set the current power state from the power state machine"""
        self.power_state = power_state
        self.power_state_name = power_state_name
    
    def reset_sound_playlist(self, sound_type=None):
        """Reset the sound effect playlist to the beginning for a specific type"""
        if sound_type is not None:
            self.sound_effect_indices[sound_type] = 0
            # Duration will be set when get_current_sound_effect is called
        else:
            # Reset all sound effect indices and durations
            self.sound_effect_indices.clear()
            self.sound_effect_durations.clear()
    
    def advance_sound_playlist(self, sound_effects_list, sound_type=None):
        """Advance to the next sound effect in the playlist, cycling back to start if needed"""
        if not sound_effects_list:
            return None
        
        # Use sound_type if provided, otherwise try to infer from the list
        if sound_type is None:
            # Try to infer sound type from the first filename
            if sound_effects_list:
                first_filename = sound_effects_list[0][0]
                if 'hit' in first_filename:
                    sound_type = 'hit'
                elif 'swing' in first_filename:
                    sound_type = 'swing'
                elif 'on' in first_filename:
                    sound_type = 'activating'
                elif 'off' in first_filename:
                    sound_type = 'deactivating'
                elif 'idle' in first_filename:
                    sound_type = 'idle'
                else:
                    sound_type = 'default'
        
        # Initialize index if not exists
        if sound_type not in self.sound_effect_indices:
            self.sound_effect_indices[sound_type] = 0
        
        # Advance index
        self.sound_effect_indices[sound_type] = (self.sound_effect_indices[sound_type] + 1) % len(sound_effects_list)
        filename, duration = sound_effects_list[self.sound_effect_indices[sound_type]]
        self.sound_effect_durations[sound_type] = duration
        return filename, duration
    
    def get_current_sound_effect(self, sound_effects_list, sound_type=None):
        """Get the current sound effect from the playlist"""
        if not sound_effects_list:
            return None
        
        # Use sound_type if provided, otherwise try to infer from the list
        if sound_type is None:
            # Try to infer sound type from the first filename
            if sound_effects_list:
                first_filename = sound_effects_list[0][0]
                if 'hit' in first_filename:
                    sound_type = 'hit'
                elif 'swing' in first_filename:
                    sound_type = 'swing'
                elif 'on' in first_filename:
                    sound_type = 'activating'
                elif 'off' in first_filename:
                    sound_type = 'deactivating'
                elif 'idle' in first_filename:
                    sound_type = 'idle'
                else:
                    sound_type = 'default'
        
        # Initialize index if not exists
        if sound_type not in self.sound_effect_indices:
            self.sound_effect_indices[sound_type] = 0
        
        # Ensure index is within bounds
        if self.sound_effect_indices[sound_type] >= len(sound_effects_list):
            self.sound_effect_indices[sound_type] = 0
        
        filename, duration = sound_effects_list[self.sound_effect_indices[sound_type]]
        self.sound_effect_durations[sound_type] = duration
        return filename, duration
    
    def get_current_sound_duration(self, sound_type):
        """Get the current duration for a specific sound type"""
        return self.sound_effect_durations.get(sound_type, 0.0)
