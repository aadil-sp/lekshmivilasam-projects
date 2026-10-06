#devType: ML
#isUsingRail: False
# =========================================================================================
# DOBOT MAGICIAN LITE - AUTO HOMING & SERVO UNLOCK CALIBRATOR
# =========================================================================================

import dType
import time

api = 0

# 1. Clear Alarms & Reset Queue
dType.ClearAllAlarmsState(api)
dType.SetQueuedCmdClear(api)
dType.SetQueuedCmdStopExec(api)
dType.SetQueuedCmdStartExec(api)

# 2. Configure Speed & Dynamics
dType.SetArmSpeedRatio(api, 1, 35, 1)
dType.SetPTPJumpParams(api, 20.0, 100.0, 1)
dType.SetLostStepParams(api, 5.0, 1)

# 3. Perform Full Homing Sequence (Calibrates Zero Position)
dType.SetProgbar(api, 10)
home_idx = dType.SetHOMECmd(api, 0, 1)

# Wait for Homing to complete
while True:
    cur_idx = dType.GetQueuedCmdCurrentIndex(api)[0]
    if cur_idx >= home_idx[0]:
        break
    dType.dSleep(200)

dType.SetProgbar(api, 40)
dType.dSleep(500)

# 4. Calibration Wave Motion (Demonstrating all 4 DOFs)
# Point 1: Safe Standby
dType.SetPTPCmdEx(api, 1, 240.0, 0.0, 80.0, 0.0, 1)
dType.SetProgbar(api, 50)
dType.dSleep(400)

# Point 2: Move Forward-Left (+X, -Y)
dType.SetPTPCmdEx(api, 1, 280.0, -80.0, 40.0, -30.0, 1)
dType.SetEndEffectorSuctionCupEx(api, 1, 1, 1) # Test Vacuum ON
dType.SetProgbar(api, 70)
dType.dSleep(600)

# Point 3: Move Forward-Right (+X, +Y)
dType.SetPTPCmdEx(api, 1, 280.0, 80.0, 40.0, 30.0, 1)
dType.SetEndEffectorSuctionCupEx(api, 0, 0, 1) # Test Vacuum OFF
dType.SetProgbar(api, 85)
dType.dSleep(600)

# Point 4: Return to Safe Standby
dType.SetPTPCmdEx(api, 1, 240.0, 0.0, 60.0, 0.0, 1)
dType.SetProgbar(api, 100)
dType.dSleep(1000)

dType.RestartMagicBox(api)
