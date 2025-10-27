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
        'power_button_pressed'
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
