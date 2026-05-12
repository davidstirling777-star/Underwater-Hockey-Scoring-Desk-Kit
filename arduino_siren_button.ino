// Arduino Nano ESP32 Siren Button Sketch
// Pin D13 monitoring: LOW = SIREN_ON (repeat every 0.5s), HIGH = SIREN_OFF
// The Arduino Nano ESP32 GPIO pins operate strictly at 3.3V.
// Applying voltages higher than 3.3V to any digital or analog pin will 
// likely damage the microcontroller. The pins are not 5V tolerant.
// All other pins pulled HIGH to prevent floating/noise issues

const int signalPin = 13; // D13 - monitor for LOW (grounded) or HIGH
bool lastSignalState = HIGH; // Assume starting HIGH (not grounded)
unsigned long lastSirenTime = 0; // Track time of last SIREN_ON output
const unsigned long SIREN_INTERVAL = 500; // 500ms = 0.5 seconds

void setup() {
  pinMode(signalPin, INPUT);        // D13 as input (monitors external signal)
  pinMode(LED_BUILTIN, OUTPUT);     // Set the built-in LED as an output
  Serial.begin(9600);               // ESP32 uses 115200 baud, UNO used 9600
  delay(500);                       // Wait for serial to stabilize
  
  // Pull all other GPIO pins HIGH to prevent floating states
  for (int pin = 0; pin < 50; pin++) {
    if (pin != signalPin && pin != LED_BUILTIN) {
      pinMode(pin, OUTPUT);
      digitalWrite(pin, HIGH);
    }
  }
}

void loop() {
  bool signalState = digitalRead(signalPin);
  unsigned long currentTime = millis();

  // D13 went LOW (grounded) - start siren sequence
  if (signalState == LOW && lastSignalState == HIGH) {
    Serial.println("SIREN_ON");
    digitalWrite(LED_BUILTIN, LOW);  // Turn LED off
    lastSirenTime = currentTime;
  }
  
  // D13 is still LOW - repeat SIREN_ON every 0.5 seconds
  if (signalState == LOW && (currentTime - lastSirenTime >= SIREN_INTERVAL)) {
    Serial.println("SIREN_ON");
    lastSirenTime = currentTime;
  }
  
  // D13 went HIGH (no longer grounded) - stop siren
  if (signalState == HIGH && lastSignalState == LOW) {
    Serial.println("SIREN_OFF");
    digitalWrite(LED_BUILTIN, HIGH); // Turn LED on
  }
  
  lastSignalState = signalState;
  delay(10); // 10ms poll for debouncing
}
