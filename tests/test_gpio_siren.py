"""Headless checks for the Pi input, contact bounce and shared USB/GPIO siren."""
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gpio_siren_listener as listener
from test_arduino_siren import ArduinoRoutingTests


class DebounceTests(unittest.TestCase):
    def test_press_and_release_bounce_emit_one_event_each(self):
        button = listener.DebouncedButton()
        samples = [(1, 0), (0, .10), (1, .11), (0, .12), (0, .16),
                   (0, .18), (0, 1), (1, 1.1), (0, 1.12), (1, 1.14),
                   (1, 1.17), (1, 1.20), (1, 2)]
        events = [event for level, now in samples
                  if (event := button.update(level, now)) is not None]
        self.assertEqual(events, ['GPIO_ON', 'GPIO_OFF'])

    def test_initially_held_button_is_debounced(self):
        button = listener.DebouncedButton()
        self.assertIsNone(button.update(0, 0))
        self.assertIsNone(button.update(0, .025))
        self.assertEqual(button.update(0, .060), 'GPIO_ON')
        self.assertIsNone(button.update(0, 1))

    def test_short_pulse_is_ignored(self):
        button = listener.DebouncedButton()
        for level, now in [(1, 0), (0, .1), (1, .12), (1, .2)]:
            self.assertIsNone(button.update(level, now))


class ListenerTests(unittest.TestCase):
    def test_other_platform_does_not_start_worker(self):
        with patch.object(listener, 'is_pi5', return_value=False), \
                patch.object(listener, 'GPIOSirenListener') as worker:
            self.assertIsNone(listener.start_gpio_listener(SimpleNamespace()))
            worker.assert_not_called()

    def test_opt_out_and_duplicate_start(self):
        app = SimpleNamespace(handle_hardware_siren_event=Mock())
        with patch.object(listener, 'is_pi5', return_value=True), \
                patch.object(listener, 'GPIOSirenListener') as worker:
            with patch.dict('os.environ', {'UWH_GPIO_SIREN': '0'}):
                self.assertIsNone(listener.start_gpio_listener(app))
            with patch.dict('os.environ', {'UWH_GPIO_SIREN': '1'}):
                first = listener.start_gpio_listener(app)
                self.assertIs(listener.start_gpio_listener(app), first)
            worker.return_value.start.assert_called_once_with()

    def test_discovers_rp1_without_fixed_chip_number(self):
        gpio = Mock()
        gpio.gpiochip_open.side_effect = [10, 20]
        gpio.gpio_get_chip_info.side_effect = [
            (0, 32, 'gpiochip0', 'other-controller'),
            (0, 54, 'gpiochip4', 'pinctrl-rp1')]
        with patch.object(listener.Path, 'glob', return_value=[
                Path('/dev/gpiochip0'), Path('/dev/gpiochip4')]):
            self.assertEqual(listener.open_rp1(gpio), 20)
        gpio.gpiochip_close.assert_called_once_with(10)

    def test_claims_input_bias_off_and_releases_on_read_failure(self):
        gpio = Mock(SET_PULL_NONE=256)
        gpio.gpio_read.side_effect = [0, 0, OSError('device lost')]
        events = []
        worker = listener.GPIOSirenListener(events.append)
        with patch.dict(sys.modules, {'lgpio': gpio}), \
                patch.object(listener, 'open_rp1', return_value=7), \
                patch.object(listener.time, 'monotonic', side_effect=[0, .060]):
            worker._run()
        gpio.gpio_claim_input.assert_called_once_with(7, 17, 256)
        gpio.gpiochip_close.assert_called_once_with(7)
        self.assertIn('GPIO_ON', events)
        self.assertEqual(events[-1], 'GPIO_OFF')
        self.assertTrue(any('device lost' in event for event in events))

    def test_missing_dependency_reports_failure_without_stopping_app(self):
        events = []
        with patch.dict(sys.modules, {'lgpio': None}):
            listener.GPIOSirenListener(events.append)._run()
        self.assertIn('GPIO17 unavailable', events[0])
        self.assertEqual(events[-1], 'GPIO_OFF')

    def test_stop_closes_gpio_handle(self):
        gpio = Mock(SET_PULL_NONE=256)
        worker = listener.GPIOSirenListener(Mock())
        worker._stop.set()
        with patch.dict(sys.modules, {'lgpio': gpio}), \
                patch.object(listener, 'open_rp1', return_value=7):
            worker._run()
        gpio.gpio_read.assert_not_called()
        gpio.gpiochip_close.assert_called_once_with(7)


class CombinedInputTests(ArduinoRoutingTests):
    def test_gpio_only_press_release(self):
        self.app._process_hardware_siren_event('GPIO_ON')
        self.app._process_hardware_siren_event('GPIO_OFF')
        self.clip.play.assert_called_once_with(loops=-1)
        self.controller.start_siren_continuous.assert_called_once_with()
        self.controller.stop_siren_continuous.assert_called_once_with()

    def test_both_sources_start_once_and_stop_on_last_release(self):
        for event in ['GPIO_ON', 'ON', 'ON', 'GPIO_ON', 'GPIO_OFF', 'GPIO_OFF']:
            self.app._process_hardware_siren_event(event)
        self.clip.play.assert_called_once_with(loops=-1)
        self.controller.start_siren_continuous.assert_called_once_with()
        self.controller.stop_siren_continuous.assert_not_called()
        self.app._process_hardware_siren_event('OFF')
        self.app._process_hardware_siren_event('OFF')
        self.controller.stop_siren_continuous.assert_called_once_with()

    def test_usb_disconnect_does_not_cancel_gpio_hold(self):
        for event in ['ON', 'GPIO_ON', 'OFF', 'ARDUINO_SERIAL_ERROR:disconnected']:
            self.app._process_hardware_siren_event(event)
        self.controller.stop_siren_continuous.assert_not_called()
        self.app._process_hardware_siren_event('GPIO_OFF')
        self.controller.stop_siren_continuous.assert_called_once_with()

    def test_log_records_both_paths_even_when_output_does_not_change(self):
        for event in ['ON', 'GPIO_ON', 'GPIO_ON', 'OFF', 'GPIO_OFF', 'GPIO_OFF']:
            self.app._process_hardware_siren_event(event)
        self.assertEqual(
            [call.args[0] for call in self.app.add_to_zigbee_log.call_args_list],
            ['Arduino USB button: SIREN_ON received',
             'GPIO17 button: SIREN_ON received',
             'Arduino USB button: SIREN_OFF received',
             'GPIO17 button: SIREN_OFF received'])
        self.controller.start_siren_continuous.assert_called_once_with()
        self.controller.stop_siren_continuous.assert_called_once_with()

    def test_gpio_status_does_not_start_siren(self):
        self.app._process_hardware_siren_event('GPIO_STATUS:GPIO17 ready')
        self.app.add_to_zigbee_log.assert_called_once_with('GPIO17 ready')
        self.clip.play.assert_not_called()


if __name__ == '__main__':
    unittest.main()
