import cv2
import time
import subprocess
import threading
import numpy as np
import json
import os
import math
from flask import Flask, Response

app = Flask(__name__)

# RealSense D435 settings
DEPTH_W = 640
DEPTH_H = 480
RGB_W = 640
RGB_H = 480
FOV_H = 87.0 # Horizontal FOV in degrees

latest_rgb = None
latest_depth_colormap = None
latest_depth_raw = None
lock = threading.Lock()

def depth_worker():
    global latest_depth_colormap, latest_depth_raw
    cmd_str = f"v4l2-ctl -d /dev/video0 --set-parm=30 --set-fmt-video=width={DEPTH_W},height={DEPTH_H},pixelformat=\"Z16 \" --stream-mmap --stream-count=0 --stream-to=-"
    p = None
    frame_size = DEPTH_W * DEPTH_H * 2
    
    while True:
        try:
            if p is None or p.poll() is not None:
                p = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                
            raw_data = p.stdout.read(frame_size)
            if len(raw_data) != frame_size:
                time.sleep(0.1)
                # Force restart if getting stuck
                if p: p.kill(); p = None
                continue
                
            depth_img = np.frombuffer(raw_data, dtype=np.uint16).reshape((DEPTH_H, DEPTH_W))
        
            # Create a colormap for visualization
            # Clip max distance to 4 meters for better coloring
            depth_vis = np.clip(depth_img, 0, 4000)
            depth_vis = (depth_vis / 4000.0 * 255).astype(np.uint8)
            depth_colormap = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)
            
            # Generate 2D scan for SLAM/Obstacle Avoider
            # Take the middle 40 rows and get the minimum distance for each column
            mid_slice = depth_img[DEPTH_H//2 - 20 : DEPTH_H//2 + 20, :]
            min_depth = np.min(mid_slice, axis=0) # array of 640 points
            
            pts = []
            for x in range(DEPTH_W):
                d = min_depth[x]
                if d > 0 and d < 8000:
                    # Map x to angle (-43.5 to +43.5)
                    # Left of image is positive angle (Standard ROS / Lidar convention)
                    angle = (DEPTH_W/2 - x) * (FOV_H / DEPTH_W)
                    pts.append([round(angle, 1), int(d)])
                    
            # Write to JSON atomically for robonav_server
            scan_data = {"hz": 15.0, "points": pts}
            try:
                with open("/tmp/lidar_scan_tmp.json", "w") as f:
                    json.dump(scan_data, f)
                os.rename("/tmp/lidar_scan_tmp.json", "/tmp/lidar_scan.json")
            except:
                pass
                
            with lock:
                latest_depth_raw = depth_img.copy()
                _, latest_depth_colormap = cv2.imencode('.jpg', depth_colormap)
        except Exception as e:
            print("Depth Camera error:", e)
            time.sleep(1.0)
            if p:
                p.kill()
                p = None

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

base_options = python.BaseOptions(model_asset_path='/home/lekshmi/robotics/hand_landmarker.task')
options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
detector = vision.HandLandmarker.create_from_options(options)

def rgb_worker():
    global latest_rgb
    cmd_str = f"v4l2-ctl -d /dev/video4 --set-parm=30 --set-fmt-video=width={RGB_W},height={RGB_H},pixelformat=YUYV --stream-mmap --stream-count=0 --stream-to=-"
    p = None
    
    while True:
        try:
            if p is None or p.poll() is not None:
                p = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                
            frame_size = RGB_W * RGB_H * 2
            raw_data = p.stdout.read(frame_size)
            
            if len(raw_data) != frame_size:
                time.sleep(0.1)
                continue
                
            yuyv = np.frombuffer(raw_data, dtype=np.uint8).reshape((RGB_H, RGB_W, 2))
            rgb = cv2.cvtColor(yuyv, cv2.COLOR_YUV2BGR_YUYV)
            
            # Hand Tracking via Tasks API
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB))
            results = detector.detect(mp_image)
            
            hand_data = {"found": False}
            if results.hand_landmarks:
                hand_landmarks = results.hand_landmarks[0]
                # Landmark 9 is MIDDLE_FINGER_MCP
                lm = hand_landmarks[9]
                cx, cy = int(lm.x * RGB_W), int(lm.y * RGB_H)
                
                # Fetch depth
                dist_mm = 0
                with lock:
                    if latest_depth_raw is not None:
                        d_h, d_w = latest_depth_raw.shape
                        sx = max(0, min(d_w - 40, cx - 20))
                        sy = max(0, min(d_h - 40, cy - 20))
                        window = latest_depth_raw[sy:sy+40, sx:sx+40]
                        valid = window[(window > 50) & (window < 2000)]
                        if len(valid) > 0:
                            dist_mm = int(np.percentile(valid, 10))
                            
                if dist_mm > 0:
                    hand_data = {
                        "found": True,
                        "cx": cx,
                        "cy": cy,
                        "dist_mm": dist_mm,
                        "err_x": cx - (RGB_W / 2),
                        "err_d": dist_mm - 250
                    }
                    # Draw target and distance
                    cv2.circle(rgb, (cx, cy), 10, (0, 255, 0), -1)
                    cv2.putText(rgb, f"{dist_mm}mm", (cx+15, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            
            # Atomic write hand tracking data
            try:
                with open("/tmp/hand_pos_tmp.json", "w") as f:
                    json.dump(hand_data, f)
                os.rename("/tmp/hand_pos_tmp.json", "/tmp/hand_pos.json")
            except: pass
            
            with lock:
                _, latest_rgb = cv2.imencode('.jpg', rgb)
        except Exception as e:
            print("RGB Camera error:", e)
            time.sleep(1.0)
            if p:
                p.kill()
                p = None

def generate_stream(stream_type):
    last_frame = None
    while True:
        frame = None
        with lock:
            if stream_type == 'rgb' and latest_rgb is not None:
                frame = latest_rgb.tobytes()
            elif stream_type == 'depth' and latest_depth_colormap is not None:
                frame = latest_depth_colormap.tobytes()
                
        if frame and frame != last_frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            last_frame = frame
        
        time.sleep(0.01) # 100Hz poll, yielding only when a new frame is ready

@app.route('/video_feed')
def video_feed():
    return Response(generate_stream('rgb'), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/depth_feed')
def depth_feed():
    return Response(generate_stream('depth'), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/obstacle')
def obstacle():
    # Return obstacle distance in center box
    with lock:
        if latest_depth_raw is None:
            return json.dumps({"distance_mm": -1})
        center_box = latest_depth_raw[DEPTH_H//2 - 50:DEPTH_H//2 + 50, DEPTH_W//2 - 50:DEPTH_W//2 + 50]
        valid = center_box[center_box > 0]
        if len(valid) == 0:
            dist = -1
        else:
            dist = int(np.percentile(valid, 10)) # 10th percentile for robustness
        return json.dumps({"distance_mm": dist})

if __name__ == '__main__':
    threading.Thread(target=depth_worker, daemon=True).start()
    threading.Thread(target=rgb_worker, daemon=True).start()
    print("RealSense Bridge starting on port 5001")
    app.run(host='0.0.0.0', port=5001, threaded=True)
