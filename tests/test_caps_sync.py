import unittest
from unittest.mock import MagicMock, patch
import evdev
from input.linux_evdev import LinuxEvdevListener

class MockEvdevDevice:
    def __init__(self, path="/dev/input/event3", name="URX URX Core75", has_led=True):
        self.path = path
        self.name = name
        self._has_led = has_led
        self.led_calls = []

    def capabilities(self):
        if self._has_led:
            return {evdev.ecodes.EV_LED: [evdev.ecodes.LED_CAPSL, evdev.ecodes.LED_NUML]}
        return {}

    def set_led(self, led_num, value):
        self.led_calls.append((led_num, value))

    def close(self):
        pass


class TestCapsSync(unittest.TestCase):
    def setUp(self):
        self.listener = LinuxEvdevListener()
        self.dev_kbd = MockEvdevDevice("/dev/input/event3", "URX URX Core75", has_led=True)
        self.dev_nkro = MockEvdevDevice("/dev/input/event7", "URX URX Core75 Keyboard", has_led=True)
        self.dev_mouse = MockEvdevDevice("/dev/input/event4", "URX URX Core75 Mouse", has_led=False)
        self.listener._devices = [self.dev_kbd, self.dev_nkro, self.dev_mouse]

    @patch.object(LinuxEvdevListener, "_query_caps_state", return_value=False)
    def test_startup_sync_sets_target_state(self, mock_query):
        """Verify on startup, sync applies actual state without artificial inverse pulses."""
        callback_calls = []
        self.listener.set_caps_lock_callback(lambda val: callback_calls.append(val))

        # First sync (startup)
        self.listener._sync_caps_lock(force=True)

        expected_calls = [(evdev.ecodes.LED_CAPSL, 0)]
        self.assertEqual(self.dev_kbd.led_calls, expected_calls)
        self.assertEqual(self.dev_nkro.led_calls, expected_calls)
        self.assertEqual(self.dev_mouse.led_calls, [])
        self.assertEqual(self.listener._last_synced_caps_state, False)
        self.assertEqual(callback_calls, [False])

    @patch.object(LinuxEvdevListener, "_query_caps_state", return_value=False)
    def test_no_redundant_writes_when_state_unchanged(self, mock_query):
        """Verify supervisor periodic ticks do not emit redundant writes when state is steady."""
        self.listener._sync_caps_lock(force=True)
        self.dev_kbd.led_calls.clear()
        self.dev_nkro.led_calls.clear()

        # Steady state periodic sync tick
        self.listener._sync_caps_lock(force=False)
        self.assertEqual(self.dev_kbd.led_calls, [])
        self.assertEqual(self.dev_nkro.led_calls, [])

    def test_runtime_toggle_emits_targeted_transition(self):
        """Verify state change from False to True emits single target update."""
        self.listener._last_synced_caps_state = False
        self.dev_kbd.led_calls.clear()
        self.dev_nkro.led_calls.clear()

        with patch.object(LinuxEvdevListener, "_query_caps_state", return_value=True):
            self.listener._sync_caps_lock(force=False)

        self.assertEqual(self.dev_kbd.led_calls, [(evdev.ecodes.LED_CAPSL, 1)])
        self.assertEqual(self.dev_nkro.led_calls, [(evdev.ecodes.LED_CAPSL, 1)])
        self.assertEqual(self.listener._last_synced_caps_state, True)


if __name__ == "__main__":
    unittest.main()
