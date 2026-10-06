# Dobot Magician Lite & Magic Box (Robotics)

**Category:** Robotics / State Sasthramela (Kerala)  
**Connected Hardware:** Dobot Magician Lite 4-DOF Robotic Arm + Magic Box Controller  
**Serial Port:** `/dev/cu.usbmodem549A30D515392`  
**Web GUI Dashboard:** [http://127.0.0.1:8080](http://127.0.0.1:8080)  
**Flash Mount:** `/Volumes/NO NAME`  
**Status:** Live Web GUI Studio Running (Hardware Verified & Calibrated)  

---

## 1. Live Web GUI Controller & Teach Studio

Launch the full interactive visual GUI:

```bash
python3 /Users/aadilsp/Desktop/Antigravity/Lekshmivilasam/dobot/src/dobot_gui.py
```
> **URL:** [http://127.0.0.1:8080](http://127.0.0.1:8080)

### Controls & Keyboard Mappings:
| Action | Key / Button (Hold to Move) | Axis / Motion |
| :--- | :---: | :--- |
| **Move Forward** | **`W`** | $+X$ (Forward on desk) |
| **Move Backward** | **`S`** | $-X$ (Backward) |
| **Move Left** | **`A`** | $-Y$ (Pan Left) |
| **Move Right** | **`D`** | $+Y$ (Pan Right) |
| **Move Up** | **`Q`** | $+Z$ (Elevation Up) |
| **Move Down** | **`E`** | $-Z$ (Elevation Down) |
| **Rotate Wrist CCW** | **`Z`** | $-R$ (Yaw Rotation) |
| **Rotate Wrist CW** | **`C`** | $+R$ (Yaw Rotation) |
| **Suction Grab / Drop** | **`1`** / **`2`** | Vacuum Suction ON / OFF |
| **Gripper Close / Open** | **`3`** / **`4`** | Pneumatic Grip / Release |
| **Save Keypoint** | **`[SPACE]`** | Captures $(X, Y, Z, R)$ + Active Gripper/Suction state |
| **Play Forward** | **`P`** | Replays forward sequence on physical arm |
| **Revert / Return Item** | **`R`** | Replays in reverse with inverted Grab/Release (returns item!) |
| **Pick & Return Cycle** | **UI Button** | Continuously loops forward transit and return transit |
| **Home Arm** | **`H`** | Safe Standby Position |
| **Step Presets** | **`1mm – 50mm`** | Selectable discrete step distance |
| **Speed Presets** | **`30%, 50%, 75%`** | Calibrated motion velocity limits |

---

## 2. Standalone MicroPython Scripts on Magic Box (`/Volumes/NO NAME/Script/`)
- **`SmartPalletizer.py`**: Automated $2 \times 2$ grid matrix palletizer.
- **`ColorSortingDemo.py`**: High-speed multi-bin sorting sequence.
- **`WaveAndDance.py`**: Kinematics showmanship & greeting wave routine.
- **`PenDrawingShape.py`**: Precision geometric 5-point star drawing with pen up/down.

---

## Activity Log & Summary
- **[Hardware Inspection]**: Detected Dobot Magic Box on `/dev/cu.usbmodem549A30D515392` and `/Volumes/NO NAME`.
- **[Playback & Scripts Deployed]**: Created `Playback.py` + `Playback.txt` and deployed 4 standalone routines to the Magic Box.
- **[Motion Engine Overhaul & Hardware JOG Integration]**: Resolved movement stall issue by integrating native hardware JOG commands (`SetJOGCmd` ID: 73) and queued PTP trajectory planner (`SetPTPCmd` ID: 84).
- **[Live GUI Studio with Continuous Movement]**: Deployed full Web Studio on port 8080 with continuous hold-to-move stepping on WASD/QE/ZC keys and on-screen buttons, dynamic speed & acceleration presets (30%, 50%, 75%), discrete step increments (1mm–50mm), vacuum suction and pneumatic gripper triggers, live 2D radar workspace visualizer, sequence player, and one-click Magic Box export.
- **[Pick, Place & Revert/Return Engine Added]**: Integrated full inverted return playback (<kbd>R</kbd>), auto gripper/suction state capture on <kbd>SPACE</kbd>, and continuous cycle looping (Forward $\leftrightarrow$ Return) for autonomous desk demonstration.
- **[Waypoint Suction & Gripper Execution Enhanced]**: Implemented dual-channel queued/immediate triggering (`ID: 62 / 63`), added vacuum seal/release dwell timers (600ms), and added inline waypoint action selectors in the table for instant modification between `Suction ON (Pick)`, `Suction OFF (Place)`, `Grip`, and `Move Only`.
