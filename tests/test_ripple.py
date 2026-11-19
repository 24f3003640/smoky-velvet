import unittest
import time
from pathlib import Path
from core.color import Color
from core.layout import KeyboardLayout
from effects.ripple import SingleRipple, LiquidGoldRippleManager

class TestRipple(unittest.TestCase):
    def setUp(self):
        json_path = Path(__file__).parent.parent / "hardware" / "layouts" / "URX_Core75_VIA.json"
        self.layout = KeyboardLayout.load_from_via_json(json_path)

    def test_single_ripple_lifecycle(self):
        t0 = 100.0
        ripple = SingleRipple(origin_led=75, start_time=t0, duration=0.85, expansion=0.55)

        # At t=t0, origin LED (dist=0) should receive Champagne Glow
        ripple.update(t0)
        contrib = ripple.calculate_led_contribution(0.0)
        self.assertIsNotNone(contrib)
        col, alpha = contrib
        self.assertGreater(col.r, 200)
        self.assertGreater(alpha, 0.5)

        # After duration, ripple finishes
        ripple.update(t0 + 0.90)
        self.assertTrue(ripple.is_finished)
        self.assertIsNone(ripple.calculate_led_contribution(0.0))

    def test_ripple_propagation(self):
        t0 = 100.0
        ripple = SingleRipple(origin_led=75, start_time=t0, duration=0.85, expansion=0.55, max_radius=5.0)

        # At half expansion (age = 0.275), wave crest should be around radius 2.5
        ripple.update(t0 + 0.275)
        c_at_crest = ripple.calculate_led_contribution(2.5)
        c_far_away = ripple.calculate_led_contribution(10.0)

        self.assertIsNotNone(c_at_crest)
        self.assertIsNone(c_far_away)

    def test_ripple_manager(self):
        mgr = LiquidGoldRippleManager()
        self.assertTrue(mgr.is_finished())

        mgr.trigger(75, timestamp=100.0)
        self.assertFalse(mgr.is_finished())

        buffer = [None] * self.layout.led_count
        mgr.update(dt=0.1, current_time=100.1)
        mgr.render(self.layout, buffer)

        # Space key (75) should be illuminated
        self.assertIsNotNone(buffer[75])
        col, alpha = buffer[75]
        self.assertIsInstance(col, Color)
        self.assertGreater(alpha, 0.0)

if __name__ == '__main__':
    unittest.main()
