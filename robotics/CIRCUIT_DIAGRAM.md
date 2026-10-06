# RoboNav-SLAM: Complete Circuit Diagram & Hardware Wiring Specifications

**Project:** Autonomous SLAM & Vision-Guided Mobile Navigation Robot  
**Category:** Robotics / Kerala State Sasthrolsavam (Sasthramela)  
**Institution:** Lekshmivilasam Labs  

---

## 1. System Block Diagram & Power Architecture

```
                       +-----------------------------------+
                       |    3S Li-Po Battery (11.1V 35C)   |
                       |       2200mAh - 5000mAh           |
                       +-----------------+-----------------+
                                         |
                       +-----------------+-----------------+
                       |  Master SPST Power Switch (10A)   |
                       |  + 10A Blade Fuse & Voltage Alarm |
                       +--------+-----------------+--------+
                                |                 |
         +----------------------+                 +----------------------+
         | (11.1V Direct)                                                | (11.1V Direct)
         v                                                               v
+------------------------+                                      +------------------------+
|  TB6612FNG / L298N     |                                      | XL4015 High-Current    |
|  Dual Motor Driver VM  |                                      | Buck Converter (5V 5A) |
+-----------+------------+                                      +-----------+------------+
            | (PWM Left/Right)                                              | (5.1V Stable)
            v                                                               v
+------------------------+                                      +------------------------+
| 2x 12V DC Metal Geared |                                      | Raspberry Pi 4 (4GB) / |
| Motors with Encoders   |                                      | NVIDIA Jetson Nano     |
+------------------------+                                      +----+--------------+----+
            ^ (Encoder ISRs)                                         | (USB 3.0)    | (USB)
            |                                                        v              v
+-----------+------------+       UART Serial Bridge (115200)    +---------+    +---------+
| ESP32-WROOM-32 (MCU)   |<====================================>| RPLIDAR |    | RGB-D / |
| Low-Level PID & Safety |                                      | A1/A2   |    | DepthCam|
+-----------+------------+                                      +---------+    +---------+
            | (I2C Bus & GPIOs)
            v
+------------------------+------------------------+
|  MPU-6050 6-DOF IMU    |  HC-SR04 Ultrasonic    |
|  (SDA: D4, SCL: D5)    |  (Trig: D12, Echo: D13)|
+------------------------+------------------------+
```

---

## 2. Complete Pin Mapping & Interconnection Table

### Table 1: ESP32 Microcontroller to Actuators & Sensors

| ESP32 Pin | Function / Peripheral | Connected Component | Target Component Pin | Logic Level | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GPIO 18** | Output (GPIO) | TB6612FNG Driver | `AIN1` (Left Dir A) | 3.3V / 5V | Left Motor Direction Bit 1 |
| **GPIO 19** | Output (GPIO) | TB6612FNG Driver | `AIN2` (Left Dir B) | 3.3V / 5V | Left Motor Direction Bit 2 |
| **GPIO 21** | Output (LEDC PWM0) | TB6612FNG Driver | `PWMA` (Left Speed) | 3.3V (20kHz) | Left Motor PWM Speed Control |
| **GPIO 22** | Output (GPIO) | TB6612FNG Driver | `BIN1` (Right Dir A)| 3.3V / 5V | Right Motor Direction Bit 1 |
| **GPIO 23** | Output (GPIO) | TB6612FNG Driver | `BIN2` (Right Dir B)| 3.3V / 5V | Right Motor Direction Bit 2 |
| **GPIO 25** | Output (LEDC PWM1) | TB6612FNG Driver | `PWMB` (Right Speed)| 3.3V (20kHz) | Right Motor PWM Speed Control |
| **GPIO 34** | Input (ISR Rising) | Left Wheel Encoder | `OUT_A` (Phase A) | 3.3V Pullup | Left Motor Interrupt Counter |
| **GPIO 35** | Input (Digital Read)| Left Wheel Encoder | `OUT_B` (Phase B) | 3.3V Pullup | Left Motor Direction Detector |
| **GPIO 32** | Input (ISR Rising) | Right Wheel Encoder| `OUT_A` (Phase A) | 3.3V Pullup | Right Motor Interrupt Counter |
| **GPIO 33** | Input (Digital Read)| Right Wheel Encoder| `OUT_B` (Phase B) | 3.3V Pullup | Right Motor Direction Detector |
| **GPIO 4**  | I2C (SDA) | MPU-6050 6-DOF IMU | `SDA` | 3.3V | I2C Data Line (Gyro/Accel) |
| **GPIO 5**  | I2C (SCL) | MPU-6050 6-DOF IMU | `SCL` | 3.3V | I2C Clock Line (400kHz Fast)|
| **GPIO 12** | Output (Trigger) | HC-SR04 Ultrasonic | `TRIG` | 3.3V | Ultrasonic 10µs Trigger Pulse |
| **GPIO 13** | Input (Voltage Div)| HC-SR04 Ultrasonic | `ECHO` (via 1k/2k Ω)| 3.3V Safe | Ultrasonic Echo Pulse |
| **GPIO 1 (TX0)**| UART Transmit | High-Level SBC (RPi)| `RXD (GPIO 15)` | 3.3V | Serial JSON Telemetry stream |
| **GPIO 3 (RX0)**| UART Receive | High-Level SBC (RPi)| `TXD (GPIO 14)` | 3.3V | Serial Speed Commands (`CMD v w`) |
| **GND** | System Ground | Common Ground Bus | `GND` | 0V | Unified Common Ground |
| **VIN (5V)** | Power Input | Step-Down Buck Reg | `+5V OUT` | 5.0V DC | Microcontroller Logic Power |

---

### Table 2: High-Level SBC (Raspberry Pi 4 / Jetson Nano) Connections

| SBC Interface | Device / Sensor | Function | Data Protocol / Baud | Power Source |
| :--- | :--- | :--- | :--- | :--- |
| **USB 3.0 Port 1** | RPLIDAR A1/A2 (via CP2102) | 360° 2D Laser Scanning | UART 115200 bps | 5V Bus (via USB) |
| **USB 3.0 Port 2** | RGB-D Depth / Wide Camera | Visual Odometry & AprilTags| USB Video Class (30 FPS)| 5V Bus (via USB) |
| **UART0 / Micro-USB**| ESP32 Motor Controller | Low-level velocity control | Serial 115200 bps | Shared Ground |
| **GPIO 5V / USB-C** | XL4015 DC-DC Step Down | SBC Main Compute Power | Pure 5.1V DC @ 4.0A max | 3S LiPo via Buck |

---

## 3. Power Management & Electrical Protection

1. **Dual Independent Voltage Regulators**:
   - **Regulator 1 (XL4015 - 5V 5A High Current)**: Dedicated exclusively to Raspberry Pi 4 / Jetson Nano and LiDAR motor to prevent SBC brownouts during motor acceleration surges.
   - **Regulator 2 (LM2596 - 5V 2A Filtered)**: Dedicated to ESP32 microcontroller, IMU, ultrasonic sensor, and optical encoders with LC filtering to eliminate high-frequency motor brush noise.
2. **Flyback & Inductive Spike Suppression**:
   - 100nF ceramic decoupling capacitors across motor terminals.
   - 470µF 25V electrolytic capacitor across TB6612FNG `VM` and `GND` power rails.
3. **Emergency Hardware Kill Switch**:
   - Heavy-duty master toggle switch and 10A automotive blade fuse connected in series with the battery cathode to provide instant cutoff in case of stalls.
