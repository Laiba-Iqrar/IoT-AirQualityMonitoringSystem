#include <WiFi.h>
#include <WiFiManager.h>  // https://github.com/tzapu/WiFiManager
#include <ThingSpeak.h>
#include "DHT.h"
#include <otadrive_esp.h>

// OTAdrive configuration
const char* otd_apiKey = "5c7260e6-e141-4ade-80df-b0d3137e5cec";
const char* firmware_version = "1.0.7";

// ThingSpeak settings
unsigned long channelID = 2917545;
const char* apiKey = "SDTBIE6V5HR3C59A";

// MQ-135 Calibration Constants
#define RL 10.0
#define R0 3.6
#define PARA 116.6
#define PARB 2.74

// Sensor pins
#define DHTPIN 4
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);
const int gasSensorPin = 35;
const int rainAnalogPin = 33;
const int rainDigitalPin = 12;

// OTA Status LED
#define OTA_LED 2

WiFiClient client;

void setup() {
  Serial.begin(9600);
  dht.begin();
  pinMode(rainDigitalPin, INPUT_PULLUP);
  pinMode(OTA_LED, OUTPUT);
  digitalWrite(OTA_LED, LOW);

  // Use WiFiManager to handle WiFi connection
  WiFiManager wm;
  Serial.println("Connecting to WiFi using WiFiManager...");
  if (!wm.autoConnect("ESP32-LS", "password123")) {
    Serial.println("Failed to connect to WiFi. Restarting...");
    ESP.restart();
  }
  Serial.println("WiFi connected!");

  // Initialize OTAdrive (version 1.1.33 compatible)
  OTADRIVE.setInfo(otd_apiKey, firmware_version);

  // OTA readiness indicator
  digitalWrite(OTA_LED, HIGH);
  Serial.println("OTA Service Initialized");

  // Initialize ThingSpeak
  ThingSpeak.begin(client);
}

void loop() {
  static unsigned long lastUpload = 0;
  static unsigned long otaCheckTime = 0;

  // OTA LED blink
  digitalWrite(OTA_LED, millis() % 1000 < 100 ? HIGH : LOW);

  // OTA check every 30 sec
  if (millis() - otaCheckTime > 30000) {
    if (OTADRIVE.updateFirmwareInfo().available) {
      Serial.println("New firmware available!");
      OTADRIVE.updateFirmware();
    }
    otaCheckTime = millis();
  }

  // Sensor readings
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  if (isnan(humidity)) humidity = 0;
  if (isnan(temperature)) temperature = 0;

  int gasValue = analogRead(gasSensorPin);
  if (gasValue <= 0) gasValue = 1;
  float voltage = gasValue * (3.3 / 4095.0);
  float rs = (3.3 - voltage) / voltage * RL;
  float ratio = rs / R0;
  float gasConcentration = 10 * (PARA * pow(ratio, -PARB));

  int rainAnalog = analogRead(rainAnalogPin);
  int rainDigital = digitalRead(rainDigitalPin) == LOW ? 1 : 0;

  // Print values to Serial
  Serial.printf("Temp: %.1f°C | Hum: %.1f%% | CO2: %.2f ppm | Rain: %d/%d\n",
                temperature, humidity, gasConcentration, rainAnalog, rainDigital);

  // Upload to ThingSpeak every 20 seconds
  if (millis() - lastUpload > 20000) {
    ThingSpeak.setField(1, temperature);
    ThingSpeak.setField(2, humidity);
    ThingSpeak.setField(3, gasConcentration);
    ThingSpeak.setField(4, rainAnalog);
    ThingSpeak.setField(5, rainDigital);

    int status = ThingSpeak.writeFields(channelID, apiKey);
    Serial.println(status == 200 ? "ThingSpeak OKAYY" : "Upload failed");
    lastUpload = millis();
  }

  delay(1000);
}
