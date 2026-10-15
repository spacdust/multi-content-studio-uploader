import unittest
import shutil
import json
from pathlib import Path
from fastapi.testclient import TestClient

from src.config import CONTENT_DIR, ACCOUNTS_DIR
from src.content_manager import ContentManager
from src.server import app

client = TestClient(app)

class TestResetUploadStatus(unittest.TestCase):
    def setUp(self):
        self.test_account = "test_reset_account"
        self.test_date = "2026-10-09"
        self.acc_dir = ACCOUNTS_DIR / self.test_account
        self.content_dir = CONTENT_DIR / self.test_account
        
        self.acc_dir.mkdir(parents=True, exist_ok=True)
        self.content_dir.mkdir(parents=True, exist_ok=True)
        (self.acc_dir / "account.json").write_text(json.dumps({
            "name": self.test_account,
            "created_at": "2026-10-09 10:00:00"
        }), encoding="utf-8")

    def tearDown(self):
        if self.acc_dir.exists():
            shutil.rmtree(self.acc_dir, ignore_errors=True)
        if self.content_dir.exists():
            shutil.rmtree(self.content_dir, ignore_errors=True)

    def test_delete_item_purges_history_and_reupload_is_pending(self):
        """Test deleting an uploaded item clears upload_history and re-uploading has status PENDING."""
        video_dir = self.content_dir / "Video" / self.test_date
        video_dir.mkdir(parents=True, exist_ok=True)
        video_file = video_dir / "video-2026-10-09-01.mp4"
        video_file.write_bytes(b"dummy video data")

        item_key = f"Video/{self.test_date}/{video_file.name}"
        ContentManager.mark_as_uploaded(self.test_account, item_key, "tiktok")
        ContentManager.mark_as_uploaded(self.test_account, item_key, "instagram")
        ContentManager.mark_as_uploaded(self.test_account, item_key, "facebook")

        # Verify status is UPLOADED before delete
        items = ContentManager.scan_content(self.test_account)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["status"], "UPLOADED")
        self.assertIn("tiktok", items[0]["uploaded_platforms"])

        # Delete item via ContentManager.delete_item
        deleted = ContentManager.delete_item(
            account_name=self.test_account,
            category="Video",
            date=self.test_date,
            item_name=video_file.name,
            item_key=item_key
        )
        self.assertTrue(deleted)
        self.assertFalse(video_file.exists())

        # Verify history is purged from upload_history.json
        history = ContentManager.load_history(self.test_account)
        self.assertNotIn(item_key, history)

        # Upload the same video again with the same name
        new_video = video_dir / "video-2026-10-09-01.mp4"
        new_video.write_bytes(b"re-uploaded video data")

        # Verify scan_content reports PENDING status with empty uploaded_platforms
        scanned_items = ContentManager.scan_content(self.test_account)
        self.assertEqual(len(scanned_items), 1)
        self.assertEqual(scanned_items[0]["status"], "PENDING")
        self.assertEqual(scanned_items[0]["uploaded_platforms"], [])
        self.assertEqual(scanned_items[0]["post_urls"], {})

    def test_auto_prune_orphaned_history_on_scan(self):
        """Test scan_content automatically prunes orphaned entries when files are deleted externally."""
        item_key = f"Video/{self.test_date}/ghost_video.mp4"
        ContentManager.mark_as_uploaded(self.test_account, item_key, "tiktok")

        history_before = ContentManager.load_history(self.test_account)
        self.assertIn(item_key, history_before)

        # File does not exist on disk, scan_content should auto-prune it
        ContentManager.scan_content(self.test_account)

        history_after = ContentManager.load_history(self.test_account)
        self.assertNotIn(item_key, history_after)

    def test_reset_item_status_method(self):
        """Test reset_item_status resets upload status without deleting the physical media file."""
        video_dir = self.content_dir / "Video" / self.test_date
        video_dir.mkdir(parents=True, exist_ok=True)
        video_file = video_dir / "video-2026-10-09-01.mp4"
        video_file.write_bytes(b"video data")

        item_key = f"Video/{self.test_date}/{video_file.name}"
        ContentManager.mark_as_uploaded(self.test_account, item_key, "tiktok")

        # Call reset_item_status
        success = ContentManager.reset_item_status(self.test_account, item_key)
        self.assertTrue(success)

        # Media file must still exist
        self.assertTrue(video_file.exists())

        # Status must now be PENDING
        scanned = ContentManager.scan_content(self.test_account)
        self.assertEqual(len(scanned), 1)
        self.assertEqual(scanned[0]["status"], "PENDING")
        self.assertEqual(scanned[0]["uploaded_platforms"], [])

    def test_api_reset_status_endpoint(self):
        """Test POST /api/content/reset-status endpoint."""
        video_dir = self.content_dir / "Video" / self.test_date
        video_dir.mkdir(parents=True, exist_ok=True)
        video_file = video_dir / "video-2026-10-09-01.mp4"
        video_file.write_bytes(b"video content")

        item_key = f"Video/{self.test_date}/{video_file.name}"
        ContentManager.mark_as_uploaded(self.test_account, item_key, "facebook")

        # Call API
        resp = client.post("/api/content/reset-status", json={
            "account": self.test_account,
            "item_key": item_key
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")

        # Check content
        scanned = ContentManager.scan_content(self.test_account)
        self.assertEqual(scanned[0]["status"], "PENDING")

    def test_api_upload_media_resets_stale_history(self):
        """Test POST /api/content/upload-media purges any stale history for the generated item name."""
        # Pre-seed history with an uploaded record for video-2026-10-09-01.mp4
        stale_key = f"Video/{self.test_date}/video-2026-10-09-01.mp4"
        ContentManager.mark_as_uploaded(self.test_account, stale_key, "tiktok")

        # Upload a file via API to the same date
        resp = client.post(
            "/api/content/upload-media",
            data={
                "account": self.test_account,
                "category": "Video",
                "date": self.test_date,
            },
            files=[
                ("files", ("raw_clip.mp4", b"video binary stream", "video/mp4"))
            ]
        )
        self.assertEqual(resp.status_code, 200)

        # Scanned items should have PENDING status, not inheriting the stale tiktok upload
        scanned = ContentManager.scan_content(self.test_account)
        self.assertEqual(len(scanned), 1)
        self.assertEqual(scanned[0]["status"], "PENDING")
        self.assertEqual(scanned[0]["uploaded_platforms"], [])

if __name__ == "__main__":
    unittest.main()
