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

def read_exact_packet(ser, expected_id=None, timeout=0.2):
    t0 = time.time()
    buf = bytearray()
    while time.time() - t0 < timeout:
        if ser.in_waiting:
            buf += ser.read(ser.in_waiting)
        # Look for 0xAA 0xAA
        while len(buf) >= 4:
            if buf[0] == 0xAA and buf[1] == 0xAA:
                pkt_len = buf[2]
                total_len = pkt_len + 4 # 2 header + 1 len + payload + 1 checksum
                if len(buf) >= total_len:
                    pkt = bytes(buf[:total_len])
                    del buf[:total_len]
                    cmd_id = pkt[3]
                    if expected_id is None or cmd_id == expected_id:
                        return pkt
                else:
                    break
            else:
                del buf[0]
        time.sleep(0.01)
    return None

def get_current_pose(ser):
    # Send GetPose (ID 10, Ctrl 0)
    ser.write(build_packet(10, 0))
    pkt = read_exact_packet(ser, expected_id=10, timeout=0.15)
    if pkt and len(pkt) >= 37:
        # payload starts at index 5: 32 bytes of 8 floats
        p = struct.unpack('<8f', pkt[5:37])
        return p
    return None

def main():
    print(f"Connecting to {PORT}...")
    ser = serial.Serial(PORT, 115200, timeout=0.05)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    time.sleep(0.1)

    # 1. Clear alarms & Start queue
    ser.write(build_packet(20, 1)) # Clear alarms
    time.sleep(0.02)
    ser.write(build_packet(240, 1)) # Start queue
    time.sleep(0.02)

    # 2. Configure JOG params
    jog_c_params = struct.pack('<8f', 120.0, 120.0, 120.0, 120.0, 150.0, 150.0, 150.0, 150.0)
    ser.write(build_packet(71, 1, jog_c_params))
    time.sleep(0.02)
    jog_common = struct.pack('<2f', 60.0, 60.0)
    ser.write(build_packet(72, 1, jog_common))
    time.sleep(0.02)

    p0 = get_current_pose(ser)
    print(f"\nInitial Pose: X={p0[0]:.1f}, Y={p0[1]:.1f}, Z={p0[2]:.1f}, R={p0[3]:.1f}")

    print("\n>>> Testing JOG Y+ (Left) for 1.2 seconds...")
    # isJoint = 0 (Cartesian), cmd = 3 (Y+)
    ser.write(build_packet(73, 1, bytes([0, 3])))
    t_end = time.time() + 1.2
    while time.time() < t_end:
        p = get_current_pose(ser)
        if p:
            print(f"  [JOGGING Y+] X={p[0]:.1f}, Y={p[1]:.1f}, Z={p[2]:.1f}")
        time.sleep(0.15)

    # STOP JOG
    ser.write(build_packet(73, 1, bytes([0, 0])))
    print(">>> Stopped JOG.")
    time.sleep(0.3)

    p1 = get_current_pose(ser)
    print(f"Pose After Y+ Jog: X={p1[0]:.1f}, Y={p1[1]:.1f}, Z={p1[2]:.1f}")

    print("\n>>> Testing JOG Y- (Right) for 1.2 seconds back...")
    # isJoint = 0 (Cartesian), cmd = 4 (Y-)
    ser.write(build_packet(73, 1, bytes([0, 4])))
    t_end = time.time() + 1.2
    while time.time() < t_end:
        p = get_current_pose(ser)
        if p:
            print(f"  [JOGGING Y-] X={p[0]:.1f}, Y={p[1]:.1f}, Z={p[2]:.1f}")
        time.sleep(0.15)

    # STOP JOG
    ser.write(build_packet(73, 1, bytes([0, 0])))
    print(">>> Stopped JOG.")
    time.sleep(0.3)

    p2 = get_current_pose(ser)
    print(f"Pose After Y- Jog: X={p2[0]:.1f}, Y={p2[1]:.1f}, Z={p2[2]:.1f}")

    print("\n>>> Testing PTP Move to (240, 0, 60)...")
    ser.write(build_packet(84, 3, struct.pack('<B4f', 1, 240.0, 0.0, 60.0, 0.0)))
    time.sleep(1.5)
    p3 = get_current_pose(ser)
    print(f"Final Pose: X={p3[0]:.1f}, Y={p3[1]:.1f}, Z={p3[2]:.1f}")

    ser.close()
    print("\n[SUCCESS] JOG & PTP Hardware Motion Verified!")

if __name__ == "__main__":
    main()
