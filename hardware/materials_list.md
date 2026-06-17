# Materials List

## Recommended Hardware

| Item | Purpose | Notes |
| --- | --- | --- |
| ESP32 or Arduino Uno/Nano | Microcontroller | Reads the INA219 over I2C and streams CSV over USB serial. |
| INA219 current/voltage sensor module | Electrical measurement | Measures bus voltage and current for a safe low-voltage DC load. |
| Breadboard | Prototyping | Keeps wiring temporary and easy to inspect. |
| Jumper wires | Connections | Use short, clear wiring where possible. |
| Low-voltage DC load | Test device | Examples: LED strip, small DC fan, resistor, or small motor. |
| USB cable and power source | Power and logging | USB powers the controller and allows serial logging. |

## Optional Additions

| Item | Purpose |
| --- | --- |
| Multimeter | Checks voltage and continuity before logging. |
| MicroSD module | Local data logging without a computer. |
| OLED display | Small live readout of voltage, current, and power. |
| Enclosure | Makes the prototype easier to demonstrate safely. |

## Safety Boundary

This project is designed for low-voltage DC loads only. Do not connect the
prototype to wall outlets, mains AC wiring, or household breaker panels.
