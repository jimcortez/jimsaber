import time
import config
import alarm
from lightsaber_state import LightsaberState
from sound_manager import SoundManager
from led_manager import LEDManager
from sensor_manager import SensorManager
from logging_manager import LoggingManager
from state_machines.power_state_machine import PowerStateMachine

class Lightsaber:
    """Main lightsaber control class - now uses modular managers"""
    
    def __init__(self):
        self.state = LightsaberState()
        
        # Initialize logging manager first
        self.logging_manager = LoggingManager()
        
        # Initialize power state machine with logging manager
        self.power_state_machine = PowerStateMachine(self.logging_manager)
        
        # Initialize other managers
        self.sound_manager = SoundManager()
        self.led_manager = LEDManager()
        self.sensor_manager = SensorManager()
        
        # Load saved animation index from NVM
        self.state.current_animation_index = LEDManager.load_animation_index_static()
    
    def run(self):
        """Main program loop using event-driven architecture with power state machine"""
        # Check for deep sleep recovery
        self._handle_deep_sleep_recovery()
        
        while True:
            # Create a copy of the current state for this tick
            old_state = self.state
            new_state = self.state.copy()
            
            # Clear events for this tick
            new_state.clear_events()

            # Update power state machine FIRST to handle state transitions
            new_state = self.power_state_machine.process_tick(old_state, new_state)
            
            # Restore switch pin if we're no longer in sleep mode and pin is not restored
            if (not self._should_enter_sleep() and 
                hasattr(self.sensor_manager, 'switch_pin') and 
                self.sensor_manager.switch_pin is None):
                self.sensor_manager.restore_switch_pin()
            
            # Check if we should enter sleep mode AFTER state machine update
            if self._should_enter_sleep():
                #give the logger a chance before we go to sleep
                new_state = self.logging_manager.process_tick(old_state, new_state, self.power_state_machine)

                self._enter_sleep_mode()
                continue
            
            # Update sensor manager to detect events and update state (only when not sleeping)
            new_state = self.sensor_manager.process_tick(old_state, new_state)
            
            # Update LED and sound managers based on state transitions
            new_state = self.led_manager.process_tick(old_state, new_state, self.power_state_machine)
            new_state = self.sound_manager.process_tick(old_state, new_state, self.power_state_machine)
            
            # Process logging at the end of the tick
            new_state = self.logging_manager.process_tick(old_state, new_state, self.power_state_machine)
            
            # Update the main state with the new state
            self.state = new_state
            
            # Adaptive timing based on power state
            self._adaptive_sleep()
    
    def _handle_deep_sleep_recovery(self):
        """Handle recovery from deep sleep"""
        try:
            if alarm.wake_alarm:
                print("Woke from deep sleep")
                # Restore power state from NVM
                self.power_state_machine.restore_state_from_nvm()
        except Exception as e:
            print(f"Deep sleep recovery error: {e}")
    
    def _should_enter_sleep(self):
        """Check if we should enter sleep mode"""
        return self.power_state_machine.should_enter_sleep()
    
    def _enter_sleep_mode(self):
        """Enter appropriate sleep mode based on power state"""
        if self.power_state_machine.should_enter_light_sleep():
            # Release the switch pin for alarm use (LIGHT_SLEEP uses alarm pins)
            self.sensor_manager.release_switch_pin()
            # Small delay to ensure pin is fully released
            time.sleep(0.1)
            print("Entering light sleep")
            self.power_state_machine.enter_light_sleep()
        elif self.power_state_machine.should_enter_deep_sleep():
            # Release the switch pin for alarm use (DEEP_SLEEP uses alarm pins)
            self.sensor_manager.release_switch_pin()
            # Small delay to ensure pin is fully released
            time.sleep(0.1)
            print("Entering deep sleep")
            self.power_state_machine.enter_deep_sleep()
        # Note: SLEEPING state doesn't use alarm pins, so no pin release needed
        # Note: Pin restoration will happen in the next main loop iteration
        # when the system wakes up and processes the next tick
    
    def _adaptive_sleep(self):
        """Apply adaptive sleep timing based on power state"""
        if self.power_state_machine.current_state == self.power_state_machine.IDLE:
            # IDLE mode: slower for power saving
            time.sleep(config.IDLE_TICK_DELAY)
        elif self.power_state_machine.current_state == self.power_state_machine.SLEEPING:
            # SLEEPING mode: reduced sleep interval for power saving
            time.sleep(config.SLEEPING_TICK_DELAY)
        else:
            # All other states: fast response
            time.sleep(config.ACTIVE_TICK_DELAY)
    


# Create and run the lightsaber
if __name__ == "__main__":
    lightsaber = Lightsaber()
    lightsaber.run()
