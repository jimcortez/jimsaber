"""Base state machine class for the lightsaber"""

import time

class StateLock:
    """State lock to prevent state transitions when certain conditions are not met"""
    
    def __init__(self, name, blocked=True, timeout=None, valid_states=None):
        """
        Initialize a state lock
        
        Args:
            name (str): Name of the lock for identification
            blocked (bool): Whether the lock is currently blocking transitions
            timeout (float): Optional timeout in seconds after which lock expires
            valid_states (list): List of states this lock is valid for
        """
        self.name = name
        self.blocked = blocked
        self.timeout = timeout
        self.valid_states = valid_states or []
        self.created_time = time.monotonic()
    
    def is_expired(self):
        """Check if the lock has expired based on timeout"""
        if self.timeout is None:
            return False
        return time.monotonic() - self.created_time > self.timeout
    
    def is_valid_for_state(self, state):
        """Check if this lock is valid for the given state"""
        return not self.valid_states or state in self.valid_states
    
    def unlock(self):
        """Unlock the state lock"""
        print(f"Unlocking state lock '{self.name}'")
        self.blocked = False
    
    def lock(self):
        """Lock the state lock"""
        self.blocked = True

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
        
        # State lock system
        self.state_locks = []
        self.pending_transition = None
    
    def transition_to(self, new_state):
        """
        Transition to a new state
        @param new_state: The new state to transition to
        @return: True if transition was successful, False otherwise
        """
        if not self.can_transition_to(new_state):
            print(f"Invalid transition from {self.current_state} to {new_state}")
            return False
        
        # Check if any state locks are blocking the transition
        if self._are_locks_blocking_transition():
            self.pending_transition = new_state
            return False
        
        # Execute the actual transition
        return self._execute_transition(new_state)
    
    def _execute_transition(self, new_state):
        """Execute the actual state transition"""
        # Execute exit callback for current state
        if self.current_state is not None and self.current_state in self.state_exit_callbacks:
            self.state_exit_callbacks[self.current_state]()
        
        # Update state
        self.previous_state = self.current_state
        self.current_state = new_state
        self.state_start_time = time.monotonic()
        
        # Clear pending transition
        self.pending_transition = None
        
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
    
    def add_state_lock(self, state_lock):
        """
        Add a state lock to prevent transitions
        
        Args:
            state_lock (StateLock): The state lock to add
            
        Returns:
            bool: True if lock was added successfully, False otherwise
        """
        # Check if current state is valid for this lock
        if not state_lock.is_valid_for_state(self.current_state):
            print(f"State lock '{state_lock.name}' is not valid for current state {self.current_state}")
            return False
        
        # Add the lock
        self.state_locks.append(state_lock)
        print(f"Added state lock '{state_lock.name}' (blocked={state_lock.blocked})")
        return True
    
    def remove_state_lock(self, lock_name):
        """
        Remove a state lock by name
        
        Args:
            lock_name (str): Name of the lock to remove
            
        Returns:
            bool: True if lock was found and removed, False otherwise
        """
        for i, lock in enumerate(self.state_locks):
            if lock.name == lock_name:
                del self.state_locks[i]
                print(f"Removed state lock '{lock_name}'")
                return True
        print(f"State lock '{lock_name}' not found")
        return False
    
    def _are_locks_blocking_transition(self):
        """Check if any state locks are currently blocking transitions"""
        # Clean up expired locks
        self._cleanup_expired_locks()
        
        # Check if any locks are blocking
        for lock in self.state_locks:
            if lock.blocked:
                return True
        return False
    
    def _cleanup_expired_locks(self):
        """Remove expired state locks"""
        expired_locks = [lock for lock in self.state_locks if lock.is_expired()]
        for lock in expired_locks:
            print(f"State lock '{lock.name}' has expired, removing")
            self.state_locks.remove(lock)
    
    def check_pending_transition(self):
        """
        Check if there's a pending transition that can now be executed
        This should be called from process_tick methods
        """
        if self.pending_transition is not None:
            if not self._are_locks_blocking_transition():
                print(f"Executing pending transition to {self.pending_transition}")
                return self._execute_transition(self.pending_transition)
        return False
