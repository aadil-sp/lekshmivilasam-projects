# Smart Farming Assistance Device (Agri-Assist Handheld)

A portable, handheld agricultural diagnostic device designed for precision farming, field testing, and greenhouse monitoring. Powered by an **Arduino Nano (ATmega328P)**, a **0.96" SSD1306 OLED display**, **3 tactile navigation buttons**, and an environmental sensor suite.

---

## 🌟 Key Features

- **Multi-Page Telemetry Interface:**
  - **Page 0 (Dashboard):** Master HUD presenting real-time summary of Soil Moisture, Ambient Temperature, Humidity, Sunlight Level, and crop status tags.
  - **Page 1 (Soil Moisture Sensor):** Volumetric water content percentage, raw 10-bit ADC reading, visual dynamic progress bar, and agronomic irrigation advice.
  - **Page 2 (Air Climate - DHT11):** Air temperature (°C / °F), relative humidity (%RH), visual humidity gauge, and microclimate risk warnings (Heat Stress, Chill, Fungal Disease).
  - **Page 3 (Sunlight - LDR):** Solar light intensity percentage, raw ADC voltage reading, visual solar bar, and crop photosynthetic condition.
- **Responsive 3-Button Navigation:**
  - **D2 (Left Button):** Cycle to previous screen (Page $3 \leftarrow 2 \leftarrow 1 \leftarrow 0$).
  - **D3 (Right Button):** Cycle to next screen (Page $0 \rightarrow 1 \rightarrow 2 \rightarrow 3$).
  - **D4 (Select / Back Button):** 
    - When on sub-pages (1, 2, or 3): **Instant return to Page 0 (Home Dashboard)**.
    - When on Page 0: Forces instant sensor re-sampling and toggles temperature display unit between Celsius (°C) and Fahrenheit (°F).
- **Zero External Pull-Up Resistors Required:** Utilizes ATmega328P internal `INPUT_PULLUP` circuitry for crisp, debounced tactile inputs.
- **AVR Memory-Optimized:** Flash string management (`F()` macro) ensures under **30% SRAM utilization**, avoiding the common SSD1306 framebuffer memory starvation crash on Arduino Nano.
- **Interactive Web Simulator Included:** Full in-browser simulation environment with virtual tactile buttons, analog sliders, and a pixel-accurate OLED renderer.

---

## 📐 Hardware Pinout

| Nano Pin | Peripheral Component | Description |
| :---: | :--- | :--- |
| **D2** | **Left Push Button** | Active LOW (Internal `INPUT_PULLUP`) |
| **D3** | **Right Push Button** | Active LOW (Internal `INPUT_PULLUP`) |
| **D4** | **Select / Back Button** | Active LOW (Internal `INPUT_PULLUP`) |
| **A0** | **Soil Moisture Sensor** | Analog 10-bit ADC Input ($0 - 1023$) |
| **A1** | **DHT11 Sensor Signal** | Digital One-Wire Interface |
| **A2** | **LDR Light Sensor Node** | Analog 10-bit ADC Input ($0 - 1023$) |
| **A4** | **OLED Display SDA** | Hardware I2C Data |
| **A5** | **OLED Display SCL** | Hardware I2C Clock |
| **5V** | **Power Bus** | Power for OLED and Sensors |
| **GND** | **Ground Bus** | Common 0V reference |

---

## 🚀 How to Flash & Run

### Method 1: Using PlatformIO CLI (Recommended)

1. Open your terminal in the `electronics2` directory:
   ```bash
   cd electronics2
   ```
2. Build the firmware:
   ```bash
   pio run
   ```
3. Connect your Arduino Nano via USB and flash:
   ```bash
   pio run --target upload
   ```
   *(Note: PlatformIO automatically handles dependencies for Adafruit SSD1306, Adafruit GFX, and DHT sensor library).*
4. Open the Serial Monitor at 115200 baud:
   ```bash
   pio device monitor -b 115200
   ```

### Method 2: Using the Arduino IDE

1. Open the Arduino IDE (v1.8.x or v2.x).
2. Open the sketch file:
   `electronics2/smart_farming_assistant/smart_farming_assistant.ino`
3. Go to **Tools $\rightarrow$ Manage Libraries...** and install:
   - `Adafruit SSD1306`
   - `Adafruit GFX Library`
   - `DHT sensor library` by Adafruit
4. Under **Tools $\rightarrow$ Board**, select **Arduino Nano**.
5. Under **Tools $\rightarrow$ Processor**, select **ATmega328P** (or *ATmega328P (Old Bootloader)* if using a CH340 clone).
6. Select your serial port and click **Upload**.

---

## 🖥️ Interactive Web Simulator

A complete browser simulator is located in `electronics2/simulator/index.html`.

To run it locally:
```bash
open electronics2/simulator/index.html
```
- Click on the virtual **Left (D2)**, **Right (D3)**, and **Select (D4)** buttons.
- Drag the **Soil Moisture**, **Temperature**, **Humidity**, and **Light Intensity** sliders to simulate real environmental field conditions.
- Keyboard shortcuts:
  - `←` Left Arrow: Previous Page
  - `→` Right Arrow: Next Page
  - `Enter` / `Space` / `Esc`: Select / Back to Dashboard

---

## 📊 Live Python Serial Telemetry Logger

Run the Python utility script to view colored telemetry logs and record readings to a CSV file:
```bash
python3 electronics2/listen_serial.py
```
Outputs timestamps, active screen index, raw ADC values, and formatted metrics directly to `farm_telemetry.csv`.

---

## 🌾 Agronomic Threshold Guide

| Metric | Range | Status / Advisory | Action Required |
| :--- | :--- | :--- | :--- |
| **Soil VWC** | $< 25\%$ | Critically Dry | Immediate drip / sprinkler irrigation required |
| **Soil VWC** | $30\% - 70\%$ | Optimal Growth Zone | Maintain current schedule |
| **Soil VWC** | $> 75\%$ | Waterlogged | Stop watering, improve sub-surface drainage |
| **Air Temp** | $> 35^\circ\text{C}$ | Heat Stress | Provide shade netting, increase misting |
| **Air Temp** | $< 15^\circ\text{C}$ | Chilling Hazard | Protect delicate saplings, greenhouse closing |
| **Humidity** | $> 80\%\text{RH}$ | High Fungal Risk | Increase cross-ventilation, inspect for blight |
| **Sunlight** | $< 20\%$ | Low / Dark | Insufficient light for sun-loving crops |
| **Sunlight** | $50\% - 80\%$ | Optimal Photosynthesis | Peak photosynthetic active radiation (PAR) |
