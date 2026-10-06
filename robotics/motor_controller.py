import serial
import time
import threading
import glob

class MotorController:
    def __init__(self, baudrate=115200):
        self.baudrate = baudrate
        self.ser = None
        self.lock = threading.Lock()
        self.connected = False
        self.last_cmd_time = 0
        self.min_pwm_l = 80 # default start threshold
        self.min_pwm_r = 80
        self.connect()

        # Start watchdog to keep connection alive and reconnect if lost
        self.watchdog_thread = threading.Thread(target=self._watchdog, daemon=True)
        self.watchdog_thread.start()
        
    def set_min_pwm(self, l, r):
        self.min_pwm_l = int(l)
        self.min_pwm_r = int(r)

    def connect(self):
        with self.lock:
            if self.ser and self.ser.is_open:
                return True
                
            ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
            # Assuming LiDAR is on USB0 and Arduino on USB1 based on hardware audit
            # Let's try to ping to confirm it's the Arduino
            for port in ports:
                try:
                    s = serial.Serial(port, self.baudrate, timeout=2.0)
                    time.sleep(2.0) # Wait for Arduino to reset
                    s.write(b'P\n')
                    resp = s.readline().decode().strip()
                    if resp == 'OK':
                        self.ser = s
                        self.connected = True
                        print(f"[MotorController] Connected to Arduino on {port}")
                        return True
                    s.close()
                except Exception as e:
                    pass
                    
            print("[MotorController] Failed to connect to Arduino")
            self.connected = False
            return False

    def send_command(self, cmd_str):
        with self.lock:
            if not self.connected or not self.ser:
                return False
            try:
                self.ser.write((cmd_str + '\n').encode())
                self.last_cmd_time = time.time()
                return True
            except Exception as e:
                print(f"[MotorController] Write error: {e}")
                self.connected = False
                if self.ser:
                    self.ser.close()
                    self.ser = None
                return False

    def map_pwm(self, speed, min_pwm):
        if speed == 0: return 0
        mag = min(1.0, abs(speed))
        return int(min_pwm + (255 - min_pwm) * mag)

    def drive(self, direction, speed=0):
        """
        direction: FWD, REV, LEFT, RIGHT, STOP
        speed: 0.0 to 1.0
        """
        l_pwm = self.map_pwm(speed, self.min_pwm_l)
        r_pwm = self.map_pwm(speed, self.min_pwm_r)
        
        # Taking motor swap and front/back swap into account
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
        # Calculate actual magnitude and apply deadzone mapping
        l_pwm = self.map_pwm(right_speed, self.min_pwm_l) # swapped left/right
        r_pwm = self.map_pwm(left_speed, self.min_pwm_r)
        
        l_pwm = l_pwm if right_speed >= 0 else -l_pwm
        r_pwm = r_pwm if left_speed >= 0 else -r_pwm
        
        # Negated for Front/Back swap
        self.send_command(f"X{-l_pwm},{-r_pwm}")
        
    def stop(self):
        self.send_command("S")

    def _watchdog(self):
        while True:
            time.sleep(0.2)
            if not self.connected:
                self.connect()
            else:
                # If no command sent for 0.8s, send a Ping to keep connection alive
                if time.time() - self.last_cmd_time > 0.8:
                    self.send_command("P")

# Global singleton
motor = MotorController()
