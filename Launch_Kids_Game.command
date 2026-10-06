#!/bin/bash

# ==============================================================================
# Cosmic Star Catcher - One-Click Launcher for macOS
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
GAME_DIR="$DIR/m5stick-kids-controller/game"

cd "$GAME_DIR" || exit 1

echo "================================================================="
echo "  🚀 COSMIC STAR CATCHER - M5StickC PLUS 2 Bluetooth Game"
echo "================================================================="
echo ""
echo "  📡 Bluetooth Setup:"
echo "     1. Ensure M5Stick is ON and in '1. GAME MODE'"
echo "     2. Mac Bluetooth -> Connect to 'M5-Kids-Pad'"
echo ""
echo "  🎮 Controls:"
echo "     - Tilt M5Stick Left/Right : Steer Rocket"
echo "     - Front M5 Button (A)    : Boost / Jetpack / Launch"
echo "     - Side Button (B)        : Action / Power-up"
echo "     (Or use Mac Keyboard Arrow Keys / Space)"
echo ""
echo "================================================================="
echo "  Launching Game..."
echo "================================================================="

python3 main.py

echo ""
echo "Game session closed. Have a stellar day! 🌟"
