import shutil
import threading
import time


def _mqtt_connect_once(host, port, username, password, timeout_seconds):
    """Test a real MQTT CONNACK, not just an open TCP port.

    A successful TCP connection alone can misreport an authenticated broker
    as healthy when the credentials have been rejected. Use a short-lived
    Paho client so the real controller's subscriptions remain untouched.
    """
    import paho.mqtt.client as mqtt_test

    try:
        client = mqtt_test.Client(
            callback_api_version=mqtt_test.CallbackAPIVersion.VERSION2
        )
    except (AttributeError, TypeError):
        # Paho MQTT 1.x uses the original callback API.
        client = mqtt_test.Client()

    received = threading.Event()
    accepted = [False]

    def on_connect(_client, _userdata, _flags, reason_code, *args):
        accepted[0] = reason_code == 0
        received.set()

    def on_connect_fail(_client, _userdata):
        received.set()

    client.on_connect = on_connect
    client.on_connect_fail = on_connect_fail

    running = False
    try:
        if username:
            client.username_pw_set(username, password)
        client.connect_async(host, port, keepalive=5)
        client.loop_start()
        running = True
        if not received.wait(timeout_seconds):
            raise TimeoutError("No MQTT connection acknowledgement received")
        return accepted[0]
    finally:
        try:
            client.disconnect()
        finally:
            if running:
                client.loop_stop()


def check_mqtt_stability(
    splash_report,
    is_mqtt_available,
    timeout_seconds=30,
    stable_threshold=3,
    mqtt_config=None
):
    """Check the configured broker without changing UWH's live MQTT client.

    A failed self-test is diagnostic only: the real controller is always
    allowed to start and retry its connection in the background.
    """
    config = mqtt_config if isinstance(mqtt_config, dict) else {}
    host = str(config.get("mqtt_broker") or "localhost").strip()
    username = str(config.get("mqtt_username") or "")
    password = str(config.get("mqtt_password") or "")

    try:
        port = int(config.get("mqtt_port", 1883))
        if not 1 <= port <= 65535 or not host:
            raise ValueError("Invalid MQTT broker address or port")
    except (ValueError, TypeError):
        splash_report(
            "Invalid saved MQTT broker or port; check Zigbee configuration",
            False
        )
        print("STARTUP: Invalid saved MQTT broker or port")
        return False

    if not is_mqtt_available():
        splash_report("MQTT Python library unavailable; continuing", False)
        print("STARTUP: MQTT Python library unavailable; continuing")
        return False

    deadline = time.monotonic() + max(0.0, float(timeout_seconds))
    mqtt_stable_count = 0
    mqtt_connection_attempts = 0

    splash_report(f"Checking configured MQTT broker {host}:{port}", True)
    print(f"STARTUP: Checking configured MQTT broker {host}:{port}")

    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break

        mqtt_connection_attempts += 1
        splash_report(
            f"Checking MQTT broker attempt {mqtt_connection_attempts}",
            True
        )

        try:
            acknowledged = _mqtt_connect_once(
                host, port, username, password, min(3.0, remaining)
            )
        except Exception as error:
            # Never log the config dictionary or a password. The exception
            # type is enough to locate DNS, connection and timing problems.
            print(
                f"STARTUP: MQTT check {mqtt_connection_attempts} failed "
                f"({type(error).__name__}); will retry"
            )
            acknowledged = False

        if acknowledged:
            mqtt_stable_count += 1
            splash_report(
                f"MQTT check {mqtt_stable_count}/{stable_threshold} passed",
                True
            )
            print(
                f"STARTUP: MQTT check "
                f"{mqtt_stable_count}/{stable_threshold} passed"
            )
            if mqtt_stable_count >= stable_threshold:
                splash_report("MQTT connection stable", True)
                print("STARTUP: Configured MQTT connection is stable")
                return True
        else:
            mqtt_stable_count = 0
            splash_report(
                f"MQTT broker {host}:{port} not ready; retrying", False
            )

        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(2.0, remaining))

    splash_report(
        "MQTT broker not ready; Zigbee will retry in background", False
    )
    print(
        f"STARTUP: MQTT check timed out after {timeout_seconds}s; "
        "Zigbee controller will still start and retry"
    )
    return False

def check_mosquitto_installed():
    return shutil.which("mosquitto") is not None


def check_zigbee2mqtt_installed():
    return shutil.which("zigbee2mqtt") is not None


def report_installation_status(splash_report):
    mosquitto_installed = check_mosquitto_installed()

    splash_report(
        "Mosquitto MQTT Broker installed"
        if mosquitto_installed
        else "Mosquitto MQTT Broker not found - install from https://mosquitto.org/download/",
        mosquitto_installed
    )

    zigbee2mqtt_installed = check_zigbee2mqtt_installed()

    splash_report(
        "Zigbee2MQTT installed"
        if zigbee2mqtt_installed
        else "Zigbee2MQTT executable not found on PATH",
        zigbee2mqtt_installed
    )

    return mosquitto_installed, zigbee2mqtt_installed
