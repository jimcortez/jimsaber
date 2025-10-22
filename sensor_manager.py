"""Sensor management module for the lightsaber"""

import time
import busio
import board
from digitalio import DigitalInOut, Direction, Pull
from analogio import AnalogIn
import adafruit_lis3dh
from adafruit_debouncer import Debouncer, Button
import config
from lightsaber_state import LightsaberState

class SensorManager:
    """Manages all sensor inputs including accelerometer, buttons, and battery monitoring"""
    
    def __init__(self):
        """
        Initialize the sensor manager
        """
        
        # Status LEDs are now controlled by LEDManager through RGBLED class
        # Removed conflicting pin usage that was causing "D11 in use" error
        
        # Initialize switch pin as None - will be set up when needed
        self.switch_pin = None
        self.switch = None
        
        # Activity button with debouncing
        activity_pin = DigitalInOut(config.ACTIVITY_PIN)
        activity_pin.direction = Direction.INPUT
        activity_pin.pull = Pull.UP
        self.activity_button = Button(activity_pin)
        
        # Initialize switch pin only if not in sleep mode
        # Don't initialize switch pin at startup to avoid conflicts with alarm system
        # It will be initialized when needed in process_tick
        
        # Accelerometer - with error handling for missing board
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.accel = adafruit_lis3dh.LIS3DH_I2C(i2c)
            self.accel.range = adafruit_lis3dh.RANGE_4_G
            print("Accelerometer initialized successfully")
        except RuntimeError as e:
            if "No pull up found on SDA or SCL" in str(e):
                print("WARNING: Accelerometer board not detected - motion detection disabled")
                print("Check wiring or connect accelerometer board for motion detection")
                self.accel = None
            else:
                # Re-raise if it's a different RuntimeError
                raise
        except Exception as e:
            print(f"WARNING: Failed to initialize accelerometer: {e}")
            print("Motion detection will be disabled")
            self.accel = None
    
    def _initialize_switch_pin(self):
        """Initialize the switch pin for button detection"""
        try:
            if self.switch_pin is None:
                switch_pin = DigitalInOut(config.SWITCH_PIN)
                switch_pin.direction = Direction.INPUT
                switch_pin.pull = Pull.UP
                self.switch = Button(switch_pin)
                self.switch_pin = switch_pin
                print("Initialized switch pin for button detection")
        except Exception as e:
            print(f"Error initializing switch pin: {e}")
        
        # Battery voltage monitoring
        self.vbat_voltage = AnalogIn(config.VOLTAGE_MONITOR_PIN)
        
        time.sleep(config.HARDWARE_STABILIZATION_DELAY)  # Allow hardware to stabilize
    
    def get_acceleration_cached(self, new_state):
        """Read accelerometer with rate limiting for performance"""
        # Set accelerometer availability based on hardware initialization
        if not hasattr(new_state, 'accelerometer_available') or new_state.accelerometer_available is None:
            new_state.accelerometer_available = self.accel is not None
            
        if not new_state.accelerometer_available or self.accel is None:
            return None
            
        now = time.monotonic()
        if now - new_state.last_accel_read >= config.ACCEL_READ_INTERVAL:
            new_state.last_accel_read = now
            new_state.cached_acceleration = self.accel.acceleration
        return new_state.cached_acceleration
    
    def get_battery_voltage(self, new_state):
        """Get battery voltage reading"""
        try:
            # Convert ADC reading to voltage
            # Formula: (ADC_value * 3.3V) / 65536 * 2 (voltage divider)
            voltage = (self.vbat_voltage.value * 3.3) / 65536 * 2
            new_state.battery_voltage = voltage
            return voltage
        except Exception as e:
            print(f"Failed to read battery voltage: {e}")
            return 0.0
    
    # Status LEDs are now controlled by LEDManager through RGBLED class
    
    
    
    
    def process_tick(self, old_state, new_state):
        """Process one tick of sensor data and detect events"""
        # Update sensor readings
        new_state.cached_acceleration = self.get_acceleration_cached(new_state)
        new_state.battery_voltage = self.get_battery_voltage(new_state)
        
        # Initialize switch pin if not already initialized and not in sleep mode
        if (self.switch is None and 
            hasattr(new_state, 'power_state') and 
            new_state.power_state is not None and
            new_state.power_state not in [6]):  # Not in DEEP_SLEEP state
            self._initialize_switch_pin()
        
        # Update button states (only if switch is initialized)
        if self.switch is not None:
            self.switch.update()
        self.activity_button.update()
        
        # Set button pressed state (only if switch is initialized)
        new_state.button_pressed = self.switch.pressed if self.switch is not None else False
        
        # Detect power button events (only if switch is initialized)
        if self.switch is not None:
            if self.switch.fell:  # Button just pressed
                if old_state.current == old_state.OFF:
                    new_state.add_event(new_state.POWER_ON_START)
                else:
                    new_state.add_event(new_state.POWER_OFF_START)
        
        # Detect activity button events
        if self.activity_button.pressed and self.activity_button.current_duration >= config.LONG_PRESS_TIME:
            if (new_state.current >= new_state.IDLE and not new_state.long_press_triggered):
                new_state.add_event(new_state.BUTTON_LONG_PRESS)
                new_state.long_press_triggered = True
        elif not self.activity_button.pressed and new_state.long_press_triggered:
            new_state.long_press_triggered = False
        elif self.activity_button.rose:
            new_state.add_event(new_state.BUTTON_SHORT_PRESS)
        
        # Detect motion events if accelerometer is available
        if new_state.accelerometer_available and new_state.current >= new_state.IDLE:
            acceleration = new_state.cached_acceleration
            if acceleration is not None:
                x, y, z = acceleration
                acceleration_magnitude = x * x + z * z
                
                # Hit detection
                if acceleration_magnitude > config.HIT_THRESHOLD:
                    if old_state.current != old_state.HIT:
                        new_state.add_event(new_state.HIT_START)
                    else:
                        new_state.add_event(new_state.HIT_IN_PROGRESS)
                elif old_state.current == old_state.HIT:
                    new_state.add_event(new_state.HIT_STOP)
                
                # Swing detection
                elif acceleration_magnitude > config.SWING_THRESHOLD:
                    if old_state.current == old_state.IDLE:
                        new_state.add_event(new_state.SWING_START)
                    elif old_state.current == old_state.SWING:
                        new_state.add_event(new_state.SWING_IN_PROGRESS)
                elif old_state.current == old_state.SWING:
                    new_state.add_event(new_state.SWING_STOP)
                
                # Idle detection
                elif old_state.current != old_state.IDLE and old_state.current != old_state.OFF:
                    new_state.add_event(new_state.IDLE_START)
                elif old_state.current == old_state.IDLE:
                    new_state.add_event(new_state.IDLE_IN_PROGRESS)
        
        # Status LEDs are now controlled by LEDManager
        
        return new_state
    
    def release_switch_pin(self):
        """Release the switch pin for use by alarm system"""
        try:
            # Force garbage collection to free any references
            import gc
            
            # Deinitialize the Button object first
            if hasattr(self, 'switch') and self.switch:
                self.switch = None
            
            # Then deinitialize the pin and unregister it
            if hasattr(self, 'switch_pin') and self.switch_pin:
                # Properly unregister the pin from its current use
                self.switch_pin.deinit()
                self.switch_pin = None
            
            # Force garbage collection multiple times
            gc.collect()
            gc.collect()
            
            # Additional delay to ensure pin is fully released and unregistered
            import time
            time.sleep(0.2)
            
            print("Released and unregistered switch pin for alarm use")
        except Exception as e:
            print(f"Error releasing switch pin: {e}")
    
    def restore_switch_pin(self):
        """Restore the switch pin after waking from sleep"""
        try:
            if not hasattr(self, 'switch_pin') or not self.switch_pin:
                self._initialize_switch_pin()
                print("Restored switch pin after wake")
        except Exception as e:
            print(f"Error restoring switch pin: {e}")
    
