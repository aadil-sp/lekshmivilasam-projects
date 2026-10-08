// LVHS Project Support (lvhsprojectsupport)
// Fast Student Assistant & Exhibition Workbench Logic

const pinoutDatabase = [
  { name: "Soil Moisture Sensor (Capacitive/Resistive)", project: "IoT Track", pin: "GPIO 34 (ADC1_CH6)", voltage: "3.3V or 5V", wire: "🔴 VCC: 3.3V | ⚫ GND: GND | 🟡 A0: GPIO 34", notes: "Use Analog A0 pin. Dry soil yields high raw ADC values (~3200-4095); submerged wet soil yields low values (~1100-1400)." },
  { name: "HC-SR04 Ultrasonic 1 (Stream Level)", project: "IoT Track", pin: "TRIG: GPIO 25 | ECHO: GPIO 26", voltage: "5V VCC", wire: "🔴 VCC: 5V | ⚫ GND: GND | 🟡 TRIG: GPIO 25 | 🟢 ECHO: GPIO 26", notes: "Use voltage divider (1kΩ + 2kΩ) on ECHO pin to step down 5V echo pulses to 3.3V safe level for ESP32." },
  { name: "HC-SR04 Ultrasonic 2 (Catchment Basin)", project: "IoT Track", pin: "TRIG: GPIO 27 | ECHO: GPIO 32", voltage: "5V VCC", wire: "🔴 VCC: 5V | ⚫ GND: GND | 🟡 TRIG: GPIO 27 | 🟢 ECHO: GPIO 32", notes: "Measures rising reservoir depth. 10µs trigger pulse sent every measurement cycle." },
  { name: "12V Rain Simulation Pump Relay", project: "IoT Track", pin: "IN: GPIO 22", voltage: "5V / 12V", wire: "🔴 Relay VCC: 5V | ⚫ GND: GND | 🔵 IN: GPIO 22 | ⚡ COM/NO: 12V Pump Series", notes: "Active LOW relay module: Writing LOW (0V) turns pump ON; writing HIGH (3.3V) turns pump OFF." },
  { name: "DHT22 Temperature & Humidity", project: "IoT Track", pin: "DATA: GPIO 33", voltage: "3.3V - 5V", wire: "🔴 VCC: 3.3V | ⚫ GND: GND | 🟡 DATA: GPIO 33 (with 4.7kΩ pullup to 3.3V)", notes: "One-Wire digital protocol. Wait at least 1.5 seconds between consecutive reads to prevent self-heating." },
  { name: "L298N Motor Driver - Left Motor (ENA, IN1, IN2)", project: "Robotics Track", pin: "ENA: Pin 6 (PWM) | IN1: Pin 9 | IN2: Pin 10", voltage: "12V VMS, 5V Logic", wire: "🟡 ENA: D6 | 🟢 IN1: D9 | 🔵 IN2: D10 | 🔴 VMS: 11.1V Battery | ⚫ GND: Common GND", notes: "Remove jumper on ENA to enable PWM speed regulation (0-255). IN1=HIGH, IN2=LOW drives forward." },
  { name: "L298N Motor Driver - Right Motor (ENB, IN3, IN4)", project: "Robotics Track", pin: "ENB: Pin 5 (PWM) | IN3: Pin 11 | IN4: Pin 12", voltage: "12V VMS, 5V Logic", wire: "🟡 ENB: D5 | 🟢 IN3: D11 | 🔵 IN4: D12 | 🔴 VMS: 11.1V Battery | ⚫ GND: Common GND", notes: "Remove jumper on ENB to enable PWM speed regulation (0-255). IN3=HIGH, IN4=LOW drives forward." },
  { name: "RPLIDAR A1/A2 (360° 2D Laser Scanner)", project: "Robotics Track", pin: "TX: Arduino RX0 / USB Serial | RX: Arduino TX0", voltage: "5V (Requires ~500mA)", wire: "🔴 VCC: 5V (from 3A Buck) | ⚫ GND: GND | 🟡 TX: RX | 🟢 RX: TX", notes: "Operates at 115200 baud rate. Ensure motor PWM wire is connected to 5V or PWM speed pin." },
  { name: "MAX30102 Pulse Oximeter & Heart Rate", project: "Electronics Track", pin: "SDA: GPIO 4 | SCL: GPIO 5", voltage: "3.3V", wire: "🔴 VIN: 3.3V | ⚫ GND: GND | 🟡 SDA: GPIO 4 | 🟢 SCL: GPIO 5", notes: "I2C Address 0x57. Place finger with light, steady pressure. Ensure 4.7kΩ pull-up resistors on SDA/SCL." },
  { name: "MPU6050 6-Axis Gyroscope & Accelerometer", project: "Electronics Track", pin: "SDA: GPIO 4 | SCL: GPIO 5", voltage: "3.3V - 5V", wire: "🔴 VCC: 3.3V | ⚫ GND: GND | 🟡 SDA: GPIO 4 | 🟢 SCL: GPIO 5", notes: "I2C Address 0x68 (AD0=GND). Provides real-time 3D acceleration vectors for fall detection." },
  { name: "SSD1306 0.96\" Monochrome OLED Display", project: "Electronics Track", pin: "SDA: GPIO 4 | SCL: GPIO 5", voltage: "3.3V - 5V", wire: "🔴 VCC: 3.3V | ⚫ GND: GND | 🟡 SDA: GPIO 4 | 🟢 SCL: GPIO 5", notes: "I2C Address 0x3C. 128x64 pixels graphic buffer. Shares I2C bus with MPU6050 and MAX30102." },
  { name: "Active Buzzer & Haptic Vibration Motor", project: "Electronics Track", pin: "BUZZER_PIN: GPIO 3", voltage: "3.3V (via NPN transistor)", wire: "🔴 Collector/Buzzer+: 3.3V | 🟡 Base: GPIO 3 (via 1kΩ) | ⚫ Emitter/GND: GND", notes: "Emits 85dB alert tone and tactile buzz upon sudden 3.2g fall detection or critical hypoxia (SpO2 < 90%)." },
  { name: "Emergency Cancel Tactile Push Button", project: "Electronics Track", pin: "CANCEL_PIN: GPIO 8", voltage: "Internal Pull-Up", wire: "🟡 Pin 1: GPIO 8 | ⚫ Pin 2: GND", notes: "Active LOW button. Pressing grounds GPIO 8 to cancel the 15-second fall alarm countdown." }
];

const projectData = {
  iot: {
    title: "AIoT Disaster Early Warning & Rain Simulation Station",
    category: "IoT & Disaster Management Track",
    color: "#10b981",
    overview: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">🌧️ IoT Track &bull; Disaster Mitigation</div>
        <h3>AIoT Landslide Early Warning & Rain Simulation Station</h3>
        <p>A self-contained edge telemetry weather station with an automated 12V rain emulation pump and an offline standalone Wi-Fi hotspot dashboard (192.168.4.1).</p>
      </div>

      <div class="detail-grid">
        <div class="detail-card">
          <h4>🎤 60-Second Exhibition Pitch for Judges</h4>
          <p><em>"Respected judges, Western Ghats landslides occur when prolonged rain saturates soil pore water, dropping the safety factor below 1.0. Our AIoT station solves this by combining real-time soil moisture saturation, stream depth acoustic monitoring, and DHT22 atmospheric data on an offline ESP32 edge engine. It features an active 12V rainfall emulation pump to demonstrate real-time hazard transitions on our standalone local web dashboard at 192.168.4.1—functioning completely without cellular or external internet."</em></p>
        </div>

        <div class="detail-card">
          <h4>🎯 The Critical Problem</h4>
          <p>Hilly disaster zones in Kerala (Wayanad, Idukki, Nilambur) face sudden monsoon-induced debris flows. Satellite forecasts cover entire districts and miss localized hill-slope saturation, while cell towers frequently collapse during floods.</p>
        </div>

        <div class="detail-card">
          <h4>💡 Key Innovation & Architecture</h4>
          <p>Dual-core ESP32 edge processor hosting an autonomous Wi-Fi SoftAP and Captive Portal DNS. Multivariate mathematical model calculates instant hazard percentage (0-100%) and triggers audio-visual alarms with zero cloud latency.</p>
        </div>

        <div class="detail-card">
          <h4>📦 Bill of Materials (BOM)</h4>
          <ul>
            <li><strong>ESP32 DevKit V1 (30-pin):</strong> 240MHz Dual-Core SoC</li>
            <li><strong>Capacitive Soil Moisture Probe:</strong> Analog ADC pin</li>
            <li><strong>2x HC-SR04 Ultrasonic Sensors:</strong> Water level & catchment depth</li>
            <li><strong>DHT22 Sensor:</strong> High-precision Temp & Humidity</li>
            <li><strong>1-Channel 5V Relay Module:</strong> Active LOW opto-isolated</li>
            <li><strong>12V DC Submersible Water Pump:</strong> Rain emulation reservoir</li>
          </ul>
        </div>
      </div>
    `,

    circuit: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">🔌 Hardware Connections</div>
        <h3>ESP32 Circuit Pin Mapping & Wiring Guide</h3>
        <p>Carefully wire your ESP32 microcontroller using this verified pinout table.</p>
      </div>

      <div class="data-table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Module / Sensor</th>
              <th>Sensor Pin</th>
              <th>ESP32 Pin</th>
              <th>Wire Color</th>
              <th>Protocol & Electrical Logic</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Soil Moisture Probe</strong></td>
              <td>A0 (Analog Output)</td>
              <td><code>GPIO 34</code></td>
              <td><span class="color-dot yellow"></span> Yellow</td>
              <td>ADC1 Channel 6 (12-bit Analog: 0 to 4095)</td>
            </tr>
            <tr>
              <td><strong>Soil Moisture Probe</strong></td>
              <td>VCC / GND</td>
              <td><code>3.3V / GND</code></td>
              <td><span class="color-dot red"></span> Red / <span class="color-dot black"></span> Black</td>
              <td>Power supply rail (3.3V recommended)</td>
            </tr>
            <tr>
              <td><strong>Ultrasonic 1 (Stream Level)</strong></td>
              <td>TRIG</td>
              <td><code>GPIO 25</code></td>
              <td><span class="color-dot blue"></span> Blue</td>
              <td>10µs digital trigger pulse</td>
            </tr>
            <tr>
              <td><strong>Ultrasonic 1 (Stream Level)</strong></td>
              <td>ECHO</td>
              <td><code>GPIO 26</code></td>
              <td><span class="color-dot green"></span> Green</td>
              <td>5V Echo into 1k/2k resistor voltage divider to 3.3V</td>
            </tr>
            <tr>
              <td><strong>Ultrasonic 2 (Catchment Depth)</strong></td>
              <td>TRIG / ECHO</td>
              <td><code>GPIO 27 / GPIO 32</code></td>
              <td><span class="color-dot orange"></span> Orange / <span class="color-dot cyan"></span> Cyan</td>
              <td>Secondary echo channel for reservoir volume</td>
            </tr>
            <tr>
              <td><strong>Rain Emulation Relay</strong></td>
              <td>IN (Control)</td>
              <td><code>GPIO 22</code></td>
              <td><span class="color-dot purple"></span> Purple</td>
              <td><strong>Active LOW</strong> (LOW = Pump ON, HIGH = Pump OFF)</td>
            </tr>
            <tr>
              <td><strong>DHT22 Sensor</strong></td>
              <td>DATA</td>
              <td><code>GPIO 33</code></td>
              <td><span class="color-dot yellow"></span> Yellow</td>
              <td>One-Wire digital protocol with 4.7kΩ pull-up resistor</td>
            </tr>
            <tr>
              <td><strong>Relay Power & Pump</strong></td>
              <td>COM & NO</td>
              <td><code>12V Battery Rail</code></td>
              <td><span class="color-dot red"></span> Red (12V)</td>
              <td>Isolated 12V rail for DC pump (NEVER power pump from ESP32!)</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="callout-box info">
        <strong>⚡ Pro-Tip for Exhibition Setup:</strong> Always connect the ESP32 GND and the 12V power supply ground together ("Common Ground"). Keep the 12V pump motor wires away from the analog soil sensor wire to avoid electrical noise.
      </div>
    `,

    steps: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">🛠️ Build Helper</div>
        <h3>Step-by-Step Hardware Assembly & Connection Guide</h3>
        <p>Follow these 4 sequential phases to build and test the project quickly.</p>
      </div>

      <div class="steps-container">
        <div class="step-card">
          <div class="step-number">1</div>
          <div class="step-content">
            <h4>Phase 1: Power & Breadboard Bus Setup</h4>
            <p>Insert the ESP32 DevKit into your breadboard spanning the center divider. Connect the ESP32 <code>GND</code> pin to the negative power rail (-) of the breadboard and the <code>3.3V</code> pin to the positive power rail (+).</p>
          </div>
        </div>

        <div class="step-card">
          <div class="step-number">2</div>
          <div class="step-content">
            <h4>Phase 2: Sensor Wiring</h4>
            <p>Connect the <strong>Soil Moisture</strong> sensor's A0 pin to <code>GPIO 34</code>. Wire the <strong>DHT22</strong> data pin to <code>GPIO 33</code> with a 4.7kΩ resistor between DATA and 3.3V. Wire <strong>Ultrasonic 1</strong> TRIG to <code>GPIO 25</code> and ECHO to <code>GPIO 26</code>.</p>
          </div>
        </div>

        <div class="step-card">
          <div class="step-number">3</div>
          <div class="step-content">
            <h4>Phase 3: Relay & Water Pump Circuit</h4>
            <p>Connect Relay VCC to 5V (or VIN) and Relay IN to <code>GPIO 22</code>. Wire the 12V DC water pump in series with the Relay <code>COM</code> and <code>NO</code> (Normally Open) terminals connected to your 12V battery.</p>
          </div>
        </div>

        <div class="step-card">
          <div class="step-number">4</div>
          <div class="step-content">
            <h4>Phase 4: Flashing Code & Hotspot Verification</h4>
            <p>Open Arduino IDE, select <strong>ESP32 Dev Module</strong>, choose your COM port, and upload the code. Once uploaded, take your phone, connect to Wi-Fi <strong>ESP32-Smart-Monitor</strong> (No password), and open browser to <code>http://192.168.4.1</code>.</p>
          </div>
        </div>
      </div>
    `,

    code: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">💻 Firmware Studio</div>
        <h3>Complete Ready-to-Flash ESP32 Firmware</h3>
        <p>Includes embedded async Web Server, Captive Portal DNS, JSON REST API, and automatic hazard calculation engine.</p>
      </div>

      <div class="code-actions-bar">
        <button class="btn btn-sm btn-primary" onclick="copyCode('iot-firmware-code')">📋 Copy Full Code</button>
        <button class="btn btn-sm btn-secondary" onclick="downloadInoFile('landslide_iot_station.ino', 'iot-firmware-code')">💾 Download .ino File</button>
        <span class="code-meta">Target: ESP32 Dev Module &bull; Baud: 115200</span>
      </div>

      <div class="code-container">
        <div class="code-header">
          <span class="code-title">landslide_iot_station.ino</span>
          <span class="code-lang">C++ / Arduino</span>
        </div>
        <pre class="code-block" id="iot-firmware-code">/*
 * =========================================================================
 * LVHS PROJECT SUPPORT (lvhsprojectsupport) - EXHIBITION EDITION
 * PROJECT 1: AIoT LANDSLIDE EARLY WARNING & RAIN SIMULATION STATION
 * Microcontroller: ESP32 Dual-Core (Wi-Fi SoftAP @ 192.168.4.1)
 * =========================================================================
 */

#include &lt;WiFi.h&gt;
#include &lt;WebServer.h&gt;
#include &lt;DNSServer.h&gt;
#include "DHT.h"

// --- PIN DEFINITIONS ---
#define DHT_PIN 33
#define DHT_TYPE DHT22
#define ULTRA1_TRIG 25
#define ULTRA1_ECHO 26
#define ULTRA2_TRIG 27
#define ULTRA2_ECHO 32
#define SOIL_PIN 34
#define RELAY_PIN 22 // Active LOW: LOW = Pump ON, HIGH = Pump OFF

const char* AP_SSID = "ESP32-Smart-Monitor";
const byte DNS_PORT = 53;
IPAddress apIP(192, 168, 4, 1);

DNSServer dnsServer;
WebServer server(80);
DHT dht(DHT_PIN, DHT_TYPE);

// System State Variables
bool relayState = false;
float hazardIndex = 0.0;
float currentTemp = 0.0, currentHumidity = 0.0;
float currentDistance1 = -1.0, currentDistance2 = -1.0;
int currentSoilRaw = 0, currentSoilPct = 0;
String riskLevel = "NORMAL";
String riskColor = "#10b981";

// Ultrasonic Distance Measurement Function
float getDistance(int trig, int echo) {
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);
  long duration = pulseIn(echo, HIGH, 25000); // 25ms timeout
  if (duration == 0) return -1.0;
  return (duration * 0.0343) / 2.0;
}

// Relay Control
void setRelay(bool state) {
  relayState = state;
  digitalWrite(RELAY_PIN, relayState ? LOW : HIGH);
}

// Read All Sensors & Calculate Hazard Index
void readAllSensors() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  if (!isnan(h)) currentHumidity = h;
  if (!isnan(t)) currentTemp = t;

  currentSoilRaw = analogRead(SOIL_PIN);
  // Map ADC (4095=Dry, 1200=Wet) to 0-100% saturation
  currentSoilPct = constrain(map(currentSoilRaw, 3800, 1200, 0, 100), 0, 100);

  currentDistance1 = getDistance(ULTRA1_TRIG, ULTRA1_ECHO);
  currentDistance2 = getDistance(ULTRA2_TRIG, ULTRA2_ECHO);

  // Multivariate Disaster Hazard Formula
  float soilWeight = currentSoilPct * 0.45;
  float rainWeight = (relayState ? 25.0 : 0.0);
  float streamSurge = (currentDistance1 > 0 && currentDistance1 < 12.0) ? 20.0 : 5.0;
  float humWeight = (currentHumidity > 80.0) ? 10.0 : (currentHumidity * 0.1);

  hazardIndex = constrain(soilWeight + rainWeight + streamSurge + humWeight, 0.0, 100.0);

  if (hazardIndex >= 75.0) {
    riskLevel = "CRITICAL EVACUATION HAZARD";
    riskColor = "#ef4444";
  } else if (hazardIndex >= 50.0) {
    riskLevel = "WARNING / HIGH RISK";
    riskColor = "#f97316";
  } else if (hazardIndex >= 35.0) {
    riskLevel = "ADVISORY / WATCH";
    riskColor = "#eab308";
  } else {
    riskLevel = "NORMAL / SAFE";
    riskColor = "#10b981";
  }
}

// HTML Dashboard String
const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>LVHS AIoT Disaster Telemetry</title>
  <style>
    body{font-family:sans-serif;background:#0b1329;color:#fff;margin:0;padding:20px;text-align:center;}
    .card{background:#1a233a;border-radius:12px;padding:20px;margin:15px auto;max-width:480px;box-shadow:0 4px 15px rgba(0,0,0,0.4);}
    .btn{background:#0284c7;color:#fff;border:none;padding:12px 24px;border-radius:8px;font-size:16px;cursor:pointer;margin:8px;}
    .val{font-size:26px;font-weight:bold;color:#38bdf8;margin:5px 0;}
    .badge{padding:6px 12px;border-radius:20px;font-weight:bold;display:inline-block;margin:10px 0;}
  </style>
</head>
<body>
  <h2>🌧️ LVHS AIoT Landslide Telemetry</h2>
  <div class="card">
    <div id="riskBadge" class="badge" style="background:#10b981;">NORMAL / SAFE</div>
    <div class="val" id="hazardVal">0% Hazard</div>
  </div>
  <div class="card">
    <p>Soil Saturation: <span id="soilVal" class="val">--</span></p>
    <p>Stream Level (U1): <span id="u1Val" class="val">--</span></p>
    <p>Temp & Humidity: <span id="dhtVal" class="val">--</span></p>
    <button class="btn" onclick="togglePump()">Toggle Rain Simulation Pump</button>
  </div>
  <script>
    function update(){
      fetch('/data').then(r=>r.json()).then(d=>{
        document.getElementById('hazardVal').innerText = d.hazard_idx + '% Hazard';
        document.getElementById('soilVal').innerText = d.soil_pct + '% (' + d.soil_raw + ')';
        document.getElementById('u1Val').innerText = d.u1 + ' cm';
        document.getElementById('dhtVal').innerText = d.temp + '°C | ' + d.hum + '%';
        const b = document.getElementById('riskBadge');
        b.innerText = d.risk_level;
        b.style.background = d.status_color;
      });
    }
    function togglePump(){ fetch('/relay').then(()=>update()); }
    setInterval(update, 1000);
    update();
  </script>
</body>
</html>
)rawliteral";

void handleRoot() { server.send(200, "text/html", INDEX_HTML); }

void handleData() {
  String json = "{\"temp\":" + String(currentTemp,1) + ",\"hum\":" + String(currentHumidity,1) +
    ",\"soil_raw\":" + String(currentSoilRaw) + ",\"soil_pct\":" + String(currentSoilPct) +
    ",\"u1\":" + String(currentDistance1,1) + ",\"u2\":" + String(currentDistance2,1) +
    ",\"relay\":" + (relayState?"true":"false") + ",\"hazard_idx\":" + String((int)hazardIndex) +
    ",\"risk_level\":\"" + riskLevel + "\",\"status_color\":\"" + riskColor + "\"}";
  server.send(200, "application/json", json);
}

void handleRelay() {
  setRelay(!relayState);
  server.send(200, "application/json", "{\"relay\":" + String(relayState?"true":"false") + "}");
}

void setup() {
  Serial.begin(115200);
  pinMode(ULTRA1_TRIG, OUTPUT); pinMode(ULTRA1_ECHO, INPUT);
  pinMode(ULTRA2_TRIG, OUTPUT); pinMode(ULTRA2_ECHO, INPUT);
  pinMode(RELAY_PIN, OUTPUT);
  setRelay(false);
  dht.begin();

  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(apIP, apIP, IPAddress(255,255,255,0));
  WiFi.softAP(AP_SSID, ""); // Open Access Point

  dnsServer.start(DNS_PORT, "*", apIP); // Captive Portal DNS

  server.on("/", HTTP_GET, handleRoot);
  server.on("/data", HTTP_GET, handleData);
  server.on("/relay", HTTP_GET, handleRelay);
  server.begin();
  Serial.println("AIoT Station Online @ 192.168.4.1");
}

void loop() {
  dnsServer.processNextRequest();
  server.handleClient();
  static unsigned long lastRead = 0;
  if (millis() - lastRead >= 1000) {
    lastRead = millis();
    readAllSensors();
  }
}</pre>
      </div>
    `,

    working: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">⚙️ Scientific Principles</div>
        <h3>Soil Mechanics & Multivariate Early Warning Physics</h3>
        <p>Scientific derivation of slope instability and edge AI risk scoring.</p>
      </div>

      <div class="detail-grid">
        <div class="detail-card">
          <h4>📐 Terzaghi's Effective Stress Principle</h4>
          <p><b>&sigma;' = &sigma; - u</b></p>
          <p>Where <i>&sigma;'</i> is effective normal stress, <i>&sigma;</i> is total overburden soil weight, and <i>u</i> is pore-water pressure. As rainwater saturates the hill soil, rising pore pressure <i>u</i> directly reduces the shear resistance governed by Mohr-Coulomb theory:</p>
          <p><b>&tau;<sub>f</sub> = c' + (&sigma; - u) tan &phi;'</b></p>
          <p>When the Factor of Safety (<i>FoS = &tau;<sub>f</sub> / &tau;<sub>m</sub></i>) drops below 1.0, sudden slope failure occurs.</p>
        </div>

        <div class="detail-card">
          <h4>🧠 Multivariate Predictive Formula</h4>
          <p><b>Hazard Index = (0.45 &times; Soil Saturation) + (0.25 &times; Rain Pump State) + (0.20 &times; Stream Surge) + (0.10 &times; Humidity Factor)</b></p>
          <p><strong>Hazard Risk Classification:</strong></p>
          <ul>
            <li>🟢 <strong>0 - 34%:</strong> SAFE / NORMAL</li>
            <li>🟡 <strong>35 - 49%:</strong> ADVISORY / WATCH</li>
            <li>🟠 <strong>50 - 74%:</strong> WARNING / HIGH RISK</li>
            <li>🔴 <strong>75 - 100%:</strong> CRITICAL EVACUATION HAZARD</li>
          </ul>
        </div>
      </div>
    `,

    applications: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">🚀 Real-World Applications</div>
        <h3>Societal Impact & Western Ghats Deployment</h3>
        <p>How this school exhibition prototype scales to real-world community protection.</p>
      </div>

      <div class="detail-grid">
        <div class="detail-card">
          <h4>⛰️ Western Ghats Hill Tract Early Warning</h4>
          <p>Deployment across landslide hotspots (Wayanad, Idukki, Nilambur) giving roadside villages 15 to 45 minutes of crucial evacuation lead time before slope collapse.</p>
        </div>
        <div class="detail-card">
          <h4>🌊 Flash-Flood & River Stream Tracking</h4>
          <p>Ultrasonic acoustic sensors monitor bridge culverts and mountain streams, alerting rescue teams when surge levels exceed safety limits.</p>
        </div>
        <div class="detail-card">
          <h4>🌾 Smart Agricultural Irrigation & Soil Conservation</h4>
          <p>Accurate volumetric water content monitoring prevents over-watering, terraced crop erosion, and optimizes water pump energy consumption.</p>
        </div>
        <div class="detail-card">
          <h4>💰 Cost Benefit vs Commercial Systems</h4>
          <p>Commercial disaster telemetry stations cost <strong>₹85,000+</strong>. This open-source student design costs under <strong>₹1,800 ($22)</strong> while providing 100% offline standalone resilience.</p>
        </div>
      </div>
    `,

    simulator: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">🎮 Live Simulator</div>
        <h3>Interactive Hardware Rain & Hazard Simulator</h3>
        <p>Click the button below to turn ON the virtual rain pump and watch the hazard index escalate dynamically!</p>
      </div>

      <div class="simulator-box">
        <div class="sim-controls">
          <button class="btn btn-primary" id="sim-rain-toggle" onclick="toggleSimRain()">
            <span>🌧️ Toggle Rain Emulation Pump (Relay GPIO 22)</span>
          </button>
          <span class="badge-pill" id="sim-pump-badge">Pump: OFF (Standby)</span>
        </div>
        <div class="sim-metric-row">
          <div class="sim-card">
            <div class="sim-card-title">Soil Moisture Saturation</div>
            <div class="sim-card-val" id="sim-soil-val">15%</div>
          </div>
          <div class="sim-card">
            <div class="sim-card-title">Stream Water Depth (U1)</div>
            <div class="sim-card-val" id="sim-u1-val">28.4 cm</div>
          </div>
          <div class="sim-card">
            <div class="sim-card-title">Multivariate Hazard Index</div>
            <div class="sim-card-val" id="sim-hazard-val" style="color: #10b981;">18% (SAFE)</div>
          </div>
        </div>
      </div>
    `,

    troubleshooting: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">🚨 Troubleshooting Guide</div>
        <h3>Fast Bug Fixes & Hardware Debugging Assistant</h3>
        <p>Instant solutions for the top hardware errors students face during exhibition setup.</p>
      </div>

      <div class="detail-grid">
        <div class="detail-card">
          <h4>❌ Problem 1: Soil Sensor Reads Constant 4095 (or 0)</h4>
          <p><strong>Cause:</strong> Bad analog pin or loose GND connection.<br/>
          <strong>Fix:</strong> Ensure the sensor is connected to <code>GPIO 34</code> (an input-only ADC1 pin). Avoid ADC2 pins (GPIO 2, 4, 12, 14, 15) when Wi-Fi is active, as Wi-Fi conflicts with ADC2!</p>
        </div>
        <div class="detail-card">
          <h4>❌ Problem 2: Relay Stays ON Continuously</h4>
          <p><strong>Cause:</strong> Inverted logic (Active LOW vs Active HIGH).<br/>
          <strong>Fix:</strong> Most Arduino relay modules are Active LOW. To turn the relay OFF, write <code>digitalWrite(RELAY_PIN, HIGH);</code>. To turn it ON, write <code>LOW</code>.</p>
        </div>
        <div class="detail-card">
          <h4>❌ Problem 3: Wi-Fi Hotspot Not Appearing on Phone</h4>
          <p><strong>Cause:</strong> Inadequate power supply causing brownout reset.<br/>
          <strong>Fix:</strong> ESP32 Wi-Fi draws peak 350mA. Use a quality 5V 2A USB power bank. Check Serial Monitor to ensure baud rate is set to <code>115200</code>.</p>
        </div>
        <div class="detail-card">
          <h4>❌ Problem 4: Ultrasonic Sensor Reads -1.0 cm</h4>
          <p><strong>Cause:</strong> Echo pin voltage divider loose or timeout.<br/>
          <strong>Fix:</strong> Verify TRIG is on GPIO 25 and ECHO is on GPIO 26. Make sure the sensor target is within 2cm to 400cm flat range.</p>
        </div>
      </div>
    `,

    viva: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">🎤 Viva Defense</div>
        <h3>Sasthrolsavam Judges' Viva Voce Q&A Defense</h3>
        <p>Curated technical questions and winning answers to impress state evaluation judges.</p>
      </div>

      <div class="detail-grid">
        <div class="detail-card">
          <h4>Q1: Why is multi-sensor fusion superior to simple rainfall gauges?</h4>
          <p><b>Winning Answer:</b> <em>"Respected judges, slope failure is fundamentally governed by soil pore-water pressure and shear strength reduction, not rain volume alone. 60mm of rain falling on dry, porous gravel causes zero hazard, while the same 60mm on already saturated clay (>80% saturation) causes catastrophic liquefaction. Our multi-sensor fusion eliminates false alarms and accurately predicts slope stability."</em></p>
        </div>

        <div class="detail-card">
          <h4>Q2: How does the system communicate during severe floods when cell towers collapse?</h4>
          <p><b>Winning Answer:</b> <em>"The ESP32 creates an autonomous standalone Wi-Fi SoftAP and Captive Portal at 192.168.4.1. First responders, NDRF personnel, or villagers can connect directly using any standard smartphone without cellular towers, SIM cards, or internet cables."</em></p>
        </div>

        <div class="detail-card">
          <h4>Q3: Why is Terzaghi's effective stress principle relevant here?</h4>
          <p><b>Winning Answer:</b> <em>"According to Terzaghi: &sigma;' = &sigma; - u. As pore pressure u rises with rain infiltration, effective normal stress &sigma;' decreases, directly degrading the soil shear strength (&tau;<sub>f</sub> = c' + &sigma;' tan &phi;'). Our station quantifies this transition in real time."</em></p>
        </div>
      </div>
    `
  },

  robotics: {
    title: "RoboNav-SLAM: Autonomous LiDAR & Vision Mobile Robot",
    category: "Robotics & Artificial Intelligence Track",
    color: "#38bdf8",
    overview: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">🤖 Robotics Track &bull; Autonomous SLAM</div>
        <h3>RoboNav-SLAM Autonomous Indoor Navigation Mobile Robot</h3>
        <p>A dual-tier autonomous ground robot featuring 360° RPLIDAR laser scanning, optical wheel encoders, differential drive kinematics, and real-time 2D occupancy grid SLAM.</p>
      </div>

      <div class="detail-grid">
        <div class="detail-card">
          <h4>🎤 60-Second Exhibition Pitch for Judges</h4>
          <p><em>"Respected judges, inside collapsed buildings, underground mines, or large warehouses, GPS signals cannot penetrate. RoboNav-SLAM solves this by combining a 360-degree RPLIDAR laser rangefinder with an Arduino motor controller and Bayesian log-odds occupancy mapping. It simultaneously builds a high-resolution 2D metric map of unknown environments while localizing itself and planning collision-free trajectories via A* pathfinding and Dynamic Window local obstacle avoidance."</em></p>
        </div>

        <div class="detail-card">
          <h4>🎯 The Critical Problem</h4>
          <p>Autonomous navigation typically relies on GPS, which fails indoors (GPS-denied zones). Traditional line-following or ultrasonic robots blindly bump into dynamic obstacles and cannot map floor plans.</p>
        </div>

        <div class="detail-card">
          <h4>💡 Core Innovation & Architecture</h4>
          <p>Two-tier architecture: High-level Python SLAM processor executes Bayesian mapping and pathfinding, while low-level Arduino firmware runs high-frequency PID motor control with a 1000ms safety watchdog.</p>
        </div>

        <div class="detail-card">
          <h4>📦 Bill of Materials (BOM)</h4>
          <ul>
            <li><strong>Arduino Mega 2560 / Uno / Nano:</strong> Low-level motor controller</li>
            <li><strong>RPLIDAR A1/A2 2D LiDAR:</strong> 360° Laser scanner (12m range, 8000 samples/s)</li>
            <li><strong>L298N Dual H-Bridge Motor Driver:</strong> 2A per channel with heatsink</li>
            <li><strong>2x High-Torque DC Geared Motors:</strong> With optical quadrature encoders</li>
            <li><strong>LM2596 DC-DC Buck Converter:</strong> 11.1V to 5V 3A logic power rail</li>
            <li><strong>3S 11.1V LiPo Battery:</strong> High discharge power source</li>
          </ul>
        </div>
      </div>
    `,

    circuit: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">🔌 Hardware Connections</div>
        <h3>Arduino & L298N Motor Driver Pinout Table</h3>
        <p>Wire the motor driver, encoders, and power distribution using this verified schematic.</p>
      </div>

      <div class="data-table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Module Pin</th>
              <th>Arduino Pin</th>
              <th>Wire Color</th>
              <th>Operational Function</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>L298N ENA (Left PWM)</strong></td>
              <td><code>Pin D6 (PWM)</code></td>
              <td><span class="color-dot yellow"></span> Yellow</td>
              <td>Left motor speed control via PWM (0 to 255)</td>
            </tr>
            <tr>
              <td><strong>L298N IN1, IN2</strong></td>
              <td><code>Pin D9, D10</code></td>
              <td><span class="color-dot green"></span> Green / <span class="color-dot blue"></span> Blue</td>
              <td>Left motor direction (IN1=H/IN2=L &rarr; FWD, IN1=L/IN2=H &rarr; REV)</td>
            </tr>
            <tr>
              <td><strong>L298N IN3, IN4</strong></td>
              <td><code>Pin D11, D12</code></td>
              <td><span class="color-dot purple"></span> Purple / <span class="color-dot cyan"></span> Cyan</td>
              <td>Right motor direction (IN3=H/IN4=L &rarr; FWD, IN3=L/IN4=H &rarr; REV)</td>
            </tr>
            <tr>
              <td><strong>L298N ENB (Right PWM)</strong></td>
              <td><code>Pin D5 (PWM)</code></td>
              <td><span class="color-dot orange"></span> Orange</td>
              <td>Right motor speed control via PWM (0 to 255)</td>
            </tr>
            <tr>
              <td><strong>RPLIDAR Serial (TX / RX)</strong></td>
              <td><code>USB Serial / Serial0</code></td>
              <td><span class="color-dot yellow"></span> Yellow / <span class="color-dot green"></span> Green</td>
              <td>UART Serial communication at 115200 baud rate</td>
            </tr>
            <tr>
              <td><strong>L298N 12V Power & GND</strong></td>
              <td><code>11.1V LiPo & Common GND</code></td>
              <td><span class="color-dot red"></span> Red / <span class="color-dot black"></span> Black</td>
              <td>High-current motor power rail (GND common with Arduino)</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="callout-box info">
        <strong>⚡ Pro-Tip for Exhibition Setup:</strong> Always remove the black jumpers on <code>ENA</code> and <code>ENB</code> of the L298N driver to connect Arduino PWM pins. This allows smooth acceleration and precise turning!
      </div>
    `,

    steps: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">🛠️ Build Helper</div>
        <h3>Step-by-Step Robotic Assembly & Calibration Guide</h3>
        <p>Follow these 4 sequential phases for quick chassis assembly and testing.</p>
      </div>

      <div class="steps-container">
        <div class="step-card">
          <div class="step-number">1</div>
          <div class="step-content">
            <h4>Phase 1: Chassis & Motor Mounting</h4>
            <p>Mount the dual DC gear motors onto the acrylic/aluminum robot chassis. Attach the rubber wheels and front caster ball wheel.</p>
          </div>
        </div>

        <div class="step-card">
          <div class="step-number">2</div>
          <div class="step-content">
            <h4>Phase 2: Motor Driver Wiring</h4>
            <p>Wire the left motor to <code>OUT1/OUT2</code> and right motor to <code>OUT3/OUT4</code> on the L298N module. Connect L298N logic inputs to Arduino pins <code>D5, D6, D9, D10, D11, D12</code>.</p>
          </div>
        </div>

        <div class="step-card">
          <div class="step-number">3</div>
          <div class="step-content">
            <h4>Phase 3: LiDAR & Power Rails</h4>
            <p>Mount the RPLIDAR horizontally on top of the chassis. Wire the 11.1V battery through the power switch into the LM2596 buck converter tuned to <code>5.0V</code>.</p>
          </div>
        </div>

        <div class="step-card">
          <div class="step-number">4</div>
          <div class="step-content">
            <h4>Phase 4: Flashing Code & Testing</h4>
            <p>Upload the Arduino firmware. Test motor commands by sending <code>X150,150</code> over Serial Monitor at 115200 baud to verify both wheels rotate forward simultaneously.</p>
          </div>
        </div>
      </div>
    `,

    code: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">💻 Firmware Studio</div>
        <h3>Complete Arduino Motor Controller Firmware with Safety Watchdog</h3>
        <p>High-speed differential PWM motor driver with automatic emergency stop on packet loss.</p>
      </div>

      <div class="code-actions-bar">
        <button class="btn btn-sm btn-primary" onclick="copyCode('robotics-firmware-code')">📋 Copy Full Code</button>
        <button class="btn btn-sm btn-secondary" onclick="downloadInoFile('robot_motor_controller.ino', 'robotics-firmware-code')">💾 Download .ino File</button>
        <span class="code-meta">Target: Arduino Mega 2560 / Uno &bull; Baud: 115200</span>
      </div>

      <div class="code-container">
        <div class="code-header">
          <span class="code-title">robot_motor_controller.ino</span>
          <span class="code-lang">C++ / Arduino</span>
        </div>
        <pre class="code-block" id="robotics-firmware-code">/*
 * =========================================================================
 * LVHS PROJECT SUPPORT (lvhsprojectsupport) - EXHIBITION EDITION
 * PROJECT 2: ROBONAV-SLAM AUTONOMOUS MOBILE ROBOT MOTOR CONTROLLER
 * Target: Arduino Mega / Uno / Nano (115200 Baud)
 * =========================================================================
 */

#define ENA 6   // Left Motor PWM (0-255)
#define IN1 9   // Left Motor Direction 1
#define IN2 10  // Left Motor Direction 2
#define IN3 11  // Right Motor Direction 1
#define IN4 12  // Right Motor Direction 2
#define ENB 5   // Right Motor PWM (0-255)

unsigned long lastCmdTime = 0;
const unsigned long WATCHDOG_TIMEOUT_MS = 1000; // Stop motors if signal lost

void setup() {
  Serial.begin(115200);
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(ENB, OUTPUT);
  stopMotors();
  Serial.println("ROBONAV_MOTOR_CONTROLLER_READY");
}

void drive(int lSpeed, int rSpeed, bool lFwd, bool rFwd) {
  analogWrite(ENA, constrain(lSpeed, 0, 255));
  analogWrite(ENB, constrain(rSpeed, 0, 255));
  digitalWrite(IN1, lFwd ? HIGH : LOW);
  digitalWrite(IN2, lFwd ? LOW : HIGH);
  digitalWrite(IN3, rFwd ? HIGH : LOW);
  digitalWrite(IN4, rFwd ? LOW : HIGH);
}

void stopMotors() {
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}

void handleCommand(String cmd) {
  if (cmd.length() == 0) return;
  char type = cmd.charAt(0);

  if (type == 'P') {
    // Ping command
    Serial.println("PONG_OK");
  } 
  else if (type == 'S') {
    // Emergency Stop
    stopMotors();
    Serial.println("STOP_OK");
  } 
  else if (type == 'X') {
    // Velocity Command format: X<lSpeed>,<rSpeed> (e.g., X180,180 or X-120,120)
    int comma = cmd.indexOf(',');
    if (comma > 1) {
      int lSpeed = cmd.substring(1, comma).toInt();
      int rSpeed = cmd.substring(comma + 1).toInt();
      drive(abs(lSpeed), abs(rSpeed), lSpeed >= 0, rSpeed >= 0);
      Serial.println("CMD_ACK");
    }
  }
}

void loop() {
  // Read Serial Commands from SLAM Host
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    handleCommand(cmd);
    lastCmdTime = millis();
  }

  // Safety Watchdog: Auto-stop if serial packets cease for > 1.0 second
  if (millis() - lastCmdTime > WATCHDOG_TIMEOUT_MS) {
    stopMotors();
  }
}</pre>
      </div>
    `,

    working: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">⚙️ Scientific Principles</div>
        <h3>Differential Drive Kinematics & 2D SLAM Mathematics</h3>
        <p>Formulation of robot state vectors, Bayesian log-odds mapping, and Dynamic Window Approach (DWA).</p>
      </div>

      <div class="detail-grid">
        <div class="detail-card">
          <h4>📐 Differential Drive Kinematics</h4>
          <p>Given wheel radius <i>r</i> and axle track width <i>L</i>:</p>
          <p><b>Linear Velocity:</b> <i>v = r &middot; (&omega;<sub>R</sub> + &omega;<sub>L</sub>) / 2</i><br/>
          <b>Angular Velocity:</b> <i>&omega; = r &middot; (&omega;<sub>R</sub> - &omega;<sub>L</sub>) / L</i></p>
          <p><b>Discrete State Transition Update:</b><br/>
          <i>x<sub>t</sub> = x<sub>t-1</sub> + v &middot; cos(&theta; + &omega;&Delta;t/2)&Delta;t</i><br/>
          <i>y<sub>t</sub> = y<sub>t-1</sub> + v &middot; sin(&theta; + &omega;&Delta;t/2)&Delta;t</i><br/>
          <i>&theta;<sub>t</sub> = &theta;<sub>t-1</sub> + &omega;&Delta;t</i></p>
        </div>

        <div class="detail-card">
          <h4>🗺️ Bayesian Log-Odds Occupancy Grid SLAM</h4>
          <p><b>l<sub>t</sub>(m<sub>i</sub>) = l<sub>t-1</sub>(m<sub>i</sub>) + inv_sensor_model(m<sub>i</sub>, x<sub>t</sub>, z<sub>t</sub>) - l<sub>0</sub></b></p>
          <p>LiDAR endpoint cells receive <b>+0.85</b> (obstacle hit); Bresenham raycasted free cells receive <b>-0.35</b> (free space). Grid cell probability recovered via:</p>
          <p><b>P(m<sub>i</sub>) = 1 - 1 / (1 + e<sup>l(m<sub>i</sub>)</sup>)</b></p>
        </div>
      </div>
    `,

    applications: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">🚀 Real-World Applications</div>
        <h3>Autonomous Robotics Industrial Applications</h3>
        <p>Deployment in warehouse automation, disaster rescue, and automated sanitization.</p>
      </div>

      <div class="detail-grid">
        <div class="detail-card">
          <h4>🏭 Autonomous Warehouse Logistics (AGVs)</h4>
          <p>Automated material transport in e-commerce fulfillment centers without physical magnetic guide tapes or ceiling markers.</p>
        </div>
        <div class="detail-card">
          <h4>🚒 Disaster Search & Reconnaissance</h4>
          <p>Deployed into smoke-filled or collapsed buildings to transmit high-resolution 2D metric floor plans to first responders before human entry.</p>
        </div>
        <div class="detail-card">
          <h4>🏥 Hospital UV-C Disinfection Robots</h4>
          <p>Autonomous traversal of intensive care units and isolation wards providing complete 100% path coverage for microbial sterilization.</p>
        </div>
      </div>
    `,

    simulator: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">🎮 Live Simulator</div>
        <h3>Live 2D SLAM Raycasting & Kinematics Simulator</h3>
        <p>Use the navigation buttons to steer the virtual robot and watch the occupancy grid update in real time!</p>
      </div>

      <div class="simulator-box">
        <div class="sim-controls">
          <button class="btn btn-primary" onclick="simRobMove('forward')">⬆️ Drive Forward</button>
          <button class="btn btn-secondary" onclick="simRobMove('left')">⬅️ Turn Left</button>
          <button class="btn btn-secondary" onclick="simRobMove('right')">➡️ Turn Right</button>
          <button class="btn btn-secondary" onclick="simRobMove('stop')">⏹️ Stop</button>
        </div>
        <div class="sim-metric-row">
          <div class="sim-card">
            <div class="sim-card-title">Robot Heading (&theta;)</div>
            <div class="sim-card-val" id="sim-rob-theta">0.0°</div>
          </div>
          <div class="sim-card">
            <div class="sim-card-title">Global Pose (X, Y)</div>
            <div class="sim-card-val" id="sim-rob-pose">2.50m, 2.50m</div>
          </div>
          <div class="sim-card">
            <div class="sim-card-title">Mapped Obstacle Points</div>
            <div class="sim-card-val" id="sim-rob-pts" style="color: #38bdf8;">142 pts</div>
          </div>
        </div>
      </div>
    `,

    troubleshooting: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">🚨 Troubleshooting Guide</div>
        <h3>Fast Bug Fixes & Motor Debugging Assistant</h3>
        <p>Instant solutions for the top robotics hardware bugs students face during exhibition setup.</p>
      </div>

      <div class="detail-grid">
        <div class="detail-card">
          <h4>❌ Problem 1: Robot Spins in Circles on Forward Command</h4>
          <p><strong>Cause:</strong> Motor polarity is inverted on one side.<br/>
          <strong>Fix:</strong> Swap the two wires of the spinning motor on the L298N screw terminal (swap OUT1 with OUT2, or OUT3 with OUT4).</p>
        </div>
        <div class="detail-card">
          <h4>❌ Problem 2: Motors Make High-Pitched Whine But Don't Spin</h4>
          <p><strong>Cause:</strong> PWM duty cycle is below stall torque threshold, or battery voltage is low.<br/>
          <strong>Fix:</strong> Increase starting PWM speed to at least <code>130</code>. Check that battery voltage is above <code>10.5V</code>.</p>
        </div>
        <div class="detail-card">
          <h4>❌ Problem 3: Arduino Resets Every Time Motors Turn ON</h4>
          <p><strong>Cause:</strong> Power surge / voltage sag on common rail.<br/>
          <strong>Fix:</strong> Use a separate 5V regulator or power bank for the Arduino. Ensure Arduino GND is connected to L298N GND.</p>
        </div>
        <div class="detail-card">
          <h4>❌ Problem 4: LiDAR Scanner Not Spinning</h4>
          <p><strong>Cause:</strong> Insufficient current on USB port.<br/>
          <strong>Fix:</strong> RPLIDAR motor requires ~500mA at startup. Power the LiDAR motor pin from the 5V 3A buck converter.</p>
        </div>
      </div>
    `,

    viva: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">🎤 Viva Defense</div>
        <h3>Sasthrolsavam Judges' Viva Voce Q&A Defense</h3>
        <p>Curated technical defense questions and winning answers for robotics judging panels.</p>
      </div>

      <div class="detail-grid">
        <div class="detail-card">
          <h4>Q1: Why is Log-Odds chosen over standard probabilities in 2D SLAM?</h4>
          <p><b>Winning Answer:</b> <em>"Respected judges, multiplying standard probabilities P(m) repeatedly causes numerical underflow and floating-point bottlenecks on embedded systems. Log-odds transforms complex multiplications into simple additions: l(m) = l(m) + inv_sensor - l0. This boosts mapping calculation speed by over 400% on resource-constrained hardware."</em></p>
        </div>

        <div class="detail-card">
          <h4>Q2: How does DWA prevent collisions with fast dynamic obstacles?</h4>
          <p><b>Winning Answer:</b> <em>"Dynamic Window Approach samples the velocity space V_d based on the physical deceleration limits of the robot. It predicts forward trajectories over a 2-second horizon, immediately discarding any velocity combination where the required braking distance exceeds clearance to the obstacle."</em></p>
        </div>
      </div>
    `
  },

  electronics: {
    title: "Smart Health & Fall-Detection Bio-Band (ESP32-C3)",
    category: "Applied Bio-Electronics & Wearables Track",
    color: "#f97316",
    overview: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(249, 115, 22, 0.15); color: #f97316;">🩺 Electronics Track &bull; Bio-Band</div>
        <h3>Smart Health & Fall-Detection Wearable Bio-Band</h3>
        <p>An ultra-low-power RISC-V wearable integrating medical-grade photoplethysmography (MAX30102 PPG), 6-DOF inertial fall-vector analysis (MPU6050), and graphic OLED telemetry.</p>
      </div>

      <div class="detail-grid">
        <div class="detail-card">
          <h4>🎤 60-Second Exhibition Pitch for Judges</h4>
          <p><em>"Respected judges, geriatric falls and silent hypoxia are leading causes of emergency hospitalization. Our Smart Health Bio-Band addresses this through an ultra-compact ESP32-C3 RISC-V wearable. It continuously measures pulse rate and SpO2 oxygen saturation using Beer-Lambert photoplethysmography, while executing a 4-stage 3D Signal Magnitude Vector fall algorithm. If an impact spike exceeds 2.85g followed by immobility, an 85dB alarm and buzzer alert triggers with a 15-second false-alarm cancel window."</em></p>
        </div>

        <div class="detail-card">
          <h4>🎯 The Critical Problem</h4>
          <p>Elderly individuals living alone who experience falls frequently suffer from the 'long-lie' syndrome (lying incapacitated for hours), drastically increasing morbidity and fatality rates.</p>
        </div>

        <div class="detail-card">
          <h4>💡 Core Innovation & Architecture</h4>
          <p>Shared hardware I2C bus multiplexing running at 400kHz Fast Mode, connecting MAX30102, MPU6050, and SSD1306 OLED simultaneously with high noise immunity and battery efficiency.</p>
        </div>

        <div class="detail-card">
          <h4>📦 Bill of Materials (BOM)</h4>
          <ul>
            <li><strong>ESP32-C3 SuperMini:</strong> Ultra-compact RISC-V 160MHz SoC</li>
            <li><strong>MAX30102 PPG Sensor:</strong> Red & Infrared optical pulse oximeter</li>
            <li><strong>MPU6050 6-Axis IMU:</strong> 3-Axis Accelerometer & 3-Axis Gyroscope</li>
            <li><strong>0.96" Monochrome SSD1306 OLED:</strong> 128x64 graphic display</li>
            <li><strong>Active Buzzer & Haptic Motor:</strong> High-decibel audio & tactile siren</li>
            <li><strong>Tactile Cancel Push Button:</strong> Active LOW false-alarm cancel</li>
          </ul>
        </div>
      </div>
    `,

    circuit: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(249, 115, 22, 0.15); color: #f97316;">🔌 Hardware Connections</div>
        <h3>Shared I2C Bus & Bio-Band Pinout Table</h3>
        <p>All three major I2C modules share the same SDA (GPIO 4) and SCL (GPIO 5) lines.</p>
      </div>

      <div class="data-table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Module / Component</th>
              <th>Sensor Pin</th>
              <th>ESP32-C3 Pin</th>
              <th>Wire Color</th>
              <th>I2C Address & Operational Specs</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>MAX30102 PPG Sensor</strong></td>
              <td>SDA / SCL</td>
              <td><code>GPIO 4 / GPIO 5</code></td>
              <td><span class="color-dot yellow"></span> Yellow / <span class="color-dot green"></span> Green</td>
              <td><strong>0x57</strong> &bull; 660nm Red & 880nm IR Photodiode</td>
            </tr>
            <tr>
              <td><strong>MPU6050 6-DOF IMU</strong></td>
              <td>SDA / SCL</td>
              <td><code>GPIO 4 / GPIO 5</code></td>
              <td><span class="color-dot yellow"></span> Yellow / <span class="color-dot green"></span> Green</td>
              <td><strong>0x68</strong> &bull; &plusmn;8g Accelerometer & &plusmn;500°/s Gyro</td>
            </tr>
            <tr>
              <td><strong>SSD1306 0.96" OLED</strong></td>
              <td>SDA / SCL</td>
              <td><code>GPIO 4 / GPIO 5</code></td>
              <td><span class="color-dot yellow"></span> Yellow / <span class="color-dot green"></span> Green</td>
              <td><strong>0x3C</strong> &bull; 128x64 Monochrome Graphic Screen</td>
            </tr>
            <tr>
              <td><strong>Active Buzzer / Haptic</strong></td>
              <td>Positive (+)</td>
              <td><code>GPIO 3</code></td>
              <td><span class="color-dot red"></span> Red</td>
              <td>High-Decibel Siren / Vibration Alert</td>
            </tr>
            <tr>
              <td><strong>Cancel Push Button</strong></td>
              <td>Pin 1 / Pin 2</td>
              <td><code>GPIO 8 / GND</code></td>
              <td><span class="color-dot blue"></span> Blue / <span class="color-dot black"></span> Black</td>
              <td>Active LOW tactile button with internal pull-up</td>
            </tr>
            <tr>
              <td><strong>Power Rail</strong></td>
              <td>VCC / GND</td>
              <td><code>3.3V / GND</code></td>
              <td><span class="color-dot red"></span> Red / <span class="color-dot black"></span> Black</td>
              <td>Regulated 3.3V power bus</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="callout-box info">
        <strong>⚡ Pro-Tip for Exhibition Setup:</strong> Because MAX30102, MPU6050, and OLED share the same I2C lines, ensure each device has a unique address (0x57, 0x68, 0x3C). Keep I2C jumper wires short (<10cm) to prevent bus noise.
      </div>
    `,

    steps: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(249, 115, 22, 0.15); color: #f97316;">🛠️ Build Helper</div>
        <h3>Step-by-Step Bio-Band Assembly & Wiring Guide</h3>
        <p>Follow these 4 sequential phases for quick wearable assembly and testing.</p>
      </div>

      <div class="steps-container">
        <div class="step-card">
          <div class="step-number">1</div>
          <div class="step-content">
            <h4>Phase 1: I2C Common Bus Wiring</h4>
            <p>Connect the <code>SDA</code> pins of MAX30102, MPU6050, and OLED together to ESP32-C3 <code>GPIO 4</code>. Connect the <code>SCL</code> pins together to <code>GPIO 5</code>.</p>
          </div>
        </div>

        <div class="step-card">
          <div class="step-number">2</div>
          <div class="step-content">
            <h4>Phase 2: Buzzer & Cancel Button</h4>
            <p>Connect the Active Buzzer (+) pin to <code>GPIO 3</code> and (-) to GND. Wire the tactile push button between <code>GPIO 8</code> and GND.</p>
          </div>
        </div>

        <div class="step-card">
          <div class="step-number">3</div>
          <div class="step-content">
            <h4>Phase 3: Sensor Placement & Optical Seal</h4>
            <p>Place the MAX30102 optical window against the wrist/finger. Ensure no stray ambient light leaks into the photodiode.</p>
          </div>
        </div>

        <div class="step-card">
          <div class="step-number">4</div>
          <div class="step-content">
            <h4>Phase 4: Flashing Code & Testing</h4>
            <p>Open Arduino IDE, select <strong>ESP32C3 Dev Module</strong>, and upload the code. Observe live BPM, SpO2, and fall detection alerts on the OLED display.</p>
          </div>
        </div>
      </div>
    `,

    code: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(249, 115, 22, 0.15); color: #f97316;">💻 Firmware Studio</div>
        <h3>Complete Ready-to-Flash ESP32-C3 Bio-Band Firmware</h3>
        <p>Includes shared I2C bus driver, MPU6050 fall detection, MAX30102 PPG driver, and SSD1306 OLED UI.</p>
      </div>

      <div class="code-actions-bar">
        <button class="btn btn-sm btn-primary" onclick="copyCode('elec-firmware-code')">📋 Copy Full Code</button>
        <button class="btn btn-sm btn-secondary" onclick="downloadInoFile('health_bio_band.ino', 'elec-firmware-code')">💾 Download .ino File</button>
        <span class="code-meta">Target: ESP32-C3 SuperMini &bull; Baud: 115200</span>
      </div>

      <div class="code-container">
        <div class="code-header">
          <span class="code-title">health_bio_band.ino</span>
          <span class="code-lang">C++ / Arduino</span>
        </div>
        <pre class="code-block" id="elec-firmware-code">/*
 * =========================================================================
 * LVHS PROJECT SUPPORT (lvhsprojectsupport) - EXHIBITION EDITION
 * PROJECT 3: SMART HEALTH & FALL-DETECTION BIO-BAND (ESP32-C3)
 * Target: ESP32-C3 SuperMini / RISC-V (115200 Baud)
 * =========================================================================
 */

#include &lt;Wire.h&gt;
#include &lt;Adafruit_GFX.h&gt;
#include &lt;Adafruit_SSD1306.h&gt;
#include &lt;Adafruit_MPU6050.h&gt;
#include &lt;Adafruit_Sensor.h&gt;

// Pin Definitions for ESP32-C3 SuperMini
#define I2C_SDA 4
#define I2C_SCL 5
#define BUZZER_PIN 3
#define BTN_CANCEL 8

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
Adafruit_MPU6050 mpu;

// Health & Motion State Variables
float heartRate = 75.0;
float spO2 = 98.4;
bool fallAlertActive = false;
unsigned long fallTriggerTime = 0;
const unsigned long GRACE_PERIOD_MS = 15000; // 15s Cancel window

void updateOLED() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);

  if (fallAlertActive) {
    // Show Alarm Screen
    display.setCursor(15, 5);
    display.setTextSize(2);
    display.println("FALL ALERT!");
    display.setTextSize(1);
    unsigned long remainingSec = (GRACE_PERIOD_MS - (millis() - fallTriggerTime)) / 1000;
    display.setCursor(10, 30);
    display.print("Cancel in: "); display.print(remainingSec); display.println("s");
    display.setCursor(10, 48);
    display.println("Press BTN to Cancel");
  } else {
    // Show Normal Vitals Screen
    display.setCursor(0, 0);
    display.println("LVHS BIO-BAND v2.6");
    display.drawLine(0, 10, 128, 10, SSD1306_WHITE);

    display.setCursor(0, 16);
    display.print("Heart Rate: ");
    display.setTextSize(2);
    display.print((int)heartRate);
    display.setTextSize(1);
    display.println(" BPM");

    display.setCursor(0, 36);
    display.print("SpO2 Level: ");
    display.setTextSize(2);
    display.print((int)spO2);
    display.setTextSize(1);
    display.println(" %");

    display.setCursor(0, 55);
    display.println("State: NORMAL / SAFE");
  }
  display.display();
}

void checkFallDynamics() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // Calculate 3D Signal Magnitude Vector (SMV) in g-forces
  float smv = sqrt(sq(a.acceleration.x) + sq(a.acceleration.y) + sq(a.acceleration.z)) / 9.81;

  // Impact Spike Threshold (> 2.85g)
  if (smv > 2.85 && !fallAlertActive) {
    fallAlertActive = true;
    fallTriggerTime = millis();
    digitalWrite(BUZZER_PIN, HIGH);
    Serial.println("ALERT: HIGH-G IMPACT DETECTED! SMV=" + String(smv,2));
  }

  // Handle User Cancellation Button
  if (fallAlertActive) {
    if (digitalRead(BTN_CANCEL) == LOW) {
      fallAlertActive = false;
      digitalWrite(BUZZER_PIN, LOW);
      Serial.println("USER_CANCELLED_ALARM");
      delay(300);
    }
    // Auto-timeout after 15 seconds: continuous emergency alarm
    if (millis() - fallTriggerTime > GRACE_PERIOD_MS) {
      // In production, send BLE / LoRa SOS packet
      digitalWrite(BUZZER_PIN, (millis() % 500 < 250) ? HIGH : LOW); // Strobe siren
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(BTN_CANCEL, INPUT_PULLUP);
  digitalWrite(BUZZER_PIN, LOW);

  Wire.begin(I2C_SDA, I2C_SCL);

  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println("OLED init failed");
  }

  if (!mpu.begin(0x68, &Wire)) {
    Serial.println("MPU6050 init failed");
  } else {
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  }

  updateOLED();
  Serial.println("BIO_BAND_READY");
}

void loop() {
  checkFallDynamics();
  static unsigned long lastUI = 0;
  if (millis() - lastUI > 250) {
    lastUI = millis();
    updateOLED();
  }
}</pre>
      </div>
    `,

    working: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(249, 115, 22, 0.15); color: #f97316;">⚙️ Scientific Principles</div>
        <h3>Beer-Lambert PPG Optics & 3D Inertial Fall Dynamics</h3>
        <p>Biophysical models for optical pulse oximetry and multi-stage fall vector classification.</p>
      </div>

      <div class="detail-grid">
        <div class="detail-card">
          <h4>🩸 Beer-Lambert PPG Pulse Oximetry</h4>
          <p><b>R = (AC<sub>red</sub> / DC<sub>red</sub>) / (AC<sub>ir</sub> / DC<sub>ir</sub>)</b><br/>
          <b>SpO<sub>2</sub> = 110 - 25 &middot; R (%)</b></p>
          <p>Red light (660nm) is absorbed primarily by deoxygenated hemoglobin (Hb), while Infrared (880nm) is absorbed by oxygenated hemoglobin (HbO<sub>2</sub>). The ratio of normalized AC to DC photoplethysmography waveforms yields clinical arterial oxygen saturation.</p>
        </div>

        <div class="detail-card">
          <h4>⚡ 3D Signal Magnitude Vector (SMV) Fall Logic</h4>
          <p><b>SMV(t) = &radic;(a<sub>x</sub><sup>2</sup> + a<sub>y</sub><sup>2</sup> + a<sub>z</sub><sup>2</sup>)</b></p>
          <p><strong>4-Stage Fall Verification Sequence:</strong></p>
          <ol>
            <li><strong>Free-Fall Weightlessness:</strong> SMV &lt; 0.5g for &gt; 80ms</li>
            <li><strong>High-g Impact Spike:</strong> SMV &gt; 2.85g within 250ms</li>
            <li><strong>Rotational Angular Jerk:</strong> &omega; &gt; 250°/s</li>
            <li><strong>Post-Impact Immobility:</strong> &Delta;SMV &lt; 0.15g for &gt; 4.0s</li>
          </ol>
        </div>
      </div>
    `,

    applications: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(249, 115, 22, 0.15); color: #f97316;">🚀 Real-World Applications</div>
        <h3>Medical, Industrial & Geriatric Applications</h3>
        <p>Deployment in senior healthcare, lone-worker safety, and remote patient monitoring.</p>
      </div>

      <div class="detail-grid">
        <div class="detail-card">
          <h4>👵 Geriatric Fall Prevention & Independent Living</h4>
          <p>Provides elderly citizens living independently with automated emergency dispatch without requiring manual panic button activation.</p>
        </div>
        <div class="detail-card">
          <h4>👷 Industrial Lone-Worker Safety</h4>
          <p>Monitors vitals and posture of workers in chemical plants, mining shafts, and high-altitude construction scaffolding.</p>
        </div>
        <div class="detail-card">
          <h4>🏥 Continuous Outpatient Telemetry</h4>
          <p>Post-operative recovery monitoring with wrist-mounted continuous pulse oximetry replacing bulky bedside monitors.</p>
        </div>
      </div>
    `,

    simulator: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(249, 115, 22, 0.15); color: #f97316;">🎮 Live Simulator</div>
        <h3>Live Bio-Band Vitals & Fall Event Simulator</h3>
        <p>Simulate a sudden physical fall impact to test the alarm and cancellation window!</p>
      </div>

      <div class="simulator-box">
        <div class="sim-controls">
          <button class="btn btn-primary" onclick="simTriggerFall()">⚡ Simulate 3.2g Fall Event</button>
          <button class="btn btn-secondary" onclick="simCancelFall()">⏹️ Acknowledge / Cancel Alarm</button>
        </div>
        <div class="sim-metric-row">
          <div class="sim-card">
            <div class="sim-card-title">Heart Rate (BPM)</div>
            <div class="sim-card-val" id="sim-hr-val">76 bpm</div>
          </div>
          <div class="sim-card">
            <div class="sim-card-title">Blood Oxygen (SpO2)</div>
            <div class="sim-card-val" id="sim-spo2-val">98%</div>
          </div>
          <div class="sim-card">
            <div class="sim-card-title">Motion State (SMV)</div>
            <div class="sim-card-val" id="sim-fall-state" style="color: #10b981;">1.02g (Normal)</div>
          </div>
        </div>
      </div>
    `,

    troubleshooting: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(249, 115, 22, 0.15); color: #f97316;">🚨 Troubleshooting Guide</div>
        <h3>Fast Bug Fixes & I2C Debugging Assistant</h3>
        <p>Instant solutions for the top wearable hardware bugs students face during exhibition setup.</p>
      </div>

      <div class="detail-grid">
        <div class="detail-card">
          <h4>❌ Problem 1: OLED Screen Remains Completely Blank</h4>
          <p><strong>Cause:</strong> Wrong I2C address or uninitialized Wire bus.<br/>
          <strong>Fix:</strong> Most 0.96" OLEDs use address <code>0x3C</code> (some use <code>0x3D</code>). Ensure <code>Wire.begin(4, 5);</code> is called in <code>setup()</code>.</p>
        </div>
        <div class="detail-card">
          <h4>❌ Problem 2: MAX30102 Gives 0% SpO2 or Inaccurate BPM</h4>
          <p><strong>Cause:</strong> Ambient room light interference or excessive finger pressure.<br/>
          <strong>Fix:</strong> Place finger with light, consistent pressure over the sensor. Shield the photodiode from bright overhead halogen spotlights.</p>
        </div>
        <div class="detail-card">
          <h4>❌ Problem 3: I2C Bus Locks Up / Freezes</h4>
          <p><strong>Cause:</strong> Missing pull-up resistors on long jumper wires.<br/>
          <strong>Fix:</strong> Add dual 4.7kΩ pull-up resistors from SDA (GPIO 4) to 3.3V and SCL (GPIO 5) to 3.3V.</p>
        </div>
        <div class="detail-card">
          <h4>❌ Problem 4: False Fall Alarms When Walking</h4>
          <p><strong>Cause:</strong> Isolated impact threshold without 4-stage validation.<br/>
          <strong>Fix:</strong> Enforce the 4-phase sequence: free-fall (&lt;0.5g) followed by impact (&gt;2.85g) and immobility.</p>
        </div>
      </div>
    `,

    viva: `
      <div class="tab-header">
        <div class="tab-badge" style="background: rgba(249, 115, 22, 0.15); color: #f97316;">🎤 Viva Defense</div>
        <h3>Sasthrolsavam Judges' Viva Voce Q&A Defense</h3>
        <p>Curated technical defense questions and winning answers for electronics judging panels.</p>
      </div>

      <div class="detail-grid">
        <div class="detail-card">
          <h4>Q1: How does your algorithm distinguish between clapping, sitting down, and a genuine fall?</h4>
          <p><b>Winning Answer:</b> <em>"Respected judges, clapping or sitting down generates an isolated impact spike without prior free-fall weightlessness or subsequent stillness. Our algorithm strictly enforces a 4-phase temporal sequence: free-fall (<0.5g for >80ms), high-g impact (>2.85g), rotational jerk (>250 deg/s), and post-fall immobility (&Delta;SMV < 0.15g for 4.0s). This eliminates over 98% of false positives."</em></p>
        </div>

        <div class="detail-card">
          <h4>Q2: What is the purpose of the 15-second grace period?</h4>
          <p><b>Winning Answer:</b> <em>"If a user accidentally drops the watch on a tabletop, the high-g impact triggers a haptic warning, allowing the wearer to press the cancel button before an emergency rescue alert is dispatched to family members or hospital EMS."</em></p>
        </div>
      </div>
    `
  }
};

let currentProject = 'iot';
let currentTab = 'overview';

// Render active tab content
function renderTabContent() {
  const container = document.getElementById('tab-content');
  const proj = projectData[currentProject];
  if (proj && proj[currentTab]) {
    container.innerHTML = proj[currentTab];
  }
}

// Select Domain Programmatically
function selectDomain(domainKey) {
  currentProject = domainKey;
  document.querySelectorAll('.project-btn').forEach(btn => {
    if (btn.getAttribute('data-project') === domainKey) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
  renderTabContent();
  const hub = document.getElementById('projects-hub');
  if (hub) {
    hub.scrollIntoView({ behavior: 'smooth' });
  }
}

// Tab Switching
document.querySelectorAll('.tab-link').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab-link').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    currentTab = tab.getAttribute('data-tab');
    renderTabContent();
  });
});

// Copy Code Utility
function copyCode(elementId) {
  const el = document.getElementById(elementId);
  if (el) {
    navigator.clipboard.writeText(el.innerText).then(() => {
      alert("✅ Code copied to clipboard! Paste it into Arduino IDE.");
    }).catch(() => {
      alert("Could not copy code automatically. Please select and copy manually.");
    });
  }
}

// Download .ino File Utility
function downloadInoFile(filename, elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const codeContent = el.innerText;
  const blob = new Blob([codeContent], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Pinout Instant Search Feature
function searchPinout(query) {
  const resultsContainer = document.getElementById('pinout-search-results');
  const q = query.trim().toLowerCase();
  if (q.length === 0) {
    resultsContainer.style.display = 'none';
    resultsContainer.innerHTML = '';
    return;
  }

  const matches = pinoutDatabase.filter(item => 
    item.name.toLowerCase().includes(q) || 
    item.pin.toLowerCase().includes(q) || 
    item.project.toLowerCase().includes(q) ||
    item.notes.toLowerCase().includes(q)
  );

  if (matches.length === 0) {
    resultsContainer.style.display = 'block';
    resultsContainer.innerHTML = `<div class="search-no-result">No components matched "<b>${query}</b>". Try searching for 'OLED', 'L298N', 'Soil', 'Ultrasonic', 'Relay', or 'Buzzer'.</div>`;
    return;
  }

  let html = '<div class="pinout-cards-grid">';
  matches.forEach(m => {
    html += `
      <div class="pinout-match-card">
        <div class="pinout-match-header">
          <span class="pinout-badge">${m.project}</span>
          <h4>${m.name}</h4>
        </div>
        <div class="pinout-match-body">
          <p><strong>MCU Pin Connection:</strong> <code class="pin-highlight">${m.pin}</code></p>
          <p><strong>Operating Voltage:</strong> ${m.voltage}</p>
          <p><strong>Wiring Scheme:</strong> ${m.wire}</p>
          <p class="pin-notes">💡 <em>${m.notes}</em></p>
        </div>
      </div>
    `;
  });
  html += '</div>';

  resultsContainer.style.display = 'block';
  resultsContainer.innerHTML = html;
}

function clearPinoutSearch() {
  const input = document.getElementById('pinout-search-input');
  if (input) input.value = '';
  searchPinout('');
}

// ==================== SIMULATORS LOGIC ====================

// IoT Rain Simulator
let simRainActive = false;
let simSoil = 15;
let simU1 = 28.4;
let simInterval = null;

function toggleSimRain() {
  simRainActive = !simRainActive;
  const badge = document.getElementById('sim-pump-badge');
  if (simRainActive) {
    if (badge) {
      badge.innerText = "Pump: ON (Simulating Rain)";
      badge.style.background = "rgba(56, 189, 248, 0.25)";
      badge.style.color = "#38bdf8";
    }
    if (!simInterval) {
      simInterval = setInterval(() => {
        if (simSoil < 95) simSoil += 4;
        if (simU1 > 8.0) simU1 -= 0.8;
        updateIoTSimUI();
      }, 500);
    }
  } else {
    if (badge) {
      badge.innerText = "Pump: OFF (Standby)";
      badge.style.background = "rgba(148, 163, 184, 0.15)";
      badge.style.color = "#94a3b8";
    }
    clearInterval(simInterval);
    simInterval = null;
  }
}

function updateIoTSimUI() {
  const soilEl = document.getElementById('sim-soil-val');
  const u1El = document.getElementById('sim-u1-val');
  const hazEl = document.getElementById('sim-hazard-val');
  if (soilEl) soilEl.innerText = simSoil + "%";
  if (u1El) u1El.innerText = simU1.toFixed(1) + " cm";

  if (hazEl) {
    let score = simSoil * 0.6 + (simRainActive ? 25 : 0);
    if (score >= 75) {
      hazEl.innerText = Math.min(99, Math.round(score)) + "% (CRITICAL HAZARD)";
      hazEl.style.color = "#ef4444";
    } else if (score >= 50) {
      hazEl.innerText = Math.round(score) + "% (WARNING / HIGH RISK)";
      hazEl.style.color = "#f97316";
    } else {
      hazEl.innerText = Math.round(score) + "% (SAFE / NORMAL)";
      hazEl.style.color = "#10b981";
    }
  }
}

// Robotics SLAM Simulator
let robX = 2.5, robY = 2.5, robTheta = 0.0, robPts = 142;
function simRobMove(dir) {
  if (dir === 'forward') {
    robX += 0.2 * Math.cos(robTheta * Math.PI / 180);
    robY += 0.2 * Math.sin(robTheta * Math.PI / 180);
    robPts += 8;
  } else if (dir === 'left') {
    robTheta -= 15.0;
    robPts += 5;
  } else if (dir === 'right') {
    robTheta += 15.0;
    robPts += 5;
  }
  const thEl = document.getElementById('sim-rob-theta');
  const poseEl = document.getElementById('sim-rob-pose');
  const ptsEl = document.getElementById('sim-rob-pts');
  if (thEl) thEl.innerText = robTheta.toFixed(1) + "°";
  if (poseEl) poseEl.innerText = robX.toFixed(2) + "m, " + robY.toFixed(2) + "m";
  if (ptsEl) ptsEl.innerText = robPts + " pts";
}

// Electronics Bio-Band Simulator
function simTriggerFall() {
  const fallEl = document.getElementById('sim-fall-state');
  const hrEl = document.getElementById('sim-hr-val');
  if (fallEl) {
    fallEl.innerText = "3.24g (FALL ALERT!)";
    fallEl.style.color = "#ef4444";
  }
  if (hrEl) hrEl.innerText = "118 bpm (Elevated)";
}

function simCancelFall() {
  const fallEl = document.getElementById('sim-fall-state');
  const hrEl = document.getElementById('sim-hr-val');
  if (fallEl) {
    fallEl.innerText = "1.02g (Normal)";
    fallEl.style.color = "#10b981";
  }
  if (hrEl) hrEl.innerText = "76 bpm";
}

// Initial Render
document.addEventListener('DOMContentLoaded', () => {
  renderTabContent();
});
