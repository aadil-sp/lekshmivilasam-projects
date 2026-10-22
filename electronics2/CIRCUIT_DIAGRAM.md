# Circuit Diagram & Hardware Wiring Guide
## Smart Farming Field Assistance Device (Handheld Agri-Meter)

---

### 1. Hardware Bill of Materials (BOM)

| Component | Specification | Quantity | Purpose |
| :--- | :--- | :---: | :--- |
| **Microcontroller** | **Arduino Nano** (ATmega328P, 5V, 16MHz) | 1 | Central processor & ADC computation |
| **Display** | **0.96" I2C Monochrome OLED** (SSD1306, 128x64) | 1 | Compact handheld telemetry HUD |
| **Navigation Buttons** | **Tactile Push Buttons** (6x6mm or 12x12mm) | 3 | Left (D2), Right (D3), Select/Back (D4) |
| **Soil Sensor** | **Soil Moisture Sensor Module** (Resistive / Capacitive) | 1 | Volumetric water content sensing (Pin A0) |
| **Climate Sensor** | **DHT11 Sensor** (Digital One-Wire on Pin A1) | 1 | Ambient air temperature & relative humidity |
| **Light Sensor** | **LDR (Photoresistor)** + 10kΩ Resistor | 1 | Solar radiation & photometrics (Pin A2) |
| **Prototyping** | Mini Breadboard / Stripboard / Perfboard + Jumper Wires | - | Handheld enclosure wiring |
| **Power Supply** | 9V Battery with DC clip **OR** 18650 Li-ion + 5V Boost | 1 | Portable field power source |

---

### 2. Complete Pin Connection Mapping Table

| Arduino Nano Pin | Connected Device / Pin | Function / Direction | Electrical Notes |
| :--- | :--- | :--- | :--- |
| **D2** | **Left Push Button** (Pin 1) | Digital Input (`INPUT_PULLUP`) | Other button terminal to **GND**. Active **LOW**. |
| **D3** | **Right Push Button** (Pin 1) | Digital Input (`INPUT_PULLUP`) | Other button terminal to **GND**. Active **LOW**. |
| **D4** | **Select / Back Button** (Pin 1) | Digital Input (`INPUT_PULLUP`) | Other button terminal to **GND**. Active **LOW**. |
| **A0** | **Soil Moisture Sensor (SIG / AOUT)** | Analog Input (`0 - 1023 ADC`) | Submerged probe measures soil impedance. |
| **A1** | **DHT11 Sensor (DATA / OUT)** | Digital Single-Bus on Pin A1 | High-speed bidirectional communication. |
| **A2** | **LDR Light Sensor (Divider Node)** | Analog Input (`0 - 1023 ADC`) | Voltage divider with 10kΩ pull-down to GND. |
| **A4** | **OLED Display SDA** | Hardware I2C Serial Data | ATmega328P hardware I2C data bus. |
| **A5** | **OLED Display SCL** | Hardware I2C Serial Clock | ATmega328P hardware I2C clock bus (400 kHz). |
| **5V** | OLED VCC, Soil VCC, DHT11 VCC, LDR Top Rail | Power Distribution (+5V DC) | Clean regulated 5V power bus. |
| **GND** | OLED GND, Soil GND, DHT11 GND, LDR 10k, Buttons | Ground Bus (0V Common) | Common ground reference across all modules. |
| **VIN** | 9V Battery (+) Red Wire (if using 9V battery) | Power Input (7V - 12V DC) | Feeds Nano's onboard AMS1117 5V regulator. |

---

### 3. Push Button Circuit Architecture (Internal Pull-Up)

```
        Arduino Nano Pin
        (D2, D3, or D4)
              │
              ├───[ Internal 20kΩ Pull-Up Resistor inside ATmega328P ]─── +5V (VCC)
              │
             ┌┴┐
             │ │  Normally Open Tactile Push Button
             └┬┘
              │
             GND (Ground)
```

> [!TIP]
> **Why No External Resistors for the Buttons?**
> The firmware configures `pinMode(pin, INPUT_PULLUP)`. This activates the internal ~20kΩ pull-up resistor inside the ATmega328P chip. 
> - **When button is unpressed (open):** Pin reads `HIGH` (5V).
> - **When button is pressed (closed):** Pin is tied directly to `GND` and reads `LOW` (0V).
> This eliminates 3 external resistors, reducing handheld enclosure clutter and wiring failure points.

---

### 4. LDR (Light Dependent Resistor) Voltage Divider Circuit

```
              +5V (Power Rail)
                     │
                    ┌┴┐
                    │ │  LDR (Photoresistor)
                    └┬┘
                     ├─── To Arduino Nano Pin A2 (Analog In)
                    ┌┴┐
                    │ │  10kΩ Fixed Resistor (Brown-Black-Orange)
                    └┬┘
                     │
                    GND (Ground Rail)
```

- In **Bright Sunlight**: LDR resistance drops to ~500Ω–1kΩ $\rightarrow$ Voltage at Pin A2 rises towards **4.5V–5V** (Raw ADC: **850–1000**).
- In **Darkness / Night**: LDR resistance surges to >100kΩ $\rightarrow$ Voltage at Pin A2 drops towards **0.2V–0.5V** (Raw ADC: **40–120**).

---

### 5. Soil Moisture Sensor Connection

```
  Soil Moisture Module              Arduino Nano
  ┌───────────────────┐             ┌────────────┐
  │  VCC              ├─────────────┤ 5V         │
  │  GND              ├─────────────┤ GND        │
  │  AOUT (Analog Out)├─────────────┤ A0         │
  │  DOUT (Digital Out) (Unused)    │            │
  └───────────────────┘             └────────────┘
```

> [!NOTE]
> The probe prongs measure electrical conductivity between the two electrodes. Drier soil has fewer electrolytes and air pockets, resulting in high resistance (ADC ~900–1023). Moist soil conducts readily, dropping the ADC to ~200–400. The code inverts and maps this cleanly to $0\% - 100\%$.

---

### 6. DHT11 Micro-Climate Connection

```
  DHT11 Sensor (3-pin or 4-pin)     Arduino Nano
  ┌───────────────────┐             ┌────────────┐
  │  Pin 1: VCC (+)   ├─────────────┤ 5V         │
  │  Pin 2: DATA (OUT)├─────────────┤ A1         │
  │  Pin 3: NC        │             │            │
  │  Pin 4: GND (-)   ├─────────────┤ GND        │
  └───────────────────┘             └────────────┘
```

*(Note: If using bare 4-pin DHT11 without a PCB module, connect a 4.7kΩ to 10kΩ pull-up resistor between VCC and DATA).*

---

### 7. OLED Display (SSD1306 128x64 I2C) Connection

```
  SSD1306 0.96" OLED                Arduino Nano
  ┌───────────────────┐             ┌────────────┐
  │  GND              ├─────────────┤ GND        │
  │  VCC              ├─────────────┤ 5V         │
  │  SCL (Clock)      ├─────────────┤ A5         │
  │  SDA (Data)       ├─────────────┤ A4         │
  └───────────────────┘             └────────────┘
```

---

### 8. Master System Schematic Diagram

```
                        ┌──────────────────────────────────────┐
                        │          ARDUINO NANO                │
                        │                                      │
       [LEFT BTN] ──D2──┤ D2 (PULLUP)                      5V  ├─── +5V (VCC Bus)
      [RIGHT BTN] ──D3──┤ D3 (PULLUP)                     GND  ├─── GND (Common)
     [SELECT BTN] ──D4──┤ D4 (PULLUP)                     VIN  ├─── +9V Batt (+)
                        │                                      │
   [SOIL AOUT] ────A0───┤ A0 (Soil ADC)                    A5  ├─── OLED SCL
   [DHT11 DATA] ───A1───┤ A1 (DHT11 Digital)               A4  ├─── OLED SDA
     [LDR NODE] ───A2───┤ A2 (Light ADC)                       │
                        └──────────────────────────────────────┘
                                  │                     │
                     ┌────────────┴───┐     ┌───────────┴────┐
                     │ SSD1306 OLED   │     │ Power Supply   │
                     │  - VCC -> 5V   │     │  - 9V Battery  │
                     │  - GND -> GND  │     │  - OR 18650    │
                     │  - SCL -> A5   │     │    3.7V Boost  │
                     │  - SDA -> A4   │     │    to 5V       │
                     └────────────────┘     └────────────────┘
```

---

### 9. Handheld Battery Power Solutions

For field portability across a farm or greenhouse, use one of the following battery options:
1. **9V Alkaline Battery (Simplest):**
   - Connect 9V (+) Red wire to Arduino **VIN** pin.
   - Connect 9V (-) Black wire through a miniature toggle power switch to Arduino **GND**.
   - Nano's internal regulator safely converts 9V down to stable 5V.
2. **Rechargeable 18650 Li-ion Cell (Recommended for Daily Use):**
   - 18650 Cell (3.7V nominal) $\rightarrow$ TP4056 Micro-USB Charging & Protection Module $\rightarrow$ MT3608 Step-Up Boost Converter (adjusted to 5.0V output) $\rightarrow$ Arduino **5V** and **GND** pins.
   - Provides 2000–3000 mAh capacity for over **18+ continuous hours** of handheld field testing!
