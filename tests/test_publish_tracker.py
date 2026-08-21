import unittest
import time
from pathlib import Path
from src.publish_tracker import PublishTracker

class TestPublishTracker(unittest.TestCase):
    def setUp(self):
        self.session_id = f"test_session_{int(time.time() * 1000)}"

    def test_publish_tracker_lifecycle(self):
        # 1. Initialize session
        session = PublishTracker.init_session(
            session_id=self.session_id,
            account="test_account",
            item_key="test_item_key",
            item_name="Test Video 1",
            category="Video",
            platforms=["tiktok", "instagram", "facebook"],
            date_str="2026-08-20"
        )
        self.assertEqual(session["session_id"], self.session_id)
        self.assertIn(session["status"], ["in_progress", "running"])
        self.assertEqual(session["percent"], 0)
        self.assertIn("tiktok", session["platforms"])
        self.assertIn("instagram", session["platforms"])
        self.assertIn("facebook", session["platforms"])

        # 2. Update step for TikTok
        PublishTracker.update_step(
            session_id=self.session_id,
            platform="tiktok",
            step_name="Memilih sound favorit...",
            percent=50,
            log_msg="Memilih sound favorit via tombol '+'",
            log_type="step"
        )

        retrieved = PublishTracker.get_session(self.session_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["platforms"]["tiktok"]["percent"], 50)
        self.assertEqual(retrieved["current_step"], "Memilih sound favorit...")
        self.assertTrue(len(retrieved["logs"]) >= 1)

        # 3. Complete all platforms
        PublishTracker.update_step(
            session_id=self.session_id,
            platform="tiktok",
            step_name="TikTok Selesai",
            percent=100,
            is_completed=True,
            post_url="https://tiktok.com/proof1"
        )
        PublishTracker.update_step(
            session_id=self.session_id,
            platform="instagram",
            step_name="Instagram Selesai",
            percent=100,
            is_completed=True,
            post_url="https://instagram.com/proof2"
        )
        PublishTracker.update_step(
            session_id=self.session_id,
            platform="facebook",
            step_name="Facebook Selesai",
            percent=100,
            is_completed=True,
            post_url="https://facebook.com/proof3"
        )

        completed_session = PublishTracker.get_session(self.session_id)
        self.assertEqual(completed_session["status"], "completed")
        self.assertEqual(completed_session["percent"], 100)

if __name__ == "__main__":
    unittest.main()
