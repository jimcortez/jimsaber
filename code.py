import time
import config
import alarm
import microcontroller
import digitalio
import supervisor
from lightsaber_state import LightsaberState
from sound_manager import SoundManager
from led_manager import LEDManager
from saber_led_manager import SaberLEDManager
from sensor_manager import SensorManager
from logging_manager import LoggingManager
from state_machines.power_state_machine import PowerStateMachine
from led_utils import get_animation_index_from_nvm

# Module-level variables (replacing class instance variables)
state = None
logging_manager = None
power_state_machine = None
sound_manager = None
led_manager = None
saber_led_manager = None
sensor_manager = None
prop_wing_enabled = False
prop_wing_enable_pin = None

def initialize_lightsaber():
    """Initialize all lightsaber components - replaces __init__ method"""
    global state, logging_manager, power_state_machine, sound_manager, led_manager, saber_led_manager, sensor_manager, prop_wing_enable_pin
    
    state = LightsaberState()
    
    # Initialize logging manager first
    logging_manager = LoggingManager()
    
    # Initialize power state machine with logging manager
    power_state_machine = PowerStateMachine(logging_manager)
    
    # Initialize other managers
    sound_manager = SoundManager()
    led_manager = LEDManager()
    saber_led_manager = SaberLEDManager()
    sensor_manager = SensorManager()

    prop_wing_enable_pin = digitalio.DigitalInOut(config.PROP_WING_PIN)
    prop_wing_enable_pin.direction = digitalio.Direction.OUTPUT
    prop_wing_enable_pin.value = False

    state.current_animation_index = get_animation_index_from_nvm()
    
def handle_deep_sleep_recovery():
    """Handle recovery from deep sleep"""
    try:
        if alarm.wake_alarm:
            print("Woke from deep sleep")
            #TODO: automatically transition to ACTIVATING state
    except Exception as e:
        print(f"Deep sleep recovery error: {e}")

def should_enter_light_sleep():
    """Check if we should enter sleep mode based on inactivity timeout"""
    if power_state_machine.current_state == power_state_machine.SLEEPING:
        # Check if we've been inactive long enough for deep sleep
        if power_state_machine.check_inactivity_timeout():
            return True
    return False

def enter_light_sleep_mode():
    """Enter deep sleep mode when inactivity timeout is reached"""    
    # Release the power button pin for alarm use
    sensor_manager.release_power_button_pin()
    # Small delay to ensure pin is fully released
    time.sleep(0.1)
    
    print("Entering light sleep mode")
    # Create button alarm for wake-up on power button pin
    button_alarm = alarm.pin.PinAlarm(pin=config.POWER_BUTTON_PIN, value=False, pull=True)
    timeout_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + config.LIGHT_SLEEP_TIMEOUT)
    
    # Exit program and enter deep sleep
    alarm_result = alarm.light_sleep_until_alarms(button_alarm, timeout_alarm)

    if alarm_result == timeout_alarm:
        return False # Timeout occurred, we should enter deep sleep
    return True

def enter_deep_sleep_mode():
    """Enter deep sleep mode when inactivity timeout is reached"""    
    # Release the power button pin for alarm use
    sensor_manager.release_power_button_pin()
    # Small delay to ensure pin is fully released
    time.sleep(0.1)
    
    print("Entering deep sleep due to inactivity timeout")
    try:
        # Create button alarm for wake-up on power button pin
        button_alarm = alarm.pin.PinAlarm(pin=config.POWER_BUTTON_PIN, value=False, pull=True)
        
        # Exit program and enter deep sleep
        alarm.exit_and_deep_sleep_until_alarms(button_alarm)
    except Exception as e:
        print(f"Deep sleep error: {e}")
        # Fallback to light sleep if deep sleep fails
        try:
            button_alarm = alarm.pin.PinAlarm(pin=config.POWER_BUTTON_PIN, value=False)
            alarm.light_sleep_until_alarms(button_alarm)
            print("Fell back to light sleep, reloading")
            supervisor.reload()
        except Exception as e2:
            print(f"Light sleep fallback error: {e2}")

def set_prop_wing_power(enabled):
    """Control the prop wing board power"""
    global prop_wing_enable_pin
    prop_wing_enable_pin.value = enabled

def adaptive_sleep():
    """Apply adaptive sleep timing based on power state"""
    if power_state_machine.current_state == power_state_machine.IDLE:
        # IDLE mode: slower for power saving
        time.sleep(config.IDLE_TICK_DELAY)
    elif power_state_machine.current_state == power_state_machine.SLEEPING:
        # SLEEPING mode: reduced sleep interval for power saving
        time.sleep(config.SLEEPING_TICK_DELAY)
    elif power_state_machine.current_state == power_state_machine.WAKING:
        # WAKING mode: fast response for quick transition
        time.sleep(config.ACTIVE_TICK_DELAY)
    else:
        # All other states: fast response
        time.sleep(config.ACTIVE_TICK_DELAY)


def main_loop():
    """Main program loop using event-driven architecture with power state machine"""
    global state

    # Check for deep sleep recovery
    handle_deep_sleep_recovery()
    
    while True:
        # Create a copy of the current state for this tick
        old_state = state
        new_state = state.copy(clear_events=True)
        
        new_state = sensor_manager.process_tick(old_state, new_state)
        
        # Update power state machine AFTER sensor events are generated
        new_state = power_state_machine.process_tick(old_state, new_state)

        if new_state.power_state == power_state_machine.WAKING:
            set_prop_wing_power(True)
        elif new_state.power_state in [power_state_machine.SLEEPING]:
            set_prop_wing_power(False)
        
        # Restore power button pin if we're no longer in sleep mode and pin is not restored
        if (not should_enter_light_sleep() and 
            sensor_manager.power_button_pin is None):
            sensor_manager.restore_power_button_pin()
        
        # Check if we should enter sleep mode AFTER state machine update
        if should_enter_light_sleep():
            #give the logger a chance before we go to sleep
            new_state = logging_manager.process_tick(old_state, new_state, power_state_machine, sound_manager)

            needs_deep_sleep = enter_light_sleep_mode() # blocks until woken up

            # Only enter deep sleep if it's enabled in config
            if needs_deep_sleep and config.ENABLE_DEEP_SLEEP:
                enter_deep_sleep_mode()
                break # this never actually happens, deep sleep stops the main loop
            
            power_state_machine.update_inactivity_timer()
        
        # During WAKING, run minimal processing to avoid USB connection issues
        if (new_state.power_state != power_state_machine.WAKING):
            new_state = led_manager.process_tick(old_state, new_state, power_state_machine)
            new_state = saber_led_manager.process_tick(old_state, new_state, power_state_machine)
            new_state = sound_manager.process_tick(old_state, new_state, power_state_machine, saber_led_manager)
            
            # Process logging at the end of the tick (skip during wake and activation)
            new_state = logging_manager.process_tick(old_state, new_state, power_state_machine, sound_manager)
        
        # Update the main state with the new state
        state = new_state
        
        # Adaptive timing based on power state
        adaptive_sleep()

# Initialize and run the lightsaber
if __name__ == "__main__":
    initialize_lightsaber()
    main_loop()
