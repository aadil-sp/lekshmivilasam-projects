#!/usr/bin/env python3
"""
RoboNav-SLAM Master Server & Telemetry Hub
High-speed SSE streaming backend for real-time LiDAR display.
"""

import os, sys, json, time, shutil, subprocess, threading, glob, math, queue
from flask import Flask, send_file, send_from_directory, jsonify, request, Response, stream_with_context

# Hardware Modules
try:
    from motor_controller import motor
    from hand_pid import HandPID
    hand_pid = HandPID(motor)
    hand_pid.start()
except ImportError:
    motor = None; hand_pid = None

APP_DIR          = os.path.dirname(os.path.abspath(__file__))
SIMULATOR_DIR    = os.path.join(APP_DIR, "simulator")
DISPLAY_HUD_HTML = os.path.join(APP_DIR, "display_hud.html")
WEB_CONTROL_HTML = os.path.join(APP_DIR, "web_control.html")
TOUCH_HTML       = os.path.join(APP_DIR, "touch_panel.html")
CALIBRATE_HTML   = os.path.join(APP_DIR, "calibrate16.html")
DRAW_HTML        = os.path.join(APP_DIR, "draw.html")
TUNE_HTML        = os.path.join(APP_DIR, "web_tune.html")

app = Flask(__name__)

# ── Shared robot state ────────────────────────────────────────────────────────
robot_state = {
    "status": "SYSTEM READY", "mode": "MANUAL",
    "ip": "10.215.119.164",
    "cpu_temp": 45.0, "cpu_load": 5,
    "ram_used": 240, "ram_total": 4039, "ram_pct": 6,
    "disk": {"used": 7.4, "total": 116.7},
    "uptime": "0h 0m", "lidar_status": "SEARCHING",
    "lidar_hz": 0.0,
    "pose": {"x": 0.0, "y": 0.0, "theta_deg": 0.0},
    "velocity": {"linear": 0.0, "angular": 0.0}
}

# ── LiDAR frame: latest serialised payload + fan-out queues ──────────────────
latest_lidar_raw  = "[]"
lidar_frame_lock  = threading.Lock()
# Fan-out: each SSE client gets its own queue
_sse_subscribers  = []
_sse_sub_lock     = threading.Lock()

def _broadcast_lidar(pts_json, hz, status):
    """Push a new frame to every active SSE subscriber queue."""
    msg = f'{{"t":"l","hz":{hz},"st":"{status}","pts":{pts_json}}}'
    with _sse_sub_lock:
        for q in _sse_subscribers:
            try:
                q.put_nowait(msg)
            except queue.Full:
                pass  # slow client — skip this frame

# ── Camera Bridge Worker ───────────────────────────────────────────────────────
def camera_bridge_worker():
    bridge_proc = None
    bridge_script = os.path.join(APP_DIR, "realsense_bridge.py")

    while True:
        try:
            if os.path.exists(bridge_script) and (bridge_proc is None or bridge_proc.poll() is not None):
                bridge_proc = subprocess.Popen(
                    [sys.executable, bridge_script],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1.0)
                continue
            
            # Hand tracking is handled by HandPID in a separate thread.
            # We just need to keep the bridge alive.
            time.sleep(2.0)
        except Exception as e:
            time.sleep(1.0)

threading.Thread(target=camera_bridge_worker, daemon=True).start()

# ── System stats worker ───────────────────────────────────────────────────────
def update_system_stats():
    while True:
        try:
            if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
                with open("/sys/class/thermal/thermal_zone0/temp") as f:
                    robot_state["cpu_temp"] = round(int(f.read()) / 1000.0, 1)
            try:
                load1 = os.getloadavg()[0]
                robot_state["cpu_load"] = min(100, max(1, int((load1 / (os.cpu_count() or 4)) * 100)))
            except Exception: pass
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo") as f:
                    lines = f.readlines()
                total = int(lines[0].split()[1]) // 1024
                avail = int(lines[2].split()[1]) // 1024
                robot_state["ram_total"] = total
                robot_state["ram_used"]  = total - avail
                robot_state["ram_pct"]   = int(((total - avail) / total) * 100)
            try:
                tb, ub, _ = shutil.disk_usage("/")
                robot_state["disk"] = {"used": round(ub/(1024**3),1), "total": round(tb/(1024**3),1)}
            except Exception: pass
            if os.path.exists("/proc/uptime"):
                with open("/proc/uptime") as f:
                    sec = float(f.read().split()[0])
                mins = int(sec // 60); hrs = mins // 60; mins %= 60
                robot_state["uptime"] = f"{hrs}h {mins}m"
            r = subprocess.run(["hostname", "-I"], capture_output=True, text=True)
            if r.stdout:
                ips = r.stdout.strip().split()
                if ips: robot_state["ip"] = ips[0]
        except Exception: pass
        time.sleep(1.5)

threading.Thread(target=update_system_stats, daemon=True).start()

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    client_ip = request.remote_addr
    if client_ip in ("127.0.0.1", "localhost", "::1"):
        if os.path.exists(DISPLAY_HUD_HTML): return send_file(DISPLAY_HUD_HTML)
    if os.path.exists(WEB_CONTROL_HTML): return send_file(WEB_CONTROL_HTML)
    if os.path.exists(DISPLAY_HUD_HTML): return send_file(DISPLAY_HUD_HTML)
    return "<h1>RoboNav Ready</h1>"

@app.route("/hud")
@app.route("/display")
def hud():
    return send_file(DISPLAY_HUD_HTML) if os.path.exists(DISPLAY_HUD_HTML) else ("HUD not found", 404)

@app.route("/control")
@app.route("/web")
def web_control():
    return send_file(WEB_CONTROL_HTML) if os.path.exists(WEB_CONTROL_HTML) else ("Web Control not found", 404)

@app.route("/tune")
def tune():
    return send_file(TUNE_HTML) if os.path.exists(TUNE_HTML) else ("Tune not found", 404)

@app.route("/cockpit")
def cockpit():
    return send_file(TOUCH_HTML) if os.path.exists(TOUCH_HTML) else ("Cockpit not found", 404)

@app.route("/draw")
def draw():
    return send_file(DRAW_HTML) if os.path.exists(DRAW_HTML) else ("Draw not found", 404)

@app.route("/calibrate")
@app.route("/calibrate16")
def calibrate():
    return send_file(CALIBRATE_HTML) if os.path.exists(CALIBRATE_HTML) else ("Calibrate not found", 404)

@app.route("/sim")
def sim():
    idx = os.path.join(SIMULATOR_DIR, "index.html")
    return send_from_directory(SIMULATOR_DIR, "index.html") if os.path.exists(idx) else ("Simulator not found", 404)

@app.route("/api/snapshot.png")
def get_snapshot():
    snap = "/tmp/web_snap.png"
    env  = {**os.environ, "XDG_RUNTIME_DIR": "/run/user/1000", "WAYLAND_DISPLAY": "wayland-0"}
    try:
        subprocess.run(["grim", snap], env=env, timeout=2)
        if os.path.exists(snap): return send_file(snap, mimetype="image/png")
    except Exception: pass
    if os.path.exists("/tmp/pi_touch_screen.png"):
        return send_file("/tmp/pi_touch_screen.png", mimetype="image/png")
    return Response(b"", status=404)

# ── API: Telemetry snapshot ───────────────────────────────────────────────────
@app.route("/api/telemetry")
def get_telemetry():
    return jsonify(robot_state)

# ── API: LiDAR snapshot (fallback for one-shot fetches) ──────────────────────
@app.route("/api/lidar")
def get_lidar():
    with lidar_frame_lock:
        pts_raw = latest_lidar_raw
    # Return minimal payload — points already compact JSON
    body = f'{{"status":"{robot_state["lidar_status"]}","hz":{robot_state["lidar_hz"]},"points":{pts_raw}}}'
    return Response(body, mimetype="application/json")

# ── API: SSE stream — pushes a new frame the instant it arrives ───────────────
@app.route("/api/lidar/stream")
def lidar_sse_stream():
    def generate():
        # Register this client's queue
        q = queue.Queue(maxsize=30)
        with _sse_sub_lock:
            _sse_subscribers.append(q)
        # Immediately send last known frame
        with lidar_frame_lock:
            pts = latest_lidar_raw
        hz     = robot_state.get("lidar_hz", 0)
        status = robot_state.get("lidar_status", "")
        yield f'data:{{"ok":true,"hz":{hz},"st":"{status}","pts":{pts}}}\n\n'
        try:
            while True:
                try:
                    msg = q.get(timeout=1.0)
                    yield f'data:{msg}\n\n'
                except queue.Empty:
                    yield ': keepalive\n\n'  # SSE comment = keepalive
        except GeneratorExit:
            pass
        finally:
            with _sse_sub_lock:
                try: _sse_subscribers.remove(q)
                except ValueError: pass

    resp = Response(stream_with_context(generate()), mimetype="text/event-stream")
    resp.headers["Cache-Control"]               = "no-cache"
    resp.headers["X-Accel-Buffering"]           = "no"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

# ── API: Combined SSE stream (telemetry + lidar, one connection) ──────────────
@app.route("/api/stream")
def combined_sse_stream():
    def generate():
        q = queue.Queue(maxsize=30)
        with _sse_sub_lock:
            _sse_subscribers.append(q)
        last_tel_push = 0.0
        # Send initial state
        with lidar_frame_lock:
            pts = latest_lidar_raw
        hz     = robot_state.get("lidar_hz", 0)
        status = robot_state.get("lidar_status", "")
        yield f'data:{{"t":"l","hz":{hz},"st":"{status}","pts":{pts}}}\n\n'
        try:
            while True:
                try:
                    msg = q.get(timeout=1.5)
                    yield f'data:{msg}\n\n'
                except queue.Empty:
                    yield ': keepalive\n\n'
                    msg = None

                now = time.time()
                if now - last_tel_push > 1.5:
                    last_tel_push = now
                    tel = json.dumps({"t": "s", **robot_state}, separators=(',', ':'))
                    yield f'data:{tel}\n\n'
        except GeneratorExit:
            pass
        finally:
            with _sse_sub_lock:
                try: _sse_subscribers.remove(q)
                except ValueError: pass

    resp = Response(stream_with_context(generate()), mimetype="text/event-stream")
    resp.headers["Cache-Control"]               = "no-cache"
    resp.headers["X-Accel-Buffering"]           = "no"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

# ── API: Control ──────────────────────────────────────────────────────────────
@app.route("/api/screen_app", methods=["POST"])
def post_screen_app():
    data = request.json or {}
    target = data.get("app", "/hud")
    content = f'''#!/usr/bin/env bash
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
  --app=http://localhost:5000{target} &
'''
    try:
        with open("/home/lekshmi/.config/labwc/autostart", "w") as f: f.write(content)
        subprocess.Popen(["sudo", "systemctl", "restart", "getty@tty1.service"])
        return jsonify({"success": True, "app": target})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/mode", methods=["POST"])
def post_mode():
    data = request.json or {}
    mode = data.get("mode", "MANUAL")
    robot_state["mode"] = mode
    
    if mode == "FOLLOW":
        if hand_pid: hand_pid.start()
    else:
        if hand_pid: hand_pid.stop()
        if motor: motor.stop()
        
    return jsonify({"ok": True, "mode": mode})

@app.route("/api/pid", methods=["POST"])
def api_pid():
    data = request.json or {}
    if hand_pid:
        hand_pid.kp_lin = data.get("lin_p", 0.002)
        hand_pid.kd_lin = data.get("lin_d", 0.001)
        hand_pid.kp_rot = data.get("rot_p", 0.002)
        hand_pid.kd_rot = data.get("rot_d", 0.001)
    if motor:
        motor.set_min_pwm(data.get("min_l", 80), data.get("min_r", 80))
    return jsonify({"ok": True})

@app.route("/api/drive", methods=["POST"])
def post_drive():
    data = request.json or {}
    direction = data.get("dir", "STOP")
    speed = float(data.get("speed", 0.5))
    
    # Only allow manual drive if in MANUAL or MAPPING mode
    if robot_state["mode"] not in ("MANUAL", "MAPPING"):
        return jsonify({"success": False, "error": "Not in manual mode"})
        
    if motor:
        motor.drive(direction, speed)
        
    v = robot_state["velocity"]
    if direction == "FWD":   v["linear"] =  speed; v["angular"] = 0.0; robot_state["status"] = "MOVING FWD"
    elif direction == "REV": v["linear"] = -speed; v["angular"] = 0.0; robot_state["status"] = "MOVING REV"
    elif direction == "LEFT":  v["linear"] = 0.0; v["angular"] =  speed*2; robot_state["status"] = "TURNING LEFT"
    elif direction == "RIGHT": v["linear"] = 0.0; v["angular"] = -speed*2; robot_state["status"] = "TURNING RIGHT"
    else:                      v["linear"] = 0.0; v["angular"] = 0.0; robot_state["status"] = "HOLD"
    
    if slam:
        slam.set_velocity_command(v["linear"], v["angular"])
        
    return jsonify({"success": True, "velocity": v})

@app.route("/api/navigate", methods=["POST"])
def post_navigate():
    data = request.json or {}
    norm_x = data.get("x", 0.5)
    norm_y = data.get("y", 0.5)
    
    if slam:
        # Convert 0-1 normalized coordinates to mm
        # Map size is slam.map_size, resolution is slam.resolution
        gx_mm = norm_x * slam.map_size * slam.resolution
        gy_mm = norm_y * slam.map_size * slam.resolution
        slam.set_goal(gx_mm, gy_mm)
        return jsonify({"success": True, "goal": [gx_mm, gy_mm]})
    return jsonify({"success": False, "error": "No SLAM module"})

@app.route("/api/map", methods=["GET"])
def get_map():
    if not slam:
        return Response(b"", status=404)
    b64 = slam.get_map_png_b64()
    return jsonify({"image": "data:image/png;base64," + b64})

@app.route("/api/map/clear", methods=["POST"])
def post_map_clear():
    if slam:
        slam.clear_map()
    return jsonify({"success": True})

@app.route("/api/arduino/cmd", methods=["POST"])
def post_arduino_cmd():
    data = request.json or {}
    cmd = data.get("cmd")
    if motor and cmd:
        motor.send_command(cmd)
    return jsonify({"success": True})

@app.route("/api/system", methods=["POST"])
def post_system():
    data = request.json or {}
    action = data.get("action")
    if action == "reboot":   subprocess.Popen(["sudo", "reboot"]);   return jsonify({"success": True})
    if action == "shutdown": subprocess.Popen(["sudo", "poweroff"]); return jsonify({"success": True})
    return jsonify({"error": "Invalid action"}), 400

if __name__ == "__main__":
    print("[*] RoboNav Master Server — port 5000 (Hardware integration + SSE)")
    app.run(host="0.0.0.0", port=5000, threaded=True)
