import unittest
from pathlib import Path
from src.validator import ContentValidator
from src.account_manager import AccountManager
from src.config import AUDIO_PRESETS, slugify_account_name

class TestContentUploader(unittest.TestCase):

    def test_account_slug(self):
        slug = slugify_account_name("Demo International Brand")
        self.assertEqual(slug, "demo_international_brand")

    def test_account_creation(self):
        acc = AccountManager.create_or_get_account("Demo International Brand", "Sekolah Internasional")
        self.assertEqual(acc["name"], "Demo International Brand")
        self.assertEqual(acc["slug"], "demo_international_brand")

    def test_caption_sanitization(self):
        long_caption = "A" * 3000
        sanitized = ContentValidator.sanitize_caption(long_caption, platform="tiktok")
        self.assertTrue(len(sanitized) <= 2200)

    def test_audio_presets_exist(self):
        self.assertIn("voiceover", AUDIO_PRESETS)
        self.assertIn("balanced", AUDIO_PRESETS)
        self.assertIn("music_beat", AUDIO_PRESETS)
        self.assertIn("mute_original", AUDIO_PRESETS)

if __name__ == "__main__":
    unittest.main()
