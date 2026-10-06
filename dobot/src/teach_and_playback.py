#!/usr/bin/env python3
"""
========================================================================================
DOBOT MAGICIAN LITE - INTERACTIVE DESK TEACH & PLAYBACK SUITE
Real-time arm pose reading, keypoint recording, suction/gripper triggering,
instant replay, and one-click export to Dobot Magic Box for offline execution!
========================================================================================
"""

import sys
import os
import time
import struct
import select
import termios
import tty
import serial

DEFAULT_PORT = "/dev/cu.usbmodem549A30D515392"
def find_magic_box_mount():
    for name in ["/Volumes/NO NAME", "/Volumes/NO NAME 1"]:
        if os.path.exists(name) and os.path.exists(os.path.join(name, "System")):
            return name
    return "/Volumes/NO NAME"

MAGIC_BOX_MOUNT = find_magic_box_mount()

class DobotDriver:
    def __init__(self, port=DEFAULT_PORT, baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.suction_on = False
        self.gripper_on = False

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.05)
            # Clear buffers
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            # Clear alarms & start queue
            self._send_cmd(20, 1) # Clear alarms
            self._send_cmd(245, 1) # Clear queue
            self._send_cmd(240, 1) # Start queue
            # Set speed params
            self.set_speed_params()
            return True
        except Exception as e:
            print(f"[ERROR] Could not connect to {self.port}: {e}")
            return False

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    def _send_cmd(self, cmd_id, ctrl=0, params=b''):
        length = len(params) + 2
        payload = bytes([cmd_id, ctrl]) + params
        checksum = (256 - (sum(payload) % 256)) % 256
        packet = bytes([0xAA, 0xAA, length]) + payload + bytes([checksum])
        self.ser.write(packet)
        time.sleep(0.02)
        resp = self.ser.read_all()
        return resp

    def get_pose(self):
        """Returns (x, y, z, r, j1, j2, j3, j4)"""
        resp = self._send_cmd(10, 0) # GetPose ID: 10
        if resp and len(resp) >= 37:
            for idx in range(len(resp) - 36):
                if resp[idx] == 0xAA and resp[idx+1] == 0xAA and resp[idx+3] == 0x0A:
                    try:
                        floats = struct.unpack('<8f', resp[idx+5:idx+37])
                        if 50.0 <= floats[0] <= 500.0:
                            return floats
                    except Exception:
                        pass
        return None

    def set_speed_params(self, velocity_ratio=50, accel_ratio=50):
        """Set JOG and PTP speed parameters"""
        params = struct.pack('<8f', 150.0, 150.0, 150.0, 150.0, 150.0, 150.0, 150.0, 150.0)
        self._send_cmd(80, 1, params) # SetPTPCoordinateParams
        self._send_cmd(81, 1, struct.pack('<2f', 50.0, 50.0))

    def set_suction(self, enable: bool):
        """Toggle Vacuum Suction Cup (ID: 62)"""
        self.suction_on = enable
        params = bytes([1, 1 if enable else 0, 0])
        self._send_cmd(62, 1, params)

    def set_gripper(self, enable: bool):
        """Toggle Pneumatic Gripper (ID: 63)"""
        self.gripper_on = enable
        params = bytes([1, 1 if enable else 0, 0])
        self._send_cmd(63, 1, params)

    def move_ptp(self, mode, x, y, z, r=0.0):
        """
        Send PTP Command (ID: 84, Ctrl: 3 Queued)
        mode: 0: JUMP_XYZ, 1: MOVJ_XYZ, 2: MOVL_XYZ
        """
        params = struct.pack('<B4f', int(mode), float(x), float(y), float(z), float(r))
        self._send_cmd(84, 3, params)


class KeypointManager:
    def __init__(self, driver: DobotDriver):
        self.driver = driver
        self.keypoints = [] # list of dicts: {x, y, z, r, mode, action, delay}

    def add_keypoint(self, pose, mode=0, action="NONE", delay_ms=500):
        """
        action: 'NONE', 'SUCTION_ON', 'SUCTION_OFF', 'GRIP_ON', 'GRIP_OFF'
        mode: 0 (JUMP), 1 (MOVJ), 2 (MOVL)
        """
        kp = {
            "x": round(pose[0], 1),
            "y": round(pose[1], 1),
            "z": round(pose[2], 1),
            "r": round(pose[3], 1),
            "mode": mode,
            "action": action,
            "delay": delay_ms
        }
        self.keypoints.append(kp)
        return kp

    def undo(self):
        if self.keypoints:
            return self.keypoints.pop()
        return None

    def clear(self):
        self.keypoints.clear()

    def print_table(self):
        print("\n" + "=" * 78)
        print(f"{'#':<3} | {'X (mm)':<7} | {'Y (mm)':<7} | {'Z (mm)':<7} | {'R (deg)':<7} | {'Mode':<6} | {'Action':<13} | {'Delay':<5}")
        print("-" * 78)
        if not self.keypoints:
            print("  (No keypoints recorded yet. Move arm and press [SPACE] to capture!)")
        for i, kp in enumerate(self.keypoints):
            mode_str = "JUMP" if kp["mode"] == 0 else ("MOVJ" if kp["mode"] == 1 else "MOVL")
            print(f"{i+1:<3} | {kp['x']:<7.1f} | {kp['y']:<7.1f} | {kp['z']:<7.1f} | {kp['r']:<7.1f} | {mode_str:<6} | {kp['action']:<13} | {kp['delay']}ms")
        print("=" * 78 + "\n")

    def play_routine(self):
        """Execute all recorded keypoints in sequence on the physical arm"""
        if not self.keypoints:
            print("[WARN] No keypoints to execute!")
            return

        print("\n>>> EXECUTING RECORDED ROUTINE ON DOBOT...")
        for i, kp in enumerate(self.keypoints):
            mode_name = "JUMP" if kp["mode"] == 0 else ("MOVJ" if kp["mode"] == 1 else "MOVL")
            print(f" -> Step {i+1}/{len(self.keypoints)}: Moving to ({kp['x']}, {kp['y']}, {kp['z']}) [{mode_name}] | Action: {kp['action']}")
            
            # Send movement
            self.driver.move_ptp(kp["mode"], kp["x"], kp["y"], kp["z"], kp["r"])
            time.sleep(1.2) # Allow arm transit

            # Trigger action
            if kp["action"] == "SUCTION_ON":
                self.driver.set_suction(True)
                print("    [+] Suction Activated (SUCK)")
            elif kp["action"] == "SUCTION_OFF":
                self.driver.set_suction(False)
                print("    [-] Suction Deactivated (RELEASE)")
            elif kp["action"] == "GRIP_ON":
                self.driver.set_gripper(True)
                print("    [+] Gripper Closed (GRIP)")
            elif kp["action"] == "GRIP_OFF":
                self.driver.set_gripper(False)
                print("    [-] Gripper Opened (RELEASE)")

            if kp["delay"] > 0:
                time.sleep(kp["delay"] / 1000.0)

        # Return to safe standby
        print("[OK] Sequence Finished! Returning to Standby...")
        self.driver.move_ptp(1, 240.0, 0.0, 50.0, 0.0)
        time.sleep(1.0)

    def export_to_magicbox(self, routine_name="MyDeskRoutine.py"):
        """Save as Playback.txt and as a standalone MicroPython script on Magic Box"""
        if not self.keypoints:
            print("[WARN] No keypoints recorded to export.")
            return

        # 1. Format Playback.txt
        # [X, Y, Z, R, Mode, EffType, EffState, Delay]
        # EffType: 0=None, 1=Gripper, 2=Suction
        playback_lines = [
            "# Dobot Teach & Playback Generated Trajectory",
            "# Format: [X, Y, Z, R, Mode, EffectorType, EffectorState, DelayMs]"
        ]
        for kp in self.keypoints:
            eff_type = 0
            eff_state = 0
            if "SUCTION" in kp["action"]:
                eff_type = 2
                eff_state = 1 if kp["action"] == "SUCTION_ON" else 0
            elif "GRIP" in kp["action"]:
                eff_type = 1
                eff_state = 1 if kp["action"] == "GRIP_ON" else 0

            line = f"[{kp['x']}, {kp['y']}, {kp['z']}, {kp['r']}, {kp['mode']}, {eff_type}, {eff_state}, {kp['delay']}]"
            playback_lines.append(line)

        # 2. Format standalone MicroPython script
        py_code = f"""#devType: ML
# =========================================================================================
# DOBOT MAGICIAN LITE - CUSTOM DESK ROUTINE: {routine_name}
# Recorded via Interactive Teach & Playback Tool
# =========================================================================================
import dType

api = 0
dType.SetQueuedCmdClear(api)
dType.SetQueuedCmdStopExec(api)
dType.SetQueuedCmdStartExec(api)

dType.SetArmSpeedRatio(api, 1, 45, 1)
dType.SetPTPJumpParams(api, 25.0, 100.0, 1)
dType.SetLostStepParams(api, 5.0, 0)
dType.SetHOMECmd(api, 0, 1)

total_steps = {len(self.keypoints)}
dType.SetProgbar(api, 0)

"""
        for i, kp in enumerate(self.keypoints):
            py_code += f"# Step {i+1}: Action = {kp['action']}\n"
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
            py_code += f"dType.SetProgbar(api, int({i+1} * 100 / total_steps))\n\n"

        py_code += """# Return to Standby
dType.SetPTPCmdEx(api, 1, 240.0, 0.0, 50.0, 0.0, 1)
dType.SetEndEffectorSuctionCupEx(api, 0, 0, 1)
dType.SetProgbar(api, 100)
dType.dSleep(1000)
dType.RestartMagicBox(api)
"""

        # Write to mounted Magic Box storage if connected
        if os.path.exists(MAGIC_BOX_MOUNT):
            # Save Playback.txt
            pb_path = os.path.join(MAGIC_BOX_MOUNT, "Playback", "Playback.txt")
            with open(pb_path, "w") as f:
                f.write("\n".join(playback_lines) + "\n")
            print(f"[OK] Saved to Magic Box Playback: {pb_path}")

            # Save Script
            sc_path = os.path.join(MAGIC_BOX_MOUNT, "Script", routine_name)
            with open(sc_path, "w") as f:
                f.write(py_code)
            print(f"[OK] Saved to Magic Box Scripts: {sc_path}")
        else:
            print(f"[WARN] Magic Box mount not found at {MAGIC_BOX_MOUNT}. Saving locally...")

        # Always save local backup
        local_dir = os.path.expanduser("/Users/aadilsp/Desktop/Antigravity/Lekshmivilasam/dobot/src/saved_routines")
        os.makedirs(local_dir, exist_ok=True)
        local_file = os.path.join(local_dir, routine_name)
        with open(local_file, "w") as f:
            f.write(py_code)
        print(f"[OK] Local backup saved: {local_file}")


def get_key_nonblocking():
    """Non-blocking single keypress reader for Unix terminal"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.08)
        if rlist:
            ch = sys.stdin.read(1)
            return ch
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def main():
    print("\n" + "=" * 78)
    print(" 🦾 DOBOT MAGICIAN LITE - INTERACTIVE DESK TEACH & PLAYBACK")
    print("=" * 78)
    print("Connecting to Dobot over USB serial...")
    driver = DobotDriver()
    if not driver.connect():
        sys.exit(1)

    print("[SUCCESS] Connected to Dobot Magician Lite!")
    manager = KeypointManager(driver)

    print("""
------------------------------------------------------------------------------
 CONTROLS & KEYBOARD SHORTCUTS:
  [SPACE] / [T]  : Capture & Save Current Arm Location as a Keypoint
  [S]            : Capture with SUCTION ON (Grab Item)
  [R]            : Capture with SUCTION OFF / RELEASE (Drop Item)
  [G]            : Capture with GRIPPER TOGGLE
  [M]            : Toggle Motion Mode (JUMP <-> MOVL <-> MOVJ)
  [P]            : 🚀 PLAYBACK & TEST RECORDED ROUTINE ON THE ARM!
  [W]            : 💾 WRITE / EXPORT TO MAGIC BOX (For Offline Button Replay)
  [L]            : List all recorded Keypoints
  [U]            : Undo Last Keypoint
  [C]            : Clear All Keypoints
  [H]            : Move Arm to Home/Standby
  [Q]            : Quit Tool
------------------------------------------------------------------------------
""")

    current_mode = 0 # 0: JUMP, 1: MOVJ, 2: MOVL
    last_pose = None

    try:
        while True:
            # Poll live arm pose
            pose = driver.get_pose()
            if pose:
                last_pose = pose
                mode_str = "JUMP" if current_mode == 0 else ("MOVJ" if current_mode == 1 else "MOVL")
                suct_str = "[SUCK: ON]" if driver.suction_on else "[SUCK: OFF]"
                # Print live telemetry on single line
                sys.stdout.write(
                    f"\rLIVE POSE -> X:{pose[0]:>6.1f} | Y:{pose[1]:>6.1f} | Z:{pose[2]:>6.1f} | R:{pose[3]:>5.1f}° | Mode:{mode_str:<4} | {suct_str} | Saved:{len(manager.keypoints)}  "
                )
                sys.stdout.flush()

            key = get_key_nonblocking()
            if key:
                key_l = key.lower()
                if key == ' ' or key_l == 't':
                    if last_pose:
                        kp = manager.add_keypoint(last_pose, mode=current_mode, action="NONE")
                        print(f"\n[+] Captured Waypoint #{len(manager.keypoints)} at ({kp['x']}, {kp['y']}, {kp['z']})")
                elif key_l == 's':
                    if last_pose:
                        driver.set_suction(True)
                        kp = manager.add_keypoint(last_pose, mode=current_mode, action="SUCTION_ON", delay_ms=700)
                        print(f"\n[+] Captured Waypoint #{len(manager.keypoints)} with [SUCTION ON] at ({kp['x']}, {kp['y']}, {kp['z']})")
                elif key_l == 'r':
                    if last_pose:
                        driver.set_suction(False)
                        kp = manager.add_keypoint(last_pose, mode=current_mode, action="SUCTION_OFF", delay_ms=500)
                        print(f"\n[+] Captured Waypoint #{len(manager.keypoints)} with [SUCTION OFF/RELEASE] at ({kp['x']}, {kp['y']}, {kp['z']})")
                elif key_l == 'g':
                    if last_pose:
                        new_state = not driver.gripper_on
                        driver.set_gripper(new_state)
                        action_name = "GRIP_ON" if new_state else "GRIP_OFF"
                        kp = manager.add_keypoint(last_pose, mode=current_mode, action=action_name, delay_ms=600)
                        print(f"\n[+] Captured Waypoint #{len(manager.keypoints)} with [{action_name}] at ({kp['x']}, {kp['y']}, {kp['z']})")
                elif key_l == 'm':
                    current_mode = (current_mode + 1) % 3
                    m_name = "JUMP (Safe Arc Lift)" if current_mode == 0 else ("MOVJ (Joint Coordinated)" if current_mode == 1 else "MOVL (Straight Linear)")
                    print(f"\n[*] Motion Mode Changed to: {m_name}")
                elif key_l == 'p':
                    manager.print_table()
                    manager.play_routine()
                elif key_l == 'w':
                    manager.print_table()
                    manager.export_to_magicbox("DeskPickAndPlace.py")
                elif key_l == 'l':
                    manager.print_table()
                elif key_l == 'u':
                    undone = manager.undo()
                    if undone:
                        print(f"\n[-] Undid Keypoint at ({undone['x']}, {undone['y']}, {undone['z']})")
                    else:
                        print("\n[WARN] No keypoints to undo.")
                elif key_l == 'c':
                    manager.clear()
                    print("\n[!] Cleared all recorded keypoints.")
                elif key_l == 'h':
                    print("\n[*] Sending arm to Home / Standby...")
                    driver.move_ptp(1, 240.0, 0.0, 50.0, 0.0)
                elif key_l == 'q' or key == '\x03': # Quit / Ctrl+C
                    print("\nExiting Teach & Playback...")
                    break

    finally:
        driver.set_suction(False)
        driver.set_gripper(False)
        driver.close()
        print("[OK] Dobot disconnected safely.")

if __name__ == "__main__":
    main()
