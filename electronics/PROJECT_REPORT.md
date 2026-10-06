# KERALA STATE SASTHROLSAVAM (SASTHRAMELA) - ELECTRONICS
## Smart IoT Health & Fall-Detection Bio-Band with On-Device Edge Analytics & Captive Medical Portal

---

### Project Metadata
- **Category:** Electronics / Higher Secondary & High School Science Fair
- **Theme:** Science, Technology & Innovation for Human Health & Safety
- **Core Microcontroller:** ESP32-C3 32-bit RISC-V SoC (160MHz)
- **Primary Sensors:** MAX30102 (PPG), MPU6050 (6-Axis IMU), DS18B20 (Thermal), GSR Electrodes (EDA)
- **User Interface:** 0.96" Monochrome OLED Display + Dual Tactile Navigation Buttons + Captive Portal Web Dashboard

---

## 1. ABSTRACT
Geriatric citizens, solitary patients, and individuals in high-stress work environments face critical risks of unattended cardiac anomalies, sudden hypoxia, acute stress spikes, and fatal mechanical falls. Traditional wearable health trackers rely heavily on proprietary cloud services, active cellular SIM cards, or internet subscriptions, rendering them inoperable in remote or network-congested emergency scenarios.

This project presents a self-contained, low-cost, multi-vital telemetry wearable: the **Smart IoT Health & Fall-Detection Bio-Band**. Powered by a power-efficient ESP32-C3 RISC-V microcontroller, it captures Photoplethysmography (PPG) vitals (Heart Rate & SpO2 via MAX30102), body temperature (DS18B20), sympathetic autonomic nervous arousal (Galvanic Skin Response/GSR), and 6-axis kinematics (MPU6050). 

The system implements an on-device Edge Fall Detection Algorithm that detects freefall acceleration followed by high-g impact. In an anomaly, an onboard audible alert is sounded while the ESP32-C3 broadcasts a standalone Wi-Fi hotspot with a **Zero-Configuration Captive Portal**. Any responding bystander, paramedic, or family member connecting with a smartphone is instantly redirected (without requiring an app or internet) to a comprehensive, real-time medical dashboard showing live telemetry, emergency status, and acknowledging alarms.

---

## 2. SCIENTIFIC PRINCIPLES & WORKING THEORY

### A. Photoplethysmography (PPG) — MAX30102
- **Principle:** Utilizes dual optical wavelength absorption (Red LED @ 660 nm and Infrared LED @ 880 nm) through vascularized capillary beds.
- **Oxygen Saturation ($SpO_2$):** Oxygenated hemoglobin ($HbO_2$) preferentially absorbs Infrared light, while deoxygenated hemoglobin ($Hb$) absorbs Red light.
- **Mathematical Formula:**
  $$\text{Ratio of Ratios } (R) = \frac{(AC_{\text{red}} / DC_{\text{red}})}{(AC_{\text{ir}} / DC_{\text{ir}})}$$
  $$SpO_2 = 110 - 25 \times R \quad (\%)$$

### B. Galvanic Skin Response (GSR) / Electrodermal Activity (EDA)
- **Principle:** Measures autonomic sympathetic nervous system stimulation. Psychological stress activates eccrine sweat glands, drastically lowering skin electrical resistance ($R_{\text{skin}}$) and increasing skin conductance ($S$).
- **Mathematical Formula:**
  $$R_{\text{skin}} = R_{\text{ref}} \times \frac{V_{\text{in}} - V_{\text{out}}}{V_{\text{out}}} \quad (k\Omega)$$
  $$\text{Conductance } (G) = \frac{1000}{R_{\text{skin}}} \quad (\mu S)$$

### C. 6-Axis Inertial Sensing & Dual-Stage Fall Detection — MPU6050
- **Principle:** 3-axis MEMS accelerometer measures inertial forces in $g$ ($1g = 9.81\text{ m/s}^2$).
- **Total Acceleration Vector Magnitude:**
  $$a_{\text{total}} = \sqrt{a_x^2 + a_y^2 + a_z^2}$$
- **Two-Stage Threshold State Machine:**
  1. *Free-fall Stage:* $a_{\text{total}} < 0.45g$ sustained for $> 60\text{ ms}$.
  2. *Impact Stage:* $a_{\text{total}} > 2.60g$ occurring within $600\text{ ms}$ of free-fall, followed by posture alteration (pitch/roll tilt variance).

---

## 3. HARDWARE & CIRCUIT PIN MAP

| Module | Pin | ESP32-C3 Pin | Purpose |
| :--- | :--- | :--- | :--- |
| **0.96" OLED (SSD1306)** | SDA, SCL, VCC, GND | GPIO 4 (SDA), GPIO 5 (SCL), 3.3V, GND | Display Menu System |
| **MAX30102 PPG** | SDA, SCL, VIN, GND | GPIO 4 (SDA), GPIO 5 (SCL), 3.3V, GND | Heart Rate & SpO2 |
| **MPU6050 IMU** | SDA, SCL, VCC, GND | GPIO 4 (SDA), GPIO 5 (SCL), 3.3V, GND | Kinematics & Fall Detection |
| **DS18B20 Temp** | DQ, VDD, GND | GPIO 2 (4.7kΩ Pull-up), 3.3V, GND | Digital Body Temperature |
| **GSR Electrodes** | Signal, VCC, GND | GPIO 0 (ADC1_CH0), 3.3V, GND | Electrodermal Stress |
| **Active Buzzer** | POS (+), NEG (-) | GPIO 3, GND | Audible Alert Siren |
| **Button 1 (Scroll)** | Pin 1, Pin 2 | GPIO 9, GND | Next Screen Navigation |
| **Button 2 (Select)** | Pin 1, Pin 2 | GPIO 8, GND | Acknowledge Alert / Mute |
| **Li-Po Battery** | 3.7V via Divider | GPIO 1 (ADC1_CH1) | Battery Percentage Monitor |

---

## 4. SOFTWARE ARCHITECTURE & CAPTIVE PORTAL

1. **Local Dual-Button Menu Engine:**
   - **Screen 0:** High-level Dashboard (HR, SpO2, Temp °C/°F, GSR, Motion state).
   - **Screen 1:** Cardiac Detailed View with live Pulse Waveform graphic.
   - **Screen 2:** Stress & Thermometry with real-time conductance bar.
   - **Screen 3:** 6-Axis Motion Angles (Pitch & Roll) + Fall Trigger Banner.
   - **Screen 4:** Wireless Hotspot Telemetry (Clients connected, SSID, IP).
2. **Captive Portal Engine:**
   - ESP32-C3 broadcasts open Wi-Fi AP (`SmartBand-Sasthramela`).
   - Custom DNS Server traps all DNS requests (Port 53) and returns `192.168.4.1`.
   - Built-in HTTP WebServer serves an ultra-lightweight glassmorphism single-page app displaying real-time live telemetry charts, remote buzzer mute, and SOS triggers.

---

## 5. BILL OF MATERIALS (BOM) & COST ANALYSIS

| Item | Specification | Qty | Approx Cost (₹ INR) |
| :--- | :--- | :--- | :--- |
| **ESP32-C3 Microcontroller** | RISC-V Single Core 160MHz, Wi-Fi+BLE | 1 | ₹290 |
| **0.96" I2C Monochrome OLED** | SSD1306 128x64 Blue/Cyan Display | 1 | ₹160 |
| **MAX30102 Module** | High Sensitivity Pulse Oximeter & PPG | 1 | ₹220 |
| **MPU6050 Module** | 6-Axis Gyroscope + Accelerometer | 1 | ₹140 |
| **DS18B20 Temp Sensor** | Waterproof / Contact probe probe | 1 | ₹90 |
| **GSR Sensor & Finger Straps** | EDA Electrodes + Conditioning Circuit | 1 | ₹210 |
| **Li-Po Battery & TP4056** | 3.7V 500mAh + USB-C TP4056 Charger | 1 | ₹180 |
| **Tactile Buttons & Buzzer** | 2x Push Switches + Active Buzzer | 1 set | ₹30 |
| **Casing & Wrist Band** | 3D Printed / Enclosure + Straps | 1 | ₹80 |
| **Total Estimated Cost** | | | **₹1,400 INR** |

*(Commercial alternatives cost ₹8,000–₹25,000 and do not provide standalone captive portal emergency telemetry).*

---

## 6. SASTHRAMELA JUDGES VIVA VOCE & TECHNICAL DEFENSE

**Q1: Why choose ESP32-C3 over standard ESP8266 or Arduino Nano?**  
*Answer:* ESP32-C3 uses a modern 32-bit RISC-V core with ultra-low active power consumption, integrated hardware cryptographic acceleration, built-in Wi-Fi and BLE 5.0, and sufficient RAM (400KB) to run concurrent DNS Captive Portal, WebServer, and multi-sensor I2C acquisition simultaneously.

**Q2: How is false-positive fall detection prevented when a user claps or jumps?**  
*Answer:* The algorithm requires a **two-phase sequential verification**: first, a weightlessness phase ($a_{\text{total}} < 0.45g$) must occur, followed strictly within 600ms by an impact spike ($> 2.6g$) and sustained orientation change. High acceleration without prior free-fall (such as clapping or running) is filtered out.

**Q3: Why is a Captive Portal superior to a cloud IoT platform in emergencies?**  
*Answer:* In remote disaster zones, rural clinics, or during cellular network blackouts, cloud-dependent devices fail completely. The captive portal operates completely decentralized and off-grid. Any smartphone connecting to the device Wi-Fi immediately pops up the telemetry screen without downloading any app or creating accounts.

---
*Kerala State Sasthrolsavam Project Portfolio &bull; Lekshmivilasam*
