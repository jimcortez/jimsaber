# Power State Machine Documentation

## Overview

The lightsaber implements a simplified power state machine that focuses on state tracking and transitions. Sleep functionality has been moved to the main code.py loop for better control and simpler state management. This system separates power state tracking from sleep handling, providing clear state transitions and efficient power usage.

## Architecture

The power state machine is implemented using a modular approach:

- **PowerStateMachine**: Core state machine logic and transitions (simplified)
- **StateMachineBase**: Base class providing common state machine functionality
- **LightsaberState**: Integration point for power state information
- **Manager Integration**: LED, Sound, and Sensor managers respond to power states
- **Sleep Handling**: Moved to code.py main loop for better control

## Power States

### State Definitions

| State | Value | Description | Power Level | LED State | Sound State | Sleep Handling |
|-------|-------|-------------|-------------|-----------|-------------|----------------|
| **BOOTING** | 0 | Initial startup state | High | Off | Silent | No Sleep |
| **SLEEPING** | 1 | Waiting for button press | Minimal | Off | Silent | **Handled by code.py** |
| **WAKING** | 2 | Wake-up delay state | Medium | Off | Silent | No Sleep |
| **ACTIVATING** | 3 | Power-on sequence | Medium | Animation | Power-on sound | No Sleep |
| **ACTIVE** | 4 | Fully operational | High | On/Animated | Idle sounds | No Sleep |
| **IDLE** | 5 | Powered, no motion | Medium | Dim/Static | Ambient sounds | No Sleep |
| **DEACTIVATING** | 6 | Power-off sequence | Medium | Animation | Power-off sound | No Sleep |

### State Transitions

The power state machine enforces strict transition rules to ensure system stability:

```
BOOTING → SLEEPING (automatic after first tick)
SLEEPING → WAKING (power button press)
WAKING → ACTIVATING (after wake delay)
ACTIVATING → ACTIVE (both LED and sound animations complete)
ACTIVE → IDLE (no motion detected for timeout)
ACTIVE → DEACTIVATING (power button press)
IDLE → ACTIVE (motion detected)
IDLE → DEACTIVATING (power button press)
DEACTIVATING → SLEEPING (both LED and sound animations complete)
```

**Note**: Deep sleep transitions are now handled by code.py when inactivity timeout is reached during SLEEPING state.

## Implementation Details

### PowerStateMachine Class

The `PowerStateMachine` class extends `StateMachineBase` and provides:

```python
class PowerStateMachine(StateMachineBase):
    # State constants
    BOOTING = 0
    SLEEPING = 1
    WAKING = 2
    ACTIVATING = 3
    ACTIVE = 4
    IDLE = 5
    DEACTIVATING = 6
```

#### Key Methods

- **`can_transition_to(target_state)`**: Validates state transitions based on defined rules
- **`transition_to(new_state)`**: Executes state transitions with callbacks
- **`is_activation_complete()`**: Checks if both LED and sound animations are complete
- **`is_deactivation_complete()`**: Checks if both LED and sound animations are complete
- **`check_inactivity_timeout()`**: Checks if inactivity timeout reached for deep sleep
- **`process_tick(old_state, new_state)`**: Main update method called each tick

### Animation Synchronization

The power state machine implements critical synchronization for power-on and power-off sequences:

#### ACTIVATING State
- **Entry**: Starts both LED power-on animation AND power-on sound simultaneously
- **Exit Criteria**: **BOTH** LED animation AND sound must complete
- **Implementation**: Tracks completion flags for both animations
- **Benefit**: Ensures smooth, uninterrupted power-on experience

#### DEACTIVATING State
- **Entry**: Starts both LED power-off animation AND power-off sound simultaneously
- **Exit Criteria**: **BOTH** LED animation AND sound must complete
- **Implementation**: Tracks completion flags for both animations
- **Benefit**: Ensures smooth, uninterrupted power-off experience

### Sleep Implementation (code.py)

Sleep functionality has been moved to the main code.py loop for better control:

#### Deep Sleep Handling
- **Trigger**: When inactivity timeout is reached during SLEEPING state
- **Implementation**: `alarm.exit_and_deep_sleep_until_alarms()` in code.py
- **Wake Condition**: Button press alarm
- **Power Consumption**: Ultra-low (2-7mA depending on chip)
- **Program State**: **Program restarts from beginning**
- **Use Case**: Maximum battery life during extended inactivity
- **State Persistence**: Current state saved to NVM before sleep
- **Recovery**: State restored from NVM on wake-up

### State Persistence

The system implements state persistence for deep sleep recovery in code.py:

```python
def _save_state_to_nvm(self):
    """Save current state to non-volatile memory for deep sleep recovery"""
    import microcontroller
    microcontroller.nvm[1] = self.power_state_machine.current_state

def _restore_state_from_nvm(self):
    """Restore state from non-volatile memory after deep sleep restart"""
    import microcontroller
    saved_state = microcontroller.nvm[1]
    if saved_state in self.power_state_machine.state_names:
        self.power_state_machine.current_state = saved_state
```

## Manager Integration

### LED Manager Integration

The LED manager responds to power states with appropriate animations:

- **SLEEPING**: All LEDs off
- **WAKING**: All LEDs off (wake delay state)
- **ACTIVATING**: Power-on chase animation on main strip, color cycle on built-in pixel
- **ACTIVE**: Full operational LED effects
- **IDLE**: Dimmed LED effects for power saving
- **DEACTIVATING**: Power-off chase animation on main strip, color cycle on built-in pixel

### Sound Manager Integration

The sound manager plays appropriate audio for each power state:

- **SLEEPING**: Silent
- **WAKING**: Silent (wake delay state)
- **ACTIVATING**: Power-on sound effect
- **ACTIVE**: Idle ambient sounds
- **IDLE**: Ambient sounds (if configured)
- **DEACTIVATING**: Power-off sound effect

### Sensor Manager Integration

The sensor manager coordinates with the power state machine:

- **Sleep Mode**: Releases switch pin for alarm use (handled by code.py)
- **Wake Mode**: Restores switch pin for normal operation
- **Motion Detection**: Updates inactivity timer and triggers state transitions

## Configuration

### Timing Constants

```python
DEEP_SLEEP_TIMEOUT = 30  # 30 seconds of inactivity before deep sleep
IDLE_TIMEOUT = 10.0      # 10 seconds before transitioning from ACTIVE to IDLE
ACTIVE_TICK_DELAY = 0.01 # Fast response for active states (10ms)
IDLE_TICK_DELAY = 0.1    # Slower response for idle state (100ms) - power saving
```

### Hardware Configuration

```python
PROP_WING_PIN = board.D10  # Pin that controls power to the prop wing board
POWER_BUTTON_PIN = board.D9 # Pin for power button detection and alarm wake-up
ACTIVITY_PIN = board.D6    # Second button for activity functions
```

## Main Loop Integration

The power state machine is integrated into the main loop as the first processing step, with sleep handling moved to code.py:

```python
def run(self):
    while True:
        old_state = self.state
        new_state = self.state.copy()
        new_state.clear_events()
        
        # Update power state machine FIRST
        new_state = self.power_state_machine.process_tick(old_state, new_state)
        
        # Check if we should enter sleep mode (handled by code.py)
        if self._should_enter_sleep():
            self._enter_sleep_mode()
            continue
        
        # Update other managers...
        self.state = new_state
        self._adaptive_sleep()
```

**Sleep Handling**: The `_should_enter_sleep()` and `_enter_sleep_mode()` methods in code.py handle deep sleep transitions based on inactivity timeout during SLEEPING state.

## Event Handling

### Power Button Events

- **SLEEPING → WAKING**: Start wake sequence
- **ACTIVE/IDLE → DEACTIVATING**: Start power-off sequence
- **Deep Sleep Recovery**: Wake from deep sleep and start activation (handled by code.py)

### Motion Events

- **IDLE → ACTIVE**: Motion detected, return to full operation
- **SLEEPING**: Update inactivity timer

### Timeout Events

- **ACTIVE → IDLE**: No motion detected for IDLE_TIMEOUT
- **SLEEPING → Deep Sleep**: No activity for DEEP_SLEEP_TIMEOUT (handled by code.py)

## Error Handling

The power state machine includes comprehensive error handling:

- **Invalid Transitions**: Logged and prevented
- **Sleep Failures**: Fallback mechanisms for alarm setup
- **NVM Operations**: Graceful handling of non-volatile memory errors
- **Animation Failures**: Robust completion tracking

## Benefits

### Simplified Architecture
- **Focused State Machine**: PowerStateMachine focuses only on state tracking and transitions
- **Separated Sleep Handling**: Sleep functionality moved to code.py for better control
- **Cleaner Code**: Reduced complexity in state machine logic

### Power Efficiency
- **Deep Sleep**: Maximum battery life during extended inactivity (handled by code.py)
- **Adaptive Timing**: Slower processing in IDLE state for power saving
- **State Persistence**: Proper state recovery after deep sleep

### System Stability
- **Clear State Transitions**: Prevents invalid state combinations
- **Synchronization**: Ensures smooth power-on/off sequences
- **Error Recovery**: Graceful handling of hardware failures
- **Better Sleep Control**: Sleep handling in main loop allows for better timing control

### Maintainability
- **Modular Design**: Clear separation of concerns between state tracking and sleep handling
- **Event-Driven**: Clean integration with existing systems
- **Extensible**: Easy to add new states or behaviors
- **Simplified Logic**: Easier to understand and debug

## Debugging and Monitoring

The power state machine includes comprehensive logging:

- **State Transitions**: Logged with timestamps
- **Animation Events**: Tracked for synchronization
- **Sleep Events**: Wake source detection and logging
- **Error Conditions**: Detailed error reporting

## Future Enhancements

Potential improvements to the power state machine:

1. **Operational State Machine**: Separate state machine for lightsaber operational modes
2. **Battery Management**: Integration with battery monitoring for smart power decisions
3. **User Preferences**: Configurable timeouts and behaviors
4. **Advanced Sleep Modes**: Additional power-saving states
5. **State History**: Tracking of state transition patterns for optimization

---

*This documentation reflects the current implementation as of the latest codebase analysis.*
