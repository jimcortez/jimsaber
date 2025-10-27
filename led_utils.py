"""Shared LED animation utilities for the lightsaber"""

import time
import adafruit_led_animation.color as color
# LED Animation library imports
from adafruit_led_animation.animation.chase import Chase
from adafruit_led_animation.animation.solid import Solid
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.sparkle import Sparkle
from adafruit_led_animation.animation.colorcycle import ColorCycle
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.blink import Blink
from adafruit_led_animation.animation.comet import Comet
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from adafruit_led_animation.group import AnimationGroup
import config
import microcontroller

# Animation class mapping
ANIMATION_CLASSES = {
    "solid": Solid,
    "rainbow_chase": RainbowChase,
    "sparkle": Sparkle,
    "colorcycle": ColorCycle,
    "pulse": Pulse,
    "chase": Chase,
    "rainbow": Rainbow,
    "blink": Blink,
    "comet": Comet,
    "rainbow_comet": RainbowComet,
    "rainbow_sparkle": RainbowSparkle,
}

class LEDAnimationManager:
    """Base class for managing LED animations with shared functionality"""
    
    def __init__(self, target_pixel, animation_configs=None):
        """
        Initialize the LED animation manager
        
        Args:
            target_pixel: The pixel object to animate (NeoPixel, RGBLED, etc.)
            animation_configs: Dictionary of animation configurations
        """
        self.target_pixel = target_pixel
        self.animation_configs = animation_configs or {}
        
        # Animation group tracking
        self.active_animations = []
        self.animation_group = None
        
        # Initialize animations from configs
        self._setup_animations()
    
    def _create_animation_from_config(self, animation_config, target_pixel=None):
        """Create an animation instance from animation config for the specified target pixel"""
        if target_pixel is None:
            target_pixel = self.target_pixel
            
        animation_type = animation_config["animation_type"]
        animation_class = ANIMATION_CLASSES.get(animation_type)
        
        if animation_class:
            try:
                return animation_class(target_pixel, **animation_config.get("params", {}))
            except TypeError as te:
                print(f"Failed to create animation: {animation_type} -> params: {animation_config.get("params", None)}")
                raise te
        else:
            raise ValueError(f"Unknown animation type: {animation_type}. Supported types: {list(ANIMATION_CLASSES.keys())}")
    
    def _setup_animations(self):
        """Initialize animations from configuration"""
        self.animations = {}
        self.default_animations = {}
        
        for state, animation_config in self.animation_configs.items():
            if state == 'default':
                self.default_animations['default'] = self._create_animation_from_config(animation_config)
            else:
                self.animations[state] = self._create_animation_from_config(animation_config)
    
    def get_animation(self, state):
        """Get animation for the given state, falling back to default if not found"""
        return self.animations.get(state, self.default_animations.get('default'))
    
    def _update_active_animations(self, animations_list):
        """Update the list of active animations and recreate the AnimationGroup if needed"""
        # Check if the animations list has changed
        if animations_list != self.active_animations:
            self.active_animations = animations_list
            # Create new AnimationGroup with the current active animations
            if self.active_animations:
                self.animation_group = AnimationGroup(*self.active_animations)
            else:
                self.animation_group = None
            print(f"Updated active animations: {len(self.active_animations)} animations")
    
    def animate(self):
        """Animate all active animations using the AnimationGroup"""
        if self.animation_group:
            self.animation_group.animate()

def create_animation_from_config(animation_config, target_pixel):
    """Create an animation instance from animation config for the specified target pixel"""
    animation_type = animation_config["animation_type"]
    animation_class = ANIMATION_CLASSES.get(animation_type)
    
    if animation_class:
        return animation_class(target_pixel, **animation_config.get("params", {}))
    else:
        raise ValueError(f"Unknown animation type: {animation_type}. Supported types: {list(ANIMATION_CLASSES.keys())}")

def mix_colors(color1, color2, weight2):
    """
    Optimized color mixing with bounds checking.
    @param color1: first color, as an (r,g,b) tuple
    @param color2: second color, as an (r,g,b) tuple
    @param weight2: blend weight (ratio) of second color, 0.0 to 1.0
    @return: (r,g,b) tuple, blended color
    """
    weight2 = max(0.0, min(1.0, weight2))
    weight1 = 1.0 - weight2
    return (
        int(color1[0] * weight1 + color2[0] * weight2),
        int(color1[1] * weight1 + color2[1] * weight2),
        int(color1[2] * weight1 + color2[2] * weight2)
    )

def get_animation_index_from_nvm():
    """Load animation index from NVM"""
    try:
        # Read the saved animation index from NVM
        saved_index = microcontroller.nvm[0]
        # Validate the index is within bounds of STRIP_ANIMATIONS config
        if 0 <= saved_index < len(config.STRIP_ANIMATIONS):
            print(f"Loaded animation index {saved_index} from NVM")
            return saved_index
        else:
            print(f"Invalid saved index {saved_index}, using default 0")
            return 0
    except Exception as e:
        print(f"Failed to load animation index: {e}, using default 0")
        return 0

def save_animation_index_to_nvm(animation_index):
    """Save animation index to NVM"""
    try:
        # Store the animation index as a single byte
        microcontroller.nvm[0] = animation_index
        print(f"Saved animation index {animation_index} to NVM")
    except Exception as e:
        print(f"Failed to save animation index: {e}")


