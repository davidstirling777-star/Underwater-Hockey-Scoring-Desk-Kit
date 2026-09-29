"""Headless checks for the configured MQTT startup self-test.

No broker, network, Tk windows, or actual MQTT credentials are required.
"""
import ast
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import startup_selftest as startup


class FakeMQTTClient:
    def __init__(self, reason_code=0, fail=False, silent=False):
        self.reason_code = reason_code
        self.fail = fail
        self.silent = silent
        self.connect_async = Mock()
        self.username_pw_set = Mock()
        self.disconnect = Mock()
        self.loop_stop = Mock()
        self.loop_start = Mock(side_effect=self._connected)

    def _connected(self):
        if self.silent:
            return
        if self.fail:
            self.on_connect_fail(self, None)
        else:
            self.on_connect(self, None, {}, self.reason_code, None)


def mqtt_module(client, paho_version2=True):
    """Supply a fake paho.mqtt.client to exercise the real import path."""
    root = types.ModuleType("paho")
    root.__path__ = []
    middle = types.ModuleType("paho.mqtt")
    middle.__path__ = []
    leaf = types.ModuleType("paho.mqtt.client")
    leaf.Client = Mock(return_value=client)
    if paho_version2:
        leaf.CallbackAPIVersion = types.SimpleNamespace(VERSION2=2)
    root.mqtt = middle
    middle.client = leaf
    return {
        "paho": root,
        "paho.mqtt": middle,
        "paho.mqtt.client": leaf,
    }, leaf


class ConfiguredMQTTStartupTests(unittest.TestCase):
    def test_remote_broker_and_authentication_are_used(self):
        client = FakeMQTTClient()
        modules, mqtt = mqtt_module(client)
        with patch.dict(sys.modules, modules):
            self.assertTrue(startup._mqtt_connect_once(
                "192.0.2.25", 28883, "uwh", "secret123", 0.1
            ))
        mqtt.Client.assert_called_once_with(callback_api_version=2)
        client.username_pw_set.assert_called_once_with("uwh", "secret123")
        client.connect_async.assert_called_once_with(
            "192.0.2.25", 28883, keepalive=5
        )
        client.loop_start.assert_called_once()
        client.disconnect.assert_called_once()
        client.loop_stop.assert_called_once()

    def test_anonymous_local_broker_does_not_set_username(self):
        client = FakeMQTTClient()
        modules, _ = mqtt_module(client)
        with patch.dict(sys.modules, modules):
            self.assertTrue(startup._mqtt_connect_once(
                "localhost", 1883, "", "", 0.1
            ))
        client.username_pw_set.assert_not_called()

    def test_rejected_authentication_is_not_a_false_success(self):
        client = FakeMQTTClient(reason_code=5)
        modules, _ = mqtt_module(client)
        with patch.dict(sys.modules, modules):
            self.assertFalse(startup._mqtt_connect_once(
                "broker.example", 1884, "bad", "wrong", 0.1
            ))
        client.loop_stop.assert_called_once()

    def test_connect_failure_does_not_pass_and_disconnects(self):
        client = FakeMQTTClient(fail=True)
        modules, _ = mqtt_module(client)
        with patch.dict(sys.modules, modules):
            self.assertFalse(startup._mqtt_connect_once(
                "offline.example", 1883, "", "", 0.1
            ))
        client.disconnect.assert_called_once()
        client.loop_stop.assert_called_once()

    def test_missing_connack_times_out_with_cleanup(self):
        client = FakeMQTTClient(silent=True)
        modules, _ = mqtt_module(client)
        with patch.dict(sys.modules, modules):
            with self.assertRaises(TimeoutError):
                startup._mqtt_connect_once(
                    "offline.example", 1883, "", "", 0.001
                )
        client.disconnect.assert_called_once()
        client.loop_stop.assert_called_once()

    def test_paho_one_compatibility(self):
        client = FakeMQTTClient()
        modules, mqtt = mqtt_module(client, paho_version2=False)
        with patch.dict(sys.modules, modules):
            self.assertTrue(startup._mqtt_connect_once(
                "older-broker", 1883, "", "", 0.1
            ))
        mqtt.Client.assert_called_once_with()

    def test_stable_checks_use_configured_endpoint_and_credentials(self):
        report = Mock()
        config = {
            "mqtt_broker": "remote.example",
            "mqtt_port": "28883",
            "mqtt_username": "score",
            "mqtt_password": "do-not-log-this",
        }
        with patch.object(startup, "_mqtt_connect_once",
                          side_effect=[True, True, True]) as probe:
            with patch.object(startup.time, "sleep", return_value=None):
                self.assertTrue(startup.check_mqtt_stability(
                    report, lambda: True, stable_threshold=3,
                    mqtt_config=config
                ))
        self.assertEqual(probe.call_count, 3)
        for call in probe.call_args_list:
            self.assertEqual(
                call.args[:4],
                ("remote.example", 28883, "score", "do-not-log-this")
            )
            self.assertGreater(call.args[4], 0)
            self.assertLessEqual(call.args[4], 3.0)
        self.assertTrue(any(
            "remote.example:28883" in c.args[0]
            for c in report.call_args_list
        ))
        self.assertFalse(any(
            "do-not-log-this" in str(c.args)
            for c in report.call_args_list
        ))

    def test_failed_check_resets_consecutive_stability_counter(self):
        with patch.object(
            startup, "_mqtt_connect_once",
            side_effect=[True, False, True, True, True]
        ) as probe:
            with patch.object(startup.time, "sleep", return_value=None):
                self.assertTrue(startup.check_mqtt_stability(
                    Mock(), lambda: True, stable_threshold=3
                ))
        self.assertEqual(probe.call_count, 5)

    def test_unavailable_mqtt_library_does_not_hold_startup(self):
        reporter = Mock()
        with patch.object(startup, "_mqtt_connect_once") as probe:
            self.assertFalse(startup.check_mqtt_stability(
                reporter, lambda: False, mqtt_config={"mqtt_broker": "remote"}
            ))
        probe.assert_not_called()
        self.assertIn("continuing", reporter.call_args.args[0])

    def test_invalid_port_does_not_probe_a_different_broker(self):
        reporter = Mock()
        with patch.object(startup, "_mqtt_connect_once") as probe:
            self.assertFalse(startup.check_mqtt_stability(
                reporter, lambda: True,
                mqtt_config={"mqtt_broker": "remote", "mqtt_port": 70000}
            ))
        probe.assert_not_called()
        self.assertIn("Invalid saved MQTT", reporter.call_args.args[0])

    def test_timeout_does_not_claim_zigbee_disabled(self):
        reporter = Mock()
        with patch.object(startup, "_mqtt_connect_once") as probe:
            self.assertFalse(startup.check_mqtt_stability(
                reporter, lambda: True, timeout_seconds=0
            ))
        probe.assert_not_called()
        self.assertIn("retry in background", reporter.call_args.args[0])

    def test_error_reporting_never_reveals_password(self):
        reporter = Mock()
        printed = []
        secret = "test-password-must-stay-secret"
        with patch.object(startup, "_mqtt_connect_once",
                          side_effect=ConnectionError(secret)):
            with patch.object(startup.time, "sleep", return_value=None):
                with patch("builtins.print",
                           side_effect=lambda *args: printed.append(str(args))):
                    self.assertFalse(startup.check_mqtt_stability(
                        reporter, lambda: True, timeout_seconds=0.025,
                        mqtt_config={
                            "mqtt_broker": "configured.example",
                            "mqtt_username": "user",
                            "mqtt_password": secret,
                        }
                    ))
        self.assertNotIn(secret, "\n".join(printed))
        self.assertNotIn(secret, str(reporter.call_args_list))

    def test_uwh_startup_passes_saved_zigbee_settings(self):
        source = (Path(__file__).resolve().parents[1] / "uwh.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        calls = [
            n for n in ast.walk(tree) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "check_mqtt_stability"
        ]
        self.assertEqual(len(calls), 1)
        kwargs = {k.arg: k.value for k in calls[0].keywords}
        self.assertIn("mqtt_config", kwargs)
        self.assertEqual(
            ast.unparse(kwargs["mqtt_config"]),
            "load_unified_settings().get('zigbeeSettings', {})"
        )


if __name__ == "__main__":
    unittest.main()
