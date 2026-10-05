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

        # Item dijadwalkan 5 hari yang lalu (> 24 jam lampau)
        mock_scan.return_value = [
            {
                "item_key": "Video/2026-09-28/vid1.mp4",
                "name": "vid1.mp4",
                "category": "Video",
                "date": "2026-09-28",
                "uploaded_platforms": [],
                "meta": {
                    "scheduled_time": "2026-09-28T19:30:00",
                    "platforms": ["tiktok"]
                }
            }
        ]

        scheduled = AutoScheduler.get_scheduled_items()
        # Item lampau yang basi (> 24 jam) tidak dimasukkan ke antrean terjadwal
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

if __name__ == "__main__":
    unittest.main()
