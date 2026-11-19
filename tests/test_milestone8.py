import unittest
import time
from core.color import Color
from core.layout import KeyboardLayout
from effects.heatmap import TypingHeatmapManager
from integrations.system_stats import SystemTelemetry

class TestMilestone8(unittest.TestCase):
    def test_heatmap_heating_and_cooling(self):
        mgr = TypingHeatmapManager(led_count=81, heat_per_stroke=0.30, cooling_half_life=2.0)
        self.assertEqual(mgr.temperatures[75], 0.0)

        # Trigger Space key (75)
        mgr.trigger(75)
        self.assertAlmostEqual(mgr.temperatures[75], 0.30, places=2)

        # Trigger again to build heat
        mgr.trigger(75)
        self.assertAlmostEqual(mgr.temperatures[75], 0.60, places=2)

        # Cool down after half-life (2.0s)
        mgr.update(dt=2.0, current_time=time.monotonic() + 2.0)
        self.assertAlmostEqual(mgr.temperatures[75], 0.30, delta=0.05)

    def test_system_telemetry_sampling(self):
        telem = SystemTelemetry()
        stats = telem.sample()
        self.assertIn("cpu_usage", stats)
        self.assertIn("cpu_temp", stats)
        self.assertIn("memory_usage", stats)
        self.assertGreaterEqual(stats["cpu_usage"], 0.0)
        self.assertLessEqual(stats["cpu_usage"], 100.0)
        self.assertGreaterEqual(stats["memory_usage"], 0.0)
        self.assertLessEqual(stats["memory_usage"], 100.0)

if __name__ == '__main__':
    unittest.main()
