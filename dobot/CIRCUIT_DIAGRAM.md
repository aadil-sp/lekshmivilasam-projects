# Hardware Interfaces & Port Schematics

**System:** Dobot Magician Lite Robotic Arm & Magic Box Controller  
**Competition:** Kerala State Sasthrolsavam / Sasthramela (Robotics & AI Category)  

---

## 1. Magic Box Port Mapping & Connectivity

```
                     +------------------------------------+
                     |         DOBOT MAGIC BOX            |
                     |  (MicroPython Cortex-M4 Controller)|
                     +------------------------------------+
                        |       |        |          |
         [12V 5A DC] ---+       |        |          +--- [USB Micro-B / Type-C]
         Power Input            |        |               (PC / Mac Serial VCP)
                                |        |
             +------------------+        +------------------+
             |                                              |
      [Multi-Pin Arm Bus]                          [External Sensor Ports]
      - Stepper / Servo Signals (J1-J4)            - Port 1: Analog / Digital In
      - Pneumatic Air Line Tube                    - Port 2: I2C Sensor Bus
      - End Effector Comm & Power                  - Port 3: UART Serial / ESP32 Link
      - Limit Switches & Optical Encoders          - Port 4: 12V High-Current Output
```

---

## 2. End Effector Wiring & Pneumatic System

| End Effector | Actuation Type | Electrical Interface | Pneumatic Connection |
| :--- | :--- | :--- | :--- |
| **Pneumatic Soft Gripper** | Dual-Action Air Pressure | 2-Pin PWM / Valve Trigger | Dual 4mm PU Air Tubes to Internal Pump |
| **Vacuum Suction Cup** | Negative Air Pressure / Vacuum | 2-Pin Solenoid Valve Trigger | 4mm Vacuum Hose to Air Box |
| **Writing Pen Holder** | Mechanical Spring Suspension | Passive / Fixed Clamp | None |
| **Laser Engraver (Opt)** | 405nm Blue Laser Diode | 12V PWM Modulation | None |

---

## 3. Communication Protocols & Baud Rates
- **USB Serial (VCP)**: 115200 Baud, 8 Data Bits, 1 Stop Bit, No Parity (`/dev/cu.usbmodem549A30D515392`)
- **Protocol**: Dobot Protocol v2 (Hex Packet Framing: `0xAA 0xAA [Len] [ID] [Ctrl] [Params...] [Checksum]`)
- **MicroPython REPL**: Direct Python interactive shell accessible via `screen /dev/tty.usbmodem549A30D515392 115200`.
