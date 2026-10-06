#!/usr/bin/env python3
import time
import struct
import serial

PORT = "/dev/cu.usbmodem549A30D515392"

def build_packet(cmd_id, ctrl, params=b''):
    length = len(params) + 2
    payload = bytes([cmd_id, ctrl]) + params
    checksum = (256 - (sum(payload) % 256)) % 256
    return bytes([0xAA, 0xAA, length]) + payload + bytes([checksum])

def send_and_recv(ser, cmd_id, ctrl, params=b'', wait=0.05):
    pkt = build_packet(cmd_id, ctrl, params)
    ser.write(pkt)
    time.sleep(wait)
    resp = ser.read_all()
    print(f"TX: {pkt.hex()} -> RX ({len(resp)} bytes): {resp.hex()}")
    return resp

def main():
    print(f"Opening {PORT}...")
    ser = serial.Serial(PORT, 115200, timeout=0.1)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    time.sleep(0.1)

    print("\n--- 1. Get Pose (ID: 10) ---")
    resp = send_and_recv(ser, 10, 0)
    if len(resp) >= 37 and resp[0] == 0xAA and resp[1] == 0xAA:
        floats = struct.unpack('<8f', resp[5:37])
        print(f"Current Pose: X={floats[0]:.2f}, Y={floats[1]:.2f}, Z={floats[2]:.2f}, R={floats[3]:.2f}")
        print(f"Joint Angles: J1={floats[4]:.2f}, J2={floats[5]:.2f}, J3={floats[6]:.2f}, J4={floats[7]:.2f}")

    print("\n--- 2. Get Alarms State (ID: 20) ---")
    resp = send_and_recv(ser, 20, 0)

    print("\n--- 3. Clear Alarms (ID: 20, Ctrl: 1) ---")
    send_and_recv(ser, 20, 1)

    print("\n--- 4. Set JOG Joint Params (ID: 70) ---")
    # 4 velocities (float), 4 accels (float)
    jog_j_params = struct.pack('<8f', 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0)
    send_and_recv(ser, 70, 1, jog_j_params)

    print("\n--- 5. Set JOG Coordinate Params (ID: 71) ---")
    jog_c_params = struct.pack('<8f', 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0)
    send_and_recv(ser, 71, 1, jog_c_params)

    print("\n--- 6. Set JOG Common Params (ID: 72) ---")
    jog_common = struct.pack('<2f', 50.0, 50.0)
    send_and_recv(ser, 72, 1, jog_common)

    print("\n--- 7. Test JOG Motion X+ (ID: 73, Ctrl: 1 or 0) for 1 second ---")
    # isJoint=0 (Cartesian), cmd=1 (X+)
    # Let's test with Ctrl=1
    jog_run = bytes([0, 1])
    send_and_recv(ser, 73, 1, jog_run)
    time.sleep(0.5)
    jog_stop = bytes([0, 0])
    send_and_recv(ser, 73, 1, jog_stop)

    time.sleep(0.2)
    resp = send_and_recv(ser, 10, 0)
    if len(resp) >= 37:
        floats = struct.unpack('<8f', resp[5:37])
        print(f"Pose After JOG: X={floats[0]:.2f}, Y={floats[1]:.2f}, Z={floats[2]:.2f}, R={floats[3]:.2f}")

    print("\n--- 8. Test Queue Execution & PTP Movement (ID: 84) ---")
    # Reset queue
    send_and_recv(ser, 245, 1) # Clear queue
    send_and_recv(ser, 240, 1) # Start queue

    # Set PTP Coordinate Params (ID: 80)
    ptp_c_params = struct.pack('<8f', 150.0, 150.0, 150.0, 150.0, 150.0, 150.0, 150.0, 150.0)
    send_and_recv(ser, 80, 1, ptp_c_params)

    # Set PTP Common Params (ID: 81)
    ptp_common = struct.pack('<2f', 50.0, 50.0)
    send_and_recv(ser, 81, 1, ptp_common)

    # Send Queued PTP (ID: 84, Ctrl: 3)
    # Mode: 1 (MOVJ_XYZ), X=240, Y=20, Z=50, R=0
    ptp_cmd = struct.pack('<B4f', 1, 240.0, 20.0, 50.0, 0.0)
    send_and_recv(ser, 84, 3, ptp_cmd)

    print("Waiting 2s for movement...")
    time.sleep(2.0)

    resp = send_and_recv(ser, 10, 0)
    if len(resp) >= 37:
        floats = struct.unpack('<8f', resp[5:37])
        print(f"Pose After PTP: X={floats[0]:.2f}, Y={floats[1]:.2f}, Z={floats[2]:.2f}, R={floats[3]:.2f}")

    # Return to 240, 0, 50
    ptp_cmd_back = struct.pack('<B4f', 1, 240.0, 0.0, 50.0, 0.0)
    send_and_recv(ser, 84, 3, ptp_cmd_back)
    time.sleep(1.0)

    ser.close()
    print("\n[DONE] Test finished.")

if __name__ == "__main__":
    main()
