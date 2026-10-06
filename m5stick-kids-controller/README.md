# 🚀 M5StickC PLUS 2 Bluetooth Controller & Cosmic Star Catcher Game

A complete interactive project featuring an **ESP32 BLE Dual-Mode Controller** on the **M5StickC PLUS 2** and a vibrant, kid-friendly space arcade game called **"Cosmic Star Catcher"** built in Python with Pygame.

---

## 🎮 Features Overview

### 1. M5StickC PLUS 2 Firmware (`firmware/`)
- **Dual-Mode System**:
  - 🕹️ **Game Mode**: Steer your rocket by **tilting the M5Stick left & right** (using the built-in MPU6886 6-axis IMU). Press the **front M5 button (A)** for Boost/Jump and the **side button (B)** for Actions.
  - 📽️ **Presentation Mode**: Turn the M5Stick into a wireless presentation clicker for **Keynote**, **Google Slides**, or **PowerPoint**!
- **Color LCD GUI (135x240)**:
  - Real-time steering visualizer with dynamic tilt bubble crosshair.
  - Live button state indicators.
  - Presenter stopwatch timer & last action display.
  - Bluetooth connection badge (🔴 Pairing / 🟢 Connected) & Battery % gauge.
- **Audio Feedback**: Built-in buzzer sound tones for menu navigation, mode selection, and button presses.
- **Ultra-Fast NimBLE Stack**: Minimal memory consumption, instant pairing with macOS / Windows / iOS / Android as a standard Bluetooth Keyboard (zero extra drivers required!).

### 2. Cosmic Star Catcher Game (`game/`)
- **Kid-Friendly Arcade Action**:
  - Catch falling golden stars ⭐ and rainbow gems 💎 to build mega score combos!
  - Dodge goofy tumbling asteroids 🪨.
  - Grab power-up orbs:
    - 🛡️ **Shield Bubble**: Protects from collisions.
    - 🧲 **Star Magnet**: Automatically sucks all nearby stars into your rocket!
    - ⚡ **Hyper Turbo**: Rainbow thruster flames and super speed!
- **Zero Asset Dependencies**:
  - 100% procedurally drawn vector graphics, starry parallax background, and particle fireworks.
  - Built-in mathematical 8-bit sound synthesizer using `numpy` & `pygame.sndarray` (no missing audio file errors).
- **Dual Controls**: Play with the **M5StickC PLUS 2 over Bluetooth** OR standard **Mac Keyboard Arrow Keys / Space**!

---

## 🕹️ Hardware Controls Reference

### 📋 Main Menu
| Button | Action |
| :--- | :--- |
| **Btn B (Side Button)** | Scroll / Cycle between `1. GAME MODE` & `2. PRESENTATION` |
| **Btn A (Big M5 Button)** | Select & Launch active mode |

### 🚀 Game Mode
| Input | Game Action | Key Sent over BLE |
| :--- | :--- | :--- |
| **Tilt Left / Right** | Steer Rocket Left / Right | `Left Arrow` / `Right Arrow` |
| **Btn A (Big M5 Button)** | Jetpack Boost / Jump / Start | `Up Arrow` (or `Space`) |
| **Btn B (Side Button)** | Action / Secondary / Power | `Down Arrow` (or `Return`) |
| **Hold Btn B or PWR** | Exit back to Main Menu | — |

### 📽️ Presentation Mode
| Input | Presentation Action | Key Sent over BLE |
| :--- | :--- | :--- |
| **Btn A (Big M5 Button)** | Next Slide | `Right Arrow` |
| **Btn B (Side Button)** | Previous Slide | `Left Arrow` |
| **Hold Btn A (> 0.8s)** | Start Slideshow / Fullscreen | `F5` |
| **Hold Btn B or PWR** | Exit back to Main Menu | — |

---

## ⚡ Quick Start Guide

### Step 1: Upload Firmware to M5StickC PLUS 2
1. Plug your **M5StickC PLUS 2** into your Mac via USB-C.
2. Open terminal and navigate to the firmware directory:
   ```bash
   cd m5stick-kids-controller/firmware
   ```
3. Build and upload using PlatformIO:
   ```bash
   pio run --target upload
   ```
4. Once uploaded, the M5Stick screen will turn on with a welcome chime and display the **M5 CONTROLLER** menu!

---

### Step 2: Pair Bluetooth with Mac
1. On your Mac, open **System Settings > Bluetooth**.
2. Look for **`M5-Kids-Pad`** in the nearby devices list.
3. Click **Connect**.
4. Once paired, the M5Stick status badge will turn from 🔴 **PAIRING** to 🟢 **BLE OK**!

---

### Step 3: Launch the Python Game
1. Install game dependencies:
   ```bash
   pip3 install -r m5stick-kids-controller/game/requirements.txt
   ```
2. Launch the game:
   ```bash
   python3 m5stick-kids-controller/game/main.py
   ```
3. On your M5Stick, select **1. GAME MODE** by pressing the **M5 Button**.
4. Tilt the M5Stick and press the front button to launch into space and catch stars! 🌟
