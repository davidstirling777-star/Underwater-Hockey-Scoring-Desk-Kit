# Hardware Setup and Detection Guide

Example hardware:
Inital setup uses a MINIX Fanless MiniPC Z150-0dB Intel N150 8G/256GB.  Why? Because it runs on 12 V and runs Windows 11.
MSI Pro MP273A 27" FHD 100Hz Business Monitor.  Why? Because it runs on 12 V.

Siren is triggered manually using an Arduino Nano Every (with headers) plugged into an Arduino Nano Screw Terminal Adapter, Solder a pull-up resister between D3 and +5V (or 3V3 for the nano).
<img width="961" height="511" alt="image" src="https://github.com/user-attachments/assets/89c260cd-dcb5-44ee-a6d9-6c9cbf8149fe" />

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
