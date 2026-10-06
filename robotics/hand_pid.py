import time
import json
import os
import threading

class HandPID:
    def __init__(self, motor):
        self.motor = motor
        self.active = False
        self.thread = None
        
        self.kp_rot = 0.002
        self.kd_rot = 0.001
        self.kp_lin = 0.002
        self.kd_lin = 0.001
        
        self.prev_err_x = 0
        self.prev_err_d = 0
        
    def start(self):
        if self.active: return
        self.active = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print("[HandPID] Started")
        
    def stop(self):
        self.active = False
        if self.thread:
            self.thread.join()
        self.motor.stop()
        print("[HandPID] Stopped")
        
    def _loop(self):
        last_mtime = 0
        while self.active:
            try:
                if not os.path.exists("/tmp/hand_pos.json"):
                    time.sleep(0.05)
                    continue
                    
                mtime = os.path.getmtime("/tmp/hand_pos.json")
                if mtime == last_mtime:
                    time.sleep(0.01)
                    continue
                last_mtime = mtime
                
                with open("/tmp/hand_pos.json", "r") as f:
                    data = json.load(f)
                    
                if not data.get("found"):
                    self.motor.stop()
                    continue
                    
                err_x = data["err_x"]
                err_d = data["err_d"]
                
                # Rotational PID
                p_rot = self.kp_rot * err_x
                d_rot = self.kd_rot * (err_x - self.prev_err_x)
                cmd_rot = p_rot + d_rot
                self.prev_err_x = err_x
                
                # Linear PID
                p_lin = self.kp_lin * err_d
                d_lin = self.kd_lin * (err_d - self.prev_err_d)
                cmd_lin = p_lin + d_lin
                self.prev_err_d = err_d
                
                # Mix
                l_speed = cmd_lin + cmd_rot
                r_speed = cmd_lin - cmd_rot
                
                # Deadband
                if abs(err_d) < 30 and abs(err_x) < 40:
                    self.motor.stop()
                else:
                    self.motor.differential(
                        max(-0.6, min(0.6, l_speed)),
                        max(-0.6, min(0.6, r_speed))
                    )
            except Exception as e:
                pass
            time.sleep(0.03)
