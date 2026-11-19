import unittest
import tempfile
from pathlib import Path
from core.profile import Profile, ProfileManager

class TestProfile(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mgr = ProfileManager(profiles_dir=Path(self.temp_dir.name))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_profiles_created(self):
        self.assertIn("smoky_velvet", self.mgr.profiles)
        self.assertIn("coding", self.mgr.profiles)
        self.assertIn("study", self.mgr.profiles)
        self.assertIn("gaming", self.mgr.profiles)
        self.assertIn("night", self.mgr.profiles)

    def test_profile_serialization(self):
        prof = self.mgr.get_profile("smoky_velvet")
        self.assertIsNotNone(prof)
        self.assertEqual(prof.base_color_hex, "#30183F")
        self.assertTrue(prof.reactive_enabled)

    def test_custom_profile_save_and_load(self):
        custom = Profile(
            name="amber_wave",
            description="Amber test profile",
            base_color_hex="#402000",
            brightness=0.75,
            reactive_enabled=True
        )
        self.mgr.save_profile(custom)
        reloaded = self.mgr.get_profile("amber_wave")
        self.assertIsNotNone(reloaded)
        self.assertEqual(reloaded.base_color_hex, "#402000")
        self.assertEqual(reloaded.brightness, 0.75)

    def test_active_profile_switching(self):
        self.assertTrue(self.mgr.set_active("coding"))
        self.assertEqual(self.mgr.active_profile_name, "coding")
        self.assertFalse(self.mgr.set_active("non_existent_profile"))

if __name__ == '__main__':
    unittest.main()
