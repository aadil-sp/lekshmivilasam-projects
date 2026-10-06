#!/usr/bin/env python3
"""
========================================================================================
DOBOT MAGICIAN LITE - PRO WEB GUI CONTROLLER & CALIBRATION STUDIO
- Reliable Suction & Gripper Waypoint Execution (with dwell timing & dual queuing)
- Native Hardware JOG Engine (SetJOGCmd ID: 73)
- Discrete Step Increments (1mm, 5mm, 10mm, 20mm, 50mm)
- Auto Gripper / Suction State & Wrist Angle Capture on [SPACE]
- Revert / Return Movement (Play in Reverse with Inverted Grab / Drop)
- Cycle Loop Pick & Return (Forward <-> Return Continuous Looping)
- 1-Click Export to Dobot Magic Box Storage
========================================================================================
"""

import os
import sys
import time
import struct
import json
import threading
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import serial


PORT = 8080
SERIAL_DEVICE = "/dev/cu.usbmodem549A30D515392"
BAUDRATE = 115200

def find_magic_box_mount():
    for name in ["/Volumes/NO NAME", "/Volumes/NO NAME 1"]:
        if os.path.exists(name) and os.path.exists(os.path.join(name, "System")):
            return name
    return "/Volumes/NO NAME"

# =========================================================================
# DOBOT PROTOCOL DRIVER
# =========================================================================
class DobotProtocolEngine:
    def __init__(self, port=SERIAL_DEVICE, baudrate=BAUDRATE):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.lock = threading.Lock()
        
        self.is_connected = False
        self.current_x = 240.0
        self.current_y = 0.0
        self.current_z = 60.0
        self.current_r = 0.0
        self.j1 = 0.0
        self.j2 = 0.0
        self.j3 = 0.0
        self.j4 = 0.0
        
        self.suction_state = False
        self.gripper_state = False
        self.speed_ratio = 50.0
        self.active_jog_cmd = 0
        
        # Keypoints & Playback
        self.keypoints = []
        self.is_playing = False
        self.active_step = -1
        self.playback_mode = "idle"

    def _build_packet(self, cmd_id, ctrl, params=b''):
        length = len(params) + 2
        payload = bytes([cmd_id, ctrl]) + params
        checksum = (256 - (sum(payload) % 256)) % 256
        return bytes([0xAA, 0xAA, length]) + payload + bytes([checksum])

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.04)
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            self.is_connected = True
            print(f"[OK] Connected to Dobot on {self.port}")

            # Initialize Controller
            self.clear_alarms()
            self.start_queue()
            self.apply_safe_speed_params(50.0)
            
            # Start background telemetry poller
            threading.Thread(target=self._poll_telemetry, daemon=True).start()
            return True
        except Exception as e:
            print(f"[WARN] Connection failed: {e}")
            self.is_connected = False
            return False

    def close(self):
        self.is_playing = False
        self.stop_jog()
        if self.ser and self.ser.is_open:
            try:
                self.set_suction(False)
                self.set_gripper(False)
                self.ser.close()
            except Exception:
                pass
        self.is_connected = False

    def clear_alarms(self):
        with self.lock:
            if self.ser and self.ser.is_open:
                self.ser.write(self._build_packet(20, 1))

    def start_queue(self):
        with self.lock:
            if self.ser and self.ser.is_open:
                self.ser.write(self._build_packet(245, 1)) # Clear Queue
                time.sleep(0.01)
                self.ser.write(self._build_packet(240, 1)) # Start Queue

    def home_arm(self):
        with self.lock:
            if self.ser and self.ser.is_open:
                self.clear_alarms()
                self.start_queue()
                self.ser.write(self._build_packet(31, 3, struct.pack('<I', 0)))

    def apply_safe_speed_params(self, speed_percent):
        self.speed_ratio = max(20.0, min(85.0, float(speed_percent)))
        with self.lock:
            if self.ser and self.ser.is_open:
                v = 50.0 + (self.speed_ratio * 1.5)
                a = 50.0 + (self.speed_ratio * 1.5)
                self.ser.write(self._build_packet(71, 1, struct.pack('<8f', v, v, v, v, a, a, a, a)))
                self.ser.write(self._build_packet(72, 1, struct.pack('<2f', self.speed_ratio, self.speed_ratio)))
                self.ser.write(self._build_packet(80, 1, struct.pack('<8f', v, v, v, v, a, a, a, a)))
                self.ser.write(self._build_packet(81, 1, struct.pack('<2f', self.speed_ratio, self.speed_ratio)))

    def _poll_telemetry(self):
        buf = bytearray()
        while self.is_connected:
            try:
                with self.lock:
                    if self.ser and self.ser.is_open:
                        self.ser.write(self._build_packet(10, 0))
                        time.sleep(0.015)
                        if self.ser.in_waiting:
                            buf += self.ser.read(self.ser.in_waiting)

                while len(buf) >= 4:
                    if buf[0] == 0xAA and buf[1] == 0xAA:
                        pkt_len = buf[2]
                        total_len = pkt_len + 4
                        if len(buf) >= total_len:
                            pkt = bytes(buf[:total_len])
                            del buf[:total_len]
                            cmd_id = pkt[3]
                            if cmd_id == 10 and len(pkt) >= 37:
                                payload = pkt[5:37]
                                if len(payload) == 32:
                                    p = struct.unpack('<8f', payload)
                                    if 50.0 <= p[0] <= 500.0 and -400.0 <= p[1] <= 400.0:
                                        self.current_x, self.current_y, self.current_z, self.current_r = p[0], p[1], p[2], p[3]
                                        self.j1, self.j2, self.j3, self.j4 = p[4], p[5], p[6], p[7]
                        else:
                            break
                    else:
                        del buf[0]
            except Exception:
                pass
            time.sleep(0.05)

    def start_jog(self, axis_cmd, is_joint=False):
        self.active_jog_cmd = int(axis_cmd)
        is_j = 1 if is_joint else 0
        with self.lock:
            if self.ser and self.ser.is_open:
                self.ser.write(self._build_packet(73, 1, bytes([is_j, self.active_jog_cmd])))

    def stop_jog(self):
        self.active_jog_cmd = 0
        with self.lock:
            if self.ser and self.ser.is_open:
                self.ser.write(self._build_packet(73, 1, bytes([0, 0])))

    def step_move(self, dx=0.0, dy=0.0, dz=0.0, dr=0.0):
        with self.lock:
            if self.ser and self.ser.is_open:
                target_x = max(140.0, min(340.0, self.current_x + float(dx)))
                target_y = max(-280.0, min(280.0, self.current_y + float(dy)))
                target_z = max(-45.0, min(150.0, self.current_z + float(dz)))
                target_r = max(-140.0, min(140.0, self.current_r + float(dr)))
                
                ptp_params = struct.pack('<B4f', 1, target_x, target_y, target_z, target_r)
                self.ser.write(self._build_packet(84, 3, ptp_params))
                
                self.current_x = target_x
                self.current_y = target_y
                self.current_z = target_z
                self.current_r = target_r

    def move_ptp(self, mode, x, y, z, r=0.0):
        with self.lock:
            if self.ser and self.ser.is_open:
                target_x = max(140.0, min(340.0, float(x)))
                target_y = max(-280.0, min(280.0, float(y)))
                target_z = max(-45.0, min(150.0, float(z)))
                target_r = max(-140.0, min(140.0, float(r)))
                ptp_params = struct.pack('<B4f', int(mode), target_x, target_y, target_z, target_r)
                self.ser.write(self._build_packet(84, 3, ptp_params))

    def set_suction(self, enable: bool):
        self.suction_state = bool(enable)
        val = 1 if enable else 0
        with self.lock:
            if self.ser and self.ser.is_open:
                # Send immediate and queued commands for guaranteed trigger
                self.ser.write(self._build_packet(62, 1, bytes([1, val, 0])))
                time.sleep(0.01)
                self.ser.write(self._build_packet(62, 3, bytes([1, val, 1])))

    def set_gripper(self, enable: bool):
        self.gripper_state = bool(enable)
        val = 1 if enable else 0
        with self.lock:
            if self.ser and self.ser.is_open:
                self.ser.write(self._build_packet(63, 1, bytes([1, val, 0])))
                time.sleep(0.01)
                self.ser.write(self._build_packet(63, 3, bytes([1, val, 1])))

    def add_keypoint(self, action="AUTO", mode=0, delay=500):
        """Auto-records pose, wrist rotation, and active gripper/suction state"""
        final_action = action
        if action == "AUTO":
            if self.suction_state:
                final_action = "SUCTION_ON"
            elif self.gripper_state:
                final_action = "GRIP_ON"
            else:
                last_actions = [k["action"] for k in self.keypoints if k["action"] != "NONE"]
                if last_actions and last_actions[-1] == "SUCTION_ON":
                    final_action = "SUCTION_OFF"
                elif last_actions and last_actions[-1] == "GRIP_ON":
                    final_action = "GRIP_OFF"
                else:
                    final_action = "NONE"

        kp = {
            "id": int(time.time() * 1000),
            "x": round(self.current_x, 1),
            "y": round(self.current_y, 1),
            "z": round(self.current_z, 1),
            "r": round(self.current_r, 1),
            "suction": self.suction_state,
            "gripper": self.gripper_state,
            "mode": int(mode),
            "action": str(final_action),
            "delay": int(delay)
        }
        self.keypoints.append(kp)
        return kp

    def update_keypoint_action(self, index, action):
        if 0 <= index < len(self.keypoints):
            self.keypoints[index]["action"] = str(action)
            return True
        return False

    def delete_keypoint(self, index):
        if 0 <= index < len(self.keypoints):
            self.keypoints.pop(index)

    def clear_keypoints(self):
        self.keypoints.clear()

    def get_inverted_sequence(self, points):
        """
        Generates return trajectory:
        Reverses coordinate positions while preserving action sequence (Pick at Loc 2 -> Place at Loc 1)
        """
        if not points:
            return []
        rev_coords = list(reversed(points))
        actions = [p["action"] for p in points]
        delays = [p["delay"] for p in points]
        
        rev = []
        for i, p in enumerate(rev_coords):
            rev.append({
                "id": int(time.time() * 1000) + i,
                "x": p["x"],
                "y": p["y"],
                "z": p["z"],
                "r": p["r"],
                "mode": p["mode"],
                "action": actions[i],
                "delay": delays[i]
            })
        return rev

    def invert_and_append_return(self):
        if not self.keypoints:
            return False, "No keypoints to invert"
        return_pts = self.get_inverted_sequence(self.keypoints)
        self.keypoints.extend(return_pts)
        return True, f"Appended {len(return_pts)} return waypoints to sequence"

    def run_playback(self, mode="forward", loop=False):
        if self.is_playing:
            return False, "Playback already in progress"
        if not self.keypoints:
            return False, "No waypoints recorded yet. Capture waypoints with [SPACE] before playing."
        
        self.playback_mode = mode
        threading.Thread(target=self._playback_worker, args=(mode, loop), daemon=True).start()
        return True, f"Started {mode} playback"

    def _execute_point_list(self, pts):
        for idx, kp in enumerate(pts):
            if not self.is_playing:
                break
            self.active_step = idx
            
            # Send movement
            self.move_ptp(kp["mode"], kp["x"], kp["y"], kp["z"], kp["r"])
            time.sleep(1.2) # Allow transit

            # Trigger tool action
            act = str(kp.get("action", "NONE")).upper()
            if "SUCTION_ON" in act:
                self.set_suction(True)
                time.sleep(0.6) # Sucking dwell
            elif "SUCTION_OFF" in act:
                self.set_suction(False)
                time.sleep(0.4) # Release dwell
            elif "GRIP_ON" in act:
                self.set_gripper(True)
                time.sleep(0.6)
            elif "GRIP_OFF" in act:
                self.set_gripper(False)
                time.sleep(0.4)

            delay_ms = kp.get("delay", 500)
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

    def _playback_worker(self, mode, loop):
        self.is_playing = True
        try:
            self.clear_alarms()
            self.start_queue()
            self.apply_safe_speed_params(self.speed_ratio)

            while self.is_playing and self.is_connected:
                if mode == "forward":
                    self._execute_point_list(self.keypoints)
                    if not loop or not self.is_playing:
                        break
                elif mode == "reverse":
                    rev_pts = self.get_inverted_sequence(self.keypoints)
                    self._execute_point_list(rev_pts)
                    if not loop or not self.is_playing:
                        break
                elif mode == "cycle":
                    self._execute_point_list(self.keypoints)
                    if not self.is_playing:
                        break
                    time.sleep(0.5)
                    rev_pts = self.get_inverted_sequence(self.keypoints)
                    self._execute_point_list(rev_pts)
                    if not loop or not self.is_playing:
                        break
                time.sleep(0.5)

            # Return to safe standby
            self.move_ptp(1, 240.0, 0.0, 60.0, 0.0)
            time.sleep(1.2)
        finally:
            self.is_playing = False
            self.active_step = -1
            self.playback_mode = "idle"
            self.clear_alarms()
            self.start_queue()
            self.apply_safe_speed_params(self.speed_ratio)

    def stop_playback(self):
        self.is_playing = False
        self.playback_mode = "idle"
        self.clear_alarms()
        self.start_queue()
        self.apply_safe_speed_params(self.speed_ratio)

    def export_magic_box(self, filename="DeskPickAndPlace.py"):
        mount = find_magic_box_mount()
        if not os.path.exists(mount):
            return False, f"Magic Box flash drive not mounted at {mount}"

        pb_lines = ["# Dobot Playback Waypoints", "# Format: [X, Y, Z, R, Mode, EffectorType, EffectorState, DelayMs]"]
        for kp in self.keypoints:
            eff_type = 2 if "SUCTION" in kp["action"] else (1 if "GRIP" in kp["action"] else 0)
            eff_state = 1 if kp["action"] in ["SUCTION_ON", "GRIP_ON"] else 0
            pb_lines.append(f"[{kp['x']}, {kp['y']}, {kp['z']}, {kp['r']}, {kp['mode']}, {eff_type}, {eff_state}, {kp['delay']}]")

        os.makedirs(os.path.join(mount, "Playback"), exist_ok=True)
        pb_path = os.path.join(mount, "Playback", "Playback.txt")
        with open(pb_path, "w") as f:
            f.write("\n".join(pb_lines) + "\n")

        py_code = f"""#devType: ML
import dType
api = 0
dType.SetQueuedCmdClear(api)
dType.SetQueuedCmdStopExec(api)
dType.SetQueuedCmdStartExec(api)
dType.SetArmSpeedRatio(api, 1, {int(self.speed_ratio)}, 1)
dType.SetPTPJumpParams(api, 25.0, 100.0, 1)
dType.SetHOMECmd(api, 0, 1)
"""
        for kp in self.keypoints:
            py_code += f"dType.SetPTPCmdEx(api, {kp['mode']}, {kp['x']}, {kp['y']}, {kp['z']}, {kp['r']}, 1)\n"
            if kp["action"] == "SUCTION_ON":
                py_code += "dType.SetEndEffectorSuctionCupEx(api, 1, 1, 1)\n"
            elif kp["action"] == "SUCTION_OFF":
                py_code += "dType.SetEndEffectorSuctionCupEx(api, 0, 0, 1)\n"
            elif kp["action"] == "GRIP_ON":
                py_code += "dType.SetEndEffectorGripperEx(api, 1, 1)\n"
            elif kp["action"] == "GRIP_OFF":
                py_code += "dType.SetEndEffectorGripperEx(api, 1, 0)\n"
            if kp["delay"] > 0:
                py_code += f"dType.dSleep({kp['delay']})\n"

        py_code += "dType.SetPTPCmdEx(api, 1, 240.0, 0.0, 50.0, 0.0, 1)\ndType.RestartMagicBox(api)\n"

        os.makedirs(os.path.join(mount, "Script"), exist_ok=True)
        script_path = os.path.join(mount, "Script", filename)
        with open(script_path, "w") as f:
            f.write(py_code)

        local_dir = os.path.expanduser("/Users/aadilsp/Desktop/Antigravity/Lekshmivilasam/dobot/src/saved_routines")
        os.makedirs(local_dir, exist_ok=True)
        with open(os.path.join(local_dir, filename), "w") as f:
            f.write(py_code)

        return True, f"Saved to {pb_path} & {script_path}"

dobot = DobotProtocolEngine()

# =========================================================================
# HTTP REST API SERVER
# =========================================================================
class GUIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))

        elif path == "/api/status":
            data = {
                "connected": dobot.is_connected,
                "x": round(dobot.current_x, 1),
                "y": round(dobot.current_y, 1),
                "z": round(dobot.current_z, 1),
                "r": round(dobot.current_r, 1),
                "j1": round(dobot.j1, 1),
                "j2": round(dobot.j2, 1),
                "j3": round(dobot.j3, 1),
                "j4": round(dobot.j4, 1),
                "speed": dobot.speed_ratio,
                "suction": dobot.suction_state,
                "gripper": dobot.gripper_state,
                "keypoints": dobot.keypoints,
                "is_playing": dobot.is_playing,
                "active_step": dobot.active_step,
                "playback_mode": dobot.playback_mode,
                "active_jog": dobot.active_jog_cmd
            }
            self.send_json(data)

        elif path == "/api/jog_start":
            qs = parse_qs(parsed.query)
            cmd = int(qs.get("cmd", [0])[0])
            is_joint = qs.get("is_joint", ["0"])[0] == "1"
            dobot.start_jog(cmd, is_joint)
            self.send_json({"ok": True, "cmd": cmd})

        elif path == "/api/jog_stop":
            dobot.stop_jog()
            self.send_json({"ok": True})

        elif path == "/api/step":
            qs = parse_qs(parsed.query)
            dx = float(qs.get("dx", [0])[0])
            dy = float(qs.get("dy", [0])[0])
            dz = float(qs.get("dz", [0])[0])
            dr = float(qs.get("dr", [0])[0])
            dobot.step_move(dx, dy, dz, dr)
            self.send_json({"ok": True})

        elif path == "/api/set_speed":
            qs = parse_qs(parsed.query)
            spd = float(qs.get("speed", [50])[0])
            dobot.apply_safe_speed_params(spd)
            self.send_json({"ok": True, "speed": dobot.speed_ratio})

        elif path == "/api/suction":
            qs = parse_qs(parsed.query)
            enable = qs.get("enable", ["0"])[0] == "1"
            dobot.set_suction(enable)
            self.send_json({"ok": True, "suction": dobot.suction_state})

        elif path == "/api/gripper":
            qs = parse_qs(parsed.query)
            enable = qs.get("enable", ["0"])[0] == "1"
            dobot.set_gripper(enable)
            self.send_json({"ok": True, "gripper": dobot.gripper_state})

        elif path == "/api/home":
            dobot.home_arm()
            self.send_json({"ok": True})

        elif path == "/api/clear_alarms":
            dobot.clear_alarms()
            dobot.start_queue()
            dobot.apply_safe_speed_params(50.0)
            self.send_json({"ok": True})

        elif path == "/api/add_keypoint":
            qs = parse_qs(parsed.query)
            action = qs.get("action", ["AUTO"])[0]
            mode = int(qs.get("mode", [0])[0])
            delay = int(qs.get("delay", [500])[0])
            kp = dobot.add_keypoint(action, mode, delay)
            self.send_json({"ok": True, "keypoint": kp})

        elif path == "/api/update_action":
            qs = parse_qs(parsed.query)
            idx = int(qs.get("index", [-1])[0])
            act = qs.get("action", ["NONE"])[0]
            ok = dobot.update_keypoint_action(idx, act)
            self.send_json({"ok": ok})

        elif path == "/api/delete_keypoint":
            qs = parse_qs(parsed.query)
            idx = int(qs.get("index", [-1])[0])
            dobot.delete_keypoint(idx)
            self.send_json({"ok": True})

        elif path == "/api/clear_keypoints":
            dobot.clear_keypoints()
            self.send_json({"ok": True})

        elif path == "/api/invert_append":
            ok, msg = dobot.invert_and_append_return()
            self.send_json({"ok": ok, "msg": msg})

        elif path == "/api/playback":
            qs = parse_qs(parsed.query)
            mode = qs.get("mode", ["forward"])[0]
            loop = qs.get("loop", ["0"])[0] == "1"
            ok, msg = dobot.run_playback(mode=mode, loop=loop)
            self.send_json({"ok": ok, "msg": msg})

        elif path == "/api/stop":
            dobot.stop_playback()
            self.send_json({"ok": True})

        elif path == "/api/export":
            ok, msg = dobot.export_magic_box("DeskPickAndPlace.py")
            self.send_json({"ok": ok, "msg": msg})

        else:
            self.send_response(404)
            self.end_headers()

    def send_json(self, data):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

# =========================================================================
# WEB GUI DASHBOARD (PICK, PLACE & INVERTED RETURN STUDIO)
# =========================================================================
HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dobot Magician Lite - Pro Pick & Place Studio</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Inter:wght@400;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .mono { font-family: 'JetBrains Mono', monospace; }
    
    .keycap-btn {
      background: linear-gradient(180deg, #334155 0%, #1e293b 100%);
      box-shadow: 0 4px 0 #0f172a, 0 6px 12px rgba(0,0,0,0.5), inset 0 1px 1px rgba(255,255,255,0.2);
      transition: all 0.05s ease;
      touch-action: none;
      user-select: none;
    }
    .keycap-btn:active, .keycap-btn.active-jog {
      transform: translateY(3px);
      box-shadow: 0 1px 0 #0f172a, 0 2px 4px rgba(0,0,0,0.4);
      background: linear-gradient(180deg, #0284c7 0%, #0369a1 100%) !important;
      color: #ffffff !important;
      border-color: #38bdf8 !important;
    }
    .badge-key {
      display: inline-block;
      padding: 1px 5px;
      border-radius: 4px;
      background: #0f172a;
      border: 1px solid #334155;
      font-family: 'JetBrains Mono', monospace;
      font-weight: bold;
      color: #38bdf8;
    }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen p-4 md:p-6 select-none">

  <div class="max-w-7xl mx-auto flex flex-col gap-6">
    
    <!-- Top Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-4">
      <div class="flex items-center gap-3">
        <div class="w-11 h-11 rounded-2xl bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400 font-bold text-2xl shadow-lg shadow-cyan-950/40">
          🦾
        </div>
        <div>
          <h1 class="text-xl md:text-2xl font-black text-white tracking-tight flex items-center gap-2">
            Dobot Magician Lite <span class="text-xs uppercase px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold tracking-wider">Pick & Return Studio</span>
          </h1>
          <p class="text-xs text-slate-400">Step & Hold Jogging &bull; Auto Gripper/Suction State on [SPACE] &bull; Inverted Return Playback</p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <button onclick="clearAlarms()" class="px-3.5 py-2 rounded-xl bg-amber-500/10 border border-amber-500/40 text-amber-300 hover:bg-amber-500/20 text-xs font-bold transition flex items-center gap-1.5 active:scale-95">
          <span>⚠️</span> Clear Alarms & Reset
        </button>
        <button onclick="sendHome()" class="px-4 py-2 rounded-xl bg-cyan-600 border border-cyan-500 hover:bg-cyan-500 text-xs font-bold text-white transition flex items-center gap-1.5 shadow-lg shadow-cyan-950/40 active:scale-95">
          <span>🏠</span> Home / Standby [H]
        </button>
      </div>
    </div>

    <!-- Main Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

      <!-- COLUMN 1: Movement Controls (4 Cols) -->
      <div class="lg:col-span-4 flex flex-col gap-5">
        
        <!-- Mode & Step Size Selection -->
        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-2xl flex flex-col gap-3">
          <div class="flex justify-between items-center">
            <span class="text-xs font-extrabold uppercase tracking-wider text-slate-300">Control Mode</span>
            
            <div class="flex bg-slate-950 rounded-xl p-0.5 border border-slate-800 text-[11px] font-bold">
              <button onclick="setMoveMode('step')" id="btnModeStep" class="px-3 py-1 rounded-lg bg-cyan-600 text-white transition">Discrete Steps</button>
              <button onclick="setMoveMode('hold')" id="btnModeHold" class="px-3 py-1 rounded-lg text-slate-400 hover:text-slate-200 transition">Hold Continuous</button>
            </div>
          </div>

          <!-- Step Size Selector -->
          <div id="stepSizeRow" class="flex flex-col gap-1.5 pt-2 border-t border-slate-800">
            <div class="flex justify-between text-[11px] text-slate-400 font-semibold">
              <span>Step Distance:</span>
              <span class="text-cyan-400 mono font-bold" id="lblStepDist">10 mm</span>
            </div>
            <div class="grid grid-cols-5 gap-1.5 mono text-xs font-bold">
              <button onclick="setStepSize(1)" class="step-btn py-1.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-slate-700 text-slate-400">1mm</button>
              <button onclick="setStepSize(5)" class="step-btn py-1.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-slate-700 text-slate-400">5mm</button>
              <button onclick="setStepSize(10)" class="step-btn py-1.5 rounded-lg bg-cyan-600 text-white font-bold border border-cyan-500 shadow-md">10mm</button>
              <button onclick="setStepSize(20)" class="step-btn py-1.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-slate-700 text-slate-400">20mm</button>
              <button onclick="setStepSize(50)" class="step-btn py-1.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-slate-700 text-slate-400">50mm</button>
            </div>
          </div>

          <!-- Safe Speed Preset Selector -->
          <div class="flex flex-col gap-1.5 pt-2 border-t border-slate-800">
            <div class="flex justify-between text-[11px] text-slate-400 font-semibold">
              <span>Speed Preset:</span>
              <span class="text-cyan-400 mono font-bold" id="lblSpeedPreset">50% Balanced</span>
            </div>
            <div class="grid grid-cols-3 gap-2 text-xs font-bold">
              <button onclick="applySpeedPreset(30, '30% Precise')" id="btnSpd30" class="py-1.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-slate-700 text-slate-400">30% Precise</button>
              <button onclick="applySpeedPreset(50, '50% Balanced')" id="btnSpd50" class="py-1.5 rounded-lg bg-cyan-600 text-white border border-cyan-500 shadow-md">50% Balanced</button>
              <button onclick="applySpeedPreset(75, '75% Fast')" id="btnSpd75" class="py-1.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-slate-700 text-slate-400">75% Fast</button>
            </div>
          </div>
        </div>

        <!-- Directional Pad -->
        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-2xl">
          <div class="flex justify-between items-center mb-3">
            <span class="text-xs font-extrabold uppercase tracking-wider text-slate-300">Motion Control Pad</span>
            <span class="text-[10px] text-cyan-400 mono font-semibold" id="motionStatusBadge">READY</span>
          </div>

          <!-- Planar D-Pad (X / Y) -->
          <div class="flex flex-col items-center gap-3 my-2">
            
            <!-- Forward (+X) -->
            <button id="btnForward" class="keycap-btn w-20 h-14 rounded-2xl flex flex-col items-center justify-center text-cyan-400 font-bold border border-slate-700">
              <span class="text-base leading-none">▲</span>
              <span class="text-[10px] text-slate-300 font-mono mt-0.5"><span class="badge-key">W</span> +X</span>
            </button>

            <div class="flex items-center gap-3">
              <!-- Left (+Y) -->
              <button id="btnLeft" class="keycap-btn w-20 h-14 rounded-2xl flex flex-col items-center justify-center text-cyan-400 font-bold border border-slate-700">
                <span class="text-base leading-none">◀</span>
                <span class="text-[10px] text-slate-300 font-mono mt-0.5"><span class="badge-key">A</span> +Y</span>
              </button>

              <div class="w-16 h-14 rounded-2xl bg-slate-950/80 border border-slate-800 flex flex-col items-center justify-center text-[9px] text-slate-500 mono font-bold text-center">
                <span id="centerPadAction">STEP</span>
                <span class="text-cyan-400" id="centerPadVal">10mm</span>
              </div>

              <!-- Right (-Y) -->
              <button id="btnRight" class="keycap-btn w-20 h-14 rounded-2xl flex flex-col items-center justify-center text-cyan-400 font-bold border border-slate-700">
                <span class="text-base leading-none">▶</span>
                <span class="text-[10px] text-slate-300 font-mono mt-0.5"><span class="badge-key">D</span> -Y</span>
              </button>
            </div>

            <!-- Backward (-X) -->
            <button id="btnBackward" class="keycap-btn w-20 h-14 rounded-2xl flex flex-col items-center justify-center text-cyan-400 font-bold border border-slate-700">
              <span class="text-base leading-none">▼</span>
              <span class="text-[10px] text-slate-300 font-mono mt-0.5"><span class="badge-key">S</span> -X</span>
            </button>
          </div>

          <!-- Elevation (Z) & Rotation (R) -->
          <div class="grid grid-cols-2 gap-3 mt-4 pt-4 border-t border-slate-800">
            <div class="flex gap-2">
              <button id="btnUp" class="keycap-btn flex-1 h-12 rounded-xl flex flex-col items-center justify-center text-emerald-400 font-bold border border-slate-700">
                <span class="text-xs">▲ UP</span>
                <span class="text-[9px] text-slate-300 mono"><span class="badge-key">Q</span> +Z</span>
              </button>
              <button id="btnDown" class="keycap-btn flex-1 h-12 rounded-xl flex flex-col items-center justify-center text-emerald-400 font-bold border border-slate-700">
                <span class="text-xs">▼ DOWN</span>
                <span class="text-[9px] text-slate-300 mono"><span class="badge-key">E</span> -Z</span>
              </button>
            </div>

            <div class="flex gap-2">
              <button id="btnRotCCW" class="keycap-btn flex-1 h-12 rounded-xl flex flex-col items-center justify-center text-purple-400 font-bold border border-slate-700">
                <span class="text-xs">↺ CCW</span>
                <span class="text-[9px] text-slate-300 mono"><span class="badge-key">Z</span> +R</span>
              </button>
              <button id="btnRotCW" class="keycap-btn flex-1 h-12 rounded-xl flex flex-col items-center justify-center text-purple-400 font-bold border border-slate-700">
                <span class="text-xs">↻ CW</span>
                <span class="text-[9px] text-slate-300 mono"><span class="badge-key">C</span> -R</span>
              </button>
            </div>
          </div>
        </div>

        <!-- End Effector Action Bar -->
        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-2xl">
          <span class="text-xs font-extrabold uppercase tracking-wider text-slate-300 block mb-3">End Effector Direct Triggers</span>
          
          <div class="grid grid-cols-2 gap-3">
            <button onclick="toggleSuction()" id="btnSuction" class="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 flex flex-col items-center justify-center gap-1 hover:border-cyan-500 transition active:scale-95">
              <span class="text-2xl">🌀</span>
              <span class="text-xs font-bold text-slate-300" id="suctionLabel">SUCTION: OFF</span>
              <span class="text-[10px] text-slate-400 mono">Keys: <span class="badge-key">1</span> / <span class="badge-key">2</span></span>
            </button>

            <button onclick="toggleGripper()" id="btnGripper" class="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 flex flex-col items-center justify-center gap-1 hover:border-emerald-500 transition active:scale-95">
              <span class="text-2xl">🦀</span>
              <span class="text-xs font-bold text-slate-300" id="gripperLabel">GRIPPER: OPEN</span>
              <span class="text-[10px] text-slate-400 mono">Keys: <span class="badge-key">3</span> / <span class="badge-key">4</span></span>
            </button>
          </div>
        </div>

      </div>

      <!-- COLUMN 2: Telemetry HUD & 2D Desk Map Visualizer (4 Cols) -->
      <div class="lg:col-span-4 flex flex-col gap-5">
        
        <!-- Live Coordinates Telemetry HUD -->
        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-2xl">
          <div class="flex justify-between items-center mb-3">
            <span class="text-xs font-extrabold uppercase tracking-wider text-slate-300">Live Telemetry HUD</span>
            <span class="text-[10px] text-emerald-400 mono font-semibold">Real-Time</span>
          </div>
          
          <div class="grid grid-cols-4 gap-2 text-center mb-3">
            <div class="bg-slate-950 p-2.5 rounded-xl border border-slate-800 shadow-inner">
              <div class="text-[9px] text-slate-500 font-mono">X (mm)</div>
              <div class="text-lg font-black text-cyan-400 mono" id="dispX">240.0</div>
            </div>
            <div class="bg-slate-950 p-2.5 rounded-xl border border-slate-800 shadow-inner">
              <div class="text-[9px] text-slate-500 font-mono">Y (mm)</div>
              <div class="text-lg font-black text-cyan-400 mono" id="dispY">0.0</div>
            </div>
            <div class="bg-slate-950 p-2.5 rounded-xl border border-slate-800 shadow-inner">
              <div class="text-[9px] text-slate-500 font-mono">Z (mm)</div>
              <div class="text-lg font-black text-emerald-400 mono" id="dispZ">60.0</div>
            </div>
            <div class="bg-slate-950 p-2.5 rounded-xl border border-slate-800 shadow-inner">
              <div class="text-[9px] text-slate-500 font-mono">R (deg)</div>
              <div class="text-lg font-black text-purple-400 mono" id="dispR">0.0°</div>
            </div>
          </div>

          <div class="grid grid-cols-4 gap-2 text-center text-[11px] mono text-slate-400 bg-slate-950/60 p-2 rounded-xl border border-slate-800/80">
            <div>J1: <span id="dispJ1" class="text-white font-bold">0°</span></div>
            <div>J2: <span id="dispJ2" class="text-white font-bold">0°</span></div>
            <div>J3: <span id="dispJ3" class="text-white font-bold">0°</span></div>
            <div>J4: <span id="dispJ4" class="text-white font-bold">0°</span></div>
          </div>
        </div>

        <!-- 2D Workspace Top-Down Map -->
        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-2xl flex flex-col items-center">
          <div class="w-full flex justify-between items-center mb-2">
            <span class="text-xs font-extrabold uppercase tracking-wider text-slate-300">Desk Workspace Radar</span>
            <span class="text-[10px] text-cyan-400 mono">R: 340mm Reach</span>
          </div>

          <div class="w-full bg-slate-950 border border-slate-800 rounded-2xl relative overflow-hidden flex items-center justify-center p-2">
            <canvas id="deskCanvas" width="320" height="230" class="w-full h-auto"></canvas>
          </div>
        </div>

        <!-- Keyboard Guide Card -->
        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-4 shadow-2xl text-[11px]">
          <span class="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 block mb-2">Keyboard Shortcuts Reference</span>
          <div class="grid grid-cols-2 gap-y-1.5 gap-x-2 text-slate-300 mono">
            <div><span class="badge-key">W / S</span> : +X / -X (Forward/Back)</div>
            <div><span class="badge-key">A / D</span> : +Y / -Y (Left/Right)</div>
            <div><span class="badge-key">Q / E</span> : +Z / -Z (Up/Down)</div>
            <div><span class="badge-key">Z / C</span> : +R / -R (Rotate Yaw)</div>
            <div><span class="badge-key">1 / 2</span> : Suction ON / OFF</div>
            <div><span class="badge-key">3 / 4</span> : Gripper CLOSE / OPEN</div>
            <div><span class="badge-key">SPACE</span> : Capture Waypoint + Tool State</div>
            <div><span class="badge-key">P / R</span> : Play Forward / Revert Return</div>
          </div>
        </div>

      </div>

      <!-- COLUMN 3: Keypoint Recording & Revert Playback Studio (4 Cols) -->
      <div class="lg:col-span-4 flex flex-col gap-5">
        
        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-2xl flex flex-col gap-4">
          <div class="flex justify-between items-center">
            <span class="text-xs font-extrabold uppercase tracking-wider text-slate-300">Pick & Return Studio</span>
            <span class="text-xs mono text-cyan-400 font-bold bg-cyan-950 px-2 py-0.5 rounded-lg border border-cyan-800"><span id="kpCount">0</span> Waypoints</span>
          </div>

          <!-- Add Keypoint Section -->
          <div class="bg-slate-950 rounded-2xl p-3.5 border border-slate-800 flex flex-col gap-2.5">
            <div class="flex justify-between items-center text-[11px] text-slate-400 font-bold uppercase">
              <span>Capture Waypoint & Tool State</span>
              <span class="text-[9px] text-cyan-400 font-mono">Press [SPACE]</span>
            </div>
            
            <div class="grid grid-cols-2 gap-2">
              <select id="selAction" class="bg-slate-900 border border-slate-700 text-xs rounded-xl p-2 text-slate-200">
                <option value="AUTO" selected>✨ AUTO (Active Tool State)</option>
                <option value="NONE">📍 Move Only (No Tool)</option>
                <option value="SUCTION_ON">🌀 Suction ON (Pick / Grab)</option>
                <option value="SUCTION_OFF">💨 Suction OFF (Place / Drop)</option>
                <option value="GRIP_ON">🦀 Gripper CLOSE (Grip)</option>
                <option value="GRIP_OFF">👐 Gripper OPEN (Release)</option>
              </select>

              <select id="selMode" class="bg-slate-900 border border-slate-700 text-xs rounded-xl p-2 text-slate-200">
                <option value="0">Mode: JUMP (Arc Lift)</option>
                <option value="2">Mode: MOVL (Linear)</option>
                <option value="1">Mode: MOVJ (Joint)</option>
              </select>
            </div>

            <button onclick="recordKeypoint()" class="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold text-xs shadow-lg shadow-cyan-950/50 active:scale-98 transition flex items-center justify-center gap-1.5">
              <span>➕</span> CAPTURE WAYPOINT (<span class="mono">SPACE</span>)
            </button>
          </div>

          <!-- Playback Actions (Forward, Reverse Return, Cycle) -->
          <div class="flex flex-col gap-2">
            
            <div class="grid grid-cols-2 gap-2">
              <!-- Play Forward -->
              <button onclick="playRoutine('forward', false)" id="btnPlayFwd" class="py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-lg shadow-emerald-950/40 active:scale-98 transition flex items-center justify-center gap-1.5">
                <span>▶</span> PLAY [P]
              </button>

              <!-- Play Reverse (Return Item) -->
              <button onclick="playRoutine('reverse', false)" id="btnPlayRev" class="py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs shadow-lg shadow-purple-950/40 active:scale-98 transition flex items-center justify-center gap-1.5">
                <span>◀</span> REVERT / RETURN [R]
              </button>
            </div>

            <div class="grid grid-cols-2 gap-2">
              <!-- Loop Cycle (Forward <-> Return) -->
              <button onclick="playRoutine('cycle', true)" id="btnCycle" class="py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-300 font-bold text-xs border border-cyan-500/30 active:scale-98 transition flex items-center justify-center gap-1.5">
                <span>🔀</span> CYCLE PICK & RETURN
              </button>

              <!-- Invert and Append to Table -->
              <button onclick="invertAndAppend()" id="btnInvertAppend" class="py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-purple-300 font-bold text-xs border border-purple-500/30 active:scale-98 transition flex items-center justify-center gap-1.5">
                <span>➕</span> INVERT & APPEND
              </button>
            </div>

            <!-- Stop Button -->
            <button onclick="stopRoutine()" id="btnStop" class="hidden py-3 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold text-xs shadow-lg shadow-red-950/40 active:scale-98 transition flex items-center justify-center gap-1.5">
              <span>⏹</span> STOP PLAYBACK (<span id="activeModeBadge">FORWARD</span>)
            </button>
          </div>

          <!-- Keypoint Table -->
          <div class="max-h-52 overflow-y-auto flex flex-col gap-1.5 pr-1" id="keypointList">
            <div class="text-center py-6 text-xs text-slate-500 mono">No waypoints recorded yet.<br>Move arm to positions, toggle tools, then press SPACE!</div>
          </div>

          <!-- Export to Magic Box Button -->
          <div class="flex gap-2 pt-2 border-t border-slate-800">
            <button onclick="exportToMagicBox()" class="flex-1 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-300 font-bold text-xs border border-cyan-500/30 active:scale-98 transition">
              💾 Export to Magic Box
            </button>
            <button onclick="clearAllKeypoints()" class="px-3 py-2.5 rounded-xl bg-slate-800 hover:bg-red-950 text-slate-400 hover:text-red-400 text-xs border border-slate-700 transition">
              🗑 Clear
            </button>
          </div>
        </div>

      </div>

    </div>
  </div>

  <script>
    let moveMode = 'step';
    let stepDist = 10.0;
    let isHolding = false;
    let liveState = null;

    function setMoveMode(mode) {
      moveMode = mode;
      const bS = document.getElementById('btnModeStep');
      const bH = document.getElementById('btnModeHold');
      const sRow = document.getElementById('stepSizeRow');
      const cAct = document.getElementById('centerPadAction');
      const cVal = document.getElementById('centerPadVal');

      if (mode === 'step') {
        bS.className = "px-3 py-1 rounded-lg bg-cyan-600 text-white transition";
        bH.className = "px-3 py-1 rounded-lg text-slate-400 hover:text-slate-200 transition";
        sRow.classList.remove('hidden');
        cAct.innerText = "STEP";
        cVal.innerText = stepDist + "mm";
      } else {
        bH.className = "px-3 py-1 rounded-lg bg-cyan-600 text-white transition";
        bS.className = "px-3 py-1 rounded-lg text-slate-400 hover:text-slate-200 transition";
        sRow.classList.add('hidden');
        cAct.innerText = "HOLD";
        cVal.innerText = "CONT.";
      }
    }

    function setStepSize(dist) {
      stepDist = parseFloat(dist);
      document.getElementById('lblStepDist').innerText = stepDist + " mm";
      document.getElementById('centerPadVal').innerText = stepDist + "mm";
      
      document.querySelectorAll('.step-btn').forEach(btn => {
        if (btn.innerText === dist + 'mm') {
          btn.className = "step-btn py-1.5 rounded-lg bg-cyan-600 text-white font-bold border border-cyan-500 shadow-md";
        } else {
          btn.className = "step-btn py-1.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-slate-700 text-slate-400";
        }
      });
    }

    function applySpeedPreset(val, label) {
      document.getElementById('lblSpeedPreset').innerText = label;
      [30, 50, 75].forEach(v => {
        let el = document.getElementById('btnSpd' + v);
        if (v === val) {
          el.className = "py-1.5 rounded-lg bg-cyan-600 text-white border border-cyan-500 shadow-md";
        } else {
          el.className = "py-1.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-slate-700 text-slate-400";
        }
      });
      fetch(`/api/set_speed?speed=${val}`);
    }

    function triggerMove(dx, dy, dz, dr, jogCmd, btnId) {
      if (moveMode === 'step') {
        let el = document.getElementById(btnId);
        if (el) {
          el.classList.add('active-jog');
          setTimeout(() => el.classList.remove('active-jog'), 120);
        }
        let actDx = dx * stepDist;
        let actDy = dy * stepDist;
        let actDz = dz * stepDist;
        let actDr = dr * (stepDist > 10 ? 15.0 : 5.0);
        fetch(`/api/step?dx=${actDx}&dy=${actDy}&dz=${actDz}&dr=${actDr}`);
      } else {
        if (isHolding) return;
        isHolding = true;
        let el = document.getElementById(btnId);
        if (el) el.classList.add('active-jog');
        fetch(`/api/jog_start?cmd=${jogCmd}&is_joint=0`);
      }
    }

    function stopHoldMove(btnId) {
      if (moveMode === 'hold') {
        if (!isHolding) return;
        isHolding = false;
        let el = document.getElementById(btnId);
        if (el) el.classList.remove('active-jog');
        fetch('/api/jog_stop');
      }
    }

    function attachEvents(btnId, dx, dy, dz, dr, jogCmd) {
      const btn = document.getElementById(btnId);
      if (!btn) return;
      
      const startFn = (e) => { e.preventDefault(); triggerMove(dx, dy, dz, dr, jogCmd, btnId); };
      const stopFn = (e) => { e.preventDefault(); stopHoldMove(btnId); };

      btn.addEventListener('mousedown', startFn);
      btn.addEventListener('mouseup', stopFn);
      btn.addEventListener('mouseleave', stopFn);

      btn.addEventListener('touchstart', startFn, {passive: false});
      btn.addEventListener('touchend', stopFn);
      btn.addEventListener('touchcancel', stopFn);
    }

    attachEvents('btnForward',   1,  0,  0,  0, 1);
    attachEvents('btnBackward', -1,  0,  0,  0, 2);
    attachEvents('btnLeft',      0,  1,  0,  0, 3);
    attachEvents('btnRight',     0, -1,  0,  0, 4);
    attachEvents('btnUp',        0,  0,  1,  0, 5);
    attachEvents('btnDown',      0,  0, -1,  0, 6);
    attachEvents('btnRotCCW',    0,  0,  0,  1, 7);
    attachEvents('btnRotCW',     0,  0,  0, -1, 8);

    const keyBindings = {
      'w': { dx: 1, dy: 0, dz: 0, dr: 0, cmd: 1, btnId: 'btnForward' },
      's': { dx: -1, dy: 0, dz: 0, dr: 0, cmd: 2, btnId: 'btnBackward' },
      'a': { dx: 0, dy: 1, dz: 0, dr: 0, cmd: 3, btnId: 'btnLeft' },
      'd': { dx: 0, dy: -1, dz: 0, dr: 0, cmd: 4, btnId: 'btnRight' },
      'q': { dx: 0, dy: 0, dz: 1, dr: 0, cmd: 5, btnId: 'btnUp' },
      'e': { dx: 0, dy: 0, dz: -1, dr: 0, cmd: 6, btnId: 'btnDown' },
      'z': { dx: 0, dy: 0, dz: 0, dr: 1, cmd: 7, btnId: 'btnRotCCW' },
      'c': { dx: 0, dy: 0, dz: 0, dr: -1, cmd: 8, btnId: 'btnRotCW' }
    };

    let activeKey = null;

    window.addEventListener('keydown', (e) => {
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) return;
      let k = e.key.toLowerCase();

      if (keyBindings[k]) {
        e.preventDefault();
        if (activeKey !== k) {
          activeKey = k;
          let m = keyBindings[k];
          triggerMove(m.dx, m.dy, m.dz, m.dr, m.cmd, m.btnId);
        }
      } else if (k === '1') {
        fetch('/api/suction?enable=1');
      } else if (k === '2') {
        fetch('/api/suction?enable=0');
      } else if (k === '3') {
        fetch('/api/gripper?enable=1');
      } else if (k === '4') {
        fetch('/api/gripper?enable=0');
      } else if (e.code === 'Space') {
        e.preventDefault();
        recordKeypoint();
      } else if (k === 'p') {
        playRoutine('forward', false);
      } else if (k === 'r') {
        playRoutine('reverse', false);
      } else if (k === 'h') {
        sendHome();
      }
    });

    window.addEventListener('keyup', (e) => {
      let k = e.key.toLowerCase();
      if (keyBindings[k] && activeKey === k) {
        let m = keyBindings[k];
        activeKey = null;
        stopHoldMove(m.btnId);
      }
    });

    function toggleSuction() {
      let next = liveState && liveState.suction ? 0 : 1;
      fetch(`/api/suction?enable=${next}`);
    }

    function toggleGripper() {
      let next = liveState && liveState.gripper ? 0 : 1;
      fetch(`/api/gripper?enable=${next}`);
    }

    function sendHome() {
      fetch('/api/home');
    }

    function clearAlarms() {
      fetch('/api/clear_alarms').then(() => alert("Alarms cleared & motors calibrated!"));
    }

    function recordKeypoint() {
      let act = document.getElementById('selAction').value;
      let mode = document.getElementById('selMode').value;
      fetch(`/api/add_keypoint?action=${act}&mode=${mode}&delay=500`).then(() => fetchStatus());
    }

    function changeWaypointAction(idx, newAct) {
      fetch(`/api/update_action?index=${idx}&action=${newAct}`).then(() => fetchStatus());
    }

    function deleteKeypoint(idx) {
      fetch(`/api/delete_keypoint?index=${idx}`).then(() => fetchStatus());
    }

    function clearAllKeypoints() {
      if (confirm("Clear all recorded keypoints?")) {
        fetch('/api/clear_keypoints').then(() => fetchStatus());
      }
    }

    function invertAndAppend() {
      if (!liveState || !liveState.keypoints || liveState.keypoints.length === 0) {
        alert("⚠️ Record a forward sequence first before appending return!");
        return;
      }
      fetch('/api/invert_append')
        .then(r => r.json())
        .then(d => {
          if (d.ok) fetchStatus();
          else alert(d.msg);
        });
    }

    function playRoutine(mode, loop) {
      if (!liveState || !liveState.keypoints || liveState.keypoints.length === 0) {
        alert("⚠️ No waypoints recorded yet! Position the arm and press [SPACE] to capture waypoints before playing.");
        return;
      }
      fetch(`/api/playback?mode=${mode}&loop=${loop ? 1 : 0}`)
        .then(r => r.json())
        .then(d => {
          if (!d.ok) alert(d.msg);
        });
    }

    function stopRoutine() {
      fetch('/api/stop');
    }

    function exportToMagicBox() {
      fetch('/api/export')
        .then(r => r.json())
        .then(d => {
          alert(d.msg || "Exported successfully!");
        });
    }

    function fetchStatus() {
      fetch('/api/status')
        .then(r => r.json())
        .then(d => {
          liveState = d;

          document.getElementById('dispX').innerText = d.x.toFixed(1);
          document.getElementById('dispY').innerText = d.y.toFixed(1);
          document.getElementById('dispZ').innerText = d.z.toFixed(1);
          document.getElementById('dispR').innerText = d.r.toFixed(1) + '°';
          
          document.getElementById('dispJ1').innerText = d.j1.toFixed(0) + '°';
          document.getElementById('dispJ2').innerText = d.j2.toFixed(0) + '°';
          document.getElementById('dispJ3').innerText = d.j3.toFixed(0) + '°';
          document.getElementById('dispJ4').innerText = d.j4.toFixed(0) + '°';

          const btnS = document.getElementById('btnSuction');
          const lblS = document.getElementById('suctionLabel');
          if (d.suction) {
            btnS.className = "p-3.5 rounded-2xl bg-cyan-500/20 border-2 border-cyan-400 flex flex-col items-center justify-center gap-1 shadow-lg shadow-cyan-950/50";
            lblS.innerText = "SUCTION: ON (SUCK)";
            lblS.className = "text-xs font-bold text-cyan-300";
          } else {
            btnS.className = "p-3.5 rounded-2xl bg-slate-950 border border-slate-800 flex flex-col items-center justify-center gap-1 hover:border-cyan-500 transition";
            lblS.innerText = "SUCTION: OFF";
            lblS.className = "text-xs font-bold text-slate-400";
          }

          const btnG = document.getElementById('btnGripper');
          const lblG = document.getElementById('gripperLabel');
          if (d.gripper) {
            btnG.className = "p-3.5 rounded-2xl bg-emerald-500/20 border-2 border-emerald-400 flex flex-col items-center justify-center gap-1 shadow-lg shadow-emerald-950/50";
            lblG.innerText = "GRIPPER: CLOSED";
            lblG.className = "text-xs font-bold text-emerald-300";
          } else {
            btnG.className = "p-3.5 rounded-2xl bg-slate-950 border border-slate-800 flex flex-col items-center justify-center gap-1 hover:border-emerald-500 transition";
            lblG.innerText = "GRIPPER: OPEN";
            lblG.className = "text-xs font-bold text-slate-400";
          }

          const btnPlayFwd = document.getElementById('btnPlayFwd');
          const btnPlayRev = document.getElementById('btnPlayRev');
          const btnCycle = document.getElementById('btnCycle');
          const btnInvertAppend = document.getElementById('btnInvertAppend');
          const btnStop = document.getElementById('btnStop');
          const badge = document.getElementById('activeModeBadge');

          if (d.is_playing) {
            btnPlayFwd.parentElement.classList.add('hidden');
            btnCycle.parentElement.classList.add('hidden');
            btnStop.classList.remove('hidden');
            badge.innerText = d.playback_mode.toUpperCase();
          } else {
            btnPlayFwd.parentElement.classList.remove('hidden');
            btnCycle.parentElement.classList.remove('hidden');
            btnStop.classList.add('hidden');
          }

          renderKeypoints(d.keypoints, d.active_step);
          drawDeskCanvas(d.x, d.y, d.z, d.keypoints);
        })
        .catch(err => console.error(err));
    }

    function renderKeypoints(kps, activeStep) {
      document.getElementById('kpCount').innerText = kps.length;
      const list = document.getElementById('keypointList');
      if (kps.length === 0) {
        list.innerHTML = `<div class="text-center py-6 text-xs text-slate-500 mono">No waypoints recorded yet.<br>Move arm to positions, toggle tools, then press SPACE!</div>`;
        return;
      }

      let html = '';
      kps.forEach((kp, idx) => {
        let isActive = idx === activeStep;
        let modeStr = kp.mode === 0 ? 'JUMP' : (kp.mode === 1 ? 'MOVJ' : 'MOVL');
        
        html += `
          <div class="flex items-center justify-between p-2 rounded-xl border ${isActive ? 'bg-cyan-500/20 border-cyan-400 shadow-md shadow-cyan-950/50' : 'bg-slate-950 border-slate-800/80'} text-xs">
            <div class="flex items-center gap-2">
              <span class="w-5 h-5 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center font-bold text-[10px] mono">${idx + 1}</span>
              <div>
                <div class="mono font-bold text-slate-200">(${kp.x}, ${kp.y}, ${kp.z}) &bull; <span class="text-purple-300">${kp.r}°</span></div>
                <div class="text-[10px] text-slate-400 font-medium">${modeStr} &bull; ${kp.delay}ms</div>
              </div>
            </div>

            <!-- Action Pill Selector -->
            <div class="flex items-center gap-1.5">
              <select onchange="changeWaypointAction(${idx}, this.value)" class="bg-slate-900 border border-slate-700 text-[11px] font-bold rounded-lg px-2 py-1 ${kp.action.includes('ON') ? 'text-cyan-400 border-cyan-500/40' : (kp.action.includes('OFF') ? 'text-amber-400 border-amber-500/40' : 'text-slate-400')}">
                <option value="NONE" ${kp.action === 'NONE' ? 'selected' : ''}>📍 Move Only</option>
                <option value="SUCTION_ON" ${kp.action === 'SUCTION_ON' ? 'selected' : ''}>🌀 Suction ON (Pick)</option>
                <option value="SUCTION_OFF" ${kp.action === 'SUCTION_OFF' ? 'selected' : ''}>💨 Suction OFF (Place)</option>
                <option value="GRIP_ON" ${kp.action === 'GRIP_ON' ? 'selected' : ''}>🦀 Gripper CLOSE</option>
                <option value="GRIP_OFF" ${kp.action === 'GRIP_OFF' ? 'selected' : ''}>👐 Gripper OPEN</option>
              </select>
              
              <button onclick="deleteKeypoint(${idx})" class="text-slate-500 hover:text-red-400 p-1 text-sm font-bold">&times;</button>
            </div>
          </div>
        `;
      });
      list.innerHTML = html;
    }

    function drawDeskCanvas(armX, armY, armZ, keypoints) {
      const canvas = document.getElementById('deskCanvas');
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;
      const cx = w / 2;
      const cy = h - 25;
      const scale = 0.55;

      ctx.clearRect(0, 0, w, h);

      ctx.beginPath();
      ctx.arc(cx, cy, 340 * scale, Math.PI, 2 * Math.PI, false);
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.2)';
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.beginPath();
      ctx.arc(cx, cy, 18, 0, 2 * Math.PI);
      ctx.fillStyle = '#1e293b';
      ctx.fill();
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 2;
      ctx.stroke();
      
      ctx.fillStyle = '#fff';
      ctx.font = '9px monospace';
      ctx.fillText('BASE', cx - 12, cy + 3);

      keypoints.forEach((kp, i) => {
        let kpx = cx + (kp.y * scale);
        let kpy = cy - (kp.x * scale);
        ctx.beginPath();
        ctx.arc(kpx, kpy, 5, 0, 2 * Math.PI);
        ctx.fillStyle = kp.action.includes('ON') ? '#06b6d4' : (kp.action.includes('OFF') ? '#f59e0b' : '#10b981');
        ctx.fill();
        ctx.fillStyle = '#fff';
        ctx.fillText(`${i+1}`, kpx + 7, kpy + 3);
      });

      let endX = cx + (armY * scale);
      let endY = cy - (armX * scale);

      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(endX, endY);
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 3;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(endX, endY, 8, 0, 2 * Math.PI);
      ctx.fillStyle = '#0284c7';
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    setInterval(fetchStatus, 80);
    fetchStatus();
  </script>
</body>
</html>
"""

def main():
    print("=" * 70)
    print("  DOBOT MAGICIAN LITE - PRO WEB STUDIO & CALIBRATION")
    print("=" * 70)
    
    dobot.connect()

    server = ThreadingHTTPServer(("127.0.0.1", PORT), GUIHandler)
    server.daemon_threads = True
    url = f"http://127.0.0.1:{PORT}"
    print(f"\n[OK] GUI Server active at: {url}")
    print("[OK] Opening web dashboard in your browser...")
    webbrowser.open(url)
    
    print("\nPress Ctrl+C to terminate the server.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Dobot GUI Server...")
        dobot.close()
        server.server_close()
        print("[OK] Server stopped.")

if __name__ == "__main__":
    main()
