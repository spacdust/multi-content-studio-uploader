import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.scheduler import AutoScheduler
from src.content_manager import ContentManager

class TestSchedulerAndRetry(unittest.TestCase):
    @patch("src.scheduler.AccountManager.list_accounts")
    @patch("src.scheduler.ContentManager.scan_content")
    @patch("src.scheduler.AuthManager.is_authenticated")
    def test_scheduled_items_keeps_partially_uploaded_items(self, mock_auth, mock_scan, mock_list_acc):
        mock_list_acc.return_value = [{"name": "TestAcc"}]
        mock_auth.return_value = True

        from datetime import datetime, timedelta
        now_str = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S")

        # Item memiliki target tiktok, instagram, facebook.
        # TikTok sudah diupload, tapi instagram & facebook belum.
        mock_scan.return_value = [
            {
                "item_key": "Video/2026-10-03/vid1.mp4",
                "name": "vid1.mp4",
                "category": "Video",
                "date": "2026-10-03",
                "uploaded_platforms": ["tiktok"],
                "meta": {
                    "scheduled_time": now_str,
                    "platforms": ["tiktok", "instagram", "facebook"]
                }
            }
        ]

        scheduled = AutoScheduler.get_scheduled_items()
        self.assertEqual(len(scheduled), 1)
        self.assertEqual(scheduled[0]["item_name"], "vid1.mp4")
        self.assertEqual(scheduled[0]["remaining_platforms"], ["instagram", "facebook"])

    @patch("src.scheduler.AccountManager.list_accounts")
    @patch("src.scheduler.ContentManager.scan_content")
    @patch("src.scheduler.AuthManager.is_authenticated")
    def test_scheduled_items_skips_fully_uploaded_items(self, mock_auth, mock_scan, mock_list_acc):
        mock_list_acc.return_value = [{"name": "TestAcc"}]
        mock_auth.return_value = True

        # Item sudah diupload ke semua target platform
        mock_scan.return_value = [
            {
                "item_key": "Video/2026-10-03/vid1.mp4",
                "name": "vid1.mp4",
                "category": "Video",
                "date": "2026-10-03",
                "uploaded_platforms": ["tiktok", "instagram", "facebook"],
                "meta": {
                    "scheduled_time": "2026-10-03T08:00:00",
                    "platforms": ["tiktok", "instagram", "facebook"]
                }
            }
        ]

        scheduled = AutoScheduler.get_scheduled_items()
        # Harus kosong karena semua platform target sudah terbit
        self.assertEqual(len(scheduled), 0)

    @patch("src.content_manager.get_account_content_dir")
    @patch("src.content_manager.get_account_dir")
    @patch("src.content_manager.console")
    @patch("src.content_manager.TikTokUploader")
    @patch("src.content_manager.InstagramUploader")
    @patch("src.content_manager.FacebookUploader")
    @patch("src.content_manager.AuthManager.is_authenticated")
    @patch("src.content_manager.time.sleep")
    def test_process_content_item_skips_already_uploaded_platforms(self, mock_sleep, mock_auth, mock_fb, mock_ig, mock_tt, mock_console, mock_acc_dir, mock_content_dir):
        mock_acc_dir.return_value = Path("C:/dummy_temp/acc")
        mock_content_dir.return_value = Path("C:/dummy_temp/content")
        mock_auth.return_value = True
        mock_ig_instance = MagicMock()
        mock_ig_instance.upload.return_value = (True, "OK", "proof_ig.png")
        mock_ig.return_value = mock_ig_instance

        mock_fb_instance = MagicMock()
        mock_fb_instance.upload.return_value = (True, "OK", "proof_fb.png")
        mock_fb.return_value = mock_fb_instance

        item = {
            "account": "MockAccount",
            "category": "Video",
            "name": "vid1.mp4",
            "item_key": "Video/2026-10-03/vid1.mp4",
            "date": "2026-10-03",
            "path": "content/MockAccount/Video/2026-10-03/vid1.mp4",
            "caption": "test caption",
            "uploaded_platforms": ["tiktok"],
            "meta": {
                "platforms": ["tiktok", "instagram", "facebook"]
            }
        }

        with patch.object(ContentManager, "mark_as_uploaded") as mock_mark:
            ok = ContentManager.process_content_item(item, platform_filter="all", headless=True)
            self.assertTrue(ok)
            # TikTok TIDAK boleh dipanggil karena sudah diupload sebelumnya!
            mock_tt.assert_not_called()
            # Instagram dan Facebook HARUS dipanggil
            mock_ig_instance.upload.assert_called_once()
            mock_fb_instance.upload.assert_called_once()

    @patch("src.content_manager.get_account_content_dir")
    @patch("src.content_manager.get_account_dir")
    @patch("src.content_manager.console")
    @patch("src.content_manager.InstagramUploader")
    @patch("src.content_manager.AuthManager.is_authenticated")
    @patch("src.content_manager.time.sleep")
    def test_process_content_item_retries_on_failure(self, mock_sleep, mock_auth, mock_ig, mock_console, mock_acc_dir, mock_content_dir):
        mock_acc_dir.return_value = Path("C:/dummy_temp/acc")
        mock_content_dir.return_value = Path("C:/dummy_temp/content")
        mock_auth.return_value = True
        mock_ig_instance = MagicMock()
        # Percobaan 1 gagal, percobaan 2 berhasil
        mock_ig_instance.upload.side_effect = [
            (False, "Something went wrong", None),
            (True, "OK", "proof_ig.png")
        ]
        mock_ig.return_value = mock_ig_instance

        item = {
            "account": "MockAccount",
            "category": "Video",
            "name": "vid1.mp4",
            "item_key": "Video/2026-10-03/vid1.mp4",
            "date": "2026-10-03",
            "path": "content/MockAccount/Video/2026-10-03/vid1.mp4",
            "caption": "test caption",
            "uploaded_platforms": [],
            "meta": {
                "platforms": ["instagram"]
            }
        }

        with patch.object(ContentManager, "mark_as_uploaded") as mock_mark:
            ok = ContentManager.process_content_item(item, platform_filter="instagram", headless=True)
            self.assertTrue(ok)
            # Harus dicoba 2 kali (karena percobaan 1 gagal dan percobaan 2 berhasil)
            self.assertEqual(mock_ig_instance.upload.call_count, 2)
            mock_mark.assert_called_once_with("MockAccount", "Video/2026-10-03/vid1.mp4", "instagram", "proof_ig.png")

    @patch("src.scheduler.AccountManager.list_accounts")
    @patch("src.scheduler.ContentManager.scan_content")
    @patch("src.scheduler.AuthManager.is_authenticated")
    def test_scheduler_stale_items_not_due(self, mock_auth, mock_scan, mock_list_acc):
        mock_list_acc.return_value = [{"name": "TestAcc"}]
        mock_auth.return_value = True

        from datetime import datetime, timedelta
        # 1. Item dijadwalkan kemarin (past date)
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        # 2. Item dijadwalkan hari ini tapi terlambat lebih dari 30 menit (2 jam lalu)
        late_today_str = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S")

        mock_scan.return_value = [
            {
                "item_key": "Video/2026-10-09/vid1.mp4",
                "name": "vid1.mp4",
                "category": "Video",
                "date": "2026-10-09",
                "uploaded_platforms": [],
                "meta": {
                    "scheduled_time": yesterday_str,
                    "platforms": ["tiktok"]
                }
            },
            {
                "item_key": "Video/2026-10-10/vid2.mp4",
                "name": "vid2.mp4",
                "category": "Video",
                "date": "2026-10-10",
                "uploaded_platforms": [],
                "meta": {
                    "scheduled_time": late_today_str,
                    "platforms": ["tiktok"]
                }
            }
        ]

        scheduled = AutoScheduler.get_scheduled_items()
        # Item kemarin maupun item yang terlambat > 30 menit tidak boleh masuk antrean aktif
        self.assertEqual(len(scheduled), 0)

    @patch("src.auth_manager.get_account_state_file")
    def test_auth_manager_cookie_expiration(self, mock_state_file):
        from src.auth_manager import AuthManager
        import json
        import tempfile
        import time

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as tmp:
            tmp_path = Path(tmp.name)
            # Cookie yang sudah kadaluarsa (expired timestamp di masa lalu)
            json.dump({
                "cookies": [
                    {"name": "sessionid", "value": "abcdef123456", "expires": time.time() - 3600}
                ]
            }, tmp)
            tmp.flush()

        mock_state_file.return_value = tmp_path
        try:
            is_valid = AuthManager.is_tiktok_authenticated("TestAcc")
            self.assertFalse(is_valid)
        finally:
            tmp_path.unlink(missing_ok=True)

    @patch("src.scheduler.AccountManager.list_accounts")
    @patch("src.scheduler.ContentManager.scan_content")
    @patch("src.scheduler.AuthManager.is_authenticated")
    def test_scheduler_get_status_rich_upcoming_queue(self, mock_auth, mock_scan, mock_list_acc):
        from datetime import datetime, timedelta
        mock_list_acc.return_value = [{"name": "TestAcc"}]
        mock_auth.return_value = True

        future_str = (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%S")
        mock_scan.return_value = [
            {
                "item_key": "Video/2026-10-15/vid1.mp4",
                "name": "vid1.mp4",
                "category": "Video",
                "date": "2026-10-15",
                "uploaded_platforms": [],
                "meta": {
                    "scheduled_time": future_str,
                    "platforms": ["tiktok", "instagram"],
                    "custom_caption": "Caption uji coba"
                }
            }
        ]

        status = AutoScheduler.get_status()
        self.assertEqual(status["total_scheduled_pending"], 1)
        self.assertEqual(len(status["upcoming_queue"]), 1)
        queue_item = status["upcoming_queue"][0]
        self.assertEqual(queue_item["item_name"], "vid1.mp4")
        self.assertEqual(queue_item["account"], "TestAcc")
        self.assertEqual(queue_item["date"], "2026-10-15")
        self.assertEqual(queue_item["remaining_platforms"], ["tiktok", "instagram"])
        self.assertEqual(queue_item["caption"], "Caption uji coba")
        self.assertIn("/api/content/media/TestAcc/Video/2026-10-15/vid1.mp4", queue_item["media_url"])

    @patch("src.server.ContentManager.scan_content")
    @patch("src.server._find_item_meta_json")
    def test_batch_clear_schedule_single_item(self, mock_find_meta, mock_scan):
        import json
        import tempfile
        from fastapi.testclient import TestClient
        from src.server import app

        client = TestClient(app)
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as tmp:
            tmp_path = Path(tmp.name)
            json.dump({"scheduled_time": "2026-10-15T15:00:00", "custom_caption": "test"}, tmp)
            tmp.flush()

        mock_find_meta.return_value = tmp_path
        try:
            res = client.post("/api/content/batch-clear-schedule", json={
                "account": "Shift & Co.",
                "items": [
                    {
                        "category": "Video",
                        "date": "2026-10-15",
                        "item_name": "video-01.mp4"
                    }
                ]
            })
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["cleared_count"], 1)

            with open(tmp_path, "r", encoding="utf-8") as f:
                cleared_data = json.load(f)
            self.assertIsNone(cleared_data.get("scheduled_time"))
        finally:
            tmp_path.unlink(missing_ok=True)

if __name__ == "__main__":
    unittest.main()

