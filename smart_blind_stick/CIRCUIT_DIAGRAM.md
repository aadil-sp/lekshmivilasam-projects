# 🔌 ESP8266 Smart Blind Stick - Circuit Diagram & Pinout

This document details the exact hardware wiring and schematic connections for the **ESP8266-based Smart Blind Stick with Fall Detection & Wi-Fi Hotspot Telemetry**.

---

## 📋 Bill of Materials (BOM)

| Component | Specification / Model | Quantity | Purpose |
| :--- | :--- | :--- | :--- |
| **Microcontroller** | ESP8266 NodeMCU V2 / V3 / D1 Mini | 1 | Master Controller + Wi-Fi Hotspot Web Server |
| **Ultrasonic Sensor** | HC-SR04 / HC-SR04P (3.3V/5V compatible) | 1 | Distance & Fall Proximity Detection |
| **Buzzer** | 5V / 3.3V Active Buzzer | 1 | Stick-mounted Audible Siren Alert |
| **Vibration Motor** | 3V Coin Vibration Motor / Module | 1 | Haptic feedback for the visually impaired user |
| **Power Supply** | 3.7V 18650 Li-ion Battery / 5V Power Bank | 1 | Portable Power Supply |
| **Resistors (Optional)**| 1kΩ & 2kΩ (Voltage Divider for HC-SR04 Echo)| 2 | Protects ESP8266 3.3V GPIO if using 5V HC-SR04 |
| **Breadboard / Perfboard** | Standard Mini Breadboard & Jumper Wires | 1 set | Wiring and Enclosure Mounting |

---

## 📌 Pin Mapping Table

| ESP8266 NodeMCU Pin | GPIO Pin | Connected Component | Component Pin | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **D1** | `GPIO 5` | Ultrasonic Sensor | **TRIG** | Trigger pulse output |
| **D2** | `GPIO 4` | Ultrasonic Sensor | **ECHO** | Echo pulse input |
| **D5** | `GPIO 14` | Active Buzzer | **(+) Positive** | Siren & proximity beep output |
| **D6** | `GPIO 12` | Vibration Motor | **(+) Positive** | Haptic pulse output |
| **VIN / 3V3** | `5V / 3.3V` | Ultrasonic Sensor & Buzzer | **VCC** | Power rail |
| **GND** | `GND` | All Components | **GND** | Common Ground rail |

---

## 🗺️ Visual Wiring Schematic (ASCII Diagram)

```
                       +-----------------------------+
                       |     ESP8266 NodeMCU         |
                       |                             |
  [HC-SR04 SENSOR]     |                             |     [ACTIVE BUZZER]
  +--------------+     |                             |     +-------------+
  |  VCC   (5V)  |<----+ VIN (5V)                    |     |  VCC (+)    |<---+ D5 (GPIO 14)
  |  TRIG        |<----+ D1  (GPIO 5)                |     |  GND (-)    |----+ GND
  |  ECHO        |----+ D2  (GPIO 4)                |     +-------------+
  |  GND         |----+ GND                         |
  +--------------+     |                             |     [VIBRATION MOTOR]
                       |                             |     +---------------+
                       | D6  (GPIO 12) -------------->---->| VCC (+)       |
                       | GND ------------------------>---->| GND (-)       |
                       |                             |     +---------------+
                       | 3V3                         |
                       | EN                          |     [POWER SUPPLY]
                       | RST                         |     +----------------+
                       | VIN <-----------------------------| +5V / Battery  |
                       | GND <-----------------------------| GND            |
                       +-----------------------------+     +----------------+
```

---

## ⚡ Level Shifter Note for HC-SR04 (5V vs 3.3V)

If using the standard **5V HC-SR04**:
- The `ECHO` pin outputs a 5V logic signal. While ESP8266 inputs are 5V-tolerant in many revisions, a simple 2-resistor voltage divider is recommended for long-term safety:
  - `HC-SR04 ECHO` $\rightarrow$ `1kΩ resistor` $\rightarrow$ `NodeMCU D2 (GPIO 4)` $\rightarrow$ `2kΩ resistor` $\rightarrow$ `GND`.
- If using **HC-SR04P** or **RCWL-9610** (which natively support 3.3V), connect directly to `3V3`, `D1`, `D2`, and `GND`.

---

## 🚀 Assembly on Stick

1. **Sensor Placement**: Mount the HC-SR04 sensor at a **30° downward angle** on the lower half of the walking stick so it scans both forward obstacles and ground drop-offs.
2. **Handle / Haptic Feedback**: Place the vibration motor directly under the handle grip so the user can feel proximity vibrations even in noisy environments.
3. **Buzzer Placement**: Place the buzzer near the top of the stick pointing outward so bystanders and caretakers can easily hear the fall emergency alarm.
