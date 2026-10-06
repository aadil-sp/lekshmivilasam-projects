/*
  =============================================================================
  RoboNav-SLAM: Differential Drive Low-Level Motor & Sensor Controller
  Kerala State Sasthrolsavam (Robotics Exhibition) - Lekshmivilasam Labs
  
  Target Microcontroller: ESP32-WROOM-32 (Dual Core 240MHz)
  Features:
   - High-speed Quadrature Encoder Interrupts (Left & Right Wheels)
   - Dual PID Velocity Control Loop @ 50 Hz (Target RPM vs Measured RPM)
   - TB6612FNG / L298N Motor Driver PWM Signal Generation (LEDC Hardware Timers)
   - MPU6050 6-DOF IMU Reading via I2C (Roll, Pitch, Yaw-rate gyroscope)
   - Ultrasonic Fail-safe Collision Watchdog
   - Serial Communication Protocol (JSON & Micro-ROS Compatible)
  =============================================================================
*/

#include <Arduino.h>
#include <Wire.h>

// --- PIN DEFINITIONS ---
// Left Motor (Motor A)
#define PIN_IN1_L     18
#define PIN_IN2_L     19
#define PIN_PWM_L     21
#define PIN_ENC_A_L   34 // Quadrature Encoder A (Interrupt)
#define PIN_ENC_B_L   35 // Quadrature Encoder B

// Right Motor (Motor B)
#define PIN_IN3_R     22
#define PIN_IN4_R     23
#define PIN_PWM_R     25
#define PIN_ENC_A_R   32 // Quadrature Encoder A (Interrupt)
#define PIN_ENC_B_R   33 // Quadrature Encoder B

// Ultrasonic Front Collision Sensor (Fail-Safe)
#define PIN_TRIG      12
#define PIN_ECHO      13

// MPU6050 I2C Pins (Default ESP32 SDA: 21, SCL: 22 - remapped to 4, 5 for clean bus)
#define PIN_SDA       4
#define PIN_SCL       5
#define MPU6050_ADDR  0x68

// --- PWM CONFIGURATION (ESP32 LEDC) ---
#define PWM_FREQ      20000 // 20 kHz Ultrasonic Frequency (prevents motor whine)
#define PWM_RES       8     // 8-bit resolution (0 - 255)
#define PWM_CH_L      0
#define PWM_CH_R      1

// --- ROBOT PHYSICAL SPECIFICATIONS ---
const float WHEEL_DIAMETER_METERS = 0.065; // 65mm Wheel
const float WHEEL_BASE_METERS     = 0.160; // 160mm Track Width
const int   TICKS_PER_REVOLUTION  = 330;   // 11 CPR * 30:1 Gear Ratio = 330 ticks

// --- ENCODER TICK COUNTERS (Atomic volatile variables) ---
volatile long leftEncoderTicks  = 0;
volatile long rightEncoderTicks = 0;

// Interrupt Service Routines
void IRAM_ATTR isrLeftEncoder() {
  int b = digitalRead(PIN_ENC_B_L);
  if (b > 0) {
    leftEncoderTicks++;
  } else {
    leftEncoderTicks--;
  }
}

void IRAM_ATTR isrRightEncoder() {
  int b = digitalRead(PIN_ENC_B_R);
  if (b > 0) {
    rightEncoderTicks--;
  } else {
    rightEncoderTicks++;
  }
}

// --- PID CONTROLLER STRUCTURE ---
struct PIDController {
  float kp;
  float ki;
  float kd;
  float target;
  float current;
  float integral;
  float prevError;
  float output;
  float minOut;
  float maxOut;

  void init(float p, float i, float d, float minVal, float maxVal) {
    kp = p; ki = i; kd = d;
    minOut = minVal; maxOut = maxVal;
    integral = 0; prevError = 0; target = 0;
  }

  float compute(float setpoint, float measured, float dt) {
    target = setpoint;
    current = measured;
    float error = target - current;
    
    integral += error * dt;
    // Anti-windup clamping
    if (integral > 100) integral = 100;
    if (integral < -100) integral = -100;

    float derivative = (error - prevError) / dt;
    prevError = error;

    output = (kp * error) + (ki * integral) + (kd * derivative);
    if (output > maxOut) output = maxOut;
    if (output < minOut) output = minOut;
    return output;
  }
};

PIDController pidLeft;
PIDController pidRight;

// --- TARGET VELOCITIES (from High-Level SBC / ROS2 via Serial) ---
float targetLinearVel  = 0.0; // m/s
float targetAngularVel = 0.0; // rad/s
unsigned long lastCmdTimestamp = 0;
const unsigned long CMD_TIMEOUT_MS = 600; // Emergency Stop if no packet received in 600ms

// --- MPU6050 GYRO / ACCEL DATA ---
int16_t rawGyroZ = 0;
float gyroZ_dps = 0.0;
float gyroZ_offset = 0.0;

void initMPU6050() {
  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x6B); // PWR_MGMT_1 register
  Wire.write(0x00); // Wake up MPU-6050
  Wire.endTransmission(true);

  // Calibrate Gyro Z offset
  long sum = 0;
  for (int i = 0; i < 200; i++) {
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(0x47); // GYRO_ZOUT_H
    Wire.endTransmission(false);
    Wire.requestFrom(MPU6050_ADDR, 2, true);
    if (Wire.available() >= 2) {
      int16_t gz = (Wire.read() << 8) | Wire.read();
      sum += gz;
    }
    delay(2);
  }
  gyroZ_offset = (float)sum / 200.0;
}

void readMPU6050() {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x47); // GYRO_ZOUT_H
  Wire.endTransmission(false);
  Wire.requestFrom(MPU6050_ADDR, 2, true);
  if (Wire.available() >= 2) {
    rawGyroZ = (Wire.read() << 8) | Wire.read();
    gyroZ_dps = ((float)rawGyroZ - gyroZ_offset) / 131.0; // 131 LSB/(deg/s) for +/-250 dps range
  }
}

// Ultrasonic Range Check
float readUltrasonicDistanceCM() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  long duration = pulseIn(PIN_ECHO, HIGH, 20000); // 20ms timeout
  if (duration == 0) return 999.0;
  return (float)duration * 0.0343 / 2.0;
}

// Set Motor Direction & PWM Speed
void setMotorOutputs(float pwmLeft, float pwmRight) {
  // Left Motor
  if (pwmLeft > 0) {
    digitalWrite(PIN_IN1_L, HIGH);
    digitalWrite(PIN_IN2_L, LOW);
    ledcWrite(PWM_CH_L, (uint32_t)min(255.0f, abs(pwmLeft)));
  } else if (pwmLeft < 0) {
    digitalWrite(PIN_IN1_L, LOW);
    digitalWrite(PIN_IN2_L, HIGH);
    ledcWrite(PWM_CH_L, (uint32_t)min(255.0f, abs(pwmLeft)));
  } else {
    digitalWrite(PIN_IN1_L, LOW);
    digitalWrite(PIN_IN2_L, LOW);
    ledcWrite(PWM_CH_L, 0);
  }

  // Right Motor
  if (pwmRight > 0) {
    digitalWrite(PIN_IN3_R, HIGH);
    digitalWrite(PIN_IN4_R, LOW);
    ledcWrite(PWM_CH_R, (uint32_t)min(255.0f, abs(pwmRight)));
  } else if (pwmRight < 0) {
    digitalWrite(PIN_IN3_R, LOW);
    digitalWrite(PIN_IN4_R, HIGH);
    ledcWrite(PWM_CH_R, (uint32_t)min(255.0f, abs(pwmRight)));
  } else {
    digitalWrite(PIN_IN3_R, LOW);
    digitalWrite(PIN_IN4_R, LOW);
    ledcWrite(PWM_CH_R, 0);
  }
}

// Parse Incoming Serial Commands: e.g. "CMD v omega\n"
void processSerialCommands() {
  while (Serial.available() > 0) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("CMD")) {
      int firstSpace = line.indexOf(' ');
      int secondSpace = line.indexOf(' ', firstSpace + 1);
      if (firstSpace > 0 && secondSpace > 0) {
        targetLinearVel = line.substring(firstSpace + 1, secondSpace).toFloat();
        targetAngularVel = line.substring(secondSpace + 1).toFloat();
        lastCmdTimestamp = millis();
      }
    } else if (line == "PING") {
      Serial.println("PONG:ROBONAV_ESP32_OK");
    } else if (line == "RESET_ENC") {
      noInterrupts();
      leftEncoderTicks = 0;
      rightEncoderTicks = 0;
      interrupts();
      Serial.println("ENC_RESET_OK");
    }
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 1000);

  // Motor Driver Direction Pins
  pinMode(PIN_IN1_L, OUTPUT);
  pinMode(PIN_IN2_L, OUTPUT);
  pinMode(PIN_IN3_R, OUTPUT);
  pinMode(PIN_IN4_R, OUTPUT);

  // Ultrasonic Pins
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);

  // Encoder Pins with internal pullups
  pinMode(PIN_ENC_A_L, INPUT_PULLUP);
  pinMode(PIN_ENC_B_L, INPUT_PULLUP);
  pinMode(PIN_ENC_A_R, INPUT_PULLUP);
  pinMode(PIN_ENC_B_R, INPUT_PULLUP);

  // Attach Hardware Interrupts
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_A_L), isrLeftEncoder, RISING);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_A_R), isrRightEncoder, RISING);

  // Setup ESP32 PWM Timers
  ledcSetup(PWM_CH_L, PWM_FREQ, PWM_RES);
  ledcSetup(PWM_CH_R, PWM_FREQ, PWM_RES);
  ledcAttachPin(PIN_PWM_L, PWM_CH_L);
  ledcAttachPin(PIN_PWM_R, PWM_CH_R);

  // Initialize PID Controllers
  // Tuned parameters: Kp=2.2, Ki=0.45, Kd=0.08
  pidLeft.init(2.2, 0.45, 0.08, -255.0, 255.0);
  pidRight.init(2.2, 0.45, 0.08, -255.0, 255.0);

  // Initialize IMU
  initMPU6050();

  Serial.println("{\"status\":\"INITIALIZED\",\"device\":\"RoboNav-SLAM ESP32 Controller\"}");
}

// 50Hz (20ms) Control Loop Timing
unsigned long prevLoopTime = 0;
long prevLeftTicks = 0;
long prevRightTicks = 0;

void loop() {
  unsigned long currentTime = millis();
  float dt = (currentTime - prevLoopTime) / 1000.0;

  // Process incoming speed commands
  processSerialCommands();

  // 50Hz Periodic PID Control Execution
  if (dt >= 0.020) { // 20ms = 50Hz
    prevLoopTime = currentTime;

    // Read Encoders Atomically
    noInterrupts();
    long curLeftTicks = leftEncoderTicks;
    long curRightTicks = rightEncoderTicks;
    interrupts();

    long dLeftTicks = curLeftTicks - prevLeftTicks;
    long dRightTicks = curRightTicks - prevRightTicks;
    prevLeftTicks = curLeftTicks;
    prevRightTicks = curRightTicks;

    // Calculate Measured Wheel Speeds (m/s)
    float distPerTick = (PI * WHEEL_DIAMETER_METERS) / (float)TICKS_PER_REVOLUTION;
    float measVLeft  = (dLeftTicks * distPerTick) / dt;
    float measVRight = (dRightTicks * distPerTick) / dt;

    // Read IMU Gyroscope
    readMPU6050();

    // Check Ultrasonic Fail-safe (Emergency Stop if obstacle < 12cm)
    float frontDist = readUltrasonicDistanceCM();
    bool safetyEmergency = (frontDist < 12.0 && targetLinearVel > 0);

    // Watchdog Timeout (stop robot if no command received)
    if (millis() - lastCmdTimestamp > CMD_TIMEOUT_MS || safetyEmergency) {
      targetLinearVel = 0;
      targetAngularVel = 0;
    }

    // Kinematic Inverse Model: Differential Drive
    // v_l = v - (omega * L / 2)
    // v_r = v + (omega * L / 2)
    float desVLeft  = targetLinearVel - (targetAngularVel * WHEEL_BASE_METERS / 2.0);
    float desVRight = targetLinearVel + (targetAngularVel * WHEEL_BASE_METERS / 2.0);

    // Convert desired m/s to target RPM scale
    float pwmL = (desVLeft == 0) ? 0 : pidLeft.compute(desVLeft, measVLeft, dt);
    float pwmR = (desVRight == 0) ? 0 : pidRight.compute(desVRight, measVRight, dt);

    // Feedforward booster to overcome static friction
    if (desVLeft > 0.02) pwmL += 25;
    else if (desVLeft < -0.02) pwmL -= 25;
    if (desVRight > 0.02) pwmR += 25;
    else if (desVRight < -0.02) pwmR -= 25;

    // Apply motor PWMs
    setMotorOutputs(pwmL, pwmR);

    // Send Telemetry JSON back to SBC / ROS2
    // FORMAT: TELEM left_ticks right_ticks meas_vl meas_vr gyro_z_dps front_dist_cm
    Serial.print("TELEM ");
    Serial.print(curLeftTicks); Serial.print(" ");
    Serial.print(curRightTicks); Serial.print(" ");
    Serial.print(measVLeft, 3); Serial.print(" ");
    Serial.print(measVRight, 3); Serial.print(" ");
    Serial.print(gyroZ_dps, 2); Serial.print(" ");
    Serial.println(frontDist, 1);
  }
}
