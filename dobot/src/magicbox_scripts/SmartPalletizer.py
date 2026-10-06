#devType: ML
#isUsingRail: False
# =========================================================================================
# DOBOT MAGICIAN LITE - AUTOMATED 2x2 MATRIX PALLETIZER
# Picks parts from feeder and organizes them into a precise 2x2 grid matrix
# =========================================================================================

import dType

api = 0
dType.SetQueuedCmdClear(api)
dType.SetQueuedCmdStopExec(api)
dType.SetQueuedCmdStartExec(api)

# Motion Parameters
dType.SetArmSpeedRatio(api, 1, 45, 1)
dType.SetPTPJumpParams(api, 25.0, 100.0, 1) # 25mm clearance jump
dType.SetLostStepParams(api, 5.0, 0)

# Optional Homing
dType.SetHOMECmd(api, 0, 1)

# Feeder Pick-up Coordinate (Source)
FEEDER_X = 310.0
FEEDER_Y = -110.0
PICK_Z   = -38.0
HOVER_Z  = 20.0

# Pallet Grid Parameters (2x2 Matrix)
GRID_START_X = 260.0
GRID_START_Y = 60.0
SPACING_X    = 40.0
SPACING_Y    = 45.0
PLACE_Z      = -38.0

total_items = 4
dType.SetProgbar(api, 0)

for item_idx in range(total_items):
    row = item_idx // 2
    col = item_idx % 2
    
    # Calculate target drop position
    target_x = GRID_START_X + (row * SPACING_X)
    target_y = GRID_START_Y + (col * SPACING_Y)
    
    # 1. Approach & Pick from Feeder
    dType.SetPTPCmdEx(api, 1, FEEDER_X, FEEDER_Y, HOVER_Z, 0.0, 1)
    dType.SetPTPCmdEx(api, 2, FEEDER_X, FEEDER_Y, PICK_Z, 0.0, 1) # MOVL straight down
    dType.SetEndEffectorSuctionCupEx(api, 1, 1, 1) # Vacuum ON
    dType.dSleep(700)
    dType.SetPTPCmdEx(api, 2, FEEDER_X, FEEDER_Y, HOVER_Z, 0.0, 1) # MOVL straight up

    # 2. Transit & Place in Pallet Matrix Slot (Row, Col)
    dType.SetPTPCmdEx(api, 1, target_x, target_y, HOVER_Z, 0.0, 1)
    dType.SetPTPCmdEx(api, 2, target_x, target_y, PLACE_Z, 0.0, 1) # MOVL down
    dType.SetEndEffectorSuctionCupEx(api, 0, 0, 1) # Vacuum OFF / Blow
    dType.dSleep(500)
    dType.SetPTPCmdEx(api, 2, target_x, target_y, HOVER_Z, 0.0, 1) # MOVL up

    # Update Magic Box Progress
    dType.SetProgbar(api, int((item_idx + 1) * 100 / total_items))
    dType.dSleep(200)

# Return to Safe Standby
dType.SetPTPCmdEx(api, 1, 240.0, 0.0, 50.0, 0.0, 1)
dType.dSleep(1000)
dType.RestartMagicBox(api)
