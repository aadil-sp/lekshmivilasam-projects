/**
 * ============================================================================
 * Project: Smart Farming Assistance Device (Agri-Assist Handheld)
 * Target Microcontroller: Arduino Nano (ATmega328P, 5V, 16MHz)
 * Display: 0.96" Monochrome I2C OLED (SSD1306, 128x64)
 * Navigation: 3 Tactile Push Buttons (Left: D2, Right: D3, Select/Back: D4)
 *
 * Sensors:
 *   1. Soil Moisture Sensor (Analog): Pin A0 (ADC 0-1023)
 *   2. DHT11 Temp & Humidity Sensor: Pin A1 (Digital IO mode on Pin A1)
 *   3. LDR Light Sensor (Analog): Pin A2 (ADC 0-1023)
 *
 * Display Layout:
 *   - Page 0: Home Dashboard (Overview of all 3 sensors + agronomic health)
 *   - Page 1: Soil Moisture Details (Raw ADC, %, Progress Bar, Irrigation Advice)
 *   - Page 2: Micro-Climate Details (Temp in °C/°F, Humidity %, Heat Index, Crop Risk)
 *   - Page 3: Sunlight & Photometrics (Raw ADC, Light %, Progress Bar, Lighting Status)
 * ============================================================================
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <DHT.h>

// ==================== HARDWARE PIN CONFIGURATION ====================
// 3 Push Buttons (Using internal INPUT_PULLUP: Pressed = LOW, Idle = HIGH)
#define BTN_LEFT_PIN      2    // Pin D2: Previous Page (Left)
#define BTN_RIGHT_PIN     3    // Pin D3: Next Page (Right)
#define BTN_SELECT_PIN    4    // Pin D4: Select / Back to Home Dashboard

// Sensors (Grouped cleanly on Arduino Nano Analog Pins)
#define SOIL_PIN          A0   // Soil Moisture Sensor (Analog In 0-1023)
#define DHT_PIN           A1   // DHT11 Sensor Signal Pin (Pin A1 / Digital 15)
#define LDR_PIN           A2   // LDR Light Sensor (Analog In 0-1023)
#define DHT_TYPE          DHT11

// OLED Display Configuration (I2C: SCL = Pin A5, SDA = Pin A4)
#define SCREEN_WIDTH      128
#define SCREEN_HEIGHT     64
#define OLED_RESET        -1   // Shared reset pin (-1 if no dedicated reset pin)
#define SCREEN_ADDRESS    0x3C // 0x3C is standard for 0.96" SSD1306 (or 0x3D)

// ==================== SENSOR CALIBRATION CONSTANTS ====================
// Typical resistive soil sensor: in dry air ~950-1023, in tap water ~250-350
// Invert logic: High ADC = Dry (0%), Low ADC = Saturated (100%)
#define SOIL_AIR_RAW      950
#define SOIL_WATER_RAW    280

// LDR calibration with 10k pull-down: Dark ~50-100, Direct light ~900-1000
#define LDR_DARK_RAW      60
#define LDR_SUN_RAW       950

// ==================== GLOBAL OBJECTS & STATE ====================
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
DHT dht(DHT_PIN, DHT_TYPE);

// Navigation State
// 0 = Dashboard (Home), 1 = Soil Moisture, 2 = Climate (DHT11), 3 = Solar/LDR
uint8_t currentPage = 0;
const uint8_t TOTAL_PAGES = 4;

// Button Debounce and State Tracking
uint8_t lastLeftReading   = HIGH;
uint8_t lastRightReading  = HIGH;
uint8_t lastSelectReading = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long DEBOUNCE_DELAY_MS = 180;

// Sensor Data Storage
int   soilRaw = 0;
int   soilPercent = 0;
float dhtTemp = 28.0;
float dhtHumidity = 65.0;
bool  dhtValid = false;
int   ldrRaw = 0;
int   ldrPercent = 0;

// System Diagnostics & UI Pulse
uint8_t heartbeatTick = 0;
bool showFahrenheit = false;

// Non-blocking Timing Loops
unsigned long lastFastSensorRead = 0;
unsigned long lastDhtRead = 0;
unsigned long lastDisplayUpdate = 0;

// ==================== HELPER FUNCTIONS ====================

// Read Soil Moisture Sensor (Analog Pin A0)
void readSoilSensor() {
  soilRaw = analogRead(SOIL_PIN);
  // Resistive sensor: higher ADC means drier soil
  int mapped = map(soilRaw, SOIL_AIR_RAW, SOIL_WATER_RAW, 0, 100);
  soilPercent = constrain(mapped, 0, 100);
}

// Read LDR Light Sensor (Analog Pin A2)
void readLdrSensor() {
  ldrRaw = analogRead(LDR_PIN);
  int mapped = map(ldrRaw, LDR_DARK_RAW, LDR_SUN_RAW, 0, 100);
  ldrPercent = constrain(mapped, 0, 100);
}

// Read DHT11 Temperature & Humidity (Pin A1)
void readDhtSensor() {
  float h = dht.readHumidity();
  float t = dht.readTemperature(); // Reading Celsius

  if (isnan(h) || isnan(t)) {
    dhtValid = false;
  } else {
    dhtValid = true;
    dhtHumidity = h;
    dhtTemp = t;
  }
}

// Draw a smooth bordered horizontal progress bar
void drawProgressBar(int16_t x, int16_t y, int16_t w, int16_t h, int percent) {
  display.drawRect(x, y, w, h, SSD1306_WHITE);
  int fillW = (int)((long)(w - 4) * percent / 100);
  fillW = constrain(fillW, 0, w - 4);
  if (fillW > 0) {
    display.fillRect(x + 2, y + 2, fillW, h - 4, SSD1306_WHITE);
  }
}

// Draw unified footer navigation bar with page dots and button hints
void drawFooterNav(uint8_t page) {
  display.drawLine(0, 53, 127, 53, SSD1306_WHITE);

  // Left & Right navigation hints
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(2, 55);
  display.print(F("<D2"));

  display.setCursor(104, 55);
  display.print(F("D3>"));

  // Centered Pagination Dots: [*] [ ] [ ] [ ]
  int startX = 45;
  for (uint8_t i = 0; i < TOTAL_PAGES; i++) {
    int dotX = startX + (i * 10);
    if (i == page) {
      display.fillCircle(dotX, 58, 2, SSD1306_WHITE);
    } else {
      display.drawCircle(dotX, 58, 2, SSD1306_WHITE);
    }
  }
}

// ==================== OLED PAGE RENDERERS ====================

// -------------------------------------------------------------
// PAGE 0: SMART FARMING DASHBOARD (HOME OVERVIEW)
// -------------------------------------------------------------
void renderDashboard() {
  // Header bar with system heartbeat icon
  display.fillRect(0, 0, 128, 11, SSD1306_WHITE);
  display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(6, 2);
  display.print(F("SMART FARM DASHBOARD"));

  // Pulsing activity indicator in top-right corner
  heartbeatTick = (heartbeatTick + 1) % 4;
  if (heartbeatTick < 2) {
    display.fillCircle(122, 5, 2, SSD1306_BLACK);
  } else {
    display.drawCircle(122, 5, 2, SSD1306_BLACK);
  }

  display.setTextColor(SSD1306_WHITE);

  // 1. Soil Overview
  display.setCursor(2, 14);
  display.print(F("SOIL: "));
  display.print(soilPercent);
  display.print(F("% "));
  if (soilPercent < 30) {
    display.print(F("[DRY:IRRIGATE]"));
  } else if (soilPercent <= 70) {
    display.print(F("[OPTIMAL]"));
  } else {
    display.print(F("[WATERLOGGED]"));
  }

  // 2. Air / Climate Overview
  display.setCursor(2, 26);
  display.print(F("AIR : "));
  if (dhtValid) {
    if (showFahrenheit) {
      int tempF = (int)((dhtTemp * 1.8) + 32.0);
      display.print(tempF);
      display.print(F("F "));
    } else {
      display.print((int)dhtTemp);
      display.print((char)247); // Degree symbol
      display.print(F("C "));
    }
    display.print(F("| HUM: "));
    display.print((int)dhtHumidity);
    display.print(F("%"));
  } else {
    display.print(F("DHT11 CONNECTING.."));
  }

  // 3. Sunlight Overview
  display.setCursor(2, 38);
  display.print(F("SUN : "));
  display.print(ldrPercent);
  display.print(F("% "));
  if (ldrPercent < 20) {
    display.print(F("[NIGHT/DARK]"));
  } else if (ldrPercent <= 75) {
    display.print(F("[GOOD LIGHT]"));
  } else {
    display.print(F("[BRIGHT SUN]"));
  }

  // 4. Action bar hint
  display.setCursor(26, 46);
  display.print(F("[D4: Back/Info]"));

  drawFooterNav(0);
}

// -------------------------------------------------------------
// PAGE 1: SOIL MOISTURE SENSOR DETAILS (ANALOG A0)
// -------------------------------------------------------------
void renderSoilPage() {
  // Title Bar
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.print(F("PAGE 1: SOIL MOISTURE"));
  display.drawLine(0, 9, 127, 9, SSD1306_WHITE);

  // Raw ADC Value & Pin info
  display.setCursor(2, 12);
  display.print(F("Analog Pin: A0 (ADC)"));
  display.setCursor(2, 21);
  display.print(F("Raw: "));
  display.print(soilRaw);
  display.print(F(" / 1023"));

  // Moisture Percentage Display
  display.setCursor(76, 21);
  display.print(F("VWC: "));
  display.print(soilPercent);
  display.print(F("%"));

  // Moisture Graphic Gauge Bar
  drawProgressBar(2, 31, 124, 7, soilPercent);

  // Agricultural Agronomic Status
  display.setCursor(2, 42);
  display.print(F("Advice: "));
  if (soilPercent < 25) {
    display.print(F("CRITICAL! IRRIGATE"));
  } else if (soilPercent < 45) {
    display.print(F("DRY - SCHEDULE WATER"));
  } else if (soilPercent <= 75) {
    display.print(F("OPTIMAL ROOT MOIST"));
  } else {
    display.print(F("WET - DRAINAGE ALERT"));
  }

  drawFooterNav(1);
}

// -------------------------------------------------------------
// PAGE 2: AIR CLIMATE SENSOR DETAILS (DHT11 PIN A1)
// -------------------------------------------------------------
void renderClimatePage() {
  // Title Bar
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.print(F("PAGE 2: AIR & CLIMATE"));
  display.drawLine(0, 9, 127, 9, SSD1306_WHITE);

  if (dhtValid) {
    // Temperature Display
    display.setCursor(2, 12);
    display.print(F("Temp: "));
    display.print(dhtTemp, 1);
    display.print((char)247);
    display.print(F("C ("));
    float tempF = (dhtTemp * 1.8) + 32.0;
    display.print((int)tempF);
    display.print(F("F)"));

    // Relative Humidity Display
    display.setCursor(2, 22);
    display.print(F("Humidity: "));
    display.print(dhtHumidity, 1);
    display.print(F(" %RH"));

    // Humidity Graphic Gauge Bar
    drawProgressBar(2, 32, 124, 7, (int)dhtHumidity);

    // Farm Climate Assessment
    display.setCursor(2, 42);
    display.print(F("Env: "));
    if (dhtTemp > 35.0) {
      display.print(F("HEAT STRESS ON CROPS"));
    } else if (dhtTemp < 15.0) {
      display.print(F("CHILLING / COLD RISK"));
    } else if (dhtHumidity > 80.0) {
      display.print(F("HIGH FUNGAL DISEASE"));
    } else {
      display.print(F("HEALTHY MICROCLIMATE"));
    }
  } else {
    display.setCursor(2, 18);
    display.print(F("DHT11 Sensor Signal"));
    display.setCursor(2, 28);
    display.print(F("Listening on Pin A1..."));
    display.setCursor(2, 40);
    display.print(F("Check 5V, GND, Pin A1"));
  }

  drawFooterNav(2);
}

// -------------------------------------------------------------
// PAGE 3: SOLAR RADIATION & LIGHT DETAILS (LDR PIN A2)
// -------------------------------------------------------------
void renderLightPage() {
  // Title Bar
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.print(F("PAGE 3: SOLAR LIGHT"));
  display.drawLine(0, 9, 127, 9, SSD1306_WHITE);

  // Raw ADC Value & Pin info
  display.setCursor(2, 12);
  display.print(F("Analog Pin: A2 (LDR)"));
  display.setCursor(2, 21);
  display.print(F("Raw: "));
  display.print(ldrRaw);
  display.print(F(" / 1023"));

  // Light Percentage Display
  display.setCursor(74, 21);
  display.print(F("Lum: "));
  display.print(ldrPercent);
  display.print(F("%"));

  // Sunlight Level Graphic Gauge Bar
  drawProgressBar(2, 31, 124, 7, ldrPercent);

  // Photosynthesis Status
  display.setCursor(2, 42);
  display.print(F("Sun: "));
  if (ldrPercent < 15) {
    display.print(F("NIGHT / SHADOWED"));
  } else if (ldrPercent < 45) {
    display.print(F("LOW LIGHT (SHADE)"));
  } else if (ldrPercent <= 80) {
    display.print(F("GOOD PHOTOSYNTHESIS"));
  } else {
    display.print(F("HIGH SOLAR SCORCH"));
  }

  drawFooterNav(3);
}

// Master Render Dispatcher
void updateDisplay() {
  display.clearDisplay();

  switch (currentPage) {
    case 0:
      renderDashboard();
      break;
    case 1:
      renderSoilPage();
      break;
    case 2:
      renderClimatePage();
      break;
    case 3:
      renderLightPage();
      break;
    default:
      currentPage = 0;
      renderDashboard();
      break;
  }

  display.display();
}

// ==================== BUTTON NAVIGATION LOGIC ====================
void handleButtons() {
  unsigned long currentMillis = millis();
  if (currentMillis - lastDebounceTime < DEBOUNCE_DELAY_MS) {
    return;
  }

  int leftState   = digitalRead(BTN_LEFT_PIN);
  int rightState  = digitalRead(BTN_RIGHT_PIN);
  int selectState = digitalRead(BTN_SELECT_PIN);

  // 1. Left Button Pressed (Active LOW on Pin D2) -> Previous Page
  if (leftState == LOW && lastLeftReading == HIGH) {
    lastDebounceTime = currentMillis;
    if (currentPage == 0) {
      currentPage = TOTAL_PAGES - 1; // Wrap around to Page 3
    } else {
      currentPage--;
    }
    Serial.print(F("[NAV] D2 Pressed -> Page "));
    Serial.println(currentPage);
  }

  // 2. Right Button Pressed (Active LOW on Pin D3) -> Next Page
  if (rightState == LOW && lastRightReading == HIGH) {
    lastDebounceTime = currentMillis;
    currentPage = (currentPage + 1) % TOTAL_PAGES;
    Serial.print(F("[NAV] D3 Pressed -> Page "));
    Serial.println(currentPage);
  }

  // 3. Select / Back Button Pressed (Active LOW on Pin D4)
  if (selectState == LOW && lastSelectReading == HIGH) {
    lastDebounceTime = currentMillis;
    if (currentPage != 0) {
      // If inside Page 1, 2, or 3: JUMP DIRECTLY BACK TO DASHBOARD (Page 0)
      currentPage = 0;
      Serial.println(F("[NAV] D4 Select/Back -> Jump to Dashboard (Page 0)"));
    } else {
      // If already on Dashboard: Toggle °C <-> °F or force sensor refresh
      showFahrenheit = !showFahrenheit;
      readSoilSensor();
      readLdrSensor();
      readDhtSensor();
      Serial.println(F("[NAV] D4 Select -> Refresh Sensors & Toggle Unit"));
    }
  }

  lastLeftReading   = leftState;
  lastRightReading  = rightState;
  lastSelectReading = selectState;
}

// Print Diagnostics to Serial Monitor for USB Telemetry
void printSerialDiagnostics() {
  Serial.print(F("[DATA] Soil A0: "));
  Serial.print(soilRaw);
  Serial.print(F(" ("));
  Serial.print(soilPercent);
  Serial.print(F("%) | LDR A2: "));
  Serial.print(ldrRaw);
  Serial.print(F(" ("));
  Serial.print(ldrPercent);
  Serial.print(F("%) | Temp: "));
  if (dhtValid) {
    Serial.print(dhtTemp, 1);
    Serial.print(F("C | Hum: "));
    Serial.print(dhtHumidity, 1);
    Serial.print(F("%"));
  } else {
    Serial.print(F("DHT_WAIT"));
  }
  Serial.print(F(" | Active Page: "));
  Serial.println(currentPage);
}

// ==================== ARDUINO SETUP & LOOP ====================
void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println(F("=============================================="));
  Serial.println(F("   SMART FARMING ASSISTANCE DEVICE (NANO)     "));
  Serial.println(F("=============================================="));

  // Initialize Push Buttons with Internal Pull-Ups
  pinMode(BTN_LEFT_PIN, INPUT_PULLUP);
  pinMode(BTN_RIGHT_PIN, INPUT_PULLUP);
  pinMode(BTN_SELECT_PIN, INPUT_PULLUP);

  // Initialize Analog Sensors
  pinMode(SOIL_PIN, INPUT);
  pinMode(LDR_PIN, INPUT);

  // Initialize DHT11 Sensor on Pin A1
  dht.begin();

  // Initialize OLED Display (I2C Address 0x3C)
  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("ERROR: OLED at 0x3C failed! Trying 0x3D..."));
    if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3D)) {
      Serial.println(F("FATAL: SSD1306 OLED not detected on I2C A4/A5."));
      while (1) {
        // Fast blink built-in LED as hardware error indicator
        pinMode(LED_BUILTIN, OUTPUT);
        digitalWrite(LED_BUILTIN, HIGH);
        delay(120);
        digitalWrite(LED_BUILTIN, LOW);
        delay(120);
      }
    }
  }

  // Display Splash Screen
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(14, 8);
  display.print(F("AGRI-ASSISTANT"));
  display.setCursor(6, 22);
  display.print(F("Smart Farming Device"));
  display.setCursor(16, 38);
  display.print(F("Calibrating..."));
  drawProgressBar(14, 48, 100, 6, 100);
  display.display();
  delay(1200);

  // Initial Sensor Sampling
  readSoilSensor();
  readLdrSensor();
  readDhtSensor();

  updateDisplay();
  Serial.println(F("System Ready! Use D2 (Left), D3 (Right), D4 (Select/Back)."));
}

void loop() {
  unsigned long currentMillis = millis();

  // 1. Process Button Presses (High frequency responsive debouncing)
  handleButtons();

  // 2. Read Fast Analog Sensors (Soil A0 & LDR A2 every 350ms)
  if (currentMillis - lastFastSensorRead >= 350) {
    lastFastSensorRead = currentMillis;
    readSoilSensor();
    readLdrSensor();
  }

  // 3. Read DHT11 Temperature & Humidity (every 2000ms for accurate sampling)
  if (currentMillis - lastDhtRead >= 2000) {
    lastDhtRead = currentMillis;
    readDhtSensor();
    printSerialDiagnostics();
  }

  // 4. Smooth Display Refresh (every 80ms / ~12.5 FPS)
  if (currentMillis - lastDisplayUpdate >= 80) {
    lastDisplayUpdate = currentMillis;
    updateDisplay();
  }
}
