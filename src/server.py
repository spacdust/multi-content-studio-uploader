import os
import sys
import re
import json
import time
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.config import (
    CONTENT_DIR,
    BASE_DIR,
    ACCOUNTS_DIR,
    LOGS_DIR,
    get_account_content_dir,
    get_account_dir
)
from src.account_manager import AccountManager
from src.auth_manager import AuthManager
from src.content_manager import ContentManager
from src.caption_generator import (
    CaptionGenerator,
    DEFAULT_LLM_BASE_URL,
    DEFAULT_LLM_API_KEY,
    DEFAULT_LLM_MODEL
)
from src.tiktok_uploader import TikTokUploader
from src.instagram_uploader import InstagramUploader
from src.publish_tracker import PublishTracker

app = FastAPI(
    title="Content Uploader Studio API",
    version="1.0.0",
    description="Backend API for Multi-Account Social Media Content Pipeline"
)

# CORS middleware for dev mode
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas
class InitDateRequest(BaseModel):
    account: str
    date: str

class GenerateCaptionRequest(BaseModel):
    account: Optional[str] = "default"
    category: Optional[str] = "Video"
    item_name: Optional[str] = ""
    topic: Optional[str] = ""
    item_path: Optional[str] = None
    extra_context: Optional[str] = None

class SaveCaptionRequest(BaseModel):
    account: str
    category: str
    date: str
    item_name: str
    caption: str
    as_draft: Optional[bool] = False
    sound_mode: Optional[str] = "favorite"
    sound_query: Optional[str] = ""
    sound_db: Optional[str] = "-7"
    scheduled_time: Optional[str] = None

class UploadItemRequest(BaseModel):
    account: str
    item_key: str
    platform: str = "all"
    headless: bool = False
    session_id: Optional[str] = None

class DeleteItemRequest(BaseModel):
    account: str
    category: str
    date: str
    item_name: str
    item_key: Optional[str] = None

class SettingsRequest(BaseModel):
    llm_base_url: str
    llm_api_key: str
    llm_model: str

class AccountLoginRequest(BaseModel):
    account: str
    platform: str # "tiktok" | "instagram"
    timeout_seconds: int = 600

class InstagramMobileLoginRequest(BaseModel):
    account: str
    username: str
    password: str
    verification_code: Optional[str] = None

class OpenStudioRequest(BaseModel):
    account: str
    platform: Optional[str] = "tiktok"

class CreateAccountRequest(BaseModel):
    name: str
    description: Optional[str] = ""

class ImportTikTokSessionRequest(BaseModel):
    account: str
    session_data: str

class UpdateLinksRequest(BaseModel):
    account: str
    item_key: str
    post_urls: Dict[str, str]

class FetchLinksRequest(BaseModel):
    account: str
    item_key: str
    caption: Optional[str] = ""
    category: Optional[str] = ""
    platforms: Optional[List[str]] = None
    force_refresh: Optional[bool] = False

# Helper to read and write .env
def read_current_env() -> Dict[str, str]:
    env_data = {
        "LLM_BASE_URL": DEFAULT_LLM_BASE_URL,
        "LLM_API_KEY": DEFAULT_LLM_API_KEY,
        "LLM_MODEL": DEFAULT_LLM_MODEL
    }
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        env_data[k.strip()] = v.strip().strip('"').strip("'")
        except Exception:
            pass
    return env_data

def save_env_data(data: Dict[str, str]):
    env_file = BASE_DIR / ".env"
    lines = [
        "# ====================================================================",
        "# KONFIGURASI LLM CAPTION GENERATOR",
        "# ====================================================================",
        f"LLM_BASE_URL={data.get('LLM_BASE_URL', DEFAULT_LLM_BASE_URL)}",
        f"LLM_API_KEY={data.get('LLM_API_KEY', DEFAULT_LLM_API_KEY)}",
        f"LLM_MODEL={data.get('LLM_MODEL', DEFAULT_LLM_MODEL)}",
        ""
    ]
    with open(env_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    for k, v in data.items():
        os.environ[k] = v

# API Routes

@app.get("/api/accounts")
def get_accounts():
    """List all registered accounts with session verification and TikTok avatar profile data."""
    accounts = AccountManager.list_accounts()
    result = []
    for acc in accounts:
        acc_name = acc["name"]
        slug = acc["slug"]
        tt_ok = AuthManager.is_tiktok_authenticated(acc_name)
        ig_ok = AuthManager.is_instagram_authenticated(acc_name) or AuthManager.is_instagram_mobile_authenticated(acc_name)
        fb_ok = AuthManager.is_facebook_authenticated(acc_name)

        tt_msg = f"Session TikTok akun '{acc_name}' AKTIF dan siap upload!" if tt_ok else f"Session state belum ada untuk akun '{acc_name}'. Silakan login terlebih dahulu."
        ig_msg = f"Session Instagram akun '{acc_name}' AKTIF dan siap upload!" if ig_ok else f"Session Instagram akun '{acc_name}' belum login / belum ada."
        fb_msg = f"Session Facebook Fanspage akun '{acc_name}' AKTIF!" if fb_ok else f"Session Facebook Fanspage akun '{acc_name}' belum login / belum ada."
        
        # Load TikTok profile (avatar, handle, nickname, followers)
        tt_profile = {}
        if tt_ok:
            try:
                tt_profile = AccountManager.get_tiktok_profile(acc_name)
            except Exception:
                pass

        result.append({
            "name": acc_name,
            "slug": slug,
            "description": acc.get("description", ""),
            "tiktok_active": tt_ok,
            "tiktok_message": tt_msg,
            "tiktok_profile": tt_profile,
            "avatar_url": f"/api/accounts/avatar/{slug}?platform=tiktok" if tt_profile.get("has_local_avatar") or tt_profile.get("avatar_url") else None,
            "instagram_active": ig_ok,
            "instagram_message": ig_msg,
            "facebook_active": fb_ok,
            "facebook_message": fb_msg
        })
    return {"accounts": result}

@app.get("/api/accounts/avatar/{account_slug}")
def get_account_avatar(account_slug: str, platform: str = "tiktok"):
    """Serves locally cached avatar image for an account."""
    acc_dir = ACCOUNTS_DIR / account_slug
    avatar_file = acc_dir / f"{platform}_avatar.jpg"
    if avatar_file.exists():
        return FileResponse(avatar_file, media_type="image/jpeg")
    
    profile_file = acc_dir / f"{platform}_profile.json"
    if profile_file.exists():
        try:
            with open(profile_file, "r", encoding="utf-8") as f:
                p_data = json.load(f)
                remote_url = p_data.get("avatar_url")
                if remote_url:
                    import requests
                    headers = {"User-Agent": "Mozilla/5.0"}
                    r = requests.get(remote_url, headers=headers, timeout=5)
                    if r.status_code == 200:
                        with open(avatar_file, "wb") as af:
                            af.write(r.content)
                        return FileResponse(avatar_file, media_type="image/jpeg")
        except Exception:
            pass

    raise HTTPException(status_code=404, detail="Avatar not found")

@app.post("/api/accounts/create")
@app.post("/api/accounts")
def create_account(req: CreateAccountRequest):
    """Create a new account."""
    clean_name = req.name.strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Nama akun tidak boleh kosong")
    data = AccountManager.create_or_get_account(clean_name, description=req.description or "")
    get_account_content_dir(clean_name)
    return {"status": "success", "account": data, "message": f"Akun '{clean_name}' berhasil didaftarkan!"}

@app.post("/api/accounts/login")
def login_account_platform(req: AccountLoginRequest):
    """Spawns an independent native visual headed browser process for logging into TikTok or Instagram."""
    acc_name = req.account
    platform = req.platform.lower()

    if platform not in ["tiktok", "instagram", "facebook"]:
        raise HTTPException(status_code=400, detail="Platform harus 'tiktok', 'instagram', atau 'facebook'")

    cmd = [
        sys.executable,
        "-m", "src.cli",
        "login",
        "--account", acc_name,
        "--platform", platform,
        "--timeout", str(req.timeout_seconds)
    ]

    subprocess.Popen(
        cmd,
        cwd=str(BASE_DIR),
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )

    return {
        "status": "started",
        "message": f"Jendela browser visual {platform.upper()} sedang dibuka di layar Anda. Silakan login pada browser tersebut."
    }

@app.post("/api/accounts/login-instagram-mobile")
def login_instagram_mobile_endpoint(req: InstagramMobileLoginRequest):
    """Direct Instagram Mobile Login with username & password."""
    acc_name = req.account
    ok, msg = AuthManager.login_instagram_mobile(
        account_name=acc_name,
        username=req.username,
        password=req.password,
        verification_code=req.verification_code
    )
    if ok:
        return {"status": "success", "message": msg}
    elif "2fa" in msg.lower() or "twofactor" in msg.lower() or "kode" in msg.lower():
        return {"status": "2fa_required", "message": msg}
    else:
        return {"status": "error", "message": msg}

@app.post("/api/accounts/import-tiktok-session")
def import_tiktok_session_endpoint(req: ImportTikTokSessionRequest):
    """Imports sessionid or full cookie string directly for TikTok authentication."""
    ok, msg = AuthManager.import_tiktok_sessionid(req.account, req.session_data)
    if ok:
        return {"status": "success", "message": msg}
    else:
        raise HTTPException(status_code=400, detail=msg)

@app.post("/api/accounts/refresh-tiktok-session")
def refresh_tiktok_session_endpoint(req: OpenStudioRequest):
    """Validates and refreshes live TikTok cookies in background."""
    ok, msg = AuthManager.refresh_tiktok_session(req.account)
    if ok:
        return {"status": "success", "message": msg}
    else:
        raise HTTPException(status_code=400, detail=msg)

@app.post("/api/accounts/open-tiktok-studio")
def open_tiktok_studio(req: OpenStudioRequest):
    """Spawns an interactive maximized headed browser directly to TikTok Studio loaded with the specific account's session."""
    acc_name = req.account
    platform = "tiktok"

    cmd = [
        sys.executable,
        "-m", "src.cli",
        "open-studio",
        "--account", acc_name,
        "--platform", platform
    ]

    subprocess.Popen(
        cmd,
        cwd=str(BASE_DIR),
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    )

    return {
        "status": "started",
        "message": f"Membuka TikTok Studio dengan sesi akun '{acc_name}' di jendela browser maximized..."
    }

@app.post("/api/accounts/open-instagram")
def open_instagram_studio(req: OpenStudioRequest):
    """Spawns an interactive maximized headed browser directly to Instagram loaded with the specific account's session."""
    acc_name = req.account
    platform = "instagram"

    cmd = [
        sys.executable,
        "-m", "src.cli",
        "open-studio",
        "--account", acc_name,
        "--platform", platform
    ]

    subprocess.Popen(
        cmd,
        cwd=str(BASE_DIR),
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    )

    return {
        "status": "started",
        "message": f"Membuka Instagram dengan sesi akun '{acc_name}' di jendela browser maximized..."
    }

@app.post("/api/accounts/open-facebook")
def open_facebook_studio(req: OpenStudioRequest):
    """Spawns an interactive maximized headed browser directly to Facebook loaded with the specific account's session."""
    acc_name = req.account
    platform = "facebook"

    cmd = [
        sys.executable,
        "-m", "src.cli",
        "open-studio",
        "--account", acc_name,
        "--platform", platform
    ]

    subprocess.Popen(
        cmd,
        cwd=str(BASE_DIR),
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    )

    return {
        "status": "started",
        "message": f"Membuka Facebook Fanspage dengan sesi akun '{acc_name}' di jendela browser maximized..."
    }

@app.get("/api/settings")
def get_settings():
    """Returns current LLM endpoint, API key, and model configurations."""
    env = read_current_env()
    return {
        "llm_base_url": env.get("LLM_BASE_URL", DEFAULT_LLM_BASE_URL),
        "llm_api_key": env.get("LLM_API_KEY", DEFAULT_LLM_API_KEY),
        "llm_model": env.get("LLM_MODEL", DEFAULT_LLM_MODEL)
    }

@app.post("/api/settings")
def save_settings(req: SettingsRequest):
    """Updates and saves LLM settings persistently to .env file."""
    data = {
        "LLM_BASE_URL": req.llm_base_url.strip(),
        "LLM_API_KEY": req.llm_api_key.strip(),
        "LLM_MODEL": req.llm_model.strip()
    }
    save_env_data(data)
    return {"status": "success", "message": "Pengaturan LLM berhasil disimpan!"}

@app.post("/api/settings/test")
def test_llm_settings(req: SettingsRequest):
    """Tests connection to the specified LLM endpoint."""
    t0 = time.time()
    try:
        from openai import OpenAI
        client = OpenAI(base_url=req.llm_base_url.strip(), api_key=req.llm_api_key.strip())
        res = client.chat.completions.create(
            model=req.llm_model.strip(),
            messages=[{"role": "user", "content": "Halo, ini tes koneksi singkat. Balas dengan 1 kata: OK"}],
            max_tokens=10,
            timeout=10
        )
        latency = round((time.time() - t0) * 1000)
        reply = res.choices[0].message.content.strip()
        return {
            "status": "success",
            "message": f"Koneksi berhasil! Latensi: {latency}ms. Respon: '{reply}'"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Koneksi gagal: {str(e)}"
        }

@app.get("/api/content")
def get_content(account: Optional[str] = None):
    """Scans and returns all content items per account, date, and category."""
    items = ContentManager.scan_content(account_name=account)
    serialized = []
    for item in items:
        slide_urls = []
        if item["category"] == "Carousel" and "slides" in item and item["slides"]:
            folder_name = Path(item["path"]).name
            for s in item["slides"]:
                slide_urls.append(f"/api/content/media/{item['account']}/{item['category']}/{item['date']}/{folder_name}/{s.name}")

        first_media_url = slide_urls[0] if slide_urls else f"/api/content/media/{item['account']}/{item['category']}/{item['date']}/{item['name']}"

        serialized.append({
            "account": item["account"],
            "category": item["category"],
            "date": item["date"],
            "name": item["name"],
            "item_key": item["item_key"],
            "path": str(item["path"]),
            "caption": item["caption"],
            "meta": item["meta"],
            "uploaded_platforms": item["uploaded_platforms"],
            "uploaded_timestamps": item.get("uploaded_timestamps", {}),
            "post_urls": item.get("post_urls", {}),
            "status": item["status"],
            "created_at": item.get("created_at", 0.0),
            "mtime": item.get("mtime", 0.0),
            "media_url": first_media_url,
            "slide_urls": slide_urls,
            "slides": [s.name for s in item["slides"]] if "slides" in item and item["slides"] else []
        })
    return {"items": serialized}

@app.post("/api/content/update-links")
def update_post_links(req: UpdateLinksRequest):
    """Updates post URLs (TikTok, Instagram, Facebook) for an uploaded content item."""
    success = ContentManager.update_post_urls(req.account, req.item_key, req.post_urls)
    return {"status": "success" if success else "error", "item_key": req.item_key, "post_urls": req.post_urls}

@app.post("/api/content/fetch-links")
@app.post("/api/content/find-links")
def auto_fetch_post_links(req: FetchLinksRequest):
    """
    Automatically extracts exact post URLs (TikTok, Instagram, Facebook) using
    account scoping and caption fingerprint matching.
    """
    from src.link_finder import LinkFinder
    
    caption = req.caption
    if not caption:
        try:
            items = ContentManager.scan_content(req.account)
            target = next((it for it in items if it.get("item_key") == req.item_key or Path(it.get("item_key", "")).name == Path(req.item_key).name), None)
            if target:
                caption = target.get("caption", "") or target.get("name", "")
        except Exception:
            pass

    results = LinkFinder.find_all_links(
        account_name=req.account,
        item_key=req.item_key,
        caption=caption or "",
        category=req.category or "",
        platforms=req.platforms,
        force_refresh=req.force_refresh or False
    )
    return {"status": "success", "item_key": req.item_key, "data": results, "post_urls": results.get("urls", {})}

@app.post("/api/content/init-date")
def init_date_folder(req: InitDateRequest):
    """Creates category folders for a specific date in an account."""
    acc_dir = get_account_content_dir(req.account)
    date_str = req.date
    (acc_dir / "Video" / date_str).mkdir(parents=True, exist_ok=True)
    (acc_dir / "Poster" / date_str).mkdir(parents=True, exist_ok=True)
    (acc_dir / "Carousel" / date_str / "Carousel 1").mkdir(parents=True, exist_ok=True)
    return {"status": "success", "message": f"Folder date {date_str} created for {req.account}"}

@app.post("/api/content/caption/generate")
@app.post("/api/caption/generate")
def generate_caption(req: GenerateCaptionRequest):
    """Generates AI caption using Multimodal Gemini Vision (No emojis, max 4 tags)."""
    name_to_use = req.item_name or req.topic or ""
    media_p = Path(req.item_path) if req.item_path else None

    # Auto-resolve media path if missing
    if not media_p and req.account and name_to_use:
        candidate_cat_dir = CONTENT_DIR / req.account / (req.category or "Video")
        if candidate_cat_dir.exists():
            for d in candidate_cat_dir.iterdir():
                if d.is_dir():
                    candidate_file = d / name_to_use
                    if candidate_file.exists():
                        media_p = candidate_file
                        break
                    # For Carousel
                    c_clean = name_to_use.split(" (")[0]
                    c_folder = d / c_clean
                    if c_folder.is_dir():
                        media_p = c_folder
                        break

    caption = CaptionGenerator.generate_caption(
        item_name=name_to_use,
        category=req.category or "Video",
        account_name=req.account or "default",
        media_path=media_p,
        extra_context=req.extra_context
    )
    return {"status": "success", "caption": caption}

@app.post("/api/content/caption/save")
@app.post("/api/caption/save")
def save_caption(req: SaveCaptionRequest):
    """Saves custom caption, scheduled time & metadata to file."""
    acc_content = CONTENT_DIR / req.account / req.category / req.date
    
    if req.category in ["Video", "Poster"]:
        target_txt = acc_content / f"{Path(req.item_name).stem}.txt"
        target_json = acc_content / f"{Path(req.item_name).stem}.json"
    else: # Carousel
        clean_name = re.sub(r'\s*\(\d+\s+Slides\)$', '', req.item_name).strip()
        carousel_folder = acc_content / clean_name
        if not carousel_folder.exists() and acc_content.exists():
            for sub in acc_content.iterdir():
                if sub.is_dir() and (sub.name == clean_name or sub.name in req.item_name or clean_name in sub.name):
                    carousel_folder = sub
                    break
        carousel_folder.mkdir(parents=True, exist_ok=True)
        target_txt = carousel_folder / "caption.txt"
        target_json = carousel_folder / "meta.json"

    with open(target_txt, "w", encoding="utf-8") as f:
        f.write(req.caption)

    # Read existing meta to preserve other fields
    meta_data = {}
    if target_json.exists():
        try:
            with open(target_json, "r", encoding="utf-8") as f:
                meta_data = json.load(f)
        except Exception:
            pass

    default_db = "-7" if req.category == "Video" else "0"
    meta_data.update({
        "caption": req.caption,
        "sound_mode": req.sound_mode or "favorite",
        "sound_query": req.sound_query if req.sound_query is not None else "",
        "sound_db": req.sound_db if (req.sound_db is not None and req.sound_db != "") else default_db,
        "scheduled_time": req.scheduled_time,
        "platforms": ["tiktok", "instagram", "facebook"],
        "as_draft": False
    })

    with open(target_json, "w", encoding="utf-8") as f:
        json.dump(meta_data, f, indent=2)

    return {"status": "success", "message": "Caption and metadata saved"}

@app.post("/api/content/delete")
def delete_content_item(req: DeleteItemRequest):
    """Safely deletes a content item and its metadata from the filesystem queue."""
    success = ContentManager.delete_item(
        account_name=req.account,
        category=req.category,
        date=req.date,
        item_name=req.item_name,
        item_key=req.item_key
    )
    if not success:
        raise HTTPException(status_code=404, detail="File atau antrean tidak ditemukan.")
    return {"status": "success", "message": f"Konten '{req.item_name}' berhasil dihapus dari antrean!"}

@app.post("/api/content/upload-media")
async def upload_content_media(
    account: str = Form(...),
    category: str = Form(...),
    date: str = Form(...),
    carousel_name: Optional[str] = Form(None),
    scheduled_time: Optional[str] = Form(None),
    files: List[UploadFile] = File(...)
):
    """Uploads single video/poster or ordered multi-image carousel with optional scheduling."""
    target_dir = CONTENT_DIR / account / category / date

    if category == "Carousel":
        c_name = carousel_name.strip() if (carousel_name and carousel_name.strip() and not carousel_name.lower().startswith("carousel ") and not carousel_name.lower().startswith("carousel-")) else ContentManager.get_next_item_name(account, "Carousel", date)
        target_folder = target_dir / c_name
        target_folder.mkdir(parents=True, exist_ok=True)

        saved_files = []
        for idx, file in enumerate(files, 1):
            ext = Path(file.filename).suffix.lower() or ".jpg"
            slide_filename = f"Slide {idx}{ext}"
            slide_path = target_folder / slide_filename
            with open(slide_path, "wb") as f:
                content = await file.read()
                f.write(content)
            saved_files.append(slide_filename)

        # Write initial meta.json with blank caption and remove any lingering .txt file
        meta_data = {
            "caption": "",
            "scheduled_time": scheduled_time if scheduled_time else None,
            "sound_mode": "favorite",
            "sound_query": "",
            "sound_db": "0",
            "platforms": ["instagram", "tiktok", "facebook"],
            "as_draft": False
        }
        with open(target_folder / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta_data, f, indent=2)

        txt_file = target_folder / "caption.txt"
        if txt_file.exists():
            try:
                txt_file.unlink()
            except Exception:
                pass

        return {
            "status": "success",
            "message": f"Carousel '{c_name}' dengan {len(saved_files)} slide berhasil disimpan!",
            "slides": saved_files,
            "folder_name": c_name
        }

    else: # Video or Poster (Single Upload)
        if not files:
            raise HTTPException(status_code=400, detail="Tidak ada file yang diunggah")

        file = files[0]
        ext = Path(file.filename).suffix.lower() or (".mp4" if category == "Video" else ".jpg")
        saved_filename = ContentManager.get_next_item_name(account, category, date, ext=ext)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / saved_filename

        with open(target_path, "wb") as f:
            content = await file.read()
            f.write(content)

        default_db = "-7" if category == "Video" else "0"
        meta_path = target_dir / f"{target_path.stem}.json"
        meta_data = {
            "caption": "",
            "scheduled_time": scheduled_time if scheduled_time else None,
            "sound_mode": "favorite",
            "sound_query": "",
            "sound_db": default_db,
            "platforms": ["tiktok", "instagram", "facebook"],
            "as_draft": False
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, indent=2)

        # Remove any lingering old .txt caption file for this item name
        txt_path = target_dir / f"{target_path.stem}.txt"
        if txt_path.exists():
            try:
                txt_path.unlink()
            except Exception:
                pass

        return {
            "status": "success",
            "filename": saved_filename,
            "path": str(target_path)
        }

# Backwards compatible alias
@app.post("/api/content/upload-file")
async def upload_content_file(
    account: str = Form(...),
    category: str = Form(...),
    date: str = Form(...),
    carousel_name: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    return await upload_content_media(
        account=account,
        category=category,
        date=date,
        carousel_name=carousel_name,
        scheduled_time=None,
        files=[file]
    )

@app.get("/api/content/media/{account}/{category}/{date}/{filename:path}")
def serve_media_file(account: str, category: str, date: str, filename: str):
    """Serves media file with byte-range streaming support for in-browser video playback."""
    file_path = CONTENT_DIR / account / category / date / filename
    if not file_path.exists():
        clean_name = re.sub(r'\s*\(\d+\s+Slides\)$', '', filename).strip()
        c_folder = CONTENT_DIR / account / category / date / clean_name
        
        date_dir = CONTENT_DIR / account / category / date
        if not c_folder.exists() and date_dir.exists():
            for sub in date_dir.iterdir():
                if sub.is_dir() and (sub.name == clean_name or sub.name in filename or clean_name in sub.name):
                    c_folder = sub
                    break

        if c_folder.exists() and c_folder.is_dir():
            for p in sorted(c_folder.iterdir()):
                if p.is_file() and p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                    file_path = p
                    break

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Media not found")

    suffix = file_path.suffix.lower()
    media_type = "video/mp4" if suffix in [".mp4", ".mov", ".mkv", ".webm"] else "image/jpeg"
    return FileResponse(file_path, media_type=media_type)

@app.post("/api/content/upload")
def upload_item(req: UploadItemRequest):
    """Executes upload in an independent native process with real-time session tracking."""
    all_items = ContentManager.scan_content(account_name=req.account)
    target_item = next((i for i in all_items if i["item_key"] == req.item_key), None)
    
    if not target_item:
        raise HTTPException(status_code=404, detail=f"Content item '{req.item_key}' not found")

    session_id = req.session_id or f"pub_{int(time.time() * 1000)}"

    # Determine target platforms
    if req.platform == "all":
        target_platforms = []
        if AuthManager.is_authenticated(req.account, "tiktok"):
            target_platforms.append("tiktok")
        if AuthManager.is_authenticated(req.account, "instagram") or AuthManager.is_instagram_mobile_authenticated(req.account):
            target_platforms.append("instagram")
        if AuthManager.is_authenticated(req.account, "facebook"):
            target_platforms.append("facebook")
        if not target_platforms:
            target_platforms = ["tiktok"]
    else:
        target_platforms = [p.strip().lower() for p in req.platform.split(",")]

    # Initialize live publishing session
    PublishTracker.init_session(
        session_id=session_id,
        account=req.account,
        item_key=target_item["item_key"],
        item_name=target_item["name"],
        category=target_item["category"],
        platforms=target_platforms,
        date_str=target_item.get("date", "")
    )

    cmd = [
        sys.executable,
        "-m", "src.cli",
        "content", "process",
        "--account", req.account,
        "--category", target_item["category"],
        "--date", target_item["date"],
        "--item", target_item["name"],
        "--platform", req.platform,
        "--session-id", session_id
    ]
    if req.headless:
        cmd.append("--headless")

    flags = subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0

    subprocess.Popen(
        cmd,
        cwd=str(BASE_DIR),
        creationflags=flags
    )

    return {
        "status": "started",
        "session_id": session_id,
        "message": f"Proses upload {target_item['name']} sedang berjalan di browser visual!",
        "target_platforms": target_platforms
    }

@app.get("/api/content/upload/progress")
def get_upload_progress(session_id: str = Query(...)):
    """Returns current publishing session progress, platform states, and logs."""
    session = PublishTracker.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Sesi publish '{session_id}' tidak ditemukan")
    return session

@app.get("/api/content/upload/stream")
async def stream_upload_progress(session_id: str = Query(...)):
    """SSE real-time event stream for publishing progress and granular logs."""
    async def event_generator():
        last_str = ""
        poll_count = 0
        while poll_count < 600: # Max 10 minutes stream
            session = PublishTracker.get_session(session_id)
            if session:
                current_str = json.dumps(session, ensure_ascii=False)
                if current_str != last_str:
                    yield f"data: {current_str}\n\n"
                    last_str = current_str

                if session.get("status") in ["completed", "failed"]:
                    yield f"data: {current_str}\n\n"
                    break
            else:
                yield f"data: {json.dumps({'session_id': session_id, 'status': 'pending', 'percent': 0, 'current_step': 'Menyiapkan sesi...'})}\n\n"

            poll_count += 1
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Serve React static build if exists
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_react_app(full_path: str):
        file_p = FRONTEND_DIST / full_path
        if file_p.exists() and file_p.is_file():
            return FileResponse(file_p)
        return FileResponse(FRONTEND_DIST / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.server:app", host="127.0.0.1", port=8000, reload=True)
