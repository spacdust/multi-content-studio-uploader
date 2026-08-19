import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from src.validator import ContentValidator
from src.account_manager import AccountManager
from src.config import AUDIO_PRESETS, slugify_account_name

class TestContentUploader(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_account_slug(self):
        slug = slugify_account_name("Demo International Brand")
        self.assertEqual(slug, "demo_international_brand")

    def test_account_creation_isolated(self):
        mock_acc_dir = Path(self.test_dir) / "test_acc"
        mock_acc_dir.mkdir(parents=True, exist_ok=True)
        with patch("src.account_manager.get_account_dir", return_value=mock_acc_dir):
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
