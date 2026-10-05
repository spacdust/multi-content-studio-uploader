import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.instagram_uploader import InstagramUploader

class TestInstagramUploader(unittest.TestCase):
    def setUp(self):
        self.uploader = InstagramUploader(headless=True)

    @patch("src.instagram_uploader.get_account_state_file")
    def test_upload_missing_session_returns_false(self, mock_state_file):
        mock_file = MagicMock()
        mock_file.exists.return_value = False
        mock_state_file.return_value = mock_file
        success, msg, path = self.uploader.upload_media_playwright(
            media_paths=["content/test.mp4"],
            caption="test",
            is_reel=True,
            account_name="test_dummy_acc"
        )
        self.assertFalse(success)
        self.assertIn("belum ada", msg.lower())

    @patch("src.instagram_uploader.get_account_state_file")
    @patch("src.instagram_uploader.get_safe_storage_state")
    @patch("src.instagram_uploader.launch_browser")
    @patch("playwright.sync_api.sync_playwright")
    def test_upload_success_when_shared(self, mock_playwright, mock_launch, mock_safe_state, mock_state_file):
        # Setup mock state file exists
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_state_file.return_value = mock_file
        mock_safe_state.return_value = {}

        # Setup mock playwright browser & page
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        mock_page.url = "https://www.instagram.com/"

        # Mock locators
        def mock_locator(sel):
            loc = MagicMock()
            if "dialog" in sel and "button" in sel:
                loc.count.return_value = 1
                loc.last = loc
                loc.first = loc
                loc.is_visible.return_value = True
                loc.all.return_value = []
                loc.inner_text.return_value = "Your reel has been shared."
                return loc
            loc.count.return_value = 1
            loc.first = loc
            loc.last = loc
            loc.is_visible.return_value = True
            loc.all.return_value = []
            loc.inner_text.return_value = ""
            return loc

        mock_page.locator.side_effect = mock_locator
        mock_page.content.return_value = "Your reel has been shared."

        success, msg, path = self.uploader.upload_media_playwright(
            media_paths=["test.mp4"],
            caption="Test Caption",
            is_reel=True,
            account_name="test_acc"
        )

        self.assertTrue(success)
        self.assertIn("berhasil", msg.lower())

    @patch("src.instagram_uploader.get_account_state_file")
    @patch("src.instagram_uploader.get_safe_storage_state")
    @patch("src.instagram_uploader.launch_browser")
    @patch("playwright.sync_api.sync_playwright")
    def test_upload_timeout_sharing_returns_false(self, mock_playwright, mock_launch, mock_safe_state, mock_state_file):
        # Setup mock state file exists
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

        mock_page.url = "https://www.instagram.com/"

        # Mock locators: sharing dialog persists and never shows success
        def mock_locator(sel):
            loc = MagicMock()
            loc.count.return_value = 1
            loc.first = loc
            loc.last = loc
            loc.is_visible.return_value = True
            loc.all.return_value = []
            loc.inner_text.return_value = "Sharing"
            return loc

        mock_page.locator.side_effect = mock_locator
        # Instagram page content stays as "Sharing"
        mock_page.content.return_value = "<div>Sharing</div>"

        # Patch max_wait_seconds by patching time or running with is_reel=False and mock fast loop
        with patch("src.instagram_uploader.Console"):
            success, msg, path = self.uploader.upload_media_playwright(
                media_paths=["test.png"],
                caption="Test Photo",
                is_reel=False,
                account_name="test_acc"
            )

        # In previous buggy code, this would have returned True!
        # Now it MUST return False!
        self.assertFalse(success)
        self.assertIn("timeout", msg.lower())

    @patch("src.instagram_uploader.get_account_state_file")
    @patch("src.instagram_uploader.get_safe_storage_state")
    @patch("src.instagram_uploader.launch_browser")
    @patch("playwright.sync_api.sync_playwright")
    def test_upload_failure_message_returns_false(self, mock_playwright, mock_launch, mock_safe_state, mock_state_file):
        # Setup mock state file exists
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

        mock_page.url = "https://www.instagram.com/"

        # Mock locators: dialog returns failure text
        def mock_locator(sel):
            loc = MagicMock()
            loc.count.return_value = 1
            loc.first = loc
            loc.last = loc
            loc.is_visible.return_value = True
            loc.all.return_value = []
            loc.inner_text.return_value = "Your reel couldn't be shared. Please try again."
            return loc

        mock_page.locator.side_effect = mock_locator
        mock_page.content.return_value = "<div>Your reel couldn't be shared</div>"

        success, msg, path = self.uploader.upload_media_playwright(
            media_paths=["test.mp4"],
            caption="Test Video",
            is_reel=True,
            account_name="test_acc"
        )

        self.assertFalse(success)
        self.assertIn("gagal", msg.lower())

if __name__ == "__main__":
    unittest.main()
