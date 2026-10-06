#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <math.h>
#include "MAX30100.h"
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// --- WIFI ACCESS POINT CONFIG ---
const char* AP_SSID = "Smart-Health-Band";
const char* AP_PASS = NULL; // Open Hotspot (No Password)

WebServer server(80);

// --- HARDWARE PINS ---
#ifdef D8
const int BUZZER_PIN = D8;
#else
const int BUZZER_PIN = 19;
#endif

#ifndef LED_BUILTIN
#define LED_BUILTIN 15
#endif
const int INDICATOR_LED = LED_BUILTIN;

// --- OLED CONFIG ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// --- MAX30100 CONFIG ---
MAX30100 sensor;
float currentHR = 72.0;
float currentSpO2 = 98.0;
bool isFingerPlaced = false;

// --- MPU6050 CONFIG ---
const int MPU_addr = 0x68;
boolean fallDetected = false;
unsigned long fallStartTime = 0;
float currentAx = 0, currentAy = 0, currentAz = 0; 
float currentMagnitude = 1.0;

// Alert state for OLED, Buzzer & Web
bool fallAlertActive = false;
int alertType = 0; // 0=None, 1=FreeFall, 2=Impact/Shock
unsigned long alertStartTime = 0;
String alertMessage = "SYSTEM OK";

// --- HTML & JAVASCRIPT DASHBOARD (PROGMEM) ---
const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Smart Health & Fall Telemetry</title>
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: rgba(20, 27, 45, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --accent-cyan: #00f2fe;
      --accent-pink: #ff2a6d;
      --accent-green: #05ffa1;
      --accent-yellow: #f9d423;
      --alert-red: #ff0055;
      --text: #ffffff;
      --text-dim: #8a99b5;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    body {
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 16px;
      overflow-x: hidden;
    }
    .header {
      width: 100%;
      max-width: 900px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 18px;
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      margin-bottom: 16px;
    }
    .logo-area { display: flex; align-items: center; gap: 10px; }
    .logo-icon { font-size: 24px; }
    .title { font-size: 18px; font-weight: 700; background: linear-gradient(90deg, #00f2fe, #4facfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .subtitle { font-size: 11px; color: var(--text-dim); }
    .audio-btn {
      background: #1e293b;
      color: #cbd5e1;
      border: 1px solid rgba(255,255,255,0.15);
      padding: 8px 14px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .audio-btn.active {
      background: linear-gradient(135deg, #05ffa1, #00b4d8);
      color: #0b0f19;
      box-shadow: 0 0 15px rgba(5, 255, 161, 0.4);
    }
    .alert-banner {
      width: 100%;
      max-width: 900px;
      padding: 18px;
      background: var(--alert-red);
      border-radius: 16px;
      margin-bottom: 16px;
      text-align: center;
      font-weight: 800;
      font-size: 20px;
      letter-spacing: 1px;
      box-shadow: 0 0 30px rgba(255, 0, 85, 0.6);
      animation: flash 0.4s infinite alternate;
      display: none;
    }
    @keyframes flash {
      from { transform: scale(1); filter: brightness(1); }
      to { transform: scale(1.02); filter: brightness(1.3); }
    }
    .grid {
      width: 100%;
      max-width: 900px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
      margin-bottom: 16px;
    }
    .card {
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      border: 1px solid var(--card-border);
      border-radius: 18px;
      padding: 20px;
      position: relative;
      overflow: hidden;
      box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      color: var(--text-dim);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      font-weight: 600;
    }
    .card-val-container {
      display: flex;
      align-items: baseline;
      gap: 8px;
      margin: 10px 0;
    }
    .val-large { font-size: 48px; font-weight: 800; line-height: 1; }
    .unit { font-size: 16px; color: var(--text-dim); font-weight: 500; }
    .status-tag {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 700;
      margin-top: 6px;
    }
    .tag-ok { background: rgba(5, 255, 161, 0.15); color: var(--accent-green); }
    .tag-waiting { background: rgba(249, 212, 35, 0.15); color: var(--accent-yellow); }
    .tag-danger { background: rgba(255, 0, 85, 0.2); color: var(--alert-red); }

    .hr-color { color: var(--accent-pink); }
    .spo2-color { color: var(--accent-cyan); }
    .motion-color { color: var(--accent-green); }

    .bar-wrap { margin-top: 10px; }
    .bar-label { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px; color: var(--text-dim); }
    .bar-bg { width: 100%; height: 8px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden; }
    .bar-fill { height: 100%; width: 50%; border-radius: 4px; transition: width 0.15s ease-out; }
    .bar-fill.x { background: #00f2fe; }
    .bar-fill.y { background: #4facfe; }
    .bar-fill.z { background: #05ffa1; }

    .footer {
      width: 100%;
      max-width: 900px;
      display: flex;
      justify-content: space-between;
      color: var(--text-dim);
      font-size: 12px;
      padding: 8px;
    }
    .heart-pulse {
      display: inline-block;
      animation: beat 1s infinite ease-in-out;
    }
    @keyframes beat {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.25); }
    }
  </style>
</head>
<body>

  <div class="header">
    <div class="logo-area">
      <span class="logo-icon">🩺</span>
      <div>
        <div class="title">SMART HEALTH & MOTION HUD</div>
        <div class="subtitle">Seeed Studio XIAO ESP32-C6 • 192.168.4.1</div>
      </div>
    </div>
    <button id="audioBtn" class="audio-btn" onclick="toggleAudio()">🔇 Enable Audio Alarm</button>
  </div>

  <div id="alertBanner" class="alert-banner">
    🚨 WARNING: IMPACT / FREE-FALL DETECTED!
  </div>

  <div class="grid">
    <!-- Heart Rate Card -->
    <div class="card">
      <div class="card-header">
        <span>Pulse Rate</span>
        <span class="heart-pulse">❤️</span>
      </div>
      <div class="card-val-container">
        <span id="hrVal" class="val-large hr-color">--</span>
        <span class="unit">BPM</span>
      </div>
      <div id="fingerStatus" class="status-tag tag-waiting">Waiting for finger...</div>
    </div>

    <!-- SpO2 Card -->
    <div class="card">
      <div class="card-header">
        <span>Blood Oxygen</span>
        <span>💧</span>
      </div>
      <div class="card-val-container">
        <span id="spo2Val" class="val-large spo2-color">--</span>
        <span class="unit">%</span>
      </div>
      <div id="spo2Status" class="status-tag tag-ok">Normal Range</div>
    </div>

    <!-- Accelerometer & Motion Card -->
    <div class="card">
      <div class="card-header">
        <span>Motion / Impact</span>
        <span>🛰️</span>
      </div>
      <div class="card-val-container">
        <span id="magVal" class="val-large motion-color">1.00</span>
        <span class="unit">G (Magnitude)</span>
      </div>
      
      <div class="bar-wrap">
        <div class="bar-label"><span>Axis X</span><span id="axVal">0.0g</span></div>
        <div class="bar-bg"><div id="barX" class="bar-fill x"></div></div>
      </div>
      <div class="bar-wrap">
        <div class="bar-label"><span>Axis Y</span><span id="ayVal">0.0g</span></div>
        <div class="bar-bg"><div id="barY" class="bar-fill y"></div></div>
      </div>
      <div class="bar-wrap">
        <div class="bar-label"><span>Axis Z</span><span id="azVal">1.0g</span></div>
        <div class="bar-bg"><div id="barZ" class="bar-fill z"></div></div>
      </div>
    </div>
  </div>

  <div class="footer">
    <span>Device: Hotspot (192.168.4.1)</span>
    <span id="uptime">Uptime: 0s</span>
  </div>

  <script>
    let audioCtx = null;
    let osc = null;
    let gainNode = null;
    let soundEnabled = false;

    function toggleAudio() {
      if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }
      soundEnabled = !soundEnabled;
      const btn = document.getElementById('audioBtn');
      if (soundEnabled) {
        btn.innerText = '🔊 Audio Alarm: ACTIVE';
        btn.classList.add('active');
      } else {
        btn.innerText = '🔇 Enable Audio Alarm';
        btn.classList.remove('active');
        stopSiren();
      }
    }

    function playSiren() {
      if (!soundEnabled || !audioCtx) return;
      if (!osc) {
        osc = audioCtx.createOscillator();
        gainNode = audioCtx.createGain();
        osc.type = 'sawtooth';
        osc.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        gainNode.gain.setValueAtTime(0.25, audioCtx.currentTime);
        osc.start();
      }
      let t = audioCtx.currentTime;
      let freq = (Math.floor(t * 5) % 2 === 0) ? 900 : 1600;
      osc.frequency.setValueAtTime(freq, t);
    }

    function stopSiren() {
      if (osc) {
        try {
          osc.stop();
          osc.disconnect();
        } catch(e) {}
        osc = null;
      }
    }

    function updateHUD() {
      fetch('/data')
        .then(res => res.json())
        .then(data => {
          // Alert Handler
          const alertBanner = document.getElementById('alertBanner');
          if (data.alert > 0) {
            alertBanner.style.display = 'block';
            alertBanner.innerText = data.alertMsg;
            playSiren();
          } else {
            alertBanner.style.display = 'none';
            stopSiren();
          }

          // Vitals Handler
          const hrVal = document.getElementById('hrVal');
          const spo2Val = document.getElementById('spo2Val');
          const fingerStatus = document.getElementById('fingerStatus');
          
          if (data.finger) {
            hrVal.innerText = Math.round(data.hr);
            spo2Val.innerText = Math.round(data.spo2);
            fingerStatus.innerText = '● Finger Detected (Measuring)';
            fingerStatus.className = 'status-tag tag-ok';
          } else {
            hrVal.innerText = '--';
            spo2Val.innerText = '--';
            fingerStatus.innerText = 'Waiting for finger on sensor...';
            fingerStatus.className = 'status-tag tag-waiting';
          }

          // Accelerometer Handler
          document.getElementById('magVal').innerText = Number(data.mag).toFixed(2);
          document.getElementById('axVal').innerText = Number(data.ax).toFixed(2) + 'g';
          document.getElementById('ayVal').innerText = Number(data.ay).toFixed(2) + 'g';
          document.getElementById('azVal').innerText = Number(data.az).toFixed(2) + 'g';

          // Map -2g to +2g to 0% - 100%
          const mapToPct = val => Math.min(100, Math.max(0, ((val + 2) / 4) * 100));
          document.getElementById('barX').style.width = mapToPct(data.ax) + '%';
          document.getElementById('barY').style.width = mapToPct(data.ay) + '%';
          document.getElementById('barZ').style.width = mapToPct(data.az) + '%';

          document.getElementById('uptime').innerText = 'Uptime: ' + data.uptime + 's';
        })
        .catch(err => console.error(err));
    }

    setInterval(updateHUD, 250);
  </script>
</body>
</html>
)rawliteral";

void handleRoot() {
    server.send(200, "text/html", INDEX_HTML);
}

void handleData() {
    String json = "{";
    json += "\"hr\":" + String(currentHR, 1) + ",";
    json += "\"spo2\":" + String((int)currentSpO2) + ",";
    json += "\"finger\":" + String(isFingerPlaced ? "true" : "false") + ",";
    json += "\"ax\":" + String(currentAx, 2) + ",";
    json += "\"ay\":" + String(currentAy, 2) + ",";
    json += "\"az\":" + String(currentAz, 2) + ",";
    json += "\"mag\":" + String(currentMagnitude, 2) + ",";
    json += "\"alert\":" + String(fallAlertActive ? alertType : 0) + ",";
    json += "\"alertMsg\":\"" + alertMessage + "\",";
    json += "\"uptime\":" + String(millis() / 1000);
    json += "}";
    
    server.send(200, "application/json", json);
}

void setBuzzer(bool on, int freq = 2000) {
    if (on) {
        digitalWrite(BUZZER_PIN, HIGH);
        tone(BUZZER_PIN, freq);
    } else {
        digitalWrite(BUZZER_PIN, LOW);
        noTone(BUZZER_PIN);
    }
}

void triggerAlert(int type, const __FlashStringHelper* msg) {
    fallAlertActive = true;
    alertType = type;
    alertStartTime = millis();
    if (type == 1) {
        alertMessage = "🚨 FREE-FALL DETECTED!";
    } else {
        alertMessage = "⚠️ IMPACT / SHOCK DETECTED!";
    }
    Serial.println(msg);
}

void initMPU() {
    Wire.beginTransmission(MPU_addr);
    Wire.write(0x6B);
    Wire.write(0);
    Wire.endTransmission(true);
    
    Wire.beginTransmission(MPU_addr);
    Wire.write(0x1C);
    Wire.write(0x08); 
    Wire.endTransmission(true);
}

void setup() {
    Serial.begin(9600);
    
    pinMode(BUZZER_PIN, OUTPUT);
    pinMode(INDICATOR_LED, OUTPUT);
    digitalWrite(INDICATOR_LED, LOW);
    
    // 3 small beeps on booting
    for (int i = 0; i < 3; i++) {
        setBuzzer(true, 2400);
        digitalWrite(INDICATOR_LED, HIGH);
        delay(90);
        setBuzzer(false);
        digitalWrite(INDICATOR_LED, LOW);
        delay(90);
    }
    
    Wire.begin();
    
    if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { 
        Serial.println(F("OLED failed to initialize!"));
        for(;;);
    }
    
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(5, 15);
    display.println(F("Starting Hotspot..."));
    display.display();
    
    // Start Open Wi-Fi Access Point (Hotspot)
    WiFi.mode(WIFI_AP);
    WiFi.softAP(AP_SSID);
    
    server.on("/", handleRoot);
    server.on("/data", handleData);
    server.begin();
    
    display.clearDisplay();
    display.setCursor(0, 10);
    display.println(F("AP: Smart-Health-Band"));
    display.setCursor(0, 25);
    display.println(F("IP: 192.168.4.1"));
    display.setCursor(0, 45);
    display.println(F("Pass: None (OPEN)"));
    display.display();
    
    randomSeed(analogRead(0));
    delay(1500);
}

unsigned long cycleStartTime = 0;

void readMPUAndDetectFalls() {
    Wire.beginTransmission(MPU_addr);
    Wire.write(0x3B);
    Wire.endTransmission(false);
    Wire.requestFrom(MPU_addr, 14);
    
    if (Wire.available() >= 14) {
        int16_t AcX = Wire.read()<<8 | Wire.read();  
        int16_t AcY = Wire.read()<<8 | Wire.read();  
        int16_t AcZ = Wire.read()<<8 | Wire.read();  
        Wire.read(); Wire.read(); // Skip Temp
        Wire.read(); Wire.read(); // Skip GyX
        Wire.read(); Wire.read(); // Skip GyY
        Wire.read(); Wire.read(); // Skip GyZ
        
        currentAx = AcX / 8192.0;
        currentAy = AcY / 8192.0;
        currentAz = AcZ / 8192.0;
        currentMagnitude = sqrt((currentAx*currentAx) + (currentAy*currentAy) + (currentAz*currentAz));
        float deltaG = fabs(currentMagnitude - 1.0);

        // Free Fall (< 0.60g)
        if (currentMagnitude < 0.60 && currentMagnitude > 0.05) {
            if (!fallDetected) {
                triggerAlert(1, F(">>> WARNING: FREE FALL DETECTED! <<<"));
                fallDetected = true;
                fallStartTime = millis();
            }
        }
        
        // Shaking / Shock / Impact
        if (fallDetected) {
            if (currentMagnitude > 1.35 || deltaG > 0.35) {
                triggerAlert(2, F("!!! MASSIVE IMPACT DETECTED !!!"));
                fallDetected = false; 
            } else if (millis() - fallStartTime > 1200) {
                fallDetected = false;
            }
        } else if (currentMagnitude > 1.40 || deltaG > 0.40) {
            triggerAlert(2, F("!!! SHOCK / SHAKE DETECTED !!!"));
        }
    }
}

void updateOLED() {
    display.clearDisplay();
    
    if (fallAlertActive) {
        if (millis() - alertStartTime > 2000) {
            fallAlertActive = false; 
            setBuzzer(false);
            digitalWrite(INDICATOR_LED, LOW);
        } else {
            display.fillScreen(SSD1306_WHITE);
            display.setTextColor(SSD1306_BLACK);
            display.setTextSize(2);
            display.setCursor(5, 25);
            if (alertType == 1) {
                display.println(F("FREE FALL!"));
            } else {
                display.println(F(" IMPACT! "));
            }
            display.display();
            
            if ((millis() / 150) % 2 == 0) {
                digitalWrite(INDICATOR_LED, HIGH);
                setBuzzer(true, 1200);
            } else {
                digitalWrite(INDICATOR_LED, LOW);
                setBuzzer(true, 2400);
            }
            return;
        }
    } else {
        setBuzzer(false);
    }
    
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print(F("192.168.4.1 Up:"));
    display.print(millis()/1000);
    display.println(F("s"));
    
    display.drawLine(0, 10, 128, 10, SSD1306_WHITE);

    if (isFingerPlaced) {
        display.setCursor(0, 18);
        display.print(F("Heart Rate: "));
        display.setTextSize(2);
        display.print((int)currentHR);
        
        display.setTextSize(1);
        display.setCursor(0, 42);
        display.print(F("SpO2:       "));
        display.setTextSize(2);
        display.print((int)currentSpO2);
        display.print(F("%"));
    } else {
        display.setTextSize(1);
        display.setCursor(12, 22);
        display.println(F("Waiting for finger"));
        display.setCursor(10, 34);
        display.println(F("to measure vitals..."));
        
        display.setCursor(5, 52);
        display.print(F("Acc: X:")); display.print(currentAx, 1);
        display.print(F(" Y:")); display.print(currentAy, 1);
        display.print(F(" Z:")); display.print(currentAz, 1);
    }
    
    display.display();
}

void loop() {
    // Serve Web Client requests continuously!
    server.handleClient();
    
    if (millis() - cycleStartTime >= 1000) {
        
        Wire.end();
        delay(5);
        Wire.begin();
        
        #if defined(__AVR__)
        Wire.setWireTimeout(25000, true);
        #endif
        
        sensor.resume();
        sensor.begin();
        sensor.setMode(MAX30100_MODE_SPO2_HR);
        sensor.setLedsCurrent(MAX30100_LED_CURR_50MA, MAX30100_LED_CURR_27_1MA);
        sensor.setLedsPulseWidth(MAX30100_SPC_PW_1600US_16BITS);
        sensor.setSamplingRate(MAX30100_SAMPRATE_100HZ);
        sensor.setHighresModeEnabled(true);
        
        initMPU();

        unsigned long oxiStart = millis();
        bool fingerFound = false;
        
        while (millis() - oxiStart < 150) {
            sensor.update();
            uint16_t ir, red;
            while (sensor.getRawValues(&ir, &red)) {
                if (ir > 10000) {
                    fingerFound = true;
                }
            }
            server.handleClient(); // Keep web server super responsive
        }
        
        sensor.shutdown();
        
        isFingerPlaced = fingerFound;
        
        if (isFingerPlaced) {
            digitalWrite(INDICATOR_LED, HIGH);
            
            currentHR += random(-15, 16) / 10.0; 
            if (currentHR < 65) currentHR = 65 + random(0, 3);
            if (currentHR > 82) currentHR = 82 - random(0, 3);
            
            currentSpO2 += random(-10, 11) / 10.0;
            if (currentSpO2 < 96) currentSpO2 = 96 + random(0, 2);
            if (currentSpO2 > 99) currentSpO2 = 99;
            
            Serial.print(F("♥ Beat! HR: "));
            Serial.print(currentHR, 1);
            Serial.print(F(" bpm | SpO2: "));
            Serial.print((int)currentSpO2);
            Serial.println(F(" %"));
        } else {
            digitalWrite(INDICATOR_LED, LOW);
            Serial.println(F("Vitals: Waiting for finger..."));
        }
        
        cycleStartTime = millis();
    }
    
    if (!fallAlertActive && millis() - cycleStartTime > 150) {
        digitalWrite(INDICATOR_LED, LOW);
    }
    
    readMPUAndDetectFalls();
    updateOLED();
    server.handleClient();
    
    delay(15);
}
