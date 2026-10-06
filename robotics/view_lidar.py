#!/usr/bin/env python3
"""
RoboNav-SLAM: Standalone Live RPLiDAR 360° Visualizer
Plots real-time distance measurements on a polar radar display.
"""

import sys
import glob
import math
import numpy as np
import matplotlib.pyplot as plt

def find_lidar_port():
    # Common ports on Linux (Pi) and macOS
    candidates = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*') + glob.glob('/dev/cu.usbserial*') + glob.glob('/dev/tty.usbserial*')
    if candidates:
        return candidates[0]
    return '/dev/ttyUSB0'

def main():
    try:
        from rplidar import RPLidar
    except ImportError:
        print("[!] RPLidar library not found. Please install with:")
        print("    pip install rplidar-roboticia --break-system-packages")
        print("    or: pip3 install rplidar-roboticia")
        sys.exit(1)

    port = sys.argv[1] if len(sys.argv) > 1 else find_lidar_port()
    baudrate = int(sys.argv[2]) if len(sys.argv) > 2 else 115200

    print(f"[*] Connecting to RPLiDAR on port: {port} @ {baudrate} baud...")

    try:
        lidar = RPLidar(port, baudrate=baudrate, timeout=3)
        info = lidar.get_info()
        health = lidar.get_health()
        print(f"[+] Device Info: {info}")
        print(f"[+] Device Health: {health}")
    except Exception as e:
        print(f"[!] Failed to connect to RPLiDAR on {port}: {e}")
        print("[*] Tip: If using RPLiDAR A2M8/A3/S1, try baudrate 256000:")
        print(f"    python3 {sys.argv[0]} {port} 256000")
        print("[*] Also check permissions: sudo chmod 666 /dev/ttyUSB0")
        sys.exit(1)

    # Setup interactive polar plot
    plt.ion()
    fig = plt.figure(figsize=(8, 8), facecolor='#090d16')
    ax = fig.add_subplot(111, projection='polar', facecolor='#0f172a')
    
    # Configure Polar Axis
    ax.set_theta_zero_location('N')  # 0 deg = Front / North
    ax.set_theta_direction(-1)       # Clockwise
    ax.set_ylim(0, 4000)             # 0 to 4 meters
    ax.set_title("RPLiDAR Live 360° Radar Scan (Distances in mm)", color='#38bdf8', fontsize=14, pad=15, fontweight='bold')
    
    # Styling
    ax.tick_params(colors='#94a3b8')
    ax.grid(color='#1e293b', linestyle='--', linewidth=0.8)
    for spine in ax.spines.values():
        spine.set_color('#38bdf8')
        spine.set_alpha(0.3)

    scatter = ax.scatter([], [], c=[], cmap='plasma', s=12, alpha=0.9)
    fig.tight_layout()

    print("[+] RPLiDAR Scanning Active! Close window or press Ctrl+C to stop.")

    try:
        for scan in lidar.iter_scans(max_buf_meas=500):
            # scan item format: (quality, angle_degrees, distance_mm)
            valid_points = [(p[1], p[2]) for p in scan if p[2] > 0]
            if not valid_points:
                continue

            angles = [np.radians(p[0]) for p in valid_points]
            distances = [p[1] for p in valid_points]

            ax.clear()
            ax.set_facecolor('#0f172a')
            ax.set_theta_zero_location('N')
            ax.set_theta_direction(-1)
            ax.set_ylim(0, 4000)
            ax.set_title(f"RPLiDAR Live Scan ({len(distances)} pts)", color='#38bdf8', fontsize=13, pad=12, fontweight='bold')
            ax.tick_params(colors='#94a3b8')
            ax.grid(color='#1e293b', linestyle='--', linewidth=0.8)

            # Draw points (color-coded by distance: green close, blue/purple far)
            ax.scatter(angles, distances, c=distances, cmap='winter', s=10, alpha=0.85)

            # Center origin (robot position)
            ax.scatter([0], [0], c='#f59e0b', s=50, marker='o', label='Robot')

            plt.pause(0.001)

    except KeyboardInterrupt:
        print("\n[*] Stopping LiDAR...")
    finally:
        try:
            lidar.stop()
            lidar.stop_motor()
            lidar.disconnect()
        except Exception:
            pass
        plt.close()
        print("[+] LiDAR stopped and disconnected successfully.")

if __name__ == '__main__':
    main()
