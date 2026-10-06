#include <Arduino.h>
#include <Wire.h>

// ESP8266 Standard I2C Pins: D2 (SDA), D1 (SCL)
#define PIN_SDA 4  // D2 (GPIO 4)
#define PIN_SCL 5  // D1 (GPIO 5)

// Alternative pin pairings in case wired to D5/D6
struct PinPair {
  int sda;
  int scl;
  const char* label;
};

PinPair pairs[] = {
  { 4, 5,   "Standard D2 (SDA) & D1 (SCL)" },
  { 5, 4,   "Reversed D1 (SDA) & D2 (SCL)" },
  { 14, 12, "D5 (SDA) & D6 (SCL)" },
  { 12, 14, "D6 (SDA) & D5 (SCL)" },
  { 0, 2,   "D3 (SDA) & D4 (SCL)" }
};

int activeSDA = -1;
int activeSCL = -1;
byte detectedAddr = 0;
bool sensorFound = false;

void scanI2C() {
  Serial.println("\n=======================================================");
  Serial.println("     ESP8266 I2C BUS SCANNER FOR HW-605 SENSOR         ");
  Serial.println("=======================================================");

  for (size_t p = 0; p < sizeof(pairs)/sizeof(pairs[0]); p++) {
    int sda = pairs[p].sda;
    int scl = pairs[p].scl;
    Serial.printf("\n[PROBE] Testing %s (SDA=%d, SCL=%d)...\n", pairs[p].label, sda, scl);

    Wire.begin(sda, scl);
    delay(30);

    int count = 0;
    for (byte addr = 1; addr < 127; addr++) {
      Wire.beginTransmission(addr);
      byte err = Wire.endTransmission();
      if (err == 0) {
        Serial.printf("  🟢 ==> FOUND I2C DEVICE AT ADDRESS: 0x%02X -> ", addr);
        if (addr == 0x68 || addr == 0x69) {
          Serial.println("MATCH: HW-605 / GY-521 (MPU-6050 6-Axis Gyro & Accelerometer)!");
          activeSDA = sda;
          activeSCL = scl;
          detectedAddr = addr;
          sensorFound = true;
        } else if (addr == 0x57) {
          Serial.println("MATCH: HW-605 (MAX30102 / MAX30100 Pulse Oximeter)!");
          activeSDA = sda;
          activeSCL = scl;
          detectedAddr = addr;
          sensorFound = true;
        } else if (addr == 0x3C || addr == 0x3D) {
          Serial.println("MATCH: SSD1306 0.96\" OLED Display!");
        } else {
          Serial.println("Generic I2C Device.");
        }
        count++;
      }
    }

    if (sensorFound) {
      Serial.printf("\n✅ [SUCCESS] Sensor Locked on %s (Address: 0x%02X)!\n", pairs[p].label, detectedAddr);
      return;
    }

    if (count == 0) {
      Serial.println("  (No I2C response on this pin pair)");
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(400);

  scanI2C();

  if (!sensorFound) {
    Serial.println("\n❌ [FAIL] No HW-605 sensor detected on any pins.");
    Serial.println("Wiring check:");
    Serial.println("  HW-605 VCC -> ESP8266 3V3 (or VIN)");
    Serial.println("  HW-605 GND -> ESP8266 GND");
    Serial.println("  HW-605 SDA -> ESP8266 D2 (GPIO 4)");
    Serial.println("  HW-605 SCL -> ESP8266 D1 (GPIO 5)");
  } else if (detectedAddr == 0x68 || detectedAddr == 0x69) {
    // Wake up MPU6050
    Wire.beginTransmission(detectedAddr);
    Wire.write(0x6B); // PWR_MGMT_1
    Wire.write(0x00); // Wake up
    Wire.endTransmission();
    Serial.println(">> MPU-6050 Initialized and Active!");
  }
}

void loop() {
  if (!sensorFound) {
    delay(3000);
    scanI2C();
    return;
  }

  // Read Live MPU-6050 Accel & Gyro values if detected
  if (detectedAddr == 0x68 || detectedAddr == 0x69) {
    Wire.beginTransmission(detectedAddr);
    Wire.write(0x3B); // ACCEL_XOUT_H
    if (Wire.endTransmission(false) == 0) {
      Wire.requestFrom((uint8_t)detectedAddr, (size_t)14, true);
      if (Wire.available() >= 14) {
        int16_t rawAX = (Wire.read() << 8) | Wire.read();
        int16_t rawAY = (Wire.read() << 8) | Wire.read();
        int16_t rawAZ = (Wire.read() << 8) | Wire.read();
        int16_t rawT  = (Wire.read() << 8) | Wire.read();
        int16_t rawGX = (Wire.read() << 8) | Wire.read();
        int16_t rawGY = (Wire.read() << 8) | Wire.read();
        int16_t rawGZ = (Wire.read() << 8) | Wire.read();

        float ax = (float)rawAX / 16384.0 * 9.81;
        float ay = (float)rawAY / 16384.0 * 9.81;
        float az = (float)rawAZ / 16384.0 * 9.81;
        float tempC = ((float)rawT / 340.0) + 36.53;
        float gx = (float)rawGX / 131.0;
        float gy = (float)rawGY / 131.0;
        float gz = (float)rawGZ / 131.0;

        Serial.printf("🧭 [LIVE MPU6050] Accel: [X:%5.2f, Y:%5.2f, Z:%5.2f] m/s² | Gyro: [X:%6.1f, Y:%6.1f, Z:%6.1f] °/s | Temp: %4.1f°C\n",
                      ax, ay, az, gx, gy, gz, tempC);
      }
    }
  } else if (detectedAddr == 0x57) {
    // MAX30102 live status
    Serial.println("❤️ [LIVE MAX30102] Sensor Communication OK (Address 0x57 responded)");
  }

  delay(200);
}
