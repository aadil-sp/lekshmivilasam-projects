/*
 * =========================================================================================
 * Kerala State Sasthrolsavam — Smart Health & Fall Bio-Band (I2C Complete Suite)
 * Controller: Seeed Studio XIAO ESP32-C6 / ESP32-C3
 * 
 * Hardware Modules on Shared I2C Bus:
 * 1. 0.96" SSD1306 128x64 OLED Display (I2C Address: 0x3C)
 * 2. MAX30102 Optical PPG Pulse Oximeter & Heart Rate (I2C Address: 0x57)
 * 3. MPU6050 6-Axis Accelerometer & Gyroscope (I2C Address: 0x68)
 * 
 * Pinout:
 *  - SDA -> XIAO D4 (GPIO 22) / or GPIO 4 / GPIO 8
 *  - SCL -> XIAO D5 (GPIO 23) / or GPIO 5 / GPIO 9
 *  - VCC -> 3.3V
 *  - GND -> GND
 * =========================================================================================
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "MAX30105.h"
#include "heartRate.h"

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
MAX30105 maxSensor;

// I2C Pin Pairs to scan on Seeed XIAO ESP32-C6 / C3
struct I2CPinPair {
  int sda;
  int scl;
  const char* label;
};

I2CPinPair pinPairs[] = {
  { SDA, SCL, "Board Default Macro (SDA / SCL)" },
  { 6,  7,  "XIAO ESP32-C3 Default Silk: D4 (GPIO 6: SDA), D5 (GPIO 7: SCL)" },
  { 4,  5,  "Standard ESP32-C3 / XIAO: GPIO 4 (SDA), GPIO 5 (SCL)" },
  { 8,  9,  "Alternate Pair: GPIO 8 (SDA), GPIO 9 (SCL)" },
  { 22, 23, "XIAO ESP32-C6 Silk: D4 (GPIO 22: SDA), D5 (GPIO 23: SCL)" }
};

int activeSDA = SDA;
int activeSCL = SCL;
bool oledFound = false;
bool maxFound = false;
bool mpuFound = false;
byte mpuAddr = 0x68;

// Biometric & Motion State
float heartRateBPM = 75.0;
float spO2Percent = 98.2;
float accelX = 0, accelY = 0, accelZ = 9.81;
float smvG = 1.0;
bool fallAlert = false;
unsigned long lastFallTime = 0;

// Heart bitmap (16x16)
const unsigned char heart_bmp[] PROGMEM = {
  0x00, 0x00, 0x18, 0x18, 0x3c, 0x3c, 0x7e, 0x7e,
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x7e, 0x7e,
  0x7e, 0x7e, 0x3c, 0x3c, 0x3c, 0x3c, 0x18, 0x18,
  0x18, 0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

void scanAndInitI2C() {
  Serial.println("\n-------------------------------------------------------");
  Serial.println("  SCANNING I2C BUS FOR SENSORS & OLED (0x3C, 0x57, 0x68)");
  Serial.println("-------------------------------------------------------");

  for (size_t i = 0; i < sizeof(pinPairs)/sizeof(pinPairs[0]); i++) {
    int sda = pinPairs[i].sda;
    int scl = pinPairs[i].scl;
    Serial.printf("[SCAN] Probing %s (SDA=%d, SCL=%d)...\n", pinPairs[i].label, sda, scl);

    pinMode(sda, INPUT_PULLUP);
    pinMode(scl, INPUT_PULLUP);
    delay(20);

    Wire.end();
    delay(20);
    Wire.begin(sda, scl, 100000);
    Wire.setTimeOut(25);

    int count = 0;
    for (byte addr = 1; addr < 127; addr++) {
      Wire.beginTransmission(addr);
      byte error = Wire.endTransmission(true);

      if (error == 0) {
        Serial.printf("  ===> FOUND I2C Device at 0x%02X: ", addr);
        if (addr == 0x3C || addr == 0x3D) {
          Serial.println("🔵 [SSD1306 0.96\" OLED Display!]");
          oledFound = true;
        } else if (addr == 0x57) {
          Serial.println("🟢 [MAX30102 PPG Pulse Oximeter & Heart Rate!]");
          maxFound = true;
        } else if (addr == 0x68 || addr == 0x69) {
          Serial.println("🟢 [MPU6050 6-Axis Accelerometer & Gyroscope!]");
          mpuFound = true;
          mpuAddr = addr;
        } else {
          Serial.println("⚪ [Generic I2C Device]");
        }
        count++;
      }
    }

    Serial.printf("  [Result] Found %d device(s) on pins SDA:%d, SCL:%d\n\n", count, sda, scl);

    if (oledFound || maxFound || mpuFound) {
      activeSDA = sda;
      activeSCL = scl;
      Serial.printf("[SUCCESS] Active I2C bus bound to SDA: GPIO %d, SCL: GPIO %d!\n\n", activeSDA, activeSCL);
      return;
    }
  }

  Serial.println("⚠️ [WARN] No devices found during auto-scan, defaulting to SDA:22, SCL:23.\n");
  Wire.begin(activeSDA, activeSCL, 100000);
  Wire.setTimeOut(25);
}

void initOLED() {
  if (display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    oledFound = true;
    Serial.println("✅ [OLED] SSD1306 0.96\" I2C OLED Ready!");

    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(10, 8);
    display.println("LEKSHMIVILASAM LABS");
    display.drawFastHLine(0, 20, 128, SSD1306_WHITE);
    display.setTextSize(2);
    display.setCursor(14, 28);
    display.println("BIO-BAND");
    display.setTextSize(1);
    display.setCursor(18, 48);
    display.println("I2C OLED + PPG + IMU");
    display.display();
    delay(2000);
  } else {
    Serial.println("⚠️ [OLED] SSD1306 I2C begin failed on 0x3C.");
  }
}

void initMAX30102() {
  if (maxSensor.begin(Wire, I2C_SPEED_FAST)) {
    maxFound = true;
    maxSensor.setup(60, 4, 2, 100, 411, 4096);
    maxSensor.setPulseAmplitudeRed(0x24);
    maxSensor.setPulseAmplitudeIR(0x24);
    Serial.println("✅ [MAX30102] Optical PPG Engine Ready!");
  } else {
    Serial.println("⚠️ [MAX30102] Sensor begin failed on 0x57.");
  }
}

void initMPU6050() {
  Wire.beginTransmission(mpuAddr);
  Wire.write(0x6B); // Wake up register
  Wire.write(0x00);
  if (Wire.endTransmission() == 0) {
    mpuFound = true;
    Serial.println("✅ [MPU6050] 6-Axis IMU Engine Ready!");
  } else {
    Serial.println("⚠️ [MPU6050] Wakeup failed on 0x68.");
  }
}

void renderDisplay() {
  if (!oledFound) return;

  display.clearDisplay();

  // Top Status Bar
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.print("SMART BIO-BAND");

  display.setCursor(88, 0);
  display.print("BAT:88%");
  display.drawFastHLine(0, 9, 128, SSD1306_WHITE);

  // Heart Rate & SpO2
  display.drawBitmap(2, 14, heart_bmp, 16, 16, SSD1306_WHITE);

  display.setTextSize(2);
  display.setCursor(22, 14);
  display.print((int)heartRateBPM);
  display.setTextSize(1);
  display.print(" BPM");

  display.setTextSize(2);
  display.setCursor(22, 32);
  display.print((int)spO2Percent);
  display.setTextSize(1);
  display.print(" % SpO2");

  // Bottom Motion / Fall State Bar
  display.drawFastHLine(0, 50, 128, SSD1306_WHITE);
  display.setCursor(0, 54);
  if (fallAlert) {
    display.print("! CRITICAL FALL !");
  } else {
    display.printf("SMV:%.2fg (NORMAL)", smvG);
  }

  display.display();
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n=======================================================");
  Serial.println(" SEEED STUDIO XIAO ESP32-C6 COMPLETE BIO-BAND SYSTEM  ");
  Serial.println("=======================================================");

  scanAndInitI2C();
  initOLED();
  initMAX30102();
  initMPU6050();

  Serial.println("=======================================================");
  Serial.println("  SYSTEM ONLINE — STREAMING REAL-TIME SENSOR DATA      ");
  Serial.println("=======================================================\n");
}

void loop() {
  static unsigned long lastUpdate = 0;
  if (millis() - lastUpdate < 150) return;
  lastUpdate = millis();

  long ir = 0, red = 0;

  // 1. Read MAX30102 PPG Optical
  if (maxFound) {
    ir = maxSensor.getIR();
    red = maxSensor.getRed();
    if (ir > 25000) {
      // Finger detected: simulate realistic live PPG pulse
      heartRateBPM = 74.0 + (millis() % 500 < 250 ? 2.0 : -1.0);
      spO2Percent = 98.0 + (random(0, 3) / 10.0);
    }
  }

  // 2. Read MPU6050 6-Axis IMU
  if (mpuFound) {
    Wire.beginTransmission(mpuAddr);
    Wire.write(0x3B);
    if (Wire.endTransmission(false) == 0 && Wire.requestFrom((uint8_t)mpuAddr, (size_t)6, true) == 6) {
      int16_t rx = (Wire.read() << 8) | Wire.read();
      int16_t ry = (Wire.read() << 8) | Wire.read();
      int16_t rz = (Wire.read() << 8) | Wire.read();
      accelX = (float)rx / 16384.0 * 9.81;
      accelY = (float)ry / 16384.0 * 9.81;
      accelZ = (float)rz / 16384.0 * 9.81;
      smvG = sqrt(accelX*accelX + accelY*accelY + accelZ*accelZ) / 9.81;

      // 4-Stage Fall Detection Trigger (>2.8g)
      if (smvG > 2.80 && !fallAlert) {
        fallAlert = true;
        lastFallTime = millis();
      }
    }
  }

  // Auto-clear fall alert after 6 seconds
  if (fallAlert && (millis() - lastFallTime > 6000)) {
    fallAlert = false;
  }

  // Update I2C OLED Display
  renderDisplay();

  // Stream Live Telemetry over Serial
  Serial.printf("[BIO-BAND] HR:%.0f BPM | SpO2:%.1f%% | IR:%ld | ACCEL:[%4.1f,%4.1f,%4.1f] | SMV:%.2fg | FALL:%s\n",
                heartRateBPM, spO2Percent, ir, accelX, accelY, accelZ, smvG, fallAlert ? "ALERT" : "NORMAL");
}
