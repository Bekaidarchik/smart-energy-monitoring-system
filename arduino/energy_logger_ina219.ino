/*
  Smart Energy Monitoring System - INA219 CSV Logger

  Hardware:
    - Arduino Uno/Nano or ESP32
    - INA219 current/voltage sensor
    - Safe low-voltage DC load

  Serial output:
    timestamp_ms,voltage_v,current_ma,power_mw

  Safety:
    This sketch is for low-voltage DC testing only. Do not connect the
    circuit to mains electricity.
*/

#include <Wire.h>
#include <Adafruit_INA219.h>

Adafruit_INA219 ina219;

const unsigned long SAMPLE_INTERVAL_MS = 1000;
unsigned long lastSampleMs = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }

  Serial.println("timestamp_ms,voltage_v,current_ma,power_mw");

  if (!ina219.begin()) {
    Serial.println("ERROR: INA219 not found. Check VCC, GND, SDA, and SCL wiring.");
    while (true) {
      delay(1000);
    }
  }

  ina219.setCalibration_32V_2A();
}

void loop() {
  unsigned long nowMs = millis();
  if (nowMs - lastSampleMs < SAMPLE_INTERVAL_MS) {
    return;
  }
  lastSampleMs = nowMs;

  float busVoltageV = ina219.getBusVoltage_V();
  float currentMa = ina219.getCurrent_mA();
  float powerMw = ina219.getPower_mW();

  Serial.print(nowMs);
  Serial.print(",");
  Serial.print(busVoltageV, 3);
  Serial.print(",");
  Serial.print(currentMa, 3);
  Serial.print(",");
  Serial.println(powerMw, 3);
}
