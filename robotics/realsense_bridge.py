#!/usr/bin/env python3
"""
High-Performance RealSense D435 / USB Camera Bridge & Hand Tracker
Optimized for Raspberry Pi 5 with low CPU usage & high-speed MJPEG streaming.
"""

import os
import sys
import time
import glob
import json
import math
import subprocess
import threading
import numpy as np
import cv2
from flask import Flask, Response, jsonify

app = Flask(__name__)

# Target resolutions
DEPTH_W = 640
DEPTH_H = 480
RGB_W = 640
RGB_H = 480
STREAM_W = 320
STREAM_H = 240
FOV_H = 87.0

# Frame buffers & locks
frame_lock = threading.Lock()
frame_cond = threading.Condition(frame_lock)

latest_rgb_jpeg = None
latest_depth_jpeg = None
latest_depth_raw = None
rgb_frame_id = 0
depth_frame_id = 0

hand_state = {"found": False}

# MediaPipe Initialization
detector = None
try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    model_path = '/home/lekshmi/robotics/hand_landmarker.task'
    if os.path.exists(model_path):
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5
        )
        detector = vision.HandLandmarker.create_from_options(options)
        print("[✓] MediaPipe HandLandmarker initialized successfully.")
    else:
        print(f"[!] Hand landmarker model not found at {model_path}")
except Exception as e:
    print(f"[!] MediaPipe initialization warning: {e}")

def create_placeholder(text, color=(30, 40, 60)):
    img = np.full((STREAM_H, STREAM_W, 3), color, dtype=np.uint8)
    cv2.putText(img, text, (30, STREAM_H // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
    _, buf = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
    return buf.tobytes()

def find_v4l2_devices():
    depth_dev = None
    rgb_dev = None
    for dev in sorted(glob.glob('/dev/video*')):
        try:
            res = subprocess.run(['v4l2-ctl', '-d', dev, '--list-formats'], capture_output=True, text=True, timeout=1)
            if 'Z16' in res.stdout and not depth_dev:
                depth_dev = dev
            elif ('YUYV' in res.stdout or 'MJPG' in res.stdout) and not rgb_dev:
                # Exclude Pi 5 internal hardware nodes (pispbe / rpi-hevc)
                info = subprocess.run(['v4l2-ctl', '-d', dev, '-D'], capture_output=True, text=True, timeout=1)
                if 'pisp' not in info.stdout.lower() and 'hevc' not in info.stdout.lower():
                    rgb_dev = dev
        except Exception:
            pass
    return depth_dev, rgb_dev

def depth_worker():
    global latest_depth_jpeg, latest_depth_raw, depth_frame_id
    p = None
    frame_size = DEPTH_W * DEPTH_H * 2
    
    while True:
        depth_dev, _ = find_v4l2_devices()
        if not depth_dev:
            # Generate standby placeholder
            with frame_cond:
                latest_depth_jpeg = create_placeholder("Depth Cam: Searching...")
                depth_frame_id += 1
                frame_cond.notify_all()
            time.sleep(2.0)
            continue
            
        cmd_str = f"v4l2-ctl -d {depth_dev} --set-parm=30 --set-fmt-video=width={DEPTH_W},height={DEPTH_H},pixelformat=\"Z16 \" --stream-mmap --stream-count=0 --stream-to=-"
        try:
            p = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            while True:
                raw_data = p.stdout.read(frame_size)
                if len(raw_data) != frame_size:
                    time.sleep(0.05)
                    break
                    
                depth_img = np.frombuffer(raw_data, dtype=np.uint16).reshape((DEPTH_H, DEPTH_W))
                
                # Fast downsample & colormap
                small_depth = cv2.resize(depth_img, (STREAM_W, STREAM_H), interpolation=cv2.INTER_NEAREST)
                depth_vis = np.clip(small_depth, 0, 4000)
                depth_vis = (depth_vis / 4000.0 * 255).astype(np.uint8)
                depth_colormap = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)
                
                # 2D LiDAR profile generation
                mid_slice = depth_img[DEPTH_H//2 - 15 : DEPTH_H//2 + 15, :]
                min_depth = np.min(mid_slice, axis=0)
                pts = []
                for x in range(0, DEPTH_W, 4): # Sample every 4th point for speed
                    d = int(min_depth[x])
                    if 50 < d < 6000:
                        angle = (DEPTH_W/2 - x) * (FOV_H / DEPTH_W)
                        pts.append([round(angle, 1), d])
                        
                scan_data = {"hz": 15.0, "points": pts}
                try:
                    with open("/tmp/lidar_scan_tmp.json", "w") as f:
                        json.dump(scan_data, f)
                    os.rename("/tmp/lidar_scan_tmp.json", "/tmp/lidar_scan.json")
                except Exception:
                    pass
                    
                _, encoded = cv2.imencode('.jpg', depth_colormap, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
                
                with frame_cond:
                    latest_depth_raw = depth_img
                    latest_depth_jpeg = encoded.tobytes()
                    depth_frame_id += 1
                    frame_cond.notify_all()
                    
        except Exception as e:
            print("Depth worker error:", e)
            time.sleep(1.0)
        finally:
            if p:
                p.kill()
                p = None

def rgb_worker():
    global latest_rgb_jpeg, rgb_frame_id, hand_state
    p = None
    frame_size = RGB_W * RGB_H * 2
    frame_counter = 0
    
    while True:
        _, rgb_dev = find_v4l2_devices()
        if not rgb_dev:
            with frame_cond:
                latest_rgb_jpeg = create_placeholder("RGB Cam: Searching...")
                rgb_frame_id += 1
                frame_cond.notify_all()
            time.sleep(2.0)
            continue
            
        cmd_str = f"v4l2-ctl -d {rgb_dev} --set-parm=30 --set-fmt-video=width={RGB_W},height={RGB_H},pixelformat=YUYV --stream-mmap --stream-count=0 --stream-to=-"
        try:
            p = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            while True:
                raw_data = p.stdout.read(frame_size)
                if len(raw_data) != frame_size:
                    time.sleep(0.05)
                    break
                    
                yuyv = np.frombuffer(raw_data, dtype=np.uint8).reshape((RGB_H, RGB_W, 2))
                rgb = cv2.cvtColor(yuyv, cv2.COLOR_YUV2BGR_YUYV)
                
                # Run HandLandmarker every 2nd frame on downscaled image for high FPS & low CPU
                frame_counter += 1
                if detector and (frame_counter % 2 == 0):
                    small_rgb = cv2.resize(rgb, (256, 192))
                    rgb_mp = cv2.cvtColor(small_rgb, cv2.COLOR_BGR2RGB)
                    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_mp)
                    results = detector.detect(mp_img)
                    
                    found = False
                    if results.hand_landmarks:
                        lm = results.hand_landmarks[0][9] # MIDDLE_FINGER_MCP
                        cx, cy = int(lm.x * RGB_W), int(lm.y * RGB_H)
                        
                        dist_mm = 0
                        with frame_lock:
                            if latest_depth_raw is not None:
                                d_h, d_w = latest_depth_raw.shape
                                sx = max(0, min(d_w - 40, cx - 20))
                                sy = max(0, min(d_h - 40, cy - 20))
                                window = latest_depth_raw[sy:sy+40, sx:sx+40]
                                valid = window[(window > 50) & (window < 2000)]
                                if len(valid) > 0:
                                    dist_mm = int(np.percentile(valid, 10))
                                    
                        if dist_mm > 0:
                            found = True
                            hand_state = {
                                "found": True,
                                "cx": cx,
                                "cy": cy,
                                "dist_mm": dist_mm,
                                "err_x": cx - (RGB_W / 2),
                                "err_d": dist_mm - 250
                            }
                            cv2.circle(rgb, (cx, cy), 12, (0, 255, 0), -1)
                            cv2.putText(rgb, f"{dist_mm}mm", (cx + 15, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    if not found:
                        hand_state = {"found": False}
                        
                    try:
                        with open("/tmp/hand_pos_tmp.json", "w") as f:
                            json.dump(hand_state, f)
                        os.rename("/tmp/hand_pos_tmp.json", "/tmp/hand_pos.json")
                    except Exception:
                        pass
                
                # Resize for lightweight Web / HUD display
                stream_img = cv2.resize(rgb, (STREAM_W, STREAM_H))
                _, encoded = cv2.imencode('.jpg', stream_img, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
                
                with frame_cond:
                    latest_rgb_jpeg = encoded.tobytes()
                    rgb_frame_id += 1
                    frame_cond.notify_all()
                    
        except Exception as e:
            print("RGB worker error:", e)
            time.sleep(1.0)
        finally:
            if p:
                p.kill()
                p = None

def generate_stream(stream_type):
    last_id = -1
    while True:
        with frame_cond:
            if stream_type == 'rgb':
                while rgb_frame_id == last_id or latest_rgb_jpeg is None:
                    frame_cond.wait(timeout=0.2)
                    if latest_rgb_jpeg is None:
                        break
                data = latest_rgb_jpeg
                last_id = rgb_frame_id
            else:
                while depth_frame_id == last_id or latest_depth_jpeg is None:
                    frame_cond.wait(timeout=0.2)
                    if latest_depth_jpeg is None:
                        break
                data = latest_depth_jpeg
                last_id = depth_frame_id
                
        if data:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + data + b'\r\n')
        else:
            time.sleep(0.05)

@app.route('/video_feed')
def video_feed():
    return Response(generate_stream('rgb'), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/depth_feed')
def depth_feed():
    return Response(generate_stream('depth'), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/hand')
def get_hand():
    return jsonify(hand_state)

if __name__ == '__main__':
    threading.Thread(target=depth_worker, daemon=True).start()
    threading.Thread(target=rgb_worker, daemon=True).start()
    print("[*] Optimized RealSense Camera Bridge running on port 5001...")
    app.run(host='0.0.0.0', port=5001, threaded=True)
