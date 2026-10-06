# KERALA STATE SASTHROLSAVAM (SASTHRAMELA) - IoT PROJECT
## AIoT Landslide & Flash-Flood Early Warning System with Embedded TinyML Sensor Fusion

---

### Project Metadata
- **Category:** Information & Communication Technology (IoT) / Sasthramela
- **Theme:** Science, Technology & Disaster Management for Community Safety
- **Target Geography:** Western Ghats Hill Tracts (Wayanad, Idukki, Pathanamthitta, Malappuram)
- **Core Microcontroller:** ESP32 Dual-Core Tensilica Xtensa LX6 (240MHz)
- **Primary Sensors:** Soil Moisture (VWC), Dual Ultrasonic Sensors (HC-SR04 for Stream & Rain Gauge), DHT22 (Atmosphere)
- **Actuators & Alerts:** 12V DC Solenoid Flush Valve, Active High-Decibel Siren, Dual Status LEDs
- **Cloud Telemetry:** Blynk IoT 2.0 Cloud Platform / REST Webhook

---

## 1. ABSTRACT
The Western Ghats of Kerala are highly susceptible to catastrophic debris flows, shallow landslides, and flash floods triggered by extreme monsoon precipitation events (such as the disasters in Wayanad, Kavalappara, and Pettimudi). Delayed localized warnings and reliance on distant regional weather forecasts often result in tragic loss of life.

This project introduces an autonomous, low-cost **AIoT Landslide & Flash-Flood Early Warning System**. The system features a novel, self-emptying automated rain gauge consisting of a catchment chamber paired with an ultrasonic sensor and a **12V Solenoid Flush Valve**. When water reaches maximum capacity, the solenoid valve autonomously drains the chamber, logs the precise timestamp, increments the cumulative rainfall volume, and calculates real-time rain intensity ($mm/hr$). 

Concurrently, the device measures volumetric soil moisture saturation, stream depth rise velocity ($cm/min$), and ambient vapor conditions. An on-device **TinyML Sensor Fusion Engine** executes continuous multivariate logistic regression inference directly on the ESP32. If the computed Landslide Hazard Index exceeds critical thresholds, the system immediately sounds a local high-decibel evacuation siren and transmits emergency telemetry to the **Blynk IoT 2.0** cloud for widespread mobile alert broadcast.

---

## 2. SCIENTIFIC PRINCIPLES & MATHEMATICAL FOUNDATIONS

### A. Soil Pore-Water Pressure & Shear Strength Reduction
- **Principle (Terzaghi's Principle of Effective Stress):**
  $$\sigma' = \sigma - u$$
  Where $\sigma'$ is effective stress, $\sigma$ is total normal stress, and $u$ is pore-water pressure. As rainwater infiltrates hill slopes, pore-water pressure $u$ escalates, diminishing effective stress and driving soil shear strength $\tau_f$ below the gravitational sliding threshold:
  $$\tau_f = c' + (\sigma - u) \tan \phi'$$

### B. Automated Siphoning Ultrasonic Rain Gauge
- **Principle:** Rainwater collected via a standard funnel (catchment area $A_f$) fills a cylindrical reservoir (cross-sectional area $A_c$). An ultrasonic sensor continuously tracks water column height $h(t)$:
  $$\text{Effective Precipitation } (P) = h(t) \times \left( \frac{A_c}{A_f} \right) \quad (\text{mm})$$
  $$\text{Instantaneous Rain Rate } (R) = \frac{\Delta h}{\Delta t} \times \left( \frac{A_c}{A_f} \right) \times 3600 \quad (\text{mm/hr})$$
- When $h(t) \ge 135\text{ mm}$, the 12V Solenoid Valve triggers for 3.0 seconds, releasing the water, recording the event timestamp, and incrementing total precipitation count.

### C. Stream Level Surge Velocity
- **Formula:**
  $$v_{\text{surge}} = \frac{d_{\text{stream}}(t_2) - d_{\text{stream}}(t_1)}{t_2 - t_1} \quad (\text{cm/min})$$

### D. Embedded TinyML Sensor Fusion (Logistic Classification)
- **Model Architecture:** Lightweight multivariate classification running on ESP32:
  $$z = w_0 + w_1 \cdot (\text{Soil Moisture \%}) + w_2 \cdot (\text{Rain Rate mm/hr}) + w_3 \cdot (\text{Cumulative Rain mm}) + w_4 \cdot (\text{Stream Rise cm/min})$$
  $$P(\text{Hazard}) = \frac{1}{1 + e^{-z}} \times 100\%$$
- **Alert Tiers:**
  - $0\% - 35\%$: **SAFE** (Green LED Active)
  - $36\% - 65\%$: **CAUTION / ADVISORY** (Yellow Advisory / Intermittent Beep)
  - $66\% - 85\%$: **HIGH HAZARD WARNING** (Red LED + Frequent Beep)
  - $86\% - 100\%$: **CRITICAL EVACUATION SIREN** (Continuous Siren + Cloud Push Notification)

---

## 3. HARDWARE & CIRCUIT INTERCONNECTIONS

| Component | Pin Function | ESP32 Pin | Logic Level / Protocol |
| :--- | :--- | :--- | :--- |
| **Soil Moisture Sensor** | Analog Output | GPIO 34 | ADC1_CH6 (0 - 3.3V) |
| **Ultrasonic 1 (Stream Depth)** | TRIG / ECHO | GPIO 5 / GPIO 18 | Digital (10µs pulse / 5V divider) |
| **Ultrasonic 2 (Rain Gauge)** | TRIG / ECHO | GPIO 19 / GPIO 21 | Digital (10µs pulse / 5V divider) |
| **12V Solenoid Valve Relay** | Relay Trigger | GPIO 22 | Active HIGH Digital Output |
| **DHT22 Sensor** | Data Pin | GPIO 4 | One-Wire Digital (4.7kΩ Pull-up) |
| **High-Decibel Siren** | Positive Driver | GPIO 23 | Digital Output (NPN 2N2222) |
| **Safe Status LED (Green)** | Anode (+) | GPIO 2 | Digital Output (220Ω Resistor) |
| **Alert Status LED (Red)** | Anode (+) | GPIO 15 | Digital Output (220Ω Resistor) |

---

## 4. IOT CLOUD INTEGRATION (BLYNK 2.0 VIRTUAL PINS)

- **V0:** Landslide Hazard Index Gauge ($0 - 100\%$)
- **V1:** Soil Moisture Saturation ($0 - 100\%$)
- **V2:** Stream Water Level ($0 - 200\text{ cm}$)
- **V3:** Instant Rainfall Rate ($0 - 150\text{ mm/hr}$)
- **V4:** Cumulative 24-Hour Precipitation ($mm$)
- **V5:** Ambient Air Temperature ($^\circ\text{C}$)
- **V6:** Relative Humidity ($\%$)
- **V7:** Solenoid Flush Counter (Total cycles)
- **V8:** Qualitative Risk Assessment Banner (*SAFE / CAUTION / HIGH HAZARD / IMMINENT LANDSLIDE*)

---

## 5. BILL OF MATERIALS (BOM) & COST ANALYSIS

| Item | Component Details | Qty | Cost (₹ INR) |
| :--- | :--- | :--- | :--- |
| **ESP32 Dev Module** | Dual-Core 240MHz Wi-Fi/BLE Microcontroller | 1 | ₹350 |
| **Ultrasonic HC-SR04** | Dual Precision Acoustic Ranging Modules | 2 | ₹140 |
| **12V Solenoid Valve** | 12V 1/2" Normally Closed DC Valve | 1 | ₹280 |
| **1-Channel Relay Module** | 5V Optocoupler Isolated Relay | 1 | ₹55 |
| **Soil Moisture Sensor** | Corrosion-Resistant Soil Probe | 1 | ₹75 |
| **DHT22 Sensor** | Calibrated Temp & Humidity Sensor | 1 | ₹160 |
| **Active Piezo Siren & LEDs** | 85dB High-Decibel Buzzer + Indicators | 1 set | ₹40 |
| **Chamber & Funnel Kit** | Acrylic Cylinder, Funnel & Plumbing | 1 | ₹150 |
| **12V Power Adapter & Buck** | 12V 2A Adapter + LM2596 5V Buck Converter | 1 | ₹190 |
| **Total Estimated Cost** | | | **₹1,440 INR** |

*(Commercial geo-hazard telemetry stations exceed ₹1,50,000 INR).*

---

## 6. SASTHRAMELA JUDGES VIVA VOCE & TECHNICAL DEFENSE

**Q1: How does an ultrasonic rain gauge with a solenoid valve outperform standard tipping-bucket rain gauges?**  
*Answer:* Tipping-bucket rain gauges contain mechanical pivot arms prone to clogging with leaves, sediment, and insects in heavy rainforest environments, causing severe undercounting. Our acoustic chamber has zero moving parts during collection, provides continuous millimetric resolution, and only opens the solenoid valve for 3 seconds to flush clean water under gravity.

**Q2: Why is multi-sensor fusion essential rather than relying solely on rainfall data?**  
*Answer:* Rainfall alone does not cause landslides; slope instability depends heavily on antecedent moisture conditions (pre-existing saturation) and drainage capacity. A 50mm rainfall on bone-dry soil has low risk, while the same 50mm on already saturated soil ($>85\%$) with surging stream levels will immediately trigger catastrophic slope failure. Sensor fusion eliminates false alarms and detects true danger.

**Q3: Can this system function if the internet or cellular network goes down during a cloudburst?**  
*Answer:* Yes. The TinyML inference engine runs **100% on-device at the edge** on the ESP32. The local acoustic siren and visual alert LEDs trigger autonomously even without any Wi-Fi or cloud connection.

---
*Kerala State Sasthrolsavam Project Portfolio &bull; Lekshmivilasam IoT Division*
