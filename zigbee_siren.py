"""
Zigbee2MQTT Wireless Siren Integration Module

serial_siren_listener.py is the lead hardware detector.
This module does not scan COM ports directly. It references the Zigbee COM
port discovered/cached by serial_siren_listener when serial fallback needs it.
"""

import threading
import time
import logging
import json
import os
import platform
from typing import Optional, Callable, Dict, Any

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    mqtt = None

try:
    import serial
    PYSERIAL_AVAILABLE = True
except ImportError:
    PYSERIAL_AVAILABLE = False
    serial = None

try:
    import serial_siren_listener
except Exception:
    serial_siren_listener = None

CURRENT_PLATFORM = platform.system()
IS_WINDOWS = CURRENT_PLATFORM == "Windows"
IS_LINUX = CURRENT_PLATFORM == "Linux"

SETTINGS_FILE = "settings.json"
ZIGBEE_CONFIG_FILE = "zigbee_config.json"

DEFAULT_CONFIG = {
    "mqtt_broker": "localhost",
    "mqtt_port": 1883,
    "mqtt_username": "",
    "mqtt_password": "",
    "mqtt_topic": "zigbee2mqtt/+",
    "siren_button_devices": ["siren_button"],
    "siren_button_device": "siren_button",
    "siren_device_name": "zigbee_siren",
    "connection_timeout": 60,
    "reconnect_delay": 5,
    "enable_logging": True,
    "serial_port": "",
    "serial_baudrate": 115200,
    "serial_timeout": 1.0,
    "use_serial_fallback": True,
    "prefer_mqtt": True,
}


def get_zigbee_port_from_lead_detector():
    """Get Zigbee COM port from serial_siren_listener, if available."""
    try:
        if serial_siren_listener:
            return serial_siren_listener.get_zigbee_port()
    except Exception as e:
        print(f"Could not get Zigbee port from serial_siren_listener: {e}")

    return ""


class ZigbeeSirenController:
    """Controls wireless siren functionality through Zigbee2MQTT."""

    def __init__(
        self,
        siren_callback: Optional[Callable] = None,
        gui_log_callback: Optional[Callable[[str], None]] = None
    ):
        self.siren_callback = siren_callback
        self.gui_log_callback = gui_log_callback
        self.mqtt_client: Optional[mqtt.Client] = None
        self.connected = False
        self.connection_thread: Optional[threading.Thread] = None
        self.should_stop = threading.Event()
        self.connection_status_callback: Optional[Callable[[bool, str], None]] = None

        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        self.logger.info(f"Zigbee controller initializing on {CURRENT_PLATFORM}")

        self.config = self.load_config()

        if not self.config.get("serial_port"):
            self.config["serial_port"] = get_zigbee_port_from_lead_detector()

        self.logger.setLevel(
            logging.INFO if self.config.get("enable_logging", True) else logging.WARNING
        )

        if not MQTT_AVAILABLE:
            self.logger.warning("paho-mqtt not available. Zigbee siren functionality disabled.")

    def _migrate_device_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        if "siren_button_device" in config and "siren_button_devices" not in config:
            single_device = config["siren_button_device"]
            if isinstance(single_device, str) and single_device:
                config["siren_button_devices"] = [single_device]
                self.logger.info(
                    f"Migrated single device '{single_device}' to device list format"
                )

        if "siren_button_devices" in config and "siren_button_device" not in config:
            device_list = config["siren_button_devices"]
            if isinstance(device_list, list) and device_list:
                config["siren_button_device"] = device_list[0]

        if "siren_button_devices" not in config:
            config["siren_button_devices"] = [
                config.get("siren_button_device", "siren_button")
            ]
        elif isinstance(config["siren_button_devices"], str):
            config["siren_button_devices"] = [config["siren_button_devices"]]

        return config

    def load_config(self) -> Dict[str, Any]:
        settings_path = os.path.join(os.getcwd(), SETTINGS_FILE)

        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    unified_settings = json.load(f)

                config = unified_settings.get("zigbeeSettings", {})
                if config:
                    config = self._migrate_device_config(config)
                    merged_config = DEFAULT_CONFIG.copy()
                    merged_config.update(config)
                    return merged_config

            except Exception as e:
                self.logger.error(f"Error loading unified config: {e}. Trying legacy file.")

        legacy_path = os.path.join(os.getcwd(), ZIGBEE_CONFIG_FILE)

        if os.path.exists(legacy_path):
            try:
                with open(legacy_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                config = self._migrate_device_config(config)
                merged_config = DEFAULT_CONFIG.copy()
                merged_config.update(config)
                self.save_config(merged_config)
                return merged_config

            except Exception as e:
                self.logger.error(f"Error loading legacy config: {e}. Using defaults.")

        default_config = DEFAULT_CONFIG.copy()
        default_config = self._migrate_device_config(default_config)
        self.save_config(default_config)
        return default_config

    def save_config(self, config: Dict[str, Any]) -> None:
        try:
            settings_path = os.path.join(os.getcwd(), SETTINGS_FILE)
            unified_settings = {}

            if os.path.exists(settings_path):
                try:
                    with open(settings_path, "r", encoding="utf-8") as f:
                        unified_settings = json.load(f)
                except Exception:
                    unified_settings = {}

            unified_settings.setdefault("zigbeeSettings", {})
            unified_settings.setdefault("soundSettings", {})
            unified_settings.setdefault("gameSettings", {})

            unified_settings["zigbeeSettings"] = config

            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(unified_settings, f, indent=2)

            self.config = config

        except Exception as e:
            self.logger.error(f"Error saving config: {e}")

    def set_siren_callback(self, callback: Callable) -> None:
        self.siren_callback = callback

    def set_connection_status_callback(
        self,
        callback: Callable[[bool, str], None]
    ) -> None:
        self.connection_status_callback = callback

    def start(self) -> bool:
        if not MQTT_AVAILABLE:
            self._notify_status(False, "MQTT library not available")
            return False

        if self.connection_thread and self.connection_thread.is_alive():
            self.logger.warning("Controller already running")
            return True

        self.should_stop.clear()
        self.connection_thread = threading.Thread(
            target=self._connection_loop,
            daemon=True
        )
        self.connection_thread.start()

        self.logger.info("Zigbee siren controller started")
        return True

    def stop(self) -> None:
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
        while not self.should_stop.is_set():
            try:
                self._setup_mqtt_client()
                self._connect_mqtt()

                while self.connected and not self.should_stop.is_set():
                    time.sleep(1)

            except Exception as e:
                self.logger.error(f"Connection error: {e}")
                self._notify_status(False, f"Error: {e}")

            if not self.should_stop.is_set():
                delay = self.config.get("reconnect_delay", 5)
                self.logger.info(f"Reconnecting in {delay} seconds...")
                time.sleep(delay)

    def _setup_mqtt_client(self) -> None:
        self.mqtt_client = mqtt.Client()

        if self.config.get("mqtt_username"):
            self.mqtt_client.username_pw_set(
                self.config.get("mqtt_username", ""),
                self.config.get("mqtt_password", "")
            )

        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_disconnect = self._on_disconnect
        self.mqtt_client.on_message = self._on_message

        self.mqtt_client.connect_async(
            self.config.get("mqtt_broker", "localhost"),
            int(self.config.get("mqtt_port", 1883)),
            int(self.config.get("connection_timeout", 60))
        )

    def _connect_mqtt(self) -> None:
        self.mqtt_client.loop_start()

        timeout = time.time() + int(self.config.get("connection_timeout", 60))

        while (
            not self.connected
            and time.time() < timeout
            and not self.should_stop.is_set()
        ):
            time.sleep(0.1)

        if not self.connected:
            try:
                self.mqtt_client.loop_stop()
            except Exception:
                pass
            raise Exception("Connection timeout")

    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc == 0:
            self.connected = True

            broker = self.config.get("mqtt_broker", "localhost")
            port = self.config.get("mqtt_port", 1883)

            self.logger.info(f"Connected to MQTT broker {broker}:{port}")

            topic = self.config.get("mqtt_topic", "zigbee2mqtt/+")
            client.subscribe(topic)

            self.logger.info(f"Subscribed to topic: {topic}")
            self._notify_status(True, "Connected")

        else:
            self.connected = False
            self.logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
            self._notify_status(False, f"Connection failed (RC: {rc})")

    def _on_disconnect(self, client, userdata, rc) -> None:
        self.connected = False

        if rc != 0:
            self.logger.warning(f"Unexpected disconnection from MQTT broker. RC: {rc}")
            self._notify_status(False, "Disconnected unexpectedly")
        else:
            self.logger.info("Disconnected from MQTT broker")
            self._notify_status(False, "Disconnected")

    def _on_message(self, client, userdata, msg) -> None:
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")

            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                self.logger.warning(f"Invalid JSON in message: {payload}")
                return

            device_name = topic.split("/")[-1]
            configured_devices = list(self.config.get("siren_button_devices", []))

            legacy_device = self.config.get("siren_button_device", "")
            if legacy_device and legacy_device not in configured_devices:
                configured_devices.append(legacy_device)

            if device_name in configured_devices:
                self._process_button_event(device_name, data)

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")

    def _process_button_event(self, device_name: str, data: Dict[str, Any]) -> None:
        try:
            action = None

            if "action" in data:
                action = data["action"]
            elif "click" in data:
                action = data["click"]
            elif "state" in data:
                action = data["state"]

            if action is None:
                return

            self.logger.info(f"Button action from {device_name}: {action}")

            if self.gui_log_callback:
                self.gui_log_callback(
                    f"Button '{device_name}' action '{action}' received via Zigbee/MQTT."
                )

            if str(action).lower() in ["single", "press", "click", "on", "1"]:
                self._trigger_siren()

        except Exception as e:
            self.logger.error(f"Error processing button event: {e}")

    def _trigger_siren(self) -> None:
        self.logger.info("Triggering wireless siren")

        if self.siren_callback:
            try:
                threading.Thread(
                    target=self.siren_callback,
                    daemon=True
                ).start()
            except Exception as e:
                self.logger.error(f"Error calling siren callback: {e}")
        else:
            self.logger.warning("No siren callback set")

    def test_siren(self) -> None:
        self.logger.info("Manual MQTT siren test triggered")

        if self.gui_log_callback:
            self.gui_log_callback("Manual MQTT siren test triggered")

        self.start_siren_continuous()

    def stop_test_siren(self) -> None:
        self.logger.info("Manual MQTT siren test stopping")

        if self.gui_log_callback:
            self.gui_log_callback("Manual MQTT siren test stopping")

        self.stop_siren_continuous()

    def start_siren_continuous(self, sound_config: Dict[str, Any] = None) -> None:
        self.logger.info("Starting continuous siren playback")
        self.start_siren()

    def stop_siren_continuous(self) -> None:
        self.logger.info("Stopping continuous siren playback")
        self.stop_siren()

    def start_siren(self) -> bool:
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

            self.logger.info(
                f"Starting siren: Publishing to {topic} with payload {payload}"
            )

            if self.gui_log_callback:
                self.gui_log_callback(f"MQTT publish topic: {topic}")
                self.gui_log_callback(f"MQTT publish payload: {payload}")
                self.gui_log_callback(f"MQTT connected: {self.connected}")

            result = self.mqtt_client.publish(topic, payload)

            try:
                result.wait_for_publish(timeout=2)
            except TypeError:
                result.wait_for_publish()

            return True

        except Exception as e:
            self.logger.error(f"Error starting siren: {e}")
            return False

    def stop_siren(self) -> bool:
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

            self.logger.info(
                f"Stopping siren: Publishing to {topic} with payload {payload}"
            )

            if self.gui_log_callback:
                self.gui_log_callback(f"MQTT publish topic: {topic}")
                self.gui_log_callback(f"MQTT publish payload: {payload}")
                self.gui_log_callback(f"MQTT connected: {self.connected}")

            result = self.mqtt_client.publish(topic, payload)

            try:
                result.wait_for_publish(timeout=2)
            except TypeError:
                result.wait_for_publish()

            return True

        except Exception as e:
            self.logger.error(f"Error stopping siren: {e}")
            return False

    def _notify_status(self, connected: bool, message: str) -> None:
        if self.connection_status_callback:
            try:
                self.connection_status_callback(connected, message)
            except Exception as e:
                self.logger.error(f"Error calling status callback: {e}")

    def get_status(self) -> Dict[str, Any]:
        devices = list(self.config.get("siren_button_devices", []))
        legacy_device = self.config.get("siren_button_device", "")

        if legacy_device and legacy_device not in devices:
            devices.append(legacy_device)

        return {
            "connected": self.connected,
            "mqtt_available": MQTT_AVAILABLE,
            "broker": f"{self.config.get('mqtt_broker', 'localhost')}:{self.config.get('mqtt_port', 1883)}",
            "topic": self.config.get("mqtt_topic", "zigbee2mqtt/+"),
            "devices": devices,
            "device": legacy_device,
            "zigbee_port": self.config.get("serial_port", ""),
        }

    def test_connection(self) -> bool:
        if not MQTT_AVAILABLE:
            return False

        try:
            test_client = mqtt.Client()

            if self.config.get("mqtt_username"):
                test_client.username_pw_set(
                    self.config.get("mqtt_username", ""),
                    self.config.get("mqtt_password", "")
                )

            test_client.connect(
                self.config.get("mqtt_broker", "localhost"),
                int(self.config.get("mqtt_port", 1883)),
                10
            )
            test_client.disconnect()
            return True

        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False


def get_default_config() -> Dict[str, Any]:
    config = DEFAULT_CONFIG.copy()
    config["serial_port"] = get_zigbee_port_from_lead_detector()
    return config


def is_mqtt_available() -> bool:
    return MQTT_AVAILABLE


def is_pyserial_available() -> bool:
    return PYSERIAL_AVAILABLE


def get_platform_info() -> Dict[str, Any]:
    return {
        "platform": CURRENT_PLATFORM,
        "is_windows": IS_WINDOWS,
        "is_linux": IS_LINUX,
        "mqtt_available": MQTT_AVAILABLE,
        "pyserial_available": PYSERIAL_AVAILABLE,
    }


def create_controller(
    siren_callback: Optional[Callable] = None,
    gui_log_callback: Optional[Callable[[str], None]] = None
):
    logger = logging.getLogger(__name__)
    logger.info(f"Running on {CURRENT_PLATFORM} - using standard MQTT controller")

    return ZigbeeSirenController(
        siren_callback=siren_callback,
        gui_log_callback=gui_log_callback
    )
