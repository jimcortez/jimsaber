# Power State Machine Documentation

## Overview

The lightsaber implements a sophisticated power state machine that manages power consumption, sleep modes, and hardware coordination. This system separates power management from operational behavior, providing clear state transitions and efficient power usage.

## Architecture

The power state machine is implemented using a modular approach:

- **PowerStateMachine**: Core state machine logic and transitions
- **StateMachineBase**: Base class providing common state machine functionality
- **LightsaberState**: Integration point for power state information
- **Manager Integration**: LED, Sound, and Sensor managers respond to power states

## Power States

### State Definitions

| State | Value | Description | Power Level | LED State | Sound State | CircuitPython Sleep |
|-------|-------|-------------|-------------|-----------|-------------|---------------------|
| **BOOTING** | 0 | Initial startup state | High | Off | Silent | No Sleep |
| **SLEEPING** | 1 | Light sleep, waiting for button | Minimal | Off | Silent | **Light Sleep** |
| **ACTIVATING** | 2 | Power-on sequence | Medium | Animation | Power-on sound | No Sleep |
| **ACTIVE** | 3 | Fully operational | High | On/Animated | Idle sounds | No Sleep |
| **IDLE** | 4 | Powered, no motion | Medium | Dim/Static | Ambient sounds | No Sleep |
| **DEACTIVATING** | 5 | Power-off sequence | Medium | Animation | Power-off sound | No Sleep |
| **DEEP_SLEEP** | 6 | Ultra-low power, program restarts | Minimal | Off | Silent | **Deep Sleep** |

### State Transitions

The power state machine enforces strict transition rules to ensure system stability:

```
BOOTING → SLEEPING (automatic after first tick)
SLEEPING → ACTIVATING (power button press)
SLEEPING → DEEP_SLEEP (5 minutes of inactivity)
ACTIVATING → ACTIVE (both LED and sound animations complete)
ACTIVE → IDLE (no motion detected for timeout)
ACTIVE → DEACTIVATING (power button press)
IDLE → ACTIVE (motion detected)
IDLE → DEACTIVATING (power button press)
DEACTIVATING → SLEEPING (both LED and sound animations complete)
DEEP_SLEEP → SLEEPING (program restart from deep sleep)
DEEP_SLEEP → ACTIVATING (power button press from deep sleep)
```

## Implementation Details

### PowerStateMachine Class

The `PowerStateMachine` class extends `StateMachineBase` and provides:

```python
class PowerStateMachine(StateMachineBase):
    # State constants
    BOOTING = 0
    SLEEPING = 1
    ACTIVATING = 2
    ACTIVE = 3
    IDLE = 4
    DEACTIVATING = 5
    DEEP_SLEEP = 6
```

#### Key Methods

- **`can_transition_to(target_state)`**: Validates state transitions based on defined rules
- **`transition_to(new_state)`**: Executes state transitions with callbacks
- **`is_activation_complete()`**: Checks if both LED and sound animations are complete
- **`is_deactivation_complete()`**: Checks if both LED and sound animations are complete
- **`enter_light_sleep()`**: Enters CircuitPython light sleep mode
- **`enter_deep_sleep()`**: Enters CircuitPython deep sleep mode
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

### CircuitPython Sleep Implementation

The power state machine integrates with CircuitPython's alarm system for power management:

#### Light Sleep (SLEEPING State)
- **Implementation**: `alarm.light_sleep_until_alarms()`
- **Wake Conditions**: Button press alarm OR timeout alarm
- **Power Consumption**: Minimal but higher than deep sleep
- **Program State**: Continues running, resumes after sleep statement
- **Use Case**: Quick wake-up for immediate response

#### Deep Sleep (DEEP_SLEEP State)
- **Implementation**: `alarm.exit_and_deep_sleep_until_alarms()`
- **Wake Condition**: Button press alarm
- **Power Consumption**: Ultra-low (2-7mA depending on chip)
- **Program State**: **Program restarts from beginning**
- **Use Case**: Maximum battery life during extended inactivity

### State Persistence

The system implements state persistence for deep sleep recovery:

```python
def save_state_to_nvm(self):
    """Save current state to non-volatile memory for deep sleep recovery"""
    import microcontroller
    microcontroller.nvm[1] = self.current_state

def restore_state_from_nvm(self):
    """Restore state from non-volatile memory after deep sleep restart"""
    import microcontroller
    saved_state = microcontroller.nvm[1]
    if saved_state in self.state_names:
        self.current_state = saved_state
```

## Manager Integration

### LED Manager Integration

The LED manager responds to power states with appropriate animations:

- **SLEEPING**: All LEDs off
- **ACTIVATING**: Power-on chase animation on main strip, color cycle on built-in pixel
- **ACTIVE**: Full operational LED effects
- **IDLE**: Dimmed LED effects for power saving
- **DEACTIVATING**: Power-off chase animation on main strip, color cycle on built-in pixel
- **DEEP_SLEEP**: All LEDs off

### Sound Manager Integration

The sound manager plays appropriate audio for each power state:

- **SLEEPING**: Silent
- **ACTIVATING**: Power-on sound effect
- **ACTIVE**: Idle ambient sounds
- **IDLE**: Ambient sounds (if configured)
- **DEACTIVATING**: Power-off sound effect
- **DEEP_SLEEP**: Silent

### Sensor Manager Integration

The sensor manager coordinates with the power state machine:

- **Sleep Mode**: Releases switch pin for alarm use
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
POWER_PIN = board.D9      # Pin for alarm wake-up functionality
SWITCH_PIN = board.D9     # Same pin used for button detection and alarm
ACTIVITY_PIN = board.D6   # Second button for activity functions
```

## Main Loop Integration

The power state machine is integrated into the main loop as the first processing step:

```python
def run(self):
    while True:
        old_state = self.state
        new_state = self.state.copy()
        new_state.clear_events()
        
        # Update power state machine FIRST
        new_state = self.power_state_machine.process_tick(old_state, new_state)
        
        # Check if we should enter sleep mode
        if self._should_enter_sleep():
            self._enter_sleep_mode()
            continue
        
        # Update other managers...
        self.state = new_state
        self._adaptive_sleep()
```

## Event Handling

### Power Button Events

- **SLEEPING → ACTIVATING**: Start power-on sequence
- **ACTIVE/IDLE → DEACTIVATING**: Start power-off sequence
- **DEEP_SLEEP → ACTIVATING**: Wake from deep sleep and start activation

### Motion Events

- **IDLE → ACTIVE**: Motion detected, return to full operation
- **SLEEPING**: Update inactivity timer

### Timeout Events

- **ACTIVE → IDLE**: No motion detected for IDLE_TIMEOUT
- **SLEEPING → DEEP_SLEEP**: No activity for DEEP_SLEEP_TIMEOUT

## Error Handling

The power state machine includes comprehensive error handling:

- **Invalid Transitions**: Logged and prevented
- **Sleep Failures**: Fallback mechanisms for alarm setup
- **NVM Operations**: Graceful handling of non-volatile memory errors
- **Animation Failures**: Robust completion tracking

## Benefits

### Power Efficiency
- **Light Sleep**: Quick wake-up with minimal power consumption
- **Deep Sleep**: Maximum battery life during extended inactivity
- **Adaptive Timing**: Slower processing in IDLE state for power saving

### System Stability
- **Clear State Transitions**: Prevents invalid state combinations
- **Synchronization**: Ensures smooth power-on/off sequences
- **Error Recovery**: Graceful handling of hardware failures

### Maintainability
- **Modular Design**: Clear separation of concerns
- **Event-Driven**: Clean integration with existing systems
- **Extensible**: Easy to add new states or behaviors

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
