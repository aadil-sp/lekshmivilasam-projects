# Landslide Alert System (IoT)

**Category:** IoT / State Sasthramela (Kerala)  
**Microcontroller:** ESP32 Dual-Core Tensilica Xtensa (240MHz)  
**Status:** Firmware & Documentation Complete  

---

## 1. System Overview
An autonomous geo-hazard early warning station designed for the disaster-prone high ranges of the Western Ghats (Wayanad, Idukki). The station continuously tracks volumetric soil saturation, river/drainage surge velocity, ambient atmospheric conditions, and operates a custom automated siphoning rain gauge powered by a **12V Solenoid Flush Valve**. An embedded **TinyML Sensor Fusion Engine** runs multivariate hazard prediction at the edge, activating local high-decibel sirens and broadcasting telemetry to **Blynk IoT 2.0**.

## 2. Integrated Sensors & Hardware
- **ESP32 Microcontroller**: 240MHz Dual Core, Wi-Fi/BLE, Hardware ADC & Timers.
- **Soil Moisture Probe**: Analog capacitive/resistive VWC monitoring (GPIO 34).
- **Ultrasonic 1 (Stream Depth)**: HC-SR04 tracking riverbed depth & surge rate (GPIO 5 / 18).
- **Ultrasonic 2 (Rain Gauge)**: HC-SR04 tracking rainfall accumulation height inside a clear container (GPIO 19 / 21).
- **12V Solenoid Valve**: Auto-flushes rainwater when chamber reaches 135mm threshold, logging precise timestamp, incrementing count, and computing rain rate (GPIO 22 via Relay).
- **DHT22**: Precision ambient temperature and relative humidity (GPIO 4).
- **Active Evacuation Siren**: High-decibel audible alarm on critical risk (GPIO 23).
- **Status LEDs**: Green Safe (GPIO 2) / Red Alert (GPIO 15).
- **Cloud Telemetry**: Blynk IoT 2.0 Virtual Pins (`V0`-`V8`) with push notifications.

## 3. Directory Layout & Deliverables
```
iot/
├── src/
│   └── landslide_iot_firmware/
│       └── landslide_iot_firmware.ino       # Full ESP32 + TinyML + Blynk firmware
├── simulator/
│   └── index.html                           # Interactive Siphon Rain Gauge & Blynk Simulator
├── CIRCUIT_DIAGRAM.md                       # Pin mapping table, schematics & layout
├── PROJECT_REPORT.md                        # Formal Kerala Sasthramela project report
├── PROJECT_REPORT.txt                       # Plain text copy of project report
├── generate_pdf.py                          # ReportLab PDF compilation script
└── Landslide_Alert_System_Sasthramela_Report.pdf  # Compiled printable PDF report
```

---

## Activity Log & Summary
- **[Init]**: Initialized IoT workspace for Kerala State Sasthramela.
- **[Firmware & TinyML Engine]**: Built complete ESP32 firmware integrating dual ultrasonic sensors, soil moisture ADC, DHT22, 12V solenoid siphoning logic with timestamp logging, embedded TinyML logistic regression classifier, and Blynk IoT 2.0 telemetry.
- **[Circuit Schematics]**: Created comprehensive pinout guide, voltage divider level-shifting, and schematic architecture (`CIRCUIT_DIAGRAM.md`).
- **[Sasthramela Documentation & PDF]**: Generated complete science fair documentation (`PROJECT_REPORT.md`, `PROJECT_REPORT.txt`) and compiled a multi-page PDF (`Landslide_Alert_System_Sasthramela_Report.pdf`) with theoretical foundations, Terzaghi's effective stress formula, and Viva Voce defense.
- **[Interactive Simulator]**: Developed real-time web simulator modeling the automated rain catchment chamber, solenoid flush cycle, sensor controls, on-device TinyML gauge, and Blynk cloud dashboard (`simulator/index.html`).
