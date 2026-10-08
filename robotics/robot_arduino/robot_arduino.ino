/*
 * RoboNav Full Autonomous & Manual Motor Controller
 * Hardware Pin Mapping:
 * - Pin 9  -> IN1 (Left Motor Forward)
 * - Pin 10 -> IN2 (Left Motor Reverse)
 * - Pin 11 -> IN3 (Right Motor Forward)
 * - Pin 12 -> IN4 (Right Motor Reverse)
 * - Pin 13 -> Onboard LED (Active Driving Indicator)
 * 
 * ENA & ENB: 5V Jumpers ON (Full 255 PWM Torque)
 */

#include <Arduino.h>

// Hardware Pin Mapping (Swapped Left <-> Right):
// Left Motor: Pin 10 (Fwd), Pin 9 (Rev)
// Right Motor: Pin 12 (Fwd), Pin 11 (Rev)
#define IN1 10  // Left Fwd
#define IN2 9   // Left Rev
#define IN3 12  // Right Fwd
#define IN4 11  // Right Rev
#define LED_PIN 13

unsigned long lastCmdTime = 0;
const unsigned long WATCHDOG_TIMEOUT_MS = 2000; // 2 seconds safety cutoff

char rxBuf[32];
byte rxPos = 0;

void stopMotors() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  digitalWrite(LED_PIN, LOW);
}

void drive(bool lFwd, bool lActive, bool rFwd, bool rActive) {
  // Left Motor
  if (!lActive) {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
  } else if (lFwd) {
    digitalWrite(IN2, LOW);
    digitalWrite(IN1, HIGH);
  } else {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
  }

  // Right Motor
  if (!rActive) {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, LOW);
  } else if (rFwd) {
    digitalWrite(IN4, LOW);
    digitalWrite(IN3, HIGH);
  } else {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
  }

  digitalWrite(LED_PIN, (lActive || rActive) ? HIGH : LOW);
}

void processCommand(char* cmd) {
  if (cmd[0] == '\0') return;
  lastCmdTime = millis();
  char type = cmd[0];

  if (type == 'P' || type == 'p') {
    Serial.println("OK");
  } else if (type == 'S' || type == 's') {
    stopMotors();
    Serial.println("STOPPED");
  } else if (type == 'F' || type == 'f') {
    drive(true, true, true, true);  // Both FWD
    Serial.println("DRIVE_FWD");
  } else if (type == 'B' || type == 'b') {
    drive(false, true, false, true); // Both REV
    Serial.println("DRIVE_REV");
  } else if (type == 'L' || type == 'l') {
    drive(false, true, true, true);  // Spin Left
    Serial.println("DRIVE_LEFT");
  } else if (type == 'R' || type == 'r') {
    drive(true, true, false, true);  // Spin Right
    Serial.println("DRIVE_RIGHT");
  } else if (type == 'X' || type == 'x') {
    // Differential Steering X<L>,<R>
    char* comma = strchr(cmd, ',');
    if (comma != NULL) {
      *comma = '\0';
      int lSpeed = atoi(cmd + 1);
      int rSpeed = atoi(comma + 1);
      
      bool lActive = abs(lSpeed) > 30;
      bool rActive = abs(rSpeed) > 30;
      bool lFwd = lSpeed >= 0;
      bool rFwd = rSpeed >= 0;

      drive(lFwd, lActive, rFwd, rActive);
      Serial.println("DRIVE_DIFF");
    }
  } else if (type == 'T' || type == 't') {
    // Pin pulse test: T<pin>,<pwm>,<ms>
    char* c1 = strchr(cmd, ',');
    if (c1 != NULL) {
      *c1 = '\0';
      int pin = atoi(cmd + 1);
      char* c2 = strchr(c1 + 1, ',');
      int pwm = 255;
      int dur = 1000;
      if (c2 != NULL) {
        *c2 = '\0';
        pwm = atoi(c1 + 1);
        dur = atoi(c2 + 1);
      } else {
        pwm = atoi(c1 + 1);
      }
      if (pin >= 2 && pin <= 13) {
        pinMode(pin, OUTPUT);
        digitalWrite(pin, pwm > 0 ? HIGH : LOW);
        Serial.print("PULSED_PIN_");
        Serial.println(pin);
        delay(dur);
        digitalWrite(pin, LOW);
      }
    }
  }
}

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(10);
  
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  
  stopMotors();
  lastCmdTime = millis();
  Serial.println("ROBONAV_FULL_READY");
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (rxPos > 0) {
        rxBuf[rxPos] = '\0';
        processCommand(rxBuf);
        rxPos = 0;
      }
    } else {
      if (rxPos < sizeof(rxBuf) - 1) {
        rxBuf[rxPos++] = c;
      }
    }
  }

  // Safety Watchdog
  if (millis() - lastCmdTime > WATCHDOG_TIMEOUT_MS) {
    stopMotors();
  }
}
