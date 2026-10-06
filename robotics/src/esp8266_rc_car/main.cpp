#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include "index_html.h"

// ==============================================================================
// L298N MOTOR DRIVER PIN CONFIGURATION (ESP8266 NodeMCU)
// ==============================================================================
// Left Motor (Motor A)
#define ENA_PIN        5   // Board Label: D1 (GPIO 5)  -> PWM Speed Left
#define IN1_PIN        4   // Board Label: D2 (GPIO 4)  -> Direction Left 1
#define IN2_PIN        0   // Board Label: D3 (GPIO 0)  -> Direction Left 2

// Right Motor (Motor B)
#define IN3_PIN        14  // Board Label: D5 (GPIO 14) -> Direction Right 1
#define IN4_PIN        12  // Board Label: D6 (GPIO 12) -> Direction Right 2
#define ENB_PIN        13  // Board Label: D7 (GPIO 13) -> PWM Speed Right

// Status Indicator
#define ONBOARD_LED    2   // Board Label: D4 (GPIO 2, Active LOW)

// ==============================================================================
// OPEN HOTSPOT CONFIGURATION
// ==============================================================================
const char* AP_SSID = "RoboCar-WiFi";

IPAddress apIP(192, 168, 4, 1);
IPAddress netMsk(255, 255, 255, 0);

ESP8266WebServer server(80);

// ==============================================================================
// DRIVE STATE & SAFETY WATCHDOG
// ==============================================================================
char currentDir = 'S';
int currentSpeed = 800; // Default 0-1023 PWM
unsigned long lastCommandTime = 0;
const unsigned long SAFETY_TIMEOUT_MS = 650; // Auto-stop if connection drops

// Function Prototypes
void setMotors(int leftPwm, int rightPwm);
void handleRoot();
void handleDrive();
void handleStatus();

void setup() {
  Serial.begin(115200);
  delay(250);
  Serial.println("\n\n==================================================");
  Serial.println("   ESP8266 + L298N WI-FI RC CAR CONTROLLER        ");
  Serial.println("==================================================");

  // Initialize Motor Pins
  pinMode(ENA_PIN, OUTPUT);
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);
  pinMode(IN3_PIN, OUTPUT);
  pinMode(IN4_PIN, OUTPUT);
  pinMode(ENB_PIN, OUTPUT);
  pinMode(ONBOARD_LED, OUTPUT);

  // Set PWM Frequency for smooth motor driving (1 kHz)
  analogWriteFreq(1000);
  analogWriteRange(1023);

  // Stop Motors initially
  setMotors(0, 0);
  digitalWrite(ONBOARD_LED, HIGH);

  // Start Open Wi-Fi Access Point (Hotspot)
  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(apIP, apIP, netMsk);
  WiFi.softAP(AP_SSID);

  Serial.println(">> Hotspot Created Successfully!");
  Serial.printf(">> Network (SSID): %s (Open - No Password)\n", AP_SSID);
  Serial.print(">> Dashboard Address: http://");
  Serial.println(WiFi.softAPIP());

  // Setup Web Server Routes
  server.on("/", HTTP_GET, handleRoot);
  server.on("/drive", HTTP_GET, handleDrive);
  server.on("/status", HTTP_GET, handleStatus);

  server.begin();
  Serial.println(">> Web Controller Server Running at http://192.168.4.1");
  Serial.println(">> Ready for WASD Keyboard & D-Pad Commands!");
}

void loop() {
  server.handleClient();

  // Safety Watchdog: If no command received within 650ms, auto-stop motors
  if (currentDir != 'S' && (millis() - lastCommandTime > SAFETY_TIMEOUT_MS)) {
    currentDir = 'S';
    setMotors(0, 0);
    digitalWrite(ONBOARD_LED, HIGH);
    Serial.println("[WATCHDOG] Safety Timeout reached. Motors Auto-Braked.");
  }
}

// ==============================================================================
// L298N DUAL MOTOR CONTROLLER ROUTINE
// ==============================================================================
void setMotors(int leftPwm, int rightPwm) {
  // Constrain PWM speeds to valid range (-1023 to 1023)
  leftPwm = constrain(leftPwm, -1023, 1023);
  rightPwm = constrain(rightPwm, -1023, 1023);

  // 1. Control Left Motor (Motor A)
  if (leftPwm > 0) {
    digitalWrite(IN1_PIN, HIGH);
    digitalWrite(IN2_PIN, LOW);
    analogWrite(ENA_PIN, leftPwm);
  } else if (leftPwm < 0) {
    digitalWrite(IN1_PIN, LOW);
    digitalWrite(IN2_PIN, HIGH);
    analogWrite(ENA_PIN, abs(leftPwm));
  } else {
    digitalWrite(IN1_PIN, LOW);
    digitalWrite(IN2_PIN, LOW);
    analogWrite(ENA_PIN, 0);
  }

  // 2. Control Right Motor (Motor B)
  if (rightPwm > 0) {
    digitalWrite(IN3_PIN, HIGH);
    digitalWrite(IN4_PIN, LOW);
    analogWrite(ENB_PIN, rightPwm);
  } else if (rightPwm < 0) {
    digitalWrite(IN3_PIN, LOW);
    digitalWrite(IN4_PIN, HIGH);
    analogWrite(ENB_PIN, abs(rightPwm));
  } else {
    digitalWrite(IN3_PIN, LOW);
    digitalWrite(IN4_PIN, LOW);
    analogWrite(ENB_PIN, 0);
  }
}

// ==============================================================================
// HTTP REQUEST HANDLERS
// ==============================================================================
void handleRoot() {
  server.sendHeader("Cache-Control", "no-cache, no-store, must-revalidate");
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "text/html", INDEX_HTML);
}

void handleDrive() {
  if (server.hasArg("dir")) {
    String dirStr = server.arg("dir");
    char dir = dirStr.charAt(0);

    if (server.hasArg("speed")) {
      currentSpeed = server.arg("speed").toInt();
      currentSpeed = constrain(currentSpeed, 250, 1023);
    }

    currentDir = dir;
    lastCommandTime = millis();
    digitalWrite(ONBOARD_LED, LOW); // Blink active LED

    switch (dir) {
      case 'F': // Forward (Inverted)
        setMotors(-currentSpeed, -currentSpeed);
        Serial.printf("[DRIVE] FORWARD  | Speed: %4d\n", currentSpeed);
        break;

      case 'B': // Backward (Inverted)
        setMotors(currentSpeed, currentSpeed);
        Serial.printf("[DRIVE] REVERSE  | Speed: %4d\n", currentSpeed);
        break;

      case 'L': // Spin Left
        setMotors(-currentSpeed, currentSpeed);
        Serial.printf("[DRIVE] TURN LEFT| Speed: %4d\n", currentSpeed);
        break;

      case 'R': // Spin Right
        setMotors(currentSpeed, -currentSpeed);
        Serial.printf("[DRIVE] TURN RGHT| Speed: %4d\n", currentSpeed);
        break;

      case 'S': // Stop
      default:
        currentDir = 'S';
        setMotors(0, 0);
        digitalWrite(ONBOARD_LED, HIGH);
        Serial.println("[DRIVE] STOPPED");
        break;
    }
  }

  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", "{\"status\":\"OK\",\"dir\":\"" + String(currentDir) + "\"}");
}

void handleStatus() {
  String json = "{";
  json += "\"dir\":\"" + String(currentDir) + "\",";
  json += "\"speed\":" + String(currentSpeed) + ",";
  json += "\"uptime\":" + String(millis() / 1000);
  json += "}";

  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", json);
}
