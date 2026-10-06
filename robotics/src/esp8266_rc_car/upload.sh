#!/usr/bin/env bash
# ==============================================================================
# ESP8266 RC CAR - ONE-CLICK UPLOAD SCRIPT
# ==============================================================================
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=========================================================="
echo "⚡ Building & Uploading ESP8266 RC Car Firmware"
echo "=========================================================="

/Library/Frameworks/Python.framework/Versions/3.11/bin/pio run -t upload

echo "=========================================================="
echo "✅ Upload Successful!"
echo ">> 1. Connect phone/laptop Wi-Fi to: 'RoboCar-WiFi'"
echo ">> 2. Open browser and visit: http://192.168.4.1"
echo "=========================================================="
