import time
import unittest
from core.color import Color
from core.layout import KeyboardLayout
from effects.volume_gauge import VolumeGaugeEffect, VOLUME_GRADIENT, MUTED_COLOR

class DummyLayout:
    led_count = 81

class TestVolumeGaugeEffect(unittest.TestCase):
    def setUp(self):
        self.effect = VolumeGaugeEffect(fade_timeout=1.0, fade_duration=0.5)

    def test_initial_state_and_trigger(self):
        self.assertFalse(self.effect.is_finished())
        self.effect.set_volume_state(0.50, muted=False)
        self.assertEqual(self.effect.current_volume, 0.50)
        self.assertFalse(self.effect.is_muted)

    def test_volume_bar_segmentation(self):
        layout = DummyLayout()
        buffer = [None] * 81

        # At 50% volume, exactly 6 of 12 F-keys should be lit with volume gradient
        self.effect.set_volume_state(0.50, muted=False)
        self.effect.render(layout, buffer)

        # F1 to F6 (indices 1 to 6) must have high alpha
        for i in range(1, 7):
            self.assertIsNotNone(buffer[i])
            col, alpha = buffer[i]
            self.assertGreater(alpha, 0.8)

        # F7 to F12 (indices 7 to 12) should have subtle track backdrop (alpha ~ 0.20)
        for i in range(7, 13):
            self.assertIsNotNone(buffer[i])
            col, alpha = buffer[i]
            self.assertLess(alpha, 0.3)

        # Delete key (index 13) should NOT be lit when unmuted
        self.assertIsNone(buffer[13])

    def test_muted_hardware_indicator(self):
        layout = DummyLayout()
        buffer = [None] * 81

        # When muted, Delete key (LED 13) must always glow in MUTED_COLOR
        self.effect.set_volume_state(0.40, muted=True)
        self.effect.render(layout, buffer)

        self.assertIsNotNone(buffer[13])
        col, alpha = buffer[13]
        self.assertEqual(col.r, MUTED_COLOR.r)
        self.assertEqual(col.g, MUTED_COLOR.g)
        self.assertEqual(col.b, MUTED_COLOR.b)
        self.assertGreaterEqual(alpha, 0.85)

        # F-keys should also display muted color pulse
        for i in range(1, 13):
            self.assertIsNotNone(buffer[i])
            col, _ = buffer[i]
            self.assertEqual(col.r, MUTED_COLOR.r)

    def test_fading_envelope(self):
        layout = DummyLayout()
        self.effect.set_volume_state(0.75, muted=False)

        # Simulate time passing beyond fade_timeout + fade_duration
        self.effect.last_active_time = time.monotonic() - 2.0
        buffer = [None] * 81
        self.effect.render(layout, buffer)

        # All F-keys should be empty (faded out cleanly)
        for i in range(1, 13):
            self.assertIsNone(buffer[i])

if __name__ == '__main__':
    unittest.main()
