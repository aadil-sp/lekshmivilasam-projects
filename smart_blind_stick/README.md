# 🦯 ESP8266 Smart Blind Stick

> **Smart Assistive Blind Cane with Automatic Fall Detection, On-Stick Siren, Wi-Fi Hotspot (`192.168.4.1`), and Web Audio Alarm for Phones & Laptops.**

---

## 🌟 Overview

The **ESP8266 Smart Blind Stick** is an IoT assistive mobility aid designed for visually impaired individuals. It serves dual purposes:
1. **Real-Time Obstacle Avoidance**: Detects obstacles in the walking path up to 4 meters away and provides proportional haptic/audio pulses.
2. **Automatic Fall Detection & Caregiver Alert**: If the stick is dropped or held within **20 cm** of the ground/obstacle continuously for **more than 10 seconds** (indicating the user has fallen down and cannot stand up), it triggers:
   - 🔊 **Stick Siren**: Loud pulsed hardware buzzer and vibration on the stick itself to alert nearby people.
   - 📱 **Phone/Laptop Emergency Alarm**: Anyone connected to the stick's Wi-Fi hotspot (`Smart-Blind-Stick` at `192.168.4.1`) gets an immediate high-pitch siren and spoken voice alert (*"Warning! Emergency! The user has fallen down! Please assist immediately!"*).

---

## 📡 Wi-Fi Hotspot & Dashboard Access

- **Wi-Fi SSID**: `Smart-Blind-Stick`
- **Wi-Fi Password**: *None (Open Wi-Fi)*
- **Dashboard Web Address**: `http://192.168.4.1`

*No internet connection or external Wi-Fi router is needed.* The ESP8266 creates its own local standalone hotspot.

---

## 🔌 Hardware Wiring & Pin Mapping

| Component | Pin | ESP8266 NodeMCU Pin | GPIO |
| :--- | :--- | :--- | :--- |
| **Ultrasonic HC-SR04** | TRIG | **D1** | GPIO 5 |
| **Ultrasonic HC-SR04** | ECHO | **D2** | GPIO 4 |
| **Active Buzzer** | (+) Positive | **D5** | GPIO 14 |
| **Vibration Motor** | (+) Positive | **D6** | GPIO 12 |
| **Power** | VCC / VIN | **VIN (5V) / 3V3** | 5V / 3.3V |
| **Ground** | GND | **GND** | Ground |

---

## 🚀 Quick Start & Flashing

### Flash to Connected ESP8266:
Run the upload script:
```bash
cd smart_blind_stick
./upload.sh
```
Or via PlatformIO:
```bash
pio run -d smart_blind_stick -t upload
```

### Serial Monitor:
```bash
pio device monitor -b 115200
```

---

## 🧪 Browser Simulator (No Hardware Needed)

To test the responsive dashboard and Web Audio siren directly in your browser:
Open `smart_blind_stick/simulator/index.html` in Google Chrome, Safari, or Firefox.
Drag the distance slider below **20 cm** and watch the 10-second timer count down and trigger the emergency siren!

---

## 📂 Project Structure

```
smart_blind_stick/
├── platformio.ini         # PlatformIO build configuration for ESP8266
├── src/
│   ├── main.cpp           # Main C++ firmware (Hotspot, Fall Logic, Web Server)
│   └── index_html.h       # Embedded HTML5/CSS/JS Dashboard with Web Audio API
├── simulator/
│   └── index.html         # Standalone browser simulator
├── CIRCUIT_DIAGRAM.md     # Full circuit schematic and pin guide
├── PROJECT_REPORT.md      # Comprehensive project documentation
├── README.md              # Project overview
└── upload.sh              # One-click firmware build and flash script
```
