import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.server import app
from src.content_manager import ContentManager

class TestMultiVideoUpload(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.test_dir = tempfile.mkdtemp()
        self.test_account = "Unit_Test_Multi_Account"
        self.test_date = "2026-10-09"

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("src.server._trigger_background_auto_caption")
    def test_upload_five_videos_creates_five_separate_reels(self, mock_caption):
        with patch("src.server.CONTENT_DIR", Path(self.test_dir)), \
             patch("src.content_manager.CONTENT_DIR", Path(self.test_dir)):

            # Create 5 dummy video files
            video_files = [
                ("files", (f"sample_clip_{i}.mp4", b"\x00\x00\x00\x18ftypmp42", "video/mp4"))
                for i in range(1, 6)
            ]

            data = {
                "account": self.test_account,
                "category": "Video",
                "date": self.test_date,
            }

            response = self.client.post(
                "/api/content/upload-media",
                data=data,
                files=video_files
            )

            self.assertEqual(response.status_code, 200)
            res_json = response.json()
            self.assertEqual(res_json["status"], "success")
            self.assertEqual(res_json["count"], 5)
            self.assertEqual(len(res_json["filenames"]), 5)
            self.assertEqual(len(res_json["item_keys"]), 5)

            # Check files created on disk
            target_dir = Path(self.test_dir) / self.test_account / "Video" / self.test_date
            self.assertTrue(target_dir.exists())

            for i in range(1, 6):
                expected_video = target_dir / f"video-{self.test_date}-{i:02d}.mp4"
                expected_meta = target_dir / f"video-{self.test_date}-{i:02d}.json"
                self.assertTrue(expected_video.exists(), f"File {expected_video} should exist")
                self.assertTrue(expected_meta.exists(), f"Metadata {expected_meta} should exist")

            # Verify ContentManager scans 5 items
            items = ContentManager.scan_content(self.test_account)
            video_items = [it for it in items if it["category"] == "Video" and it["date"] == self.test_date]
            self.assertEqual(len(video_items), 5)

            # Verify mock_caption was called for each of the 5 videos
            self.assertEqual(mock_caption.call_count, 5)

    @patch("src.server._trigger_background_auto_caption")
    def test_upload_single_video_still_works(self, mock_caption):
        with patch("src.server.CONTENT_DIR", Path(self.test_dir)), \
             patch("src.content_manager.CONTENT_DIR", Path(self.test_dir)):

            video_files = [
                ("files", ("single_clip.mp4", b"\x00\x00\x00\x18ftypmp42", "video/mp4"))
            ]

            data = {
                "account": self.test_account,
                "category": "Video",
                "date": self.test_date,
            }

            response = self.client.post(
                "/api/content/upload-media",
                data=data,
                files=video_files
            )

            self.assertEqual(response.status_code, 200)
            res_json = response.json()
            self.assertEqual(res_json["status"], "success")
            self.assertEqual(res_json["count"], 1)
            self.assertEqual(res_json["filename"], f"video-{self.test_date}-01.mp4")

            target_dir = Path(self.test_dir) / self.test_account / "Video" / self.test_date
            self.assertTrue((target_dir / f"video-{self.test_date}-01.mp4").exists())
            self.assertTrue((target_dir / f"video-{self.test_date}-01.json").exists())

    @patch("src.server._trigger_background_auto_caption")
    def test_upload_multiple_posters_creates_separate_posters(self, mock_caption):
        with patch("src.server.CONTENT_DIR", Path(self.test_dir)), \
             patch("src.content_manager.CONTENT_DIR", Path(self.test_dir)):

            poster_files = [
                ("files", (f"poster_img_{i}.jpg", b"\xff\xd8\xff\xe0\x00\x10JFIF", "image/jpeg"))
                for i in range(1, 4)
            ]

            data = {
                "account": self.test_account,
                "category": "Poster",
                "date": self.test_date,
            }

            response = self.client.post(
                "/api/content/upload-media",
                data=data,
                files=poster_files
            )

            self.assertEqual(response.status_code, 200)
            res_json = response.json()
            self.assertEqual(res_json["status"], "success")
            self.assertEqual(res_json["count"], 3)
            self.assertEqual(len(res_json["filenames"]), 3)

            target_dir = Path(self.test_dir) / self.test_account / "Poster" / self.test_date
            for i in range(1, 4):
                self.assertTrue((target_dir / f"poster-{self.test_date}-{i:02d}.jpg").exists())
                self.assertTrue((target_dir / f"poster-{self.test_date}-{i:02d}.json").exists())

if __name__ == "__main__":
    unittest.main()
