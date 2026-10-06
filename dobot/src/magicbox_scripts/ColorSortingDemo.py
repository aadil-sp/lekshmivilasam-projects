#devType: ML
#isUsingRail: False
# =========================================================================================
# DOBOT MAGICIAN LITE - MULTI-BIN COLOR / CATEGORY SORTING DEMO
# Simulates automated sorting from central intake to Left, Center & Right bins
# =========================================================================================

import dType

api = 0
dType.SetQueuedCmdClear(api)
dType.SetQueuedCmdStopExec(api)
dType.SetQueuedCmdStartExec(api)

# Fast Dynamics for Industrial Demonstration
dType.SetArmSpeedRatio(api, 1, 60, 1)
dType.SetPTPJumpParams(api, 30.0, 120.0, 1) # Rapid 30mm Jump clearance
dType.SetLostStepParams(api, 5.0, 0)
dType.SetHOMECmd(api, 0, 1)

# Intake Conveyor / Feed Location
INTAKE_X = 320.0
INTAKE_Y = 0.0
PICK_Z   = -36.0

# 3 Categorized Destination Bins (Left=Red, Center=Green, Right=Blue)
BINS = [
    {"name": "BIN 1 (LEFT)",   "x": 270.0, "y": -120.0, "z": -35.0},
    {"name": "BIN 2 (CENTER)", "x": 330.0, "y":    0.0, "z": -35.0},
    {"name": "BIN 3 (RIGHT)",  "x": 270.0, "y":  120.0, "z": -35.0}
]

total_cycles = len(BINS)
dType.SetProgbar(api, 0)

for idx, b in enumerate(BINS):
    dType.PrintInfo(api, "Sorting -> " + b["name"])

    # 1. JUMP to Intake Point & Pick Object
    dType.SetPTPCmdEx(api, 0, INTAKE_X, INTAKE_Y, PICK_Z, 0.0, 1) # Mode 0: JUMP
    dType.SetEndEffectorSuctionCupEx(api, 1, 1, 1) # Vacuum ON
    dType.dSleep(800)

    # 2. JUMP to Destination Bin & Drop Object
    dType.SetPTPCmdEx(api, 0, b["x"], b["y"], b["z"], 0.0, 1) # Mode 0: JUMP
    dType.SetEndEffectorSuctionCupEx(api, 0, 0, 1) # Vacuum OFF / Blow
    dType.dSleep(500)

    # Update Progress
    dType.SetProgbar(api, int((idx + 1) * 100 / total_cycles))
    dType.dSleep(300)

# Return to Rest Position
dType.SetPTPCmdEx(api, 1, 240.0, 0.0, 50.0, 0.0, 1)
dType.dSleep(1000)
dType.RestartMagicBox(api)
