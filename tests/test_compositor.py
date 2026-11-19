import unittest
from pathlib import Path
from core.color import Color, MIDNIGHT_PURPLE
from core.compositor import Compositor
from core.layout import KeyboardLayout

class TestCompositor(unittest.TestCase):
    def setUp(self):
        json_path = Path(__file__).parent.parent / "hardware" / "layouts" / "URX_Core75_VIA.json"
        self.layout = KeyboardLayout.load_from_via_json(json_path)
        self.comp = Compositor(self.layout)

    def test_default_base_render(self):
        frame, is_dirty = self.comp.render_frame()
        self.assertTrue(is_dirty)
        self.assertEqual(len(frame), 81)
        self.assertEqual(frame[0], MIDNIGHT_PURPLE)

    def test_dirty_caching(self):
        frame1, is_dirty1 = self.comp.render_frame()
        self.assertTrue(is_dirty1)

        # Second identical render should report is_dirty == False
        frame2, is_dirty2 = self.comp.render_frame()
        self.assertFalse(is_dirty2)

    def test_indicator_override(self):
        white = Color(255, 255, 255)
        self.comp.indicator_layer.set_indicator(44, white, opacity=1.0)
        frame, is_dirty = self.comp.render_frame()
        self.assertTrue(is_dirty)
        # Caps lock key (44) should be overridden to white
        self.assertEqual(frame[44], white)
        # Other keys should remain Midnight Purple
        self.assertEqual(frame[0], MIDNIGHT_PURPLE)

    def test_brightness_scaling(self):
        self.comp.set_brightness(0.5)
        frame, _ = self.comp.render_frame()
        # Midnight purple is (48, 24, 63); half brightness should be ~(24, 12, 32)
        self.assertEqual(frame[0].r, 24)
        self.assertEqual(frame[0].g, 12)
        self.assertEqual(frame[0].b, 32)

if __name__ == '__main__':
    unittest.main()
