#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels
#define OLED_RESET    -1 // Reset pin # (or -1 if sharing Arduino reset pin)

// Declaration for an SSD1306 display connected to I2C (SDA, SCL pins)
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

void setup() {
  Serial.begin(9600);
  while(!Serial);
  
  Serial.println("Starting OLED Display Test...");

  // Initialize with the I2C addr 0x3C (for the 128x64 or 128x32 OLED)
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { 
    Serial.println(F("SSD1306 allocation failed. Check wiring or I2C Address (0x3C vs 0x3D)!"));
    for(;;); // Don't proceed, loop forever
  }

  Serial.println("OLED Found! Drawing test sequence...");

  // Clear the internal display buffer
  display.clearDisplay();

  // Draw some static test text
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(F("Initialization..."));
  
  display.setTextSize(2);
  display.setCursor(0, 20);
  display.println(F("OLED WORKS"));

  display.display(); // Push internal buffer to the physical screen
  delay(2000);
}

void loop() {
  // Simple animation to prove the screen is continuously refreshing
  display.clearDisplay();
  
  // Show Arduino uptime
  display.setTextSize(1);
  display.setCursor(15, 5);
  display.print(F("Uptime: "));
  display.print(millis() / 1000);
  display.println(F(" sec"));

  // Draw a pulsing circle animation in the center
  static int radius = 2;
  static int direction = 1;
  
  display.drawCircle(64, 40, radius, SSD1306_WHITE);
  display.drawCircle(64, 40, radius - 1, SSD1306_WHITE); // Make it slightly thicker
  
  radius += direction;
  if (radius > 18 || radius < 2) {
    direction = -direction;
  }

  // Draw a border box
  display.drawRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, SSD1306_WHITE);

  // Push to screen
  display.display();
  delay(40);
}
