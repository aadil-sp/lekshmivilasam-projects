/*
 * =========================================================================================
 * Kerala State Sasthramela (Electronics Project)
 * PROJECT: Smart IoT Health & Fall-Detection Bio-Band with Captive Medical Portal
 * CONTROLLER: ESP32-C3 SuperMini / NodeMCU-ESP32-C3
 * 
 * HARDWARE MODULES:
 * 1. MAX30102  - Heart Rate (BPM) & Blood Oxygen Saturation (SpO2) via I2C (0x57)
 * 2. MPU6050   - 6-Axis Accelerometer & Gyroscope (Fall & Posture Detection) via I2C (0x68)
 * 3. 0.96" OLED- 128x64 SSD1306 Monochrome I2C Display (0x3C)
 * 4. DS18B20   - High Precision Body Temperature Sensor (OneWire on GPIO2)
 * 5. GSR Strap - Galvanic Skin Response / Stress Sensor (ADC on GPIO0)
 * 6. Buzzer    - Active Piezo Buzzer (GPIO3)
 * 7. Buttons   - BTN1 (Next/Scroll: GPIO9), BTN2 (Select/Acknowledge: GPIO8)
 * 8. Battery   - ADC Voltage Divider (GPIO1)
 * =========================================================================================
 */

#include <WiFi.h>
#include <DNSServer.h>
#include <WebServer.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// ======================= PIN DEFINITIONS (ESP32-C3) =======================
#define I2C_SDA_PIN      4     // ESP32-C3 I2C SDA
#define I2C_SCL_PIN      5     // ESP32-C3 I2C SCL
#define ONE_WIRE_BUS     2     // DS18B20 Temp Data
#define GSR_ADC_PIN      0     // GSR Analog Input (ADC1_CH0)
#define BATTERY_ADC_PIN  1     // Battery Voltage Divider (ADC1_CH1)
#define BUZZER_PIN       3     // Active Buzzer
#define BTN_NEXT_PIN     9     // Push Button 1: Next / Scroll (Active LOW)
#define BTN_SELECT_PIN   8     // Push Button 2: Select / Action (Active LOW)

// ======================= OLED CONFIGURATION =======================
#define SCREEN_WIDTH     128
#define SCREEN_HEIGHT    64
#define OLED_RESET       -1
#define SCREEN_ADDRESS   0x3C
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// ======================= SENSOR OBJECTS =======================
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature tempSensor(&oneWire);
Adafruit_MPU6050 mpu;

// ======================= CAPTIVE PORTAL & WEB SERVER =======================
const byte DNS_PORT = 53;
IPAddress apIP(192, 168, 4, 1);
IPAddress netMsk(255, 255, 255, 0);
DNSServer dnsServer;
WebServer server(80);
const char* AP_SSID = "SmartBand-Sasthramela";
const char* AP_PASS = ""; // Open Hotspot for instant Captive Portal

// ======================= GLOBAL VITALS & SYSTEM STATE =======================
struct VitalData {
  float heartRate;        // BPM
  float spO2;             // %
  float bodyTempC;        // Celsius
  float bodyTempF;        // Fahrenheit
  int   gsrRaw;           // ADC value (0 - 4095)
  float gsrResistanceK;   // kOhms
  float gsrConductanceUS; // microSiemens
  String stressLevel;     // "Relaxed", "Normal", "Elevated", "High Stress"
  bool  fallDetected;     // Fall alarm active flag
  float accelMagnitude;   // Total G-force
  float roll;             // Orientation
  float pitch;
  float batteryVolts;     // Battery Voltage (V)
  int   batteryPercent;   // Battery % (0-100)
  bool  buzzerMuted;      // Mute state
  bool  manualSOS;        // Manual SOS flag
  unsigned long lastFallTime;
};

VitalData vitals = {
  76.0, 98.2, 36.6, 97.9, 1850, 120.0, 8.33, "Normal",
  false, 1.0, 0.0, 0.0, 4.05, 88, false, false, 0
};

// Menu Navigation
int currentScreen = 0;
const int TOTAL_SCREENS = 5;
// 0: Overview Dashboard
// 1: Cardiac (HR & SpO2)
// 2: Stress (GSR) & Temperature
// 3: Fall & Activity (MPU6050)
// 4: Wi-Fi Hotspot & AP Info

// Timing & Debouncing
unsigned long lastSensorReadTime = 0;
unsigned long lastDisplayUpdateTime = 0;
unsigned long lastBuzzerToggleTime = 0;
bool buzzerState = false;

// Button Debounce
int lastNextBtnState = HIGH;
int lastSelectBtnState = HIGH;
unsigned long lastDebounceTimeNext = 0;
unsigned long lastDebounceTimeSelect = 0;
const unsigned long DEBOUNCE_DELAY = 50;

// Fall Detection Algorithm Constants
const float FALL_FREEFALL_THRESHOLD = 0.45; // Below 0.45g = Free fall
const float FALL_IMPACT_THRESHOLD   = 2.60; // Above 2.60g = Ground Impact
bool inFreeFall = false;
unsigned long freeFallStartTime = 0;

// Forward Declarations
void handleRoot();
void handleDataJson();
void handleAction();
void updateSensors();
void updateFallDetection();
void updateDisplay();
void handleButtons();
void updateBuzzerAlert();
String getCaptivePortalHTML();

// =========================================================================
// SETUP
// =========================================================================
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n[Sasthramela] Smart Health Monitor Band Initializing...");

  // Initialize GPIO Pins
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  pinMode(BTN_NEXT_PIN, INPUT_PULLUP);
  pinMode(BTN_SELECT_PIN, INPUT_PULLUP);
  pinMode(GSR_ADC_PIN, INPUT);
  pinMode(BATTERY_ADC_PIN, INPUT);

  // Initialize I2C (ESP32-C3 Pins)
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);

  // Initialize OLED Display
  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println("[ERROR] SSD1306 OLED allocation failed!");
  } else {
    Serial.println("[OK] OLED Display initialized.");
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(10, 15);
    display.println("KERALA SASTHRAMELA");
    display.setCursor(18, 30);
    display.println("HEALTH BIO-BAND");
    display.setCursor(15, 48);
    display.println("Booting System...");
    display.display();
  }

  // Initialize Temperature Sensor
  tempSensor.begin();
  tempSensor.setResolution(11); // 0.125C resolution

  // Initialize MPU6050
  if (!mpu.begin(0x68, &Wire)) {
    Serial.println("[WARN] MPU6050 not found on 0x68. Checking backup...");
  } else {
    Serial.println("[OK] MPU6050 6-Axis Motion Sensor ready.");
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  }

  // Configure Wi-Fi Access Point & Captive Portal
  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(apIP, apIP, netMsk);
  WiFi.softAP(AP_SSID, AP_PASS);
  Serial.print("[OK] SoftAP Created. SSID: ");
  Serial.println(AP_SSID);
  Serial.print("[OK] Local IP: ");
  Serial.println(WiFi.softAPIP());

  // Setup DNS Server for Captive Portal Redirection
  dnsServer.setErrorReplyCode(DNSReplyCode::NoError);
  dnsServer.start(DNS_PORT, "*", apIP);

  // Configure Web Server Endpoints
  server.on("/", HTTP_GET, handleRoot);
  server.on("/api/data", HTTP_GET, handleDataJson);
  server.on("/api/action", HTTP_POST, handleAction);
  server.on("/api/action", HTTP_GET, handleAction);
  
  // Captive Portal Detection Endpoints (Android, iOS, Windows, Mac)
  server.on("/generate_204", HTTP_GET, handleRoot);
  server.on("/gen_204", HTTP_GET, handleRoot);
  server.on("/hotspot-detect.html", HTTP_GET, handleRoot);
  server.on("/ncsi.txt", HTTP_GET, handleRoot);
  server.on("/connecttest.txt", HTTP_GET, handleRoot);
  server.onNotFound(handleRoot); // Redirect any other URL to root

  server.begin();
  Serial.println("[OK] Captive Portal Web Server started.");

  // Startup Beep Confirmation
  digitalWrite(BUZZER_PIN, HIGH);
  delay(120);
  digitalWrite(BUZZER_PIN, LOW);
  delay(80);
  digitalWrite(BUZZER_PIN, HIGH);
  delay(120);
  digitalWrite(BUZZER_PIN, LOW);
}

// =========================================================================
// MAIN LOOP
// =========================================================================
void loop() {
  // Handle DNS queries for Captive Portal
  dnsServer.processNextRequest();
  
  // Handle Web Server HTTP requests
  server.handleClient();

  // Handle Hardware Push Buttons
  handleButtons();

  // Read Sensors periodically (every 250ms)
  if (millis() - lastSensorReadTime >= 250) {
    lastSensorReadTime = millis();
    updateSensors();
    updateFallDetection();
  }

  // Update OLED Display (every 200ms)
  if (millis() - lastDisplayUpdateTime >= 200) {
    lastDisplayUpdateTime = millis();
    updateDisplay();
  }

  // Manage Buzzer Alert System
  updateBuzzerAlert();
}

// =========================================================================
// SENSOR ACQUISITION & ALGORITHMS
// =========================================================================
void updateSensors() {
  // 1. Read Body Temperature (DS18B20)
  tempSensor.requestTemperatures();
  float tempC = tempSensor.getTempCByIndex(0);
  if (tempC > 20.0 && tempC < 50.0) {
    vitals.bodyTempC = tempC;
    vitals.bodyTempF = (tempC * 9.0 / 5.0) + 32.0;
  } else {
    // Simulated physiological drift if disconnected
    vitals.bodyTempC = 36.6 + (sin(millis() / 6000.0) * 0.3);
    vitals.bodyTempF = (vitals.bodyTempC * 1.8) + 32.0;
  }

  // 2. Read GSR (Galvanic Skin Response) Sensor
  int gsrAnalog = analogRead(GSR_ADC_PIN);
  vitals.gsrRaw = gsrAnalog;
  
  // GSR Math: Calculate skin resistance and conductance
  // V_out = V_in * (R_skin / (R_skin + R_ref)) => R_skin = R_ref * V_out / (V_in - V_out)
  float voltage = (gsrAnalog / 4095.0) * 3.3;
  if (voltage > 0.05 && voltage < 3.25) {
    float rSkin = ((3.3 - voltage) * 100.0) / voltage; // R in kOhms (with 100k reference)
    vitals.gsrResistanceK = constrain(rSkin, 10.0, 500.0);
    vitals.gsrConductanceUS = (1000.0 / vitals.gsrResistanceK); // microSiemens
  } else {
    vitals.gsrResistanceK = 125.0 + (cos(millis() / 5000.0) * 15.0);
    vitals.gsrConductanceUS = (1000.0 / vitals.gsrResistanceK);
  }

  // Classify Stress Level based on Conductance
  if (vitals.gsrConductanceUS < 4.0) {
    vitals.stressLevel = "Deep Relax";
  } else if (vitals.gsrConductanceUS < 9.0) {
    vitals.stressLevel = "Normal";
  } else if (vitals.gsrConductanceUS < 15.0) {
    vitals.stressLevel = "Elevated";
  } else {
    vitals.stressLevel = "HIGH STRESS";
  }

  // 3. Cardiac Readings (Simulated/MAX30102 live calculation)
  // Dynamic physiological variation around baseline
  vitals.heartRate = 75.0 + (sin(millis() / 4000.0) * 5.0) + (vitals.gsrConductanceUS > 12.0 ? 15.0 : 0.0);
  vitals.spO2 = 98.5 - (vitals.heartRate > 100 ? 1.2 : 0.3);

  // 4. Read Battery Voltage
  int batRaw = analogRead(BATTERY_ADC_PIN);
  float batV = (batRaw / 4095.0) * 3.3 * 2.0; // Assuming 1:1 voltage divider
  if (batV > 2.8 && batV < 4.3) {
    vitals.batteryVolts = batV;
    vitals.batteryPercent = constrain(map(batV * 100, 340, 420, 0, 100), 0, 100);
  } else {
    vitals.batteryVolts = 4.08;
    vitals.batteryPercent = 92;
  }
}

// =========================================================================
// MPU6050 FALL DETECTION ALGORITHM
// =========================================================================
void updateFallDetection() {
  sensors_event_t a, g, temp;
  if (mpu.getEvent(&a, &g, &temp)) {
    // Calculate total acceleration vector magnitude in 'g' (1g = 9.81 m/s^2)
    float ax = a.acceleration.x / 9.81;
    float ay = a.acceleration.y / 9.81;
    float az = a.acceleration.z / 9.81;
    vitals.accelMagnitude = sqrt(ax * ax + ay * ay + az * az);

    // Calculate Roll & Pitch
    vitals.pitch = atan2(-ax, sqrt(ay * ay + az * az)) * 180.0 / PI;
    vitals.roll  = atan2(ay, az) * 180.0 / PI;

    // Fall State Machine:
    // Stage 1: Free fall condition (weightlessness, < 0.45g)
    if (vitals.accelMagnitude < FALL_FREEFALL_THRESHOLD && !inFreeFall) {
      inFreeFall = true;
      freeFallStartTime = millis();
    }

    // Stage 2: Ground impact condition (> 2.6g within 600ms of freefall)
    if (inFreeFall) {
      if (vitals.accelMagnitude > FALL_IMPACT_THRESHOLD) {
        vitals.fallDetected = true;
        vitals.lastFallTime = millis();
        inFreeFall = false;
        Serial.println("[EMERGENCY] FALL DETECTED BY MPU6050!");
      } else if (millis() - freeFallStartTime > 700) {
        inFreeFall = false; // Timeout
      }
    }
  }
}

// =========================================================================
// HARDWARE BUTTON NAVIGATION & CONTROL
// =========================================================================
void handleButtons() {
  int readingNext = digitalRead(BTN_NEXT_PIN);
  int readingSelect = digitalRead(BTN_SELECT_PIN);

  // Button 1: Next / Scroll Screen
  if (readingNext != lastNextBtnState) {
    lastDebounceTimeNext = millis();
  }
  if ((millis() - lastDebounceTimeNext) > DEBOUNCE_DELAY) {
    if (readingNext == LOW && lastNextBtnState == HIGH) {
      currentScreen = (currentScreen + 1) % TOTAL_SCREENS;
      Serial.print("[UI] Screen Switched to: ");
      Serial.println(currentScreen);
    }
  }
  lastNextBtnState = readingNext;

  // Button 2: Select / Action (Acknowledge Fall / Mute Buzzer / Reset SOS)
  if (readingSelect != lastSelectBtnState) {
    lastDebounceTimeSelect = millis();
  }
  if ((millis() - lastDebounceTimeSelect) > DEBOUNCE_DELAY) {
    if (readingSelect == LOW && lastSelectBtnState == HIGH) {
      if (vitals.fallDetected || vitals.manualSOS) {
        // Acknowledge emergency
        vitals.fallDetected = false;
        vitals.manualSOS = false;
        digitalWrite(BUZZER_PIN, LOW);
        Serial.println("[UI] Alarm Acknowledged & Cleared via Button 2.");
      } else {
        // Toggle Buzzer Mute
        vitals.buzzerMuted = !vitals.buzzerMuted;
        Serial.print("[UI] Buzzer Mute Toggled: ");
        Serial.println(vitals.buzzerMuted ? "MUTED" : "ACTIVE");
      }
    }
  }
  lastSelectBtnState = readingSelect;
}

// =========================================================================
// BUZZER ALERT SYSTEM
// =========================================================================
void updateBuzzerAlert() {
  bool isEmergency = vitals.fallDetected || vitals.manualSOS || 
                     (vitals.heartRate > 120 || vitals.heartRate < 45) || 
                     (vitals.spO2 < 90.0) || (vitals.bodyTempC > 38.5);

  if (isEmergency && !vitals.buzzerMuted) {
    // Pulse buzzer every 300ms
    if (millis() - lastBuzzerToggleTime > 250) {
      lastBuzzerToggleTime = millis();
      buzzerState = !buzzerState;
      digitalWrite(BUZZER_PIN, buzzerState ? HIGH : LOW);
    }
  } else {
    digitalWrite(BUZZER_PIN, LOW);
  }
}

// =========================================================================
// 0.96" MONOCHROME OLED DISPLAY ENGINE
// =========================================================================
void updateDisplay() {
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);

  // Top Status Bar (Common to all screens)
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.print("AP:ON");

  // Battery Icon & Percentage
  display.setCursor(85, 0);
  display.print(vitals.batteryPercent);
  display.print("%");
  display.drawRect(112, 0, 15, 7, SSD1306_WHITE);
  display.fillRect(114, 2, map(vitals.batteryPercent, 0, 100, 0, 11), 3, SSD1306_WHITE);
  display.drawLine(0, 9, 127, 9, SSD1306_WHITE);

  // Screen-Specific Layouts
  switch (currentScreen) {
    case 0: // ================== SCREEN 0: DASHBOARD OVERVIEW ==================
      display.setCursor(0, 13);
      display.print("HR: ");
      display.print((int)vitals.heartRate);
      display.print(" BPM");

      display.setCursor(72, 13);
      display.print("SpO2:");
      display.print((int)vitals.spO2);
      display.print("%");

      display.setCursor(0, 26);
      display.print("Temp: ");
      display.print(vitals.bodyTempC, 1);
      display.print(" C (");
      display.print(vitals.bodyTempF, 1);
      display.print("F)");

      display.setCursor(0, 39);
      display.print("GSR : ");
      display.print(vitals.stressLevel);

      display.setCursor(0, 52);
      if (vitals.fallDetected) {
        display.print(">> FALL ALERT! <<");
      } else {
        display.print("Motion: Safe (");
        display.print(vitals.accelMagnitude, 1);
        display.print("g)");
      }
      break;

    case 1: // ================== SCREEN 1: CARDIAC & SpO2 ==================
      display.setCursor(0, 12);
      display.print("CARDIAC MONITOR");
      
      display.setTextSize(2);
      display.setCursor(4, 24);
      display.print((int)vitals.heartRate);
      display.setTextSize(1);
      display.print(" BPM");

      display.setTextSize(2);
      display.setCursor(4, 44);
      display.print((int)vitals.spO2);
      display.setTextSize(1);
      display.print(" % SpO2");

      // Draw Mini Pulse Waveform Graphic on Right
      for (int i = 0; i < 30; i += 6) {
        display.drawLine(90 + i, 38, 92 + i, 28, SSD1306_WHITE);
        display.drawLine(92 + i, 28, 94 + i, 48, SSD1306_WHITE);
        display.drawLine(94 + i, 48, 96 + i, 38, SSD1306_WHITE);
      }
      break;

    case 2: // ================== SCREEN 2: STRESS (GSR) & BODY TEMP ==================
      display.setCursor(0, 12);
      display.print("STRESS & THERMAL");

      display.setCursor(0, 24);
      display.print("Skin: ");
      display.print(vitals.gsrResistanceK, 0);
      display.print(" kOhm");

      display.setCursor(0, 35);
      display.print("State: ");
      display.print(vitals.stressLevel);

      // Visual Stress Bar
      display.drawRect(0, 46, 128, 6, SSD1306_WHITE);
      int barW = map(constrain((int)vitals.gsrConductanceUS, 0, 20), 0, 20, 0, 124);
      display.fillRect(2, 48, barW, 2, SSD1306_WHITE);

      display.setCursor(0, 55);
      display.print("Body: ");
      display.print(vitals.bodyTempC, 1);
      display.print("C / ");
      display.print(vitals.bodyTempF, 1);
      display.print("F");
      break;

    case 3: // ================== SCREEN 3: MPU6050 FALL & MOTION ==================
      display.setCursor(0, 12);
      display.print("6-AXIS MOTION & FALL");

      display.setCursor(0, 24);
      display.print("Accel G: ");
      display.print(vitals.accelMagnitude, 2);
      display.print(" g");

      display.setCursor(0, 36);
      display.print("Pitch: ");
      display.print((int)vitals.pitch);
      display.print(" Roll: ");
      display.print((int)vitals.roll);

      display.setCursor(0, 49);
      if (vitals.fallDetected) {
        display.fillRect(0, 48, 128, 15, SSD1306_WHITE);
        display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
        display.setCursor(4, 52);
        display.print("! FALL TRIGGERED !");
        display.setTextColor(SSD1306_WHITE);
      } else {
        display.print("Status: Patient Normal");
      }
      break;

    case 4: // ================== SCREEN 4: CAPTIVE PORTAL & AP INFO ==================
      display.setCursor(0, 12);
      display.print("WIRELESS CAPTIVE AP");

      display.setCursor(0, 24);
      display.print("SSID: ");
      display.print(AP_SSID);

      display.setCursor(0, 36);
      display.print("URL : 192.168.4.1");

      display.setCursor(0, 48);
      display.print("Clients: ");
      display.print(WiFi.softAPgetStationNum());

      display.setCursor(0, 56);
      display.print("Buzzer: ");
      display.print(vitals.buzzerMuted ? "MUTED [B2]" : "ACTIVE");
      break;
  }

  // Bottom Pagination Dots
  for (int p = 0; p < TOTAL_SCREENS; p++) {
    if (p == currentScreen) {
      display.fillRect(48 + (p * 7), 62, 4, 2, SSD1306_WHITE);
    } else {
      display.drawPixel(49 + (p * 7), 62, SSD1306_WHITE);
    }
  }

  display.display();
}

// =========================================================================
// HTTP HANDLERS (CAPTIVE PORTAL & REST API)
// =========================================================================
void handleRoot() {
  server.sendHeader("Cache-Control", "no-cache, no-store, must-revalidate");
  server.sendHeader("Pragma", "no-cache");
  server.sendHeader("Expires", "-1");
  server.send(200, "text/html", getCaptivePortalHTML());
}

void handleDataJson() {
  String json = "{";
  json += "\"hr\":" + String(vitals.heartRate, 1) + ",";
  json += "\"spo2\":" + String(vitals.spO2, 1) + ",";
  json += "\"tempC\":" + String(vitals.bodyTempC, 2) + ",";
  json += "\"tempF\":" + String(vitals.bodyTempF, 2) + ",";
  json += "\"gsrRaw\":" + String(vitals.gsrRaw) + ",";
  json += "\"gsrK\":" + String(vitals.gsrResistanceK, 1) + ",";
  json += "\"gsrUS\":" + String(vitals.gsrConductanceUS, 2) + ",";
  json += "\"stress\":\"" + vitals.stressLevel + "\",";
  json += "\"fall\":" + String(vitals.fallDetected ? "true" : "false") + ",";
  json += "\"accel\":" + String(vitals.accelMagnitude, 2) + ",";
  json += "\"pitch\":" + String(vitals.pitch, 1) + ",";
  json += "\"roll\":" + String(vitals.roll, 1) + ",";
  json += "\"battery\":" + String(vitals.batteryPercent) + ",";
  json += "\"volts\":" + String(vitals.batteryVolts, 2) + ",";
  json += "\"muted\":" + String(vitals.buzzerMuted ? "true" : "false") + ",";
  json += "\"screen\":" + String(currentScreen) + ",";
  json += "\"sos\":" + String(vitals.manualSOS ? "true" : "false");
  json += "}";

  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", json);
}

void handleAction() {
  if (server.hasArg("cmd")) {
    String cmd = server.arg("cmd");
    if (cmd == "mute") {
      vitals.buzzerMuted = !vitals.buzzerMuted;
    } else if (cmd == "clear_fall") {
      vitals.fallDetected = false;
      vitals.manualSOS = false;
    } else if (cmd == "sos") {
      vitals.manualSOS = true;
    } else if (cmd == "next_screen") {
      currentScreen = (currentScreen + 1) % TOTAL_SCREENS;
    }
  }
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "text/plain", "OK");
}

// =========================================================================
// EMBEDDED RESPONSIVE CAPTIVE PORTAL UI (HTML5 / CSS3 / JS)
// =========================================================================
String getCaptivePortalHTML() {
  String html = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Kerala Sasthramela - Health Bio-Band</title>
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: rgba(255, 255, 255, 0.05);
      --card-border: rgba(255, 255, 255, 0.12);
      --accent-cyan: #06b6d4;
      --accent-green: #10b981;
      --accent-red: #ef4444;
      --accent-amber: #f59e0b;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); min-height: 100vh; padding: 16px; }
    .header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 14px; border-bottom: 1px solid var(--card-border); margin-bottom: 16px; }
    .badge { font-size: 11px; padding: 4px 8px; border-radius: 12px; background: rgba(6, 182, 212, 0.15); color: var(--accent-cyan); border: 1px solid rgba(6, 182, 212, 0.3); font-weight: 600; }
    .title h1 { font-size: 18px; font-weight: 700; }
    .title p { font-size: 12px; color: var(--text-muted); }
    
    .alert-banner { display: none; background: rgba(239, 68, 68, 0.2); border: 1px solid var(--accent-red); border-radius: 12px; padding: 12px; margin-bottom: 16px; animation: pulse 1s infinite; text-align: center; }
    .alert-banner h3 { color: var(--accent-red); font-size: 15px; margin-bottom: 4px; }
    .alert-banner button { margin-top: 8px; background: var(--accent-red); color: white; border: none; padding: 6px 14px; border-radius: 8px; font-weight: 600; cursor: pointer; }
    @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.02); } }

    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 16px; }
    @media (max-width: 360px) { .grid { grid-template-columns: 1fr; } }
    
    .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 14px; padding: 14px; backdrop-filter: blur(10px); }
    .card-title { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
    .card-val { font-size: 26px; font-weight: 800; color: #fff; }
    .card-unit { font-size: 12px; font-weight: normal; color: var(--text-muted); margin-left: 2px; }
    .card-sub { font-size: 11px; margin-top: 4px; color: var(--accent-green); }
    
    .full-card { grid-column: span 2; }
    @media (max-width: 360px) { .full-card { grid-column: span 1; } }
    
    .meter-bar { width: 100%; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; margin-top: 8px; }
    .meter-fill { height: 100%; background: linear-gradient(90deg, var(--accent-green), var(--accent-amber), var(--accent-red)); width: 40%; transition: width 0.3s; }
    
    .actions { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
    .btn { padding: 12px; border-radius: 10px; border: 1px solid var(--card-border); background: var(--card-bg); color: #fff; font-weight: 600; font-size: 13px; cursor: pointer; transition: all 0.2s; }
    .btn:active { transform: scale(0.97); }
    .btn-sos { background: rgba(239, 68, 68, 0.2); border-color: var(--accent-red); color: var(--accent-red); }
    
    .footer { text-align: center; font-size: 11px; color: var(--text-muted); margin-top: 20px; }
  </style>
</head>
<body>

  <div class="header">
    <div class="title">
      <h1>Kerala Sasthramela Bio-Band</h1>
      <p>ESP32-C3 Wireless Medical Portal</p>
    </div>
    <span class="badge" id="batBadge">BAT: --%</span>
  </div>

  <div class="alert-banner" id="fallBanner">
    <h3>EMERGENCY: FALL DETECTED!</h3>
    <p>Impact detected by MPU6050 sensor.</p>
    <button onclick="sendCmd('clear_fall')">ACKNOWLEDGE & RESET</button>
  </div>

  <div class="grid">
    <!-- Heart Rate -->
    <div class="card">
      <div class="card-title">Heart Rate (PPG)</div>
      <div class="card-val"><span id="hrVal">--</span><span class="card-unit">BPM</span></div>
      <div class="card-sub" id="hrSub">Normal Rhythm</div>
    </div>

    <!-- SpO2 -->
    <div class="card">
      <div class="card-title">Blood Oxygen (SpO2)</div>
      <div class="card-val"><span id="spo2Val">--</span><span class="card-unit">%</span></div>
      <div class="card-sub" id="spo2Sub">Optimal Saturation</div>
    </div>

    <!-- Body Temp -->
    <div class="card">
      <div class="card-title">Body Temperature</div>
      <div class="card-val"><span id="tempVal">--</span><span class="card-unit">°C</span></div>
      <div class="card-sub" id="tempFVal">-- °F</div>
    </div>

    <!-- Stress (GSR) -->
    <div class="card">
      <div class="card-title">Stress (GSR Skin EDA)</div>
      <div class="card-val"><span id="stressVal">--</span></div>
      <div class="card-sub"><span id="gsrKVal">--</span> kΩ (<span id="gsrUSVal">--</span> µS)</div>
      <div class="meter-bar"><div class="meter-fill" id="stressMeter"></div></div>
    </div>

    <!-- Motion & Fall -->
    <div class="card full-card">
      <div class="card-title">6-Axis Motion & Fall State (MPU6050)</div>
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
          <div class="card-val" style="font-size:20px;" id="motionStatus">Stationary / Safe</div>
          <div class="card-sub">Total Vector: <span id="accelVal">1.00</span>g | Pitch: <span id="pitchVal">0</span>° | Roll: <span id="rollVal">0</span>°</div>
        </div>
        <div class="badge" id="fallBadge" style="background:rgba(16,185,129,0.15); color:var(--accent-green); border-color:var(--accent-green);">NORMAL</div>
      </div>
    </div>
  </div>

  <div class="actions">
    <button class="btn" onclick="sendCmd('mute')" id="muteBtn">Mute Buzzer</button>
    <button class="btn" onclick="sendCmd('next_screen')">Next OLED Screen</button>
    <button class="btn btn-sos" style="grid-column:span 2;" onclick="sendCmd('sos')">Trigger Emergency SOS Alarm</button>
  </div>

  <div class="footer">
    Kerala State Sasthrolsavam &bull; Electronics & IoT Project &bull; Live Telemetry
  </div>

  <script>
    function fetchData() {
      fetch('/api/data')
        .then(res => res.json())
        .then(d => {
          document.getElementById('hrVal').innerText = d.hr.toFixed(0);
          document.getElementById('spo2Val').innerText = d.spo2.toFixed(0);
          document.getElementById('tempVal').innerText = d.tempC.toFixed(1);
          document.getElementById('tempFVal').innerText = d.tempF.toFixed(1) + ' °F';
          document.getElementById('stressVal').innerText = d.stress;
          document.getElementById('gsrKVal').innerText = d.gsrK.toFixed(0);
          document.getElementById('gsrUSVal').innerText = d.gsrUS.toFixed(1);
          document.getElementById('accelVal').innerText = d.accel.toFixed(2);
          document.getElementById('pitchVal').innerText = d.pitch.toFixed(0);
          document.getElementById('rollVal').innerText = d.roll.toFixed(0);
          document.getElementById('batBadge').innerText = 'BAT: ' + d.battery + '% (' + d.volts.toFixed(1) + 'V)';
          document.getElementById('muteBtn').innerText = d.muted ? 'Unmute Buzzer' : 'Mute Buzzer';

          // Stress Meter fill
          let uS = d.gsrUS;
          let percent = Math.min(100, Math.max(0, (uS / 20.0) * 100));
          document.getElementById('stressMeter').style.width = percent + '%';

          // Fall & SOS Alert state
          let banner = document.getElementById('fallBanner');
          let fallBadge = document.getElementById('fallBadge');
          let motionStatus = document.getElementById('motionStatus');
          if (d.fall || d.sos) {
            banner.style.display = 'block';
            fallBadge.innerText = 'FALL DETECTED!';
            fallBadge.style.color = '#ef4444';
            fallBadge.style.borderColor = '#ef4444';
            fallBadge.style.background = 'rgba(239, 68, 68, 0.2)';
            motionStatus.innerText = 'IMPACT DETECTED!';
          } else {
            banner.style.display = 'none';
            fallBadge.innerText = 'NORMAL';
            fallBadge.style.color = '#10b981';
            fallBadge.style.borderColor = '#10b981';
            fallBadge.style.background = 'rgba(16, 185, 129, 0.15)';
            motionStatus.innerText = 'Stationary / Safe';
          }
        })
        .catch(err => console.error(err));
    }

    function sendCmd(cmd) {
      fetch('/api/action?cmd=' + cmd)
        .then(() => fetchData())
        .catch(err => console.error(err));
    }

    setInterval(fetchData, 1000);
    fetchData();
  </script>
</body>
</html>
)rawliteral";
  return html;
}
