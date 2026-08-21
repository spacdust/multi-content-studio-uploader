import os
import re
import json
from pathlib import Path
from typing import Union, Optional, Tuple, Dict, Any

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONTENT_DIR = BASE_DIR / "content"
AUTH_DIR = BASE_DIR / "auth"
ACCOUNTS_DIR = BASE_DIR / "accounts"
QUEUE_DIR = BASE_DIR / "queue"
POSTED_DIR = BASE_DIR / "posted"
FAILED_DIR = BASE_DIR / "failed"
LOGS_DIR = BASE_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"
SOUNDS_DIR = ASSETS_DIR / "sounds"
TEMP_DIR = BASE_DIR / "temp"

# Ensure core directories exist
for directory in [CONTENT_DIR, AUTH_DIR, ACCOUNTS_DIR, QUEUE_DIR, POSTED_DIR, FAILED_DIR, LOGS_DIR, SOUNDS_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

def slugify_account_name(name: str) -> str:
    """Convert human account name to filesystem-friendly slug."""
    slug = re.sub(r"[^\w\s-]", "", name.lower().strip())
    return re.sub(r"[-\s]+", "_", slug)

def get_account_dir(account_name: str = "default") -> Path:
    """Get the directory path for a specific account data/session."""
    slug = slugify_account_name(account_name)
    acc_dir = ACCOUNTS_DIR / slug
    acc_dir.mkdir(parents=True, exist_ok=True)
    return acc_dir

def get_account_content_dir(account_name: str) -> Path:
    """Get the root content directory for a specific account."""
    acc_content = CONTENT_DIR / account_name
    # Buat 3 subfolder kategori utama
    (acc_content / "Video").mkdir(parents=True, exist_ok=True)
    (acc_content / "Poster").mkdir(parents=True, exist_ok=True)
    (acc_content / "Carousel").mkdir(parents=True, exist_ok=True)
    return acc_content

def get_account_state_file(account_name: str, platform: str) -> Path:
    """Get the storageState JSON path for an account and platform."""
    acc_dir = get_account_dir(account_name)
    plat = platform.lower()
    if plat == "tiktok":
        return acc_dir / "tiktok_state.json"
    elif plat == "instagram":
        return acc_dir / "instagram_state.json"
    elif plat == "facebook":
        return acc_dir / "facebook_state.json"
    elif plat in ["meta", "meta_business"]:
        return acc_dir / "meta_state.json"
    raise ValueError(f"Unknown platform: {platform}")

# Platform URLs
TIKTOK_UPLOAD_URL = "https://www.tiktok.com/creator-center/upload"
TIKTOK_LOGIN_URL = "https://www.tiktok.com/login"
TIKTOK_ALT_UPLOAD_URL = "https://www.tiktok.com/upload"

INSTAGRAM_BASE_URL = "https://www.instagram.com/"
INSTAGRAM_LOGIN_URL = "https://www.instagram.com/accounts/login/"

META_BUSINESS_LOGIN_URL = "https://business.facebook.com/login/"
META_BUSINESS_HOME_URL = "https://business.facebook.com/latest/home"
META_BUSINESS_COMPOSER_URL = "https://business.facebook.com/latest/composer"

# Browser Configurations
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

VIEWPORT = {"width": 1440, "height": 900}

# Supported File Extensions
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".aac", ".m4a", ".ogg", ".flac"}
MAX_VIDEO_SIZE_MB = 500

# Audio Mixing Presets
AUDIO_PRESETS = {
    "voiceover": {
        "original_vol": 1.0,
        "music_vol": 0.15,
        "description": "Suara vokal/narasi jelas (100%), musik latar lembut (15%) - Edukasi/vlog"
    },
    "balanced": {
        "original_vol": 1.0,
        "music_vol": 0.25,
        "description": "Seimbang antara suara asli (100%) dan musik (25%) - Standar"
    },
    "music_beat": {
        "original_vol": 0.3,
        "music_vol": 1.0,
        "description": "Musik dominan (100%), suara asli pelan (30%) - Trend/cinematic"
    },
    "mute_original": {
        "original_vol": 0.0,
        "music_vol": 1.0,
        "description": "Mute total suara asli (0%), hanya memutar musik baru (100%)"
    },
    "boost_voice": {
        "original_vol": 1.5,
        "music_vol": 0.12,
        "description": "Menaikkan volume suara asli (150%) dan musik tipis (12%)"
    }
}

def launch_browser(p, headless: bool = False, slow_mo: int = 0, extra_args: list = None):
    """
    Launches browser:
    - If headless=False: Opens visible maximized native Chrome window.
    - If headless=True: Opens 100% invisible background headless Chromium (no window flash/flicker on Windows).
    """
    if headless:
        headless_args = [
            "--headless=new",
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            "--disable-renderer-backgrounding",
            "--mute-audio"
        ]
        if extra_args:
            headless_args.extend(extra_args)
        try:
            return p.chromium.launch(
                headless=True,
                slow_mo=0,
                args=headless_args
            )
        except Exception:
            return p.chromium.launch(
                channel="chrome",
                headless=True,
                slow_mo=0,
                args=headless_args
            )
    else:
        headed_args = [
            "--start-maximized",
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--no-default-browser-check"
        ]
        if extra_args:
            headed_args.extend(extra_args)
        try:
            return p.chromium.launch(
                channel="chrome",
                headless=False,
                slow_mo=slow_mo,
                args=headed_args
            )
        except Exception:
            return p.chromium.launch(
                headless=False,
                slow_mo=slow_mo,
                args=headed_args
            )

def get_safe_storage_state(state_file: Union[str, Path, None]) -> Optional[dict]:
    """
    Loads and sanitizes storage_state JSON so that Playwright never crashes
    due to invalid sameSite values ('no_restriction', 'unspecified', lowercase 'lax', etc.),
    and strips bloated/corrupting origins.
    Returns a safe dictionary ready to pass directly to new_context(storage_state=...).
    """
    if not state_file:
        return None
    p = Path(state_file)
    if not p.exists():
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None
        
        # Strip bloated localStorage origins
        data["origins"] = []
        
        # Sanitize sameSite for each cookie
        for c in data.get("cookies", []):
            val = c.get("sameSite")
            if not val or not isinstance(val, str):
                c["sameSite"] = "None"
            elif "strict" in val.lower():
                c["sameSite"] = "Strict"
            elif "lax" in val.lower():
                c["sameSite"] = "Lax"
            else:
                c["sameSite"] = "None"
        
        return data
    except Exception:
        return None
