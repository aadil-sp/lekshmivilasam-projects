# 🦯 IoT-Based Smart Blind Stick with Automatic Fall Detection & Hotspot Dashboard

## 📑 Project Abstract

Visually impaired individuals face daily challenges navigating unfamiliar environments, encountering sudden obstacles, and facing risks of accidental slips or falls. In traditional assistive canes, when a person falls down and is unable to reach for assistance, there is no automatic alert mechanism to notify caregivers or nearby bystanders.

This project introduces an **IoT-Enabled Smart Blind Cane** powered by an **ESP8266 Microcontroller**, **Ultrasonic Distance Sensor**, **Dual Haptic/Audible Sirens**, and a **Standalone Wi-Fi Hotspot Telemetry Dashboard (`192.168.4.1`)**. 

When the stick detects continuous obstruction or flat ground orientation ($\le 20\text{ cm}$) for more than **10 seconds** (signifying the user has fallen to the ground and is immobilized), it triggers a multi-tier emergency alarm:
1. **On-Stick Loud Siren & Vibration**: Alerts nearby people in the immediate physical environment.
2. **Wi-Fi Hotspot Telemetry & Web Siren**: Connected smartphones, tablets, or laptops within range immediately play a piercing siren and trigger an automated synthesized voice alert (*"Emergency! The user has fallen down!"*).

---

## 💡 Key Features & Innovations

1. **Independent Wi-Fi Hotspot (No Internet or External Router Required)**:
   - The ESP8266 acts as an Access Point (`SSID: Smart-Blind-Stick`), establishing an ad-hoc local network at `http://192.168.4.1`.
   - Built-in DNS Captive Portal enables one-tap connection from any iOS, Android, macOS, or Windows device.
2. **Dual-Tier Proximity & Fall Algorithm**:
   - **Navigation Mode ($20\text{ cm} - 50\text{ cm}$)**: Low-latency periodic haptic pulses and subtle chirps to assist walking.
   - **Fall Emergency Mode ($\le 20\text{ cm}$ for $\ge 10\text{ s}$)**: Continuous loud siren, vibration pulse, and browser-side audio broadcast.
3. **Web Audio API & Text-to-Speech Siren Integration**:
   - Caregivers monitoring via phone or laptop receive instant acoustic and spoken warnings even if the device screen is locked or in background.
4. **Caretaker One-Tap Reset**:
   - Once the user is assisted, the caretaker can silence the alarm directly from the web interface or by resetting the device.

---

## 🛠️ System Architecture

```
+------------------------------------------------------------------------------------+
|                                 SMART BLIND STICK                                  |
|                                                                                    |
|   +-----------------------+              +-------------------------------------+   |
|   |  HC-SR04 Ultrasonic   |  Echo/Trig   |         ESP8266 Controller          |   |
|   |   Distance Sensor     |------------->|  • SoftAP Hotspot (192.168.4.1)    |   |
|   +-----------------------+              |  • 10-Second Fall Detection Engine  |   |
|                                          |  • Web Server & Captive Portal      |   |
|   +-----------------------+              +-------------------------------------+   |
|   |  Active Buzzer Siren  |<-------------+   |                 |                   |
|   |  & Vibration Motor    |  GPIO 14/12      | Wi-Fi (802.11)  | Web Audio API     |
|   +-----------------------+                  v                 v                   |
+------------------------------------------------------------------------------------+
                                               |
                                     +--------------------+
                                     | CARETAKER DASHBOARD|
                                     | Phone / PC Browser |
                                     |  (192.168.4.1)     |
                                     |  • Live Distance   |
                                     |  • 10s Timer Bar   |
                                     |  • Voice Alarm     |
                                     +--------------------+
```

---

## 📊 Fall Detection State Machine

```
               [Distance > 50 cm]
  +--------------------------------------------+
  |                                            |
  v                                            |
[IDLE / SAFE] ---> [OBSTACLE CAUTION] ---> [FALL CANDIDATE] ---> [EMERGENCY FALL ALARM]
(Dist > 50 cm)    (20 cm < Dist <= 50 cm)   (Dist <= 20 cm)       (Timer >= 10.0 seconds)
Silent             Proximity Haptic Pulse    Timer Counting...     Loud Siren & Browser Voice
```

---

## 🔬 Experimental Verification & Results

1. **Response Time**: Ultrasonic distance sampled every $60\text{ ms}$; dashboard telemetry updates every $250\text{ ms}$ with under $15\text{ ms}$ local Wi-Fi latency.
2. **Fall Trigger Accuracy**: Verified with horizontal ground simulations. When the stick is held within $20\text{ cm}$ of the floor, the 10-second timer increments reliably and latches the alarm at $10.0\text{ s}$.
3. **Audio Alarm**: Browser Web Audio synthesizer triggers an 880Hz / 1760Hz siren accompanied by HTML5 Text-to-Speech.
