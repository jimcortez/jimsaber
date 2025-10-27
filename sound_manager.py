"""Sound management module for the lightsaber"""

import time
import audioio
import audiocore
import board
import config
from lightsaber_state import LightsaberState
from state_machines.state_machine_base import StateLock

class SoundManager:
    """Manages all audio functionality for the lightsaber"""
    
    def __init__(self):
        """
        Initialize the sound manager
        """
        self.audio = audioio.AudioOut(board.A0)
        self.activation_lock = None
        self.deactivation_lock = None
        
        # Audio state tracking (moved from LightsaberState)
        # effect_sound: tuple of (filename, is_currently_playing)
        self.effect_sound = None
        # idle_sound: pointer to the wave file object that stays open
        self.idle_sound = None
        # Track when effects started for duration-based completion
        self.sound_start_time = 0.0
        
    def play_wav_filename(self, name, loop=False):
        """
        Play a WAV file in the 'sounds' directory by filename.
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
            return True
        except Exception as e:
            print(f"Failed to play sound {name}: {e}")
            return False
    
    def play_wav(self, wave_file, loop=False):
        """
        Play a WAV file from an already-opened file pointer.
        @param wave_file: open file pointer to a WAV file
        @param loop: if True, sound will repeat indefinitely (until interrupted
                     by another sound).
        """
        try:
            wave = audiocore.WaveFile(wave_file)
            self.audio.play(wave, loop=loop)
            return True
        except Exception as e:
            print(f"Failed to play sound from file pointer: {e}")
            return False
    
    def stop_sound(self):
        """Stop any currently playing sound"""
        try:
            self.audio.stop()
            print("Sound stopped")
        except Exception as e:
            print(f"Failed to stop sound: {e}")
    
    def stop_effect(self):
        """Stop any currently playing effect"""
        self.stop_sound()
        self.effect_sound = None
        print("Effect stopped")
    
    def play_effect(self, effect_name):
        """
        Play a sound effect and update internal state
        @param effect_name: name of the effect to play
        """
        self.effect_sound = (effect_name, True)
        self.sound_start_time = time.monotonic()
        return self.play_wav_filename(effect_name)
    
    def play_random_effect(self):
        """Play a random sound effect from the configured list"""
        import random
        effect = random.choice(config.SOUND_EFFECTS)
        self.play_effect(effect)
        print(f"Playing effect: {effect}")
    
    def play_idle_sound(self):
        """Play the idle hum sound in a loop"""
        # Open idle sound file if not already open
        if self.idle_sound is None:
            try:
                self.idle_sound = open('sounds/idle.wav', 'rb')
                print("Opened idle sound file")
            except Exception as e:
                print(f"Failed to open idle sound file: {e}")
                return
        
        # Play with looping - audio module handles the looping internally
        try:
            self.play_wav(self.idle_sound, loop=True)
            print("Playing idle sound")
        except Exception as e:
            print(f"Failed to play idle sound: {e}")
    
    def play_power_on_sound(self):
        """Play the power on sound"""
        return self.play_wav_filename('on')
    
    def play_power_off_sound(self):
        """Play the power off sound"""
        return self.play_wav_filename('off')
    
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
    
    def _handle_activation_state(self, new_state, power_state_machine):
        """Handle sound behavior for ACTIVATING state with state lock management"""
        # Create and add state lock for activation sound if not already created
        if self.activation_lock is None:
            self.activation_lock = StateLock(
                name="activation_sound",
                blocked=True,
                timeout=config.ACTIVATION_DURATION + 2.0,  # Add buffer time
                valid_states=[power_state_machine.ACTIVATING]
            )
            power_state_machine.add_state_lock(self.activation_lock)
            print("Created activation sound state lock")

        if self.activation_lock.blocked:
            # Start playing power-on sound if not already playing
            if self.effect_sound is None and not self.is_playing():
                self.play_power_on_sound()
                self.effect_sound = ('on', True)
                self.sound_start_time = time.monotonic()
                print("Started power-on sound")
            
            # Check if power-on sound duration has been reached
            elif self.effect_sound is not None:
                elapsed = time.monotonic() - self.sound_start_time
                if elapsed >= config.ACTIVATION_DURATION:
                    self.effect_sound = None
                    print("Power-on sound completed (duration-based)")
                    
                    # Release the state lock
                    if self.activation_lock:
                        self.activation_lock.unlock()

                elif not self.is_playing():
                    # Sound finished but duration not reached - loop the sound
                    self.play_power_on_sound()
    
    def _handle_deactivation_state(self, new_state, power_state_machine):
        """Handle sound behavior for DEACTIVATING state with state lock management"""
        # Create and add state lock for deactivation sound if not already created
        if self.deactivation_lock is None:
            self.deactivation_lock = StateLock(
                name="deactivation_sound",
                blocked=True,
                timeout=config.DEACTIVATION_DURATION + 2.0,  # Add buffer time
                valid_states=[power_state_machine.DEACTIVATING]
            )
            power_state_machine.add_state_lock(self.deactivation_lock)
            print("Created deactivation sound state lock")

        if self.deactivation_lock.blocked:
            # Start playing power-off sound if not already playing
            if self.effect_sound is None:
                self.play_power_off_sound()
                self.effect_sound = ('off', True)
                self.sound_start_time = time.monotonic()
                print("Started power-off sound")
            
            # Check if power-on sound duration has been reached
            elif self.effect_sound is not None:
                elapsed = time.monotonic() - self.sound_start_time
                if elapsed >= config.DEACTIVATION_DURATION:
                    self.effect_sound = None
                    print("Power-off sound completed (duration-based)")
                    
                    # Release the state lock
                    if self.deactivation_lock:
                        self.deactivation_lock.unlock()
            elif not self.is_playing():
                # Sound finished but duration not reached - loop the sound
                self.play_power_off_sound()
    
    def _handle_hit_state(self, new_state):
        """Handle sound behavior for HIT state"""
        if self.effect_sound is None or self.effect_sound[0] != 'hit':
            # Start playing hit sound
            self.play_hit_sound()
            print("Started hit sound")
        elif self.effect_sound is not None and self.effect_sound[0] == 'hit':
            # Check if hit sound has finished playing
            if not self.is_playing():
                self.effect_sound = None
                print("Hit sound completed")
    
    def _handle_swing_state(self, new_state):
        """Handle sound behavior for SWING state"""
        if self.effect_sound is None or self.effect_sound[0] != 'swing':
            # Start playing swing sound
            self.play_swing_sound()
            print("Started swing sound")
        elif self.effect_sound is not None and self.effect_sound[0] == 'swing':
            # Check if swing sound has finished playing
            if not self.is_playing():
                self.effect_sound = None
                print("Swing sound completed")

    def process_tick(self, old_state, new_state, power_state_machine, saber_led_manager=None):
        """Process one tick of sound management based on state transitions"""

        if new_state.power_state == power_state_machine.ACTIVATING:
            self._handle_activation_state(new_state, power_state_machine)
            return new_state
        elif (old_state.power_state == power_state_machine.ACTIVATING and 
            new_state.power_state != power_state_machine.ACTIVATING and 
            self.activation_lock):
            # Clean up activation lock if transitioning away from ACTIVATING
            print("Transitioning away from ACTIVATING - cleaning up activation lock")
            self.activation_lock.unlock()
            power_state_machine.remove_state_lock("activation_sound")
            self.activation_lock = None
        
        if new_state.power_state == power_state_machine.DEACTIVATING:
            self._handle_deactivation_state(new_state, power_state_machine)
            return new_state
        elif (old_state.power_state == power_state_machine.DEACTIVATING and 
            new_state.power_state != power_state_machine.DEACTIVATING and 
            self.deactivation_lock):
            # Clean up deactivation lock if transitioning away from DEACTIVATING
            print("Transitioning away from DEACTIVATING - cleaning up deactivation lock")
            self.deactivation_lock.unlock()
            power_state_machine.remove_state_lock("deactivation_sound")
            self.deactivation_lock = None

        if new_state.power_state == power_state_machine.ACTIVE or new_state.power_state == power_state_machine.IDLE:
            # Handle motion events in ACTIVE and IDLE states
            if new_state.has_event(new_state.HIT_START) or (self.effect_sound and self.effect_sound[0] == 'hit'):
                self._handle_hit_state(new_state)
            elif new_state.has_event(new_state.SWING_START) or (self.effect_sound and self.effect_sound[0] == 'swing'):
                self._handle_swing_state(new_state)

            # Update effect_sound playing status
            if self.effect_sound is not None:
                effect_name, _ = self.effect_sound
                if not self.is_playing():
                    # Effect finished playing
                    self.effect_sound = (effect_name, False)
            
            # Play idle sound if no effect is playing
            if self.effect_sound is None or not self.effect_sound[1]:
                if not self.is_playing():
                    self.play_idle_sound()

        if self.is_playing() and new_state.power_state not in [power_state_machine.ACTIVATING, 
            power_state_machine.ACTIVE, power_state_machine.IDLE, 
            power_state_machine.DEACTIVATING]:
            # SLEEPING: Silent (only stop if transitioning TO sleeping)
            self.stop_sound()
        
        return new_state