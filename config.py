"""Configuration constants for the lightsaber"""

import board
import adafruit_led_animation.color as color

# Colors (red, green, blue) -- each 0 (off) to 255 (brightest)
PRIMARY_COLOR = (100, 0, 255)  # purple
IDLE_COLOR = (25, 0, 64)       # dimmed primary (1/4 brightness)
HIT_COLOR = (255, 255, 255)    # white

STRIP_ANIMATIONS = [
    {
        "animation_type": "solid",
        "params": {
            "color": color.RED
        }
    },
    {
        "animation_type": "solid",
        "params": {
            "color": color.BLUE
        }
    },
    {
        "animation_type": "solid",
        "params": {
            "color": color.PURPLE
        }
    },
    {
        "animation_type": "solid",
        "params": {
            "color": color.GREEN
        }
    },
    {
        "animation_type": "rainbow_chase",
        "params": {
            "speed": 0.3,
            "size": 3,
            "spacing": 2
            
        }
    },
    {
        "animation_type": "sparkle",
        "params": {
            "speed": 0.1,
            "color": color.WHITE
        }
    }
]

# Animation settings
ANIMATION_DURATION = 2.0  # How long to run the color cycle animation

# Chase animation settings for power on/off
CHASE_SPEED = 0.1  # Speed of chase animation
CHASE_SIZE = 3  # Number of pixels in the chase
CHASE_SPACING = 2  # Spacing between chase elements

# Builtin pixel ColorCycle animation settings
BUILTIN_PIXEL_ANIMATIONS = {
    'activating': {
        "animation_type": "colorcycle",
        "params": {
            "speed": 1.0,
            "colors": [color.RED, color.BLUE, color.PURPLE, color.GREEN]
        }
    },
    'active': {
        "animation_type": "colorcycle",
        "params": {
            "speed": 0.5,
            "colors": [color.RED, color.GREEN, color.BLUE]
        }
    },
    'idle': {
        "animation_type": "pulse",
        "params": {
            "speed": 1.0,
            "color": color.YELLOW
        }
    },
    'deactivating': {
        "animation_type": "colorcycle",
        "params": {
            "speed": 1.0,
            "colors": [color.RED, color.BLUE, color.PURPLE, color.GREEN]
        }
    },
    'sleeping': {
        "animation_type": "pulse",
        "params": {
            "color": color.RED,
            "speed": 5.0
        }
    }
}

# Power button LED animations for each power state
POWER_BUTTON_LED_ANIMATIONS = {
    'idle': {
        "animation_type": "pulse",
        "params": {
            "speed": 1.0,
            "color": color.YELLOW
        }
    },
    'sleeping': {
        "animation_type": "pulse",
        "params": {
            "color": color.RED,
            "speed": 5.0
        }
    },
    'default': {
        "animation_type": "solid",
        "params": {
            "speed": 1.0,
            "color": color.PURPLE
        }
    }
}


# Sound effects for long press (can be modified)
SOUND_EFFECTS = ['hit', 'swing', 'on', 'off']

# Sensitivity thresholds - smaller numbers = more sensitive to motion
HIT_THRESHOLD = 350
SWING_THRESHOLD = 125

# Hardware configuration
NUM_PIXELS = 114
NEOPIXEL_PIN = board.D5  # Main NeoPixel strip
BUILTIN_NEOPIXEL_PIN = board.NEOPIXEL  # Built-in NeoPixel on Feather M4
POWER_PIN = board.D9  # Pin for alarm wake-up functionality (same as button pin)
# Note: D9 is used for both button detection and alarm wake-up
SWITCH_PIN = board.D9
ACTIVITY_PIN = board.D6  # Second button for activity functions
VOLTAGE_MONITOR_PIN = board.VOLTAGE_MONITOR  # Battery voltage monitoring

# Power button RGB LED pins (high-current MOSFET drivers)
POWER_BUTTON_LED_RED = board.D11   # Red channel for power button LED
POWER_BUTTON_LED_GREEN = board.D12 # Green channel for power button LED
POWER_BUTTON_LED_BLUE = board.D13  # Blue channel for power button LED

# NeoPixel brightness levels (0.0 to 1.0)
STRIP_BRIGHTNESS = 1.0  # Main NeoPixel strip brightness
BUILTIN_PIXEL_BRIGHTNESS = 0.3  # Built-in NeoPixel brightness (lower for status indication)
POWER_BUTTON_LED_BRIGHTNESS = 0.8  # Power button RGB LED brightness (high-current capable)

# Timing constants
POWER_ON_DURATION = 1.7
POWER_OFF_DURATION = 1.15
DEBOUNCE_TIME = 0.2
LONG_PRESS_TIME = 0.5  # Time for long press detection
ACCEL_READ_INTERVAL = 0.01  # 100Hz max for accelerometer reading
STATE_LOG_INTERVAL = 30.0  # Log state every 30 seconds

# Power state machine settings
DEEP_SLEEP_TIMEOUT = 30 # 300.0  # 5 minutes of inactivity before deep sleep
IDLE_TIMEOUT = 10.0  # Time before transitioning from ACTIVE to IDLE

# Hardware stabilization and timing
HARDWARE_STABILIZATION_DELAY = 0.1  # Delay for hardware to stabilize on startup
LED_ANIMATION_DELAY = 0.01  # Small delay in LED animations to prevent overwhelming system

# Main loop timing
ACTIVE_TICK_DELAY = 0.01  # Fast response for active states (10ms)
IDLE_TICK_DELAY = 0.1     # Slower response for idle state (100ms) - power saving
