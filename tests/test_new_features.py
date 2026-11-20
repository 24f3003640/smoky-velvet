import unittest
import time
from core.layout import KeyboardLayout
from effects.wpm import WpmGaugeEffect, NUMBER_ROW_LEDS
from effects.pomodoro import PomodoroTimerEffect, FROW_LEDS
from effects.breathing import AmbientBreathingEffect
from effects.audio_pulse import AudioPulseEffect
from core.color import Color

class MockLayout:
    def __init__(self, count=82):
        self.led_count = count
    def distance(self, a, b):
        return abs(a - b) * 0.5

class TestNewFeatures(unittest.TestCase):
    def test_wpm_gauge_speed_calculation(self):
        wpm = WpmGaugeEffect(window_seconds=4.0)
        now = time.monotonic()
        # Simulate typing 20 keystrokes in 4 seconds = 4 words in 4s = 60 WPM
        for i in range(20):
            wpm.register_keystroke(now - (3.5 - i * 0.15))

        wpm.update(0.1, now)
        self.assertGreater(wpm.current_wpm, 15.0)

        # Verify buffer render fills number row keys
        layout = MockLayout()
        buffer = [None] * 82
        wpm.render(layout, buffer)
        # Should have at least one number key populated
        rendered = any(buffer[k] is not None for k in NUMBER_ROW_LEDS)
        self.assertTrue(rendered)

    def test_wpm_gauge_themes(self):
        wpm = WpmGaugeEffect(window_seconds=4.0)
        self.assertEqual(wpm.theme, "tachometer")
        self.assertTrue(wpm.set_theme("ice_cyan"))
        self.assertEqual(wpm.theme, "ice_cyan")
        self.assertTrue(wpm.set_theme("cyberpunk"))
        self.assertTrue(wpm.set_theme("amber_gold"))
        self.assertTrue(wpm.set_theme("neon_mint"))
        self.assertFalse(wpm.set_theme("invalid_theme"))

        now = time.monotonic()
        for i in range(25):
            wpm.register_keystroke(now - (3.5 - i * 0.12))
        wpm.update(0.1, now)
        layout = MockLayout()
        buffer = [None] * 82
        wpm.render(layout, buffer)
        # Key 15 ('1') should be rendered with a Color
        self.assertIsNotNone(buffer[15])
        col, opacity = buffer[15]
        self.assertGreater(opacity, 0.0)

    def test_pomodoro_timer_lifecycle(self):
        pomo = PomodoroTimerEffect()
        self.assertFalse(pomo.is_active)

        # Start 25 minute timer
        pomo.start_timer(25.0)
        self.assertTrue(pomo.is_active)
        self.assertTrue(pomo.enabled)
        self.assertIn(":", pomo.remaining_minutes_str)

        # Render countdown on F-row
        layout = MockLayout()
        buffer = [None] * 82
        pomo.render(layout, buffer)
        # Should have F-keys populated
        rendered_fkeys = [k for k in FROW_LEDS if buffer[k] is not None]
        self.assertEqual(len(rendered_fkeys), len(FROW_LEDS))

        # Cancel
        pomo.cancel()
        self.assertFalse(pomo.is_active)
        self.assertFalse(pomo.enabled)

    def test_ambient_breathing_effect(self):
        breath = AmbientBreathingEffect(period=4.0)
        breath.enabled = True
        breath.update(0.1, 1.0)
        layout = MockLayout()
        buffer = [None] * 82
        breath.render(layout, buffer)
        self.assertIsNotNone(buffer[0])
        # Opacity should be within safe low ambient range
        col, alpha = buffer[0]
        self.assertLessEqual(alpha, 0.40)
        self.assertGreaterEqual(alpha, 0.05)

    def test_audio_pulse_effect(self):
        pulse = AudioPulseEffect(origin_led=75)
        pulse.enabled = True
        now = time.monotonic()
        pulse.trigger_beat(energy=0.8, timestamp=now)
        layout = MockLayout()
        buffer = [None] * 82
        pulse.render(layout, buffer)
        # LEDs near spacebar should be populated
        self.assertIsNotNone(buffer[75])

if __name__ == "__main__":
    unittest.main()
