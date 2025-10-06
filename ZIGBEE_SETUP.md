# Zigbee2MQTT Wireless Siren Setup Guide

This guide explains how to set up and use the Zigbee2MQTT wireless siren functionality in the Underwater Hockey Scoring Desk Kit.

## Overview

The Zigbee2MQTT wireless siren integration allows Chief Referees to trigger the game siren remotely using Zigbee wireless buttons. This eliminates the need for wired connections between the referee and the scoring desk.

## Prerequisites

### Hardware Requirements
- Raspberry Pi 5 (or compatible system)
- Zigbee USB dongle (CC2531, CC2538, or similar)
- Zigbee button device (compatible with Zigbee2MQTT)
- MQTT broker (can run on the same Pi)

### Software Requirements
- Python 3.12+ with tkinter
- Zigbee2MQTT software
- Mosquitto MQTT broker
- Python MQTT library: `pip install paho-mqtt`

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

The "Test Siren via MQTT" button now supports press-and-hold functionality:

- **Press and Hold**: Immediately starts the siren sound and sends MQTT ON command to the siren device
- **Release**: Sends MQTT OFF command to stop the siren device

This allows you to:
1. Test the local siren sound playback instantly
2. Control a remote Zigbee siren device via MQTT (when connected)
3. Simulate the actual game siren behavior with precise control

**Note**: The local sound will play as long as the audio file duration. The MQTT commands control the remote Zigbee siren device.

You can also test wireless triggering by pressing your physical Zigbee button device.

## Sound Configuration

The wireless siren uses the same sound settings as the regular siren:

1. Go to the "Sounds" tab
2. Select your preferred siren sound file
3. Adjust siren volume as needed
4. Adjust Air/Water channel volumes
5. Click "Save Settings"

The wireless siren will automatically use these settings when triggered.

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

The application can control a remote Zigbee siren device via MQTT. When you press the "Test Siren via MQTT" button:

**ON Command (Button Press)**
- Topic: `zigbee2mqtt/{siren_device_name}/set`
- Payload: `{"state": "ON"}`

**OFF Command (Button Release)**
- Topic: `zigbee2mqtt/{siren_device_name}/set`
- Payload: `{"state": "OFF"}`

This is compatible with Sonoff ZBDongle-P and standard Zigbee2MQTT device conventions. Make sure your siren device is paired with Zigbee2MQTT and the device name matches the "Siren Device Name" setting in the UI.

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