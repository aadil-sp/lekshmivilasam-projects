#include <M5Unified.h>
#include <BleKeyboard.h>
#include "config.h"

// Global Objects
BleKeyboard bleKeyboard(DEVICE_NAME, DEVICE_MANUFACTURER, 100);
M5Canvas canvas(&M5.Display);

// State Variables
AppState currentState = STATE_MENU;
int selectedMenuItem = MENU_GAME;
bool bleConnected = false;
uint32_t lastBatteryCheck = 0;
int batteryLevel = 100;

// Game Mode State
bool imuTiltEnabled = true;
bool keyLeftPressed = false;
bool keyRightPressed = false;
bool keyUpPressed = false;
bool keyDownPressed = false;
float currentTiltX = 0.0f;
float currentTiltY = 0.0f;

// Presenter Mode State
int slideCount = 1;
uint32_t presenterStartTime = 0;
String lastActionText = "READY";
uint32_t lastActionTime = 0;

// UI Redraw Flag
bool needRedraw = true;

// Helper: Play buzzer tone
void playSound(int freq, int durationMs = 60) {
    M5.Speaker.tone(freq, durationMs);
}

// Draw Top Status Bar (BLE + Battery + Mode Indicator)
void drawStatusBar(const char* title, uint16_t themeColor) {
    canvas.fillRect(0, 0, 240, 24, 0x0000);
    
    // Mode title
    canvas.setTextColor(themeColor);
    canvas.setTextDatum(middle_left);
    canvas.drawString(title, 8, 12);

    // Bluetooth Status icon/text
    if (bleKeyboard.isConnected()) {
        canvas.fillCircle(160, 12, 4, COLOR_ACCENT_GAME);
        canvas.setTextColor(COLOR_ACCENT_GAME);
        canvas.setTextDatum(middle_left);
        canvas.drawString("BLE OK", 168, 12);
    } else {
        canvas.fillCircle(160, 12, 4, COLOR_WARN);
        canvas.setTextColor(COLOR_TEXT_MUTED);
        canvas.setTextDatum(middle_left);
        canvas.drawString("PAIRING", 168, 12);
    }

    // Battery Indicator
    canvas.setTextColor(COLOR_TEXT);
    canvas.setTextDatum(middle_right);
    char batStr[12];
    snprintf(batStr, sizeof(batStr), "%d%%", batteryLevel);
    canvas.drawString(batStr, 234, 12);

    // Divider line
    canvas.drawFastHLine(0, 24, 240, 0x2124);
}

// Render Main Menu
void drawMenuUI() {
    canvas.fillScreen(COLOR_BG);
    drawStatusBar("M5 CONTROLLER", COLOR_TEXT);

    // Menu Card 1: Game Mode
    uint16_t card1Bg = (selectedMenuItem == MENU_GAME) ? COLOR_CARD_SEL : COLOR_CARD_BG;
    uint16_t card1Border = (selectedMenuItem == MENU_GAME) ? COLOR_ACCENT_GAME : COLOR_BG;
    canvas.fillRoundRect(10, 32, 220, 42, 6, card1Bg);
    canvas.drawRoundRect(10, 32, 220, 42, 6, card1Border);
    
    canvas.setTextDatum(middle_left);
    canvas.setTextColor((selectedMenuItem == MENU_GAME) ? COLOR_ACCENT_GAME : COLOR_TEXT);
    canvas.drawString("1. GAME MODE", 22, 48);
    canvas.setTextColor(COLOR_TEXT_MUTED);
    canvas.drawString("Tilt Steering + Boost Jump", 22, 63);

    // Menu Card 2: Presenter Mode
    uint16_t card2Bg = (selectedMenuItem == MENU_PRESENTER) ? COLOR_CARD_SEL : COLOR_CARD_BG;
    uint16_t card2Border = (selectedMenuItem == MENU_PRESENTER) ? COLOR_ACCENT_PRES : COLOR_BG;
    canvas.fillRoundRect(10, 78, 220, 42, 6, card2Bg);
    canvas.drawRoundRect(10, 78, 220, 42, 6, card2Border);

    canvas.setTextDatum(middle_left);
    canvas.setTextColor((selectedMenuItem == MENU_PRESENTER) ? COLOR_ACCENT_PRES : COLOR_TEXT);
    canvas.drawString("2. PRESENTATION", 22, 94);
    canvas.setTextColor(COLOR_TEXT_MUTED);
    canvas.drawString("Keynote / Slides Clicker", 22, 109);

    // Bottom Button Help Hints
    canvas.fillRect(0, 122, 240, 13, 0x0000);
    canvas.setTextDatum(middle_center);
    canvas.setTextColor(0x7BEF);
    canvas.drawString("[Btn A: SELECT]   [Btn B: NEXT]", 120, 128);
}

// Render Game Mode UI
void drawGameUI() {
    canvas.fillScreen(COLOR_BG);
    drawStatusBar("GAME MODE", COLOR_ACCENT_GAME);

    // Real-time Motion / Tilt Visualizer
    canvas.drawRoundRect(10, 30, 105, 84, 6, COLOR_CARD_BG);
    canvas.setTextDatum(top_center);
    canvas.setTextColor(COLOR_TEXT_MUTED);
    canvas.drawString("TILT STEERING", 62, 34);

    // Center Crosshair
    int cx = 62;
    int cy = 76;
    canvas.drawFastHLine(cx - 24, cy, 48, 0x31A6);
    canvas.drawFastVLine(cx, cy - 24, 48, 0x31A6);
    
    // Tilt Bubble
    int bx = cx + (int)(currentTiltX * 45.0f);
    int by = cy + (int)(currentTiltY * 45.0f);
    bx = constrain(bx, cx - 24, cx + 24);
    by = constrain(by, cy - 24, cy + 24);
    
    uint16_t bubbleColor = (abs(currentTiltX) > TILT_THRESHOLD_X) ? COLOR_ACCENT_GAME : COLOR_CARD_SEL;
    canvas.fillCircle(bx, by, 7, bubbleColor);
    canvas.drawCircle(bx, by, 7, COLOR_TEXT);

    // Right Box: Button Status
    canvas.drawRoundRect(122, 30, 108, 84, 6, COLOR_CARD_BG);
    canvas.setTextDatum(top_center);
    canvas.setTextColor(COLOR_TEXT_MUTED);
    canvas.drawString("BUTTONS", 176, 34);

    // Button A indicator (Big M5 button -> Jump/Boost)
    bool btnAPressed = M5.BtnA.isPressed() || keyUpPressed;
    canvas.fillRoundRect(128, 48, 96, 26, 4, btnAPressed ? COLOR_ACCENT_GAME : COLOR_CARD_BG);
    canvas.drawRoundRect(128, 48, 96, 26, 4, btnAPressed ? COLOR_TEXT : 0x4208);
    canvas.setTextDatum(middle_center);
    canvas.setTextColor(btnAPressed ? 0x0000 : COLOR_TEXT);
    canvas.drawString("M5: JUMP/BOOST", 176, 61);

    // Button B indicator (Side button -> Laser / Power)
    bool btnBPressed = M5.BtnB.isPressed() || keyDownPressed;
    canvas.fillRoundRect(128, 80, 96, 26, 4, btnBPressed ? COLOR_ACCENT_PRES : COLOR_CARD_BG);
    canvas.drawRoundRect(128, 80, 96, 26, 4, btnBPressed ? COLOR_TEXT : 0x4208);
    canvas.setTextDatum(middle_center);
    canvas.setTextColor(btnBPressed ? 0x0000 : COLOR_TEXT);
    canvas.drawString("SIDE: ACTION", 176, 93);

    // Bottom Navigation Hint
    canvas.fillRect(0, 120, 240, 15, 0x0000);
    canvas.setTextDatum(middle_center);
    canvas.setTextColor(0x7BEF);
    canvas.drawString("[Hold PWR or Hold B to Exit]", 120, 127);
}

// Render Presenter Mode UI
void drawPresenterUI() {
    canvas.fillScreen(COLOR_BG);
    drawStatusBar("PRESENTER", COLOR_ACCENT_PRES);

    // Slide Counter / Timer Card
    canvas.fillRoundRect(10, 30, 220, 52, 6, COLOR_CARD_BG);
    canvas.setTextDatum(middle_left);
    canvas.setTextColor(COLOR_TEXT_MUTED);
    canvas.drawString("ELAPSED TIME", 20, 44);

    // Presenter Timer
    uint32_t elapsedSec = (millis() - presenterStartTime) / 1000;
    int mins = elapsedSec / 60;
    int secs = elapsedSec % 60;
    char timeStr[16];
    snprintf(timeStr, sizeof(timeStr), "%02d:%02d", mins, secs);
    canvas.setTextDatum(middle_left);
    canvas.setTextColor(COLOR_ACCENT_PRES);
    canvas.drawString(timeStr, 20, 64);

    // Last Action Card
    canvas.setTextDatum(middle_right);
    canvas.setTextColor(COLOR_TEXT_MUTED);
    canvas.drawString("LAST ACTION", 218, 44);
    canvas.setTextColor(COLOR_TEXT);
    canvas.drawString(lastActionText.c_str(), 218, 64);

    // Button Control Hints
    canvas.fillRoundRect(10, 86, 105, 30, 4, M5.BtnA.isPressed() ? COLOR_ACCENT_PRES : COLOR_CARD_BG);
    canvas.setTextDatum(middle_center);
    canvas.setTextColor(M5.BtnA.isPressed() ? 0x0000 : COLOR_TEXT);
    canvas.drawString("M5: NEXT ->", 62, 101);

    canvas.fillRoundRect(125, 86, 105, 30, 4, M5.BtnB.isPressed() ? COLOR_ACCENT_PRES : COLOR_CARD_BG);
    canvas.setTextDatum(middle_center);
    canvas.setTextColor(M5.BtnB.isPressed() ? 0x0000 : COLOR_TEXT);
    canvas.drawString("<- B: PREV", 177, 101);

    // Bottom Navigation Hint
    canvas.fillRect(0, 120, 240, 15, 0x0000);
    canvas.setTextDatum(middle_center);
    canvas.setTextColor(0x7BEF);
    canvas.drawString("[Hold A: Play | Hold B: Back]", 120, 127);
}

// Handle Game Mode Logic
void handleGameMode() {
    // Read IMU Accelerometer Data
    float ax = 0, ay = 0, az = 0;
    if (M5.Imu.isEnabled()) {
        M5.Imu.getAccelData(&ax, &ay, &az);
    }
    
    // In Rotation(1) Landscape:
    // Left/Right tilt is along Y-axis, Up/Down tilt along X-axis
    currentTiltX = ay;
    currentTiltY = ax;

    if (bleKeyboard.isConnected()) {
        // Left Steering
        if (currentTiltX < -TILT_THRESHOLD_X) {
            if (!keyLeftPressed) {
                bleKeyboard.press(KEY_LEFT_ARROW);
                keyLeftPressed = true;
            }
        } else if (currentTiltX > -TILT_DEADZONE_X && keyLeftPressed) {
            bleKeyboard.release(KEY_LEFT_ARROW);
            keyLeftPressed = false;
        }

        // Right Steering
        if (currentTiltX > TILT_THRESHOLD_X) {
            if (!keyRightPressed) {
                bleKeyboard.press(KEY_RIGHT_ARROW);
                keyRightPressed = true;
            }
        } else if (currentTiltX < TILT_DEADZONE_X && keyRightPressed) {
            bleKeyboard.release(KEY_RIGHT_ARROW);
            keyRightPressed = false;
        }

        // Button A: Jump / Boost (Space / Up Arrow)
        if (M5.BtnA.wasPressed()) {
            bleKeyboard.press(KEY_UP_ARROW);
            keyUpPressed = true;
            playSound(NOTE_BEEP_HIGH, 40);
        }
        if (M5.BtnA.wasReleased()) {
            bleKeyboard.release(KEY_UP_ARROW);
            keyUpPressed = false;
        }

        // Button B: Action / Secondary (Down Arrow / Enter)
        if (M5.BtnB.wasPressed()) {
            bleKeyboard.press(KEY_DOWN_ARROW);
            keyDownPressed = true;
            playSound(NOTE_BEEP_MID, 40);
        }
        if (M5.BtnB.wasReleased()) {
            bleKeyboard.release(KEY_DOWN_ARROW);
            keyDownPressed = false;
        }
    }

    // Exit Game Mode: Hold Button B or Press Power
    if (M5.BtnB.wasHold() || M5.BtnPWR.wasClicked()) {
        // Release any held keys
        if (keyLeftPressed) bleKeyboard.release(KEY_LEFT_ARROW);
        if (keyRightPressed) bleKeyboard.release(KEY_RIGHT_ARROW);
        if (keyUpPressed) bleKeyboard.release(KEY_UP_ARROW);
        if (keyDownPressed) bleKeyboard.release(KEY_DOWN_ARROW);
        keyLeftPressed = keyRightPressed = keyUpPressed = keyDownPressed = false;
        
        currentState = STATE_MENU;
        playSound(NOTE_CANCEL, 100);
        needRedraw = true;
    }
}

// Handle Presenter Mode Logic
void handlePresenterMode() {
    if (bleKeyboard.isConnected()) {
        // Hold Button A: Start Presentation / Fullscreen (F5)
        if (M5.BtnA.wasHold()) {
            bleKeyboard.write(KEY_F5);
            lastActionText = "FULLSCREEN (F5)";
            lastActionTime = millis();
            playSound(NOTE_START, 120);
        }
        // Click Button A: Next Slide
        else if (M5.BtnA.wasClicked()) {
            bleKeyboard.write(KEY_RIGHT_ARROW);
            slideCount++;
            lastActionText = "NEXT SLIDE ->";
            lastActionTime = millis();
            playSound(NOTE_BEEP_HIGH, 50);
        }

        // Hold Button B: Exit to Main Menu
        if (M5.BtnB.wasHold() || M5.BtnPWR.wasClicked()) {
            currentState = STATE_MENU;
            playSound(NOTE_CANCEL, 100);
            needRedraw = true;
            return;
        }
        // Click Button B: Previous Slide
        else if (M5.BtnB.wasClicked()) {
            bleKeyboard.write(KEY_LEFT_ARROW);
            if (slideCount > 1) slideCount--;
            lastActionText = "<- PREV SLIDE";
            lastActionTime = millis();
            playSound(NOTE_BEEP_LOW, 50);
        }
    } else {
        if (M5.BtnB.wasHold() || M5.BtnPWR.wasClicked()) {
            currentState = STATE_MENU;
            playSound(NOTE_CANCEL, 100);
            needRedraw = true;
        }
    }
}

// Handle Menu Selection Logic
void handleMenu() {
    // Cycle Menu Item with Button B
    if (M5.BtnB.wasClicked()) {
        selectedMenuItem = (selectedMenuItem + 1) % MENU_COUNT;
        playSound(NOTE_BEEP_MID, 40);
        needRedraw = true;
    }

    // Select Menu Item with Button A
    if (M5.BtnA.wasClicked()) {
        playSound(NOTE_SELECT, 80);
        if (selectedMenuItem == MENU_GAME) {
            currentState = STATE_GAME_MODE;
        } else if (selectedMenuItem == MENU_PRESENTER) {
            currentState = STATE_PRESENTER_MODE;
            presenterStartTime = millis();
            slideCount = 1;
            lastActionText = "READY";
        }
        needRedraw = true;
    }
}

void setup() {
    auto cfg = M5.config();
    M5.begin(cfg);

    // Setup Display (Landscape 240x135)
    M5.Display.setRotation(1);
    M5.Display.setBrightness(180);
    
    // Create flicker-free Sprite Canvas
    canvas.createSprite(240, 135);
    canvas.setTextWrap(false);

    // Initialize IMU
    M5.Imu.begin();

    // Initialize Speaker / Buzzer
    M5.Speaker.begin();
    M5.Speaker.setVolume(120);

    // Startup Tone
    playSound(NOTE_START, 150);

    // Start BLE HID Keyboard
    bleKeyboard.begin();

    // Initial battery read
    batteryLevel = M5.Power.getBatteryLevel();
    if (batteryLevel < 0) batteryLevel = 100;
}

void loop() {
    M5.update();

    // Check battery level periodically
    if (millis() - lastBatteryCheck > BATTERY_UPDATE_MS) {
        lastBatteryCheck = millis();
        int bat = M5.Power.getBatteryLevel();
        if (bat >= 0) {
            batteryLevel = bat;
            if (bleKeyboard.isConnected()) {
                bleKeyboard.setBatteryLevel(batteryLevel);
            }
        }
    }

    // Track BLE Connection state changes
    bool isConnected = bleKeyboard.isConnected();
    if (isConnected != bleConnected) {
        bleConnected = isConnected;
        playSound(isConnected ? NOTE_BEEP_HIGH : NOTE_CANCEL, 100);
        needRedraw = true;
    }

    // Handle Active State
    switch (currentState) {
        case STATE_MENU:
            handleMenu();
            drawMenuUI();
            break;

        case STATE_GAME_MODE:
            handleGameMode();
            drawGameUI();
            break;

        case STATE_PRESENTER_MODE:
            handlePresenterMode();
            drawPresenterUI();
            break;
    }

    // Push canvas to screen
    canvas.pushSprite(0, 0);

    // Small delay to prevent CPU thrashing
    delay(20);
}
