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
        # Current sound effect file pointer for cycling
        self.current_effect_file = None
        
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
        self._close_current_effect_file()
        print("Effect stopped")
    
    def _close_current_effect_file(self):
        """Close the current effect file pointer if it exists"""
        if self.current_effect_file:
            try:
                self.current_effect_file.close()
                print("Closed current effect file")
            except Exception as e:
                print(f"Error closing effect file: {e}")
            finally:
                self.current_effect_file = None
    
    def play_effect(self, effect_name):
        """
        Play a sound effect and update internal state
        @param effect_name: name of the effect to play
        """
        self.effect_sound = (effect_name, True)
        self.sound_start_time = time.monotonic()
        return self.play_wav_filename(effect_name)
    
    def play_effect_from_playlist(self, effect_name, duration, state=None):
        """
        Play a sound effect from the playlist with proper file management
        @param effect_name: name of the effect to play
        @param duration: duration of the effect in seconds
        @param state: LightsaberState object to update with current duration
        """
        # Close previous effect file if it exists
        self._close_current_effect_file()
        
        # Update state with current duration if provided
        if state is not None:
            # Don't set global duration anymore - each sound type has its own duration
            pass
        
        # Open new effect file
        try:
            file_path = 'sounds/' + effect_name + '.wav'
            
            self.current_effect_file = open(file_path, 'rb')
            wave = audiocore.WaveFile(self.current_effect_file)
            self.audio.play(wave, loop=False)
            
            self.effect_sound = (effect_name, True)
            self.sound_start_time = time.monotonic()
            
            return True
        except Exception as e:
            print(f"Failed to play effect {effect_name}: {e}")
            self._close_current_effect_file()
            return False
    
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

    def _ensure_idle_file_open(self):
        """Ensure the idle sound file is open without starting playback"""
        if self.idle_sound is None:
            try:
                self.idle_sound = open('sounds/idle.wav', 'rb')
                
            except Exception as e:
                print(f"Failed to open idle sound file (ensure): {e}")
    
    def _close_idle_file(self):
        """Close the idle sound file if open"""
        if self.idle_sound:
            try:
                self.idle_sound.close()
                print("Closed idle sound file")
            except Exception as e:
                print(f"Error closing idle sound file: {e}")
            finally:
                self.idle_sound = None
    
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
        # Pre-open idle file so it remains available during ACTIVE/IDLE
        self._ensure_idle_file_open()
        # Get the activation sound effects list
        activation_effects = config.SOUND_EFFECTS.get('activating', [])
        if not activation_effects:
            print("No activation sound effects configured")
            return
        
        # Create and add state lock for activation sound if not already created
        if self.activation_lock is None:
            # Use the duration of the first activation sound effect
            activation_duration = activation_effects[0][1]
            self.activation_lock = StateLock(
                name="activation_sound",
                blocked=True,
                timeout=activation_duration + 0.5,  # Add small buffer to prevent race conditions
                valid_states=[power_state_machine.ACTIVATING]
            )
            power_state_machine.add_state_lock(self.activation_lock)
            print("Created activation sound state lock")

        if self.activation_lock.blocked:
            # Start playing first activation sound if not already playing
            if self.effect_sound is None and not self.is_playing():
                # Reset playlist to beginning for activation
                new_state.reset_sound_playlist('activating')
                filename, duration = new_state.get_current_sound_effect(activation_effects, 'activating')
                if filename:
                    self.play_effect_from_playlist(filename, duration, new_state)
                    print("Started activation sound")
            
            # Check if current activation sound duration has been reached
            if self.effect_sound is not None:
                
                elapsed = time.monotonic() - self.sound_start_time
                current_duration = new_state.get_current_sound_duration('activating')
                
                if elapsed >= current_duration:
                    # Current sound completed - finish activation
                    self.effect_sound = None
                    print("Activation sound completed")
                    
                    # Release the state lock
                    if self.activation_lock:
                        self.activation_lock.unlock()

                elif not self.is_playing():
                    # Sound finished but duration not reached - for activation sounds,
                    # we don't restart since they should complete based on duration
                    pass
    
    def _handle_deactivation_state(self, new_state, power_state_machine):
        """Handle sound behavior for DEACTIVATING state with state lock management"""
        
        # Get the deactivation sound effects list
        deactivation_effects = config.SOUND_EFFECTS.get('deactivating', [])
        
        if not deactivation_effects:
            print("No deactivation sound effects configured")
            return
        
        # Create and add state lock for deactivation sound if not already created
        if self.deactivation_lock is None:
            # Use the duration of the first deactivation sound effect
            deactivation_duration = deactivation_effects[0][1]
            
            
            self.deactivation_lock = StateLock(
                name="deactivation_sound",
                blocked=True,
                timeout=deactivation_duration + 0.5,  # Add small buffer to prevent race conditions
                valid_states=[power_state_machine.DEACTIVATING]
            )
            power_state_machine.add_state_lock(self.deactivation_lock)
            print("Created deactivation sound state lock")

        
        
        
        
        if self.deactivation_lock.blocked:
            # Start playing first deactivation sound if not already playing
            if self.effect_sound is None and not self.is_playing():
                
                # Reset playlist to beginning for deactivation
                new_state.reset_sound_playlist('deactivating')
                filename, duration = new_state.get_current_sound_effect(deactivation_effects, 'deactivating')
                
                
                if filename:
                    self.play_effect_from_playlist(filename, duration, new_state)
                    print("Started deactivation sound")
                    
                else:
                    print("ERROR: No deactivation filename returned")
            else:
                pass
            
            # Check if current deactivation sound duration has been reached
            if self.effect_sound is not None:
                elapsed = time.monotonic() - self.sound_start_time
                current_duration = new_state.get_current_sound_duration('deactivating')
                
                
                if elapsed >= current_duration:
                    # Current sound completed - finish deactivation
                    self.effect_sound = None
                    print("Deactivation sound completed")
                    
                    # Release the state lock
                    if self.deactivation_lock:
                        self.deactivation_lock.unlock()

                elif not self.is_playing():
                    # Sound finished but duration not reached - for deactivation sounds,
                    # we don't restart since they should complete based on duration
                    pass
    
    def _handle_hit_state(self, new_state):
        """Handle sound behavior for HIT state"""
        hit_effects = config.SOUND_EFFECTS.get('hit', [])
        if not hit_effects:
            print("No hit sound effects configured")
            return
        
        if self.effect_sound is None or self.effect_sound[0] not in [effect[0] for effect in hit_effects]:
            # Start playing hit sound from playlist
            new_state.reset_sound_playlist('hit')
            filename, duration = new_state.get_current_sound_effect(hit_effects, 'hit')
            if filename:
                self.play_effect_from_playlist(filename, duration, new_state)
                print("Started hit sound")
        elif self.effect_sound is not None:
            # Check if hit sound has finished playing
            if not self.is_playing():
                # Hit sound completed - advance to next for next hit
                new_state.advance_sound_playlist(hit_effects, 'hit')
                self.effect_sound = None
                print("Hit sound completed")
    
    def _handle_swing_state(self, new_state):
        """Handle sound behavior for SWING state"""
        swing_effects = config.SOUND_EFFECTS.get('swing', [])
        if not swing_effects:
            print("No swing sound effects configured")
            return
        
        if self.effect_sound is None or self.effect_sound[0] not in [effect[0] for effect in swing_effects]:
            # Start playing swing sound from playlist
            new_state.reset_sound_playlist('swing')
            filename, duration = new_state.get_current_sound_effect(swing_effects, 'swing')
            if filename:
                self.play_effect_from_playlist(filename, duration, new_state)
                print("Started swing sound")
        elif self.effect_sound is not None:
            # Check if swing sound has finished playing
            if not self.is_playing():
                # Swing sound completed - advance to next for next swing
                new_state.advance_sound_playlist(swing_effects, 'swing')
                self.effect_sound = None
                print("Swing sound completed")

    def process_tick(self, old_state, new_state, power_state_machine, saber_led_manager=None):
        """Process one tick of sound management based on state transitions"""

        if new_state.power_state == power_state_machine.ACTIVATING:
            # Stop any currently playing sound when transitioning TO ACTIVATING
            if old_state.power_state != power_state_machine.ACTIVATING and self.is_playing():
                
                self.stop_sound()
                self.effect_sound = None
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
            # Stop any currently playing sound when transitioning TO DEACTIVATING
            if old_state.power_state != power_state_machine.DEACTIVATING and self.is_playing():
                
                self.stop_sound()
                self.effect_sound = None
            # Close idle file at start of deactivation so it can be reopened on next activation
            self._close_idle_file()
            
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
                    # Always use the persistent idle file for hum
                    self.play_idle_sound()

        if self.is_playing() and new_state.power_state not in [power_state_machine.ACTIVATING, 
            power_state_machine.ACTIVE, power_state_machine.IDLE, 
            power_state_machine.DEACTIVATING]:
            # SLEEPING: Silent (only stop if transitioning TO sleeping)
            self.stop_sound()
        
        return new_state
    
    def cleanup(self):
        """Clean up resources when shutting down"""
        self.stop_sound()
        self._close_current_effect_file()
        self._close_idle_file()