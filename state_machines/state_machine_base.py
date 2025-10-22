"""Base state machine class for the lightsaber"""

import time

class StateMachineBase:
    """Base class for all state machines in the lightsaber system"""
    
    def __init__(self):
        """Initialize the base state machine"""
        self.current_state = None
        self.previous_state = None
        self.state_start_time = 0.0
        self.transition_callbacks = {}
        self.state_entry_callbacks = {}
        self.state_exit_callbacks = {}
    
    def transition_to(self, new_state):
        """
        Transition to a new state
        @param new_state: The new state to transition to
        @return: True if transition was successful, False otherwise
        """
        if not self.can_transition_to(new_state):
            print(f"Invalid transition from {self.current_state} to {new_state}")
            return False
        
        # Execute exit callback for current state
        if self.current_state is not None and self.current_state in self.state_exit_callbacks:
            self.state_exit_callbacks[self.current_state]()
        
        # Update state
        self.previous_state = self.current_state
        self.current_state = new_state
        self.state_start_time = time.monotonic()
        
        # Execute entry callback for new state
        if new_state in self.state_entry_callbacks:
            self.state_entry_callbacks[new_state]()
        
        # Execute transition callback
        transition_key = (self.previous_state, new_state)
        if transition_key in self.transition_callbacks:
            self.transition_callbacks[transition_key]()
        
        print(f"State transition: {self.previous_state} -> {new_state}")
        return True
    
    def can_transition_to(self, target_state):
        """
        Check if transition to target state is valid
        @param target_state: The state to transition to
        @return: True if transition is valid, False otherwise
        """
        # Override in subclasses to implement specific transition rules
        return True
    
    def add_state_entry_callback(self, state, callback):
        """Add a callback to be called when entering a state"""
        self.state_entry_callbacks[state] = callback
    
    def get_state_name(self, state):
        """Get the name of a state (override in subclasses)"""
        return str(state)
