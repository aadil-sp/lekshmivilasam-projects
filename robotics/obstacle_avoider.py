import time
import threading
from motor_controller import motor

class ObstacleAvoider:
    def __init__(self):
        self.active = False
        self.thread = None
        self.latest_scan = []
        self.lock = threading.Lock()
        
    def update_scan(self, points):
        """Called by the main loop when new LiDAR data arrives."""
        with self.lock:
            self.latest_scan = points

    def start(self):
        if self.active:
            return
        self.active = True
        self.thread = threading.Thread(target=self._avoider_loop, daemon=True)
        self.thread.start()
        print("[ObstacleAvoider] Started")

    def stop(self):
        self.active = False
        if self.thread:
            self.thread.join(timeout=1.0)
        motor.stop()
        print("[ObstacleAvoider] Stopped")

    def _avoider_loop(self):
        while self.active:
            with self.lock:
                scan = list(self.latest_scan)
                
            if not scan:
                time.sleep(0.05)
                continue
                
            # Segmentation: Front is 0 +/- 20 degrees
            # points are [angle_deg, dist_mm]
            front_min = 9999
            left_min = 9999
            right_min = 9999
            
            for angle, dist in scan:
                if dist < 100: continue # ignore noise too close
                
                # Normalize angle to -180 to 180
                a = angle
                if a > 180: a -= 360
                
                if -25 <= a <= 25:
                    front_min = min(front_min, dist)
                elif 25 < a <= 75:
                    right_min = min(right_min, dist)
                elif -75 <= a < -25:
                    left_min = min(left_min, dist)
                    
            # Logic based on mode
            mode = getattr(self, "current_mode", "OBSTACLE")
            
            if mode == "FOLLOW":
                # Follow at 30cm (300mm)
                # Keep distance between 250 and 350
                if front_min < 250:
                    motor.drive("BWD", 0.4) # Too close, reverse
                elif front_min > 350 and front_min < 1000:
                    # Move towards the object
                    motor.drive("FWD", 0.4)
                else:
                    # Within target distance, or object lost
                    motor.stop()
            else:
                # Basic OBSTACLE avoidance logic
                if front_min < 350:
                    # Blocked! Turn to the more open side
                    if left_min > right_min:
                        motor.differential(-0.4, 0.4) # Turn left
                    else:
                        motor.differential(0.4, -0.4) # Turn right
                elif front_min < 600:
                    # Obstacle approaching, slow down and slightly curve
                    base_speed = 0.3
                    if left_min > right_min:
                        motor.differential(base_speed - 0.15, base_speed + 0.15)
                    else:
                        motor.differential(base_speed + 0.15, base_speed - 0.15)
                else:
                    # Clear path, go forward
                    motor.drive("FWD", 0.5)
                    
            time.sleep(0.05) # 20Hz decision loop

avoider = ObstacleAvoider()
