import shutil


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
