#!/bin/bash
# Upload script for AIoT Landslide Early Warning System
cd "$(dirname "$0")"

echo "=========================================================="
echo "  AIoT Landslide Warning System - Firmware Flasher        "
echo "=========================================================="
echo "Target port: /dev/cu.usbserial-0001 or /dev/cu.SLAB_USBtoUART"
echo ""
echo "NOTE: If you see 'Connecting........', PRESS & HOLD the"
echo "BOOT (or FLASH / IO0) button on the ESP32 until upload begins!"
echo "=========================================================="

/Library/Frameworks/Python.framework/Versions/3.11/bin/pio run -t upload

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================================="
    echo " [SUCCESS] Firmware successfully uploaded to ESP32!"
    echo "=========================================================="
else
    echo ""
    echo "=========================================================="
    echo " [RETRYING] If failed, hold down the BOOT button now..."
    echo "=========================================================="
    python3 ~/.platformio/packages/tool-esptoolpy/esptool.py --chip esp32 --port /dev/cu.usbserial-0001 --baud 115200 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 .pio/build/esp32dev/bootloader.bin 0x8000 .pio/build/esp32dev/partitions.bin 0x10000 .pio/build/esp32dev/firmware.bin
fi
