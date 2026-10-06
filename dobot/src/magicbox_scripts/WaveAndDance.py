#devType: ML
#isUsingRail: False
# =========================================================================================
# DOBOT MAGICIAN LITE - SHOWMANSHIP DANCE & GREETING ROUTINE
# Smooth coordinated 4-axis motion demonstrating kinematics, arcs & greetings
# =========================================================================================

import dType
import math

api = 0
dType.SetQueuedCmdClear(api)
dType.SetQueuedCmdStopExec(api)
dType.SetQueuedCmdStartExec(api)

# Smooth acceleration and velocity
dType.SetArmSpeedRatio(api, 1, 50, 1)
dType.SetHOMECmd(api, 0, 1)
dType.SetProgbar(api, 0)

# 1. Wake up & Stand Tall
dType.PrintInfo(api, "Hello Kerala Sasthramela!")
dType.SetPTPCmdEx(api, 1, 220.0, 0.0, 90.0, 0.0, 1)
dType.dSleep(500)

# 2. Friendly Waving Motion (Left - Right Pan with end servo rotation)
for wave in range(3):
    dType.SetPTPCmdEx(api, 1, 260.0, -80.0, 70.0, -35.0, 1)
    dType.dSleep(250)
    dType.SetPTPCmdEx(api, 1, 260.0,  80.0, 70.0,  35.0, 1)
    dType.dSleep(250)
    dType.SetProgbar(api, int(20 + (wave * 15)))

# 3. Circular Inspection Scan (Continuous Cartesian Arc)
dType.PrintInfo(api, "Scanning Workspace...")
CENTER_X = 270.0
CENTER_Y = 0.0
RADIUS   = 50.0
SCAN_Z   = 30.0

for deg in range(0, 360, 30):
    rad = math.radians(deg)
    x = CENTER_X + (RADIUS * math.cos(rad))
    y = CENTER_Y + (RADIUS * math.sin(rad))
    dType.SetPTPCmdEx(api, 2, x, y, SCAN_Z, 0.0, 1) # MOVL straight segment
    dType.dSleep(40)

dType.SetProgbar(api, 80)

# 4. Nodding Gesture
for nod in range(2):
    dType.SetPTPCmdEx(api, 1, 260.0, 0.0, 10.0, 0.0, 1)
    dType.dSleep(200)
    dType.SetPTPCmdEx(api, 1, 260.0, 0.0, 80.0, 0.0, 1)
    dType.dSleep(200)

# 5. Return to Rest / Home
dType.SetPTPCmdEx(api, 1, 220.0, 0.0, 50.0, 0.0, 1)
dType.SetProgbar(api, 100)
dType.dSleep(1000)
dType.RestartMagicBox(api)
