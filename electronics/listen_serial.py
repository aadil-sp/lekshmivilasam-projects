import serial
import serial.tools.list_ports
import time
import sys

def get_port():
    print("Scanning for serial ports...")
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No serial ports found. Please connect your device.")
        sys.exit(1)
        
    for port in ports:
        # ESP32 C3 / XIAO typically show up as usbmodem on Mac
        if "usbmodem" in port.device.lower():
            print(f"Found likely ESP32-C3 device at: {port.device}")
            return port.device
            
    print("Found these ports:")
    for p in ports:
        print(f" - {p.device}")
    
    # If no usbmodem is found, just pick the first one as a fallback or ask user
    chosen = ports[0].device
    print(f"Using default port: {chosen}")
    return chosen

def listen():
    port_name = get_port()
    baud_rate = 115200

    print(f"\nConnecting to {port_name} at {baud_rate} baud...")
    
    try:
        # We disable DTR and RTS so it doesn't accidentally reset the C3 into bootloader mode
        ser = serial.Serial(port_name, baud_rate, timeout=1)
        ser.dtr = False
        ser.rts = False
        
        print("Connected! Listening for data. Press Ctrl+C to stop.\n")
        print("-" * 50)
        
        while True:
            try:
                line = ser.readline()
                if line:
                    print(line.decode("utf-8", errors="replace").strip())
            except UnicodeDecodeError:
                pass
            
    except serial.SerialException as e:
        print(f"Error connecting to serial port: {e}")
    except KeyboardInterrupt:
        print("\n\nStopped listening. Goodbye!")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    listen()
