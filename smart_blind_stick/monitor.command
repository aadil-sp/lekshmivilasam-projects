#!/usr/bin/env bash
# ==============================================================================
# ESP8266 SMART BLIND STICK - LIVE SERIAL MONITOR
# ==============================================================================
PORT="/dev/cu.wchusbserial120"
if [ ! -e "$PORT" ]; then
    PORT=$(ls /dev/cu.usbserial* /dev/cu.wchusbserial* 2>/dev/null | head -n 1)
fi

echo "=========================================================="
echo "📡 Opening Serial Monitor on: $PORT @ 115200 Baud"
echo "Press Ctrl+C or close window to exit."
echo "=========================================================="

/Library/Frameworks/Python.framework/Versions/3.11/bin/pio device monitor -b 115200 --port "$PORT"
