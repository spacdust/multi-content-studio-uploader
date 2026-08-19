import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from src.config import SUPPORTED_VIDEO_EXTENSIONS, MAX_VIDEO_SIZE_MB

class ContentValidator:
    """Validates video files and metadata before uploading."""

    @staticmethod
    def validate_video_file(video_path: str | Path) -> Tuple[bool, Optional[str]]:
        """Validate if the video file exists, has a valid extension and size."""
        path = Path(video_path)
        if not path.exists():
            return False, f"File video tidak ditemukan: {path}"
        
        if not path.is_file():
            return False, f"Path bukan berupa file: {path}"
            
        ext = path.suffix.lower()
        if ext not in SUPPORTED_VIDEO_EXTENSIONS:
            return False, f"Format video '{ext}' tidak didukung. Gunakan salah satu dari: {', '.join(SUPPORTED_VIDEO_EXTENSIONS)}"
            
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > MAX_VIDEO_SIZE_MB:
            return False, f"Ukuran file ({size_mb:.2f} MB) melebihi batas maksimum {MAX_VIDEO_SIZE_MB} MB."
            
        if size_mb == 0:
            return False, "File video kosong (0 bytes)."
            
        return True, None

    @staticmethod
    def sanitize_caption(caption: str, platform: str = "general") -> str:
        """Format and trim caption according to platform character limits."""
        cleaned = caption.strip() if caption else ""
        
        # TikTok limit is ~2200 chars (newer accounts up to 4000)
        # Instagram limit is ~2200 chars
        if platform == "tiktok" and len(cleaned) > 2200:
            cleaned = cleaned[:2197] + "..."
        elif platform == "instagram" and len(cleaned) > 2200:
            cleaned = cleaned[:2197] + "..."
            
        return cleaned

    @staticmethod
    def extract_hashtags(caption: str) -> list[str]:
        """Extract hashtags list from caption string."""
        if not caption:
            return []
        words = caption.split()
        return [w for w in words if w.startswith("#") and len(w) > 1]
