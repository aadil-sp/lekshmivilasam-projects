# AgroSense Handheld: Portable Multi-Spectral Smart Farming Field Assistance Device

**Category:** Applied Electronics & Agricultural Automation  
**Platform:** Arduino Nano (ATmega328P AVR Architecture)  
**State Science Fair Competition Portfolio**  
**Status:** Hardware Verified & Firmware Validated  

---

## 1. Abstract & Executive Summary
Agricultural yields across smallholder farms are heavily compromised by uncalibrated manual irrigation, localized micro-climate heat stress, and sub-optimal sunlight exposure. While macro-meteorological forecasts provide general regional weather trends, they fail to capture field-level soil hydraulics and micro-climatic variations.

**AgroSense Handheld** is a portable, field-ready agricultural intelligence device developed on the Arduino Nano platform. It integrates a 0.96" SSD1306 monochrome graphic OLED HUD, a 3-button tactile field navigation interface (D2 Left, D3 Right, D4 Select/Back), an analog soil volumetric water content probe (A0), a DHT11 atmospheric humidity/temperature sensor (D5), and a wide-spectrum light dependent resistor (LDR on A1). The device implements a multi-page interactive operating HUD featuring an aggregated Farm Health Index, individual sensor diagnostic deep-dives, automated agronomic classification, and unit toggling—all executing on an ultra-compact embedded budget of under ₹750 ($9).

---

## 2. Problem Statement & Agronomic Significance
1. **Soil Over-Irrigation & Under-Irrigation:** Over-irrigation causes nutrient leaching, soil anaerobic conditions, and root fungal rot, whereas moisture deficit past the permanent wilting point triggers irreversible cellular dehydration.
2. **Vapor Pressure Deficit (VPD) Blindspots:** Atmospheric temperature and humidity dictate plant stomatal conductance. High heat with low humidity causes excessive transpiration shock, while high humidity creates mold spore outbreaks.
3. **Photoperiod & Light Saturation:** Insufficient light retards Calvin cycle carbon fixation, while excessive direct solar radiation causes photo-inhibition and leaf scalding.
4. **Lack of Affordable Handheld Tools:** Commercial soil multi-testers cost upwards of ₹12,000 to ₹35,000, placing them beyond the reach of rural farmers and school research stations.

---

## 3. Mathematical Foundations & Scientific Formulation

### A. Soil Volumetric Water Content (VWC) Calibration
The analog soil probe measures impedance based on the dielectric permittivity and conductive ion concentration of moist soil. Volumetric water content $\theta$ is mapped via piece-wise linear calibration:
$$\theta = \left( \frac{\text{ADC}_{\text{dry}} - \text{ADC}_{\text{measured}}}{\text{ADC}_{\text{dry}} - \text{ADC}_{\text{saturated}}} \right) \times 100\%$$
Where:
* $\text{ADC}_{\text{dry}} \approx 950$ (Dry air baseline)
* $\text{ADC}_{\text{saturated}} \approx 300$ (Full saturation)

### B. Rothfusz Heat Index Formulation
To predict thermal stress on leafy vegetative crops, the firmware calculates the apparent thermal index combining dry-bulb temperature ($T$ in °F) and relative humidity ($R$ in %):
$$\text{HI} = -42.379 + 2.04901523T + 10.14333127R - 0.22475541TR - 0.00683783T^2 - 0.05481717R^2 + 0.00122874T^2R + 0.00085282TR^2 - 0.00000199T^2R^2$$

### C. Solar Photometric Illuminance Approximation
Using the empirical power-law transfer function of cadmium-sulfide (CdS) photoresistors:
$$R_{\text{LDR}} = 10{,}000 \times \left( \frac{1023 - \text{ADC}_{\text{LDR}}}{\text{ADC}_{\text{LDR}}} \right)$$
$$\text{Illuminance (Lux)} \approx \left( \frac{500 \times 10^3}{R_{\text{LDR}}} \right)^{1.4}$$

---

## 4. UI Architecture & Button Navigation Matrix

The firmware implements a debounced Finite State Machine (FSM) cycling across 4 dedicated screens:

```
[Page 0: AgroDash Home HUD]
         │
         ├── Press D3 (Right) ────> [Page 1: Soil Hydraulics]
         │                                   │
         ├── Press D3 (Right) <──────────────┘
         │
         ├── Press D3 (Right) ────> [Page 2: Micro-Climate (DHT11)]
         │                                   │
         ├── Press D3 (Right) <──────────────┘
         │
         └── Press D3 (Right) ────> [Page 3: Solar Photometrics (LDR)]
                                             │
             Press D3 (Right) <──────────────┘ (Wraps back to Page 0)
```

### Button Mapping:
* **Pin D2 (Left Button):** Decrements page index (`currentPage--`). Wraps to Page 3 if decremented from Page 0.
* **Pin D3 (Right Button):** Increments page index (`currentPage++`). Wraps to Page 0 if incremented from Page 3.
* **Pin D4 (Select / Back Button):**
  * *On Page 0:* Toggles **Auto-Cycle Mode** (automatically advances page every 4 seconds).
  * *On Page 1:* Triggers an instant forced ADC re-sample and zero-calibration.
  * *On Page 2:* Toggles temperature unit display between Celsius (°C) and Fahrenheit (°F).
  * *On Page 3:* Returns navigation immediately to Page 0.
  * *Long Press (>700ms anywhere):* Master return to Page 0 Home Dashboard.

---

## 5. Bill of Materials (BOM) & Cost Analysis

| Component | Technical Specifications | Qty | Cost (INR) | Functional Role |
| :--- | :--- | :---: | :---: | :--- |
| **Arduino Nano** | ATmega328P 16MHz, CH340 USB, 5V Logic | 1 | ₹240 | Core FSM Controller & ADC Processor |
| **0.96" SSD1306 OLED** | 128x64 pixels, I2C interface, 0.08W power | 1 | ₹180 | Visual Telemetry & HUD Display |
| **Soil Moisture Sensor** | Corrosion-resistant probe with comparator board | 1 | ₹65 | Volumetric Root-Zone Moisture Tracking |
| **DHT11 Sensor** | 0-50°C, 20-90% RH digital one-wire sensor | 1 | ₹85 | Ambient Micro-Climate Measurement |
| **LDR Photoresistor** | 5mm CdS sensor + 10kΩ metal film resistor | 1 | ₹15 | Sunlight Intensity & Photoperiod |
| **Tactile Push Buttons** | 6x6x5mm PCB momentary switches | 3 | ₹15 | Field User Input & Page Navigation |
| **Breadboard & Wires** | Mini breadboard + Dupont jumper cables | 1 | ₹70 | Modular Interconnection |
| **9V Battery / Clip** | Heavy-duty 9V cell with DC barrel / Vin clip | 1 | ₹40 | Portable Handheld Field Power |
| **TOTAL COST** | **Complete Portable Field Prototype** | — | **₹710** | **~96% Cost Savings vs Commercial Units** |

---

## 6. Judges' Viva Voce Defense Guide

### Q1: Why use an analog soil moisture probe instead of digital switching?
**Defense:** Digital soil sensor modules only output a high/low binary trigger based on an arbitrary potentiometer threshold. In precision agriculture, binary signals fail to show soil drying rate or moisture gradients. Our design reads the full 10-bit analog ADC range (0–1023), computing exact volumetric moisture percentage and water retention decay curves.

### Q2: How does the system handle button contact bouncing?
**Defense:** Mechanical tactile switches generate electrical contact noise lasting 5 to 20ms during closure. Our firmware implements a non-blocking software debounce filter using `millis()` timing with a 180ms refractory period. This completely eliminates page flickering and accidental double-skips without freezing the CPU using blocking `delay()` calls.

### Q3: Why is the I2C bus clocked at 400kHz instead of standard 100kHz?
**Defense:** Refreshing a 128x64 monochrome OLED buffer requires sending 1,024 bytes of frame data plus commands. At 100kHz standard mode, a full redraw consumes ~102ms (dropping frame rate to ~9 FPS). Elevating the ATmega328P Two-Wire Interface (TWI) to 400kHz Fast Mode reduces redraw latency to ~26ms, achieving smooth 25 FPS animations with zero flicker.

### Q4: How does this handheld prototype benefit rural smallholder farmers?
**Defense:** Commercial agronomic multi-testers cost between ₹12,000 and ₹35,000, making them completely unaffordable for average farmers. AgroSense delivers instant field-level diagnostic accuracy for under ₹750, empowering farmers to prevent crop water stress, optimize irrigation pump schedules, and maximize crop yields.
