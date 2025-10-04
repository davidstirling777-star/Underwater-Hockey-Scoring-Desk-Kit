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
    "connection_timeout": 60,
    "reconnect_delay": 5,
    "enable_logging": True
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
    Windows-specific Zigbee siren controller.
    
    This class provides a framework for Windows Zigbee support using alternative
    approaches to the Linux MQTT-based system. Currently provides logging and
    graceful degradation, with structure for future expansion.
    
    Potential Windows Integration Approaches:
    1. Direct serial communication with Zigbee dongle (via pyserial)
    2. Windows-compatible MQTT broker (Mosquitto for Windows, EMQX, etc.)
    3. Zigbee2MQTT running under WSL2 with Windows MQTT client
    4. Alternative Zigbee libraries (python-zigpy, zigbee-herdsman-converters)
    5. Network-based solutions (Zigbee hub with REST API or webhooks)
    
    Future Development Notes:
    - Implement serial port enumeration for Zigbee dongles on Windows
    - Add COM port detection and configuration
    - Support Windows service integration
    - Add Windows-specific logging to Event Viewer
    - Support Windows firewall configuration helpers
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
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Load configuration (using same config structure as Linux version)
        self.config = self.load_config()
        
        # Log platform information
        self.logger.info(f"Windows Zigbee controller initialized on {CURRENT_PLATFORM}")
        self.logger.warning("Windows Zigbee support is currently limited.")
        self.logger.info("For full functionality on Windows, consider:")
        self.logger.info("  1. Installing Mosquitto MQTT broker for Windows")
        self.logger.info("  2. Running Zigbee2MQTT under WSL2")
        self.logger.info("  3. Using a network-based Zigbee hub with MQTT support")
        
        # Check for available libraries
        if MQTT_AVAILABLE:
            self.logger.info("MQTT library (paho-mqtt) is available - MQTT integration possible")
        else:
            self.logger.warning("MQTT library not available. Install with: pip install paho-mqtt")
        
        if PYSERIAL_AVAILABLE:
            self.logger.info("PySerial is available - direct serial communication possible")
            self._detect_serial_ports()
        else:
            self.logger.info("PySerial not available. For serial support: pip install pyserial")
    
    def _detect_serial_ports(self) -> None:
        """Detect available serial ports on Windows (for future Zigbee dongle support)."""
        if not PYSERIAL_AVAILABLE:
            return
        
        try:
            ports = serial.tools.list_ports.comports()
            if ports:
                self.logger.info("Available COM ports detected:")
                for port in ports:
                    self.logger.info(f"  - {port.device}: {port.description}")
                    # Future: Check for Zigbee dongle identifiers in description
                    # Common identifiers: Silicon Labs, CP210x, CC2531, CC2652
            else:
                self.logger.info("No COM ports detected")
        except Exception as e:
            self.logger.error(f"Error detecting serial ports: {e}")
    
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
        
        Currently returns False with informative logging.
        Future implementations can add actual Windows Zigbee integration here.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        self.logger.warning("Windows Zigbee controller start requested")
        self.logger.info("Native Windows Zigbee support not yet implemented")
        self.logger.info("Workaround: Use MQTT broker on Windows with Zigbee2MQTT")
        
        # If MQTT is available, suggest using the standard controller
        if MQTT_AVAILABLE:
            self.logger.info("MQTT library is available - consider using standard MQTT integration")
        
        self._notify_status(False, "Windows Zigbee not supported (use MQTT)")
        return False
    
    def stop(self) -> None:
        """Stop the Windows Zigbee controller."""
        self.connected = False
        self._notify_status(False, "Stopped")
        self.logger.info("Windows Zigbee controller stopped")
    
    def _notify_status(self, connected: bool, message: str) -> None:
        """Notify connection status change."""
        if self.connection_status_callback:
            try:
                self.connection_status_callback(connected, message)
            except Exception as e:
                self.logger.error(f"Error calling status callback: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status information."""
        return {
            "connected": self.connected,
            "platform": CURRENT_PLATFORM,
            "mqtt_available": MQTT_AVAILABLE,
            "pyserial_available": PYSERIAL_AVAILABLE,
            "broker": "N/A (Windows)",
            "topic": "N/A (Windows)",
            "devices": [],
            "device": ""
        }
    
    def test_connection(self) -> bool:
        """Test connection (currently not implemented for Windows)."""
        self.logger.warning("Connection test not implemented for Windows native mode")
        self.logger.info("To use Zigbee on Windows, install MQTT broker and use standard controller")
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