// Arduino Every or Nano Siren Button Sketch, using Arduino Screw Terminal Connector
// Add the Adafruit NeoPixel library
// Pin A4 (Pin 18) monitoring: LOW = SIREN_ON (repeat every 0.5s), HIGH = SIREN_OFF
// Connect a pull-up resistor between A4 (Pin 18) and +5V.
// Connect momentary Normally Open (NO) switch between Pin A4 (Pin 18) and Ground (GND).
// Sort your own calibration between voltage divider and actual voltage of battery.
//
// NeoPixel Stick: 8 LEDs, DIN on D2
//
// Battery monitoring:
// For Arduino Nano Every:
//   R1 = 10 kΩ from Battery Positive (+) to A3
//   R2 = 3.3 kΩ from A3 to Ground
// Battery negative, Arduino GND, and voltage divider ground must all be common.
//
// NeoPixel functions:
//   NeoPixel 1: dim green power indicator
//   NeoPixel 2: yellow when siren is active
//   NeoPixel 5: green above 13.2V, yellow from 11.9V to 13.2V
//   NeoPixels 5-8: warning indicators
//
// Battery warning behaviour:
//   No battery detected: LEDs 5-8 slow red breathing.
//   Battery > 14.5V: NeoPixel 5 green.
//   Battery 12.0V to 14.5V: NeoPixel 5 yellow.
//   Battery < 12.0V: 10 second delay, then red alternating warning.
//   Sudden voltage drop > 0.5V: 10 second delay, then red alternating warning.
//   Warning stops once voltage returns to 13.2V or higher.

#include <Adafruit_NeoPixel.h>

const int signalPin = 18;
const int neoPixelPin = 2;
const int numPixels = 8;
const int batterySensePin = A3;

Adafruit_NeoPixel pixels(numPixels, neoPixelPin, NEO_GRB + NEO_KHZ800);

unsigned long lastSirenTime = 0;
const unsigned long SIREN_INTERVAL = 500;

bool sirenActive = false;

int debounceCounter = 0;
int releaseDebounceCounter = 0;

const int DEBOUNCE_THRESHOLD = 3;
const int RELEASE_DEBOUNCE_THRESHOLD = 3;

// Battery voltage divider setup
const float R1 = 10000.0; // ohms
const float R2 = 3300.0;  // ohms
const float ADC_REF_VOLTAGE = 5.0;

// Calibration
// Use 1.0 for no correction.
// Sort your own calibration between voltage divider and actual voltage of battery.
// Previous measured correction was 13.0 / 13.6 = 0.956.
const float BATTERY_CALIBRATION = 0.956;

// Battery warning values
const float HAPPY_VOLTAGE = 13.2;  // pick a voltage just above your battery voltage
const float NOT_HAPPY_VOLTAGE = 11.9;
const float DROP_THRESHOLD = 0.5;
const float NO_VOLTAGE_THRESHOLD = 1.0;

const unsigned long LOW_VOLTAGE_DELAY = 10000;
const unsigned long BATTERY_CHECK_INTERVAL = 100;
const unsigned long BATTERY_FLASH_INTERVAL = 167;

const int NO_VOLTAGE_FADE_TIME = 2000;
const int NO_VOLTAGE_MIN_RED = 1;
const int NO_VOLTAGE_MAX_RED = 32;

const int BATTERY_GREEN_BRIGHTNESS = 24;
const int BATTERY_YELLOW_BRIGHTNESS = 24;

const int BATTERY_ADC_SAMPLES = 8;

float lastVoltage = 0.0;

bool lowVoltagePending = false;
unsigned long lowVoltageStartTime = 0;

bool batteryDropWarning = false;
unsigned long lastBatteryCheckTime = 0;
unsigned long lastBatteryFlashTime = 0;
bool batteryFlashState = false;

bool noVoltageWarning = false;

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

void loop() {
  bool signalState = digitalRead(signalPin);
  unsigned long currentTime = millis();

  if (signalState == LOW) {
    debounceCounter++;
    releaseDebounceCounter = 0;
  } else {
    debounceCounter = 0;
    releaseDebounceCounter++;
  }

  if (debounceCounter == DEBOUNCE_THRESHOLD && !sirenActive) {
    Serial.println("SIREN_ON");

    digitalWrite(LED_BUILTIN, HIGH);

    pixels.setPixelColor(1, pixels.Color(204, 204, 0));
    pixels.show();

    lastSirenTime = currentTime;
    sirenActive = true;
  }

  if (signalState == LOW && sirenActive && (currentTime - lastSirenTime >= SIREN_INTERVAL)) {
    Serial.println("SIREN_ON");
    lastSirenTime = currentTime;

    pinMode(signalPin, OUTPUT);
    digitalWrite(signalPin, HIGH);
    delayMicroseconds(100);
    pinMode(signalPin, INPUT);
  }

  if (releaseDebounceCounter == RELEASE_DEBOUNCE_THRESHOLD && sirenActive) {
    Serial.println("SIREN_OFF");

    digitalWrite(LED_BUILTIN, LOW);

    pixels.setPixelColor(1, pixels.Color(0, 0, 0));
    pixels.show();

    sirenActive = false;
  }

  checkBatteryVoltage();

  if (noVoltageWarning) {
    updateNoVoltageWarning();
  } else if (batteryDropWarning) {
    updateBatteryDropWarning();
  } else {
    updateBatteryStatusLED();
  }

  delay(10);
}

float readBatteryVoltage() {
  long adcTotal = 0;

  for (int i = 0; i < BATTERY_ADC_SAMPLES; i++) {
    adcTotal += analogRead(batterySensePin);
    delayMicroseconds(300);
  }

  float adcAverage = adcTotal / (float)BATTERY_ADC_SAMPLES;
  float pinVoltage = adcAverage * (ADC_REF_VOLTAGE / 1023.0);
  float actualBatteryV = pinVoltage * ((R1 + R2) / R2) * BATTERY_CALIBRATION;

  return actualBatteryV;
}

void checkBatteryVoltage() {
  unsigned long currentTime = millis();

  if (currentTime - lastBatteryCheckTime < BATTERY_CHECK_INTERVAL) {
    return;
  }

  lastBatteryCheckTime = currentTime;

  float actualBatteryV = readBatteryVoltage();

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

  if (lastVoltage > 0 && (lastVoltage - actualBatteryV) > DROP_THRESHOLD) {
    lowVoltagePending = true;
    lowVoltageStartTime = currentTime;
  }

  if (actualBatteryV < NOT_HAPPY_VOLTAGE && !lowVoltagePending) {
    lowVoltagePending = true;
    lowVoltageStartTime = currentTime;
  }

  if (lowVoltagePending && actualBatteryV >= HAPPY_VOLTAGE) {
    lowVoltagePending = false;
  }

  if (lowVoltagePending && (currentTime - lowVoltageStartTime >= LOW_VOLTAGE_DELAY)) {
    batteryDropWarning = true;
    lowVoltagePending = false;
    lastBatteryFlashTime = 0;
    batteryFlashState = false;
  }

  lastVoltage = actualBatteryV;
}

void updateBatteryStatusLED() {
  if (noVoltageWarning || batteryDropWarning || lowVoltagePending) {
    return;
  }

  float actualBatteryV = readBatteryVoltage();

  clearBatteryWarningPixels();

  if (actualBatteryV >= HAPPY_VOLTAGE) {
    // NeoPixel 5 green
    pixels.setPixelColor(4, pixels.Color(0, BATTERY_GREEN_BRIGHTNESS, 0));
  } else if (actualBatteryV >= NOT_HAPPY_VOLTAGE) {
    // NeoPixel 5 yellow
    pixels.setPixelColor(4, pixels.Color(BATTERY_YELLOW_BRIGHTNESS, BATTERY_YELLOW_BRIGHTNESS, 0));
  }

  pixels.show();
}

void updateBatteryDropWarning() {
  unsigned long currentTime = millis();

  if (!batteryDropWarning) {
    return;
  }

  float actualBatteryV = readBatteryVoltage();

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
      pixels.setPixelColor(6, pixels.Color(255, 0, 0));
      pixels.setPixelColor(7, pixels.Color(255, 0, 0));

      pixels.setPixelColor(4, pixels.Color(0, 0, 0));
      pixels.setPixelColor(5, pixels.Color(0, 0, 0));
    } else {
      pixels.setPixelColor(4, pixels.Color(255, 0, 0));
      pixels.setPixelColor(5, pixels.Color(255, 0, 0));

      pixels.setPixelColor(6, pixels.Color(0, 0, 0));
      pixels.setPixelColor(7, pixels.Color(0, 0, 0));
    }

    pixels.show();
  }
}

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

  pixels.setPixelColor(4, pixels.Color(redBrightness, 0, 0));
  pixels.setPixelColor(5, pixels.Color(redBrightness, 0, 0));
  pixels.setPixelColor(6, pixels.Color(redBrightness, 0, 0));
  pixels.setPixelColor(7, pixels.Color(redBrightness, 0, 0));

  pixels.show();
}

void clearBatteryWarningPixels() {
  pixels.setPixelColor(4, pixels.Color(0, 0, 0));
  pixels.setPixelColor(5, pixels.Color(0, 0, 0));
  pixels.setPixelColor(6, pixels.Color(0, 0, 0));
  pixels.setPixelColor(7, pixels.Color(0, 0, 0));
}
