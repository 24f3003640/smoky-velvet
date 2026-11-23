"""
Unit tests for Windows cross-platform compatibility layers:
- hardware/windows_hid.py (hidapi transport)
- input/windows_listener.py (pynput keystroke resolution and Win32 Caps Lock)
- core/ipc.py (Windows TCP socket transport)
"""
import unittest
from unittest.mock import MagicMock, patch
from core.color import Color
from core.layout import EVDEV_KEY_TO_LED
from hardware.windows_hid import WindowsSignalRGBAdapter, CMD_SIGNALRGB_ENABLE, CMD_SIGNALRGB_DISABLE, CMD_SIGNALRGB_STREAM
from input.windows_listener import WindowsInputListener, SPECIAL_KEY_MAP, CHAR_SYMBOL_MAP

class TestWindowsSupport(unittest.TestCase):

    def test_windows_hid_connect_and_stream(self):
        adapter = WindowsSignalRGBAdapter(led_count=82)

        mock_hid = MagicMock()
        mock_dev = MagicMock()
        mock_hid.device.return_value = mock_dev
        mock_hid.enumerate.return_value = [
            {"interface_number": 1, "path": b"\\\\?\\hid#vid_36b0&pid_3130#01"}
        ]

        with patch.dict("sys.modules", {"hid": mock_hid}):
            # Test connection
            connected = adapter.connect()
            self.assertTrue(connected)
            self.assertTrue(adapter.is_connected)

            # Verify 0x25 Enable packet written with 0x00 Report ID (33 bytes)
            mock_dev.open_path.assert_called_with(b"\\\\?\\hid#vid_36b0&pid_3130#01")
            write_calls = mock_dev.write.call_args_list
            self.assertGreater(len(write_calls), 0)
            first_pkt = write_calls[0][0][0]
            self.assertEqual(first_pkt[0], 0x00)
            self.assertEqual(first_pkt[1], CMD_SIGNALRGB_ENABLE)

            # Test frame transmission
            colors = [Color(255, 0, 0)] * 82
            sent = adapter.send_frame(colors, force=True)
            self.assertTrue(sent)

            # Verify stream packet structure (0x00, 0x24, start_idx, count...)
            stream_call = mock_dev.write.call_args[0][0]
            self.assertEqual(stream_call[0], 0x00)
            self.assertEqual(stream_call[1], CMD_SIGNALRGB_STREAM)

            # Test disconnection
            adapter.disconnect()
            self.assertFalse(adapter.is_connected)
            mock_dev.close.assert_called()

    def test_windows_input_key_resolution(self):
        listener = WindowsInputListener()

        # Character keys
        class MockCharKey:
            def __init__(self, char):
                self.char = char

        key_a = MockCharKey('a')
        self.assertEqual(listener._resolve_key_name(key_a), "KEY_A")
        self.assertEqual(EVDEV_KEY_TO_LED[listener._resolve_key_name(key_a)], 45)

        key_space = MockCharKey(' ')
        # Mock named special keys
        class MockNamedKey:
            def __init__(self, name):
                self.name = name

        k_space = MockNamedKey('space')
        self.assertEqual(listener._resolve_key_name(k_space), "KEY_SPACE")
        self.assertEqual(EVDEV_KEY_TO_LED[listener._resolve_key_name(k_space)], 75)

        k_caps = MockNamedKey('caps_lock')
        self.assertEqual(listener._resolve_key_name(k_caps), "KEY_CAPSLOCK")
        self.assertEqual(EVDEV_KEY_TO_LED[listener._resolve_key_name(k_caps)], 44)

        k_esc = MockNamedKey('esc')
        self.assertEqual(listener._resolve_key_name(k_esc), "KEY_ESC")
        self.assertEqual(EVDEV_KEY_TO_LED[listener._resolve_key_name(k_esc)], 0)

        k_del = MockNamedKey('delete')
        self.assertEqual(listener._resolve_key_name(k_del), "KEY_DELETE")
        self.assertEqual(EVDEV_KEY_TO_LED[listener._resolve_key_name(k_del)], 13)

    def test_windows_volume_actions(self):
        listener = WindowsInputListener()
        knob_events = []
        listener.set_knob_callback(lambda action, ts: knob_events.append(action))

        class MockNamedKey:
            def __init__(self, name):
                self.name = name

        listener._on_press(MockNamedKey('media_volume_up'))
        self.assertIn("volume_up", knob_events)

        listener._on_press(MockNamedKey('media_volume_down'))
        self.assertIn("volume_down", knob_events)

        listener._on_press(MockNamedKey('media_volume_mute'))
        self.assertIn("mute_click", knob_events)

    def test_windows_knob_win_key_media_track(self):
        import input.windows_listener
        listener = WindowsInputListener()
        knob_events = []
        listener.set_knob_callback(lambda action, ts: knob_events.append(action))

        class MockNamedKey:
            def __init__(self, name):
                self.name = name

        # Simulate Win key (VK_LWIN 0x5B) being held via mock windll
        mock_windll = MagicMock()
        mock_windll.user32.GetAsyncKeyState.side_effect = lambda vk: 0x8000 if vk == 0x5B else 0
        with patch.object(input.windows_listener.ctypes, "windll", mock_windll, create=True):
            listener._on_press(MockNamedKey('media_volume_up'))
            self.assertEqual(knob_events[-1], "media_next")

            listener._on_press(MockNamedKey('media_volume_down'))
            self.assertEqual(knob_events[-1], "media_prev")

if __name__ == "__main__":
    unittest.main()
