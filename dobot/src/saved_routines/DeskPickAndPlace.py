#devType: ML
# =========================================================================================
# DOBOT MAGICIAN LITE - CUSTOM DESK ROUTINE: DeskPickAndPlace.py
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

total_steps = 1
dType.SetProgbar(api, 0)

# Step 1: Action = SUCTION_ON
dType.SetPTPCmdEx(api, 0, 193.7, 274.6, 32.5, 54.8, 1)
dType.SetEndEffectorSuctionCupEx(api, 1, 1, 1)
dType.dSleep(700)
dType.SetProgbar(api, int(1 * 100 / total_steps))

# Return to Standby
dType.SetPTPCmdEx(api, 1, 240.0, 0.0, 50.0, 0.0, 1)
dType.SetEndEffectorSuctionCupEx(api, 0, 0, 1)
dType.SetProgbar(api, 100)
dType.dSleep(1000)
dType.RestartMagicBox(api)
