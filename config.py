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
            "speed": 0.01
        }
    },
    'default': {
        "animation_type": "solid",
        "params": {
            "color": color.PURPLE
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
            "speed": 0.01
        }
    },
    'pressed': {
        "animation_type": "solid",
        "params": {
            "color": color.WHITE
        }
    },
    'default': {
        "animation_type": "solid",
        "params": {
            "color": color.PURPLE
        }
    }
}

# Activity button LED animations for each power state
ACTIVITY_BUTTON_LED_ANIMATIONS = {
    'idle': {
        "animation_type": "pulse",
        "params": {
            "speed": 2.0,
            "color": color.WHITE
        }
    },
    'pressed': {
        "animation_type": "solid",
        "params": {
            "color": color.WHITE
        }
    },
    'default': {
        "animation_type": "solid",
        "params": {
            "color": color.WHITE
        }
    }
}

SABER_STATE_ANIMATIONS = {
    'hit': {
        "animation_type": "solid",
        "params": {
            "color": color.WHITE
        }
    },
    # 'swing': {
    #     "animation_type": "solid",
    #     "params": {
    #         "color": color.GREEN
    #     }
    # },
    'activating': {
        "animation_type": "chase",
        "params": {
            "speed": 0.1,
            "size": 3,
            "spacing": 2,
            "color": PRIMARY_COLOR
        }
    },
    'deactivating': {
        "animation_type": "chase",
        "params": {
            "speed": 0.1,
            "size": 3,
            "spacing": 2,
            "color": (25, 0, 64),  # Black for power off
            "reverse": True
        }
    }
}

# Sound effects for long press (can be modified)
SOUND_EFFECTS = ['hit', 'swing', 'on', 'off']

# Sensitivity thresholds - smaller numbers = more sensitive to motion
HIT_THRESHOLD = 350
SWING_THRESHOLD = 125

# Motion effect durations (in seconds)
HIT_DURATION = 0.5  # How long the hit effect lasts (white flash)
SWING_DURATION = 0.3  # How long the swing effect lasts

PROP_WING_PIN = board.D10  # Pin that controls power to the prop wing board

# Note: D9 is used for both button detection and alarm wake-up
POWER_BUTTON_PIN = board.D9
# Power button RGB LED pins (high-current MOSFET drivers)
POWER_BUTTON_LED_RED = board.D11   # Red channel for power button LED
POWER_BUTTON_LED_GREEN = board.D12 # Green channel for power button LED
POWER_BUTTON_LED_BLUE = board.D13  # Blue channel for power button LED
POWER_BUTTON_LED_BRIGHTNESS = 0.8  # Power button RGB LED brightness (high-current capable)


# Activity button LED pin (monochrome PWM controlled)
ACTIVITY_PIN = board.A3  # Second button for activity functions (analog input)
ACTIVITY_BUTTON_THRESHOLD = 32768  # Analog threshold for button press (0-65535, ~1.65V)
ACTIVITY_BUTTON_LED_PIN = board.A4  # Pin for activity button LED
ACTIVITY_BUTTON_LED_BRIGHTNESS = 0.6  # Activity button LED brightness (monochrome PWM)

# NeoPixel brightness levels (0.0 to 1.0)
NUM_PIXELS = 150
NEOPIXEL_PIN = board.D5  # Main NeoPixel strip
STRIP_BRIGHTNESS = 1.0  # Main NeoPixel strip brightness

BUILTIN_NEOPIXEL_PIN = board.NEOPIXEL  # Built-in NeoPixel on Feather M4
BUILTIN_PIXEL_BRIGHTNESS = 0.5  # Built-in NeoPixel brightness (lower for status indication)

VOLTAGE_MONITOR_PIN = board.VOLTAGE_MONITOR  # Battery voltage monitoring

# Timing constants
POWER_ON_DURATION = 1.7
POWER_OFF_DURATION = 1.15
ACTIVATION_DURATION = 1.7  # User-configurable duration for power on/off animations and sounds
DEACTIVATION_DURATION = 1.15  # User-configurable duration for power off animations and sounds
DEBOUNCE_TIME = 0.2
LONG_PRESS_TIME = 0.5  # Time for long press detection
DOUBLE_PRESS_TIMEOUT = 0.5  # Maximum time between presses for double-press detection
ACCEL_READ_INTERVAL = 0.01  # 100Hz max for accelerometer reading
STATE_LOG_INTERVAL = 30.0  # Log state every 30 seconds

# Power state machine settings
ENABLE_DEEP_SLEEP = False  # Enable deep sleep mode (set to False to use light sleep only)
LIGHT_SLEEP_TIMEOUT = 60.0  # 1 minute of sleeping before light sleep
DEEP_SLEEP_TIMEOUT = 30 # 300.0  # 5 minutes of inactivity before deep sleep
IDLE_TIMEOUT = 10.0  # Time before transitioning from ACTIVE to IDLE
AUTO_SHUTDOWN_TIMEOUT = 300.0  # 5 minute of being IDLE before auto-shutdown
WAKING_DURATION = 0.1  # 100ms delay for WAKING state to stabilize before activation

# Hardware stabilization and timing
HARDWARE_STABILIZATION_DELAY = 0.1  # Delay for hardware to stabilize on startup

# Main loop timing
ACTIVE_TICK_DELAY = 0.01  # Fast response for active states (10ms)
IDLE_TICK_DELAY = 0.1     # Slower response for idle state (100ms) - power saving
SLEEPING_TICK_DELAY = 0.1  # Reduced sleep interval for SLEEPING state