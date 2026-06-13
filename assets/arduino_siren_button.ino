// Arduino Every or Nano Siren Button Sketch, using Arduino Screw Terminal Connector
// Add the Adafruit NeoPixel library
// Pin A4 (Pin 18) monitoring: LOW = SIREN_ON (repeat every 0.5s), HIGH = SIREN_OFF
// Connect a pull-up resistor between A4 (Pin 18) and +5V.
// Connect momentary Normally Open (NO) switch between Pin A4 (Pin 18) and Ground (GND).
//
// NeoPixel Stick: 8 LEDs, DIN on D2
//
// Battery monitoring:
// Use voltage divider:
// For Arduino Nano Every:
//   R1 = 10 kΩ from Battery Positive (+) to A3
//   R2 = 3.3 kΩ from A3 to Ground
// Battery negative, Arduino GND, and voltage divider ground must all be common.
// To prevent battery monitoring, add 10 kΩ resistor between 5V and A3.
// Important: only fit this bypass resistor when the battery divider is disconnected.
//
// With R1 = 10k and R2 = 3.3k:
//   15V battery/charger voltage becomes about 3.72V at A3,
//   which is safe for a 5V Arduino Nano Every BUT NOT AN ARDUINO NANO ESP32.
//
// NeoPixel functions:
//   NeoPixel 1: dim green power indicator
//   NeoPixel 2: yellow when siren is active
//   NeoPixels 5-8: battery warning indicators
//
// Battery warning behaviour:
//   If A3 has no voltage: LEDs 5-8 slowly fade red together between brightness 4 and 24.
//   If voltage suddenly drops by more than 0.5V: start 10 second pending timer.
//   If voltage drops below 12.0V: start 10 second pending timer.
//   If voltage returns to 14.5V within 10 seconds: cancel warning.
//   If voltage stays unhappy for 10 seconds: LEDs 5-8 flash red in alternating pairs at about 3Hz.
//   Flashing stops once voltage returns to 14.5V or higher.

#include <Adafruit_NeoPixel.h>

// -------------------------
// Pin setup
// -------------------------

const int signalPin = 18;       // A4 / Pin 18
const int neoPixelPin = 2;      // D2
const int numPixels = 8;
const int batterySensePin = A3;

// -------------------------
// NeoPixel setup
// -------------------------

Adafruit_NeoPixel pixels(numPixels, neoPixelPin, NEO_GRB + NEO_KHZ800);

// -------------------------
// Siren button setup
// -------------------------

unsigned long lastSirenTime = 0;
const unsigned long SIREN_INTERVAL = 500;

bool sirenActive = false;

int debounceCounter = 0;
int releaseDebounceCounter = 0;

const int DEBOUNCE_THRESHOLD = 3;
const int RELEASE_DEBOUNCE_THRESHOLD = 3;

// -------------------------
// Battery voltage divider setup
// -------------------------

const float R1 = 10000.0; // ohms
const float R2 = 3300.0;  // ohms
const float ADC_REF_VOLTAGE = 5.0;

// -------------------------
// Battery warning values
// -------------------------

const float HAPPY_VOLTAGE = 14.5;
const float NOT_HAPPY_VOLTAGE = 12.0;
const float DROP_THRESHOLD = 0.5;
const float NO_VOLTAGE_THRESHOLD = 1.0;

const unsigned long LOW_VOLTAGE_DELAY = 10000;
const unsigned long BATTERY_CHECK_INTERVAL = 100;
const unsigned long BATTERY_FLASH_INTERVAL = 167;

const int NO_VOLTAGE_FADE_TIME = 2000;
const int NO_VOLTAGE_MIN_RED = 1;
const int NO_VOLTAGE_MAX_RED = 32;

const int BATTERY_ADC_SAMPLES = 8;

// -------------------------
// Battery warning state
// -------------------------

float lastVoltage = 0.0;

bool lowVoltagePending = false;
unsigned long lowVoltageStartTime = 0;

bool batteryDropWarning = false;
unsigned long lastBatteryCheckTime = 0;
unsigned long lastBatteryFlashTime = 0;
bool batteryFlashState = false;

bool noVoltageWarning = false;

// -------------------------
// Setup
// -------------------------

void setup() {
  pinMode(signalPin, INPUT);
  pinMode(LED_BUILTIN, OUTPUT);

  Serial.begin(9600);
  delay(500);

  pixels.begin();
  pixels.clear();

  // NeoPixel 1: dim green power-on indicator
  pixels.setPixelColor(0, pixels.Color(0, 16, 0));

  // NeoPixel 2: off until siren is active
  pixels.setPixelColor(1, pixels.Color(0, 0, 0));

  clearBatteryWarningPixels();
  pixels.show();

  lastVoltage = readBatteryVoltage();
}

// -------------------------
// Main loop
// -------------------------

void loop() {
  bool signalState = digitalRead(signalPin);
  unsigned long currentTime = millis();

  // Siren button debounce
  if (signalState == LOW) {
    debounceCounter++;
    releaseDebounceCounter = 0;
  } else {
    debounceCounter = 0;
    releaseDebounceCounter++;
  }

  // Button held LOW long enough: start siren
  if (debounceCounter == DEBOUNCE_THRESHOLD && !sirenActive) {
    Serial.println("SIREN_ON");

    digitalWrite(LED_BUILTIN, HIGH);

    // NeoPixel 2 yellow when built-in LED is ON
    pixels.setPixelColor(1, pixels.Color(204, 204, 0));
    pixels.show();

    lastSirenTime = currentTime;
    sirenActive = true;
  }

  // Button still LOW: repeat SIREN_ON every 0.5 seconds
  if (signalState == LOW && sirenActive && (currentTime - lastSirenTime >= SIREN_INTERVAL)) {
    Serial.println("SIREN_ON");
    lastSirenTime = currentTime;

    // Momentarily pull pin HIGH to verify it is still grounded
    pinMode(signalPin, OUTPUT);
    digitalWrite(signalPin, HIGH);
    delayMicroseconds(100);
    pinMode(signalPin, INPUT);
  }

  // Button released HIGH long enough: stop siren
  if (releaseDebounceCounter == RELEASE_DEBOUNCE_THRESHOLD && sirenActive) {
    Serial.println("SIREN_OFF");

    digitalWrite(LED_BUILTIN, LOW);

    // NeoPixel 2 off when built-in LED is OFF
    pixels.setPixelColor(1, pixels.Color(0, 0, 0));
    pixels.show();

    sirenActive = false;
  }

  checkBatteryVoltage();

  if (noVoltageWarning) {
    updateNoVoltageWarning();
  } else {
    updateBatteryDropWarning();
  }

  delay(10);
}

// -------------------------
// Battery voltage reading
// -------------------------

float readBatteryVoltage() {
  long adcTotal = 0;

  for (int i = 0; i < BATTERY_ADC_SAMPLES; i++) {
    adcTotal += analogRead(batterySensePin);
    delayMicroseconds(300);
  }

  float adcAverage = adcTotal / (float)BATTERY_ADC_SAMPLES;
  float pinVoltage = adcAverage * (ADC_REF_VOLTAGE / 1023.0);
  float actualBatteryV = pinVoltage * ((R1 + R2) / R2);

  return actualBatteryV;
}

// -------------------------
// Battery voltage logic
// -------------------------

void checkBatteryVoltage() {
  unsigned long currentTime = millis();

  if (currentTime - lastBatteryCheckTime < BATTERY_CHECK_INTERVAL) {
    return;
  }

  lastBatteryCheckTime = currentTime;

  float actualBatteryV = readBatteryVoltage();

  // No voltage on A3: use slow fading warning on LEDs 5-8
  if (actualBatteryV < NO_VOLTAGE_THRESHOLD) {
    noVoltageWarning = true;
    batteryDropWarning = false;
    lowVoltagePending = false;
    lastVoltage = actualBatteryV;
    return;
  }

  if (noVoltageWarning) {
    clearBatteryWarningPixels();
    pixels.show();
  }

  noVoltageWarning = false;

  // Sudden voltage drop detected
  if (lastVoltage > 0 && (lastVoltage - actualBatteryV) > DROP_THRESHOLD) {
    lowVoltagePending = true;
    lowVoltageStartTime = currentTime;
  }

  // Battery below not-happy voltage
  if (actualBatteryV < NOT_HAPPY_VOLTAGE && !lowVoltagePending) {
    lowVoltagePending = true;
    lowVoltageStartTime = currentTime;
  }

  // If voltage recovers before 10 seconds, cancel pending warning
  if (lowVoltagePending && actualBatteryV >= HAPPY_VOLTAGE) {
    lowVoltagePending = false;
  }

  // If voltage stays unhappy for 10 seconds, start flashing
  if (lowVoltagePending && (currentTime - lowVoltageStartTime >= LOW_VOLTAGE_DELAY)) {
    batteryDropWarning = true;
    lowVoltagePending = false;
    lastBatteryFlashTime = 0;
    batteryFlashState = false;
  }

  lastVoltage = actualBatteryV;
}

// -------------------------
// Alternating pair battery warning
// -------------------------

void updateBatteryDropWarning() {
  unsigned long currentTime = millis();

  if (!batteryDropWarning) {
    return;
  }

  float actualBatteryV = readBatteryVoltage();

  // Stop flashing once battery voltage has recovered
  if (actualBatteryV >= HAPPY_VOLTAGE) {
    batteryDropWarning = false;
    clearBatteryWarningPixels();
    pixels.show();
    return;
  }

  if (currentTime - lastBatteryFlashTime >= BATTERY_FLASH_INTERVAL) {
    lastBatteryFlashTime = currentTime;
    batteryFlashState = !batteryFlashState;

    if (batteryFlashState) {
      // NeoPixels 7 and 8 red
      pixels.setPixelColor(6, pixels.Color(255, 0, 0));
      pixels.setPixelColor(7, pixels.Color(255, 0, 0));

      // NeoPixels 5 and 6 off
      pixels.setPixelColor(4, pixels.Color(0, 0, 0));
      pixels.setPixelColor(5, pixels.Color(0, 0, 0));
    } else {
      // NeoPixels 5 and 6 red
      pixels.setPixelColor(4, pixels.Color(255, 0, 0));
      pixels.setPixelColor(5, pixels.Color(255, 0, 0));

      // NeoPixels 7 and 8 off
      pixels.setPixelColor(6, pixels.Color(0, 0, 0));
      pixels.setPixelColor(7, pixels.Color(0, 0, 0));
    }

    pixels.show();
  }
}

// -------------------------
// No-voltage slow fade warning
// -------------------------

void updateNoVoltageWarning() {
  unsigned long currentTime = millis();

  unsigned long cycleTime = NO_VOLTAGE_FADE_TIME * 2UL;
  unsigned long position = currentTime % cycleTime;

  int redBrightness;

  if (position < NO_VOLTAGE_FADE_TIME) {
    redBrightness = map(position, 0, NO_VOLTAGE_FADE_TIME, NO_VOLTAGE_MIN_RED, NO_VOLTAGE_MAX_RED);
  } else {
    redBrightness = map(position - NO_VOLTAGE_FADE_TIME, 0, NO_VOLTAGE_FADE_TIME, NO_VOLTAGE_MAX_RED, NO_VOLTAGE_MIN_RED);
  }

  pixels.setPixelColor(4, pixels.Color(redBrightness, 0, 0)); // NeoPixel 5
  pixels.setPixelColor(5, pixels.Color(redBrightness, 0, 0)); // NeoPixel 6
  pixels.setPixelColor(6, pixels.Color(redBrightness, 0, 0)); // NeoPixel 7
  pixels.setPixelColor(7, pixels.Color(redBrightness, 0, 0)); // NeoPixel 8

  pixels.show();
}

// -------------------------
// Utility
// -------------------------

void clearBatteryWarningPixels() {
  pixels.setPixelColor(4, pixels.Color(0, 0, 0)); // NeoPixel 5
  pixels.setPixelColor(5, pixels.Color(0, 0, 0)); // NeoPixel 6
  pixels.setPixelColor(6, pixels.Color(0, 0, 0)); // NeoPixel 7
  pixels.setPixelColor(7, pixels.Color(0, 0, 0)); // NeoPixel 8
}
