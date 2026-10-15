import unittest
import json
import shutil
from pathlib import Path
from fastapi.testclient import TestClient

from src.server import app, CONTENT_DIR
from src.content_manager import ContentManager

class TestPlatformSwitchAndSoundMode(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.test_account = "test_switch_sound_acc"
        self.acc_dir = CONTENT_DIR / self.test_account
        if self.acc_dir.exists():
            shutil.rmtree(self.acc_dir, ignore_errors=True)
        self.acc_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.acc_dir.exists():
            shutil.rmtree(self.acc_dir, ignore_errors=True)

    def test_default_sound_mode_is_none_in_content_manager(self):
        """Verifikasi default sound_mode saat item dibaca adalah 'none' (No Sound)"""
        video_dir = self.acc_dir / "Video" / "2026-10-10"
        video_dir.mkdir(parents=True, exist_ok=True)
        dummy_vid = video_dir / "video-2026-10-10-01.mp4"
        dummy_vid.write_bytes(b"dummy mp4 content")

        # Scan content - metadata should default sound_mode to 'none'
        items = ContentManager.scan_content(self.test_account)
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item["meta"].get("sound_mode"), "none")

    def test_batch_schedule_saves_custom_platforms(self):
        """Verifikasi batch-schedule menyimpan daftar platform pilihan (misal: hanya IG dan FB)"""
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        future_iso = f"{future_date}T15:30:00"

        video_dir = self.acc_dir / "Video" / future_date
        video_dir.mkdir(parents=True, exist_ok=True)
        dummy_vid = video_dir / f"video-{future_date}-01.mp4"
        dummy_vid.write_bytes(b"dummy mp4 content")

        meta_file = video_dir / f"video-{future_date}-01.json"
        meta_file.write_text(json.dumps({
            "caption": "Test video",
            "sound_mode": "none",
            "platforms": ["tiktok", "instagram", "facebook"]
        }), encoding="utf-8")

        # Call batch schedule with custom platforms: ['instagram', 'facebook'] (TikTok turned OFF)
        res = self.client.post("/api/content/batch-schedule", json={
            "account": self.test_account,
            "items": [
                {
                    "category": "Video",
                    "date": future_date,
                    "item_name": f"video-{future_date}-01.mp4",
                    "scheduled_time": future_iso
                }
            ],
            "platforms": ["instagram", "facebook"]
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["updated_count"], 1)

        # Inspect saved meta.json
        with open(meta_file, "r", encoding="utf-8") as f:
            saved_meta = json.load(f)

        self.assertEqual(saved_meta["scheduled_time"], future_iso)
        self.assertEqual(saved_meta["platforms"], ["instagram", "facebook"])

    def test_save_caption_preserves_custom_platforms_and_defaults_sound_none(self):
        """Verifikasi save_caption tidak menimpa custom platforms dan default sound_mode adalah 'none'"""
        video_dir = self.acc_dir / "Video" / "2026-10-10"
        video_dir.mkdir(parents=True, exist_ok=True)
        dummy_vid = video_dir / "video-2026-10-10-01.mp4"
        dummy_vid.write_bytes(b"dummy mp4 content")

        meta_file = video_dir / "video-2026-10-10-01.json"
        meta_file.write_text(json.dumps({
            "caption": "Initial caption",
            "sound_mode": "none",
            "platforms": ["tiktok"]  # hanya tiktok aktif
        }), encoding="utf-8")

        # Save caption without specifying platforms or sound_mode
        res = self.client.post("/api/content/caption/save", json={
            "account": self.test_account,
            "category": "Video",
            "date": "2026-10-10",
            "item_name": "video-2026-10-10-01.mp4",
            "caption": "Updated caption"
        })
        self.assertEqual(res.status_code, 200)

        with open(meta_file, "r", encoding="utf-8") as f:
            saved_meta = json.load(f)

        self.assertEqual(saved_meta["caption"], "Updated caption")
        self.assertEqual(saved_meta["sound_mode"], "none")
        self.assertEqual(saved_meta["platforms"], ["tiktok"])

if __name__ == "__main__":
    unittest.main()
