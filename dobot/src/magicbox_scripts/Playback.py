#devType: ML
#isUsingRail: False
# =========================================================================================
# DOBOT MAGICIAN LITE - PLAYBACK EXECUTION ENGINE
# Auto-loads and replays waypoint trajectories from Playback.txt with End-Effector Control
# =========================================================================================

import dType

api = 0
dType.SetQueuedCmdClear(api)
dType.SetQueuedCmdStopExec(api)
dType.SetQueuedCmdStartExec(api)

# Configure Speed & Dynamics
dType.SetArmSpeedRatio(api, 1, 50, 1)
dType.SetPTPJumpParams(api, 25.0, 100.0, 1)
dType.SetLostStepParams(api, 5.0, 0)

# Optional Homing on Start
dType.SetHOMECmd(api, 0, 1)

txt_file = 'Playback/Playback.txt'

try:
    with open(txt_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    total_points = len(lines)
    dType.SetProgbar(api, 0)

    for idx, line in enumerate(lines):
        # Format: [X, Y, Z, R, Mode, EffectorType, EffectorState, DelayMs]
        # Example: [250.0, 0.0, 50.0, 0.0, 1, 2, 1, 500]
        line_clean = line.replace('[', '').replace(']', '')
        parts = [float(p.strip()) for p in line_clean.split(',')]
        
        x, y, z, r = parts[0], parts[1], parts[2], parts[3]
        mode = int(parts[4]) if len(parts) > 4 else 1 # 0: JUMP, 1: MOVJ, 2: MOVL
        eff_type = int(parts[5]) if len(parts) > 5 else 0 # 0: None, 1: Gripper, 2: Suction
        eff_state = int(parts[6]) if len(parts) > 6 else 0 # 1: ON/Grip, 0: OFF/Release
        delay_ms = int(parts[7]) if len(parts) > 7 else 100

        # Send Arm Motion Command
        dType.SetPTPCmdEx(api, mode, x, y, z, r, 1)

        # Control End Effector if specified
        if eff_type == 1: # Gripper
            dType.SetEndEffectorGripperEx(api, 1, eff_state)
        elif eff_type == 2: # Suction Cup
            dType.SetEndEffectorSuctionCupEx(api, eff_state, eff_state, 1)

        if delay_ms > 0:
            dType.dSleep(delay_ms)

        dType.SetProgbar(api, int((idx + 1) * 100 / total_points))

    # Return to Safe Standby
    dType.SetPTPCmdEx(api, 1, 240.0, 0.0, 60.0, 0.0, 1)
    dType.SetEndEffectorSuctionCupEx(api, 0, 0, 1)
    dType.SetEndEffectorGripperEx(api, 0, 0)
    dType.SetProgbar(api, 100)
    dType.dSleep(1000)

except Exception as e:
    dType.PrintInfo(api, "Playback Err: " + str(e))

dType.RestartMagicBox(api)
