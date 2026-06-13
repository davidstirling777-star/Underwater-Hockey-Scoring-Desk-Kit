# Hardware Setup and Detection Guide

Example hardware:
Inital setup uses a MINIX Fanless MiniPC Z150-0dB Intel N150 8G/256GB.  Why? Because it runs on 12 V and runs Windows 11.
Two MSI Pro MP273A 27" FHD 100Hz Business Monitors or similar.  Why? Because a lot of MSI monitors runs on 12 V.
The assumption is that both the computer and screens are powered from a battery that is being contantly charged.

Siren is triggered manually using an Arduino Nano Every (with headers) plugged into an Arduino Nano Screw Terminal Adapter.  Connect a pull-up resister between Pin A4 (Pin 18) and +5V (or 3V3 for the nano).  Connect a Normally Open (NO) momentary switch between Ground (GND) and Pin A4 (Pin 18).

For battery voltage monitoring, create a voltage divider using suitable resistors and put the junction to Pin A3.  This will detect when some clutz trips over the power cord or disconnects the battery charger.  Battery Monitoring can be ignored by adding a 10 kΩ resistor between 5V and A3

<img width="1200" height="1600" alt="WhatsApp Image 2026-06-12 at 4 07 02 PM" src="https://github.com/user-attachments/assets/cc0db17d-c047-429d-967f-7ca70b6f3b27" />



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
