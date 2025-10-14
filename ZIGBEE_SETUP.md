# Zigbee2MQTT Wireless Siren Setup Guide

This guide explains how to set up and use the Zigbee2MQTT wireless siren functionality in the Underwater Hockey Scoring Desk Kit.

## Overview

The Zigbee2MQTT wireless siren integration allows Chief Referees to trigger the game siren remotely using Zigbee wireless buttons. This eliminates the need for wired connections between the referee and the scoring desk.

**Platform Support:**
- **Linux (Raspberry Pi)**: Full MQTT support via Zigbee2MQTT (recommended)
- **Windows**: Direct serial communication with Zigbee dongle OR MQTT support

## Prerequisites

### Hardware Requirements
- Raspberry Pi 5 (or compatible system for Linux) OR Windows PC
- Zigbee USB dongle (CC2531, CC2538, CP210x, Silicon Labs, or similar)
- Zigbee button device (compatible with Zigbee2MQTT)
- MQTT broker (optional on Windows when using serial mode)

### Software Requirements

#### For Linux (Raspberry Pi):
- Python 3.12+ with tkinter
- Zigbee2MQTT software
- Mosquitto MQTT broker
- Python libraries: `pip install paho-mqtt pyserial`

#### For Windows:
- Python 3.12+ with tkinter
- Python libraries: `pip install pyserial`
- Optional: MQTT broker (Mosquitto for Windows) and `pip install paho-mqtt`

## Installation Steps

### 1. Install MQTT Broker (Mosquitto)

```bash
# On Raspberry Pi/Debian systems
sudo apt update
sudo apt install mosquitto mosquitto-clients

# Start and enable the service
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# Test the broker
mosquitto_pub -h localhost -t test/topic -m "Hello MQTT"
mosquitto_sub -h localhost -t test/topic
```

### 2. Install Zigbee2MQTT

```bash
# Install Node.js (required for Zigbee2MQTT)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Zigbee2MQTT
sudo mkdir /opt/zigbee2mqtt
sudo chown pi:pi /opt/zigbee2mqtt
cd /opt/zigbee2mqtt

# Download and extract
wget -qO- https://github.com/Koenkk/zigbee2mqtt/archive/refs/tags/1.33.2.tar.gz | tar xz --strip-components=1

# Install dependencies
npm install --production
```

### 3. Configure Zigbee2MQTT

Create configuration file `/opt/zigbee2mqtt/data/configuration.yaml`:

```yaml
# MQTT broker configuration
mqtt:
  base_topic: zigbee2mqtt
  server: 'mqtt://localhost:1883'

# Serial port configuration (adjust for your USB dongle)
serial:
  port: /dev/ttyUSB0
  adapter: zstack

# Enable web interface
frontend:
  port: 8080

# Device configuration
devices:
  # Will be populated when you pair devices

# Advanced settings
advanced:
  log_level: info
  pan_id: 6754
  channel: 11
  network_key: GENERATE
```

### 4. Install Python MQTT Library

```bash
pip install paho-mqtt
```

### 5. Start Zigbee2MQTT

```bash
cd /opt/zigbee2mqtt
npm start
```

The web interface will be available at `http://your-pi-ip:8080`.

## Windows Setup (Serial Communication)

Windows systems can use **direct serial communication** with the Zigbee dongle without requiring Zigbee2MQTT or MQTT broker. This is the simplest method for Windows users.

### 1. Install Python Libraries

```cmd
pip install pyserial
```

Optional (for MQTT fallback):
```cmd
pip install paho-mqtt
```

### 2. Connect Zigbee Dongle

1. Plug your Zigbee USB dongle into a USB port
2. Windows will automatically detect and install drivers
3. Check Device Manager to confirm COM port (e.g., COM3, COM4)
   - Open Device Manager → Ports (COM & LPT)
   - Look for entries containing: CC2531, CC2652, CP210x, Silicon Labs, or similar

### 3. Auto-Detection

The application will automatically:
- Detect available COM ports on startup
- Identify Zigbee dongles by manufacturer/description
- Connect to the detected dongle

**Common Zigbee Dongles Detected:**
- TI CC2531, CC2652, CC2538 (Texas Instruments Zigbee chips)
- CP2102, CP2104, CP210x (Silicon Labs USB-to-serial)
- Silicon Labs devices
- FTDI USB-to-serial adapters
- CH340/CH341 USB-to-serial

### 4. Manual Configuration (Optional)

If auto-detection fails, you can manually specify the COM port in `settings.json`:

```json
{
  "zigbeeSettings": {
    "serial_port": "COM3",
    "serial_baudrate": 115200,
    "serial_timeout": 1.0,
    "use_serial_fallback": true,
    "prefer_mqtt": false
  }
}
```

### 5. Serial Communication Protocol

The controller supports multiple data formats from the Zigbee dongle:

**JSON Format** (recommended):
```json
{"action": "single"}
{"click": "single"}
{"state": "ON"}
```

**Simple Format:**
```
BUTTON_PRESS
BTN:1
```

**Key-Value Format:**
```
action:single device:button1
```

### 6. Sending Siren Commands (Serial)

When using serial mode, the controller can send commands to control a Zigbee siren:

**ON Command:**
```json
{"state": "ON"}
```

**OFF Command:**
```json
{"state": "OFF"}
```

These commands are sent automatically when using the "Test Siren via MQTT" button in serial mode.

### Windows MQTT Setup (Alternative)

If you prefer to use MQTT on Windows (requires Zigbee2MQTT):

1. **Install Mosquitto for Windows:**
   - Download from: https://mosquitto.org/download/
   - Run the installer
   - Start the Mosquitto service

2. **Install Zigbee2MQTT under WSL2:**
   - Install WSL2: `wsl --install`
   - Follow Linux installation steps within WSL2
   - Configure Zigbee2MQTT to connect to Windows MQTT broker: `server: 'mqtt://host.docker.internal:1883'`

3. **Configure Application:**
   - Set `prefer_mqtt: true` in settings.json
   - Configure MQTT broker as `localhost`
   - Follow standard MQTT configuration steps

The application will automatically use MQTT if available and configured.

## Device Pairing

### 1. Put Zigbee2MQTT in Pairing Mode
- Open the web interface at `http://your-pi-ip:8080`
- Click "Permit Join" to enable pairing mode
- Pairing mode stays active for 60 seconds

### 2. Pair Your Button Device
- Press and hold the pairing button on your Zigbee button device
- Follow device-specific pairing instructions
- The device should appear in the Zigbee2MQTT web interface

### 3. Configure Device Name
- In the web interface, rename your button device to something recognizable
- Example: `siren_button` or `referee_button`
- Note this name - you'll need it in the UWH application

## UWH Application Configuration

### 1. Open the Zigbee Siren Tab
- Start the UWH application: `python3 uwh.py`
- Click on the "Zigbee Siren" tab

### 2. Configure Connection Settings

**MQTT Broker:** `localhost` (if running locally)
**Port:** `1883` (default MQTT port)
**Username/Password:** Leave blank if no authentication is configured
**MQTT Topic:** `zigbee2mqtt/+` (monitors all Zigbee2MQTT devices)
**Button Device Names:** Enter device names (comma-separated for multiple buttons, e.g., `siren_button, referee_button_1`)
**Siren Device Name:** Enter the Zigbee siren device name to control (e.g., `zigbee_siren`)

### 3. Test Connection
- Click "Test Connection" to verify MQTT connectivity
- Click "Save Configuration" to store your settings
- Click "Connect" to start monitoring for button presses

### 4. Configuration File Location

All UWH application settings are now stored in a unified `settings.json` file in the application directory. This file contains:

- **soundSettings**: Audio preferences (sound files, volume levels)
- **zigbeeSettings**: MQTT connection and Zigbee device settings
- **gameSettings**: Game timing and rule configuration

The application automatically creates this file with default settings on first run. You can edit it directly or use the application's UI tabs to modify settings. Changes made through the UI are automatically saved to this file.

### 5. Test Siren

The "Test Siren via MQTT" button now supports press-and-hold functionality with continuous sound looping:

- **Press and Hold**: Immediately starts the siren sound in a continuous loop and sends MQTT ON command to the siren device
- **Release**: Stops the siren sound loop immediately and sends MQTT OFF command to stop the siren device

This allows you to:
1. Test the local siren sound playback with continuous looping while the button is held
2. Control a remote Zigbee siren device via MQTT (when connected)
3. Simulate the actual game siren behavior with precise control
4. Stop the siren instantly by releasing the button

**Note**: The local sound will loop continuously while the button is held down, stopping immediately when released. The MQTT commands control the remote Zigbee siren device in parallel.

You can also test wireless triggering by pressing your physical Zigbee button device.

## Sound Configuration

The wireless siren uses the same sound settings as the regular siren:

1. Go to the "Sounds" tab
2. Select your preferred siren sound file
3. Adjust siren volume as needed
4. Adjust Air/Water channel volumes
5. Set the "Number of seconds to play Siren" duration
6. Click "Save Settings"

The wireless siren will automatically use these settings when triggered.

### Zigbee Button Trigger Behavior

When a physical Zigbee button is pressed, the siren behavior is:

- **Single Press/Click Event**: Physical Zigbee buttons send a single event when pressed (action types: "single", "press", "click", "ON")
- **Siren Duration**: The siren plays for the duration configured in the Sounds tab ("Number of seconds to play Siren")
- **No Press-and-Hold**: Physical button triggers do NOT support press-and-hold functionality - they are momentary single events
- **Duration Setting Applies**: The "Number of seconds to play Siren" setting **does** affect Zigbee button triggers

**Example**: If you set "Number of seconds to play Siren" to 2.5 seconds, then pressing a Zigbee button will play the siren sound for 2.5 seconds.

**Important Distinction**: This is different from the "Test Siren via MQTT" button in the UI, which supports press-and-hold for continuous looping. Physical Zigbee buttons use standard Zigbee event protocols and send single momentary events, not continuous press states.

## Troubleshooting

### Connection Issues

**Problem:** "MQTT library not available"
```bash
# Solution: Install the MQTT library
pip install paho-mqtt
```

**Problem:** "Connection test failed"
- Check that Mosquitto is running: `sudo systemctl status mosquitto`
- Verify broker settings (hostname, port, credentials)
- Test with command line: `mosquitto_pub -h localhost -t test -m hello`

**Problem:** "Connection timeout"
- Check firewall settings
- Verify MQTT broker is accessible from the UWH application
- Try connecting to `127.0.0.1` instead of `localhost`

### Device Recognition Issues

**Problem:** Button presses not detected
1. Check device name matches configuration exactly
2. Verify device is paired and online in Zigbee2MQTT web interface
3. Monitor MQTT messages: `mosquitto_sub -h localhost -t zigbee2mqtt/+`
4. Check the Activity Log in the Zigbee Siren tab

**Problem:** Device appears offline
1. Check battery level of wireless button
2. Verify Zigbee network coverage
3. Re-pair the device if necessary

### Audio Issues

**Problem:** Siren doesn't play when button is pressed
1. Test manual siren: Click "Test Siren via MQTT"
2. Check sound file configuration in Sounds tab
3. Verify audio system is working: `aplay /usr/share/sounds/alsa/Front_Left.wav`
4. Check volume levels in Sounds tab

**Problem:** Audio plays but at wrong volume
1. Configure Air/Water channel volumes in Sounds tab
2. Test with regular siren button first
3. Check system audio mixer: `alsamixer`

**Problem:** Siren duration is too short or too long when Zigbee button is pressed
1. Go to the Sounds tab
2. Adjust "Number of seconds to play Siren" setting
3. This setting controls siren playback duration for **both** app-initiated sirens and Zigbee button triggers
4. Click "Save Settings" to apply changes
5. Test with your Zigbee button

**Note:** Physical Zigbee button presses send single momentary events (not press-and-hold). The siren will play for the configured duration each time the button is pressed.

### System Integration Issues

**Problem:** Zigbee2MQTT won't start
1. Check USB dongle connection: `lsusb`
2. Verify serial port permissions: `sudo usermod -a -G dialout $USER`
3. Check Zigbee2MQTT logs: `cd /opt/zigbee2mqtt && npm start`

**Problem:** MQTT broker issues
```bash
# Check status
sudo systemctl status mosquitto

# View logs
sudo journalctl -u mosquitto -f

# Restart service
sudo systemctl restart mosquitto
```

### Windows-Specific Issues

**Problem:** Serial port not detected
1. Check Device Manager for COM port
2. Verify Zigbee dongle is properly connected
3. Update USB drivers if needed
4. Manually specify port in settings.json: `"serial_port": "COM3"`
5. Check application logs for detection details

**Problem:** Serial connection fails
1. Verify correct COM port in Device Manager
2. Close other applications using the COM port (Arduino IDE, PuTTY, etc.)
3. Try different USB port
4. Check baudrate setting (default: 115200)
5. Review error messages in application logs

**Problem:** Button presses not detected (Serial mode)
1. Verify Zigbee dongle is sending data (check application logs)
2. Ensure button is paired with Zigbee dongle firmware
3. Check serial data format matches supported formats (JSON, simple, key-value)
4. Try sending test commands manually using a serial terminal
5. Increase logging level for debugging

**Problem:** MQTT not working on Windows
1. Verify Mosquitto service is running:
   - Open Services (services.msc)
   - Find "Mosquitto Broker" service
   - Ensure it's Running
2. Check firewall settings allow port 1883
3. Test MQTT broker: `mosquitto_pub -h localhost -t test -m "hello"`
4. Verify Zigbee2MQTT is connected (if using WSL2)

**Problem:** Switching between Serial and MQTT
1. Stop the controller before switching modes
2. Update settings.json:
   - `"prefer_mqtt": true` for MQTT priority
   - `"prefer_mqtt": false` for Serial priority
3. Restart the application
4. Check connection status in Zigbee Siren tab

## Advanced Configuration

### Custom MQTT Topics

If using a different MQTT topic structure, modify the configuration:

```json
# In settings.json (under zigbeeSettings section)
{
  "soundSettings": { ... },
  "zigbeeSettings": {
    "mqtt_topic": "my_zigbee/+",
    "siren_button_devices": ["my_button_name"],
    "siren_device_name": "my_siren_device",
    "mqtt_broker": "localhost",
    "mqtt_port": 1883,
    ...
  },
  "gameSettings": { ... }
}
```

The UWH application now uses a unified `settings.json` file that contains all configuration settings:
- **soundSettings**: Audio configuration (volumes, sound files)
- **zigbeeSettings**: MQTT and Zigbee device configuration  
- **gameSettings**: Game timing and rule configuration

You can edit this file directly or use the application's configuration tabs to modify settings.

### Siren Device Control

The application can control a remote Zigbee siren device via MQTT. When you press and hold the "Test Siren via MQTT" button:

**ON Command (Button Press)**
- Topic: `zigbee2mqtt/{siren_device_name}/set`
- Payload: `{"state": "ON"}`
- Local behavior: Starts continuous siren sound loop

**OFF Command (Button Release)**
- Topic: `zigbee2mqtt/{siren_device_name}/set`
- Payload: `{"state": "OFF"}`
- Local behavior: Stops siren sound loop immediately

This is compatible with Sonoff ZBDongle-P and standard Zigbee2MQTT device conventions. Make sure your siren device is paired with Zigbee2MQTT and the device name matches the "Siren Device Name" setting in the UI.

**Note**: The local siren sound now loops continuously while the button is held, providing better feedback and testing capabilities. The loop stops immediately when the button is released.

### Multiple Button Support

The UWH application now supports multiple Zigbee buttons for triggering the wireless siren. This allows multiple referees or officials to have their own button devices.

#### Configuring Multiple Buttons in the UI

1. Open the UWH application and go to the "Zigbee Siren" tab
2. In the "Button Device Names" field, enter multiple device names separated by commas:
   - Example: `siren_button, referee_button_1, referee_button_2`
   - Spaces around commas are automatically trimmed
3. Click "Save Configuration" to store the settings
4. Click "Connect" to start monitoring all configured devices

#### Configuring Multiple Buttons in settings.json

You can also directly edit the `settings.json` file to configure multiple buttons:

```json
{
  "zigbeeSettings": {
    "mqtt_broker": "localhost",
    "mqtt_port": 1883,
    "mqtt_topic": "zigbee2mqtt/+",
    "siren_button_devices": ["siren_button", "referee_button_1", "referee_button_2"],
    "siren_button_device": "siren_button"
  }
}
```

- **siren_button_devices**: Array of device names that can trigger the siren
- **siren_button_device**: Single device name (kept for backward compatibility)

#### Backward Compatibility

The application maintains full backward compatibility with existing single-button configurations:
- Old configurations using `siren_button_device` are automatically migrated to the new list format
- Both old and new configuration formats are supported
- The UI automatically converts between single device strings and comma-separated lists

### Custom Button Actions

Different Zigbee buttons send different event types. Common formats:

```json
{"action": "single"}        # Most common
{"click": "single"}         # Some manufacturers  
{"state": "ON"}            # Simple on/off buttons
{"button": 1, "action": "single"}  # Multi-button devices
```

Modify `_process_button_event()` in `zigbee_siren.py` to handle your specific button format.

### Security Configuration

For production use, enable MQTT authentication:

1. Configure Mosquitto with users:
```bash
sudo mosquitto_passwd -c /etc/mosquitto/passwd uwh_user
sudo nano /etc/mosquitto/conf.d/default.conf
```

2. Add to configuration file:
```
allow_anonymous false
password_file /etc/mosquitto/passwd
```

3. Update UWH configuration with username/password

## Monitoring and Logging

### View Real-time MQTT Messages
```bash
# Monitor all Zigbee2MQTT messages
mosquitto_sub -h localhost -t zigbee2mqtt/+

# Monitor specific device
mosquitto_sub -h localhost -t zigbee2mqtt/siren_button
```

### Application Logs
- Enable logging in Zigbee Siren tab configuration
- View Activity Log in the application
- Python logging goes to console when running `python3 uwh.py`

### System Service Setup

To run as a system service:

1. Create service file `/etc/systemd/system/uwh-scoring.service`:
```ini
[Unit]
Description=UWH Scoring Desk Kit
After=network.target mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Underwater-Hockey-Scoring-Desk-Kit
ExecStart=/usr/bin/python3 uwh.py
Restart=always
Environment=DISPLAY=:0

[Install]
WantedBy=multi-user.target
```

2. Enable and start:
```bash
sudo systemctl enable uwh-scoring
sudo systemctl start uwh-scoring
```

## Support and Maintenance

### Regular Maintenance
- Monitor battery levels of wireless devices
- Keep Zigbee2MQTT updated
- Backup configuration files
- Test wireless connectivity before games

### Performance Tips
- Use 2.4GHz WiFi channel different from Zigbee (11, 15, 20, 25, 26)
- Place Zigbee coordinator away from WiFi router
- Use Zigbee router devices to extend range if needed

### Troubleshooting Commands
```bash
# Test MQTT connectivity
mosquitto_pub -h localhost -t test -m "hello"
mosquitto_sub -h localhost -t test

# Check USB devices
lsusb | grep -i zigbee

# Test Python MQTT
python3 -c "import paho.mqtt.client as mqtt; print('MQTT OK')"

# Check system audio
aplay -l
alsamixer
```

For additional support, check the Activity Log in the Zigbee Siren tab and the Zigbee2MQTT web interface at `http://your-pi:8080`.