#!/usr/bin/env python3
"""
RoboNav Ultra-Light Vision Core & Index Finger Follower
- Real-time 30 FPS Camera Capture & MediaPipe Index Fingertip Tracking
- Default Autonomous Hand-Follow Mode
- Instant WASD / D-Pad Keyboard Manual Override with Auto-Resume
- Zero-Latency Dual MJPEG Stream & Telemetry Server
"""

import os
import sys
import time
import json
import glob
import math
import shutil
import threading
import subprocess
import numpy as np
import cv2
from flask import Flask, Response, jsonify, request, send_file, send_from_directory

# ── Flask App Setup ──────────────────────────────────────────────────────────
app = Flask(__name__)
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DISPLAY_HUD_HTML = os.path.join(APP_DIR, "display_hud.html")
WEB_CONTROL_HTML = os.path.join(APP_DIR, "web_control.html")

# ── Hardware Motor Controller ────────────────────────────────────────────────
try:
    from motor_controller import motor
except Exception as e:
    print(f"[!] MotorController import warning: {e}")
    motor = None

# ── Resolutions & FOV ────────────────────────────────────────────────────────
RGB_W, RGB_H = 640, 480
DEPTH_W, DEPTH_H = 640, 480
OUT_W, OUT_H = 320, 240
FOV_H = 87.0

# ── Global State & Condition Sync ────────────────────────────────────────────
frame_lock = threading.Lock()
frame_cond = threading.Condition(frame_lock)

latest_rgb_jpeg = None
latest_depth_jpeg = None
latest_depth_raw = None
rgb_seq = 0
depth_seq = 0
rgb_fps = 0.0
depth_fps = 0.0

tracking_data = {
    "found": False,
    "cx": 0, "cy": 0,
    "dist_mm": 0,
    "err_x": 0, "err_d": 0,
    "fps": 0.0
}

# ── PID & Mode Configuration (DEFAULT: Hand Follow ACTIVE) ───────────────────
pid_config = {
    "active": True, # Default: Hand Follow Enabled on Boot
    "target_dist_mm": 350,
    "kp_lin": 0.0018, "kd_lin": 0.0008,
    "kp_rot": 0.0022, "kd_rot": 0.0010,
    "min_pwm": 80, "max_speed": 0.6
}

manual_override_until = 0.0
prev_err_x = 0
prev_err_d = 0

# ── MediaPipe Index Finger Landmarker ────────────────────────────────────────
detector = None
try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    model_path = os.path.join(APP_DIR, 'hand_landmarker.task')
    if os.path.exists(model_path):
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1,
            min_hand_detection_confidence=0.4,
            min_hand_presence_confidence=0.4
        )
        detector = vision.HandLandmarker.create_from_options(options)
        print("[✓] MediaPipe Index Finger Tracker ready.")
except Exception as e:
    print(f"[!] MediaPipe init error: {e}")

# ── Placeholder Generator ───────────────────────────────────────────────────
def make_placeholder(text, color=(15, 23, 42)):
    img = np.full((OUT_H, OUT_W, 3), color, dtype=np.uint8)
    cv2.putText(img, text, (20, OUT_H // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (56, 189, 248), 1, cv2.LINE_AA)
    _, buf = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
    return buf.tobytes()

# ── V4L2 Device Auto-Finder ─────────────────────────────────────────────────
def find_devices():
    depth_dev, rgb_dev = None, None
    for dev in sorted(glob.glob('/dev/video*')):
        try:
            info = subprocess.run(['v4l2-ctl', '-d', dev, '-D'], capture_output=True, text=True, timeout=0.5)
            if 'pisp' in info.stdout.lower() or 'hevc' in info.stdout.lower():
                continue
            fmts = subprocess.run(['v4l2-ctl', '-d', dev, '--list-formats'], capture_output=True, text=True, timeout=0.5)
            if 'Z16' in fmts.stdout and not depth_dev:
                depth_dev = dev
            elif ('YUYV' in fmts.stdout or 'MJPG' in fmts.stdout or 'RGB' in fmts.stdout) and not rgb_dev:
                rgb_dev = dev
        except Exception:
            pass
    return depth_dev, rgb_dev

# ── RGB Capture & Index Finger Tracking Worker ──────────────────────────────
def rgb_worker():
    global latest_rgb_jpeg, rgb_seq, rgb_fps, tracking_data
    frame_times = []
    
    while True:
        _, rgb_dev = find_devices()
        if not rgb_dev:
            with frame_cond:
                latest_rgb_jpeg = make_placeholder("RGB Camera: Searching USB...")
                rgb_seq += 1
                frame_cond.notify_all()
            time.sleep(1.5)
            continue
            
        cap = cv2.VideoCapture(rgb_dev, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, RGB_W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RGB_H)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        
        if not cap.isOpened():
            time.sleep(1.0)
            continue
            
        print(f"[✓] RGB Camera opened on {rgb_dev} (Target: 30 FPS)")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or frame is None:
                break
                
            found = False
            cx, cy, dist_mm = 0, 0, 0
            
            # MediaPipe Index Finger Detection
            if detector:
                small = cv2.resize(frame, (256, 192), interpolation=cv2.INTER_LINEAR)
                rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_small)
                results = detector.detect(mp_img)
                
                if results.hand_landmarks:
                    landmarks = results.hand_landmarks[0]
                    # Landmark 8 = INDEX_FINGER_TIP
                    index_tip = landmarks[8]
                    cx = int(index_tip.x * RGB_W)
                    cy = int(index_tip.y * RGB_H)
                    
                    # Fetch depth distance from synchronized depth frame
                    with frame_lock:
                        if latest_depth_raw is not None:
                            d_h, d_w = latest_depth_raw.shape
                            sx = max(0, min(d_w - 30, cx - 15))
                            sy = max(0, min(d_h - 30, cy - 15))
                            roi = latest_depth_raw[sy:sy+30, sx:sx+30]
                            valid = roi[(roi > 80) & (roi < 3000)]
                            if len(valid) > 0:
                                dist_mm = int(np.percentile(valid, 15))
                                
                    found = True
                    err_x = cx - (RGB_W / 2)
                    err_d = (dist_mm - pid_config["target_dist_mm"]) if dist_mm > 0 else 0
                    
                    tracking_data = {
                        "found": True,
                        "cx": cx, "cy": cy,
                        "dist_mm": dist_mm,
                        "err_x": err_x, "err_d": err_d,
                        "fps": rgb_fps
                    }
                    
                    # 🎯 Target Crosshair on Index Finger Tip
                    cv2.circle(frame, (cx, cy), 14, (0, 255, 0), 2, cv2.LINE_AA)
                    cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1, cv2.LINE_AA)
                    cv2.line(frame, (cx - 20, cy), (cx + 20, cy), (0, 255, 0), 1, cv2.LINE_AA)
                    cv2.line(frame, (cx, cy - 20), (cx, cy + 20), (0, 255, 0), 1, cv2.LINE_AA)
                    
                    # Target info text
                    txt = f"INDEX TIP: {dist_mm}mm" if dist_mm > 0 else "INDEX TIP TRACKED"
                    cv2.putText(frame, txt, (max(10, cx - 70), max(25, cy - 25)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2, cv2.LINE_AA)
            
            if not found:
                tracking_data["found"] = False
                
            # Real FPS calculation
            t1 = time.time()
            frame_times.append(t1)
            while frame_times and (t1 - frame_times[0]) > 1.0:
                frame_times.pop(0)
            rgb_fps = round(len(frame_times), 1)
            
            # HUD Mode Overlay
            is_manual = (time.time() < manual_override_until)
            mode_label = "WASD OVERRIDE" if is_manual else ("HAND FOLLOW" if pid_config["active"] else "MANUAL")
            color = (56, 189, 248) if not is_manual else (245, 158, 11)
            cv2.putText(frame, f"{mode_label} | {rgb_fps} FPS", (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2, cv2.LINE_AA)
            
            # Fast downscale for streaming
            out_frame = cv2.resize(frame, (OUT_W, OUT_H), interpolation=cv2.INTER_LINEAR)
            _, encoded = cv2.imencode('.jpg', out_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
            
            with frame_cond:
                latest_rgb_jpeg = encoded.tobytes()
                rgb_seq += 1
                frame_cond.notify_all()
                
        cap.release()
        time.sleep(0.5)

# ── Depth Worker ─────────────────────────────────────────────────────────────
def depth_worker():
    global latest_depth_jpeg, latest_depth_raw, depth_seq, depth_fps
    p = None
    frame_size = DEPTH_W * DEPTH_H * 2
    frame_times = []
    
    while True:
        depth_dev, _ = find_devices()
        if not depth_dev:
            with frame_cond:
                latest_depth_jpeg = make_placeholder("Depth Camera: Searching USB...")
                depth_seq += 1
                frame_cond.notify_all()
            time.sleep(1.5)
            continue
            
        cmd_str = f"v4l2-ctl -d {depth_dev} --set-parm=30 --set-fmt-video=width={DEPTH_W},height={DEPTH_H},pixelformat=\"Z16 \" --stream-mmap --stream-count=0 --stream-to=-"
        try:
            p = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            while True:
                raw_data = p.stdout.read(frame_size)
                if len(raw_data) != frame_size:
                    time.sleep(0.02)
                    break
                    
                depth_img = np.frombuffer(raw_data, dtype=np.uint16).reshape((DEPTH_H, DEPTH_W))
                
                # Fast colormap visualization
                small_depth = cv2.resize(depth_img, (OUT_W, OUT_H), interpolation=cv2.INTER_NEAREST)
                depth_vis = np.clip(small_depth, 0, 3500)
                depth_vis = (depth_vis / 3500.0 * 255).astype(np.uint8)
                depth_colormap = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)
                
                t1 = time.time()
                frame_times.append(t1)
                while frame_times and (t1 - frame_times[0]) > 1.0:
                    frame_times.pop(0)
                depth_fps = round(len(frame_times), 1)
                cv2.putText(depth_colormap, f"DEPTH: {depth_fps} FPS", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                
                _, encoded = cv2.imencode('.jpg', depth_colormap, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                
                with frame_cond:
                    latest_depth_raw = depth_img
                    latest_depth_jpeg = encoded.tobytes()
                    depth_seq += 1
                    frame_cond.notify_all()
                    
        except Exception as e:
            print("Depth worker error:", e)
            time.sleep(1.0)
        finally:
            if p:
                p.kill()
                p = None

# ── Index Finger PID Follower Loop with Manual WASD Override ─────────────────
def pid_loop():
    global prev_err_x, prev_err_d
    while True:
        try:
            # Check if user is actively driving manually
            is_manual_override = (time.time() < manual_override_until)
            
            if not is_manual_override and pid_config["active"] and tracking_data["found"] and motor is not None:
                err_x = tracking_data["err_x"]
                err_d = tracking_data["err_d"]
                
                # Angular PID (Turning to center the index fingertip)
                p_rot = pid_config["kp_rot"] * err_x
                d_rot = pid_config["kd_rot"] * (err_x - prev_err_x)
                cmd_rot = p_rot + d_rot
                prev_err_x = err_x
                
                # Linear PID (Maintaining follow distance)
                p_lin = pid_config["kp_lin"] * err_d
                d_lin = pid_config["kd_lin"] * (err_d - prev_err_d)
                cmd_lin = p_lin + d_lin
                prev_err_d = err_d
                
                # Deadzone checking
                if abs(err_d) < 35 and abs(err_x) < 40:
                    motor.stop()
                else:
                    l_spd = max(-pid_config["max_speed"], min(pid_config["max_speed"], cmd_lin + cmd_rot))
                    r_spd = max(-pid_config["max_speed"], min(pid_config["max_speed"], cmd_lin - cmd_rot))
                    motor.differential(l_spd, r_spd)
            elif not is_manual_override:
                prev_err_x = 0
                prev_err_d = 0
        except Exception:
            pass
        time.sleep(0.033) # 30 Hz Control Loop

# ── MJPEG Stream Generators ──────────────────────────────────────────────────
def stream_mjpeg(stream_type):
    last_seq = -1
    while True:
        with frame_cond:
            if stream_type == 'rgb':
                while rgb_seq == last_seq or latest_rgb_jpeg is None:
                    frame_cond.wait(timeout=0.1)
                    if latest_rgb_jpeg is None: break
                data = latest_rgb_jpeg
                last_seq = rgb_seq
            else:
                while depth_seq == last_seq or latest_depth_jpeg is None:
                    frame_cond.wait(timeout=0.1)
                    if latest_depth_jpeg is None: break
                data = latest_depth_jpeg
                last_seq = depth_seq
                
        if data:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + data + b'\r\n')
        else:
            time.sleep(0.03)

# ── Web Endpoints ────────────────────────────────────────────────────────────
@app.route('/')
def index():
    client_ip = request.remote_addr
    if client_ip in ("127.0.0.1", "localhost", "::1"):
        if os.path.exists(DISPLAY_HUD_HTML): return send_file(DISPLAY_HUD_HTML)
    if os.path.exists(WEB_CONTROL_HTML): return send_file(WEB_CONTROL_HTML)
    return "<h1>RoboNav Vision Core Ready</h1>"

@app.route('/hud')
def hud():
    if os.path.exists(DISPLAY_HUD_HTML): return send_file(DISPLAY_HUD_HTML)
    return "Display HUD not found"

@app.route('/video_feed')
def video_feed():
    return Response(stream_mjpeg('rgb'), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/depth_feed')
def depth_feed():
    return Response(stream_mjpeg('depth'), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/drive', methods=['POST'])
def post_drive():
    """Manual Drive Command (WASD Override)"""
    global manual_override_until
    data = request.json or {}
    direction = data.get("dir", "STOP")
    speed = float(data.get("speed", 0.6))
    
    if direction in ("FWD", "REV", "LEFT", "RIGHT"):
        manual_override_until = time.time() + 1.2 # Override for 1.2s
        if motor:
            motor.drive(direction, speed)
    else:
        manual_override_until = time.time() + 0.3
        if motor:
            motor.stop()
            
    return jsonify({
        "success": True,
        "direction": direction,
        "manual_override": True
    })

@app.route('/api/control', methods=['POST'])
def post_control():
    data = request.json or {}
    cmd = data.get("command")
    if cmd == "start_follow":
        pid_config["active"] = True
    elif cmd == "stop_follow" or cmd == "stop":
        pid_config["active"] = False
        if motor: motor.stop()
    return jsonify({"success": True, "pid_active": pid_config["active"]})

@app.route('/api/pid', methods=['POST'])
def post_pid():
    data = request.json or {}
    for k in ["kp_lin", "kd_lin", "kp_rot", "kd_rot", "target_dist_mm", "min_pwm", "max_speed"]:
        if k in data:
            pid_config[k] = float(data[k])
    if motor and "min_pwm" in data:
        motor.set_min_pwm(pid_config["min_pwm"], pid_config["min_pwm"])
    return jsonify({"success": True, "config": pid_config})

@app.route('/api/telemetry')
def get_telemetry():
    cpu_temp = 40.0
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            cpu_temp = round(int(f.read().strip()) / 1000.0, 1)
    except Exception: pass
    
    cpu_load = 5
    try:
        cpu_load = int((os.getloadavg()[0] / (os.cpu_count() or 4)) * 100)
    except Exception: pass
    
    ram_used, ram_total = 250, 4039
    try:
        with open("/proc/meminfo", "r") as f:
            lines = f.readlines()
            tot = int(lines[0].split()[1]) // 1024
            av = int(lines[2].split()[1]) // 1024
            ram_total = tot
            ram_used = tot - av
    except Exception: pass
    
    ip = "10.68.210.164"
    try:
        ips = subprocess.run(["hostname", "-I"], capture_output=True, text=True).stdout.split()
        if ips: ip = ips[0]
    except Exception: pass
    
    is_manual = (time.time() < manual_override_until)
    mode_str = "WASD OVERRIDE" if is_manual else ("HAND FOLLOW (ACTIVE)" if pid_config["active"] else "MANUAL (STOPPED)")
    
    return jsonify({
        "ip": ip,
        "cpu_temp": cpu_temp,
        "cpu_load": min(100, cpu_load),
        "ram_used": ram_used,
        "ram_total": ram_total,
        "rgb_fps": rgb_fps,
        "depth_fps": depth_fps,
        "mode": mode_str,
        "is_manual_override": is_manual,
        "pid_active": pid_config["active"],
        "tracking": tracking_data
    })

if __name__ == '__main__':
    threading.Thread(target=rgb_worker, daemon=True).start()
    threading.Thread(target=depth_worker, daemon=True).start()
    threading.Thread(target=pid_loop, daemon=True).start()
    print("[*] RoboNav Vision Core & Index Finger Follower running on port 5000...")
    app.run(host='0.0.0.0', port=5000, threaded=True)
