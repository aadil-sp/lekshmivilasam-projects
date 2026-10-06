# KERALA STATE SASTHROLSAVAM (SASTHRAMELA) - ROBOTICS & AI
## Intelligent 4-DOF Articulated Robotic Arm with Computer Vision Sorting & Edge MicroPython Control

---

### Project Metadata
- **Category:** Robotics & Artificial Intelligence / Sasthrolsavam
- **Theme:** Automation, Industry 4.0 & AI-Driven Precision Manufacturing
- **Primary Manipulator:** Dobot Magician Lite 4-Axis Articulated Robot Arm
- **Controller Unit:** Dobot Magic Box (ARM Cortex-M4 MicroPython SoC)
- **Computer Vision:** Real-Time HSV Contour Extraction & Perspective Homography Transform
- **End Effectors:** Pneumatic Soft Gripper, Vacuum Suction Cap, Spring Pen Plotter

---

## 1. ABSTRACT
In modern smart manufacturing, high-speed sorting of delicate or hazardous items (electronics, pharmaceuticals, agricultural produce) requires high-precision articulated robotic manipulators capable of autonomous visual identification and trajectory planning.

This project implements an **Intelligent 4-DOF Articulated Robotic Sorting System** using the **Dobot Magician Lite** manipulator and its embedded **Magic Box MicroPython Controller**. A high-resolution vision pipeline performs color segmentation, centroid extraction, and perspective transformation, converting 2D camera pixels $(u, v)$ directly into 3D robot Cartesian coordinates $(X, Y, Z, R)$. 

The system leverages on-board Point-to-Point (PTP: JUMP/MOVL) motion profiles with pneumatic vacuum suction and soft-gripper actuation. Additionally, the Magic Box executes standalone, decentralized MicroPython scripts directly from its internal flash storage, enabling industrial deployment without continuous external PC reliance.

---

## 2. KINEMATICS & MATHEMATICAL FORMULATIONS

### A. Inverse Kinematics (Geometric Decomposition)
For a target Cartesian coordinate $(X, Y, Z)$ and end-effector yaw rotation $R$:
1. **Base Joint Angle ($\theta_1$):**
   $$\theta_1 = \text{atan2}(Y, X)$$
2. **Horizontal Projection ($r$) & Effective Reach:**
   $$r = \sqrt{X^2 + Y^2} - d_{\text{offset}}$$
3. **Rear Arm ($\theta_2$) & Forearm ($\theta_3$) Angles:**
   Using the Law of Cosines on the planar 2-link structure (lengths $L_1, L_2$):
   $$\cos \theta_3 = \frac{r^2 + Z^2 - L_1^2 - L_2^2}{2 L_1 L_2}$$
   $$\theta_2 = \text{atan2}(Z, r) - \text{atan2}(L_2 \sin \theta_3, L_1 + L_2 \cos \theta_3)$$
4. **End-Effector Orientation ($\theta_4$):**
   $$\theta_4 = R - \theta_1$$

### B. Computer Vision Homography Perspective Calibration
- **Transformation Formula:**
  $$\begin{bmatrix} X_{\text{robot}} \\ Y_{\text{robot}} \\ 1 \end{bmatrix} = \mathbf{H} \begin{bmatrix} u_{\text{pixel}} \\ v_{\text{pixel}} \\ 1 \end{bmatrix}$$
  Where $\mathbf{H}$ is the $3 \times 3$ perspective transformation matrix determined via 4-point real-world calibration.

---

## 3. SOFTWARE & MICROPYTHON RUNTIME ARCHITECTURE

The Magic Box controller runs a custom FreeRTOS MicroPython engine exposing the `dType` library:
- `dType.SetPTPCmdEx(api, ptpMode, x, y, z, r, isQueued)`: Dispatches kinematic trajectories.
  - `ptpMode = 0`: JUMP mode (lifts $Z$, travels horizontally, lowers to target).
  - `ptpMode = 1`: MOVJ mode (coordinated joint interpolation).
  - `ptpMode = 2`: MOVL mode (strict Cartesian straight-line linear motion).
- `dType.SetEndEffectorSuctionCupEx(api, enableCtrl, onSuck, isQueued)`: Controls vacuum air pump.
- `dType.SetEndEffectorGripperEx(api, enableCtrl, isGrip, isQueued)`: Drives pneumatic soft gripper.

---

## 4. BILL OF MATERIALS (BOM) & SPECIFICATIONS

| Component | Technical Specification | Function |
| :--- | :--- | :--- |
| **Dobot Magician Lite** | 4-DOF Articulated Arm ($\pm 0.2\text{ mm}$ Repeatability, 250g payload) | Precision Robotic Manipulator |
| **Dobot Magic Box** | ARM Cortex-M4 MicroPython Controller | Motion Planning & I/O Sequencing |
| **End Effector Suite** | Vacuum Suction Cup, Pneumatic Gripper, Writing Pen | Multi-Task Object Manipulation |
| **Vision Sensor** | USB HD CMOS Camera (30 FPS, 1080p) | Color & Object Detection |
| **12V 5A Power Supply** | DC Switch Mode Power Supply | System Power Distribution |

---

## 5. SASTHRAMELA JUDGES VIVA VOCE & TECHNICAL DEFENSE

**Q1: What is the advantage of JUMP motion mode over standard linear interpolation in pick-and-place?**  
*Answer:* JUMP mode automatically lifts the end-effector vertically by a configurable clearance height ($\Delta Z$), traverses horizontally across the workspace above obstacles, and descends vertically. This avoids collisions with neighboring bins and reduces motor stress during fast sorting cycles.

**Q2: How does the system achieve repeatability down to $\pm 0.2\text{ mm}$?**  
*Answer:* The arm employs precision stepper motors paired with high-resolution magnetic rotary encoders, anti-backlash planetary reduction gearboxes, and automated homing limit switches that calibrate zero-offset coordinates upon boot.

**Q3: How does the embedded MicroPython Magic Box benefit industrial IoT workflows?**  
*Answer:* It enables fully autonomous, decentralized operation. Motion routines and logic are flashed directly onto the Magic Box's non-volatile storage, allowing the robot to execute sorting and assembly cycles independently with single-button hardware execution, eliminating host computer dependency.

---
*Kerala State Sasthrolsavam Project Portfolio &bull; Lekshmivilasam Robotics Division*
