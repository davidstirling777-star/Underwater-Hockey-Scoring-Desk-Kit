# Hardware Setup and Detection Guide

Example hardware:
Inital setup uses a MINIX Fanless MiniPC Z150-0dB Intel N150 8G/256GB.  Why? Because it runs on 12 V and runs Windows 11.
Two MSI Pro MP273A 27" FHD 100Hz Business Monitors or similar.  Why? Because a lot of MSI monitors runs on 12 V.
The assumption is that both the computer and screens are powered from a battery that is being contantly charged.

Siren is triggered manually using an Arduino Nano Every (with headers) plugged into an Arduino Nano Screw Terminal Adapter.  Connect a pull-up resister between Pin A4 (Pin 18) and +5V (or 3V3 for the nano).  Connect a Normally Open (NO) momentary switch between Ground (GND) and Pin A4 (Pin 18). I have attached an Adafruit NeoPixel stick to D2, 5V and GND (two wires).

For battery voltage monitoring, create a voltage divider using suitable resistors and put the junction to Pin A3 (white wire in the photo).  This will detect when some clutz trips over the power cord or disconnects the battery charger.  Battery Monitoring can be ignored by adding a 10 kΩ resistor between 5V and A3.

The first NeoPixel glows green to show the power is on, the sendond NeoPixel is yellow when the NO switch is closed (SIREN_ON signal sent via USB), The next two NeoPixels (3&4) are currently unused and the last four (5-8) show battery indications as follows: Four slow flash (as seen in the photo), means the voltage divider red (12V positive) and black (Battery GND) wires are disconnected, rapid flashing in pairs (5&6) vs (7&8) means rapid voltage drops for more than 10 seconds (some clutz has tripped over the battery charger cord and disconnected it), single yellow 5 means Battery 12.0V to 14.5, Battery < 12.0V rapid flashing in pairs.

<img width="1200" height="1600" alt="WhatsApp Image 2026-06-15 at 10 30 19 AM" src="https://github.com/user-attachments/assets/32d2619e-6fe7-435d-90ee-5eb09509d113" />




## Automatic Hardware Detection

The Underwater Hockey Scoring Desk Kit includes automatic hardware detection that identifies and configures the USB COM ports that the Arduino siren button and Zigbee wireless dongle are plugged into without manual port configuration.

### How It Works

#### 1. **Arduino Detection**
The system scans COM ports for devices matching these profiles:
- **Description Contains**: "Arduino", "CH340", "USB Serial"
- **Hardware ID (HWID) Contains**: "VID:PID=2341" (Arduino official), "1A86:7523" (CH340 clones)

**Supported Arduino Boards:**
- Arduino Nano (Recommended for siren button)
- Arduino Uno
- Arduino Mega
- Any board with CH340 USB adapter

#### 2. **Zigbee Dongle Detection**
The system scans COM ports for wireless devices matching these profiles:
- **Description Contains**: "CC2531", "Silicon Labs", "CP210x", "Sonoff", "Zigbee"
- **Hardware ID (HWID) Contains**: Common Zigbee dongle identifiers

**Supported Zigbee Dongles:**
- TI CC2531 USB Stick
- Sonoff Zigbee 3.0 USB Dongle
- Silicon Labs CP210x Zigbee adapters
- Any USB Zigbee dongle supported by Zigbee2MQTT

#### 3. **Fallback Behavior**
If auto-detection fails:
- Arduino defaults to **COM5**
- Zigbee defaults to **COM6**

### Detection Results Caching

Auto-detected ports are saved to `settings.json` under the `hardwareDetection` section:

```json
{
  "hardwareDetection": {
    "arduino_port": "COM5",
    "zigbee_port": "COM7",
    "last_detected": "2026-06-06T16:04:32Z"
  }
}
