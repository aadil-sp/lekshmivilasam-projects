#!/usr/bin/env bash
set -e

echo "========================================="
echo "   RoboNav-SLAM: RPLiDAR Quick Setup"
echo "========================================="

# 1. Check Serial Port
echo "[1/4] Checking for RPLiDAR USB serial devices..."
LIDAR_PORT=$(ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null | head -n 1 || true)

if [ -z "$LIDAR_PORT" ]; then
    echo "[!] No USB serial device found! Please ensure RPLiDAR is plugged into the Pi."
    echo "[*] Available ports:"
    ls -l /dev/tty* 2>/dev/null || true
else
    echo "[+] Found device on port: $LIDAR_PORT"
    echo "[2/4] Setting serial permissions..."
    sudo chmod 666 "$LIDAR_PORT" || true
    sudo usermod -a -G dialout "$USER" 2>/dev/null || true
fi

# 2. Install dependencies
echo "[3/4] Installing Python drivers and display libraries..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3-pip python3-matplotlib python3-numpy python3-serial

pip3 install rplidar-roboticia --break-system-packages 2>/dev/null || pip3 install rplidar-roboticia || true

# 3. Launch Option
echo "[4/4] Setup complete!"
echo ""
echo "Select how you want to view the LiDAR:"
echo "1) Fullscreen Live Polar Radar GUI (view_lidar.py)"
echo "2) RoboNav HUD & Web Server (robonav_server.py on port 5000)"
echo ""
read -p "Enter choice [1 or 2] (default: 1): " CHOICE
CHOICE=${CHOICE:-1}

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$CHOICE" == "2" ]; then
    echo "[*] Starting RoboNav Master Server..."
    python3 "$DIR/robonav_server.py"
else
    echo "[*] Launching Live RPLiDAR Display..."
    python3 "$DIR/view_lidar.py"
fi
