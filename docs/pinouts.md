# Lightsaber Pinouts

This document describes the pin connections for the [Adafruit Prop-Maker Lightsaber](https://learn.adafruit.com/lightsaber-featherwing?view=all) project.

## Hardware Overview

The lightsaber project uses:
- **Adafruit Feather M4 Express** - Main microcontroller board
- **Adafruit Prop-Maker FeatherWing** - Motion detection, audio, and LED control board
- **NeoPixel Strip** - 144 LED/m strip for the blade
- **Speaker** - 4 ohm 3W, 40mm diameter speaker
- **Battery** - 4400mAh lithium polymer battery
- **Buttons** - 16mm diameter panel mount buttons

## Feather M4 Express Pins (Main Board)

### Digital Pins Used

| Pin | Function | Component | Description |
|-----|----------|-----------|-------------|
| **D5** | NeoPixel Output | NeoPixel Strip | Main blade LED strip connection (via Prop-Maker FeatherWing) |
| **D6** | Digital Input | Activity Button | Second button for effects and animation cycling |
| **D9** | Digital Input | Power Switch | Main power on/off button |
| **D11** | Digital Output | Status LED (Red) | Red status indicator LED |
| **D12** | Digital Output | Status LED (Green) | Green status indicator LED |
| **D13** | Digital Output | Status LED (Blue) | Blue status indicator LED |

### Analog Pins Used

| Pin | Function | Component | Description |
|-----|----------|-----------|-------------|
| **A0** | Audio Output | Speaker | Audio output to speaker via Prop-Maker FeatherWing |

### I2C Communication

| Pin | Function | Component | Description |
|-----|----------|-----------|-------------|
| **SCL** | I2C Clock | Accelerometer | I2C clock line to LIS3DH accelerometer on Prop-Maker FeatherWing |
| **SDA** | I2C Data | Accelerometer | I2C data line to LIS3DH accelerometer on Prop-Maker FeatherWing |

### Built-in Features

| Feature | Function | Description |
|---------|----------|-------------|
| **NEOPIXEL** | Built-in LED | Single RGB LED on the Feather M4 board for status indication |
| **USB** | Programming/Charging | microUSB port for programming and battery charging |
| **VOLTAGE_MONITOR** | Battery Monitoring | Built-in analog input for battery voltage monitoring |

## Prop-Maker FeatherWing (Add-on Board)

The Prop-Maker FeatherWing connects to the Feather M4 Express via the standard Feather headers and provides integrated functionality:

### Integrated Components (On FeatherWing)

| Component | Function | Description |
|-----------|----------|-------------|
| **LIS3DH Accelerometer** | Motion Detection | 3-axis accelerometer for swing and hit detection |
| **Class-D Audio Amplifier** | Sound Output | Built-in audio amplifier for speaker output |
| **NeoPixel Driver** | LED Control | Built-in driver for NeoPixel strip control |
| **3W RGB LED Driver** | Status LEDs | Driver for status indicator LEDs |

### JST Connectors (On FeatherWing)

| Connector | Function | Component | Description |
|-----------|----------|-----------|-------------|
| **NeoPixel Port** | LED Strip | NeoPixel Strip | 3-pin JST connector for blade LEDs |
| **Speaker Port** | Audio Output | Speaker | 2-pin JST connector for speaker connection |
| **Battery Port** | Power Input | Battery | 2-pin JST connector for battery connection |

### FeatherWing Pin Connections

| FeatherWing Function | Feather M4 Pin | Description |
|----------------------|----------------|-------------|
| **NeoPixel Control** | D5 | Controls NeoPixel strip via built-in driver |
| **Audio Input** | A0 | Receives audio signal from Feather M4 |
| **I2C Accelerometer** | SCL/SDA | Communicates with LIS3DH accelerometer |
| **Status LED Control** | D11/D12/D13 | Controls status LEDs via built-in driver |

## Physical Connections

### Buttons (16mm Panel Mount) - Connected to Feather M4
- **Power Switch**: Connected to **Feather M4 D9** - Main on/off functionality
- **Activity Button**: Connected to **Feather M4 D6** - Secondary button for effects and animation cycling

### LED Connections
- **NeoPixel Strip**: Connected to **Prop-Maker FeatherWing NeoPixel port** (controlled by Feather M4 D5)
- **Built-in NeoPixel**: Single RGB LED on **Feather M4 board** (NEOPIXEL pin)
- **Status LEDs**: Red (D11), Green (D12), Blue (D13) on **Feather M4** for system status indication

### Audio Connection
- **Speaker**: 4 ohm 3W speaker connected to **Prop-Maker FeatherWing speaker port**
- **Audio Output**: **Feather M4 A0** pin provides audio signal to **Prop-Maker FeatherWing**

### Power Management
- **Battery**: 4400mAh lithium polymer battery connected to **Prop-Maker FeatherWing battery port**
- **Voltage Monitoring**: **Feather M4 VOLTAGE_MONITOR** pin for battery level detection
- **Charging**: **Feather M4 microUSB** port for battery charging

### Motion Detection
- **Accelerometer**: LIS3DH 3-axis accelerometer integrated on **Prop-Maker FeatherWing**
- **I2C Communication**: **Feather M4 SCL/SDA** pins connect to accelerometer on **Prop-Maker FeatherWing**

## Hardware Specifications

### NeoPixel Strip
- **Type**: Adafruit Mini Skinny NeoPixel Digital RGB LED Strip
- **Density**: 144 LED/m
- **Length**: 1 meter
- **Connection**: 3-pin JST cable to Prop-Maker FeatherWing

### Speaker
- **Type**: 4 ohm 3W speaker
- **Diameter**: 40mm
- **Connection**: 2-pin JST cable to Prop-Maker FeatherWing

### Battery
- **Type**: Lithium Ion Battery Pack
- **Capacity**: 4400mAh
- **Voltage**: 3.7V nominal
- **Connection**: 2-pin JST cable to Prop-Maker FeatherWing

### Buttons
- **Type**: 16mm diameter panel mount buttons
- **Power Switch**: Momentary pushbutton for main power control
- **Activity Button**: RGB momentary pushbutton for effects and animation cycling

## Assembly Notes

### Feather Stack
- **Feather M4 Express** (main board) and **Prop-Maker FeatherWing** (add-on board) connect via standard Feather headers
- Short Feather Male Headers (12-pin and 16-pin) used for connection
- Short Feather Female Headers (12-pin and 16-pin) for secure mounting

### Wiring
- **NeoPixel Strip**: 3-pin JST cable from blade to **Prop-Maker FeatherWing NeoPixel port**
- **Speaker**: 2-pin JST cable to **Prop-Maker FeatherWing speaker port**
- **Battery**: 2-pin JST cable to **Prop-Maker FeatherWing battery port**
- **Buttons**: Direct wiring to **Feather M4 pins D6 and D9**

### Access Points
- **Programming**: **Feather M4 microUSB** port accessible when blade emitter is removed
- **Volume Control**: Audio volume trim pot on **Prop-Maker FeatherWing**
- **Reset Button**: **Feather M4 reset** button accessible through hilt opening

## Troubleshooting

### Common Connection Issues
1. **NeoPixel strip not lighting**: Check 3-pin JST connection to Prop-Maker FeatherWing
2. **No sound output**: Verify speaker connection and volume trim pot setting
3. **Buttons not responding**: Check wiring to D6 and D9 pins
4. **Motion detection not working**: Verify I2C connections (SCL/SDA) between boards

### Power Issues
1. **Battery not charging**: Check microUSB connection and battery JST connection
2. **Low battery performance**: Verify 4400mAh battery capacity and connections
3. **Deep sleep issues**: Check power button wiring and alarm functionality

## References

- [Adafruit Prop-Maker Lightsaber Guide](https://learn.adafruit.com/lightsaber-featherwing?view=all)
- [Adafruit Feather M4 Express](https://www.adafruit.com/product/3857)
- [Adafruit Prop-Maker FeatherWing](https://www.adafruit.com/product/3988)
- [Adafruit NeoPixel Strip](https://www.adafruit.com/product/1461)