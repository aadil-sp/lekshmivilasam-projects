#include <Wire.h>
#include <math.h>

const int MPU_addr = 0x68;
int16_t AcX, AcY, AcZ, Tmp, GyX, GyY, GyZ;

boolean fallDetected = false;
unsigned long fallStartTime = 0;
boolean isConnected = false;

// Re-usable function to configure the sensor
void initMPU() {
  // Wake up the MPU-6050
  Wire.beginTransmission(MPU_addr);
  Wire.write(0x6B);  
  Wire.write(0);     
  Wire.endTransmission(true);
  
  // Set accelerometer range to +/- 4g
  Wire.beginTransmission(MPU_addr);
  Wire.write(0x1C);  
  Wire.write(0x08);  
  Wire.endTransmission(true);
}

// Function to test if the sensor is actually physically connected on the I2C bus
bool checkConnection() {
  Wire.beginTransmission(MPU_addr);
  return (Wire.endTransmission() == 0);
}

void setup() {
  Serial.begin(9600);
  while(!Serial);
  Wire.begin();
  
  Serial.println("Starting MPU6050 Smart Monitor...");
}

unsigned long lastPrint = 0;

void loop() {
  // 1. Connectivity Check
  bool currentConnection = checkConnection();
  
  if (!currentConnection) {
    if (millis() - lastPrint > 1000) {
       Serial.println("MPU6050 ERROR: Sensor not found! Please check SDA/SCL and Power wiring.");
       lastPrint = millis();
    }
    isConnected = false;
    
    // We exit the loop early here so it doesn't process phantom "0" data and trigger false falls
    return; 
  }
  
  // 2. Auto-Recovery 
  // If it was disconnected and you just plugged it in, we need to wake it back up!
  if (!isConnected) {
    initMPU();
    isConnected = true;
    Serial.println("MPU6050 Connected successfully! Monitoring started...");
    Serial.println("-------------------------------------------------");
  }
  
  // 3. Read the Data safely
  Wire.beginTransmission(MPU_addr);
  Wire.write(0x3B);  
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_addr, 14);  
  
  if (Wire.available() >= 14) {
      AcX = Wire.read()<<8 | Wire.read();  
      AcY = Wire.read()<<8 | Wire.read();  
      AcZ = Wire.read()<<8 | Wire.read();  
      Tmp = Wire.read()<<8 | Wire.read();  
      GyX = Wire.read()<<8 | Wire.read();  
      GyY = Wire.read()<<8 | Wire.read();  
      GyZ = Wire.read()<<8 | Wire.read();  
      
      float ax = AcX / 8192.0;
      float ay = AcY / 8192.0;
      float az = AcZ / 8192.0;

      float magnitude = sqrt((ax*ax) + (ay*ay) + (az*az));

      // --- FALL & SHOCK DETECTION LOGIC ---
      if (magnitude < 0.4) {
        if (!fallDetected) {
           Serial.println(">>> WARNING: FREE FALL DETECTED! (Dropping...) <<<");
           fallDetected = true;
           fallStartTime = millis();
        }
      }
      
      if (fallDetected) {
          if (magnitude > 2.0) {
              Serial.println("!!! MASSIVE IMPACT DETECTED !!! (Hit the ground)");
              fallDetected = false; 
              delay(1000); 
          } else if (millis() - fallStartTime > 1000) {
              fallDetected = false;
          }
      } else if (magnitude > 2.5) {
          Serial.println("!!! SHOCK / BUMP DETECTED !!!");
          delay(500); 
      }

      if (millis() - lastPrint > 500) {
          Serial.print("Accel(g) -> X:"); Serial.print(ax, 2);
          Serial.print(" Y:"); Serial.print(ay, 2);
          Serial.print(" Z:"); Serial.print(az, 2);
          Serial.print(" | Magnitude: "); Serial.print(magnitude, 2);
          Serial.print(" || Gyro -> X:"); Serial.print(GyX);
          Serial.print(" Y:"); Serial.print(GyY);
          Serial.print(" Z:"); Serial.println(GyZ);
          lastPrint = millis();
      }
  }
  
  delay(10); 
}
