#!/usr/bin/env bash
# ==============================================================================
# ESP8266 SMART BLIND STICK - ONE-CLICK UPLOAD SCRIPT
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================================="
echo "⚡ Building & Uploading ESP8266 Smart Blind Stick Firmware"
echo "=========================================================="

PIO_BIN="/Library/Frameworks/Python.framework/Versions/3.11/bin/pio"
if [ ! -f "$PIO_BIN" ]; then
    PIO_BIN="pio"
fi

echo ">> Running PlatformIO Build and Upload..."
$PIO_BIN run -t upload

echo "=========================================================="
echo "✅ Upload Successful!"
echo ">> 1. Connect phone/laptop Wi-Fi to: 'Smart-Blind-Stick' (Password: password123)"
echo ">> 2. Open browser and visit: http://192.168.4.1"
echo "=========================================================="
