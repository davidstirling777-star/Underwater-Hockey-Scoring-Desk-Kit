// Arduino Every or Nano Siren Button Sketch
// Using Arduino Screw Terminal Connector
// Pin A4 (Pin 18) monitoring: LOW = SIREN_ON (repeat every 0.5s), HIGH = SIREN_OFF
// Connect a pull-up resister between A4 (Pin 18) and +5V (or 3V3 for the nano)
// Connect Normally Open (NO) momentary swtich between Pin A4 (Pin 18) and Ground (GND)
// The Arduino Nano ESP32 GPIO pins operate strictly at 3.3V.
// Applying voltages higher than 3.3V to any digital or analog pin will 
// likely damage the Nano microcontroller. The pins are not 5V tolerant.

const int signalPin = 18; // signalPin - monitor for LOW (grounded) or HIGH
bool lastSignalState = HIGH; // Assume starting HIGH (not grounded)
unsigned long lastSirenTime = 0; // Track time of last SIREN_ON output
const unsigned long SIREN_INTERVAL = 500; // 500ms = 0.5 seconds
bool sirenActive = false; // Track if siren is currently active
int debounceCounter = 0; // Track consecutive LOW reads
int releaseDebounceCounter = 0; // Track consecutive HIGH reads
const int DEBOUNCE_THRESHOLD = 3; // Require 3 consecutive LOW reads (~30ms hold time)
const int RELEASE_DEBOUNCE_THRESHOLD = 3; // Require 3 consecutive HIGH reads (~30ms release confirmation)

void setup() {
  pinMode(signalPin, INPUT);        // signalPin as input (monitors external signal)
  pinMode(LED_BUILTIN, OUTPUT);     // Set the built-in LED as an output
  Serial.begin(9600);               // Nano and ESP32 can easily use 115200 baud, UNO used 9600
  delay(500);                       // Wait for serial to stabilize
}

void loop() {
  bool signalState = digitalRead(signalPin);
  unsigned long currentTime = millis();

  // Track debounce counter for LOW state
  if (signalState == LOW) {
    debounceCounter++;
    releaseDebounceCounter = 0; // Reset release counter
  } else {
    debounceCounter = 0; // Reset press counter
    releaseDebounceCounter++;
  }

  // signalPin held LOW long enough - start siren sequence
  if (debounceCounter == DEBOUNCE_THRESHOLD && !sirenActive) {
    Serial.println("SIREN_ON");
    digitalWrite(LED_BUILTIN, HIGH);  // Turn LED on
    lastSirenTime = currentTime;
    sirenActive = true;
  }
  
  // signalPin is still LOW - repeat SIREN_ON every 0.5 seconds
  if (signalState == LOW && sirenActive && (currentTime - lastSirenTime >= SIREN_INTERVAL)) {
    Serial.println("SIREN_ON");
    lastSirenTime = currentTime;
    
    // Momentarily pull pin HIGH to verify it's still grounded
    pinMode(signalPin, OUTPUT);
    digitalWrite(signalPin, HIGH);
    delayMicroseconds(100); // 100 microsecond pulse
    pinMode(signalPin, INPUT); // Switch back to input mode
  }
  
  // signalPin held HIGH long enough - stop siren
  if (releaseDebounceCounter == RELEASE_DEBOUNCE_THRESHOLD && sirenActive) {
    Serial.println("SIREN_OFF");
    digitalWrite(LED_BUILTIN, LOW); // Turn LED off
    sirenActive = false;
  }
  
  delay(10); // 10ms poll for debouncing
}
