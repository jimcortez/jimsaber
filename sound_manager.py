"""Sound management module for the lightsaber"""

import audioio
import audiocore
import board
import config
from lightsaber_state import LightsaberState

class SoundManager:
    """Manages all audio functionality for the lightsaber"""
    
    def __init__(self):
        """
        Initialize the sound manager
        """
        self.audio = audioio.AudioOut(board.A0)
        
    def play_wav(self, name, loop=False):
        """
        Play a WAV file in the 'sounds' directory.
        @param name: partial file name string, complete name will be built around
                     this, e.g. passing 'foo' will play file 'sounds/foo.wav'.
        @param loop: if True, sound will repeat indefinitely (until interrupted
                     by another sound).
        """
        print("playing", name)
        try:
            wave_file = open('sounds/' + name + '.wav', 'rb')
            wave = audiocore.WaveFile(wave_file)
            self.audio.play(wave, loop=loop)
            # Note: current_sound and idle_sound_playing are managed in process_tick
            return True
        except Exception as e:
            print(f"Failed to play sound {name}: {e}")
            return False
    
    def stop_sound(self):
        """Stop any currently playing sound"""
        try:
            self.audio.stop()
            # Note: state variables are managed in process_tick
            print("Sound stopped")
        except Exception as e:
            print(f"Failed to stop sound: {e}")
    
    def stop_effect(self):
        """Stop any currently playing effect"""
        self.stop_sound()
        print("Effect stopped")
    
    def play_effect(self, effect_name, new_state):
        """
        Play a sound effect and update state
        @param effect_name: name of the effect to play
        @param new_state: current state object to update
        """
        new_state.effect_playing = True
        new_state.effect_sound = effect_name
        new_state.idle_sound_playing = False
        return self.play_wav(effect_name)
    
    def play_random_effect(self, new_state):
        """Play a random sound effect from the configured list"""
        import random
        effect = random.choice(config.SOUND_EFFECTS)
        self.play_effect(effect, new_state)
        print(f"Playing effect: {effect}")
    
    def play_idle_sound(self, new_state):
        """Play the idle hum sound in a loop"""
        if not new_state.idle_sound_playing and not new_state.effect_playing:
            new_state.idle_sound_playing = True
            self.play_wav('idle', loop=True)
    
    def play_power_on_sound(self):
        """Play the power on sound"""
        return self.play_wav('on')
    
    def play_power_off_sound(self):
        """Play the power off sound"""
        return self.play_wav('off')
    
    def play_swing_sound(self):
        """Play the swing sound"""
        return self.play_effect('swing')
    
    def play_hit_sound(self):
        """Play the hit sound"""
        return self.play_effect('hit')
    
    def is_playing(self):
        """Check if any sound is currently playing"""
        try:
            return self.audio.playing
        except Exception:
            return False
    
    
    def process_tick(self, old_state, new_state, power_state_machine):
        """Process one tick of sound management based on state transitions"""
        # Handle power state machine integration
        self._handle_power_state_sound_behavior(old_state, new_state, power_state_machine)
        
        # Handle motion events
        if new_state.has_event(new_state.HIT_START):
            self.play_hit_sound()
            new_state.current_sound = 'hit'
        elif new_state.has_event(new_state.SWING_START):
            self.play_swing_sound()
            new_state.current_sound = 'swing'
        elif new_state.has_event(new_state.IDLE_START):
            # Resume idle sound when returning to idle
            if new_state.current >= new_state.IDLE:
                self.play_idle_sound(new_state)
                new_state.current_sound = 'idle'
        
        # Handle button events
        if new_state.has_event(new_state.BUTTON_LONG_PRESS):
            self.play_random_effect(new_state)
            new_state.current_sound = 'random_effect'
        elif new_state.has_event(new_state.BUTTON_SHORT_PRESS):
            if new_state.effect_playing:
                self.stop_effect()
                new_state.current_sound = None
        
        # Monitor effect completion
        if new_state.effect_playing and not self.is_playing():
            new_state.effect_playing = False
            new_state.effect_sound = None
            new_state.current_sound = None
            # Resume idle sound if lightsaber is on
            if new_state.current >= new_state.IDLE:
                self.play_idle_sound(new_state)
                new_state.current_sound = 'idle'
        
        # Update state from sound manager
        new_state.effect_playing = new_state.effect_playing
        new_state.effect_sound = new_state.effect_sound
        new_state.idle_sound_playing = new_state.idle_sound_playing
        
        return new_state
    
    def _handle_power_state_sound_behavior(self, old_state, new_state, power_state_machine):
        """Handle sound behavior based on power state machine states"""
        if not hasattr(new_state, 'power_state') or new_state.power_state is None:
            return
        
        # Check if we're transitioning TO sleeping state
        old_power_state = getattr(old_state, 'power_state', None)
        new_power_state = new_state.power_state
        
        if new_power_state == power_state_machine.SLEEPING:
            # SLEEPING: Silent (only stop if transitioning TO sleeping)
            if old_power_state != power_state_machine.SLEEPING:
                self.stop_sound()
            
        elif new_state.power_state == power_state_machine.ACTIVATING:
            # ACTIVATING: Play power-on sound
            if not new_state.effect_playing:
                self.play_power_on_sound()
                new_state.current_sound = 'on'
            
        elif new_state.power_state == power_state_machine.ACTIVE:
            # ACTIVE: Play idle sounds
            if not new_state.effect_playing and not new_state.idle_sound_playing:
                self.play_idle_sound(new_state)
                new_state.current_sound = 'idle'
            
        elif new_state.power_state == power_state_machine.IDLE:
            # IDLE: Play ambient sounds
            if not new_state.effect_playing and not new_state.idle_sound_playing:
                self.play_idle_sound(new_state)
                new_state.current_sound = 'idle'
            
        elif new_state.power_state == power_state_machine.DEACTIVATING:
            # DEACTIVATING: Play power-off sound
            if not new_state.effect_playing:
                self.play_power_off_sound()
                new_state.current_sound = 'off'
            
        elif new_state.power_state == power_state_machine.DEEP_SLEEP:
            # DEEP_SLEEP: Silent
            self.stop_sound()
    
    
