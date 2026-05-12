// Arduino Nano ESP32 Siren Button Sketch
// Pin D13 monitoring: 3V3 = SIREN_ON (LED off), LOW = SIREN_OFF (LED on)
// The Arduino Nano ESP32 GPIO pins operate strictly at 3.3V.
// Applying voltages higher than 3.3V to any digital or analog pin will 
// likely damage the microcontroller. The pins are not 5V tolerant.
// All other pins pulled HIGH to prevent floating/noise issues

const int signalPin = 13; // D13 - monitor for 3V3 or LOW
bool lastSignalState = LOW; // Assume starting LOW

void setup() {
  pinMode(signalPin, INPUT);        // D13 as input (monitors external 5V signal)
  pinMode(LED_BUILTIN, OUTPUT);     // Set the built-in LED as an output
  Serial.begin(9600);             // ESP32 uses 115200 baud, UNO used 9600
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

  // Signal went HIGH (3V3/5V applied)
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
