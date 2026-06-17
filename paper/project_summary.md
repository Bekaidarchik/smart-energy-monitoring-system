# Smart Energy Monitoring System

## Abstract

This project develops a safe, low-cost energy monitoring prototype for
low-voltage DC loads. The system is designed around an Arduino or ESP32
microcontroller and an INA219 current/voltage sensor. The current version uses a
simulation-first workflow to build and verify the complete data pipeline before
hardware measurements are collected.

## Motivation

Energy monitoring connects electrical measurement, embedded systems, data
logging, and energy-efficiency analysis. A small low-voltage prototype can
demonstrate the same engineering principles used in larger monitoring systems
without working with hazardous mains electricity.

## Method

The analysis workflow generates voltage and current samples for four example
loads: an LED strip, a small DC fan, a power resistor, and a pulsed load. Power
is calculated from voltage and current:

```text
P = V * I
```

Cumulative energy is calculated by summing power over each sampling interval:

```text
E = sum(P * dt)
```

The project exports cleaned CSV data, time-series figures, a load comparison,
and a text summary.

## Hardware Plan

The planned hardware version uses an INA219 module connected over I2C to an
Arduino or ESP32. The INA219 is placed in series with the positive supply line
of a low-voltage DC load. The microcontroller streams CSV data over USB serial
for analysis.

## Safety Scope

This project measures low-voltage DC loads as a safe model of energy monitoring.
It does not measure household mains electricity, replace a smart meter, or
monitor whole-home energy use.

## Future Work

- Capture real INA219 measurements from one or more low-voltage loads.
- Add prototype photos.
- Compare simulated and measured results.
- Add optional live plotting or dashboard output.
- Add SD card logging for untethered measurements.
