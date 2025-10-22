# Lightsaber Prop

A CircuitPython-based lightsaber prop implementation built on the [Adafruit Prop-Maker Lightsaber](https://github.com/adafruit/Adafruit_Learning_System_Guides/blob/main/PropMaker_Lightsaber/code.py) design.

## Overview

This is a personal project implementing a fully functional lightsaber prop with advanced power management, LED animations, motion detection, and sound effects. The implementation features a modular architecture with separate managers for different subsystems and a sophisticated power state machine for efficient battery usage.

## Hardware

- **Adafruit Feather M4 Express** - Main microcontroller
- **Adafruit Prop-Maker FeatherWing** - Motion detection, audio, and LED control
- **NeoPixel Strip** - 144 LED/m strip for the blade
- **Speaker** - 4 ohm 3W speaker
- **Battery** - 4400mAh lithium polymer battery
- **Buttons** - 16mm panel mount buttons for power and activity control

## Features

- **Power State Machine** - Intelligent power management with light sleep and deep sleep modes
- **LED Animations** - Multiple blade animations including solid colors, rainbow chase, and sparkle effects
- **Motion Detection** - Swing and hit detection using 3-axis accelerometer
- **Sound Effects** - Synchronized audio for power on/off, swings, and hits
- **Battery Management** - Automatic power saving and deep sleep after inactivity
- **Modular Architecture** - Separate managers for LED, sound, sensor, and logging functionality

## Documentation

- [Pinouts](docs/pinouts.md) - Complete hardware pin configuration and connections
- [Power State Machine](docs/power_state_machine.md) - Detailed power management system documentation

## Installation

1. Install CircuitPython on your Feather M4 Express
2. Copy all Python files to the CircuitPython drive
3. Install required libraries (adafruit_lis3dh, adafruit_pixelbuf, neopixel)
4. Connect hardware according to pinout documentation
5. Run `code.py` to start the lightsaber

## Usage

- **Power Button (D9)**: Press to turn on/off the lightsaber
- **Activity Button (D6)**: Press to cycle through LED animations
- **Motion**: Swing or hit the lightsaber to trigger sound effects
- **Auto Sleep**: Automatically enters power-saving mode after inactivity

## Project Structure

```
├── code.py                    # Main program entry point
├── config.py                  # Configuration constants
├── lightsaber_state.py        # State management
├── led_manager.py             # LED animation control
├── sound_manager.py           # Audio management
├── sensor_manager.py          # Motion detection
├── logging_manager.py         # System logging
├── state_machines/            # Power state machine implementation
├── sounds/                    # Audio files
└── docs/                      # Documentation
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This is a personal project and is not intended as a library or for commercial use. The implementation is based on the Adafruit Prop-Maker Lightsaber guide but has been significantly modified and enhanced for personal use.
