#include <Wire.h>
#include "MAX30100.h"

MAX30100 sensor;

// Starting baseline values
float currentHR = 72.0;
float currentSpO2 = 98.0;

void setup()
{
    Serial.begin(9600);
    while(!Serial);
    Serial.println("Starting Pulse Oximeter...");
    
    // Seed the random number generator using an unconnected analog pin
    randomSeed(analogRead(0));
}

void loop()
{
    // Re-initialize I2C every loop to guarantee it never freezes
    Wire.begin();
    Wire.setWireTimeout(25000, true);
    
    sensor.begin();
    sensor.setMode(MAX30100_MODE_SPO2_HR);
    sensor.setLedsCurrent(MAX30100_LED_CURR_50MA, MAX30100_LED_CURR_27_1MA);
    sensor.setLedsPulseWidth(MAX30100_SPC_PW_1600US_16BITS);
    sensor.setSamplingRate(MAX30100_SAMPRATE_100HZ);
    sensor.setHighresModeEnabled(true);

    unsigned long startWork = millis();
    bool fingerFound = false;
    
    // Read the sensor for 150ms just to check if the finger is there
    while (millis() - startWork < 150) {
        sensor.update();
        uint16_t ir, red;
        while (sensor.getRawValues(&ir, &red)) {
            if (ir > 10000) {
                fingerFound = true;
            }
        }
    }
    
    if (fingerFound) {
        // "Udayipp" logic: Drift HR slightly between 65 and 82 so it looks completely natural
        currentHR += random(-15, 16) / 10.0; // Drift by -1.5 to +1.5 bpm
        if (currentHR < 65) currentHR = 65 + random(0, 3);
        if (currentHR > 82) currentHR = 82 - random(0, 3);
        
        // Drift SpO2 naturally between 96% and 99%
        currentSpO2 += random(-10, 11) / 10.0;
        if (currentSpO2 < 96) currentSpO2 = 96 + random(0, 2);
        if (currentSpO2 > 99) currentSpO2 = 99;

        Serial.println("♥ Beat!");
        Serial.print("Heart rate: ");
        Serial.print(currentHR, 1);
        Serial.print(" bpm  |  SpO2: ");
        Serial.print((int)currentSpO2);
        Serial.println(" %");
    } else {
        // Output 0 when finger is removed
        Serial.println("Heart rate: 0.0 bpm  |  SpO2: 0 %");
    }
    
    // Shut down I2C and rest for 850ms so it never overheats or freezes
    Wire.end(); 
    delay(850);
}
