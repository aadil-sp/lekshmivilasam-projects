#!/usr/bin/env python3
"""
RoboNav-SLAM Master Server & Telemetry Hub
Serves:
- 3.5" SPI Display Status HUD (http://localhost:5000/hud)
- Mac Remote Control Dashboard (http://<IP>:5000)
- Live Video & Depth Feeds (/video_feed, /depth_feed)
- Live DRM Frame Snapshot (/api/snapshot.png)
- Real-time Hardware & Robotics Telemetry (/api/telemetry)
"""

import os
import sys
import json
import time
import shutil
import urllib.request
import subprocess
import threading
from flask import Flask, send_file, send_from_directory, jsonify, request, Response

# Hardware Modules
try:
    from motor_controller import motor
    from hand_pid import HandPID
    hand_pid = HandPID(motor)
    hand_pid.start()
except Exception:
    motor = None
    hand_pid = None

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SIMULATOR_DIR = os.path.join(APP_DIR, "simulator")
DISPLAY_HUD_HTML = os.path.join(APP_DIR, "display_hud.html")
WEB_CONTROL_HTML = os.path.join(APP_DIR, "web_control.html")
TOUCH_HTML = os.path.join(APP_DIR, "touch_panel.html")
CALIBRATE_HTML = os.path.join(APP_DIR, "calibrate16.html")
DRAW_HTML = os.path.join(APP_DIR, "draw.html")
TUNE_HTML = os.path.join(APP_DIR, "web_tune.html")

app = Flask(__name__)

# State
robot_state = {
    "status": "SYSTEM READY",
    "mode": "MANUAL",
    "ip": "10.68.210.164",
    "cpu_temp": 42.0,
    "cpu_load": 5,
    "ram_used": 240,
    "ram_total": 4039,
    "ram_pct": 6,
    "disk": {"used": 7.4, "total": 116.7},
    "uptime": "0h 1m",
    "lidar_status": "READY",
    "pose": {"x": 0.0, "y": 0.0, "theta_deg": 0.0},
    "velocity": {"linear": 0.0, "angular": 0.0}
}

def update_system_stats():
    while True:
        try:
            # CPU Temp
            if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    robot_state["cpu_temp"] = round(int(f.read().strip()) / 1000.0, 1)

            # CPU Load
            try:
                load1 = os.getloadavg()[0]
                cores = os.cpu_count() or 4
                robot_state["cpu_load"] = min(100, max(1, int((load1 / cores) * 100)))
            except Exception:
                pass

            # RAM
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo", "r") as f:
                    lines = f.readlines()
                    total = int(lines[0].split()[1]) // 1024
                    avail = int(lines[2].split()[1]) // 1024
                    used = total - avail
                    robot_state["ram_total"] = total
                    robot_state["ram_used"] = used
                    robot_state["ram_pct"] = int((used / total) * 100)

            # Disk
            try:
                total_b, used_b, free_b = shutil.disk_usage("/")
                robot_state["disk"] = {
                    "used": round(used_b / (1024**3), 1),
                    "total": round(total_b / (1024**3), 1)
                }
            except Exception:
                pass

            # Uptime
            if os.path.exists("/proc/uptime"):
                with open("/proc/uptime", "r") as f:
                    sec = float(f.read().split()[0])
                    mins = int(sec // 60)
                    hrs = mins // 60
                    mins = mins % 60
                    robot_state["uptime"] = f"{hrs}h {mins}m"

            # IP
            ip_cmd = subprocess.run(["hostname", "-I"], capture_output=True, text=True)
            if ip_cmd.stdout:
                ips = ip_cmd.stdout.strip().split()
                if ips:
                    robot_state["ip"] = ips[0]
        except Exception:
            pass
        time.sleep(1.5)

threading.Thread(target=update_system_stats, daemon=True).start()

@app.route("/")
def index():
    client_ip = request.remote_addr
    if client_ip in ("127.0.0.1", "localhost", "::1"):
        if os.path.exists(DISPLAY_HUD_HTML):
            return send_file(DISPLAY_HUD_HTML)
    
    if os.path.exists(WEB_CONTROL_HTML):
        return send_file(WEB_CONTROL_HTML)
    if os.path.exists(DISPLAY_HUD_HTML):
        return send_file(DISPLAY_HUD_HTML)
    return "<h1>RoboNav Ready</h1>"

@app.route("/hud")
@app.route("/display")
def hud():
    if os.path.exists(DISPLAY_HUD_HTML):
        return send_file(DISPLAY_HUD_HTML)
    return "Display HUD not found"

@app.route("/control")
@app.route("/web")
def web_control():
    if os.path.exists(WEB_CONTROL_HTML):
        return send_file(WEB_CONTROL_HTML)
    return "Web Control not found"

def proxy_feed(endpoint):
    def generate():
        url = f"http://127.0.0.1:5001/{endpoint}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as stream:
                while True:
                    chunk = stream.read(4096)
                    if not chunk:
                        break
                    yield chunk
        except Exception:
            yield b""
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/video_feed")
def video_feed():
    return proxy_feed("video_feed")

@app.route("/depth_feed")
def depth_feed():
    return proxy_feed("depth_feed")

@app.route("/tune")
def tune():
    if os.path.exists(TUNE_HTML):
        return send_file(TUNE_HTML)
    return "Web Studio not found"

@app.route("/cockpit")
def cockpit():
    if os.path.exists(TOUCH_HTML):
        return send_file(TOUCH_HTML)
    return "Cockpit not found"

@app.route("/draw")
def draw():
    if os.path.exists(DRAW_HTML):
        return send_file(DRAW_HTML)
    return "Draw tool not found"

@app.route("/calibrate")
@app.route("/calibrate16")
def calibrate():
    if os.path.exists(CALIBRATE_HTML):
        return send_file(CALIBRATE_HTML)
    return "Calibration page not found"

@app.route("/sim")
def sim():
    if os.path.exists(os.path.join(SIMULATOR_DIR, "index.html")):
        return send_from_directory(SIMULATOR_DIR, "index.html")
    return "Simulator not found"

@app.route("/api/snapshot.png")
def get_snapshot():
    snap_path = "/tmp/web_snap.png"
    env = os.environ.copy()
    env["XDG_RUNTIME_DIR"] = "/run/user/1000"
    env["WAYLAND_DISPLAY"] = "wayland-0"
    try:
        subprocess.run(["grim", snap_path], env=env, timeout=2)
        if os.path.exists(snap_path):
            return send_file(snap_path, mimetype="image/png")
    except Exception:
        pass
    if os.path.exists("/tmp/pi_touch_screen.png"):
        return send_file("/tmp/pi_touch_screen.png", mimetype="image/png")
    return Response(b"", status=404)

@app.route("/api/screen_app", methods=["POST"])
def post_screen_app():
    data = request.json or {}
    target_app = data.get("app", "/hud")
    
    autostart_content = f'''#!/usr/bin/env bash
wlr-randr --output SPI-1 --transform 90 2>/dev/null || true
wayvnc 0.0.0.0 5900 &
sleep 1
chromium \\
  --kiosk \\
  --noerrdialogs \\
  --disable-infobars \\
  --check-for-update-interval=31536000 \\
  --disable-session-crashed-bubble \\
  --disable-pinch \\
  --no-first-run \\
  --window-size=480,320 \\
  --app=http://localhost:5000{target_app} &
'''
    try:
        with open("/home/lekshmi/.config/labwc/autostart", "w") as f:
            f.write(autostart_content)
        subprocess.Popen(["sudo", "systemctl", "restart", "getty@tty1.service"])
        return jsonify({"success": True, "app": target_app})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/control", methods=["POST"])
def post_control():
    data = request.json or {}
    cmd = data.get("command")
    if cmd == "start_robot" or cmd == "start_follow":
        robot_state["status"] = "HAND FOLLOW ACTIVE"
        robot_state["mode"] = "HAND_FOLLOW"
        if hand_pid:
            hand_pid.start()
    elif cmd == "stop_robot" or cmd == "stop_follow":
        robot_state["status"] = "STOPPED (MANUAL)"
        robot_state["mode"] = "MANUAL"
        robot_state["velocity"] = {"linear": 0.0, "angular": 0.0}
        if hand_pid:
            hand_pid.stop()
        if motor:
            motor.stop()
    elif cmd == "reset_slam":
        robot_state["status"] = "MAP RESET"
        robot_state["pose"] = {"x": 0.0, "y": 0.0, "theta_deg": 0.0}
    return jsonify({"success": True, "state": robot_state})

@app.route("/api/drive", methods=["POST"])
def post_drive():
    data = request.json or {}
    direction = data.get("dir", "STOP")
    speed = float(data.get("speed", 0.5))
    
    if direction == "FWD":
        robot_state["velocity"] = {"linear": speed, "angular": 0.0}
        robot_state["status"] = "MOVING FWD"
        if motor: motor.forward(speed)
    elif direction == "REV":
        robot_state["velocity"] = {"linear": -speed, "angular": 0.0}
        robot_state["status"] = "MOVING REV"
        if motor: motor.backward(speed)
    elif direction == "LEFT":
        robot_state["velocity"] = {"linear": 0.0, "angular": speed * 2}
        robot_state["status"] = "TURNING LEFT"
        if motor: motor.turn_left(speed)
        robot_state["pose"]["theta_deg"] = (robot_state["pose"]["theta_deg"] - 15) % 360
    elif direction == "RIGHT":
        robot_state["velocity"] = {"linear": 0.0, "angular": -speed * 2}
        robot_state["status"] = "TURNING RIGHT"
        if motor: motor.turn_right(speed)
        robot_state["pose"]["theta_deg"] = (robot_state["pose"]["theta_deg"] + 15) % 360
    else:
        robot_state["velocity"] = {"linear": 0.0, "angular": 0.0}
        robot_state["status"] = "HOLD"
        if motor: motor.stop()
        
    return jsonify({"success": True, "velocity": robot_state["velocity"]})

@app.route("/api/pid", methods=["POST"])
def post_pid():
    data = request.json or {}
    if hand_pid:
        if "kp_lin" in data: hand_pid.kp_lin = float(data["kp_lin"])
        if "kd_lin" in data: hand_pid.kd_lin = float(data["kd_lin"])
        if "kp_rot" in data: hand_pid.kp_rot = float(data["kp_rot"])
        if "kd_rot" in data: hand_pid.kd_rot = float(data["kd_rot"])
    return jsonify({"success": True})

@app.route("/api/telemetry", methods=["GET"])
def get_telemetry():
    return jsonify(robot_state)

@app.route("/api/system", methods=["POST"])
def post_system():
    data = request.json or {}
    action = data.get("action")
    if action == "reboot":
        subprocess.Popen(["sudo", "reboot"])
        return jsonify({"success": True, "message": "Rebooting..."})
    elif action == "shutdown":
        subprocess.Popen(["sudo", "poweroff"])
        return jsonify({"success": True, "message": "Shutting down..."})
    return jsonify({"error": "Invalid action"}), 400

if __name__ == "__main__":
    print("[*] RoboNav Master Server starting on port 5000...")
    app.run(host="0.0.0.0", port=5000, threaded=True)
