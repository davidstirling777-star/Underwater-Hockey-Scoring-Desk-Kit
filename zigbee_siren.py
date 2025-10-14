"""
Zigbee2MQTT Wireless Siren Integration Module

This module provides wireless siren control through Zigbee2MQTT for the 
Underwater Hockey Scoring Desk Kit. It handles MQTT communication, button
event processing, and integration with the main sound system.

Key Features:
- MQTT client with automatic reconnection
- Zigbee button event handling for wireless siren triggers
- Integration with existing sound volume and playback logic
- Proper threading and error handling
- Configuration management and logging
- Fallback behavior when Zigbee is unavailable
- Cross-platform support (Linux with MQTT, Windows with alternative approaches)
"""

import threading
import time
import logging
import json
import os
import platform
from typing import Optional, Callable, Dict, Any

# Try to import paho-mqtt, with graceful fallback
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    mqtt = None

# Try to import pyserial for Windows serial communication, with graceful fallback
try:
    import serial
    import serial.tools.list_ports
    PYSERIAL_AVAILABLE = True
except ImportError:
    PYSERIAL_AVAILABLE = False
    serial = None

# Detect the current platform
CURRENT_PLATFORM = platform.system()  # Returns 'Windows', 'Linux', 'Darwin', etc.
IS_WINDOWS = CURRENT_PLATFORM == 'Windows'
IS_LINUX = CURRENT_PLATFORM == 'Linux'

# Configuration file for unified settings
SETTINGS_FILE = "settings.json"

# Legacy file for backward compatibility migration
ZIGBEE_CONFIG_FILE = "zigbee_config.json"

# Default configuration
DEFAULT_CONFIG = {
    "mqtt_broker": "localhost",
    "mqtt_port": 1883,
    "mqtt_username": "",
    "mqtt_password": "",
    "mqtt_topic": "zigbee2mqtt/+",
    "siren_button_devices": ["siren_button"],  # Now supports multiple devices as a list
    "siren_button_device": "siren_button",     # Keep for backward compatibility
    "siren_device_name": "zigbee_siren",       # The actual siren device to control
    "connection_timeout": 60,
    "reconnect_delay": 5,
    "enable_logging": True,
    # Serial configuration for Windows
    "serial_port": "",                         # Auto-detect if empty
    "serial_baudrate": 115200,
    "serial_timeout": 1.0,
    "use_serial_fallback": True,               # Use serial if MQTT unavailable
    "prefer_mqtt": True                        # Prefer MQTT over serial when both available
}

class ZigbeeSirenController:
    """
    Controls wireless siren functionality through Zigbee2MQTT.
    
    This class manages MQTT connections, processes button events,
    and provides callbacks for siren activation.
    """
    
    def __init__(self, siren_callback: Optional[Callable] = None):
        """
        Initialize the Zigbee siren controller.
        
        Args:
            siren_callback: Function to call when siren should be activated
        """
        self.siren_callback = siren_callback
        self.mqtt_client: Optional[mqtt.Client] = None
        self.connected = False
        self.connection_thread: Optional[threading.Thread] = None
        self.should_stop = threading.Event()
        
        # Set up logging BEFORE loading config (migration needs logger)
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Log platform information
        self.logger.info(f"Zigbee controller initializing on {CURRENT_PLATFORM}")
        if IS_WINDOWS:
            self.logger.info("Running on Windows - ensure MQTT broker is installed and configured")
        
        # Load configuration (may trigger migration which needs logger)
        self.config = self.load_config()
        
        # Update logging level based on config
        if self.config["enable_logging"]:
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.WARNING)
        
        # Connection status callback for UI updates
        self.connection_status_callback: Optional[Callable[[bool, str], None]] = None
        
        if not MQTT_AVAILABLE:
            self.logger.warning("paho-mqtt not available. Zigbee siren functionality disabled.")
            self.logger.info("Install with: pip install paho-mqtt")
            if IS_WINDOWS:
                self.logger.info("On Windows, also install MQTT broker (Mosquitto for Windows or EMQX)")
    
    def _migrate_device_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate old single device config to new multiple device format."""
        # If we have the old single device format, convert to new list format
        if "siren_button_device" in config and "siren_button_devices" not in config:
            single_device = config["siren_button_device"]
            if isinstance(single_device, str) and single_device:
                # Convert single device string to list
                config["siren_button_devices"] = [single_device]
                self.logger.info(f"Migrated single device '{single_device}' to device list format")
        
        # If we have the new format but not the old, ensure backward compatibility
        if "siren_button_devices" in config and "siren_button_device" not in config:
            device_list = config["siren_button_devices"]
            if isinstance(device_list, list) and device_list:
                # Set the first device as the legacy single device for compatibility
                config["siren_button_device"] = device_list[0]
        
        # Ensure siren_button_devices is always a list
        if "siren_button_devices" not in config:
            config["siren_button_devices"] = [config.get("siren_button_device", "siren_button")]
        elif isinstance(config["siren_button_devices"], str):
            # Handle case where it might be stored as a string
            config["siren_button_devices"] = [config["siren_button_devices"]]
        
        return config
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from unified settings file with migration support."""
        # First try to load from unified settings file
        settings_path = os.path.join(os.getcwd(), SETTINGS_FILE)
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r') as f:
                    unified_settings = json.load(f)
                    config = unified_settings.get("zigbeeSettings", {})
                    if config:
                        # Migrate device configuration BEFORE merging with defaults
                        config = self._migrate_device_config(config)
                        # Then merge with defaults for any missing keys
                        merged_config = DEFAULT_CONFIG.copy()
                        merged_config.update(config)
                        return merged_config
            except Exception as e:
                self.logger.error(f"Error loading unified config: {e}. Trying legacy file.")
        
        # Fallback to legacy zigbee_config.json for migration
        legacy_config_path = os.path.join(os.getcwd(), ZIGBEE_CONFIG_FILE)
        if os.path.exists(legacy_config_path):
            try:
                with open(legacy_config_path, 'r') as f:
                    config = json.load(f)
                # Migrate device configuration BEFORE merging with defaults
                config = self._migrate_device_config(config)
                # Then merge with defaults for any missing keys
                merged_config = DEFAULT_CONFIG.copy()
                merged_config.update(config)
                
                # Migrate to unified settings
                self.logger.info("Migrating Zigbee settings to unified config file")
                self.save_config(merged_config)
                return merged_config
            except Exception as e:
                self.logger.error(f"Error loading legacy config: {e}. Using defaults.")
        
        # Save default config to unified settings
        default_config = DEFAULT_CONFIG.copy()
        default_config = self._migrate_device_config(default_config)
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to unified settings file."""
        try:
            # Load current unified settings
            unified_settings = {}
            settings_path = os.path.join(os.getcwd(), SETTINGS_FILE)
            if os.path.exists(settings_path):
                try:
                    with open(settings_path, 'r') as f:
                        unified_settings = json.load(f)
                except Exception:
                    pass
            
            # Ensure structure exists
            if "zigbeeSettings" not in unified_settings:
                unified_settings["zigbeeSettings"] = {}
            if "soundSettings" not in unified_settings:
                unified_settings["soundSettings"] = {
                    "pips_sound": "Default",
                    "siren_sound": "Default", 
                    "pips_volume": 50.0,
                    "siren_volume": 50.0,
                    "air_volume": 50.0,
                    "water_volume": 50.0
                }
            if "gameSettings" not in unified_settings:
                unified_settings["gameSettings"] = {
                    "time_to_start_first_game": "",
                    "start_first_game_in": 1,
                    "team_timeouts_allowed": True,
                    "team_timeout_period": 1,
                    "half_period": 1,
                    "half_time_break": 1,
                    "overtime_allowed": True,
                    "overtime_game_break": 1,
                    "overtime_half_period": 1,
                    "overtime_half_time_break": 1,
                    "sudden_death_game_break": 1,
                    "between_game_break": 1,
                    "crib_time": 3
                }
            
            # Update Zigbee settings
            unified_settings["zigbeeSettings"] = config
            
            # Save unified settings
            with open(settings_path, 'w') as f:
                json.dump(unified_settings, f, indent=2)
            self.config = config
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def set_siren_callback(self, callback: Callable) -> None:
        """Set the callback function for siren activation."""
        self.siren_callback = callback
    
    def set_connection_status_callback(self, callback: Callable[[bool, str], None]) -> None:
        """Set callback for connection status updates."""
        self.connection_status_callback = callback
    
    def start(self) -> bool:
        """
        Start the Zigbee siren controller.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if not MQTT_AVAILABLE:
            self._notify_status(False, "MQTT library not available")
            return False
        
        if self.connection_thread and self.connection_thread.is_alive():
            self.logger.warning("Controller already running")
            return True
        
        self.should_stop.clear()
        self.connection_thread = threading.Thread(target=self._connection_loop, daemon=True)
        self.connection_thread.start()
        
        self.logger.info("Zigbee siren controller started")
        return True
    
    def stop(self) -> None:
        """Stop the Zigbee siren controller."""
        self.should_stop.set()
        
        if self.mqtt_client and self.connected:
            try:
                self.mqtt_client.disconnect()
            except Exception as e:
                self.logger.error(f"Error disconnecting MQTT client: {e}")
        
        if self.connection_thread and self.connection_thread.is_alive():
            self.connection_thread.join(timeout=5)
        
        self.connected = False
        self._notify_status(False, "Stopped")
        self.logger.info("Zigbee siren controller stopped")
    
    def _connection_loop(self) -> None:
        """Main connection loop running in separate thread."""
        while not self.should_stop.is_set():
            try:
                self._setup_mqtt_client()
                self._connect_mqtt()
                
                # Keep connection alive
                while self.connected and not self.should_stop.is_set():
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Connection error: {e}")
                self._notify_status(False, f"Error: {str(e)}")
                
            if not self.should_stop.is_set():
                self.logger.info(f"Reconnecting in {self.config['reconnect_delay']} seconds...")
                time.sleep(self.config['reconnect_delay'])
    
    def _setup_mqtt_client(self) -> None:
        """Set up MQTT client with callbacks."""
        self.mqtt_client = mqtt.Client()
        
        # Set username/password if provided
        if self.config["mqtt_username"]:
            self.mqtt_client.username_pw_set(
                self.config["mqtt_username"], 
                self.config["mqtt_password"]
            )
        
        # Set up callbacks
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_disconnect = self._on_disconnect
        self.mqtt_client.on_message = self._on_message
        
        # Set timeouts
        self.mqtt_client.connect_async(
            self.config["mqtt_broker"],
            self.config["mqtt_port"],
            self.config["connection_timeout"]
        )
    
    def _connect_mqtt(self) -> None:
        """Connect to MQTT broker."""
        try:
            self.mqtt_client.loop_start()
            
            # Wait for connection
            timeout = time.time() + self.config["connection_timeout"]
            while not self.connected and time.time() < timeout and not self.should_stop.is_set():
                time.sleep(0.1)
            
            if not self.connected:
                raise Exception("Connection timeout")
                
        except Exception as e:
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
            raise e
    
    def _on_connect(self, client, userdata, flags, rc) -> None:
        """Callback for successful MQTT connection."""
        if rc == 0:
            self.connected = True
            self.logger.info(f"Connected to MQTT broker {self.config['mqtt_broker']}:{self.config['mqtt_port']}")
            
            # Subscribe to Zigbee2MQTT topic
            topic = self.config["mqtt_topic"]
            client.subscribe(topic)
            self.logger.info(f"Subscribed to topic: {topic}")
            
            self._notify_status(True, "Connected")
        else:
            self.connected = False
            self.logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
            self._notify_status(False, f"Connection failed (RC: {rc})")
    
    def _on_disconnect(self, client, userdata, rc) -> None:
        """Callback for MQTT disconnection."""
        self.connected = False
        if rc != 0:
            self.logger.warning(f"Unexpected disconnection from MQTT broker. RC: {rc}")
            self._notify_status(False, "Disconnected unexpectedly")
        else:
            self.logger.info("Disconnected from MQTT broker")
            self._notify_status(False, "Disconnected")
    
    def _on_message(self, client, userdata, msg) -> None:
        """Process incoming MQTT messages."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            self.logger.debug(f"Received message on {topic}: {payload}")
            
            # Parse JSON payload
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                self.logger.warning(f"Invalid JSON in message: {payload}")
                return
            
            # Check if this is from any of our configured siren button devices
            device_name = topic.split('/')[-1]  # Extract device name from topic
            
            # Get the list of configured devices
            configured_devices = self.config.get("siren_button_devices", [])
            
            # For backward compatibility, also check the old single device config
            if "siren_button_device" in self.config:
                legacy_device = self.config["siren_button_device"]
                if legacy_device and legacy_device not in configured_devices:
                    configured_devices.append(legacy_device)
            
            # Process if device matches any of our configured devices
            if device_name in configured_devices:
                self._process_button_event(device_name, data)
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    def _process_button_event(self, device_name: str, data: Dict[str, Any]) -> None:
        """Process button events from Zigbee device."""
        try:
            # Look for button press events
            # Common Zigbee button event formats:
            if "action" in data:
                action = data["action"]
                self.logger.info(f"Button action from {device_name}: {action}")
                
                # Trigger siren on button press (various action types)
                if action in ["single", "press", "click", "on", "1"]:
                    self._trigger_siren()
                    
            elif "click" in data:
                click_type = data["click"]
                self.logger.info(f"Button click from {device_name}: {click_type}")
                
                # Trigger on single click
                if click_type == "single":
                    self._trigger_siren()
                    
            elif "state" in data:
                state = data["state"]
                self.logger.info(f"Button state from {device_name}: {state}")
                
                # Trigger on ON state
                if state == "ON":
                    self._trigger_siren()
                    
        except Exception as e:
            self.logger.error(f"Error processing button event: {e}")
    
    def _trigger_siren(self) -> None:
        """Trigger the siren through the callback."""
        self.logger.info("Triggering wireless siren")
        
        if self.siren_callback:
            try:
                # Call the siren callback in a separate thread to avoid blocking MQTT
                threading.Thread(target=self.siren_callback, daemon=True).start()
            except Exception as e:
                self.logger.error(f"Error calling siren callback: {e}")
        else:
            self.logger.warning("No siren callback set")
    
    def start_siren(self) -> bool:
        """
        Start the siren by sending MQTT ON command to the siren device.
        
        Returns:
            bool: True if command sent successfully, False otherwise
        """
        if not MQTT_AVAILABLE:
            self.logger.warning("MQTT not available - cannot control siren")
            return False
        
        if not self.connected or not self.mqtt_client:
            self.logger.warning("MQTT not connected - cannot start siren")
            return False
        
        try:
            siren_device = self.config.get("siren_device_name", "zigbee_siren")
            topic = f"zigbee2mqtt/{siren_device}/set"
            payload = json.dumps({"state": "ON"})
            
            self.logger.info(f"Starting siren: Publishing to {topic} with payload {payload}")
            self.mqtt_client.publish(topic, payload)
            return True
        except Exception as e:
            self.logger.error(f"Error starting siren: {e}")
            return False
    
    def stop_siren(self) -> bool:
        """
        Stop the siren by sending MQTT OFF command to the siren device.
        
        Returns:
            bool: True if command sent successfully, False otherwise
        """
        if not MQTT_AVAILABLE:
            self.logger.warning("MQTT not available - cannot control siren")
            return False
        
        if not self.connected or not self.mqtt_client:
            self.logger.warning("MQTT not connected - cannot stop siren")
            return False
        
        try:
            siren_device = self.config.get("siren_device_name", "zigbee_siren")
            topic = f"zigbee2mqtt/{siren_device}/set"
            payload = json.dumps({"state": "OFF"})
            
            self.logger.info(f"Stopping siren: Publishing to {topic} with payload {payload}")
            self.mqtt_client.publish(topic, payload)
            return True
        except Exception as e:
            self.logger.error(f"Error stopping siren: {e}")
            return False
    
    def _notify_status(self, connected: bool, message: str) -> None:
        """Notify connection status change."""
        if self.connection_status_callback:
            try:
                self.connection_status_callback(connected, message)
            except Exception as e:
                self.logger.error(f"Error calling status callback: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status information."""
        devices = self.config.get("siren_button_devices", [])
        # Include legacy device for compatibility if not in list
        legacy_device = self.config.get("siren_button_device", "")
        if legacy_device and legacy_device not in devices:
            devices = devices + [legacy_device]
        
        return {
            "connected": self.connected,
            "mqtt_available": MQTT_AVAILABLE,
            "broker": f"{self.config['mqtt_broker']}:{self.config['mqtt_port']}",
            "topic": self.config["mqtt_topic"],
            "devices": devices,
            "device": self.config.get("siren_button_device", "")  # Keep for backward compatibility
        }
    
    def test_connection(self) -> bool:
        """Test MQTT connection (synchronous)."""
        if not MQTT_AVAILABLE:
            return False
        
        try:
            test_client = mqtt.Client()
            
            if self.config["mqtt_username"]:
                test_client.username_pw_set(
                    self.config["mqtt_username"],
                    self.config["mqtt_password"]
                )
            
            test_client.connect(
                self.config["mqtt_broker"],
                self.config["mqtt_port"],
                10
            )
            test_client.disconnect()
            return True
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False


def get_default_config() -> Dict[str, Any]:
    """Get default Zigbee configuration."""
    return DEFAULT_CONFIG.copy()


def is_mqtt_available() -> bool:
    """Check if MQTT library is available."""
    return MQTT_AVAILABLE


def is_pyserial_available() -> bool:
    """Check if pyserial library is available."""
    return PYSERIAL_AVAILABLE


def get_platform_info() -> Dict[str, Any]:
    """Get platform information for diagnostics."""
    return {
        "platform": CURRENT_PLATFORM,
        "is_windows": IS_WINDOWS,
        "is_linux": IS_LINUX,
        "mqtt_available": MQTT_AVAILABLE,
        "pyserial_available": PYSERIAL_AVAILABLE
    }


class WindowsZigbeeSirenController:
    """
    Windows-specific Zigbee siren controller with serial and MQTT support.
    
    This class provides Windows Zigbee support through:
    1. Direct serial communication with Zigbee dongle (via pyserial) - PRIMARY
    2. Windows-compatible MQTT broker (Mosquitto for Windows, EMQX, etc.) - FALLBACK
    
    Serial Communication:
    - Auto-detects Zigbee dongles (CC2531, CP210x, Silicon Labs, etc.)
    - Reads button events from serial data
    - Sends serial commands to trigger siren ON/OFF
    - Robust error handling and reconnection logic
    
    Connection Priority:
    - If prefer_mqtt=True and MQTT available: Use MQTT
    - If prefer_mqtt=False or MQTT unavailable: Use Serial
    - Automatic fallback between methods if connection fails
    """
    
    def __init__(self, siren_callback: Optional[Callable] = None):
        """
        Initialize the Windows Zigbee siren controller.
        
        Args:
            siren_callback: Function to call when siren should be activated
        """
        self.siren_callback = siren_callback
        self.connected = False
        self.connection_status_callback: Optional[Callable[[bool, str], None]] = None
        
        # Connection management
        self.mqtt_controller: Optional[ZigbeeSirenController] = None
        self.serial_connection: Optional[serial.Serial] = None
        self.serial_thread: Optional[threading.Thread] = None
        self.should_stop = threading.Event()
        self.using_mqtt = False
        self.using_serial = False
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Load configuration
        self.config = self.load_config()
        
        # Log platform information
        self.logger.info(f"Windows Zigbee controller initialized on {CURRENT_PLATFORM}")
        self.logger.info("Windows Zigbee support modes:")
        self.logger.info("  1. Direct serial communication with Zigbee dongle")
        self.logger.info("  2. MQTT broker integration (requires Mosquitto for Windows)")
        
        # Check for available libraries
        if MQTT_AVAILABLE:
            self.logger.info("MQTT library (paho-mqtt) is available")
        else:
            self.logger.warning("MQTT library not available. Install with: pip install paho-mqtt")
        
        if PYSERIAL_AVAILABLE:
            self.logger.info("PySerial is available - serial communication enabled")
            self._detect_serial_ports()
        else:
            self.logger.warning("PySerial not available. Install with: pip install pyserial")
    
    def _detect_serial_ports(self) -> Optional[str]:
        """
        Detect available serial ports and identify Zigbee dongles.
        
        Returns:
            str: Path to detected Zigbee dongle, or None if not found
        """
        if not PYSERIAL_AVAILABLE:
            return None
        
        # Common Zigbee dongle identifiers
        zigbee_identifiers = [
            'CC2531', 'CC2652', 'CC2538',  # TI Zigbee chips
            'CP210', 'CP2102', 'CP2104',   # Silicon Labs USB-to-serial
            'Silicon Labs',                 # Silicon Labs devices
            'FTDI',                         # FTDI USB-to-serial
            'CH340', 'CH341',              # CH340/CH341 USB-to-serial
            'Zigbee', 'ZigBee'             # Generic Zigbee identifiers
        ]
        
        try:
            ports = serial.tools.list_ports.comports()
            detected_zigbee_port = None
            
            if ports:
                self.logger.info("Available COM ports detected:")
                for port in ports:
                    description = port.description.upper()
                    manufacturer = (port.manufacturer or "").upper()
                    
                    # Check if this is a potential Zigbee dongle
                    is_zigbee = any(identifier.upper() in description or 
                                   identifier.upper() in manufacturer 
                                   for identifier in zigbee_identifiers)
                    
                    marker = " [POTENTIAL ZIGBEE DONGLE]" if is_zigbee else ""
                    self.logger.info(f"  - {port.device}: {port.description}{marker}")
                    
                    if is_zigbee and not detected_zigbee_port:
                        detected_zigbee_port = port.device
                        self.logger.info(f"  → Auto-detected Zigbee dongle: {port.device}")
            else:
                self.logger.info("No COM ports detected")
            
            return detected_zigbee_port
            
        except Exception as e:
            self.logger.error(f"Error detecting serial ports: {e}")
            return None
    
    def _open_serial_connection(self, port: str) -> bool:
        """
        Open serial connection to Zigbee dongle.
        
        Args:
            port: COM port path (e.g., 'COM3')
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if not PYSERIAL_AVAILABLE:
            self.logger.error("PySerial not available - cannot open serial connection")
            return False
        
        try:
            self.logger.info(f"Opening serial connection to {port} at {self.config['serial_baudrate']} baud")
            
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=self.config['serial_baudrate'],
                timeout=self.config['serial_timeout'],
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            # Give the connection a moment to stabilize
            time.sleep(0.5)
            
            if self.serial_connection.is_open:
                self.logger.info(f"Serial connection established to {port}")
                return True
            else:
                self.logger.error(f"Failed to open serial connection to {port}")
                return False
                
        except serial.SerialException as e:
            self.logger.error(f"Serial connection error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error opening serial connection: {e}")
            return False
    
    def _close_serial_connection(self) -> None:
        """Close serial connection."""
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.close()
                self.logger.info("Serial connection closed")
            except Exception as e:
                self.logger.error(f"Error closing serial connection: {e}")
        self.serial_connection = None
    
    def _serial_read_loop(self) -> None:
        """
        Main serial reading loop running in separate thread.
        Reads incoming data and processes button events.
        """
        self.logger.info("Serial read loop started")
        
        while not self.should_stop.is_set():
            try:
                if not self.serial_connection or not self.serial_connection.is_open:
                    self.logger.warning("Serial connection lost, attempting reconnect...")
                    self._notify_status(False, "Serial connection lost")
                    
                    # Try to reconnect
                    port = self.config.get('serial_port', '')
                    if not port:
                        port = self._detect_serial_ports()
                    
                    if port and self._open_serial_connection(port):
                        self._notify_status(True, f"Serial reconnected: {port}")
                    else:
                        time.sleep(self.config['reconnect_delay'])
                        continue
                
                # Read data from serial port
                if self.serial_connection.in_waiting > 0:
                    try:
                        # Read line from serial port
                        line = self.serial_connection.readline()
                        
                        # Decode and strip whitespace
                        data_str = line.decode('utf-8', errors='ignore').strip()
                        
                        if data_str:
                            self.logger.debug(f"Serial data received: {data_str}")
                            self._parse_serial_data(data_str)
                    
                    except UnicodeDecodeError as e:
                        self.logger.warning(f"Failed to decode serial data: {e}")
                    except Exception as e:
                        self.logger.error(f"Error reading serial data: {e}")
                
                # Small delay to prevent CPU spinning
                time.sleep(0.01)
                
            except Exception as e:
                self.logger.error(f"Error in serial read loop: {e}")
                time.sleep(1)
        
        self.logger.info("Serial read loop stopped")
    
    def _parse_serial_data(self, data: str) -> None:
        """
        Parse incoming serial data and process button events.
        
        Expected formats:
        - JSON: {"action": "single", "device": "button1"}
        - Simple: BUTTON_PRESS or BTN:1
        - Zigbee2MQTT format: action:single device:button1
        
        Args:
            data: Raw string data from serial port
        """
        try:
            # Try parsing as JSON first (most common for Zigbee2MQTT-like format)
            if data.startswith('{') and data.endswith('}'):
                try:
                    json_data = json.loads(data)
                    self._process_button_event("serial_device", json_data)
                    return
                except json.JSONDecodeError:
                    pass
            
            # Parse simple button press commands
            data_upper = data.upper()
            
            # Common button trigger keywords
            button_keywords = ['BUTTON', 'BTN', 'PRESS', 'CLICK', 'ACTION']
            
            if any(keyword in data_upper for keyword in button_keywords):
                self.logger.info(f"Button event detected from serial: {data}")
                self._trigger_siren()
                return
            
            # Try to parse key-value format (action:single device:button1)
            if ':' in data:
                parts = {}
                for item in data.split():
                    if ':' in item:
                        key, value = item.split(':', 1)
                        parts[key.lower()] = value.lower()
                
                if parts:
                    self._process_button_event("serial_device", parts)
                    return
            
            # If we can't parse it, log for debugging
            self.logger.debug(f"Unrecognized serial data format: {data}")
            
        except Exception as e:
            self.logger.error(f"Error parsing serial data: {e}")
    
    def _process_button_event(self, device_name: str, data: Dict[str, Any]) -> None:
        """
        Process button events from serial data.
        Same logic as MQTT version for consistency.
        
        Args:
            device_name: Name of the device (for logging)
            data: Dictionary containing button event data
        """
        try:
            # Look for button press events
            if "action" in data:
                action = data["action"]
                self.logger.info(f"Button action from {device_name}: {action}")
                
                if action in ["single", "press", "click", "on", "1"]:
                    self._trigger_siren()
                    
            elif "click" in data:
                click_type = data["click"]
                self.logger.info(f"Button click from {device_name}: {click_type}")
                
                if click_type == "single":
                    self._trigger_siren()
                    
            elif "state" in data:
                state = data["state"]
                self.logger.info(f"Button state from {device_name}: {state}")
                
                if state == "ON" or state == "on":
                    self._trigger_siren()
                    
        except Exception as e:
            self.logger.error(f"Error processing button event: {e}")
    
    def _trigger_siren(self) -> None:
        """Trigger the siren through the callback."""
        self.logger.info("Triggering wireless siren (serial)")
        
        if self.siren_callback:
            try:
                threading.Thread(target=self.siren_callback, daemon=True).start()
            except Exception as e:
                self.logger.error(f"Error calling siren callback: {e}")
        else:
            self.logger.warning("No siren callback set")
    
    def _send_serial_command(self, command: str) -> bool:
        """
        Send command over serial connection.
        
        Args:
            command: Command string to send
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            self.logger.warning("Serial connection not available")
            return False
        
        try:
            # Ensure command ends with newline
            if not command.endswith('\n'):
                command += '\n'
            
            self.serial_connection.write(command.encode('utf-8'))
            self.serial_connection.flush()
            
            self.logger.debug(f"Serial command sent: {command.strip()}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending serial command: {e}")
            return False
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from unified settings file."""
        # Reuse the same config loading logic as Linux version
        settings_path = os.path.join(os.getcwd(), SETTINGS_FILE)
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r') as f:
                    unified_settings = json.load(f)
                    config = unified_settings.get("zigbeeSettings", {})
                    if config:
                        merged_config = DEFAULT_CONFIG.copy()
                        merged_config.update(config)
                        return merged_config
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
        
        return DEFAULT_CONFIG.copy()
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to unified settings file."""
        try:
            unified_settings = {}
            settings_path = os.path.join(os.getcwd(), SETTINGS_FILE)
            if os.path.exists(settings_path):
                try:
                    with open(settings_path, 'r') as f:
                        unified_settings = json.load(f)
                except Exception:
                    pass
            
            if "zigbeeSettings" not in unified_settings:
                unified_settings["zigbeeSettings"] = {}
            
            unified_settings["zigbeeSettings"] = config
            
            with open(settings_path, 'w') as f:
                json.dump(unified_settings, f, indent=2)
            self.config = config
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def set_siren_callback(self, callback: Callable) -> None:
        """Set the callback function for siren activation."""
        self.siren_callback = callback
    
    def set_connection_status_callback(self, callback: Callable[[bool, str], None]) -> None:
        """Set callback for connection status updates."""
        self.connection_status_callback = callback
    
    def start(self) -> bool:
        """
        Start the Windows Zigbee controller.
        
        Attempts to connect using MQTT (if available and preferred) or Serial.
        Falls back between methods based on configuration and availability.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        self.logger.info("Starting Windows Zigbee controller...")
        
        # Determine connection method
        prefer_mqtt = self.config.get('prefer_mqtt', True)
        use_serial_fallback = self.config.get('use_serial_fallback', True)
        
        # Try MQTT first if preferred and available
        if prefer_mqtt and MQTT_AVAILABLE:
            self.logger.info("Attempting MQTT connection (preferred method)...")
            if self._start_mqtt():
                self.using_mqtt = True
                self.using_serial = False
                self.connected = True
                self._notify_status(True, "Connected via MQTT")
                return True
            else:
                self.logger.warning("MQTT connection failed")
        
        # Try serial if MQTT failed or not preferred
        if PYSERIAL_AVAILABLE:
            self.logger.info("Attempting serial connection...")
            if self._start_serial():
                self.using_serial = True
                self.using_mqtt = False
                self.connected = True
                return True
            else:
                self.logger.warning("Serial connection failed")
        
        # Try MQTT as fallback if serial failed and we haven't tried MQTT yet
        if not prefer_mqtt and use_serial_fallback and MQTT_AVAILABLE:
            self.logger.info("Attempting MQTT connection (fallback)...")
            if self._start_mqtt():
                self.using_mqtt = True
                self.using_serial = False
                self.connected = True
                self._notify_status(True, "Connected via MQTT (fallback)")
                return True
        
        # Failed to connect with any method
        self.logger.error("Failed to start - no connection method available")
        self._notify_status(False, "Connection failed")
        return False
    
    def _start_mqtt(self) -> bool:
        """
        Start MQTT connection using the standard controller.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not MQTT_AVAILABLE:
                return False
            
            self.mqtt_controller = ZigbeeSirenController(self.siren_callback)
            
            # Copy our callbacks to the MQTT controller
            if self.connection_status_callback:
                self.mqtt_controller.set_connection_status_callback(self.connection_status_callback)
            
            return self.mqtt_controller.start()
            
        except Exception as e:
            self.logger.error(f"Error starting MQTT: {e}")
            return False
    
    def _start_serial(self) -> bool:
        """
        Start serial connection to Zigbee dongle.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not PYSERIAL_AVAILABLE:
            self.logger.error("PySerial not available")
            return False
        
        try:
            # Get serial port from config or auto-detect
            port = self.config.get('serial_port', '')
            
            if not port or port == '':
                self.logger.info("No serial port configured, attempting auto-detection...")
                port = self._detect_serial_ports()
            
            if not port:
                self.logger.error("No Zigbee dongle detected")
                self._notify_status(False, "No Zigbee dongle found")
                return False
            
            # Open serial connection
            if not self._open_serial_connection(port):
                self._notify_status(False, f"Failed to open {port}")
                return False
            
            # Start serial reading thread
            self.should_stop.clear()
            self.serial_thread = threading.Thread(target=self._serial_read_loop, daemon=True)
            self.serial_thread.start()
            
            self.logger.info(f"Serial connection started on {port}")
            self._notify_status(True, f"Serial: {port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting serial connection: {e}")
            self._notify_status(False, f"Serial error: {str(e)}")
            return False
    
    def stop(self) -> None:
        """Stop the Windows Zigbee controller."""
        self.logger.info("Stopping Windows Zigbee controller...")
        
        # Stop MQTT if active
        if self.using_mqtt and self.mqtt_controller:
            try:
                self.mqtt_controller.stop()
            except Exception as e:
                self.logger.error(f"Error stopping MQTT controller: {e}")
            self.mqtt_controller = None
        
        # Stop serial if active
        if self.using_serial:
            self.should_stop.set()
            
            # Wait for serial thread to finish
            if self.serial_thread and self.serial_thread.is_alive():
                self.serial_thread.join(timeout=5)
            
            # Close serial connection
            self._close_serial_connection()
        
        self.connected = False
        self.using_mqtt = False
        self.using_serial = False
        self._notify_status(False, "Stopped")
        self.logger.info("Windows Zigbee controller stopped")
    
    def start_siren(self) -> bool:
        """
        Start the siren via MQTT or serial command.
        
        Returns:
            bool: True if command sent successfully, False otherwise
        """
        if self.using_mqtt and self.mqtt_controller:
            return self.mqtt_controller.start_siren()
        
        elif self.using_serial:
            # Send siren ON command via serial
            commands = [
                '{"state": "ON"}',           # JSON format
                'SIREN_ON',                   # Simple format
                'state:ON'                    # Key-value format
            ]
            
            success = False
            for cmd in commands:
                if self._send_serial_command(cmd):
                    success = True
                    break
            
            if success:
                self.logger.info("Siren ON command sent via serial")
            else:
                self.logger.warning("Failed to send siren ON command")
            
            return success
        
        else:
            self.logger.warning("Not connected - cannot start siren")
            return False
    
    def stop_siren(self) -> bool:
        """
        Stop the siren via MQTT or serial command.
        
        Returns:
            bool: True if command sent successfully, False otherwise
        """
        if self.using_mqtt and self.mqtt_controller:
            return self.mqtt_controller.stop_siren()
        
        elif self.using_serial:
            # Send siren OFF command via serial
            commands = [
                '{"state": "OFF"}',          # JSON format
                'SIREN_OFF',                  # Simple format
                'state:OFF'                   # Key-value format
            ]
            
            success = False
            for cmd in commands:
                if self._send_serial_command(cmd):
                    success = True
                    break
            
            if success:
                self.logger.info("Siren OFF command sent via serial")
            else:
                self.logger.warning("Failed to send siren OFF command")
            
            return success
        
        else:
            self.logger.warning("Not connected - cannot stop siren")
            return False
    
    def _notify_status(self, connected: bool, message: str) -> None:
        """Notify connection status change."""
        if self.connection_status_callback:
            try:
                self.connection_status_callback(connected, message)
            except Exception as e:
                self.logger.error(f"Error calling status callback: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status information."""
        status = {
            "connected": self.connected,
            "platform": CURRENT_PLATFORM,
            "mqtt_available": MQTT_AVAILABLE,
            "pyserial_available": PYSERIAL_AVAILABLE,
            "connection_method": "none"
        }
        
        if self.using_mqtt and self.mqtt_controller:
            mqtt_status = self.mqtt_controller.get_status()
            status.update({
                "connection_method": "mqtt",
                "broker": mqtt_status.get("broker", "N/A"),
                "topic": mqtt_status.get("topic", "N/A"),
                "devices": mqtt_status.get("devices", []),
                "device": mqtt_status.get("device", "")
            })
        
        elif self.using_serial and self.serial_connection:
            status.update({
                "connection_method": "serial",
                "broker": "N/A (Serial)",
                "topic": "N/A (Serial)",
                "devices": ["serial_device"],
                "device": "serial_device",
                "serial_port": self.serial_connection.port if self.serial_connection else "N/A"
            })
        
        else:
            status.update({
                "broker": "N/A",
                "topic": "N/A",
                "devices": [],
                "device": ""
            })
        
        return status
    
    def test_connection(self) -> bool:
        """Test connection for the active method."""
        if self.using_mqtt and self.mqtt_controller:
            return self.mqtt_controller.test_connection()
        
        elif self.using_serial and self.serial_connection:
            # Test serial connection by checking if port is open
            try:
                if self.serial_connection and self.serial_connection.is_open:
                    self.logger.info("Serial connection test: OK")
                    return True
                else:
                    self.logger.warning("Serial connection test: Port not open")
                    return False
            except Exception as e:
                self.logger.error(f"Serial connection test failed: {e}")
                return False
        
        else:
            self.logger.warning("No active connection to test")
            return False


def create_controller(siren_callback: Optional[Callable] = None):
    """
    Factory function to create the appropriate controller for the current platform.
    
    On Linux: Returns standard ZigbeeSirenController with MQTT support
    On Windows: Returns WindowsZigbeeSirenController (currently limited functionality)
                or ZigbeeSirenController if MQTT is available
    
    Args:
        siren_callback: Function to call when siren should be activated
    
    Returns:
        Appropriate controller instance for the platform
    """
    logger = logging.getLogger(__name__)
    
    # On Windows, check if MQTT is available
    if IS_WINDOWS:
        logger.info(f"Running on Windows ({CURRENT_PLATFORM})")
        
        if MQTT_AVAILABLE:
            logger.info("MQTT available on Windows - using standard MQTT controller")
            logger.info("Ensure MQTT broker (Mosquitto/EMQX) is installed and running on Windows")
            # Use standard controller if MQTT is available
            return ZigbeeSirenController(siren_callback)
        else:
            logger.warning("MQTT not available on Windows - using limited Windows controller")
            logger.info("Install MQTT support: pip install paho-mqtt")
            # Use Windows-specific controller with limited functionality
            return WindowsZigbeeSirenController(siren_callback)
    
    # On Linux or other platforms, use standard MQTT controller
    logger.info(f"Running on {CURRENT_PLATFORM} - using standard MQTT controller")
    return ZigbeeSirenController(siren_callback)