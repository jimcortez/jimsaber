"""Lightsaber state management module"""

class LightsaberState:
    """Comprehensive state management for lightsaber and all subsystems"""
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
        
        # LED and animation state
        self.active_color = None
        self.current_animation_index = 0
        self.color_animation_active = False
        self.animation_start_time = 0.0
        self.power_animation_active = False
        self.power_animation_start_time = 0.0
        self.saber_effect_active = False
        self.saber_effect = None
        self.saber_effect_start_time = 0.0

        # Sensor state
        self.last_accel_read = 0.0
        self.cached_acceleration = None
        self.switch_pressed = False
        self.activity_button_pressed = False
        self.long_press_triggered = False
        
        # Power and battery state
        self.prop_wing_enabled = False
        self.battery_voltage = 0.0
        self.last_battery_read = 0.0
        
        # Power state machine integration
        self.power_state = None  # Will be set by PowerManager
        self.power_state_name = "UNKNOWN"
        
        # Status indicator state
        self.status_leds = {
            'red': False,
            'green': False, 
            'blue': False
        }
        self.builtin_pixel_color = (0, 0, 0)
        
        # Button states
        self.power_button_pressed = False
        self.activity_button_pressed = False
    
    def copy(self, clear_events=True):
        """Create a deep copy of the current state"""
        new_state = LightsaberState()
        new_state.swing_hit_state = self.swing_hit_state
        new_state.previous = self.previous
        new_state.trigger_time = self.trigger_time
        new_state.last_state_log_time = self.last_state_log_time
        if clear_events:
            new_state.events = []
        else:
            new_state.events = self.events.copy()
        new_state.current_event = self.current_event
        new_state.active_color = self.active_color
        new_state.current_animation_index = self.current_animation_index
        new_state.color_animation_active = self.color_animation_active
        new_state.animation_start_time = self.animation_start_time
        new_state.power_animation_active = self.power_animation_active
        new_state.power_animation_start_time = self.power_animation_start_time
        new_state.saber_effect_active = self.saber_effect_active
        new_state.saber_effect = self.saber_effect
        new_state.saber_effect_start_time = self.saber_effect_start_time
        new_state.last_accel_read = self.last_accel_read
        new_state.cached_acceleration = self.cached_acceleration
        new_state.switch_pressed = self.switch_pressed
        new_state.activity_button_pressed = self.activity_button_pressed
        new_state.long_press_triggered = self.long_press_triggered
        new_state.prop_wing_enabled = self.prop_wing_enabled
        new_state.battery_voltage = self.battery_voltage
        new_state.last_battery_read = self.last_battery_read
        new_state.power_state = self.power_state
        new_state.power_state_name = self.power_state_name
        new_state.status_leds = self.status_leds.copy()
        new_state.builtin_pixel_color = self.builtin_pixel_color
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
