/*
 * =========================================================================================
 * ESP32 AIoT Environmental Monitoring & Rain Simulation System
 * =========================================================================================
 * Hardware Pinout:
 *  - DHT22 (Temp & Humidity): GPIO 33
 *  - Ultrasonic 1: TRIG -> GPIO 25, ECHO -> GPIO 26
 *  - Ultrasonic 2: TRIG -> GPIO 27, ECHO -> GPIO 32
 *  - Soil Moisture Sensor: GPIO 34 (Analog ADC1_CH6)
 *  - Rain Emulation Pump (Relay): GPIO 22 (Active LOW: LOW = ON, HIGH = OFF)
 *
 * Network & Web Interface:
 *  - ESP32 Standalone Hotspot (Access Point): "ESP32-Smart-Monitor" (No Password)
 *  - Default Web Dashboard IP: http://192.168.4.1
 *  - Embedded Captive Portal (Auto-redirect on mobile connection)
 *  - Fully offline, mobile-responsive real-time dashboard with async REST API
 *  - Automated Disaster & Saturation Prediction Engine
 * =========================================================================================
 */

#include <WiFi.h>
#include <WebServer.h>
#include <DNSServer.h>
#include "DHT.h"

// ======================== PIN DEFINITIONS ========================
#define DHT_PIN         33
#define DHT_TYPE        DHT22

#define ULTRA1_TRIG     25
#define ULTRA1_ECHO     26

#define ULTRA2_TRIG     27
#define ULTRA2_ECHO     32

#define SOIL_PIN        34

#define RELAY_PIN       22    // Active LOW: LOW = Pump ON, HIGH = Pump OFF

// ======================== CALIBRATION & CONSTANTS ================
#define SOIL_DRY_ADC    3500  // Typical raw ADC value in dry soil / air
#define SOIL_WET_ADC    1200  // Typical raw ADC value in saturated soil / water

const char* AP_SSID = "ESP32-Smart-Monitor";
const char* AP_PASS = "";  // Open Wi-Fi (No password)

const byte DNS_PORT = 53;
IPAddress apIP(192, 168, 4, 1);
IPAddress netMsk(255, 255, 255, 0);

DNSServer dnsServer;
WebServer server(80);
DHT dht(DHT_PIN, DHT_TYPE);

// ======================== GLOBAL STATE ===========================
bool relayState = false;  // false = OFF (HIGH on pin), true = ON (LOW on pin)

float currentTemp = 0.0;
float currentHumidity = 0.0;
int   currentSoilRaw = 0;
int   currentSoilPct = 0;
float currentDistance1 = -1.0;
float currentDistance2 = -1.0;

float hazardIndex = 0.0;       // 0% to 100%
String riskLevel = "NORMAL";
String predictionText = "System initialized. Monitoring ambient conditions.";
String riskColor = "#10b981";  // Emerald Green

unsigned long lastSensorReadTime = 0;
const unsigned long SENSOR_INTERVAL = 1200; // Read sensors every 1.2 seconds

// ======================== SENSOR HELPER FUNCTIONS ================
float getDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // 25ms timeout (~400cm max range) to avoid blocking web server
  long duration = pulseIn(echoPin, HIGH, 25000);

  if (duration == 0) return -1.0;

  return (duration * 0.0343) / 2.0;
}

int readSmoothedSoil() {
  long sum = 0;
  for (int i = 0; i < 5; i++) {
    sum += analogRead(SOIL_PIN);
    delayMicroseconds(100);
  }
  return sum / 5;
}

void setRelay(bool state) {
  relayState = state;
  digitalWrite(RELAY_PIN, relayState ? LOW : HIGH); // Active LOW
  Serial.print("[PUMP] Rain Simulation Relay: ");
  Serial.println(relayState ? "ON (Simulating Rain)" : "OFF (Standby)");
}

// ======================== PREDICTION LOGIC =======================
void updatePredictions() {
  // Calculate hazard score based on multivariate inputs:
  // 1. Soil saturation (weight: 45%)
  // 2. Rain simulation status (weight: 25%)
  // 3. Water accumulation / proximity on Ultrasonic sensors (weight: 20%)
  // 4. Humidity factor (weight: 10%)

  float soilScore = (float)currentSoilPct * 0.45;

  float rainScore = relayState ? 25.0 : 0.0;

  float waterLevelScore = 0.0;
  // If ultrasonic sensors detect water surface rising (distance < 15cm)
  if (currentDistance1 > 0 && currentDistance1 < 12.0) {
    waterLevelScore += 10.0 * (1.0 - (currentDistance1 / 12.0));
  }
  if (currentDistance2 > 0 && currentDistance2 < 12.0) {
    waterLevelScore += 10.0 * (1.0 - (currentDistance2 / 12.0));
  }

  float humScore = 0.0;
  if (!isnan(currentHumidity) && currentHumidity > 70.0) {
    humScore = ((currentHumidity - 70.0) / 30.0) * 10.0;
  }

  hazardIndex = constrain(soilScore + rainScore + waterLevelScore + humScore, 0.0, 100.0);

  // Categorize Risk Level & Actionable Prediction Message
  if (hazardIndex >= 75.0) {
    riskLevel = "CRITICAL HAZARD";
    riskColor = "#ef4444"; // Red
    predictionText = "HIGH DISASTER RISK: Severe soil saturation & rapid water runoff detected! Soil stability compromised.";
  } else if (hazardIndex >= 50.0) {
    riskLevel = "WARNING / HIGH RISK";
    riskColor = "#f97316"; // Orange
    predictionText = "ELEVATED RISK: Active rainfall & high moisture detected. Water accumulation is increasing.";
  } else if (hazardIndex >= 25.0) {
    riskLevel = "ADVISORY / WATCH";
    riskColor = "#f59e0b"; // Amber Yellow
    predictionText = relayState 
      ? "Rain simulation active. Soil moisture is gradually absorbing precipitation."
      : "Moderate moisture detected. All stream and environmental readings stable.";
  } else {
    riskLevel = "SAFE / NORMAL";
    riskColor = "#10b981"; // Green
    predictionText = "Optimal stability. Low moisture, dry catchment basin, and clear atmospheric conditions.";
  }
}

void readAllSensors() {
  // Ultrasonic 1
  float d1 = getDistance(ULTRA1_TRIG, ULTRA1_ECHO);
  if (d1 > 0.0) currentDistance1 = d1;
  else currentDistance1 = -1.0;

  // Ultrasonic 2
  float d2 = getDistance(ULTRA2_TRIG, ULTRA2_ECHO);
  if (d2 > 0.0) currentDistance2 = d2;
  else currentDistance2 = -1.0;

  // DHT22
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  if (!isnan(t)) currentTemp = t;
  if (!isnan(h)) currentHumidity = h;

  // Soil
  currentSoilRaw = readSmoothedSoil();
  // Map ADC (lower value = wetter soil in resistive/capacitive sensors)
  int pct = map(currentSoilRaw, SOIL_DRY_ADC, SOIL_WET_ADC, 0, 100);
  currentSoilPct = constrain(pct, 0, 100);

  // Update Prediction Engine
  updatePredictions();
}

// ======================== HTML DASHBOARD (PROGMEM) ===============
const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Smart AIoT Environmental & Rain Simulation System</title>
  <style>
    :root {
      --bg: #090d16;
      --card-bg: rgba(20, 29, 47, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --accent-glow: rgba(56, 189, 248, 0.25);
      --green: #10b981;
      --orange: #f59e0b;
      --red: #ef4444;
      --card-radius: 18px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    body {
      background: radial-gradient(circle at top right, #13233e, var(--bg));
      color: var(--text);
      min-height: 100vh;
      padding: 20px 14px 40px;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .container {
      width: 100%;
      max-width: 900px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    /* Header */
    .header {
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--card-border);
      border-radius: var(--card-radius);
      padding: 20px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 14px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.37);
    }
    .header h1 {
      font-size: 1.4rem;
      font-weight: 700;
      letter-spacing: -0.5px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .header h1 span { color: var(--accent); }
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #34d399;
      padding: 6px 14px;
      border-radius: 999px;
      font-size: 0.82rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .pulse-dot {
      width: 8px;
      height: 8px;
      background: #10b981;
      border-radius: 50%;
      box-shadow: 0 0 10px #10b981;
      animation: pulse 1.6s infinite ease-in-out;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.3; transform: scale(0.8); }
    }

    /* Relay / Rain Pump Controller */
    .controller-card {
      background: linear-gradient(135deg, rgba(30, 58, 138, 0.4), rgba(15, 23, 42, 0.8));
      border: 1px solid rgba(56, 189, 248, 0.3);
      border-radius: var(--card-radius);
      padding: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
      flex-wrap: wrap;
      gap: 16px;
    }
    .controller-info h2 {
      font-size: 1.25rem;
      font-weight: 700;
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .controller-info p {
      color: var(--text-muted);
      font-size: 0.88rem;
    }
    .toggle-wrap {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .switch {
      position: relative;
      display: inline-block;
      width: 68px;
      height: 36px;
    }
    .switch input { opacity: 0; width: 0; height: 0; }
    .slider {
      position: absolute;
      cursor: pointer;
      top: 0; left: 0; right: 0; bottom: 0;
      background-color: #334155;
      transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      border-radius: 36px;
      border: 2px solid rgba(255,255,255,0.1);
    }
    .slider:before {
      position: absolute;
      content: "";
      height: 26px;
      width: 26px;
      left: 3px;
      bottom: 3px;
      background-color: white;
      transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      border-radius: 50%;
      box-shadow: 0 2px 6px rgba(0,0,0,0.4);
    }
    input:checked + .slider {
      background: linear-gradient(135deg, #0284c7, #38bdf8);
      box-shadow: 0 0 16px var(--accent-glow);
    }
    input:checked + .slider:before {
      transform: translateX(32px);
    }
    .relay-status-pill {
      font-size: 0.85rem;
      font-weight: 700;
      padding: 6px 12px;
      border-radius: 8px;
      letter-spacing: 0.5px;
    }
    .relay-on { background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf8; }
    .relay-off { background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); }

    /* Prediction Banner */
    .prediction-card {
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      border: 1px solid var(--card-border);
      border-radius: var(--card-radius);
      padding: 22px 24px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .prediction-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
    }
    .prediction-title {
      font-size: 1.1rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .risk-badge {
      padding: 6px 14px;
      border-radius: 999px;
      font-size: 0.82rem;
      font-weight: 800;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      transition: all 0.3s ease;
    }
    .hazard-bar-wrap {
      width: 100%;
      height: 12px;
      background: #1e293b;
      border-radius: 6px;
      overflow: hidden;
      position: relative;
    }
    .hazard-bar {
      height: 100%;
      width: 0%;
      border-radius: 6px;
      transition: width 0.6s ease, background-color 0.6s ease;
    }
    .prediction-msg {
      font-size: 0.95rem;
      color: #cbd5e1;
      line-height: 1.45;
      background: rgba(0, 0, 0, 0.25);
      padding: 12px 16px;
      border-radius: 12px;
      border-left: 4px solid var(--accent);
    }

    /* Grid of Sensors */
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 16px;
    }
    .sensor-card {
      background: var(--card-bg);
      backdrop-filter: blur(10px);
      border: 1px solid var(--card-border);
      border-radius: var(--card-radius);
      padding: 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: transform 0.2s ease, border-color 0.2s ease;
      box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
    .sensor-card:hover {
      transform: translateY(-2px);
      border-color: rgba(255, 255, 255, 0.16);
    }
    .sensor-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }
    .sensor-name {
      font-size: 0.85rem;
      color: var(--text-muted);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .sensor-icon {
      font-size: 1.3rem;
    }
    .sensor-value {
      font-size: 2.1rem;
      font-weight: 800;
      letter-spacing: -0.5px;
      color: #fff;
      display: flex;
      align-items: baseline;
      gap: 6px;
      margin-bottom: 6px;
    }
    .sensor-unit {
      font-size: 1rem;
      font-weight: 500;
      color: var(--text-muted);
    }
    .sensor-sub {
      font-size: 0.8rem;
      color: var(--text-muted);
    }
    .progress-bar-wrap {
      width: 100%;
      height: 6px;
      background: #1e293b;
      border-radius: 3px;
      margin-top: 10px;
      overflow: hidden;
    }
    .progress-bar {
      height: 100%;
      width: 0%;
      background: var(--accent);
      border-radius: 3px;
      transition: width 0.5s ease;
    }

    /* Footer */
    .footer {
      text-align: center;
      color: var(--text-muted);
      font-size: 0.8rem;
      margin-top: 10px;
    }
  </style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <header class="header">
      <div>
        <h1>🌧️ <span>AIoT</span> Disaster & Weather Monitor</h1>
        <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 2px;">
          ESP32 Live Telemetry &bull; Hotspot: <strong>192.168.4.1</strong>
        </p>
      </div>
      <div class="status-badge" id="conn-badge">
        <div class="pulse-dot"></div>
        <span id="conn-text">LIVE CONNECTED</span>
      </div>
    </header>

    <!-- Rain Simulation Pump Controller -->
    <section class="controller-card">
      <div class="controller-info">
        <h2>⚡ Rain Simulation Pump (Relay)</h2>
        <p>Switch ON the pump to emulate rainfall onto the terrain and trigger runoff.</p>
      </div>
      <div class="toggle-wrap">
        <span class="relay-status-pill relay-off" id="relay-pill">OFF (STANDBY)</span>
        <label class="switch">
          <input type="checkbox" id="relay-switch" onchange="toggleRelay(this.checked)">
          <span class="slider"></span>
        </label>
      </div>
    </section>

    <!-- Disaster & Risk Prediction Engine -->
    <section class="prediction-card">
      <div class="prediction-header">
        <div class="prediction-title">
          🧠 Smart Predictive Analysis & Risk Engine
        </div>
        <div class="risk-badge" id="risk-badge" style="background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981;">
          SAFE / NORMAL
        </div>
      </div>
      <div class="hazard-bar-wrap">
        <div class="hazard-bar" id="hazard-bar" style="width: 15%; background-color: #10b981;"></div>
      </div>
      <div class="prediction-msg" id="prediction-msg">
        System initialized. Monitoring ambient conditions and soil saturation...
      </div>
    </section>

    <!-- Sensor Metrics Grid -->
    <main class="grid">
      <!-- Temperature -->
      <div class="sensor-card">
        <div class="sensor-top">
          <span class="sensor-name">Ambient Temp</span>
          <span class="sensor-icon">🌡️</span>
        </div>
        <div class="sensor-value">
          <span id="temp-val">--</span><span class="sensor-unit">°C</span>
        </div>
        <div class="sensor-sub">DHT22 Digital Sensor</div>
      </div>

      <!-- Humidity -->
      <div class="sensor-card">
        <div class="sensor-top">
          <span class="sensor-name">Relative Humidity</span>
          <span class="sensor-icon">💧</span>
        </div>
        <div class="sensor-value">
          <span id="hum-val">--</span><span class="sensor-unit">%</span>
        </div>
        <div class="progress-bar-wrap">
          <div class="progress-bar" id="hum-bar" style="background: #38bdf8;"></div>
        </div>
      </div>

      <!-- Soil Moisture -->
      <div class="sensor-card">
        <div class="sensor-top">
          <span class="sensor-name">Soil Moisture</span>
          <span class="sensor-icon">🌱</span>
        </div>
        <div class="sensor-value">
          <span id="soil-pct">--</span><span class="sensor-unit">%</span>
        </div>
        <div class="sensor-sub" id="soil-raw">Raw ADC: --</div>
        <div class="progress-bar-wrap">
          <div class="progress-bar" id="soil-bar" style="background: #10b981;"></div>
        </div>
      </div>

      <!-- Ultrasonic 1 -->
      <div class="sensor-card">
        <div class="sensor-top">
          <span class="sensor-name">Ultrasonic 1 (Stream/Level)</span>
          <span class="sensor-icon">📏</span>
        </div>
        <div class="sensor-value">
          <span id="u1-val">--</span><span class="sensor-unit" id="u1-unit">cm</span>
        </div>
        <div class="sensor-sub">Trigger: 25 | Echo: 26</div>
      </div>

      <!-- Ultrasonic 2 -->
      <div class="sensor-card">
        <div class="sensor-top">
          <span class="sensor-name">Ultrasonic 2 (Reservoir/Depth)</span>
          <span class="sensor-icon">📊</span>
        </div>
        <div class="sensor-value">
          <span id="u2-val">--</span><span class="sensor-unit" id="u2-unit">cm</span>
        </div>
        <div class="sensor-sub">Trigger: 27 | Echo: 32</div>
      </div>
    </main>

    <!-- Footer -->
    <footer class="footer">
      Autonomous IoT System &bull; Standalone Wi-Fi Portal &bull; Active LOW Relay 22
    </footer>
  </div>

  <script>
    let isToggling = false;

    async function fetchTelemetry() {
      try {
        const response = await fetch('/data');
        if (!response.ok) throw new Error('Network error');
        const data = await response.json();

        // Temperature & Humidity
        document.getElementById('temp-val').innerText = (data.temp !== null && data.temp >= 0) ? data.temp.toFixed(1) : '--';
        document.getElementById('hum-val').innerText = (data.hum !== null && data.hum >= 0) ? data.hum.toFixed(1) : '--';
        document.getElementById('hum-bar').style.width = Math.min(100, Math.max(0, data.hum || 0)) + '%';

        // Soil
        document.getElementById('soil-pct').innerText = data.soil_pct;
        document.getElementById('soil-raw').innerText = 'Raw ADC: ' + data.soil_raw;
        document.getElementById('soil-bar').style.width = data.soil_pct + '%';
        if (data.soil_pct > 75) {
          document.getElementById('soil-bar').style.background = '#ef4444';
        } else if (data.soil_pct > 40) {
          document.getElementById('soil-bar').style.background = '#38bdf8';
        } else {
          document.getElementById('soil-bar').style.background = '#10b981';
        }

        // Ultrasonic 1
        if (data.u1 < 0) {
          document.getElementById('u1-val').innerText = 'NO ECHO';
          document.getElementById('u1-unit').innerText = '';
        } else {
          document.getElementById('u1-val').innerText = data.u1.toFixed(1);
          document.getElementById('u1-unit').innerText = 'cm';
        }

        // Ultrasonic 2
        if (data.u2 < 0) {
          document.getElementById('u2-val').innerText = 'NO ECHO';
          document.getElementById('u2-unit').innerText = '';
        } else {
          document.getElementById('u2-val').innerText = data.u2.toFixed(1);
          document.getElementById('u2-unit').innerText = 'cm';
        }

        // Relay Switch sync (if user is not actively toggling)
        if (!isToggling) {
          const sw = document.getElementById('relay-switch');
          const pill = document.getElementById('relay-pill');
          sw.checked = data.relay;
          if (data.relay) {
            pill.className = 'relay-status-pill relay-on';
            pill.innerText = 'ON (SIMULATING RAIN)';
          } else {
            pill.className = 'relay-status-pill relay-off';
            pill.innerText = 'OFF (STANDBY)';
          }
        }

        // Risk / Predictions
        const badge = document.getElementById('risk-badge');
        const hbar = document.getElementById('hazard-bar');
        const msg = document.getElementById('prediction-msg');

        badge.innerText = data.risk_level;
        badge.style.color = data.status_color;
        badge.style.borderColor = data.status_color;
        badge.style.background = data.status_color + '25';

        hbar.style.width = data.hazard_idx + '%';
        hbar.style.backgroundColor = data.status_color;

        msg.innerText = data.prediction_text;
        msg.style.borderLeftColor = data.status_color;

        // Connection Badge
        document.getElementById('conn-text').innerText = 'LIVE CONNECTED';
        document.getElementById('conn-badge').style.color = '#34d399';

      } catch (err) {
        console.error("Telemetry poll failed:", err);
        document.getElementById('conn-text').innerText = 'CONNECTING...';
        document.getElementById('conn-badge').style.color = '#f59e0b';
      }
    }

    async function toggleRelay(state) {
      isToggling = true;
      const pill = document.getElementById('relay-pill');
      pill.innerText = state ? 'ACTIVATING PUMP...' : 'STOPPING PUMP...';
      try {
        const res = await fetch('/relay?state=' + (state ? '1' : '0'));
        const json = await res.json();
        const sw = document.getElementById('relay-switch');
        sw.checked = json.relay;
        if (json.relay) {
          pill.className = 'relay-status-pill relay-on';
          pill.innerText = 'ON (SIMULATING RAIN)';
        } else {
          pill.className = 'relay-status-pill relay-off';
          pill.innerText = 'OFF (STANDBY)';
        }
      } catch (e) {
        console.error("Failed to toggle relay:", e);
      } finally {
        setTimeout(() => { isToggling = false; }, 400);
      }
    }

    // Fast polling every 1000ms
    setInterval(fetchTelemetry, 1000);
    fetchTelemetry();
  </script>
</body>
</html>
)rawliteral";

// ======================== HTTP HANDLERS ==========================
void handleRoot() {
  server.send(200, "text/html", INDEX_HTML);
}

void handleData() {
  String json = "{";
  json += "\"temp\":" + (isnan(currentTemp) ? "null" : String(currentTemp, 1)) + ",";
  json += "\"hum\":" + (isnan(currentHumidity) ? "null" : String(currentHumidity, 1)) + ",";
  json += "\"soil_raw\":" + String(currentSoilRaw) + ",";
  json += "\"soil_pct\":" + String(currentSoilPct) + ",";
  json += "\"u1\":" + String(currentDistance1, 2) + ",";
  json += "\"u2\":" + String(currentDistance2, 2) + ",";
  json += "\"relay\":" + String(relayState ? "true" : "false") + ",";
  json += "\"hazard_idx\":" + String((int)hazardIndex) + ",";
  json += "\"risk_level\":\"" + riskLevel + "\",";
  json += "\"prediction_text\":\"" + predictionText + "\",";
  json += "\"status_color\":\"" + riskColor + "\"";
  json += "}";

  server.send(200, "application/json", json);
}

void handleRelay() {
  if (server.hasArg("state")) {
    String stateArg = server.arg("state");
    if (stateArg == "1" || stateArg == "true" || stateArg == "on") {
      setRelay(true);
    } else {
      setRelay(false);
    }
  } else {
    // Toggle if no explicit state given
    setRelay(!relayState);
  }

  String json = "{\"relay\":" + String(relayState ? "true" : "false") + "}";
  server.send(200, "application/json", json);
}

// Captive Portal Redirection
void handleNotFound() {
  server.sendHeader("Location", String("http://") + apIP.toString() + "/", true);
  server.send(302, "text/plain", "");
}

// ======================== SETUP & LOOP ===========================
void setup() {
  Serial.begin(115200);
  delay(500);

  // Pin Configurations
  pinMode(ULTRA1_TRIG, OUTPUT);
  pinMode(ULTRA1_ECHO, INPUT);

  pinMode(ULTRA2_TRIG, OUTPUT);
  pinMode(ULTRA2_ECHO, INPUT);

  pinMode(RELAY_PIN, OUTPUT);
  
  // Initialize Relay OFF (Active LOW -> HIGH is OFF)
  setRelay(false);

  // Start DHT22
  dht.begin();

  Serial.println();
  Serial.println("=================================================");
  Serial.println(" AIoT Environmental & Rain Simulation System");
  Serial.println("=================================================");

  // 1. Configure Standalone Wi-Fi Hotspot (SoftAP)
  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(apIP, apIP, netMsk);
  bool apCreated = WiFi.softAP(AP_SSID, AP_PASS);

  if (apCreated) {
    Serial.print("[WIFI] Hotspot Created Successfully: ");
    Serial.println(AP_SSID);
    Serial.print("[WIFI] Dashboard IP: http://");
    Serial.println(WiFi.softAPIP());
  } else {
    Serial.println("[WIFI] Failed to start SoftAP!");
  }

  // 2. Start DNS Server for Captive Portal (Redirects all domain requests to 192.168.4.1)
  dnsServer.setErrorReplyCode(DNSReplyCode::NoError);
  dnsServer.start(DNS_PORT, "*", apIP);

  // 3. Web Server Routes
  server.on("/", HTTP_GET, handleRoot);
  server.on("/data", HTTP_GET, handleData);
  server.on("/relay", HTTP_GET, handleRelay);

  // Captive Portal Check Endpoints
  server.on("/generate_204", HTTP_GET, handleRoot);       // Android captive check
  server.on("/hotspot-detect.html", HTTP_GET, handleRoot); // Apple iOS captive check
  server.on("/canonical.html", HTTP_GET, handleRoot);
  server.on("/connecttest.txt", HTTP_GET, handleRoot);     // Windows check
  server.on("/ncsi.txt", HTTP_GET, handleRoot);
  server.onNotFound(handleNotFound);

  server.begin();
  Serial.println("[HTTP] Web Server Started on Port 80");
  Serial.println("[SYSTEM] Ready. Connect to 'ESP32-Smart-Monitor' and open http://192.168.4.1");

  // Initial sensor read
  readAllSensors();
}

void loop() {
  // 1. Process DNS requests for captive portal
  dnsServer.processNextRequest();

  // 2. Process incoming Web Server client requests
  server.handleClient();

  // 3. Periodic Non-Blocking Sensor Readings & Telemetry Update
  unsigned long now = millis();
  if (now - lastSensorReadTime >= SENSOR_INTERVAL) {
    lastSensorReadTime = now;
    readAllSensors();

    // Debug Serial Output
    Serial.print("T:");
    Serial.print(currentTemp, 1);
    Serial.print("C | H:");
    Serial.print(currentHumidity, 1);
    Serial.print("% | Soil:");
    Serial.print(currentSoilPct);
    Serial.print("% (");
    Serial.print(currentSoilRaw);
    Serial.print(") | U1:");
    Serial.print(currentDistance1, 1);
    Serial.print("cm | U2:");
    Serial.print(currentDistance2, 1);
    Serial.print("cm | Relay:");
    Serial.print(relayState ? "ON" : "OFF");
    Serial.print(" | Risk:");
    Serial.println(riskLevel);
  }
}
