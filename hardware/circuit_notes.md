# Circuit Notes

## Measurement Concept

The INA219 module is placed in series with the positive supply line of a
low-voltage DC load. The sensor measures the voltage across its shunt resistor
to estimate current, and it also reports bus voltage over I2C.

The microcontroller reads:

- bus voltage in volts
- current in milliamps
- power in milliwatts

The analysis script converts these readings into amperes, watts, joules, and
watt-hours.

## Wiring Summary

| INA219 Pin | Arduino Uno/Nano | ESP32 Example | Purpose |
| --- | --- | --- | --- |
| VCC | 5V | 3V3 | Sensor power |
| GND | GND | GND | Common ground |
| SDA | A4 | GPIO 21 | I2C data |
| SCL | A5 | GPIO 22 | I2C clock |
| VIN+ | DC supply positive | DC supply positive | Current path into sensor |
| VIN- | Load positive | Load positive | Current path out to load |

The load negative terminal returns directly to supply ground.

## Safety Notes

- Keep the test load low-voltage DC.
- Confirm polarity before powering the circuit.
- Start with a small current load such as an LED strip segment, small fan, or
  resistor.
- Stay within the current rating of the INA219 breakout board.
- Do not measure wall outlet power with this circuit.

## Planned Hardware Validation

1. Wire the INA219 to the microcontroller over I2C.
2. Check that the example sketch detects the sensor.
3. Connect a low-voltage load through `VIN+` and `VIN-`.
4. Compare sensor voltage with a multimeter reading.
5. Capture 30-60 seconds of serial CSV output.
6. Save the captured data into `data/raw_measurements.csv`.
7. Rerun `python analysis/energy_analysis.py`.

The analysis script can read the Arduino serial format directly:

```text
timestamp_ms,voltage_v,current_ma,power_mw
```
