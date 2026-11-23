import unittest
from unittest.mock import MagicMock
from core.layout import KeyboardLayout
from core.engine import LightingEngine

class DummyAdapter:
    def __init__(self):
        self.device = MagicMock()
        self.device.name = "Test URX Core75"
        self._is_paused = False

    @property
    def is_paused(self):
        return self._is_paused

    @property
    def is_connected(self):
        return True

    def connect(self):
        return True

    def disconnect(self):
        pass

    def pause_streaming(self):
        self._is_paused = True
        return True

    def resume_streaming(self):
        self._is_paused = False
        return True

    def send_frame(self, frame, force=False):
        return not self._is_paused or force

class TestEngineKnobAndHardwareMode(unittest.TestCase):
    def setUp(self):
        layout_mock = MagicMock()
        layout_mock.led_count = 81
        self.adapter = DummyAdapter()
        self.engine = LightingEngine(layout=layout_mock, adapter=self.adapter, enable_hyprland=False)

    def test_knob_volume_activity(self):
        self.engine.volume_gauge.trigger_activity = MagicMock()

        self.engine._on_knob_action("volume_up", 100.0)
        self.engine.volume_gauge.trigger_activity.assert_called_once()

        self.engine.volume_gauge.trigger_activity.reset_mock()
        self.engine._on_knob_action("volume_down", 101.0)
        self.engine.volume_gauge.trigger_activity.assert_called_once()

    def test_knob_gestures_toggle_mode(self):
        self.assertFalse(self.adapter.is_paused)

        # Long press toggles to Hardware Preset Mode
        self.engine._on_knob_action("knob_long_press", 100.0)
        self.assertTrue(self.adapter.is_paused)

        # Long press again toggles back to Smoky Velvet Software Mode
        self.engine._on_knob_action("knob_long_press", 105.0)
        self.assertFalse(self.adapter.is_paused)

        # Double click also toggles mode
        self.engine._on_knob_action("knob_double_click", 110.0)
        self.assertTrue(self.adapter.is_paused)

    def test_ipc_hardware_mode_and_volume(self):
        # Pause via IPC
        resp = self.engine._handle_ipc_command({"action": "hardware_mode"})
        self.assertEqual(resp.get("status"), "ok")
        self.assertTrue(self.adapter.is_paused)

        # Status check
        status = self.engine._handle_ipc_command({"action": "status"})
        self.assertTrue(status["data"]["hardware_mode"])
        self.assertIn("volume", status["data"])
        self.assertIn("muted", status["data"])

        # Resume via IPC
        resp = self.engine._handle_ipc_command({"action": "software_mode"})
        self.assertEqual(resp.get("status"), "ok")
        self.assertFalse(self.adapter.is_paused)

    def test_knob_media_next_prev_actions(self):
        self.engine._dispatch_mpris = MagicMock()

        # media_next should call _dispatch_mpris("Next")
        self.engine._on_knob_action("media_next", 200.0)
        self.engine._dispatch_mpris.assert_called_with("Next")

        # media_prev should call _dispatch_mpris("Previous")
        self.engine._on_knob_action("media_prev", 201.0)
        self.engine._dispatch_mpris.assert_called_with("Previous")

    def test_evdev_super_knob_mapping(self):
        from input.linux_evdev import LinuxEvdevListener
        listener = LinuxEvdevListener()

        # Default: volume up / down
        self.assertEqual(listener._resolve_knob_turn("up"), "volume_up")
        self.assertEqual(listener._resolve_knob_turn("down"), "volume_down")

        # With Super (Win key) held: media_next / media_prev
        with listener._modifier_lock:
            listener._active_modifiers.add("super")

        self.assertEqual(listener._resolve_knob_turn("up"), "media_next")
        self.assertEqual(listener._resolve_knob_turn("down"), "media_prev")

        # With Ctrl or Alt: workspace_next / workspace_prev
        with listener._modifier_lock:
            listener._active_modifiers.remove("super")
            listener._active_modifiers.add("ctrl")

        self.assertEqual(listener._resolve_knob_turn("up"), "workspace_next")
        self.assertEqual(listener._resolve_knob_turn("down"), "workspace_prev")

if __name__ == '__main__':
    unittest.main()
