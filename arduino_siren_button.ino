// Arduino Nano Every Siren Button Sketch
// NO/COM waterproof button: COM to GND, NO to D2 (or change pin below)

const int buttonPin = 2; // Adjust to your wiring (D2 default)
bool lastButtonState = HIGH; // Assume not pressed (INPUT_PULLUP)

void setup() {
  pinMode(buttonPin, INPUT_PULLUP); // NO/COM: COM to GND, NO to pin
  Serial.begin(9600);
}

void loop() {
  bool buttonState = digitalRead(buttonPin);

  // Button pressed (LOW when pressed)
  if (buttonState == LOW && lastButtonState == HIGH) {
    Serial.println("SIREN_ON");
  }
  // Button released
  if (buttonState == HIGH && lastButtonState == LOW) {
    Serial.println("SIREN_OFF");
  }
  lastButtonState = buttonState;
  delay(10); // 10ms poll, no debounce needed
}