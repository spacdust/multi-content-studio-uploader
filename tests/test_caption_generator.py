import unittest
import re
from src.caption_generator import CaptionGenerator

class TestCaptionGenerator(unittest.TestCase):

    def test_sanitize_llm_caption_max_4_hashtags(self):
        raw = (
            "Belajar asyik bersama santri di sekolah hari ini! "
            "Penuh semangat dan keceriaan.\n\n"
            "#school #education #santrikeren #fyp #viral #trending #islamic"
        )
        cleaned = CaptionGenerator.sanitize_llm_caption(raw, max_hashtags=4)
        hashtags = re.findall(r"#[A-Za-z0-9_]+", cleaned)
        self.assertEqual(len(hashtags), 4)
        self.assertEqual(hashtags, ["#school", "#education", "#santrikeren", "#fyp"])

    def test_fallback_caption_generation(self):
        caption = CaptionGenerator.generate_fallback_caption(
            topic="kegiatan_tahfidz_quran",
            category="Video",
            account_name="Demo School Official"
        )
        hashtags = re.findall(r"#[A-Za-z0-9_]+", caption)
        self.assertLessEqual(len(hashtags), 4)
        self.assertIn("Demo School Official", caption)
        self.assertIn("Kegiatan Tahfidz Quran", caption)

if __name__ == "__main__":
    unittest.main()
