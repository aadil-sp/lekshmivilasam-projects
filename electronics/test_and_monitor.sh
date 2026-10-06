#!/bin/bash
# HW-605 / MAX30102 Test & Live PPG Monitor Script for Seeed Studio XIAO ESP32-C6
cd "$(dirname "$0")"

echo "=========================================================="
echo "  HW-605 / MAX30102 PULSE OXIMETER TESTBENCH              "
echo "  Target: Seeed Studio XIAO ESP32-C6                      "
echo "=========================================================="

/Library/Frameworks/Python.framework/Versions/3.11/bin/pio run -t upload

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================================="
    echo " [SUCCESS] Flashed! Opening Live Heart Rate Monitor...     "
    echo " (Place your finger gently on the sensor now)             "
    echo "=========================================================="
    sleep 1
    python3 -c "
import serial, time
try:
    s = serial.Serial('/dev/cu.usbmodem11201', 115200, timeout=0.2)
    print('Connected to XIAO ESP32-C6. Streaming PPG & Pulse Data:\n')
    while True:
        line = s.readline()
        if line:
            print(line.decode('utf-8', errors='ignore').strip())
except KeyboardInterrupt:
    print('\nMonitor stopped by user.')
except Exception as e:
    print('Serial error:', e)
"
else
    echo "Upload failed. Please check connection."
fi
