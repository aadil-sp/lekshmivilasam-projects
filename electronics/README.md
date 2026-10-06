# Health Monitor Band (Electronics)

**Category:** Electronics / State Sasthramela (Kerala)  
**Microcontroller:** ESP32-C3 RISC-V SoC (160MHz)  
**Status:** Firmware & Documentation Complete  

---

## 1. System Overview
A wearable medical telemetry & fall-detection bio-band built for geriatric care, solo patients, and hazardous environments. Features on-device biosignal processing, 0.96" monochrome OLED multi-screen menu navigation with 2 physical push buttons, and an off-grid Wi-Fi Captive Medical Portal (`192.168.4.1`).

## 2. Integrated Sensors & Hardware
- **ESP32-C3 RISC-V**: Wi-Fi + BLE, I2C, ADC, Captive DNS & HTTP Server.
- **MAX30102**: Optical PPG sensor measuring Heart Rate (BPM) & Blood Oxygen Saturation (SpO2).
- **MPU6050**: 6-Axis IMU (Accelerometer & Gyroscope) with dual-threshold Fall Detection algorithm.
- **DS18B20**: High-precision contact digital body temperature sensor (°C & °F).
- **GSR Electrodes**: Galvanic Skin Response / Electrodermal Activity (EDA) measuring sympathetic stress in $\mu S$.
- **0.96" SSD1306 OLED**: Monochrome 128x64 display with 5 switchable diagnostic pages.
- **Dual Tactile Buttons**: Mounted below display (BTN1: Scroll/Next on GPIO 9, BTN2: Select/Mute on GPIO 8).
- **Active Piezo Buzzer**: High-decibel pulsed acoustic siren for tachycardia, hypoxia, high fever, or fall events.
- **Power Subsystem**: 3.7V Li-Po battery with TP4056 USB-C charging and ADC battery monitoring.

## 3. Directory Layout & Deliverables
```
electronics/
├── src/
│   └── health_band_firmware/
│       └── health_band_firmware.ino    # Complete Arduino/ESP32-C3 firmware
├── simulator/
│   └── index.html                      # Interactive 0.96" OLED & Captive Portal Simulator
├── CIRCUIT_DIAGRAM.md                  # Pin mapping table, schematics & layout
├── PROJECT_REPORT.md                   # Full Kerala Sasthramela project report
├── PROJECT_REPORT.txt                  # Plain text copy of project report
├── generate_pdf.py                     # ReportLab PDF compilation script
└── Health_Monitor_Band_Sasthramela_Report.pdf  # Compiled printable PDF report
```

---

## Activity Log & Summary
- **[Init]**: Project workspace initialized for Kerala State Sasthramela.
- **[Firmware & Hardware Spec]**: Configured complete ESP32-C3 firmware integrating MAX30102, MPU6050, DS18B20, GSR stress sensor, active buzzer, dual-button navigation, and captive portal web server (`192.168.4.1`).
- **[Circuit Schematics]**: Documented comprehensive pin mapping table and schematic flow (`CIRCUIT_DIAGRAM.md`).
- **[Sasthramela Documentation & PDF]**: Created formal science fair report in Markdown (`PROJECT_REPORT.md`), plain text (`PROJECT_REPORT.txt`), and compiled a multi-page PDF (`Health_Monitor_Band_Sasthramela_Report.pdf`) including Viva Voce defense.
- **[Interactive Simulator]**: Built interactive 0.96" single-color OLED simulator with dual push buttons below the screen and synchronized smartphone captive portal dashboard (`simulator/index.html`).
