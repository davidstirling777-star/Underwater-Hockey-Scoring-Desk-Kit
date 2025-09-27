# Zigbee Siren Integration

This document describes the Zigbee2MQTT button integration for wireless siren control in the Underwater Hockey Scoring Desk Kit.

## Overview

The Zigbee siren integration allows wireless control of the siren using Zigbee buttons through a Zigbee2MQTT bridge. This enables the chief referee to activate the siren remotely without being tethered to the scoring desk.

## Components

### 1. `zigbee_siren.py` Module
- Standalone MQTT client for Zigbee2MQTT integration
- Handles button press/release events
- Provides connection status monitoring
- Thread-safe operation with callback system
- Graceful fallback when dependencies unavailable

### 2. "Zigbee Siren" Tab
- Real-time connection status display
- Button state monitoring
- Manual siren testing controls
- Activity logging with timestamps
- Start/stop Zigbee controller

## Dependencies

### Required
- `paho-mqtt` - MQTT client library
  ```bash
  pip install paho-mqtt
  ```

### Hardware Requirements
- MQTT broker (Mosquitto recommended)
- Zigbee2MQTT bridge
- Compatible Zigbee button device

## Configuration

### Default Settings
- **MQTT Broker**: `localhost:1883`
- **Zigbee2MQTT Topic**: `zigbee2mqtt`
- **Button Device Name**: `siren_button`

### Customization
Modify the ZigbeeSirenController initialization in `uwh.py`:
```python
self.zigbee_siren = ZigbeeSirenController(
    mqtt_broker="your_broker_ip",
    mqtt_port=1883,
    button_device_name="your_button_name"
)
```

## Usage

### Setup
1. Install and configure Zigbee2MQTT
2. Pair your Zigbee button with device name `siren_button`
3. Install paho-mqtt: `pip install paho-mqtt`
4. Start the application

### Operation
1. Open the "Zigbee Siren" tab
2. Click "Start Zigbee Controller" 
3. Verify "Connected" status appears
4. Press and hold the Zigbee button to activate siren
5. Release button to deactivate siren

### Manual Testing
- Use "Test Siren" button for manual testing
- Check activity log for event monitoring
- Connection status updates automatically

## Features

### ✅ Implemented
- Real-time MQTT connection monitoring
- Button press/release detection
- Continuous siren while button held
- Manual siren testing
- Activity logging
- Graceful degradation without dependencies
- Thread-safe operation
- Non-interfering with existing functionality

### Button Event Handling
The integration handles various Zigbee button payload formats:
- `action`: `single`, `hold`, `press`, `on`, `release`, `off`
- `click`: `single`, `hold`
- `state`: `ON`, `OFF`, `true`, `false`, `1`, `0`

## Troubleshooting

### Common Issues

**"paho-mqtt not available"**
- Install with: `pip install paho-mqtt`

**"Connection refused"**
- Verify MQTT broker is running
- Check broker IP/port configuration
- Ensure firewall allows MQTT traffic

**"Button not responding"**
- Verify button is paired in Zigbee2MQTT
- Check device name matches configuration
- Monitor Zigbee2MQTT logs for button events

**Siren not playing**
- Verify sound files exist in application directory
- Check volume settings in Sounds tab
- Test with manual siren button first

### Activity Log Messages
- `[HH:MM:SS] Zigbee button pressed - Siren activated`
- `[HH:MM:SS] Zigbee button released - Siren deactivated`
- `[HH:MM:SS] MQTT connection: Connected/Disconnected`
- `[HH:MM:SS] Manual siren test - ON/OFF`

## Integration Details

The Zigbee integration is designed to be completely non-intrusive:
- Existing functionality remains unchanged
- New tab added alongside existing tabs
- Graceful fallback when dependencies missing
- No performance impact on main application
- Thread-safe implementation

## Testing

Run the integration test suite:
```bash
python3 /tmp/test_integration.py
```

Or test the standalone module:
```bash
python3 zigbee_siren.py
```