import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.facebook_uploader import FacebookUploader

class TestFacebookUploader(unittest.TestCase):
    def setUp(self):
        self.uploader = FacebookUploader(headless=True)

    @patch("src.facebook_uploader.get_account_state_file")
    def test_upload_missing_session_returns_false(self, mock_state_file):
        mock_file = MagicMock()
        mock_file.exists.return_value = False
        mock_state_file.return_value = mock_file
        success, msg, path = self.uploader.upload_media(
            media_paths=["content/test.mp4"],
            caption="test",
            is_reel=True,
            account_name="dummy_fb_acc"
        )
        self.assertFalse(success)
        self.assertIn("belum ada", msg.lower())

    def test_upload_empty_media_returns_false(self):
        success, msg, path = self.uploader.upload_media(
            media_paths=[],
            caption="test",
            is_reel=True,
            account_name="dummy_fb_acc"
        )
        self.assertFalse(success)
        self.assertIn("tidak ada file media", msg.lower())

    @patch("src.facebook_uploader.get_account_state_file")
    @patch("src.facebook_uploader.get_safe_storage_state")
    @patch("src.facebook_uploader.launch_browser")
    @patch("playwright.sync_api.sync_playwright")
    def test_upload_reel_success(self, mock_playwright, mock_launch, mock_safe_state, mock_state_file):
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_state_file.return_value = mock_file
        mock_safe_state.return_value = {}

        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        mock_page.url = "https://www.facebook.com/"

        # Mock expect_file_chooser
        mock_fc = MagicMock()
        mock_fc_info = MagicMock()
        mock_fc_info.value = mock_fc
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_fc_info
        mock_cm.__exit__.return_value = None
        mock_page.expect_file_chooser.return_value = mock_cm

        # Mock locators
        def mock_locator(sel):
            loc = MagicMock()
            if "password" in sel or "pass" in sel:
                loc.count.return_value = 0
                loc.is_visible.return_value = False
                return loc
            loc.count.return_value = 1
            loc.first = loc
            loc.last = loc
            loc.is_visible.return_value = True
            loc.all.return_value = []
            loc.inner_text.return_value = ""
            return loc

        mock_page.locator.side_effect = mock_locator

        # Mock sync_playwright context manager
        mock_pw_instance = MagicMock()
        mock_playwright.return_value.__enter__.return_value = mock_pw_instance

        # Call upload_media
        success, msg, path = self.uploader.upload_media(
            media_paths=["content/test.mp4"],
            caption="Test Caption #Reels",
            is_reel=True,
            account_name="dummy_fb_acc"
        )

        self.assertTrue(success)
        self.assertIn("berhasil", msg.lower())
        mock_page.expect_file_chooser.assert_called_once()
        mock_fc.set_files.assert_called_once()

    @patch("src.facebook_uploader.get_account_state_file")
    @patch("src.facebook_uploader.get_safe_storage_state")
    @patch("src.facebook_uploader.launch_browser")
    @patch("playwright.sync_api.sync_playwright")
    def test_upload_photo_success(self, mock_playwright, mock_launch, mock_safe_state, mock_state_file):
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_state_file.return_value = mock_file
        mock_safe_state.return_value = {}

        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        mock_page.url = "https://www.facebook.com/"

        # Mock expect_file_chooser
        mock_fc = MagicMock()
        mock_fc_info = MagicMock()
        mock_fc_info.value = mock_fc
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_fc_info
        mock_cm.__exit__.return_value = None
        mock_page.expect_file_chooser.return_value = mock_cm

        def mock_locator(sel):
            loc = MagicMock()
            if "password" in sel or "pass" in sel:
                loc.count.return_value = 0
                loc.is_visible.return_value = False
                return loc
            loc.count.return_value = 1
            loc.first = loc
            loc.last = loc
            loc.is_visible.return_value = True
            loc.all.return_value = []
            loc.inner_text.return_value = ""
            return loc

        mock_page.locator.side_effect = mock_locator

        mock_pw_instance = MagicMock()
        mock_playwright.return_value.__enter__.return_value = mock_pw_instance

        success, msg, path = self.uploader.upload_media(
            media_paths=["content/test.png"],
            caption="Test Photo Caption",
            is_reel=False,
            account_name="dummy_fb_acc"
        )

        self.assertTrue(success)
        self.assertIn("berhasil", msg.lower())
        mock_page.expect_file_chooser.assert_called_once()
        mock_fc.set_files.assert_called_once()

if __name__ == "__main__":
    unittest.main()
