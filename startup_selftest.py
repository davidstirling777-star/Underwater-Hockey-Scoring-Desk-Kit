import shutil
import time

def check_mqtt_stability(
    splash_report,
    is_mqtt_available,
    timeout_seconds=30,
    stable_threshold=3
):
    mqtt_connection_stable = False
    mqtt_check_start = time.time()
    mqtt_connection_attempts = 0
    mqtt_stable_count = 0

    splash_report("Beginning MQTT stability verification", True)
    print("STARTUP: Beginning MQTT stability verification...")

    while time.time() - mqtt_check_start < timeout_seconds:
        mqtt_connection_attempts += 1

        splash_report(
            f"Checking MQTT broker attempt {mqtt_connection_attempts}",
            True
        )

        try:
            if is_mqtt_available():
                import paho.mqtt.client as mqtt_test

                try:
                    test_client = mqtt_test.Client(
                        callback_api_version=mqtt_test.CallbackAPIVersion.VERSION2
                    )
                except AttributeError:
                    test_client = mqtt_test.Client()

                try:
                    test_client.connect("localhost", 1883, keepalive=5)
                    test_client.disconnect()

                    mqtt_stable_count += 1

                    splash_report(
                        f"MQTT check {mqtt_stable_count}/{stable_threshold} passed",
                        True
                    )

                    print(
                        f"STARTUP: MQTT connection check "
                        f"{mqtt_stable_count}/{stable_threshold} passed"
                    )

                    if mqtt_stable_count >= stable_threshold:
                        mqtt_connection_stable = True
                        splash_report("MQTT connection stable", True)
                        break

                except Exception as mqtt_err:
                    mqtt_stable_count = 0
                    splash_report(
                        f"MQTT connection test failed: {mqtt_err}",
                        False
                    )
                    print(f"STARTUP: MQTT connection test failed: {mqtt_err}")

            else:
                splash_report("MQTT library not available - continuing", False)
                print("STARTUP: MQTT not available, continuing without Zigbee support")
                mqtt_connection_stable = True
                break

        except Exception as init_err:
            mqtt_stable_count = 0
            splash_report(f"MQTT check error: {init_err}", False)
            print(f"STARTUP: MQTT check error: {init_err}")

        time.sleep(2)

    if mqtt_connection_stable:
        print("STARTUP: MQTT network connection is STABLE - proceeding with initialization")
        splash_report("MQTT ready", True)
    else:
        print(
            f"STARTUP: MQTT timeout after {timeout_seconds}s - continuing without Zigbee"
        )
        splash_report("MQTT unavailable - continuing without Zigbee", False)

    return mqtt_connection_stable

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
