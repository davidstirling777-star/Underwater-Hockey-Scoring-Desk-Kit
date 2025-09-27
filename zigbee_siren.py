"""
Zigbee2MQTT Button Integration Module for Underwater Hockey Scoring Desk Kit

This module provides Zigbee2MQTT integration for triggering the siren via wireless buttons.
It uses paho-mqtt to listen for button events from Zigbee2MQTT and activates/deactivates
the siren accordingly, keeping the siren going while the button is held.
"""

import json
import threading
import time
from typing import Callable, Optional

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("Warning: paho-mqtt not available. Zigbee siren functionality will be disabled.")


class ZigbeeSirenController:
    """Controller for Zigbee2MQTT button integration with siren functionality."""
    
    def __init__(self, 
                 mqtt_broker: str = "localhost", 
                 mqtt_port: int = 1883,
                 zigbee2mqtt_topic: str = "zigbee2mqtt",
                 button_device_name: str = "siren_button"):
        """
        Initialize the Zigbee siren controller.
        
        Args:
            mqtt_broker: MQTT broker hostname/IP
            mqtt_port: MQTT broker port
            zigbee2mqtt_topic: Base topic for Zigbee2MQTT
            button_device_name: Name of the button device in Zigbee2MQTT
        """
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.zigbee2mqtt_topic = zigbee2mqtt_topic
        self.button_device_name = button_device_name
        
        # Connection state
        self.connected = False
        self.client = None
        self.connection_thread = None
        
        # Button state
        self.button_pressed = False
        self.last_button_event = None
        self.button_hold_start = None
        
        # Callbacks
        self.on_button_press: Optional[Callable] = None
        self.on_button_release: Optional[Callable] = None
        self.on_connection_change: Optional[Callable[[bool], None]] = None
        
        # Threading
        self._running = False
        self._lock = threading.Lock()
        
        if not MQTT_AVAILABLE:
            print("Warning: Cannot initialize Zigbee siren controller - paho-mqtt not available")
    
    def set_callbacks(self, 
                     on_button_press: Optional[Callable] = None,
                     on_button_release: Optional[Callable] = None,
                     on_connection_change: Optional[Callable[[bool], None]] = None):
        """Set callback functions for button events and connection changes."""
        self.on_button_press = on_button_press
        self.on_button_release = on_button_release
        self.on_connection_change = on_connection_change
    
    def start(self) -> bool:
        """Start the Zigbee siren controller."""
        if not MQTT_AVAILABLE:
            return False
            
        if self._running:
            return True
            
        self._running = True
        
        # Initialize MQTT client
        self.client = mqtt.Client()
        self.client.on_connect = self._on_mqtt_connect
        self.client.on_disconnect = self._on_mqtt_disconnect
        self.client.on_message = self._on_mqtt_message
        
        # Start connection in background thread
        self.connection_thread = threading.Thread(target=self._connection_worker, daemon=True)
        self.connection_thread.start()
        
        return True
    
    def stop(self):
        """Stop the Zigbee siren controller."""
        self._running = False
        
        if self.client and self.connected:
            self.client.disconnect()
        
        if self.connection_thread:
            self.connection_thread.join(timeout=2.0)
    
    def _connection_worker(self):
        """Background thread worker for managing MQTT connection."""
        while self._running:
            try:
                if not self.connected:
                    print(f"Attempting to connect to MQTT broker at {self.mqtt_broker}:{self.mqtt_port}")
                    self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
                    self.client.loop_start()
                
                time.sleep(1)  # Check connection status every second
                
            except Exception as e:
                print(f"MQTT connection error: {e}")
                self.connected = False
                if self.on_connection_change:
                    self.on_connection_change(False)
                time.sleep(5)  # Wait 5 seconds before retry
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback for when MQTT client connects."""
        if rc == 0:
            self.connected = True
            print("Connected to MQTT broker")
            
            # Subscribe to button events
            topic = f"{self.zigbee2mqtt_topic}/{self.button_device_name}"
            client.subscribe(topic)
            print(f"Subscribed to topic: {topic}")
            
            if self.on_connection_change:
                self.on_connection_change(True)
        else:
            print(f"Failed to connect to MQTT broker, return code {rc}")
            self.connected = False
            if self.on_connection_change:
                self.on_connection_change(False)
    
    def _on_mqtt_disconnect(self, client, userdata, rc):
        """Callback for when MQTT client disconnects."""
        self.connected = False
        print("Disconnected from MQTT broker")
        if self.on_connection_change:
            self.on_connection_change(False)
    
    def _on_mqtt_message(self, client, userdata, msg):
        """Callback for when MQTT message is received."""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            # Check if this is our button device
            if not topic.endswith(self.button_device_name):
                return
            
            # Process button events
            self._process_button_event(payload)
            
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
    
    def _process_button_event(self, payload: dict):
        """Process button event from Zigbee2MQTT payload."""
        with self._lock:
            self.last_button_event = payload
            
            # Look for button press/release indicators
            # Common Zigbee button payloads include 'action', 'click', 'state' fields
            action = payload.get('action', '')
            click = payload.get('click', '')
            state = payload.get('state', '')
            
            # Determine if button is pressed or released
            button_now_pressed = False
            
            if action in ['single', 'hold', 'press', 'on']:
                button_now_pressed = True
            elif action in ['release', 'off']:
                button_now_pressed = False
            elif click in ['single', 'hold']:
                button_now_pressed = True
            elif state in ['ON', 'true', True, 1]:
                button_now_pressed = True
            elif state in ['OFF', 'false', False, 0]:
                button_now_pressed = False
            
            # Handle button state changes
            if button_now_pressed and not self.button_pressed:
                # Button just pressed
                self.button_pressed = True
                self.button_hold_start = time.time()
                print("Zigbee button pressed - activating siren")
                if self.on_button_press:
                    self.on_button_press()
                    
            elif not button_now_pressed and self.button_pressed:
                # Button just released
                self.button_pressed = False
                hold_duration = time.time() - self.button_hold_start if self.button_hold_start else 0
                print(f"Zigbee button released after {hold_duration:.1f}s - deactivating siren")
                if self.on_button_release:
                    self.on_button_release()
    
    def get_status(self) -> dict:
        """Get current status of the Zigbee siren controller."""
        with self._lock:
            return {
                'connected': self.connected,
                'button_pressed': self.button_pressed,
                'last_event': self.last_button_event,
                'mqtt_available': MQTT_AVAILABLE,
                'broker': f"{self.mqtt_broker}:{self.mqtt_port}",
                'device_name': self.button_device_name,
                'running': self._running
            }
    
    def is_connected(self) -> bool:
        """Check if controller is connected to MQTT broker."""
        return self.connected
    
    def is_button_pressed(self) -> bool:
        """Check if button is currently pressed."""
        return self.button_pressed


# Test/demo function for standalone usage
if __name__ == "__main__":
    def on_press():
        print("SIREN ON!")
        
    def on_release():
        print("SIREN OFF!")
        
    def on_connection(connected):
        print(f"Connection status: {'Connected' if connected else 'Disconnected'}")
    
    controller = ZigbeeSirenController()
    controller.set_callbacks(on_press, on_release, on_connection)
    
    if controller.start():
        print("Zigbee siren controller started. Press Ctrl+C to exit.")
        try:
            while True:
                status = controller.get_status()
                print(f"Status: {status}")
                time.sleep(5)
        except KeyboardInterrupt:
            print("Stopping...")
            controller.stop()
    else:
        print("Failed to start Zigbee siren controller")