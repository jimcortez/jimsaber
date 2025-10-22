"""Power state machine for the lightsaber"""

import time
import alarm
import config
from .state_machine_base import StateMachineBase

class PowerStateMachine(StateMachineBase):
    """Power state machine managing lightsaber power states"""
    
    # Power states
    BOOTING = 0
    SLEEPING = 1
    ACTIVATING = 2
    ACTIVE = 3
    IDLE = 4
    DEACTIVATING = 5
    DEEP_SLEEP = 6
    LIGHT_SLEEP = 7
    
    def __init__(self, logging_manager=None):
        """Initialize the power state machine"""
        super().__init__()
        self.logging_manager = logging_manager
        
        # Initialize to BOOTING state
        self.current_state = self.BOOTING
        self.state_start_time = time.monotonic()
        
        # Animation completion tracking
        self.led_animation_complete = False
        self.sound_animation_complete = False
        
        # Inactivity tracking
        self.inactivity_timer = 0.0
        
        # State names for debugging
        self.state_names = {
            self.BOOTING: "BOOTING",
            self.SLEEPING: "SLEEPING",
            self.ACTIVATING: "ACTIVATING", 
            self.ACTIVE: "ACTIVE",
            self.IDLE: "IDLE",
            self.DEACTIVATING: "DEACTIVATING",
            self.DEEP_SLEEP: "DEEP_SLEEP",
            self.LIGHT_SLEEP: "LIGHT_SLEEP"
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
            self.SLEEPING: [self.ACTIVATING, self.LIGHT_SLEEP],
            self.LIGHT_SLEEP: [self.ACTIVATING, self.DEEP_SLEEP],
            self.ACTIVATING: [self.ACTIVE],
            self.ACTIVE: [self.IDLE, self.DEACTIVATING],
            self.IDLE: [self.ACTIVE, self.DEACTIVATING],
            self.DEACTIVATING: [self.SLEEPING],
            self.DEEP_SLEEP: [self.SLEEPING, self.ACTIVATING]
        }
        
        return target_state in valid_transitions.get(current, [])
    
    def is_activation_complete(self):
        """Check if both LED and sound animations are complete for activation"""
        return (self.led_animation_complete and 
                self.sound_animation_complete)
    
    def is_deactivation_complete(self):
        """Check if both LED and sound animations are complete for deactivation"""
        return (self.led_animation_complete and 
                self.sound_animation_complete)
    
    def set_led_animation_complete(self, complete):
        """Set LED animation completion status"""
        self.led_animation_complete = complete
        if self.logging_manager:
            self.logging_manager.log_animation_event("LED", complete)
    
    def set_sound_animation_complete(self, complete):
        """Set sound animation completion status"""
        self.sound_animation_complete = complete
        if self.logging_manager:
            self.logging_manager.log_animation_event("Sound", complete)
    
    def reset_animation_flags(self):
        """Reset animation completion flags"""
        self.led_animation_complete = False
        self.sound_animation_complete = False
        if self.logging_manager:
            self.logging_manager.log_animation_reset()
    
    def check_inactivity_timeout(self):
        """Check if inactivity timeout reached for deep sleep transition"""
        if self.current_state == self.SLEEPING:
            if time.monotonic() - self.inactivity_timer > config.DEEP_SLEEP_TIMEOUT:
                return True
        return False
    
    def check_light_sleep_timeout(self):
        """Check if light sleep timeout reached for transitioning from SLEEPING to LIGHT_SLEEP"""
        if self.current_state == self.SLEEPING:
            if time.monotonic() - self.inactivity_timer > config.LIGHT_SLEEP_TIMEOUT:
                return True
        return False
    
    def update_inactivity_timer(self):
        """Update the inactivity timer (call when activity is detected)"""
        self.inactivity_timer = time.monotonic()
    
    def enter_light_sleep(self):
        """Enter light sleep mode for LIGHT_SLEEP state"""
        try:
            # Create button alarm for wake-up on button press
            button_alarm = alarm.pin.PinAlarm(pin=config.POWER_PIN, value=False, pull=True)
            
            # Create timer alarm to wake up after DEEP_SLEEP_TIMEOUT for deep sleep transition
            timer_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + config.DEEP_SLEEP_TIMEOUT)
            
            # Sleep until either button is pressed or timeout is reached
            alarm.light_sleep_until_alarms(button_alarm, timer_alarm)
            print("Woke from light sleep")
        except Exception as e:
            print(f"Light sleep error: {e}")
            # If light sleep fails, try without pull-up
            try:
                button_alarm = alarm.pin.PinAlarm(pin=config.POWER_PIN, value=False)
                timer_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + config.DEEP_SLEEP_TIMEOUT)
                alarm.light_sleep_until_alarms(button_alarm, timer_alarm)
                print("Woke from light sleep (retry)")
            except Exception as e2:
                print(f"Light sleep retry error: {e2}")
    
    
    def was_woken_by_timer(self):
        """Check if the system was woken by a timer alarm (indicating deep sleep transition)"""
        try:
            # Check if we have a timer alarm that woke us up
            if alarm.wake_alarm is not None:
                print(f"Wake alarm type: {type(alarm.wake_alarm)}")
                is_timer = isinstance(alarm.wake_alarm, alarm.time.TimeAlarm)
                print(f"Was woken by timer: {is_timer}")
                return is_timer
            else:
                print("No wake alarm detected")
                return False
        except Exception as e:
            print(f"Error checking wake alarm: {e}")
            return False
    
    def enter_deep_sleep(self):
        """Enter deep sleep mode for DEEP_SLEEP state"""
        # Save state to non-volatile memory
        self.save_state_to_nvm()
        
        # Create button alarm for wake-up on D10 (separate from button pin)
        button_alarm = alarm.pin.PinAlarm(pin=config.POWER_PIN, value=False, pull=True)
        
        # Exit program and enter deep sleep
        #TODO: deep sleep seems to fail with invalid pin
        #alarm.exit_and_deep_sleep_until_alarms(button_alarm)
        alarm.light_sleep_until_alarms(button_alarm)
    
    def save_state_to_nvm(self):
        """Save current state to non-volatile memory for deep sleep recovery"""
        try:
            import microcontroller
            # Save current state as a single byte
            microcontroller.nvm[1] = self.current_state
            print(f"Saved power state {self.get_state_name(self.current_state)} to NVM")
        except Exception as e:
            print(f"Failed to save state to NVM: {e}")
    
    def restore_state_from_nvm(self):
        """Restore state from non-volatile memory after deep sleep restart"""
        try:
            import microcontroller
            # Read saved state from NVM
            saved_state = microcontroller.nvm[1]
            if saved_state in self.state_names:
                self.current_state = saved_state
                self.state_start_time = time.monotonic()
                print(f"Restored power state {self.get_state_name(saved_state)} from NVM")
                return True
        except Exception as e:
            print(f"Failed to restore state from NVM: {e}")
        return False
    
    def handle_power_button_press(self):
        """Handle power button press based on current state"""
        if self.current_state == self.SLEEPING or self.current_state == self.LIGHT_SLEEP:
            # Start activation sequence
            self.reset_animation_flags()
            self.transition_to(self.ACTIVATING)
        elif self.current_state == self.ACTIVE or self.current_state == self.IDLE:
            # Start deactivation sequence
            self.reset_animation_flags()
            self.transition_to(self.DEACTIVATING)
        elif self.current_state == self.DEEP_SLEEP:
            # Wake from deep sleep and start activation
            self.reset_animation_flags()
            self.transition_to(self.ACTIVATING)
    
    def handle_motion_detected(self):
        """Handle motion detection based on current state"""
        if self.current_state == self.IDLE:
            # Return to active state
            self.transition_to(self.ACTIVE)
        elif self.current_state in [self.SLEEPING, self.LIGHT_SLEEP]:
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
            self.reset_animation_flags()
            self.transition_to(self.DEACTIVATING)
    
    def update(self):
        """Update the power state machine - call this in main loop"""
        # Check for booting to sleeping transition (happens after first tick)
        if self.current_state == self.BOOTING:
            self.transition_to(self.SLEEPING)
            return  # Don't check other conditions immediately after state transition
        
        # Check for light sleep timeout (SLEEPING -> LIGHT_SLEEP)
        if self.check_light_sleep_timeout():
            print("Light sleep timeout reached - transitioning to LIGHT_SLEEP")
            self.transition_to(self.LIGHT_SLEEP)
            return
        
        # Check if we were woken by timer alarm (indicating deep sleep transition from LIGHT_SLEEP)
        if self.current_state == self.LIGHT_SLEEP and self.was_woken_by_timer():
            print("Timer wake detected - transitioning to DEEP_SLEEP")
            self.transition_to(self.DEEP_SLEEP)
            return
        
        # Check for deep sleep timeout (fallback check) - only if we've been in light sleep long enough
        if (self.current_state == self.LIGHT_SLEEP and 
            time.monotonic() - self.inactivity_timer > config.DEEP_SLEEP_TIMEOUT):
            self.transition_to(self.DEEP_SLEEP)
            return
        
        # Check for activation completion
        if (self.current_state == self.ACTIVATING and 
            self.is_activation_complete()):
            self.transition_to(self.ACTIVE)
        
        # Check for deactivation completion
        if (self.current_state == self.DEACTIVATING and 
            self.is_deactivation_complete()):
            self.transition_to(self.SLEEPING)
    
    
    def should_enter_sleep(self):
        """Check if the state machine should enter sleep mode"""
        return self.current_state in [self.SLEEPING, self.LIGHT_SLEEP, self.DEEP_SLEEP]
    
    def should_enter_light_sleep(self):
        """Check if the state machine should enter light sleep"""
        return self.current_state == self.LIGHT_SLEEP
    
    def should_enter_deep_sleep(self):
        """Check if the state machine should enter deep sleep"""
        return self.current_state == self.DEEP_SLEEP
    
    def process_tick(self, old_state, new_state):
        """Process one tick of power state machine and handle power-related events"""
        # Update power state machine
        self.update()
        
        # Handle power button events
        if new_state.has_event(new_state.BUTTON_SHORT_PRESS):
            self.handle_power_button_press()
        
        # Handle motion events
        if new_state.has_event(new_state.SWING_START) or new_state.has_event(new_state.HIT_START):
            self.handle_motion_detected()
        
        # Handle no motion timeout (transition from ACTIVE to IDLE)
        if (new_state.current == new_state.ACTIVE and 
            time.monotonic() - new_state.trigger_time > config.IDLE_TIMEOUT):
            self.handle_no_motion_timeout()
        
        # Handle idle auto-shutdown timeout (transition from IDLE to DEACTIVATING)
        if (self.current_state == self.IDLE and 
            time.monotonic() - self.state_start_time > config.AUTO_SHUTDOWN_TIMEOUT):
            self.handle_idle_auto_shutdown_timeout()
        
        # Update power enabled state based on power state machine
        if self.current_state in [
            self.ACTIVATING,
            self.ACTIVE,
            self.IDLE,
            self.DEACTIVATING
        ]:
            new_state.power_enabled = True
        else:
            new_state.power_enabled = False
        
        # Update power state in LightsaberState
        new_state.set_power_state(
            self.current_state,
            self.get_state_name(self.current_state)
        )
        
        # Log state transition if it changed
        if self.logging_manager and hasattr(self, '_last_logged_state'):
            if self._last_logged_state != self.current_state:
                print(f"Power state transition: {self.get_state_name(self._last_logged_state)} -> {self.get_state_name(self.current_state)}")
                self._last_logged_state = self.current_state
        elif self.logging_manager:
            self._last_logged_state = self.current_state
        
        return new_state
