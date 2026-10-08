#!/usr/bin/env python3
"""
RoboNav High-Reliability Motor Controller
Direct non-blocking serial communication with CH340 / Arduino motor driver.
"""

import serial
import time
import threading
import glob
import os

class MotorController:
    def __init__(self, baudrate=115200):
        self.baudrate = baudrate
        self.ser = None
        self.lock = threading.Lock()
        self.connected = False
        self.last_cmd_time = 0
        self.min_pwm_l = 80
        self.min_pwm_r = 80
        
        # Connect immediately
        self.connect()

        # Watchdog thread for auto-reconnect & keepalive
        self.watchdog_thread = threading.Thread(target=self._watchdog, daemon=True)
        self.watchdog_thread.start()
        
    def set_min_pwm(self, l, r):
        self.min_pwm_l = max(50, min(255, int(l)))
        self.min_pwm_r = max(50, min(255, int(r)))

    def connect(self):
        with self.lock:
            if self.ser and self.ser.is_open:
                return True
                
            # Scan serial ports
            ports = sorted(glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*'))
            if not ports:
                self.connected = False
                return False
                
            for port in ports:
                try:
                    s = serial.Serial(
                        port=port,
                        baudrate=self.baudrate,
                        timeout=0.1,
                        write_timeout=0.1
                    )
                    time.sleep(0.5) # Brief settle time
                    # Flush buffers
                    s.reset_input_buffer()
                    s.reset_output_buffer()
                    s.write(b"S\n") # Initial stop command
                    self.ser = s
                    self.connected = True
                    print(f"[✓] MotorController connected to Arduino on {port}")
                    return True
                except Exception as e:
                    print(f"[!] Serial connect error on {port}: {e}")
                    
            self.connected = False
            return False

    def send_command(self, cmd_str):
        with self.lock:
            if not self.connected or not self.ser:
                return False
            try:
                self.ser.write((cmd_str + '\n').encode('ascii'))
                self.last_cmd_time = time.time()
                return True
            except Exception as e:
                print(f"[!] MotorController write error: {e}")
                self.connected = False
                if self.ser:
                    try: self.ser.close()
                    except Exception: pass
                    self.ser = None
                return False

    def map_pwm(self, speed, min_pwm):
        if abs(speed) < 0.05:
            return 0
        mag = min(1.0, abs(speed))
        return int(min_pwm + (255 - min_pwm) * mag)

    def drive(self, direction, speed=0.5):
        """
        direction: FWD, REV, LEFT, RIGHT, STOP
        speed: 0.0 to 1.0
        """
        l_pwm = self.map_pwm(speed, self.min_pwm_l)
        r_pwm = self.map_pwm(speed, self.min_pwm_r)
        
        if direction == "FWD":
            self.send_command(f"X{-r_pwm},{-l_pwm}")
        elif direction == "REV":
            self.send_command(f"X{r_pwm},{l_pwm}")
        elif direction == "LEFT":
            self.send_command(f"X{r_pwm},{-l_pwm}")
        elif direction == "RIGHT":
            self.send_command(f"X{-r_pwm},{l_pwm}")
        else:
            self.send_command("S")

    def differential(self, left_speed, right_speed):
        """
        left_speed, right_speed: -1.0 to 1.0
        """
        l_pwm = self.map_pwm(right_speed, self.min_pwm_l) # swapped L/R
        r_pwm = self.map_pwm(left_speed, self.min_pwm_r)
        
        l_pwm = l_pwm if right_speed >= 0 else -l_pwm
        r_pwm = r_pwm if left_speed >= 0 else -r_pwm
        
        # Invert for motor orientation
        self.send_command(f"X{-l_pwm},{-r_pwm}")
        
    def stop(self):
        self.send_command("S")

    def _watchdog(self):
        while True:
            time.sleep(1.0)
            if not self.connected:
                self.connect()

# Global singleton
motor = MotorController()
