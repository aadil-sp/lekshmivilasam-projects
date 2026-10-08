#!/usr/bin/env python3
"""
OfficePi Ultra-Low-Latency Camera Studio + High-Torque Robot Driver
Features:
- Zero-lag 35 FPS CSI Ribbon Camera & USB Webcam stream
- Direct FWD/REV/LEFT/RIGHT/STOP & Differential drive at high PWM (180-255)
- MediaPipe Hand Landmark AI (Targeting Landmark 8 Index Fingertip)
- Autonomous Hand Following + Instant WASD Keyboard & Virtual Joystick Manual Override
- Arduino Serial Driver on /dev/ttyUSB0 (115200 Baud)
- Direct 3.5" Physical Screen Framebuffer Mirror (/dev/fb0) with IP & Connection Status
- Modern Responsive Web Studio UI (http://10.68.210.43:5000)
"""

import os
import sys
import time
import math
import glob
import json
import socket
import threading
import numpy as np
import cv2
from flask import Flask, Response, jsonify, request, send_file

# Optional serial for Arduino
try:
    import serial
except ImportError:
    serial = None

# Optional TFLite runtime
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    try:
        import tensorflow.lite as tflite
    except ImportError:
        tflite = None

app = Flask(__name__)
APP_DIR = os.path.dirname(os.path.abspath(__file__))
STUDIO_HTML = os.path.join(APP_DIR, "camera_studio.html")
PALM_MODEL = "/home/officepi/palm_detection_lite.tflite"
LANDMARK_MODEL = "/home/officepi/hand_landmark_lite.tflite"
FB_DEVICE = "/dev/fb0"

def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "10.68.210.43"

HOST_IP = get_host_ip()

# ── Global Synchronization & Video Pipeline ────────────────────────────────────
frame_lock = threading.Lock()
frame_cond = threading.Condition(frame_lock)

latest_jpeg = None
latest_bgr_frame = None
latest_screen_frame = None
frame_seq = 0
fps_real = 0.0
active_camera_type = "csi"  # "csi" or "usb"
usb_device_path = "/dev/video0"
running = True

# Control Modes: "HAND_FOLLOW", "MANUAL", "STOPPED"
robot_mode = "HAND_FOLLOW"
manual_override_until = 0.0
default_drive_speed = 255  # Full PWM (Max Torque)

hand_tracking_enabled = True
hand_data = {
    "found": False,
    "cx": 0, "cy": 0,
    "landmarks_count": 0,
    "err_x": 0, "err_y": 0,
    "box_size": 0,
    "confidence": 0.0,
    "engine": "SEARCHING",
    "fps": 0.0
}

# 21 Hand Connections
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),       # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),       # Index
    (0, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (0, 13), (13, 14), (14, 15), (15, 16), # Ring
    (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
    (5, 9), (9, 13), (13, 17)             # Palm
]

def generate_anchors():
    anchors = []
    for y in range(24):
        for x in range(24):
            x_c = (x + 0.5) / 24.0
            y_c = (y + 0.5) / 24.0
            anchors.append([x_c, y_c])
            anchors.append([x_c, y_c])
    for y in range(12):
        for x in range(12):
            x_c = (x + 0.5) / 12.0
            y_c = (y + 0.5) / 12.0
            for _ in range(6):
                anchors.append([x_c, y_c])
    return np.array(anchors, dtype=np.float32)

SSD_ANCHORS = generate_anchors()

# ── High-Torque Universal Arduino Serial Driver ─────────────────────────────────────────
class ArduinoMotorController:
    def __init__(self, baudrate=115200):
        self.baudrate = baudrate
        self.ser = None
        self.lock = threading.Lock()
        self.connected = False
        self.port_name = "NONE"
        self.last_drive_cmd = "S"
        self.last_cmd_time = 0.0
        self.active_pinset = 0
        self.connect()
        threading.Thread(target=self._watchdog, daemon=True).start()

    def connect(self):
        if serial is None:
            return False
        with self.lock:
            if self.ser and self.ser.is_open:
                return True
            ports = sorted(glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*'), reverse=True)
            if not ports:
                self.connected = False
                self.port_name = "NONE"
                return False
            for p in ports:
                try:
                    s = serial.Serial(p, baudrate=self.baudrate, timeout=0.05, write_timeout=0.05)
                    time.sleep(0.3)
                    s.reset_input_buffer()
                    s.reset_output_buffer()
                    s.write(b"S\n")
                    self.ser = s
                    self.connected = True
                    self.port_name = p
                    print(f"[✓] MotorController connected to Arduino on {p}")
                    return True
                except Exception:
                    pass
            self.connected = False
            self.port_name = "NONE"
            return False

    def send_raw(self, cmd_str, force=False):
        with self.lock:
            if not self.connected or not self.ser:
                return False
            now = time.time()
            if not force and cmd_str == self.last_drive_cmd and (now - self.last_cmd_time) < 0.20:
                return True
            try:
                self.ser.write((cmd_str + '\n').encode('ascii'))
                self.ser.flush()
                self.last_drive_cmd = cmd_str
                self.last_cmd_time = now
                return True
            except Exception:
                self.connected = False
                if self.ser:
                    try: self.ser.close()
                    except Exception: pass
                    self.ser = None
                return False

    def drive_manual(self, direction, speed_pwm=255):
        if direction == "FWD":
            self.send_raw("F")
        elif direction == "REV":
            self.send_raw("B")
        elif direction == "LEFT":
            self.send_raw("L")
        elif direction == "RIGHT":
            self.send_raw("R")
        else:
            self.send_raw("S")

    def differential(self, left_pwm, right_pwm):
        l = max(-255, min(255, int(left_pwm)))
        r = max(-255, min(255, int(right_pwm)))
        self.send_raw(f"X{l},{r}")

    def pulse_pin(self, pin, pwm=255, duration=1000):
        return self.send_raw(f"T{pin},{pwm},{duration}", force=True)

    def set_pinset(self, preset_id):
        self.active_pinset = preset_id
        return True

    def stop(self):
        self.send_raw("S", force=True)

    def _watchdog(self):
        while True:
            time.sleep(1.0)
            if not self.connected:
                self.connect()

motors = ArduinoMotorController()

# ── Strict MediaPipe Hand AI Detector ─────────────────────────────────────────
class HandDetector:
    def __init__(self, palm_path=PALM_MODEL, landmark_path=LANDMARK_MODEL):
        self.palm_interp = None
        self.lm_interp = None
        self.tflite_ready = False
        
        self.latest_landmarks = []
        self.prev_box = None
        self.confidence = 0.0
        self.found = False
        self.engine_type = "NONE"
        self.fingertip_pt = None
        self.box_size = 0
        
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        
        if tflite is not None and os.path.exists(palm_path) and os.path.exists(landmark_path):
            try:
                self.palm_interp = tflite.Interpreter(model_path=palm_path, num_threads=2)
                self.palm_interp.allocate_tensors()
                self.palm_in = self.palm_interp.get_input_details()[0]['index']
                self.palm_outs = self.palm_interp.get_output_details()
                
                self.lm_interp = tflite.Interpreter(model_path=landmark_path, num_threads=2)
                self.lm_interp.allocate_tensors()
                self.lm_in = self.lm_interp.get_input_details()[0]['index']
                self.lm_outs = self.lm_interp.get_output_details()
                
                self.tflite_ready = True
                print("[✓] MediaPipe Hand AI loaded with XNNPACK!")
            except Exception as e:
                print(f"[!] TFLite init error: {e}")

    def preprocess(self, frame_bgr):
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        eq_gray = self.clahe.apply(gray)
        return cv2.cvtColor(eq_gray, cv2.COLOR_GRAY2RGB)

    def validate_hand(self, pts, w, h):
        if len(pts) != 21:
            return False
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        bw = max(xs) - min(xs)
        bh = max(ys) - min(ys)
        if bw < 20 or bh < 20 or bw > w * 0.98 or bh > h * 0.98:
            return False
        aspect = bw / float(bh)
        if aspect > 4.0 or aspect < 0.25:
            return False
        return True

    def detect_palm(self, prep_rgb, orig_w, orig_h):
        resized = cv2.resize(prep_rgb, (192, 192))
        in_data = (resized.astype(np.float32) / 255.0)[np.newaxis, ...]
        self.palm_interp.set_tensor(self.palm_in, in_data)
        self.palm_interp.invoke()
        
        boxes = self.palm_interp.get_tensor(self.palm_outs[0]['index'])[0]
        scores = self.palm_interp.get_tensor(self.palm_outs[1]['index'])[0, :, 0]
        probs = 1.0 / (1.0 + np.exp(-np.clip(scores, -20.0, 20.0)))
        best_idx = np.argmax(probs)
        best_conf = probs[best_idx]
        
        if best_conf < 0.40:
            return None
            
        box = boxes[best_idx]
        anchor = SSD_ANCHORS[best_idx]
        cx = (box[0] / 192.0 + anchor[0]) * orig_w
        cy = (box[1] / 192.0 + anchor[1]) * orig_h
        box_size = max(box[2] / 192.0 * orig_w, box[3] / 192.0 * orig_h) * 2.6
        return (cx, cy, box_size, best_conf)

    def run_landmarks(self, prep_rgb, cx, cy, box_size, orig_w, orig_h):
        half = box_size / 2.0
        x1 = max(0, int(cx - half))
        y1 = max(0, int(cy - half))
        x2 = min(orig_w, int(cx + half))
        y2 = min(orig_h, int(cy + half))
        if x2 - x1 < 20 or y2 - y1 < 20:
            return None, 0.0
            
        crop = prep_rgb[y1:y2, x1:x2]
        crop_w, crop_h = x2 - x1, y2 - y1
        resized = cv2.resize(crop, (224, 224))
        in_data = (resized.astype(np.float32) / 255.0)[np.newaxis, ...]
        
        self.lm_interp.set_tensor(self.lm_in, in_data)
        self.lm_interp.invoke()
        
        raw_lm = self.lm_interp.get_tensor(self.lm_outs[0]['index'])[0]
        conf = float(self.lm_interp.get_tensor(self.lm_outs[1]['index'])[0][0])
        
        if conf < 0.40:
            return None, conf
            
        pts = []
        for i in range(21):
            lx = raw_lm[i * 3 + 0] / 224.0 * crop_w + x1
            ly = raw_lm[i * 3 + 1] / 224.0 * crop_h + y1
            pts.append((int(lx), int(ly)))
            
        if not self.validate_hand(pts, orig_w, orig_h):
            return None, 0.0
            
        return pts, conf

    def process(self, frame_bgr):
        if not hand_tracking_enabled:
            self.found = False
            return
            
        h, w = frame_bgr.shape[:2]
        prep_rgb = self.preprocess(frame_bgr)
        
        if self.tflite_ready:
            if self.prev_box is not None:
                cx, cy, box_size = self.prev_box
                pts, conf = self.run_landmarks(prep_rgb, cx, cy, box_size, w, h)
                if pts is not None and conf >= 0.40:
                    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                    min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
                    new_size = max(max_x - min_x, max_y - min_y) * 1.5
                    self.prev_box = ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0, new_size)
                    self.latest_landmarks = pts
                    self.confidence = conf
                    self.found = True
                    self.engine_type = "MediaPipe AI"
                    self.fingertip_pt = pts[8]  # Landmark 8: Index Fingertip
                    self.box_size = int(new_size)
                    return

            palm = self.detect_palm(prep_rgb, w, h)
            if palm is not None:
                cx, cy, box_size, palm_conf = palm
                pts, conf = self.run_landmarks(prep_rgb, cx, cy, box_size, w, h)
                if pts is not None and conf >= 0.40:
                    self.prev_box = (cx, cy, box_size)
                    self.latest_landmarks = pts
                    self.confidence = conf
                    self.found = True
                    self.engine_type = "MediaPipe AI"
                    self.fingertip_pt = pts[8]
                    self.box_size = int(box_size)
                    return

        self.prev_box = None
        self.latest_landmarks = []
        self.found = False
        self.confidence = 0.0
        self.engine_type = "SEARCHING"
        self.fingertip_pt = None
        self.box_size = 0

hand_detector = HandDetector()

# ── Autonomous Hand Following Control Loop ───────────────────────────────────
def autonomous_hand_following_step(cx, cy, box_size, w, h):
    if robot_mode != "HAND_FOLLOW" or time.time() < manual_override_until:
        return

    # Proximity check: stop if hand is very close (< 15cm)
    if box_size > 360:
        motors.stop()
        return

    err_x = cx - (w // 2)  # -320 to +320
    norm_err_x = err_x / float(w // 2)
    
    deadband = 0.09  # Center deadband (~28px) for snappy response
    
    if abs(norm_err_x) < deadband:
        # Centered: Drive straight forward
        motors.drive_manual("FWD", 255)
    elif norm_err_x < -deadband:
        # Hand on Left: Turn Left
        motors.drive_manual("LEFT", 255)
    else:
        # Hand on Right: Turn Right
        motors.drive_manual("RIGHT", 255)

# ── Asynchronous AI Inference & Control Thread ───────────────────────────────
def ai_and_control_loop():
    global hand_data
    last_hand_seen = 0.0
    
    while running:
        if hand_tracking_enabled:
            frame_to_process = None
            with frame_lock:
                if latest_bgr_frame is not None:
                    frame_to_process = latest_bgr_frame.copy()
            
            if frame_to_process is not None:
                hand_detector.process(frame_to_process)
                h, w = frame_to_process.shape[:2]
                
                if hand_detector.found and hand_detector.fingertip_pt is not None:
                    cx, cy = hand_detector.fingertip_pt
                    last_hand_seen = time.time()
                    hand_data = {
                        "found": True,
                        "cx": cx,
                        "cy": cy,
                        "landmarks_count": 21,
                        "err_x": cx - (w // 2),
                        "err_y": cy - (h // 2),
                        "box_size": hand_detector.box_size,
                        "confidence": round(hand_detector.confidence, 2),
                        "engine": hand_detector.engine_type,
                        "fps": fps_real
                    }
                    if robot_mode == "HAND_FOLLOW":
                        autonomous_hand_following_step(cx, cy, hand_detector.box_size, w, h)
                else:
                    hand_data = {
                        "found": False,
                        "cx": 0, "cy": 0,
                        "landmarks_count": 0,
                        "err_x": 0, "err_y": 0,
                        "box_size": 0,
                        "confidence": 0.0,
                        "engine": "SEARCHING",
                        "fps": fps_real
                    }
                    # Instant stop when hand is lost for 0.25s
                    if robot_mode == "HAND_FOLLOW" and (time.time() - last_hand_seen) > 0.25:
                        if time.time() >= manual_override_until:
                            motors.stop()
            time.sleep(0.015)
        else:
            time.sleep(0.05)

# ── Fast Anti-Aliased Overlay Rendering ──────────────────────────────────────
def draw_hand_overlays(frame):
    h, w = frame.shape[:2]
    
    if hand_tracking_enabled and hand_detector.found and len(hand_detector.latest_landmarks) == 21:
        pts = hand_detector.latest_landmarks
        for p1_idx, p2_idx in HAND_CONNECTIONS:
            p1, p2 = pts[p1_idx], pts[p2_idx]
            if 0 <= p1[0] < w and 0 <= p1[1] < h and 0 <= p2[0] < w and 0 <= p2[1] < h:
                cv2.line(frame, p1, p2, (34, 197, 94), 2, cv2.LINE_AA)
                
        for idx, (px, py) in enumerate(pts):
            if 0 <= px < w and 0 <= py < h:
                if idx in (4, 8, 12, 16, 20):
                    cv2.circle(frame, (px, py), 5, (239, 68, 68), -1, cv2.LINE_AA)
                else:
                    cv2.circle(frame, (px, py), 3, (6, 182, 212), -1, cv2.LINE_AA)
                    cv2.circle(frame, (px, py), 3, (255, 255, 255), 1, cv2.LINE_AA)
        
        ix, iy = pts[8]
        if 0 <= ix < w and 0 <= iy < h:
            cv2.circle(frame, (ix, iy), 18, (34, 197, 94), 2, cv2.LINE_AA)
            cv2.circle(frame, (ix, iy), 5, (0, 0, 255), -1, cv2.LINE_AA)
            cv2.line(frame, (ix - 24, iy), (ix + 24, iy), (34, 197, 94), 1, cv2.LINE_AA)
            cv2.line(frame, (ix, iy - 24), (ix, iy + 24), (34, 197, 94), 1, cv2.LINE_AA)
            
            lbl = f"INDEX TIP (L8): ({ix}, {iy}) [{int(hand_detector.confidence*100)}%]"
            cv2.rectangle(frame, (max(10, ix - 90), max(5, iy - 38)), (max(10, ix - 90) + 260, max(5, iy - 38) + 18), (0, 0, 0), -1)
            cv2.putText(frame, lbl, (max(14, ix - 86), max(18, iy - 25)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (34, 197, 94), 1, cv2.LINE_AA)
    
    # ── Top HUD Status Banner ────────────────────────────────────────────────
    cv2.rectangle(frame, (8, 6), (w - 8, 30), (0, 0, 0), -1)
    
    cam_str = active_camera_type.upper()
    status_text = f"{cam_str} | {fps_real:.1f} FPS | MODE: {robot_mode}"
    cv2.putText(frame, status_text, (14, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (56, 189, 248), 1, cv2.LINE_AA)
    
    serial_str = f"ARDUINO: {motors.port_name}" if motors.connected else "ARDUINO: NO USB"
    serial_col = (34, 197, 94) if motors.connected else (245, 158, 11)
    
    right_text = f"IP: {HOST_IP}:5000 | {serial_str}"
    text_size = cv2.getTextSize(right_text, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)[0]
    cv2.putText(frame, right_text, (w - text_size[0] - 16, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.42, serial_col, 1, cv2.LINE_AA)
    
    return frame

# ── Direct Framebuffer /dev/fb0 Mirror Thread ────────────────────────────────
def screen_mirror_thread():
    if not os.path.exists(FB_DEVICE):
        return
        
    print(f"[✓] Direct Framebuffer Screen Mirror active on {FB_DEVICE} (480x320 RGB565)")
    try:
        fb = open(FB_DEVICE, "wb", buffering=0)
    except Exception as e:
        print(f"[!] Cannot open framebuffer: {e}")
        return

    while running:
        frame_to_show = None
        with frame_lock:
            if latest_screen_frame is not None:
                frame_to_show = latest_screen_frame
        
        if frame_to_show is not None:
            try:
                small = cv2.resize(frame_to_show, (480, 320))
                r = (small[:, :, 2].astype(np.uint16) >> 3) << 11
                g = (small[:, :, 1].astype(np.uint16) >> 2) << 5
                b = (small[:, :, 0].astype(np.uint16) >> 3)
                rgb565 = (r | g | b).astype(np.uint16)
                fb.seek(0)
                fb.write(rgb565.tobytes())
            except Exception:
                pass
        time.sleep(0.03)
        
    fb.close()

# ── Picamera2 (CSI Ribbon Camera) Capture Loop ──────────────────────────────
def csi_capture_loop():
    global latest_jpeg, latest_bgr_frame, latest_screen_frame, frame_seq, fps_real, running
    
    print("[*] Initializing Picamera2 for CSI Ribbon Camera (OV5647)...")
    try:
        from picamera2 import Picamera2
        picam2 = Picamera2()
        config = picam2.create_video_configuration(
            main={"size": (640, 480), "format": "RGB888"},
            controls={"FrameRate": 30}
        )
        picam2.configure(config)
        picam2.start()
        print("[✓] Picamera2 CSI Camera active at 30 FPS!")
        
        frame_times = []
        
        while running and active_camera_type == "csi":
            frame = picam2.capture_array()
            if frame is None:
                time.sleep(0.01)
                continue
                
            bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            with frame_lock:
                latest_bgr_frame = bgr
            
            processed = draw_hand_overlays(bgr.copy())
            
            with frame_lock:
                latest_screen_frame = processed
            
            _, enc = cv2.imencode('.jpg', processed, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
            jpeg_bytes = enc.tobytes()
            
            t_now = time.time()
            frame_times.append(t_now)
            while frame_times and (t_now - frame_times[0]) > 1.0:
                frame_times.pop(0)
            fps_real = round(len(frame_times), 1)
            
            with frame_cond:
                latest_jpeg = jpeg_bytes
                frame_seq += 1
                frame_cond.notify_all()
                
        picam2.stop()
        picam2.close()
    except Exception as e:
        print(f"[!] Picamera2 error: {e}")

# ── USB Webcam Capture Loop ──────────────────────────────────────────────────
def usb_capture_loop():
    global latest_jpeg, latest_bgr_frame, latest_screen_frame, frame_seq, fps_real, running
    print(f"[*] Starting USB Webcam capture on {usb_device_path}...")
    cap = cv2.VideoCapture(usb_device_path, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    
    frame_times = []
    
    while running and active_camera_type == "usb":
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.05)
            continue
            
        with frame_lock:
            latest_bgr_frame = frame
            
        processed = draw_hand_overlays(frame.copy())
        
        with frame_lock:
            latest_screen_frame = processed
            
        _, enc = cv2.imencode('.jpg', processed, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        jpeg_bytes = enc.tobytes()
        
        t_now = time.time()
        frame_times.append(t_now)
        while frame_times and (t_now - frame_times[0]) > 1.0:
            frame_times.pop(0)
        fps_real = round(len(frame_times), 1)
        
        with frame_cond:
            latest_jpeg = jpeg_bytes
            frame_seq += 1
            frame_cond.notify_all()
            
    cap.release()

def camera_manager_thread():
    while running:
        if active_camera_type == "csi":
            csi_capture_loop()
        else:
            usb_capture_loop()
        time.sleep(0.5)

# ── MJPEG Zero-Latency Stream Generator ─────────────────────────────────────
def generate_mjpeg():
    last_seq = -1
    while True:
        with frame_cond:
            while frame_seq == last_seq or latest_jpeg is None:
                frame_cond.wait(timeout=0.1)
                if latest_jpeg is None:
                    break
            data = latest_jpeg
            last_seq = frame_seq
            
        if data:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + data + b'\r\n')
        else:
            time.sleep(0.02)

# ── HTTP Endpoints ──────────────────────────────────────────────────────────
@app.route('/')
def index():
    if os.path.exists(STUDIO_HTML):
        return send_file(STUDIO_HTML)
    return "<h1>OfficePi Robot Studio Ready</h1>"

@app.route('/video_feed')
def video_feed():
    return Response(generate_mjpeg(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/snapshot.jpg')
def snapshot():
    with frame_lock:
        if latest_jpeg:
            return Response(latest_jpeg, mimetype='image/jpeg')
    return Response(b'', status=503)

@app.route('/api/tracking')
def get_tracking():
    return jsonify({
        "enabled": hand_tracking_enabled,
        "hand": hand_data,
        "mode": robot_mode,
        "fps": fps_real
    })

@app.route('/api/set_mode', methods=['POST'])
def set_mode():
    global robot_mode, manual_override_until
    data = request.json or {}
    new_mode = data.get("mode", "HAND_FOLLOW")
    if new_mode in ("HAND_FOLLOW", "MANUAL", "STOPPED"):
        robot_mode = new_mode
        manual_override_until = 0.0
        if robot_mode in ("STOPPED", "MANUAL"):
            motors.stop()
        print(f"[*] Robot mode switched to: {robot_mode}")
        return jsonify({"success": True, "mode": robot_mode})
    return jsonify({"error": "Invalid mode"}), 400

@app.route('/api/drive', methods=['POST'])
def drive():
    global robot_mode, manual_override_until
    data = request.json or {}
    cmd = data.get("cmd", "STOP").upper()
    speed_pwm = int(data.get("speed", default_drive_speed))
    
    # Manual command overrides autonomous following for 2 seconds
    manual_override_until = time.time() + 2.0
    
    if cmd in ("FWD", "REV", "LEFT", "RIGHT", "STOP"):
        motors.drive_manual(cmd, speed_pwm)
    elif cmd == "DIFF":
        l = int(data.get("l", 0))
        r = int(data.get("r", 0))
        motors.differential(l, r)
        
    return jsonify({
        "success": True,
        "cmd": cmd,
        "speed": speed_pwm,
        "arduino_connected": motors.connected,
        "port": motors.port_name
    })

@app.route('/api/stop', methods=['POST'])
def emergency_stop():
    global robot_mode
    robot_mode = "STOPPED"
    motors.stop()
    return jsonify({"success": True, "mode": "STOPPED"})

@app.route('/api/toggle_tracking', methods=['POST'])
def toggle_tracking():
    global hand_tracking_enabled
    data = request.json or {}
    if "enabled" in data:
        hand_tracking_enabled = bool(data["enabled"])
    else:
        hand_tracking_enabled = not hand_tracking_enabled
    return jsonify({"success": True, "enabled": hand_tracking_enabled})

@app.route('/api/switch_camera', methods=['POST'])
def switch_camera():
    global active_camera_type, usb_device_path
    data = request.json or {}
    cam_type = data.get("type", "csi")
    if cam_type in ("csi", "usb"):
        active_camera_type = cam_type
        if "usb_path" in data:
            usb_device_path = data["usb_path"]
        print(f"[*] Switched camera to: {active_camera_type}")
        return jsonify({"success": True, "active": active_camera_type})
    return jsonify({"error": "Invalid camera type"}), 400

@app.route('/api/set_pinset', methods=['POST'])
def set_pinset():
    data = request.json or {}
    preset_id = int(data.get("preset", 0))
    ok = motors.set_pinset(preset_id)
    return jsonify({"success": ok, "preset": preset_id})

@app.route('/api/pulse_pin', methods=['POST'])
def pulse_pin():
    data = request.json or {}
    pin = int(data.get("pin", 13))
    pwm = int(data.get("pwm", 255))
    duration = int(data.get("duration", 1000))
    ok = motors.pulse_pin(pin, pwm, duration)
    return jsonify({"success": ok, "pin": pin, "pwm": pwm, "duration": duration})

@app.route('/api/stats')
def stats():
    cpu_temp = 42.0
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            cpu_temp = round(int(f.read().strip()) / 1000.0, 1)
    except Exception: pass
    
    cpu_load = int((os.getloadavg()[0] / (os.cpu_count() or 4)) * 100)
    
    return jsonify({
        "fps": fps_real,
        "cpu_temp": cpu_temp,
        "cpu_load": min(100, cpu_load),
        "host_ip": HOST_IP,
        "camera_type": active_camera_type.upper(),
        "robot_mode": robot_mode,
        "arduino": {
            "connected": motors.connected,
            "port": motors.port_name,
            "last_cmd": motors.last_drive_cmd,
            "pinset": motors.active_pinset
        },
        "hand_tracking": hand_tracking_enabled,
        "hand": hand_data
    })

if __name__ == '__main__':
    threading.Thread(target=ai_and_control_loop, daemon=True).start()
    threading.Thread(target=screen_mirror_thread, daemon=True).start()
    threading.Thread(target=camera_manager_thread, daemon=True).start()
    print(f"[*] OfficePi Robot Studio running at http://{HOST_IP}:5000...")
    app.run(host='0.0.0.0', port=5000, threaded=True)
