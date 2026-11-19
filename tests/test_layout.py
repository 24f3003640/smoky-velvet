import unittest
from pathlib import Path
from core.layout import KeyboardLayout, EVDEV_KEY_TO_LED

class TestLayout(unittest.TestCase):
    def setUp(self):
        json_path = Path(__file__).parent.parent / "hardware" / "layouts" / "URX_Core75_VIA.json"
        self.layout = KeyboardLayout.load_from_via_json(json_path)

    def test_led_count(self):
        self.assertEqual(self.layout.led_count, 81)

    def test_key_lookup(self):
        esc = self.layout.get_key(0)
        self.assertIsNotNone(esc)
        self.assertEqual(esc.name, "Escape")
        self.assertEqual(esc.x, 0.5)

        space = self.layout.get_key(75)
        self.assertIsNotNone(space)
        self.assertEqual(space.name, "Space")
        self.assertEqual(space.width, 6.25)

    def test_distance_symmetry(self):
        d1 = self.layout.distance(0, 75)
        d2 = self.layout.distance(75, 0)
        self.assertAlmostEqual(d1, d2)
        self.assertGreater(d1, 0.0)

    def test_evdev_keycodes(self):
        self.assertEqual(EVDEV_KEY_TO_LED["KEY_ESC"], 0)
        self.assertEqual(EVDEV_KEY_TO_LED["KEY_SPACE"], 75)
        self.assertEqual(EVDEV_KEY_TO_LED["KEY_ENTER"], 56)
        self.assertEqual(EVDEV_KEY_TO_LED["KEY_CAPSLOCK"], 44)

if __name__ == '__main__':
    unittest.main()
