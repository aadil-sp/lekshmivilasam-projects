#!/usr/bin/env bash
# ==============================================================================
# SEEED XIAO + HW-605 LIVE SENSOR MONITOR
# ==============================================================================
PORT="/dev/cu.usbmodem1201"
if [ ! -e "$PORT" ]; then
    PORT=$(ls /dev/cu.usbmodem* 2>/dev/null | head -n 1)
fi

echo "=========================================================="
echo "📡 Opening Live Sensor Monitor on: $PORT @ 115200 Baud"
echo "Press Ctrl+C to exit."
echo "=========================================================="

/Library/Frameworks/Python.framework/Versions/3.11/bin/pio device monitor -b 115200 --port "$PORT"
