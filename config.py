"""Configuration constants for the lightsaber"""

import board
import adafruit_led_animation.color as color
from audio_utils import get_wav_duration

NUM_PIXELS = 115
PIXEL_WIDTH_MM = (1/NUM_PIXELS) * 1000

SOUND_EFFECTS = {
    'activating':[
        ('on', get_wav_duration('on'))
    ],
    'deactivating':[
        ('off', get_wav_duration('off'))
    ],
    'hit':[
        ('hit', get_wav_duration('hit')),
        ('hit2', get_wav_duration('hit2')),
        ('hit3', get_wav_duration('hit3'))
    ],
    'swing':[
        ('swing', get_wav_duration('swing')),
        ('swing2', get_wav_duration('swing2')),
        ('swing3', get_wav_duration('swing3'))
    ],
    'idle':[
        ('idle', get_wav_duration('idle'))
    ]
}

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
        "animation_type": "rainbow",
        "params": {
            "speed": 0.05,
            "period": 2
        }
    },
    # {
    #     "animation_type": "marble_roll",
    #     "params": {
    #         "speed": 0.02,
    #         "marble_color": color.WHITE,
    #         "marble_diameter_mm": PIXEL_WIDTH_MM,
    #         "pixel_width_mm": PIXEL_WIDTH_MM,
    #         "gravity": 9.81,
    #         "floor_friction": 2.0,
    #         "mass": 0.02,
    #         "background_color": color.BLACK
    #     }
    # }
]

#Fallback sabercolor when animations don't have a single color
PRIMARY_COLOR = color.PURPLE
STRIP_BRIGHTNESS = 0.75  # Main saber strip brightness
NEOPIXEL_PIN = board.D5  # Main NeoPixel strip
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
        "animation_type": "saber_activate",
        "params": {
            "speed": 0.01,
            "duration": 0.0,  # Will be set dynamically from state
            "color": PRIMARY_COLOR
        }
    },
    'deactivating': {
        "animation_type": "saber_activate",
        "params": {
            "speed": 0.01,
            "duration": 0.0,  # Will be set dynamically from state
            "color": color.BLACK,
            "reverse": True
        }
    }
}

BUILTIN_PIXEL_BRIGHTNESS = 1.0  # Built-in NeoPixel brightness (lower for status indication)
BUILTIN_NEOPIXEL_PIN = board.NEOPIXEL  # Built-in NeoPixel on Feather M4
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
            "speed": 0.5
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
# Note: D9 is used for both button detection and alarm wake-up
POWER_BUTTON_PIN = board.D9
# Power button RGB LED pins (high-current MOSFET drivers)
POWER_BUTTON_LED_RED = board.D11   # Red channel for power button LED
POWER_BUTTON_LED_GREEN = board.D12 # Green channel for power button LED
POWER_BUTTON_LED_BLUE = board.D13  # Blue channel for power button LED
POWER_BUTTON_LED_BRIGHTNESS = 1.0  # Power button RGB LED brightness (high-current capable)
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
            "speed": 1.0
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
# Activity button LED pin (monochrome PWM controlled)
ACTIVITY_PIN = board.A3  # Second button for activity functions (analog input)
ACTIVITY_BUTTON_THRESHOLD = 32768  # Analog threshold for button press (0-65535, ~1.65V)
ACTIVITY_BUTTON_LED_PIN = board.A4  # Pin for activity button LED
ACTIVITY_BUTTON_LED_BRIGHTNESS = 0.6  # Activity button LED brightness (monochrome PWM)
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

# Sensitivity thresholds - smaller numbers = more sensitive to motion
HIT_THRESHOLD = 350
SWING_THRESHOLD = 125

# Motion filtering parameters
MOTION_FILTER_WINDOW_SIZE = 5  # Moving average window size for noise reduction

# Motion effect durations (in seconds)
HIT_DURATION = 0.46  # How long the hit effect lasts (white flash)
SWING_DURATION = 0.31  # How long the swing effect lasts

PROP_WING_PIN = board.D10  # Pin that controls power to the prop wing board

VOLTAGE_MONITOR_PIN = board.VOLTAGE_MONITOR  # Battery voltage monitoring

DEBOUNCE_TIME = 0.2
LONG_PRESS_TIME = 0.5  # Time for long press detection
DOUBLE_PRESS_TIMEOUT = 0.5  # Maximum time between presses for double-press detection
ACCEL_READ_INTERVAL = 0.005  # 200Hz max for accelerometer reading (improved swing detection)
BATTERY_READ_INTERVAL = 60.0  # Read battery voltage once per 60 seconds
STATE_LOG_INTERVAL = 30.0  # Log state every 30 seconds

# Power state machine settings
ENABLE_DEEP_SLEEP = False  # Enable deep sleep mode (set to False to use light sleep only)
LIGHT_SLEEP_TIMEOUT = 60.0  # 1 minute of sleeping before light sleep
DEEP_SLEEP_TIMEOUT = 30 # 300.0  # 5 minutes of inactivity before deep sleep
IDLE_TIMEOUT = 10.0  # Time before transitioning from ACTIVE to IDLE
AUTO_SHUTDOWN_TIMEOUT = 300.0  # 5 minute of being IDLE before auto-shutdown
WAKING_DURATION = 0.1  # 100ms delay for WAKING state to stabilize before activation

# Main loop timing
ACTIVE_TICK_DELAY = 0.01  # Fast response for active states (10ms)
IDLE_TICK_DELAY = 0.01     # Slower response for idle state (1ms) - power saving
SLEEPING_TICK_DELAY = 0.1  # Reduced sleep interval for SLEEPING state