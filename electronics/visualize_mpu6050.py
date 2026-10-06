import serial
import serial.tools.list_ports
import time
import sys
import re

def get_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "usbmodem" in port.device.lower():
            return port.device
    return ports[0].device if ports else None

def draw_bar(val, min_val, max_val, width=20):
    # Clamp
    val = max(min_val, min(max_val, val))
    # Map to 0-1
    normalized = (val - min_val) / (max_val - min_val)
    pos = int(normalized * width)
    
    bar = ["-"] * width
    
    if pos >= 0 and pos < width:
        bar[pos] = "O"
    
    return "[" + "".join(bar) + "]"

def main():
    port_name = get_port()
    if not port_name:
        print("No device found.")
        sys.exit(1)
        
    print(f"Listening for MPU-6050 on {port_name}...\n")
    
    # Regex to extract Accel and Gyro data from the serial print
    # 🧭 [MPU-6050 IMU] Accel(m/s²): [ 9.81,  0.00,  0.00] | Gyro(°/s): [   0.0,    0.0,    0.0] | Temp: 25.0°C
    pattern = re.compile(r"Accel\(m/s.\):\s*\[\s*([\d\.\-]+),\s*([\d\.\-]+),\s*([\d\.\-]+)\]\s*\|\s*Gyro\(./s\):\s*\[\s*([\d\.\-]+),\s*([\d\.\-]+),\s*([\d\.\-]+)\]")

    try:
        ser = serial.Serial(port_name, 115200, timeout=1)
        ser.dtr = False
        ser.rts = False
        
        connected = False
        
        while True:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue
                
            if "[SUCCESS]" in line or "Ready!" in line:
                connected = True
                
            if "No HW-605 sensor detected" in line:
                sys.stdout.write("\r\033[K" + "STATUS: ❌ Disconnected - Checking I2C wiring (SDA=8, SCL=9)...")
                sys.stdout.flush()
                connected = False
                continue
                
            match = pattern.search(line)
            if match:
                ax, ay, az, gx, gy, gz = map(float, match.groups())
                
                # Clear terminal and print dashboard
                sys.stdout.write("\033[2J\033[H")
                print("=======================================")
                print("      MPU-6050 MOTION DASHBOARD        ")
                print("=======================================\n")
                print("STATUS: ✅ Connected & Streaming Data\n")
                
                print("--- ACCELEROMETER (m/s^2) ---")
                print(f"X: {ax:6.2f} {draw_bar(ax, -10, 10)}")
                print(f"Y: {ay:6.2f} {draw_bar(ay, -10, 10)}")
                print(f"Z: {az:6.2f} {draw_bar(az, -10, 10)}")
                
                print("\n--- GYROSCOPE (deg/s) ---")
                print(f"X: {gx:6.1f} {draw_bar(gx, -200, 200)}")
                print(f"Y: {gy:6.1f} {draw_bar(gy, -200, 200)}")
                print(f"Z: {gz:6.1f} {draw_bar(gz, -200, 200)}")
                
                print("\nTilt the sensor to see the bars move!")
                print("Press Ctrl+C to exit.")
            elif not connected and "[SCAN]" not in line and "I2C" not in line and "---" not in line and "===" not in line:
                 # Print other debug info
                 pass

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()
