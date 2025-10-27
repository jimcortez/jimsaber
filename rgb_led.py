"""RGB LED class for controlling high-current MOSFET RGB LEDs via PWM"""

import pwmio
import board
from digitalio import DigitalInOut, Direction

class RGBLED:
    """
    A reusable RGB LED class that controls high-current MOSFET RGB LEDs via PWM.
    
    This class provides a NeoPixel-like interface for controlling RGB LEDs connected
    to high-current MOSFET drivers. It uses PWM to modulate the brightness of each
    color channel (Red, Green, Blue).
    
    Usage:
        # Create an RGB LED instance
        led = RGBLED(board.D11, board.D12, board.D13, brightness=0.5)
        
        # Set color using RGB tuple (0-255 range)
        led[0] = (255, 0, 0)  # Red
        led[0] = (0, 255, 0)  # Green
        led[0] = (0, 0, 255)  # Blue
        led[0] = (255, 255, 0)  # Yellow
        
        # Turn off
        led[0] = (0, 0, 0)
        
        # Update brightness
        led.brightness = 0.8
    """
    
    def __init__(self, red_pin, green_pin, blue_pin, brightness=1.0, auto_write=True):
        """
        Initialize the RGB LED controller.
        
        Args:
            red_pin: Pin for red channel (e.g., board.D11)
            green_pin: Pin for green channel (e.g., board.D12)
            blue_pin: Pin for blue channel (e.g., board.D13)
            brightness: Overall brightness multiplier (0.0 to 1.0)
            auto_write: If True, automatically update LED when color is set
        """
        self._brightness = max(0.0, min(1.0, brightness))
        self.auto_write = auto_write
        
        # Initialize PWM outputs for each color channel
        self._red_pwm = pwmio.PWMOut(red_pin, frequency=1000, duty_cycle=0)
        self._green_pwm = pwmio.PWMOut(green_pin, frequency=1000, duty_cycle=0)
        self._blue_pwm = pwmio.PWMOut(blue_pin, frequency=1000, duty_cycle=0)
        
        # Current color values (0-255)
        self._red_value = 0
        self._green_value = 0
        self._blue_value = 0
        
        # PWM duty cycle range (0-65535 for 16-bit PWM)
        self._pwm_range = 65535
        
        # Initialize to off
        self._update_pwm()
    
    @property
    def brightness(self):
        """Get the current brightness level (0.0 to 1.0)"""
        return self._brightness
    
    @brightness.setter
    def brightness(self, value):
        """Set the brightness level (0.0 to 1.0)"""
        self._brightness = max(0.0, min(1.0, value))
        if self.auto_write:
            self._update_pwm()
    
    def _rgb_to_pwm(self, rgb_value):
        """
        Convert RGB value (0-255) to PWM duty cycle (0-65535) with brightness scaling.
        
        Args:
            rgb_value: RGB value from 0-255
            
        Returns:
            PWM duty cycle value from 0-65535
        """
        # Apply brightness scaling and convert to PWM range
        scaled_value = rgb_value * self._brightness
        return int((scaled_value / 255.0) * self._pwm_range)
    
    def _update_pwm(self):
        """Update the PWM duty cycles for all channels"""
        self._red_pwm.duty_cycle = self._rgb_to_pwm(self._red_value)
        self._green_pwm.duty_cycle = self._rgb_to_pwm(self._green_value)
        self._blue_pwm.duty_cycle = self._rgb_to_pwm(self._blue_value)
    
    def __setitem__(self, index, value):
        """
        Set the color using NeoPixel-like interface.
        
        Args:
            index: Must be 0 (only one LED supported)
            value: RGB tuple (r, g, b) with values 0-255
        """
        if index != 0:
            raise IndexError("RGBLED only supports index 0")
        
        if not isinstance(value, (tuple, list)) or len(value) != 3:
            raise ValueError("Color must be a 3-element tuple/list (r, g, b)")
        
        r, g, b = value
        self._red_value = max(0, min(255, int(r)))
        self._green_value = max(0, min(255, int(g)))
        self._blue_value = max(0, min(255, int(b)))
        
        if self.auto_write:
            self._update_pwm()
    
    def __getitem__(self, index):
        """
        Get the current color using NeoPixel-like interface.
        
        Args:
            index: Must be 0 (only one LED supported)
            
        Returns:
            RGB tuple (r, g, b) with current values
        """
        if index != 0:
            raise IndexError("RGBLED only supports index 0")
        
        return (self._red_value, self._green_value, self._blue_value)
    
    def fill(self, color):
        """
        Fill the LED with a color (NeoPixel-like interface).
        
        Args:
            color: RGB tuple (r, g, b) with values 0-255
        """
        self[0] = color
    
    def show(self):
        """Update the LED display (for compatibility with NeoPixel interface)"""
        self._update_pwm()
    
    def deinit(self):
        """Deinitialize the PWM outputs to free up pins"""
        self._red_pwm.deinit()
        self._green_pwm.deinit()
        self._blue_pwm.deinit()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically deinitialize"""
        self.deinit()


class MonochromeLED:
    """
    A monochrome LED class that controls a single LED via PWM.
    
    This class provides a NeoPixel-like interface for controlling a monochrome LED
    connected to a PWM pin. It converts color inputs to brightness values, allowing
    the Adafruit LED Animation library to be used with monochrome LEDs.
    
    Usage:
        # Create a monochrome LED instance
        led = MonochromeLED(board.D10, brightness=0.5)
        
        # Set color using RGB tuple (0-255 range) - brightness calculated from color
        led[0] = (255, 0, 0)    # Red -> full brightness
        led[0] = (128, 128, 128) # Gray -> 50% brightness
        led[0] = (0, 0, 0)      # Black -> off
        
        # Turn off
        led[0] = (0, 0, 0)
        
        # Update brightness
        led.brightness = 0.8
    """
    
    def __init__(self, pin, brightness=1.0, auto_write=True):
        """
        Initialize the monochrome LED controller.
        
        Args:
            pin: Pin for LED control (e.g., board.D10)
            brightness: Overall brightness multiplier (0.0 to 1.0)
            auto_write: If True, automatically update LED when color is set
        """
        self._brightness = max(0.0, min(1.0, brightness))
        self.auto_write = auto_write
        
        # Initialize PWM output
        self._pwm = pwmio.PWMOut(pin, frequency=1000, duty_cycle=0)
        
        # Current brightness value (0-255)
        self._brightness_value = 0
        
        # PWM duty cycle range (0-65535 for 16-bit PWM)
        self._pwm_range = 65535
        
        # Initialize to off
        self._update_pwm()
    
    @property
    def brightness(self):
        """Get the current brightness level (0.0 to 1.0)"""
        return self._brightness
    
    @brightness.setter
    def brightness(self, value):
        """Set the brightness level (0.0 to 1.0)"""
        self._brightness = max(0.0, min(1.0, value))
        if self.auto_write:
            self._update_pwm()
    
    def _color_to_brightness(self, color):
        """
        Convert RGB color to brightness value (0-255).
        
        Uses the luminance formula to calculate perceived brightness from RGB values.
        
        Args:
            color: RGB tuple (r, g, b) with values 0-255
            
        Returns:
            Brightness value from 0-255
        """
        if not isinstance(color, (tuple, list)) or len(color) != 3:
            return 0
        
        r, g, b = color
        # Use standard luminance formula: 0.299*R + 0.587*G + 0.114*B
        brightness = int(0.299 * r + 0.587 * g + 0.114 * b)
        return max(0, min(255, brightness))
    
    def _brightness_to_pwm(self, brightness_value):
        """
        Convert brightness value (0-255) to PWM duty cycle (0-65535) with brightness scaling.
        
        Args:
            brightness_value: Brightness value from 0-255
            
        Returns:
            PWM duty cycle value from 0-65535
        """
        # Apply brightness scaling and convert to PWM range
        scaled_value = brightness_value * self._brightness
        return int((scaled_value / 255.0) * self._pwm_range)
    
    def _update_pwm(self):
        """Update the PWM duty cycle"""
        self._pwm.duty_cycle = self._brightness_to_pwm(self._brightness_value)
    
    def __setitem__(self, index, value):
        """
        Set the color using NeoPixel-like interface.
        
        Args:
            index: Must be 0 (only one LED supported)
            value: RGB tuple (r, g, b) with values 0-255
        """
        if index != 0:
            raise IndexError("MonochromeLED only supports index 0")
        
        if not isinstance(value, (tuple, list)) or len(value) != 3:
            raise ValueError("Color must be a 3-element tuple/list (r, g, b)")
        
        # Convert color to brightness
        self._brightness_value = self._color_to_brightness(value)
        
        if self.auto_write:
            self._update_pwm()
    
    def __getitem__(self, index):
        """
        Get the current color using NeoPixel-like interface.
        
        Args:
            index: Must be 0 (only one LED supported)
            
        Returns:
            RGB tuple (r, g, b) with current brightness as grayscale
        """
        if index != 0:
            raise IndexError("MonochromeLED only supports index 0")
        
        # Return grayscale representation of current brightness
        return (self._brightness_value, self._brightness_value, self._brightness_value)
    
    def fill(self, color):
        """
        Fill the LED with a color (NeoPixel-like interface).
        
        Args:
            color: RGB tuple (r, g, b) with values 0-255
        """
        self[0] = color
    
    def show(self):
        """Update the LED display (for compatibility with NeoPixel interface)"""
        self._update_pwm()
    
    def deinit(self):
        """Deinitialize the PWM output to free up pin"""
        self._pwm.deinit()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically deinitialize"""
        self.deinit()


class OnOffLed:
    """
    A simple on/off LED class that controls a single LED via digital I/O.
    
    This class provides a NeoPixel-like interface for controlling a monochrome LED
    that can only be turned on or off (no PWM). It converts color inputs to on/off
    states, allowing the Adafruit LED Animation library to be used with simple LEDs.
    
    Usage:
        # Create an on/off LED instance
        led = OnOffLed(board.D10, brightness=0.5)
        
        # Set color using RGB tuple (0-255 range) - any non-zero color turns LED on
        led[0] = (255, 0, 0)    # Red -> LED on
        led[0] = (128, 128, 128) # Gray -> LED on
        led[0] = (0, 0, 0)      # Black -> LED off
        
        # Turn off
        led[0] = (0, 0, 0)
        
        # Turn on (any non-zero color)
        led[0] = (255, 255, 255)  # White -> LED on
        
        # Brightness is stored for compatibility but not used (LED is on/off only)
        led.brightness = 0.8
    """
    
    def __init__(self, pin, brightness=1.0, auto_write=True):
        """
        Initialize the on/off LED controller.
        
        Args:
            pin: Pin for LED control (e.g., board.D10)
            brightness: Overall brightness multiplier (0.0 to 1.0) - stored but not used
            auto_write: If True, automatically update LED when color is set
        """
        self._brightness = max(0.0, min(1.0, brightness))
        self.auto_write = auto_write
        
        # Initialize digital output
        self._digital_out = DigitalInOut(pin)
        self._digital_out.direction = Direction.OUTPUT
        self._digital_out.value = False
        
        # Current state (True = on, False = off)
        self._is_on = False
    
    @property
    def brightness(self):
        """Get the current brightness level (0.0 to 1.0)"""
        return self._brightness
    
    @brightness.setter
    def brightness(self, value):
        """Set the brightness level (0.0 to 1.0) - stored but not used for on/off LEDs"""
        self._brightness = max(0.0, min(1.0, value))
        # Note: brightness is stored for compatibility but not used since LED is on/off only
    
    def _color_to_on_off(self, color):
        """
        Convert RGB color to on/off state.
        
        Any non-zero color will turn the LED on, (0,0,0) will turn it off.
        
        Args:
            color: RGB tuple (r, g, b) with values 0-255
            
        Returns:
            True if LED should be on, False if off
        """
        if not isinstance(color, (tuple, list)) or len(color) != 3:
            return False
        
        r, g, b = color
        # If any color component is non-zero, turn LED on
        return r > 0 or g > 0 or b > 0
    
    def _update_led(self):
        """Update the LED state"""
        self._digital_out.value = self._is_on
    
    def __setitem__(self, index, value):
        """
        Set the color using NeoPixel-like interface.
        
        Args:
            index: Must be 0 (only one LED supported)
            value: RGB tuple (r, g, b) with values 0-255
        """
        if index != 0:
            raise IndexError("OnOffLed only supports index 0")
        
        if not isinstance(value, (tuple, list)) or len(value) != 3:
            raise ValueError("Color must be a 3-element tuple/list (r, g, b)")
        
        # Convert color to on/off state
        self._is_on = self._color_to_on_off(value)
        
        if self.auto_write:
            self._update_led()
    
    def __getitem__(self, index):
        """
        Get the current color using NeoPixel-like interface.
        
        Args:
            index: Must be 0 (only one LED supported)
            
        Returns:
            RGB tuple (r, g, b) - white if on, black if off
        """
        if index != 0:
            raise IndexError("OnOffLed only supports index 0")
        
        # Return white if on, black if off
        if self._is_on:
            return (255, 255, 255)
        else:
            return (0, 0, 0)
    
    def fill(self, color):
        """
        Fill the LED with a color (NeoPixel-like interface).
        
        Args:
            color: RGB tuple (r, g, b) with values 0-255
        """
        self[0] = color
    
    def show(self):
        """Update the LED display (for compatibility with NeoPixel interface)"""
        self._update_led()
    
    def deinit(self):
        """Deinitialize the digital output to free up pin"""
        self._digital_out.deinit()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically deinitialize"""
        self.deinit()
