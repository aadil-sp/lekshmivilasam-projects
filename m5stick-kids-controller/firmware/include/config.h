#pragma once

#include <Arduino.h>

// BLE HID Configuration
#define DEVICE_NAME         "M5-Kids-Pad"
#define DEVICE_MANUFACTURER "M5Stack"
#define BATTERY_UPDATE_MS   15000

// IMU Tilt Thresholds for Game Mode
// Acceleration values (in G's, 1.0 = normal gravity)
#define TILT_THRESHOLD_X    0.28f   // Left/Right tilt sensitivity
#define TILT_DEADZONE_X     0.10f   // Deadzone around center
#define TILT_THRESHOLD_Y    0.35f   // Forward/Backward tilt
#define TILT_DEADZONE_Y     0.12f

// Sound Frequencies (Hz)
#define NOTE_BEEP_LOW       440
#define NOTE_BEEP_MID       880
#define NOTE_BEEP_HIGH      1760
#define NOTE_SELECT         1200
#define NOTE_CANCEL         350
#define NOTE_START          1500

// UI Theme Colors (RGB565)
#define COLOR_BG            0x0821  // Deep Space Dark Blue
#define COLOR_CARD_BG       0x18E5  // Slate Blue
#define COLOR_CARD_SEL      0x047F  // Vibrant Sky Blue
#define COLOR_TEXT          0xFFFF  // Pure White
#define COLOR_TEXT_MUTED    0x9CD3  // Soft Gray
#define COLOR_ACCENT_GAME   0x07E0  // Neon Green
#define COLOR_ACCENT_PRES   0xFD20  // Radiant Orange
#define COLOR_ACCENT_BLE    0x05FF  // Cyan
#define COLOR_WARN          0xF800  // Bright Red

// Controller Modes
enum AppState {
    STATE_MENU = 0,
    STATE_GAME_MODE,
    STATE_PRESENTER_MODE
};

// Menu Item IDs
enum MenuItem {
    MENU_GAME = 0,
    MENU_PRESENTER,
    MENU_COUNT
};
