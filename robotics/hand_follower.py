import time
import math
import numpy as np
import cv2
import threading

try:
    import mediapipe as mp
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
except ImportError:
    mp_hands = None

class HandFollower:
    def __init__(self, motor):
        self.motor = motor
        self.active = False
        self.lock = threading.Lock()
        self.thread = None
        
        # PID Constants - can be adjusted via UI
        self.pid = {
            "rot": {"p": 0.002, "i": 0.0, "d": 0.001},
            "lin": {"p": 0.002, "i": 0.0, "d": 0.001}
        }
        
        # State
        self.err_x_prev = 0
        self.err_d_prev = 0
        
        # Latest frames from Realsense Bridge
        self.latest_rgb = None
        self.latest_depth = None
        
        if mp_hands:
            self.hands = mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
    def update_frames(self, rgb, depth):
        with self.lock:
            if rgb is not None:
                self.latest_rgb = rgb.copy()
            if depth is not None:
                self.latest_depth = depth.copy()
                
    def set_pid(self, axis, p, i, d):
        if axis in self.pid:
            self.pid[axis] = {"p": p, "i": i, "d": d}
            
    def start(self):
        if self.active: return
        self.active = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print("[HandFollower] Started")
        
    def stop(self):
        self.active = False
        if self.thread:
            self.thread.join()
        self.motor.stop()
        print("[HandFollower] Stopped")
        
    def _loop(self):
        while self.active:
            with self.lock:
                rgb = self.latest_rgb
                depth = self.latest_depth
                
            if rgb is None or depth is None or mp_hands is None:
                time.sleep(0.05)
                continue
                
            # Run Mediapipe
            results = self.hands.process(cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB))
            
            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                # Use MCP of middle finger (landmark 9) as hand center
                lm = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
                
                h, w, _ = rgb.shape
                cx = int(lm.x * w)
                cy = int(lm.y * h)
                
                # Get depth around this pixel
                # Depth map is usually shifted, so we search a small window
                # Ensure we don't go out of bounds
                d_h, d_w = depth.shape
                sx = max(0, min(d_w - 40, cx - 20))
                sy = max(0, min(d_h - 40, cy - 20))
                window = depth[sy:sy+40, sx:sx+40]
                
                valid_depths = window[(window > 50) & (window < 2000)]
                if len(valid_depths) > 0:
                    dist_mm = np.percentile(valid_depths, 10) # 10th percentile for closest robust point
                else:
                    dist_mm = 0
                    
                if dist_mm > 0:
                    # Calculate errors
                    err_x = cx - (w / 2) # Positive if hand is to the right
                    err_d = dist_mm - 250 # Positive if hand is further than 25cm
                    
                    # Rotational PID
                    p_rot = self.pid["rot"]["p"] * err_x
                    d_rot = self.pid["rot"]["d"] * (err_x - self.err_x_prev)
                    cmd_rot = p_rot + d_rot
                    self.err_x_prev = err_x
                    
                    # Linear PID
                    p_lin = self.pid["lin"]["p"] * err_d
                    d_lin = self.pid["lin"]["d"] * (err_d - self.err_d_prev)
                    cmd_lin = p_lin + d_lin
                    self.err_d_prev = err_d
                    
                    # Cap speeds
                    cmd_rot = max(-0.5, min(0.5, cmd_rot))
                    cmd_lin = max(-0.5, min(0.5, cmd_lin))
                    
                    # Differential drive mix
                    # cmd_lin is forward, cmd_rot is right turn
                    # Left motor = lin + rot, Right motor = lin - rot
                    l_speed = cmd_lin + cmd_rot
                    r_speed = cmd_lin - cmd_rot
                    
                    # Cap mixed speeds
                    l_speed = max(-0.8, min(0.8, l_speed))
                    r_speed = max(-0.8, min(0.8, r_speed))
                    
                    # Apply deadband
                    if abs(err_d) < 20 and abs(err_x) < 30:
                        self.motor.stop()
                    else:
                        self.motor.differential(l_speed, r_speed)
                else:
                    # Hand detected but no valid depth
                    self.motor.stop()
            else:
                # No hand detected
                self.motor.stop()
                
            time.sleep(0.03) # ~30Hz control loop

