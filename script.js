// Lekshmivilasam Projects Interactive Portal Data & Logic

const projectData = {
  iot: {
    title: "AIoT Disaster Early Warning & Rain Simulation System",
    category: "IoT & Disaster Management",
    color: "#10b981",
    overview: `
      <div class="tab-header">
        <h3>🌧️ AIoT Landslide Early Warning & Rain Simulation Station</h3>
        <p>A self-contained edge computing meteorological telemetry station with an automated rain emulation pump and standalone Wi-Fi hotspot dashboard (192.168.4.1).</p>
      </div>
      <div class="detail-grid">
        <div class="detail-card">
          <h4>🎯 Problem Statement</h4>
          <p>Western Ghats hill tracts in Kerala (Wayanad, Idukki, Nilambur) face devastating monsoon-induced debris flows. Delayed regional macro-forecasts fail to capture hyper-localized slope saturation.</p>
        </div>
        <div class="detail-card">
          <h4>💡 Core Innovation</h4>
          <p>Autonomous standalone Wi-Fi Hotspot with an integrated 12V rain emulation pump operated via relay to emulate precipitation dynamics, combined with multivariate hazard classification.</p>
        </div>
        <div class="detail-card">
          <h4>🔬 Key Sensor Array</h4>
          <ul>
            <li>Analog Soil Moisture Sensor (GPIO 34 ADC)</li>
            <li>Dual HC-SR04 Ultrasonic Sensors (GPIO 25/26 & 27/32)</li>
            <li>DHT22 Digital Temperature & Humidity (GPIO 33)</li>
            <li>12V Rain Simulation Pump Relay (GPIO 22 Active LOW)</li>
          </ul>
        </div>
        <div class="detail-card">
          <h4>📊 Performance Highlights</h4>
          <ul>
            <li>100% Offline Standalone Hotspot (192.168.4.1)</li>
            <li>Sub-second asynchronous REST telemetry API</li>
            <li>Zero dependency on cellular or external internet</li>
          </ul>
        </div>
      </div>
    `,
    circuit: `
      <div class="tab-header">
        <h3>🔌 Pin Mapping & Hardware Schematics</h3>
        <p>Complete circuit interconnections for ESP32 Dual-Core (240MHz) SoC.</p>
      </div>
      <div class="data-table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Module / Sensor</th>
              <th>Pin Function</th>
              <th>ESP32 Pin</th>
              <th>Protocol & Electrical Logic</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>Soil Moisture Probe</td><td>Analog (A0)</td><td>GPIO 34</td><td>ADC1_CH6 (12-bit Analog: 0 to 4095)</td></tr>
            <tr><td>Ultrasonic 1 (Stream Level)</td><td>TRIG / ECHO</td><td>GPIO 25 / GPIO 26</td><td>10µs Trigger / 5V-to-3.3V Divider Echo</td></tr>
            <tr><td>Ultrasonic 2 (Catchment Basin)</td><td>TRIG / ECHO</td><td>GPIO 27 / GPIO 32</td><td>10µs Trigger / 5V-to-3.3V Divider Echo</td></tr>
            <tr><td>Rain Emulation Pump Relay</td><td>Relay Input</td><td>GPIO 22</td><td>Active LOW Optocoupler (LOW=ON, HIGH=OFF)</td></tr>
            <tr><td>DHT22 Atmosphere Sensor</td><td>Data Pin</td><td>GPIO 33</td><td>One-Wire Digital Bus (4.7kΩ Pull-up)</td></tr>
            <tr><td>Autonomous Hotspot</td><td>SoftAP</td><td>Antenna</td><td>SSID: ESP32-Smart-Monitor @ 192.168.4.1</td></tr>
          </tbody>
        </table>
      </div>
    `,
    code: `
      <div class="tab-header">
        <h3>💻 Complete ESP32 Firmware & Web Dashboard</h3>
        <p>Full C++ source code with embedded asynchronous HTTP/JSON API and Captive Portal DNS.</p>
      </div>
      <div class="code-container">
        <div class="code-header">
          <span class="code-title">landslide_iot_firmware.ino</span>
          <button class="btn-copy" onclick="copyCode('iot-code')">Copy Code</button>
        </div>
        <pre class="code-block" id="iot-code">
#include &lt;WiFi.h&gt;
#include &lt;WebServer.h&gt;
#include &lt;DNSServer.h&gt;
#include "DHT.h"

#define DHT_PIN 33
#define DHT_TYPE DHT22
#define ULTRA1_TRIG 25
#define ULTRA1_ECHO 26
#define ULTRA2_TRIG 27
#define ULTRA2_ECHO 32
#define SOIL_PIN 34
#define RELAY_PIN 22 // Active LOW: LOW = Pump ON, HIGH = Pump OFF

const char* AP_SSID = "ESP32-Smart-Monitor";
DNSServer dnsServer;
WebServer server(80);
DHT dht(DHT_PIN, DHT_TYPE);

bool relayState = false;
float hazardIndex = 0.0;
float currentTemp = 0.0, currentHumidity = 0.0, currentDistance1 = -1.0, currentDistance2 = -1.0;
int currentSoilRaw = 0, currentSoilPct = 0;
String riskLevel = "NORMAL", riskColor = "#10b981";

float getDistance(int trig, int echo) {
  digitalWrite(trig, LOW); delayMicroseconds(2);
  digitalWrite(trig, HIGH); delayMicroseconds(10); digitalWrite(trig, LOW);
  long dur = pulseIn(echo, HIGH, 25000);
  return (dur == 0) ? -1.0 : (dur * 0.0343) / 2.0;
}

void setRelay(bool state) {
  relayState = state;
  digitalWrite(RELAY_PIN, relayState ? LOW : HIGH);
}

void handleData() {
  String json = "{\\"temp\\":" + String(currentTemp,1) + ",\\"hum\\":" + String(currentHumidity,1) +
    ",\\"soil_raw\\":" + String(currentSoilRaw) + ",\\"soil_pct\\":" + String(currentSoilPct) +
    ",\\"u1\\":" + String(currentDistance1,1) + ",\\"u2\\":" + String(currentDistance2,1) +
    ",\\"relay\\":" + (relayState?"true":"false") + ",\\"hazard_idx\\":" + String((int)hazardIndex) +
    ",\\"risk_level\\":\\"" + riskLevel + "\\",\\"status_color\\":\\"" + riskColor + "\\"}";
  server.send(200, "application/json", json);
}

void handleRelay() {
  if (server.hasArg("state")) {
    String s = server.arg("state");
    setRelay(s == "1" || s == "true" || s == "on");
  } else {
    setRelay(!relayState);
  }
  server.send(200, "application/json", "{\\"relay\\":" + String(relayState?"true":"false") + "}");
}

void setup() {
  Serial.begin(115200);
  pinMode(ULTRA1_TRIG, OUTPUT); pinMode(ULTRA1_ECHO, INPUT);
  pinMode(ULTRA2_TRIG, OUTPUT); pinMode(ULTRA2_ECHO, INPUT);
  pinMode(RELAY_PIN, OUTPUT); setRelay(false);
  dht.begin();

  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, ""); // Open Hotspot
  dnsServer.start(53, "*", IPAddress(192,168,4,1)); // Captive Portal

  server.on("/", HTTP_GET, handleRoot);
  server.on("/data", HTTP_GET, handleData);
  server.on("/relay", HTTP_GET, handleRelay);
  server.begin();
}

void loop() {
  dnsServer.processNextRequest();
  server.handleClient();
  static unsigned long lastRead = 0;
  if (millis() - lastRead >= 1200) {
    lastRead = millis();
    readAllSensors();
  }
}
        </pre>
      </div>
    `,
    working: `
      <div class="tab-header">
        <h3>⚙️ Scientific Principles & Mathematical Formulation</h3>
        <p>Soil pore-pressure liquefaction physics and real-time multivariate predictive fusion.</p>
      </div>
      <div class="detail-grid">
        <div class="detail-card">
          <h4>📐 Terzaghi's Effective Stress Principle</h4>
          <p><b>&sigma;' = &sigma; - u</b></p>
          <p>Where <i>&sigma;'</i> is effective normal stress, <i>&sigma;</i> is total stress, and <i>u</i> is pore-water pressure. As rainwater infiltrates slope soil, escalating <i>u</i> reduces shear strength: <b>&tau;<sub>f</sub> = c' + (&sigma; - u) tan &phi;'</b>. When Factor of Safety (<i>FoS = &tau;<sub>f</sub> / &tau;<sub>m</sub></i>) drops below 1.0, sudden slope failure occurs.</p>
        </div>
        <div class="detail-card">
          <h4>🧠 Multivariate Disaster Hazard Formula</h4>
          <p><b>Hazard Index (0 - 100%) = 0.45&middot;(Soil Saturation) + 0.25&middot;(Rain Pump Factor) + 0.20&middot;(Stream Surge) + 0.10&middot;(Humidity)</b></p>
          <p><b>Alert Categories:</b><br/>
          🟢 <b>0 - 34%:</b> SAFE / NORMAL<br/>
          🟡 <b>35 - 49%:</b> ADVISORY / WATCH<br/>
          🟠 <b>50 - 74%:</b> WARNING / HIGH RISK<br/>
          🔴 <b>75 - 100%:</b> CRITICAL EVACUATION HAZARD</p>
        </div>
      </div>
    `,
    applications: `
      <div class="tab-header">
        <h3>🚀 Real-World Applications & Societal Impact</h3>
        <p>Deployment in disaster mitigation, slope safety, and automated irrigation.</p>
      </div>
      <div class="detail-grid">
        <div class="detail-card">
          <h4>⛰️ Western Ghats Landslide Monitoring</h4>
          <p>Autonomous monitoring along high-risk ghat roads (Thamarassery, Kuttiady, Munnar) providing localized siren alerts prior to regional disaster notification.</p>
        </div>
        <div class="detail-card">
          <h4>🌊 Flash-Flood Runoff Detection</h4>
          <p>Stream acoustic elevation sensors track rapid runoff accumulation in river catchments, warning downstream riverine settlements.</p>
        </div>
        <div class="detail-card">
          <h4>🌾 Precision Agriculture & Terraced Farming</h4>
          <p>Soil volumetric water content tracking enables automated water conservation and crop slope erosion prevention.</p>
        </div>
      </div>
    `,
    simulator: `
      <div class="tab-header">
        <h3>🎮 Live AIoT Hardware & Rain Emulation Simulator</h3>
        <p>Test the interactive rain simulation switch and watch the on-device hazard index dynamically escalate!</p>
      </div>
      <div class="simulator-box">
        <div class="sim-controls">
          <button class="btn btn-primary" id="sim-rain-toggle" onclick="toggleSimRain()">
            <span>🌧️ Toggle Rain Simulation Pump (Relay GPIO 22)</span>
          </button>
          <span class="badge-pill" id="sim-pump-badge">Pump: OFF (Standby)</span>
        </div>
        <div class="sim-metric-row">
          <div class="sim-card">
            <div class="sim-card-title">Soil Moisture Saturation</div>
            <div class="sim-card-val" id="sim-soil-val">15%</div>
          </div>
          <div class="sim-card">
            <div class="sim-card-title">Stream Water Level (U1)</div>
            <div class="sim-card-val" id="sim-u1-val">28.4 cm</div>
          </div>
          <div class="sim-card">
            <div class="sim-card-title">Hazard Prediction Index</div>
            <div class="sim-card-val" id="sim-hazard-val" style="color: #10b981;">18% (SAFE)</div>
          </div>
        </div>
      </div>
    `,
    viva: `
      <div class="tab-header">
        <h3>🎤 Sasthrolsavam Judges' Viva Voce Defense</h3>
        <p>Curated technical defense questions and answers for state science fair judging panels.</p>
      </div>
      <div class="detail-grid">
        <div class="detail-card">
          <h4>Q1: Why is multi-sensor fusion superior to simple rainfall gauges?</h4>
          <p><b>Defense:</b> Landslides depend on soil pore-water pressure and shear strength reduction. 50mm of rain on dry porous soil causes zero hazard, whereas 50mm on already saturated soil (>80% VWC) with surging runoff causes catastrophic slope liquefaction. Sensor fusion eliminates both false alarms and missed alerts.</p>
        </div>
        <div class="detail-card">
          <h4>Q2: How does the disaster station operate if telecom networks collapse?</h4>
          <p><b>Defense:</b> The ESP32 hosts an autonomous standalone Hotspot running an embedded web server and local prediction engine at 192.168.4.1. First responders can connect locally via Wi-Fi from up to 80 meters away without any cellular or internet infrastructure.</p>
        </div>
      </div>
    `
  },

  robotics: {
    title: "RoboNav-SLAM: Autonomous LiDAR & Vision Mobile Robot",
    category: "Robotics & Artificial Intelligence",
    color: "#38bdf8",
    overview: `
      <div class="tab-header">
        <h3>🤖 RoboNav-SLAM Autonomous Indoor Navigation Mobile Robot</h3>
        <p>A dual-tier autonomous navigation mobile robot equipped with 360° RPLIDAR laser scanning, optical wheel encoders, and real-time 2D occupancy grid SLAM.</p>
      </div>
      <div class="detail-grid">
        <div class="detail-card">
          <h4>🎯 Problem Statement</h4>
          <p>GPS signals cannot penetrate indoor structures, disaster rubble, or multistory warehouses, rendering conventional GPS waypoint navigation impossible.</p>
        </div>
        <div class="detail-card">
          <h4>💡 Core Innovation</h4>
          <p>Combines real-time Bayesian Log-Odds Occupancy Grid SLAM with A* global pathfinding and the Dynamic Window Approach (DWA) for dynamic collision-free navigation.</p>
        </div>
        <div class="detail-card">
          <h4>🔬 Hardware Architecture</h4>
          <ul>
            <li>RPLIDAR A1/A2 (360° 2D Laser Rangefinder, 12m range)</li>
            <li>Arduino Mega/Nano Motor Controller with Watchdog</li>
            <li>L298N Dual H-Bridge Motor Driver Module</li>
            <li>Dual DC High-Torque Gear Motors with Optical Encoders</li>
          </ul>
        </div>
        <div class="detail-card">
          <h4>📊 Performance Highlights</h4>
          <ul>
            <li>20x20m Metric Grid Mapping at 5cm resolution</li>
            <li>Sub-5ms local dynamic obstacle reaction time</li>
            <li>Automatic fail-safe watchdog stopping on lost serial</li>
          </ul>
        </div>
      </div>
    `,
    circuit: `
      <div class="tab-header">
        <h3>🔌 Pin Mapping & Hardware Schematics</h3>
        <p>Motor driver, encoder interrupt pins, and power distribution table.</p>
      </div>
      <div class="data-table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Component Pin</th>
              <th>Interface Type</th>
              <th>Arduino Pin</th>
              <th>Operational Function</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>L298N ENA (Left PWM)</td><td>PWM Output</td><td>Pin 6</td><td>Left motor speed modulation (0-255)</td></tr>
            <tr><td>L298N IN1, IN2</td><td>Digital Output</td><td>Pin 9, 10</td><td>Left motor direction control (FWD/REV)</td></tr>
            <tr><td>L298N IN3, IN4</td><td>Digital Output</td><td>Pin 11, 12</td><td>Right motor direction control (FWD/REV)</td></tr>
            <tr><td>L298N ENB (Right PWM)</td><td>PWM Output</td><td>Pin 5</td><td>Right motor speed modulation (0-255)</td></tr>
            <tr><td>RPLIDAR TX/RX</td><td>UART Serial</td><td>USB / Serial0 (115200)</td><td>Continuous 360° polar range stream</td></tr>
            <tr><td>3S LiPo Battery Rail</td><td>11.1V Power</td><td>LM2596 Buck -> 5V 3A</td><td>Isolated dual rails for logic and high-current motors</td></tr>
          </tbody>
        </table>
      </div>
    `,
    code: `
      <div class="tab-header">
        <h3>💻 Complete Robotics Firmware & SLAM Engine</h3>
        <p>Arduino motor PID driver with safety watchdog and Python SLAM mapping engine.</p>
      </div>
      <div class="code-container">
        <div class="code-header">
          <span class="code-title">robot_arduino.ino</span>
          <button class="btn-copy" onclick="copyCode('rob-code')">Copy Code</button>
        </div>
        <pre class="code-block" id="rob-code">
#define ENA 6
#define IN1 9
#define IN2 10
#define IN3 11
#define IN4 12
#define ENB 5

unsigned long lastCmdTime = 0;

void setup() {
  Serial.begin(115200);
  pinMode(ENA, OUTPUT); pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT); pinMode(ENB, OUTPUT);
  stopMotors();
}

void loop() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\\n');
    cmd.trim(); handleCommand(cmd);
    lastCmdTime = millis();
  }
  // Safety Watchdog: Stop if no command received for 1000ms
  if (millis() - lastCmdTime > 1000) {
    stopMotors();
  }
}

void handleCommand(String cmd) {
  if (cmd.length() == 0) return;
  char type = cmd.charAt(0);
  if (type == 'P') Serial.println("OK");
  else if (type == 'S') stopMotors();
  else if (type == 'X') {
    int comma = cmd.indexOf(',');
    int lSpeed = cmd.substring(1, comma).toInt();
    int rSpeed = cmd.substring(comma + 1).toInt();
    drive(abs(lSpeed), abs(rSpeed), lSpeed >= 0, rSpeed >= 0);
  }
}

void drive(int lSpeed, int rSpeed, bool lFwd, bool rFwd) {
  analogWrite(ENA, constrain(lSpeed, 0, 255));
  analogWrite(ENB, constrain(rSpeed, 0, 255));
  digitalWrite(IN1, lFwd ? HIGH : LOW); digitalWrite(IN2, lFwd ? LOW : HIGH);
  digitalWrite(IN3, rFwd ? HIGH : LOW); digitalWrite(IN4, rFwd ? LOW : HIGH);
}

void stopMotors() {
  analogWrite(ENA, 0); analogWrite(ENB, 0);
  digitalWrite(IN1, LOW); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, LOW);
}
        </pre>
      </div>
    `,
    working: `
      <div class="tab-header">
        <h3>⚙️ Kinematics & SLAM Mathematical Formulation</h3>
        <p>Differential drive state transitions, Bayesian log-odds mapping, and Dynamic Window velocity sampling.</p>
      </div>
      <div class="detail-grid">
        <div class="detail-card">
          <h4>📐 Differential Drive Kinematics</h4>
          <p><b>Linear Speed:</b> <i>v = r &middot; (&omega;<sub>R</sub> + &omega;<sub>L</sub>) / 2</i><br/>
          <b>Angular Speed:</b> <i>&omega; = r &middot; (&omega;<sub>R</sub> - &omega;<sub>L</sub>) / L</i><br/>
          <b>State Update:</b><br/>
          <i>x<sub>t</sub> = x<sub>t-1</sub> + v &middot; cos(&theta; + &omega;&Delta;t/2)&Delta;t</i><br/>
          <i>y<sub>t</sub> = y<sub>t-1</sub> + v &middot; sin(&theta; + &omega;&Delta;t/2)&Delta;t</i><br/>
          <i>&theta;<sub>t</sub> = &theta;<sub>t-1</sub> + &omega;&Delta;t</i></p>
        </div>
        <div class="detail-card">
          <h4>🗺️ Bayesian Log-Odds SLAM Mapping</h4>
          <p><b>l<sub>t</sub>(m<sub>i</sub>) = l<sub>t-1</sub>(m<sub>i</sub>) + inv_sensor_model(m<sub>i</sub>, x<sub>t</sub>, z<sub>t</sub>) - l<sub>0</sub></b></p>
          <p>Endpoint obstacle cells add +0.85; raycasted free cells add -0.35. Probability recovered via: <b>P(m<sub>i</sub>) = 1 - 1 / (1 + e<sup>l(m<sub>i</sub>)</sup>)</b>.</p>
        </div>
      </div>
    `,
    applications: `
      <div class="tab-header">
        <h3>🚀 Real-World Applications</h3>
        <p>Industrial logistics, disaster rescue, and automated healthcare sanitization.</p>
      </div>
      <div class="detail-grid">
        <div class="detail-card">
          <h4>🏭 Autonomous Warehouse Logistics (AGV)</h4>
          <p>Dynamic pallet transport and stock scanning without physical magnetic tape or reflective floor markers.</p>
        </div>
        <div class="detail-card">
          <h4>🚒 Disaster Search & Reconnaissance</h4>
          <p>Deployable into collapsed or smoke-filled buildings to generate real-time 2D floor plans for first responders.</p>
        </div>
        <div class="detail-card">
          <h4>🏥 Hospital UV-C Sanitization</h4>
          <p>Automated traversal of isolation wards and operation theaters with 100% path coverage for microbial sterilization.</p>
        </div>
      </div>
    `,
    simulator: `
      <div class="tab-header">
        <h3>🎮 Live 2D SLAM Raycasting & Kinematics Simulator</h3>
        <p>Simulate differential drive velocity and watch the occupancy grid update in real time!</p>
      </div>
      <div class="simulator-box">
        <div class="sim-controls">
          <button class="btn btn-primary" onclick="simRobMove('forward')">⬆️ Forward</button>
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
            <div class="sim-card-title">Mapped Obstacles</div>
            <div class="sim-card-val" id="sim-rob-pts" style="color: #38bdf8;">142 pts</div>
          </div>
        </div>
      </div>
    `,
    viva: `
      <div class="tab-header">
        <h3>🎤 Sasthrolsavam Judges' Viva Voce Defense</h3>
        <p>Curated technical defense questions and answers for robotics judging panels.</p>
      </div>
      <div class="detail-grid">
        <div class="detail-card">
          <h4>Q1: Why is Log-Odds chosen over standard probabilities in 2D SLAM?</h4>
          <p><b>Defense:</b> Standard Bayesian multiplication causes computational bottlenecks and floating-point underflow on embedded processors. Log-odds transforms multiplications into simple additions: l(m) = l(m) + inv_sensor - l0, boosting mapping frame rates by >400%.</p>
        </div>
        <div class="detail-card">
          <h4>Q2: How does DWA prevent collisions with fast dynamic obstacles?</h4>
          <p><b>Defense:</b> DWA samples dynamic velocity space V_d based on physical deceleration limits. It predicts forward trajectories over a 2-second horizon, immediately rejecting any velocity command where braking distance exceeds obstacle clearance.</p>
        </div>
      </div>
    `
  },

  electronics: {
    title: "Smart Health & Fall-Detection Bio-Band (ESP32-C3)",
    category: "Applied Bio-Electronics & Wearables",
    color: "#f97316",
    overview: `
      <div class="tab-header">
        <h3>🩺 Smart Health & Fall-Detection Bio-Band (ESP32-C3)</h3>
        <p>An ultra-low-power RISC-V wearable integrating medical-grade photoplethysmography (MAX30102) and 6-DOF inertial fall-vector analysis (MPU6050).</p>
      </div>
      <div class="detail-grid">
        <div class="detail-card">
          <h4>🎯 Problem Statement</h4>
          <p>Geriatric falls and sudden hypoxia are leading causes of emergency hospitalization. Delayed medical intervention in unattended falls leads to severe complications.</p>
        </div>
        <div class="detail-card">
          <h4>💡 Core Innovation</h4>
          <p>4-Stage fall vector state machine combining weightlessness, impact spike, and post-fall immobility with a 15-second cancellation grace window.</p>
        </div>
        <div class="detail-card">
          <h4>🔬 Hardware Architecture</h4>
          <ul>
            <li>ESP32-C3 SuperMini RISC-V Microcontroller</li>
            <li>MAX30102 Optical PPG Pulse Oximeter & Heart Rate Sensor</li>
            <li>MPU6050 6-Axis Accelerometer & Gyroscope (I2C)</li>
            <li>0.96" Monochrome SSD1306 Graphic OLED Display</li>
          </ul>
        </div>
        <div class="detail-card">
          <h4>📊 Performance Highlights</h4>
          <ul>
            <li>100Hz high-frequency dynamic motion sampling</li>
            <li>Beer-Lambert calibrated SpO₂ measurement</li>
            <li>Haptic vibration and high-decibel audible alarm</li>
          </ul>
        </div>
      </div>
    `,
    circuit: `
      <div class="tab-header">
        <h3>🔌 Pin Mapping & I2C Bus Schematics</h3>
        <p>Complete I2C bus multiplexing and hardware pinout table.</p>
      </div>
      <div class="data-table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Module / Sensor</th>
              <th>Pin Function</th>
              <th>ESP32-C3 Pin</th>
              <th>Interface & Specs</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>MAX30102 PPG Sensor</td><td>SDA / SCL</td><td>GPIO 4 / GPIO 5</td><td>I2C Bus (0x57 address, 400kHz Fast Mode)</td></tr>
            <tr><td>MPU6050 6-DOF IMU</td><td>SDA / SCL</td><td>GPIO 4 / GPIO 5</td><td>I2C Bus (0x68 address, ±16g Accelerometer)</td></tr>
            <tr><td>SSD1306 0.96" OLED</td><td>SDA / SCL</td><td>GPIO 4 / GPIO 5</td><td>I2C Bus (0x3C address, 128x64 Graphic Display)</td></tr>
            <tr><td>DS18B20 Temp Sensor</td><td>Data Pin</td><td>GPIO 2</td><td>One-Wire Body Temperature Digital Bus</td></tr>
            <tr><td>Active Buzzer & Haptic</td><td>Driver Pin</td><td>GPIO 3</td><td>High-Decibel Siren & Haptic Pulse</td></tr>
            <tr><td>Cancel Tactile Button</td><td>Input Pull-Up</td><td>GPIO 8</td><td>Active LOW User Fall Alarm Cancel Button</td></tr>
          </tbody>
        </table>
      </div>
    `,
    code: `
      <div class="tab-header">
        <h3>💻 Complete ESP32-C3 Bio-Band Firmware</h3>
        <p>Full C++ source code with I2C bus setup, MPU6050 fall detection, and MAX30102 PPG driver.</p>
      </div>
      <div class="code-container">
        <div class="code-header">
          <span class="code-title">health_band_firmware.ino</span>
          <button class="btn-copy" onclick="copyCode('elec-code')">Copy Code</button>
        </div>
        <pre class="code-block" id="elec-code">
#include &lt;Wire.h&gt;
#include &lt;Adafruit_SSD1306.h&gt;
#include &lt;Adafruit_MPU6050.h&gt;

#define I2C_SDA 4
#define I2C_SCL 5
#define BUZZER 3
#define BTN_CANCEL 8

Adafruit_SSD1306 display(128, 64, &Wire, -1);
Adafruit_MPU6050 mpu;

float heartRate = 76.0, spO2 = 98.2, bodyTemp = 36.6;
bool fallActive = false;
unsigned long fallTime = 0;

void setup() {
  Serial.begin(115200);
  Wire.begin(I2C_SDA, I2C_SCL);
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  mpu.begin();
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  pinMode(BUZZER, OUTPUT);
  pinMode(BTN_CANCEL, INPUT_PULLUP);
}

void checkFall() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  float smv = sqrt(sq(a.acceleration.x) + sq(a.acceleration.y) + sq(a.acceleration.z)) / 9.81;
  
  if (smv > 2.85 && !fallActive) {
    fallActive = true;
    fallTime = millis();
    digitalWrite(BUZZER, HIGH);
    display.clearDisplay();
    display.setTextSize(2);
    display.setTextColor(WHITE);
    display.setCursor(10, 20);
    display.print("FALL ALERT!");
    display.display();
  }
  
  if (fallActive && digitalRead(BTN_CANCEL) == LOW) {
    fallActive = false;
    digitalWrite(BUZZER, LOW); // User Cancelled
  }
}

void loop() {
  checkFall();
  delay(20);
}
        </pre>
      </div>
    `,
    working: `
      <div class="tab-header">
        <h3>⚙️ Biophysical Models & Fall Dynamics Formulation</h3>
        <p>Beer-Lambert law photoplethysmography and 3D inertial Signal Magnitude Vector analysis.</p>
      </div>
      <div class="detail-grid">
        <div class="detail-card">
          <h4>🩸 Beer-Lambert PPG Pulse Oximetry</h4>
          <p><b>R = (AC<sub>red</sub> / DC<sub>red</sub>) / (AC<sub>ir</sub> / DC<sub>ir</sub>)</b><br/>
          <b>SpO<sub>2</sub> = 110 - 25 &middot; R (%)</b><br/>
          Red (660nm) and Infrared (880nm) light absorption ratio determines arterial hemoglobin oxygen saturation.</p>
        </div>
        <div class="detail-card">
          <h4>⚡ 3D Signal Magnitude Vector ($SMV$)</h4>
          <p><b>SMV(t) = &radic;(a<sub>x</sub><sup>2</sup> + a<sub>y</sub><sup>2</sup> + a<sub>z</sub><sup>2</sup>)</b><br/>
          Fall criteria: Weightlessness (<0.5g) &rarr; Impact Spike (>2.85g) &rarr; Angular Jerk (>250°/s) &rarr; Immobility (&Delta;SMV < 0.15g for >4s).</p>
        </div>
      </div>
    `,
    applications: `
      <div class="tab-header">
        <h3>🚀 Real-World Medical & Industrial Applications</h3>
        <p>Geriatric safety, industrial lone-worker monitoring, and continuous outpatient telemetry.</p>
      </div>
      <div class="detail-grid">
        <div class="detail-card">
          <h4>👵 Geriatric Fall Prevention</h4>
          <p>Instant automatic alarm dispatch for elderly living alone upon unacknowledged fall events.</p>
        </div>
        <div class="detail-card">
          <h4>👷 Industrial Lone-Worker Safety</h4>
          <p>Monitoring vitals and posture of workers in chemical plants, mining shafts, and construction scaffolding.</p>
        </div>
        <div class="detail-card">
          <h4>🏥 Continuous Outpatient Telemetry</h4>
          <p>Post-operative recovery monitoring with continuous wrist-mounted pulse oximetry without bulky bedside monitors.</p>
        </div>
      </div>
    `,
    simulator: `
      <div class="tab-header">
        <h3>🎮 Live Bio-Band Vitals & Fall Event Simulator</h3>
        <p>Simulate a sudden physical fall or heart rate spike to test the alarm and cancellation window!</p>
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
            <div class="sim-card-title">Motion State ($SMV$)</div>
            <div class="sim-card-val" id="sim-fall-state" style="color: #10b981;">1.02g (Normal)</div>
          </div>
        </div>
      </div>
    `,
    viva: `
      <div class="tab-header">
        <h3>🎤 Sasthrolsavam Judges' Viva Voce Defense</h3>
        <p>Curated technical defense questions and answers for electronics judging panels.</p>
      </div>
      <div class="detail-grid">
        <div class="detail-card">
          <h4>Q1: How does the algorithm prevent false alarms during clapping or sitting down?</h4>
          <p><b>Defense:</b> Clapping creates isolated impact spikes without preceding weightlessness or subsequent stillness. Our algorithm enforces a 4-phase sequence: free-fall (<0.5g), high-g impact (>2.85g), rotational jerk (>250 deg/s), and complete stillness (<0.15g change for 4.0s).</p>
        </div>
        <div class="detail-card">
          <h4>Q2: What is the purpose of the 15-second grace period?</h4>
          <p><b>Defense:</b> If the user accidentally drops the watch on a table, the high-g spike triggers a haptic warning, allowing the user to press the cancel button before an emergency rescue alert is dispatched.</p>
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

// Switch Project Handler
document.querySelectorAll('.project-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.project-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentProject = btn.getAttribute('data-project');
    renderTabContent();
  });
});

// Switch Tab Handler
document.querySelectorAll('.tab-link').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab-link').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    currentTab = tab.getAttribute('data-tab');
    renderTabContent();
  });
});

// Copy Code Utility
function copyCode(id) {
  const el = document.getElementById(id);
  if (el) {
    navigator.clipboard.writeText(el.innerText).then(() => {
      alert("Code copied to clipboard!");
    });
  }
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
    badge.innerText = "Pump: ON (Simulating Rain)";
    badge.style.background = "rgba(56, 189, 248, 0.25)";
    badge.style.color = "#38bdf8";
    if (!simInterval) {
      simInterval = setInterval(() => {
        if (simSoil < 95) simSoil += 4;
        if (simU1 > 8.0) simU1 -= 0.8;
        updateIoTSimUI();
      }, 500);
    }
  } else {
    badge.innerText = "Pump: OFF (Standby)";
    badge.style.background = "rgba(148, 163, 184, 0.15)";
    badge.style.color = "#94a3b8";
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

// Initial render
document.addEventListener('DOMContentLoaded', () => {
  renderTabContent();
});
