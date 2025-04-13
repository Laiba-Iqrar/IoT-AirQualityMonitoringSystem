#include <WiFi.h>
#include <ThingSpeak.h>
#include "DHT.h"

const char* ssid = "Iqrar-ZiNetwork-netsol";
const char* password = "iqrar@786";

// ThingSpeak 
unsigned long channelID = 2917545;
const char* apiKey = "write api key";

// DHT22 
#define DHTPIN 4
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// Gas Sensor
const int gasSensorPin = 36; // ESP32's A0 = GPIO36
const int loadResistance = 10000;

// Rain Sensor
const int rainAnalogPin = 34;
const int rainDigitalPin = 14;

WiFiClient client;

void setup() {
  Serial.begin(9600);
  dht.begin();
  pinMode(rainDigitalPin, INPUT);

  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  
  ThingSpeak.begin(client); 
}

void loop() {
  static unsigned long lastUpload = 0;
  delay(2000); // Match DHT22's 2-sec delay

  // Read DHT22
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  if (isnan(humidity)) humidity = 0;
  if (isnan(temperature)) temperature = 0;

  // Read Gas Sensor
  int gasValue = analogRead(gasSensorPin);
  float voltage = gasValue * (3.3 / 4095.0);
  float resistance = loadResistance * (3.3 - voltage) / voltage;
  float gasConcentration = pow(10, ((resistance - 11000.0) / 6000.0));

  // Read Rain Sensor
  int rainAnalog = analogRead(rainAnalogPin);
  int rainDigital = digitalRead(rainDigitalPin) == LOW ? 1 : 0; // 1=Raining

  // Serial Monitor Output
  Serial.print("Temp: "); Serial.print(temperature);
  Serial.print("°C | Hum: "); Serial.print(humidity);
  Serial.print("% | Gas: "); Serial.print(gasConcentration, 2);
  Serial.print(" | Rain AO: "); Serial.print(rainAnalog);
  Serial.print(" | Rain DO: "); Serial.println(rainDigital);

  // Upload to ThingSpeak every 20 seconds
  if (millis() - lastUpload > 20000) {
    // Assign data to ThingSpeak fields
    ThingSpeak.setField(1, temperature);
    ThingSpeak.setField(2, humidity);
    ThingSpeak.setField(3, gasConcentration);
    ThingSpeak.setField(4, rainAnalog);
    ThingSpeak.setField(5, rainDigital);

    // Send data
    int status = ThingSpeak.writeFields(channelID, apiKey);
    if (status == 200) {
      Serial.println("ThingSpeak upload OK!");
    } else {
      Serial.println("Upload failed. Error: " + String(status));
    }
    lastUpload = millis();
  }
}
