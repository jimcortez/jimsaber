"""Sensor management module for the lightsaber"""

import time
import busio
import board
from digitalio import DigitalInOut, Direction, Pull
from analogio import AnalogIn
import adafruit_lis3dh
from adafruit_debouncer import Button, Debouncer
import config
from lightsaber_state import LightsaberState

class SensorManager:
    """Manages all sensor inputs including accelerometer, buttons, and battery monitoring"""
    
    def __init__(self):
        """
        Initialize the sensor manager
        """
        # Initialize power button pin as None - will be set up when needed
        self.power_button_pin = None
        self.power_button = None
        
        # Power button double-press tracking
        self.last_power_button_press_time = 0.0
        self.power_button_press_count = 0
        self.pending_single_press = False  # Track if we have a pending single press waiting
        
        # Activity button with analog input and debouncing
        self.activity_pin = AnalogIn(config.ACTIVITY_PIN)
        # Create a debouncer with a lambda that reads analog value and compares to threshold
        self.activity_button = Debouncer(
            lambda: self.activity_pin.value > config.ACTIVITY_BUTTON_THRESHOLD,
            interval=config.DEBOUNCE_TIME
        )
        
        self._initialize_power_button_pin()
        
        # Battery voltage monitoring - initialize once in constructor
        self.vbat_voltage = AnalogIn(config.VOLTAGE_MONITOR_PIN)
        
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
    
    def _initialize_power_button_pin(self):
        """Initialize the power button pin for button detection"""
        try:
            if self.power_button_pin is None:
                power_button_pin = DigitalInOut(config.POWER_BUTTON_PIN)
                power_button_pin.direction = Direction.INPUT
                power_button_pin.pull = Pull.UP
                self.power_button = Button(power_button_pin)
                self.power_button_pin = power_button_pin
                print("Initialized power button pin for button detection")
        except Exception as e:
            print(f"Error initializing power button pin: {e}")
    
    def get_acceleration_cached(self, new_state):
        """Read accelerometer with rate limiting for performance"""
        if self.accel is None:
            return None
            
        now = time.monotonic()
        if now - new_state.last_accel_read >= config.ACCEL_READ_INTERVAL:
            new_state.last_accel_read = now
            new_state.cached_acceleration = self.accel.acceleration
        return new_state.cached_acceleration
    
    def get_battery_voltage(self, new_state):
        """Get battery voltage reading with rate limiting"""
        now = time.monotonic()
        
        # Force read on boot (when last_battery_read is 0) or when interval has elapsed
        if new_state.last_battery_read == 0.0 or (now - new_state.last_battery_read >= config.BATTERY_READ_INTERVAL):
            try:
                # Convert ADC reading to voltage
                # Formula: (ADC_value * 3.3V) / 65536 * 2 (voltage divider)
                voltage = (self.vbat_voltage.value * 3.3) / 65536 * 2
                new_state.battery_voltage = voltage
                new_state.last_battery_read = now
            except Exception as e:
                print(f"Failed to read battery voltage: {e}")
                # Keep the previous cached value on error
        
        # Return the cached value
        return new_state.battery_voltage
    
    def _update_sensor_readings(self, new_state):
        """Update sensor readings for the current tick"""
        new_state.cached_acceleration = self.get_acceleration_cached(new_state)
        new_state.battery_voltage = self.get_battery_voltage(new_state)
    
    def _process_power_button(self, old_state, new_state):
        """Process power button events and state updates with double-press detection"""
        # Initialize power button pin if not already initialized
        self._initialize_power_button_pin()
        
        # Update button states (only if power button is initialized)
        self.power_button.update()
        
        # Set button pressed state (only if power button is initialized)
        new_state.power_button_pressed = self.power_button.pressed
        
        current_time = time.monotonic()
        
        # Detect button press (rising edge)
        if not old_state.power_button_pressed and new_state.power_button_pressed:
            print("Power button pressed")
            
            time_since_last_press = current_time - self.last_power_button_press_time
            
            # Check if this is a double-press (within timeout window and we have a pending press)
            if self.pending_single_press and time_since_last_press < config.DOUBLE_PRESS_TIMEOUT:
                # Double-press detected - only trigger animation cycle if swing_hit_state is not OFF
                if new_state.swing_hit_state != new_state.OFF:
                    print("Power button double-press detected - cycling animation")
                    new_state.add_event(new_state.ACTIVITY_BUTTON_SHORT_PRESS)
                else:
                    print("Power button double-press detected but swing_hit_state is OFF - triggering normal press")
                    # Still add the normal short press event
                    new_state.add_event(new_state.POWER_BUTTON_SHORT_PRESS)
                
                # Clear pending single press since we handled it as a double-press
                self.pending_single_press = False
                self.power_button_press_count = 0
            else:
                # First press - don't emit event yet, wait to see if there's a second press
                self.pending_single_press = True
                self.power_button_press_count = 1
            
            # Update last press time
            self.last_power_button_press_time = current_time
        
        # Check if we have a pending single press that has timed out
        if self.pending_single_press:
            time_since_last_press = current_time - self.last_power_button_press_time
            if time_since_last_press >= config.DOUBLE_PRESS_TIMEOUT:
                # Timeout expired - emit the pending single press event
                print("Single press confirmed after timeout")
                new_state.add_event(new_state.POWER_BUTTON_SHORT_PRESS)
                self.pending_single_press = False
                self.power_button_press_count = 0
    
    def _process_activity_button(self, old_state, new_state):
        """Process activity button events and state updates with analog input"""
        # Update the debouncer
        self.activity_button.update()
        
        # Update state with current button pressed status
        new_state.activity_button_pressed = self.activity_button.value

        if old_state.activity_button_pressed != new_state.activity_button_pressed:
            print("Activity button pressed state changed")
        
        # Detect activity button events
        if self.activity_button.value and self.activity_button.current_duration >= config.LONG_PRESS_TIME:
            if (new_state.swing_hit_state >= new_state.IDLE and not new_state.long_press_triggered):
                print("Activity button long press detected")
                new_state.add_event(new_state.ACTIVITY_BUTTON_LONG_PRESS)
                new_state.long_press_triggered = True
        elif not self.activity_button.value and new_state.long_press_triggered:
            new_state.long_press_triggered = False
        elif self.activity_button.rose:
            print("Activity button short press detected")
            new_state.add_event(new_state.ACTIVITY_BUTTON_SHORT_PRESS)
    
    def _process_motion_detection(self, old_state, new_state):
        """Process motion detection events from accelerometer"""
        # Detect motion events
        if new_state.swing_hit_state != new_state.OFF:
            acceleration = new_state.cached_acceleration
            if acceleration is not None:
                x, y, z = acceleration
                acceleration_magnitude = x * x + z * z
                
                # Determine current motion state based on acceleration thresholds
                if acceleration_magnitude > config.HIT_THRESHOLD:
                    # HIT: Large acceleration detected
                    print("HIT: Large acceleration detected")
                    if old_state.swing_hit_state != old_state.HIT:
                        new_state.add_event(new_state.HIT_START)
                        new_state.swing_hit_state = new_state.HIT
                    else:
                        new_state.add_event(new_state.HIT_IN_PROGRESS)
                        new_state.swing_hit_state = new_state.HIT
                        
                elif acceleration_magnitude > config.SWING_THRESHOLD:
                    print("SWING: Moderate acceleration detected")
                    # SWING: Moderate acceleration detected
                    if old_state.swing_hit_state == old_state.HIT:
                        # Transitioning from HIT to SWING
                        new_state.add_event(new_state.HIT_STOP)
                        new_state.add_event(new_state.SWING_START)
                        new_state.swing_hit_state = new_state.SWING
                    elif old_state.swing_hit_state == old_state.IDLE:
                        # Starting swing from idle
                        new_state.add_event(new_state.SWING_START)
                        new_state.swing_hit_state = new_state.SWING
                    elif old_state.swing_hit_state == old_state.SWING:
                        # Continue swinging
                        new_state.add_event(new_state.SWING_IN_PROGRESS)
                        new_state.swing_hit_state = new_state.SWING
                        
                else:
                    # IDLE: Low acceleration detected
                    if old_state.swing_hit_state == old_state.HIT:
                        # Transitioning from HIT to IDLE
                        new_state.add_event(new_state.HIT_STOP)
                        new_state.add_event(new_state.IDLE_START)
                        new_state.swing_hit_state = new_state.IDLE
                    elif old_state.swing_hit_state == old_state.SWING:
                        # Transitioning from SWING to IDLE
                        new_state.add_event(new_state.SWING_STOP)
                        new_state.add_event(new_state.IDLE_START)
                        new_state.swing_hit_state = new_state.IDLE
                    elif old_state.swing_hit_state == old_state.IDLE:
                        # Continue idle
                        new_state.add_event(new_state.IDLE_IN_PROGRESS)
                        new_state.swing_hit_state = new_state.IDLE
    
    def release_power_button_pin(self):
        """Release the power button pin for use by alarm system"""
        try:
            # Deinitialize the Button object first
            if hasattr(self, 'power_button') and self.power_button:
                self.power_button = None
            
            # Then deinitialize the pin and unregister it
            if hasattr(self, 'power_button_pin') and self.power_button_pin:
                # Properly unregister the pin from its current use
                self.power_button_pin.deinit()
                self.power_button_pin = None
        
            
            # Additional delay to ensure pin is fully released and unregistered
            time.sleep(0.2)
            
            print("Released and unregistered power button pin for alarm use")
        except Exception as e:
            print(f"Error releasing power button pin: {e}")
    
    def restore_power_button_pin(self):
        """Restore the power button pin after waking from sleep"""
        try:
            if not self.power_button_pin:
                self._initialize_power_button_pin()
                print("Restored power button pin after wake")
        except Exception as e:
            print(f"Error restoring power button pin: {e}")
    
    def process_tick(self, old_state, new_state):
        """Process one tick of sensor data and detect events"""

        self._update_sensor_readings(new_state)
        self._process_power_button(old_state, new_state)
        self._process_activity_button(old_state, new_state)
        self._process_motion_detection(old_state, new_state)
        return new_state