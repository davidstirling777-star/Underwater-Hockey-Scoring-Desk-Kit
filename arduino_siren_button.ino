// Arduino Nano ESP32 Siren Button Sketch
// Pin D21 monitoring: 5V = SIREN_ON (LED off), LOW = SIREN_OFF (LED on)

const int signalPin = 21; // D21 - monitor for 5V or LOW
bool lastSignalState = LOW; // Assume starting LOW

void setup() {
  pinMode(signalPin, INPUT);        // D21 as input (monitors external 5V signal)
  pinMode(LED_BUILTIN, OUTPUT);     // Set the built-in LED as an output
  Serial.begin(115200);             // ESP32 uses 115200 baud
  delay(500);                       // Wait for serial to stabilize
}

void loop() {
  bool signalState = digitalRead(signalPin);

  // Signal went HIGH (5V applied)
  if (signalState == HIGH && lastSignalState == LOW) {
    Serial.println("SIREN_ON");
    digitalWrite(LED_BUILTIN, LOW);  // Turn LED off
  }
  // Signal went LOW
  if (signalState == LOW && lastSignalState == HIGH) {
    Serial.println("SIREN_OFF");
    digitalWrite(LED_BUILTIN, HIGH); // Turn LED on
  }
  lastSignalState = signalState;
  delay(10); // 10ms poll for debouncing
}
