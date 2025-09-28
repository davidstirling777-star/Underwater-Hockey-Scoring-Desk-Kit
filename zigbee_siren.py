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
"""

import threading
import time
import logging
import json
import os
from typing import Optional, Callable, Dict, Any

# Try to import paho-mqtt, with graceful fallback
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    mqtt = None

# Configuration file for Zigbee settings
ZIGBEE_CONFIG_FILE = "zigbee_config.json"

# Default configuration
DEFAULT_CONFIG = {
    "mqtt_broker": "localhost",
    "mqtt_port": 1883,
    "mqtt_username": "",
    "mqtt_password": "",
    "mqtt_topic": "zigbee2mqtt/+",
    "siren_button_device": "siren_button",
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
        self.config = self.load_config()
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        if self.config["enable_logging"]:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        # Connection status callback for UI updates
        self.connection_status_callback: Optional[Callable[[bool, str], None]] = None
        
        if not MQTT_AVAILABLE:
            self.logger.warning("paho-mqtt not available. Zigbee siren functionality disabled.")
            self.logger.info("Install with: pip install paho-mqtt")
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file or create default."""
        if os.path.exists(ZIGBEE_CONFIG_FILE):
            try:
                with open(ZIGBEE_CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                # Merge with defaults for any missing keys
                merged_config = DEFAULT_CONFIG.copy()
                merged_config.update(config)
                return merged_config
            except Exception as e:
                self.logger.error(f"Error loading config: {e}. Using defaults.")
        
        # Save default config
        self.save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to JSON file."""
        try:
            with open(ZIGBEE_CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
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
            
            # Check if this is from our siren button device
            device_name = topic.split('/')[-1]  # Extract device name from topic
            if device_name == self.config["siren_button_device"]:
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
        return {
            "connected": self.connected,
            "mqtt_available": MQTT_AVAILABLE,
            "broker": f"{self.config['mqtt_broker']}:{self.config['mqtt_port']}",
            "topic": self.config["mqtt_topic"],
            "device": self.config["siren_button_device"]
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