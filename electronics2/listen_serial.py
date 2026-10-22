#!/usr/bin/env python3
"""
Serial Telemetry Listener and CSV Logger
Smart Farming Assistance Device (Arduino Nano)
Baud Rate: 115200 bps
"""

import sys
import time
import glob
import csv
import re
from datetime import datetime

try:
    import serial
except ImportError:
    print("\n[!] 'pyserial' library not found.")
    print("    Install it via: pip install pyserial\n")
    sys.exit(1)

def find_arduino_port():
    """Auto-detect common Arduino USB serial ports across macOS, Linux, and Windows."""
    patterns = [
        '/dev/cu.usbserial*',
        '/dev/cu.usbmodem*',
        '/dev/cu.wchusbserial*',
        '/dev/ttyUSB*',
        '/dev/ttyACM*',
        'COM*'
    ]
    ports = []
    for pattern in patterns:
        ports.extend(glob.glob(pattern))
    
    if not ports:
        return None
    return ports[0]

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else find_arduino_port()
    
    if not port:
        print("❌ No Arduino Nano detected on USB serial ports.")
        print("   Please connect your device or specify the port manually:")
        print("   python3 listen_serial.py /dev/cu.usbserial-1410\n")
        sys.exit(1)

    baud = 115200
    csv_file = "farm_telemetry.csv"

    print("=" * 65)
    print("  🌾 SMART FARMING ASSISTANCE DEVICE — TELEMETRY MONITOR 🌾")
    print(f"  Port: {port} | Baud Rate: {baud}")
    print(f"  Logging telemetry to: {csv_file}")
    print("  Press Ctrl+C to stop.")
    print("=" * 65 + "\n")

    # Initialize CSV file with headers if needed
    try:
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(["Timestamp", "Soil_ADC", "Soil_Percent", "LDR_ADC", "LDR_Percent", "Temp_C", "Humidity_Percent", "Active_Page", "Raw_Message"])
    except Exception as e:
        print(f"[!] Warning: Could not open CSV file for logging: {e}")

    try:
        ser = serial.Serial(port, baud, timeout=1.5)
        time.sleep(2)  # Wait for Arduino bootloader reset
        ser.reset_input_buffer()
        print("✅ Serial connection established. Listening for farm metrics...\n")

        while True:
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if not line:
                continue

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Check if this line is a data telemetry message
            if "[DATA]" in line:
                # Colorized terminal output
                print(f"\033[92m[{now_str}]\033[0m \033[1m{line}\033[0m")

                # Parse metrics with regular expressions:
                # Format: [DATA] Soil A0: 450 (62%) | LDR A2: 800 (75%) | Temp: 28.5C | Hum: 65.0% | Active Page: 0
                soil_adc = re.search(r'Soil A0:\s*(\d+)', line)
                soil_pct = re.search(r'Soil A0:\s*\d+\s*\((\d+)%\)', line)
                ldr_adc  = re.search(r'LDR A2:\s*(\d+)', line)
                ldr_pct  = re.search(r'LDR A2:\s*\d+\s*\((\d+)%\)', line)
                temp_val = re.search(r'Temp:\s*([0-9.]+)C', line)
                hum_val  = re.search(r'Hum:\s*([0-9.]+)%', line)
                page_val = re.search(r'Active Page:\s*(\d+)', line)

                try:
                    with open(csv_file, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            now_str,
                            soil_adc.group(1) if soil_adc else "",
                            soil_pct.group(1) if soil_pct else "",
                            ldr_adc.group(1) if ldr_adc else "",
                            ldr_pct.group(1) if ldr_pct else "",
                            temp_val.group(1) if temp_val else "",
                            hum_val.group(1) if hum_val else "",
                            page_val.group(1) if page_val else "",
                            line
                        ])
                except Exception:
                    pass

            elif "[NAV]" in line:
                # Navigation event in bright cyan
                print(f"\033[96m[{now_str}] 🧭 {line}\033[0m")
            else:
                # General debug line in dim white
                print(f"\033[90m[{now_str}] {line}\033[0m")

    except serial.SerialException as e:
        print(f"\n❌ Serial Communication Error: {e}")
    except KeyboardInterrupt:
        print("\n\n🛑 Telemetry logging terminated by user.")
    finally:
        try:
            if 'ser' in locals() and ser.is_open:
                ser.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
