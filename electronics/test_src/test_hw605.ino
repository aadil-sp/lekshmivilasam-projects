/*
 * =========================================================================================
 * Seeed Studio XIAO ESP32 - Universal HW-605 (MAX30102 / MPU-6050) Sensor Testbench
 * =========================================================================================
 */

#include <Arduino.h>
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"

MAX30105 maxSensor;

// Pin combinations to scan on Seeed XIAO
struct I2CPinPair {
  int sda;
  int scl;
  const char* label;
};

I2CPinPair pinPairs[] = {
  { 8, 9,   "ESP32-C3 Super Mini / GPIO 8 (SDA) / GPIO 9 (SCL)" }
};

int activeSDA = -1;
int activeSCL = -1;
bool isMAX30102 = false;
bool isMPU6050 = false;
byte mpuAddress = 0x68;

// Function Prototypes
void scanI2CBus();
void setupSensors();
void readMAX30102Data();
void readMPU6050Data();

void scanI2CBus() {
  Serial.println("\n------------------------------------------------------");
  Serial.println("  SCANNING I2C BUS FOR HW-605 SENSORS (0x57 / 0x68)   ");
  Serial.println("------------------------------------------------------");

  for (size_t i = 0; i < sizeof(pinPairs)/sizeof(pinPairs[0]); i++) {
    int sda = pinPairs[i].sda;
    int scl = pinPairs[i].scl;
    Serial.printf("[SCAN] Probing %s (SDA=%d, SCL=%d)...\n", pinPairs[i].label, sda, scl);

    Wire.end();
    delay(40);
    Wire.begin(sda, scl, 100000);
    delay(40);

    int foundCount = 0;
    for (byte addr = 1; addr < 127; addr++) {
      Wire.beginTransmission(addr);
      byte err = Wire.endTransmission();
      if (err == 0) {
        Serial.printf("  ==> FOUND I2C Device at 0x%02X: ", addr);
        if (addr == 0x57) {
          Serial.println("🟢 [MATCH: HW-605 MAX30102 Pulse Oximeter / Heart Rate!]");
          isMAX30102 = true;
          activeSDA = sda;
          activeSCL = scl;
        } else if (addr == 0x68 || addr == 0x69) {
          Serial.println("🟢 [MATCH: HW-605 / GY-521 MPU-6050 6-Axis Gyro & Accel!]");
          isMPU6050 = true;
          mpuAddress = addr;
          activeSDA = sda;
          activeSCL = scl;
        } else if (addr == 0x3C || addr == 0x3D) {
          Serial.println("🔵 [SSD1306 OLED Display]");
        } else {
          Serial.println("⚪ [Generic I2C Device]");
        }
        foundCount++;
      }
    }

    if (isMAX30102 || isMPU6050) {
      Serial.printf("[SUCCESS] HW-605 confirmed on SDA=GPIO%d, SCL=GPIO%d!\n", activeSDA, activeSCL);
      return;
    }

    if (foundCount == 0) {
      Serial.println("  No I2C devices responded on these pins.");
    }
  }
}

void setup() {
  Serial.begin(115200);
  unsigned long start = millis();
  while (!Serial && (millis() - start < 3000));
  delay(500);

  Serial.println("\n=======================================================");
  Serial.println("   SEEED XIAO + HW-605 SENSOR DIAGNOSTIC TESTBENCH    ");
  Serial.println("=======================================================");

  scanI2CBus();

  if (!isMAX30102 && !isMPU6050) {
    Serial.println("\n❌ [FAIL] No HW-605 sensor detected on any I2C pins!");
    Serial.println("Please check physical wiring:");
    Serial.println("  HW-605 VCC / VIN -> XIAO 3.3V (or 5V)");
    Serial.println("  HW-605 GND       -> XIAO GND");
    Serial.println("  HW-605 SDA       -> XIAO D4 / SDA (GPIO 22 / GPIO 4)");
    Serial.println("  HW-605 SCL       -> XIAO D5 / SCL (GPIO 23 / GPIO 5)");
    Serial.println("\nAuto-retrying I2C scan every 3 seconds...");
    return;
  }

  setupSensors();
}

void setupSensors() {
  Wire.begin(activeSDA, activeSCL, 400000);

  if (isMAX30102) {
    Serial.println("\n[INIT] Initializing MAX30102 registers...");
    if (maxSensor.begin(Wire, I2C_SPEED_FAST)) {
      maxSensor.setup(60, 4, 2, 100, 411, 4096);
      maxSensor.setPulseAmplitudeRed(0x24);
      maxSensor.setPulseAmplitudeIR(0x24);
      Serial.println("✅ [OK] MAX30102 Pulse Oximeter Ready! Place finger on sensor.");
    } else {
      Serial.println("⚠️ [WARN] MAX30102 begin failed.");
    }
  }

  if (isMPU6050) {
    Serial.println("\n[INIT] Initializing MPU-6050 registers...");
    // Wake up MPU6050 (write 0x00 to PWR_MGMT_1 register 0x6B)
    Wire.beginTransmission(mpuAddress);
    Wire.write(0x6B);
    Wire.write(0x00);
    byte err = Wire.endTransmission();
    if (err == 0) {
      Serial.println("✅ [OK] MPU-6050 Gyro & Accelerometer Ready!");
    } else {
      Serial.println("⚠️ [WARN] MPU-6050 wakeup failed.");
    }
  }

  Serial.println("-------------------------------------------------------");
}

void loop() {
  if (!isMAX30102 && !isMPU6050) {
    delay(3000);
    scanI2CBus();
    if (isMAX30102 || isMPU6050) setupSensors();
    return;
  }

  if (isMAX30102) {
    readMAX30102Data();
  }

  if (isMPU6050) {
    readMPU6050Data();
  }

  delay(120);
}

// MAX30102 PPG Optical reading
void readMAX30102Data() {
  static unsigned long lastPrint = 0;
  long ir = maxSensor.getIR();
  long red = maxSensor.getRed();

  if (millis() - lastPrint >= 150) {
    lastPrint = millis();
    if (ir > 20000) {
      Serial.printf("❤️ [MAX30102 PPG] Finger Detected! IR: %6ld | RED: %6ld | Status: HEALTHY ACTIVE\n", ir, red);
    } else {
      Serial.printf("⚪ [MAX30102] Sensor Online (IR: %ld). Place finger on sensor to test PPG...\n", ir);
    }
  }
}

// MPU-6050 6-Axis IMU reading
void readMPU6050Data() {
  static unsigned long lastPrint = 0;

  Wire.beginTransmission(mpuAddress);
  Wire.write(0x3B); // Start reading at ACCEL_XOUT_H
  if (Wire.endTransmission(false) != 0) return;

  Wire.requestFrom((uint8_t)mpuAddress, (size_t)14, true);
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

    if (millis() - lastPrint >= 200) {
      lastPrint = millis();
      Serial.printf("🧭 [MPU-6050 IMU] Accel(m/s²): [%5.2f, %5.2f, %5.2f] | Gyro(°/s): [%6.1f, %6.1f, %6.1f] | Temp: %.1f°C\n",
                    ax, ay, az, gx, gy, gz, tempC);
    }
  }
}
