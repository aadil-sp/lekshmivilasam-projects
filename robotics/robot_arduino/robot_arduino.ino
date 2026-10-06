#define ENA 6
#define IN1 9
#define IN2 10
#define IN3 11
#define IN4 12
#define ENB 5

unsigned long lastCmdTime = 0;

void setup() {
  Serial.begin(115200);
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(ENB, OUTPUT);
  stopMotors();
}

void loop() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    handleCommand(cmd);
    lastCmdTime = millis();
  }
  
  // Watchdog: Stop if no command for 1000ms
  if (millis() - lastCmdTime > 1000) {
    stopMotors();
  }
}

void handleCommand(String cmd) {
  if (cmd.length() == 0) return;
  char type = cmd.charAt(0);
  int speed = 0;
  if (cmd.length() > 1) {
    speed = cmd.substring(1).toInt();
  }
  speed = constrain(speed, 0, 255);

  if (type == 'P') {
    Serial.println("OK");
  } else if (type == 'S') {
    stopMotors();
  } else if (type == 'F') {
    drive(speed, speed, true, true);
  } else if (type == 'B') {
    drive(speed, speed, false, false);
  } else if (type == 'L') {
    drive(speed, speed, false, true); // Left back, Right fwd
  } else if (type == 'R') {
    drive(speed, speed, true, false); // Left fwd, Right back
  } else if (type == 'X') {
    // Differential X<L>,<R> where L and R are -255 to 255
    int commaIdx = cmd.indexOf(',');
    if (commaIdx != -1) {
      int lSpeed = cmd.substring(1, commaIdx).toInt();
      int rSpeed = cmd.substring(commaIdx + 1).toInt();
      bool lFwd = lSpeed >= 0;
      bool rFwd = rSpeed >= 0;
      drive(abs(lSpeed), abs(rSpeed), lFwd, rFwd);
    }
  }
}

void drive(int lSpeed, int rSpeed, bool lFwd, bool rFwd) {
  analogWrite(ENA, constrain(lSpeed, 0, 255));
  analogWrite(ENB, constrain(rSpeed, 0, 255));
  
  digitalWrite(IN1, lFwd ? HIGH : LOW);
  digitalWrite(IN2, lFwd ? LOW : HIGH);
  digitalWrite(IN3, rFwd ? HIGH : LOW);
  digitalWrite(IN4, rFwd ? LOW : HIGH);
}

void stopMotors() {
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}
