import numpy as np
import cv2
import threading
import math
import time
import base64
import json

class SLAMEngine:
    def __init__(self, map_size_px=400, resolution_mm=50):
        # 400x400 map at 50mm (5cm) per pixel = 20x20 meters
        self.map_size = map_size_px
        self.resolution = resolution_mm
        
        # Grid: 127 = unknown, 255 = free, 0 = occupied
        self.grid = np.full((self.map_size, self.map_size), 127, dtype=np.uint8)
        
        # Robot pose: x_mm, y_mm, theta_rad
        self.pose = [self.map_size * self.resolution / 2, 
                     self.map_size * self.resolution / 2, 
                     0.0]
        
        self.lock = threading.Lock()
        
        # Dead reckoning state
        self.last_update_time = time.time()
        self.cmd_v = 0.0 # linear mm/s
        self.cmd_w = 0.0 # angular rad/s
        
    def set_velocity_command(self, v_m_s, w_rad_s):
        with self.lock:
            self.cmd_v = v_m_s * 1000.0 # convert to mm/s
            self.cmd_w = w_rad_s

    def update(self, scan_points):
        """
        scan_points: list of [angle_deg, dist_mm]
        """
        now = time.time()
        dt = now - self.last_update_time
        self.last_update_time = now
        
        with self.lock:
            # 1. Odometry update (dead reckoning)
            self.pose[2] += self.cmd_w * dt
            # normalize theta
            self.pose[2] = (self.pose[2] + math.pi) % (2 * math.pi) - math.pi
            
            self.pose[0] += self.cmd_v * math.cos(self.pose[2]) * dt
            self.pose[1] += self.cmd_v * math.sin(self.pose[2]) * dt
            
            # Robot grid coordinates
            rx = int(self.pose[0] / self.resolution)
            ry = int(self.pose[1] / self.resolution)
            
            if not (0 <= rx < self.map_size and 0 <= ry < self.map_size):
                return # out of bounds
                
            # 2. Map update via raycasting
            # To speed up, we don't raycast every point every time in pure Python, 
            # we'll use OpenCV's line drawing which is vectorized in C++
            
            free_mask = np.zeros_like(self.grid)
            occ_mask = np.zeros_like(self.grid)
            
            for angle_deg, dist_mm in scan_points:
                if dist_mm < 100 or dist_mm > 8000:
                    continue # out of range
                
                # Convert scan polar to map cartesian
                # Angle 0 is front, positive clockwise in our lidar setup
                angle_rad = math.radians(angle_deg) + self.pose[2]
                
                end_x = self.pose[0] + dist_mm * math.cos(angle_rad)
                end_y = self.pose[1] + dist_mm * math.sin(angle_rad)
                
                ex = int(end_x / self.resolution)
                ey = int(end_y / self.resolution)
                
                # Clip to map
                ex = max(0, min(self.map_size - 1, ex))
                ey = max(0, min(self.map_size - 1, ey))
                
                # Draw free space ray
                cv2.line(free_mask, (rx, ry), (ex, ey), 1, 1)
                
                # Mark endpoint as occupied if within bounds and not max range
                if dist_mm < 7900:
                    occ_mask[ey, ex] = 1 # note cv2 image indexing is y,x
                    
            # Apply masks
            # For free space, increase brightness towards 255
            self.grid = np.where(free_mask == 1, np.minimum(self.grid.astype(np.uint16) + 10, 255).astype(np.uint8), self.grid)
            # For occupied space, decrease towards 0
            self.grid = np.where(occ_mask == 1, np.maximum(self.grid.astype(np.int16) - 50, 0).astype(np.uint8), self.grid)

    def get_map_png_b64(self):
        with self.lock:
            # Convert grid to RGB for display
            display_grid = cv2.cvtColor(self.grid, cv2.COLOR_GRAY2RGB)
            
            # Draw robot
            rx = int(self.pose[0] / self.resolution)
            ry = int(self.pose[1] / self.resolution)
            if 0 <= rx < self.map_size and 0 <= ry < self.map_size:
                cv2.circle(display_grid, (rx, ry), 2, (0, 0, 255), -1)
                # Draw heading
                hx = int(rx + 5 * math.cos(self.pose[2]))
                hy = int(ry + 5 * math.sin(self.pose[2]))
                cv2.line(display_grid, (rx, ry), (hx, hy), (0, 255, 0), 1)
            
            # Encode to PNG
            _, buffer = cv2.imencode('.png', display_grid)
            return base64.b64encode(buffer).decode('utf-8')
            
    def get_pose(self):
        with self.lock:
            return {"x": self.pose[0], "y": self.pose[1], "theta_deg": math.degrees(self.pose[2])}
            
    def set_goal(self, gx_mm, gy_mm):
        self.goal = (gx_mm, gy_mm)
        print(f"[SLAM] Goal set to {gx_mm}, {gy_mm}")
        
    def navigate(self, motor):
        if not hasattr(self, 'goal') or self.goal is None:
            return
            
        with self.lock:
            px, py, pth = self.pose
            
        gx, gy = self.goal
        dx = gx - px
        dy = gy - py
        dist = math.hypot(dx, dy)
        
        if dist < 150: # Reached goal (within 15cm)
            motor.stop()
            self.goal = None
            print("[SLAM] Goal reached!")
            return
            
        target_heading = math.atan2(dy, dx)
        heading_error = target_heading - pth
        
        # Normalize to -pi to pi
        heading_error = (heading_error + math.pi) % (2 * math.pi) - math.pi
        
        # Pure pursuit controller
        if abs(heading_error) > 0.5: # Needs to turn (approx > 30 degrees)
            speed = 0.4
            if heading_error > 0:
                motor.differential(-speed, speed) # Turn Left
            else:
                motor.differential(speed, -speed) # Turn Right
        else: # Face roughly correct, move forward and slightly adjust
            # Cap the adjustment
            adj = max(-0.2, min(0.2, heading_error * 0.5))
            motor.differential(0.5 - adj, 0.5 + adj)
            
    def clear_map(self):
        with self.lock:
            self.grid.fill(127)
            self.pose = [self.map_size * self.resolution / 2, self.map_size * self.resolution / 2, 0.0]

slam = SLAMEngine()
