#devType: ML
#isUsingRail: False
# =========================================================================================
# DOBOT MAGICIAN LITE - PRECISION 5-POINT STAR PEN DRAWING
# Demonstrates pen up/down and continuous Cartesian geometric line drawing
# =========================================================================================

import dType
import math

api = 0
dType.SetQueuedCmdClear(api)
dType.SetQueuedCmdStopExec(api)
dType.SetQueuedCmdStartExec(api)

# Precise Drawing Speed
dType.SetArmSpeedRatio(api, 1, 35, 1)
dType.SetHOMECmd(api, 0, 1)

# Drawing Surface Heights
PEN_UP_Z   = 10.0   # Safe clearance height
PEN_DOWN_Z = -42.0  # Pen contact drawing height

CENTER_X = 280.0
CENTER_Y = 0.0
OUTER_R  = 45.0
INNER_R  = 20.0

# Generate 5-Point Star Vertices
points = []
for i in range(10):
    r = OUTER_R if (i % 2 == 0) else INNER_R
    angle_deg = i * 36 - 90 # Start pointing top
    rad = math.radians(angle_deg)
    px = CENTER_X + (r * math.cos(rad))
    py = CENTER_Y + (r * math.sin(rad))
    points.append((px, py))

# Close the polygon
points.append(points[0])

dType.SetProgbar(api, 0)
total_steps = len(points)

# 1. Move above the starting vertex
dType.SetPTPCmdEx(api, 1, points[0][0], points[0][1], PEN_UP_Z, 0.0, 1)
dType.dSleep(400)

# 2. Lower pen to paper
dType.SetPTPCmdEx(api, 2, points[0][0], points[0][1], PEN_DOWN_Z, 0.0, 1)
dType.dSleep(200)

# 3. Draw star perimeter
for idx, pt in enumerate(points[1:], start=1):
    dType.SetPTPCmdEx(api, 2, pt[0], pt[1], PEN_DOWN_Z, 0.0, 1) # MOVL linear stroke
    dType.dSleep(100)
    dType.SetProgbar(api, int(idx * 100 / total_steps))

# 4. Lift pen and return to standby
dType.SetPTPCmdEx(api, 2, points[-1][0], points[-1][1], PEN_UP_Z, 0.0, 1)
dType.dSleep(300)
dType.SetPTPCmdEx(api, 1, 220.0, 0.0, 50.0, 0.0, 1)
dType.SetProgbar(api, 100)
dType.dSleep(1000)
dType.RestartMagicBox(api)
