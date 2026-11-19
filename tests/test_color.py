import unittest
from core.color import Color, Gradient, MIDNIGHT_PURPLE, CHAMPAGNE_GLOW, WARM_GOLD, ANTIQUE_GOLD, DEEP_OLD_GOLD, LIQUID_GOLD_GRADIENT

class TestColor(unittest.TestCase):
    def test_hex_conversion(self):
        c = Color.from_hex("#30183F")
        self.assertEqual(c.r, 48)
        self.assertEqual(c.g, 24)
        self.assertEqual(c.b, 63)
        self.assertEqual(c.to_hex(), "#30183F")

    def test_clamping(self):
        c = Color(-10, 300, 128)
        self.assertEqual(c.r, 0)
        self.assertEqual(c.g, 255)
        self.assertEqual(c.b, 128)

    def test_lerp(self):
        black = Color(0, 0, 0)
        white = Color(200, 200, 200)
        mid = black.lerp(white, 0.5)
        self.assertEqual(mid.r, 100)
        self.assertEqual(mid.g, 100)
        self.assertEqual(mid.b, 100)

    def test_additive_blend(self):
        c1 = Color(100, 50, 0)
        c2 = Color(100, 100, 200)
        blended = c1.blend_additive(c2, alpha=1.0)
        self.assertEqual(blended.r, 200)
        self.assertEqual(blended.g, 150)
        self.assertEqual(blended.b, 200)

    def test_gradient_stops(self):
        # Stop 0 should be Champagne Glow
        self.assertEqual(LIQUID_GOLD_GRADIENT.sample(0.0), CHAMPAGNE_GLOW)
        # Stop 1 should be Deep Old Gold
        self.assertEqual(LIQUID_GOLD_GRADIENT.sample(1.0), DEEP_OLD_GOLD)
        # Intermediate stop
        mid = LIQUID_GOLD_GRADIENT.sample(0.5)
        self.assertIsInstance(mid, Color)

if __name__ == '__main__':
    unittest.main()
