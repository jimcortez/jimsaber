"""Power state machine for the lightsaber"""

import time
import alarm
import config
from .state_machine_base import StateMachineBase

class PowerStateMachineState:
    BOOTING = 0
    SLEEPING = 1
    WAKING = 2
    ACTIVATING = 3
    ACTIVE = 4
    IDLE = 5
    DEACTIVATING = 6

    state_names = {
        BOOTING: "BOOTING",
        SLEEPING: "SLEEPING",
        WAKING: "WAKING",
        ACTIVATING: "ACTIVATING", 
        ACTIVE: "ACTIVE",
        IDLE: "IDLE",
        DEACTIVATING: "DEACTIVATING"
    }

    def get_state_name(state):
        """Get the name of a power state"""
        return PowerStateMachineState.state_names.get(state, f"UNKNOWN({state})")

class PowerStateMachine(StateMachineBase):
    """Power state machine managing lightsaber power states"""
    
    # Power states
    BOOTING = 0
    SLEEPING = 1
    WAKING = 2
    ACTIVATING = 3
    ACTIVE = 4
    IDLE = 5
    DEACTIVATING = 6
    
    def __init__(self, logging_manager=None):
        """Initialize the power state machine"""
        super().__init__()
        self.logging_manager = logging_manager
        self._last_logged_state = self.BOOTING
        
        # Initialize to BOOTING state
        self.current_state = self.BOOTING
        self.state_start_time = time.monotonic()
        
        # Animation completion tracking
        self.led_animation_complete = False
        self.sound_animation_complete = False
        
        # Inactivity tracking
        self.inactivity_timer = 0.0
        
        
        # WAKING state tracking
        self.waking_start_time = 0.0
        self.waking_duration = config.WAKING_DURATION  # Delay for WAKING state to stabilize
        self._waking_initialized = False
        
        # State names for debugging
        self.state_names = {
            self.BOOTING: "BOOTING",
            self.SLEEPING: "SLEEPING",
            self.WAKING: "WAKING",
            self.ACTIVATING: "ACTIVATING", 
            self.ACTIVE: "ACTIVE",
            self.IDLE: "IDLE",
            self.DEACTIVATING: "DEACTIVATING"
        }
        
        # Initialize inactivity timer
        self.update_inactivity_timer()
    
    def get_state_name(self, state):
        """Get the name of a power state"""
        return self.state_names.get(state, f"UNKNOWN({state})")
    
    def can_transition_to(self, target_state):
        """Check if transition to target state is valid based on power state rules"""
        current = self.current_state
        
        # Define valid transitions
        valid_transitions = {
            self.BOOTING: [self.SLEEPING],
            self.SLEEPING: [self.WAKING],
            self.WAKING: [self.ACTIVATING],
            self.ACTIVATING: [self.ACTIVE],
            self.ACTIVE: [self.IDLE, self.DEACTIVATING],
            self.IDLE: [self.ACTIVE, self.DEACTIVATING],
            self.DEACTIVATING: [self.SLEEPING]
        }
        
        return target_state in valid_transitions.get(current, [])
    
    def check_inactivity_timeout(self):
        """Check if inactivity timeout reached for deep sleep transition"""
        if self.current_state == self.SLEEPING:
            if time.monotonic() - self.inactivity_timer > config.DEEP_SLEEP_TIMEOUT:
                return True
        return False
    
    def update_inactivity_timer(self):
        """Update the inactivity timer (call when activity is detected)"""
        self.inactivity_timer = time.monotonic()

    
    def handle_power_button_press(self):
        """Handle power button press based on current state"""
        print(f"handle_power_button_press called with current_state: {self.get_state_name(self.current_state)}")
        if self.current_state == self.SLEEPING:
            # Start wake sequence
            print("Starting wake sequence from SLEEPING")
            self.transition_to(self.WAKING)
        elif self.current_state == self.ACTIVE or self.current_state == self.IDLE:
            # Start deactivation sequence
            print("Starting deactivation sequence from ACTIVE/IDLE")
            self.transition_to(self.DEACTIVATING)
        else:
            print(f"No action taken for power button press in state: {self.get_state_name(self.current_state)}")
    
    def handle_motion_detected(self):
        """Handle motion detection based on current state"""
        if self.current_state == self.IDLE:
            # Return to active state
            self.transition_to(self.ACTIVE)
        elif self.current_state == self.ACTIVE:
            # Update state start time to reset idle timeout
            self.state_start_time = time.monotonic()
        elif self.current_state == self.SLEEPING:
            # Update inactivity timer
            self.update_inactivity_timer()
    
    def handle_no_motion_timeout(self):
        """Handle no motion timeout based on current state"""
        if self.current_state == self.ACTIVE:
            # Transition to idle state
            self.transition_to(self.IDLE)
    
    def handle_idle_auto_shutdown_timeout(self):
        """Handle auto-shutdown timeout when device has been IDLE for too long"""
        if self.current_state == self.IDLE:
            # Transition to deactivating state for auto-shutdown
            self.transition_to(self.DEACTIVATING)

    def _handle_auto_transition(self):
        # Update power state machine
        if self.current_state == self.BOOTING:
            print("Transitioning from BOOTING to SLEEPING")
            self.transition_to(self.SLEEPING)
        
        # Handle WAKING state auto-transition to ACTIVATING
        elif self.current_state == self.WAKING:
            self.transition_to(self.ACTIVATING)

        #auto-transition to ACTIVE from ACTIVATING, locks will block if needed
        elif self.current_state == self.ACTIVATING :
            self.transition_to(self.ACTIVE)
        
        #auto-transition to SLEEPING from DEACTIVATING, locks will block if needed
        elif self.current_state == self.DEACTIVATING:
            self.transition_to(self.SLEEPING)
    
    def process_tick(self, old_state, new_state):
        """Process one tick of power state machine and handle power-related events"""
        # Check for pending transitions first
        self.check_pending_transition()
        
        # Handle power button events
        if new_state.has_event(new_state.POWER_BUTTON_SHORT_PRESS):
            self.handle_power_button_press()
        
        # Handle motion events
        if new_state.has_event(new_state.SWING_START) or new_state.has_event(new_state.HIT_START):
            self.handle_motion_detected()
        
        # Handle no motion timeout (transition from ACTIVE to IDLE)
        if (self.current_state == self.ACTIVE and 
            time.monotonic() - self.state_start_time > config.IDLE_TIMEOUT):
            self.handle_no_motion_timeout()
        
        # Handle idle auto-shutdown timeout (transition from IDLE to DEACTIVATING)
        if (self.current_state == self.IDLE and 
            time.monotonic() - self.state_start_time > config.AUTO_SHUTDOWN_TIMEOUT):
            self.handle_idle_auto_shutdown_timeout()
        
        # Log state transition if it changed
        if self._last_logged_state == self.current_state:
            self._handle_auto_transition()
        else:
            print(f"Power state transition: {self.get_state_name(self._last_logged_state)} -> {self.get_state_name(self.current_state)}")
            
            # Handle swing_hit_state updates based on power state transitions
            # Set to IDLE when entering ACTIVE from ACTIVATING
            if (self._last_logged_state == self.ACTIVATING and 
                self.current_state == self.ACTIVE):
                new_state.swing_hit_state = new_state.IDLE
                print("Set swing_hit_state to IDLE (entered ACTIVE)")
            
            # Set to OFF when entering DEACTIVATING
            elif self.current_state == self.DEACTIVATING:
                new_state.swing_hit_state = new_state.OFF
                print("Set swing_hit_state to OFF (entered DEACTIVATING)")

            
         # Update power state in LightsaberState
        new_state.set_power_state(
            self.current_state,
            self.get_state_name(self.current_state)
        )
        
        self._last_logged_state = self.current_state
        
        return new_state
    
