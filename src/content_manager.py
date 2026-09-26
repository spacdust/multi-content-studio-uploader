import os
import json
import time
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.config import (
    CONTENT_DIR,
    get_account_content_dir,
    get_account_dir,
    SUPPORTED_VIDEO_EXTENSIONS,
    SUPPORTED_IMAGE_EXTENSIONS,
    LOGS_DIR
)
from src.caption_generator import CaptionGenerator
from src.tiktok_uploader import TikTokUploader
from src.instagram_uploader import InstagramUploader
from src.account_manager import AccountManager
from src.auth_manager import AuthManager

console = Console(highlight=False, legacy_windows=False)

class ContentManager:
    """
    Manages structured multi-account content repository:
    content/
    └── <Nama Akun>/
        ├── Video/
        │   └── <Tanggal>/
        │       ├── Vid1.mp4 (opsional Vid1.txt / Auto-LLM Caption)
        │       └── Vid2.mp4
        ├── Poster/
        │   └── <Tanggal>/
        │       ├── Pic1.jpg (opsional Pic1.txt / Auto-LLM Caption)
        │       └── Pic2.jpg
        └── Carousel/
            └── <Tanggal>/
                └── <Nama Carousel>/
                    ├── Slide1.jpg
                    ├── Slide2.jpg
                    └── caption.txt (opsional Auto-LLM Caption)
    """

    @classmethod
    def get_history_file(cls, account_name: str) -> Path:
        """Returns the upload history tracker path for an account."""
        acc_dir = get_account_dir(account_name)
        history_file = acc_dir / "upload_history.json"
        if not history_file.exists():
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)
        return history_file

    @classmethod
    def get_custom_order_file(cls, account_name: str) -> Path:
        """Returns the custom queue order path for an account."""
        acc_dir = get_account_dir(account_name)
        order_file = acc_dir / "queue_order.json"
        if not order_file.exists():
            with open(order_file, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)
        return order_file

    @classmethod
    def load_custom_order(cls, account_name: str) -> List[str]:
        """Loads ordered list of item_keys for an account."""
        order_file = cls.get_custom_order_file(account_name)
        try:
            with open(order_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    @classmethod
    def save_custom_order(cls, account_name: str, ordered_keys: List[str]) -> bool:
        """Saves custom queue ordering of item_keys."""
        order_file = cls.get_custom_order_file(account_name)
        try:
            with open(order_file, "w", encoding="utf-8") as f:
                json.dump(ordered_keys, f, indent=2)
            return True
        except Exception as e:
            console.print(f"[bold red]Gagal menyimpan custom queue order: {e}[/bold red]")
            return False

    @classmethod
    def load_history(cls, account_name: str) -> Dict[str, Any]:
        """Loads upload history for an account."""
        hist_file = cls.get_history_file(account_name)
        try:
            with open(hist_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @classmethod
    def mark_as_uploaded(cls, account_name: str, item_key: str, platform: str, proof_path: Optional[str] = None, post_url: Optional[str] = None):
        """Marks a content item as successfully uploaded with timestamp, proof, and post URL."""
        hist_file = cls.get_history_file(account_name)
        history = cls.load_history(account_name)
        
        if item_key not in history:
            history[item_key] = {"uploaded_platforms": [], "timestamps": {}, "proofs": {}, "post_urls": {}}

        if "post_urls" not in history[item_key]:
            history[item_key]["post_urls"] = {}

        if "timestamps" not in history[item_key]:
            history[item_key]["timestamps"] = {}

        if "proofs" not in history[item_key]:
            history[item_key]["proofs"] = {}

        if platform not in history[item_key]["uploaded_platforms"]:
            history[item_key]["uploaded_platforms"].append(platform)

        history[item_key]["timestamps"][platform] = time.strftime("%Y-%m-%d %H:%M:%S")
        if proof_path:
            history[item_key]["proofs"][platform] = str(proof_path)
        if post_url:
            history[item_key]["post_urls"][platform] = str(post_url).strip()

        with open(hist_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

    @classmethod
    def update_post_urls(cls, account_name: str, item_key: str, post_urls: Dict[str, str]) -> bool:
        """Updates or sets post URLs for specific platforms of an item."""
        hist_file = cls.get_history_file(account_name)
        history = cls.load_history(account_name)

        if item_key not in history:
            history[item_key] = {"uploaded_platforms": [], "timestamps": {}, "proofs": {}, "post_urls": {}}
        
        if "post_urls" not in history[item_key]:
            history[item_key]["post_urls"] = {}

        for plat, url in post_urls.items():
            if url:
                history[item_key]["post_urls"][plat] = str(url).strip()
            elif plat in history[item_key]["post_urls"]:
                del history[item_key]["post_urls"][plat]

        with open(hist_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
        return True

    @classmethod
    def auto_fetch_post_links(cls, account_name: str, item_key: str, force_refresh: bool = True) -> Dict[str, str]:
        """
        Attempts to automatically extract the live exact post URLs from TikTok Studio,
        Instagram Profile Feed, and Facebook Fanspage concurrently in parallel with caption matching.
        Forces re-fetch when requested to overwrite stale or incorrect URLs.
        """
        history = cls.load_history(account_name)
        hist_item = history.get(item_key, {})
        uploaded = hist_item.get("uploaded_platforms", [])
        post_urls = dict(hist_item.get("post_urls", {}))

        # Retrieve caption for keyword matching
        caption_snippet = ""
        try:
            items = cls.scan_content(account_name)
            target = next((it for it in items if it.get("item_key") == item_key), None)
            if target:
                caption_snippet = target.get("caption", "") or target.get("name", "")
        except Exception:
            pass

        tasks = {}
        with ThreadPoolExecutor(max_workers=3) as executor:
            if "tiktok" in uploaded and (force_refresh or not post_urls.get("tiktok")):
                from src.tiktok_uploader import TikTokUploader
                tasks["tiktok"] = executor.submit(TikTokUploader.fetch_latest_post_link, account_name, caption_snippet)

            if "instagram" in uploaded and (force_refresh or not post_urls.get("instagram")):
                from src.instagram_uploader import InstagramUploader
                tasks["instagram"] = executor.submit(InstagramUploader.fetch_latest_post_link, account_name, caption_snippet)

            if "facebook" in uploaded and (force_refresh or not post_urls.get("facebook")):
                from src.facebook_uploader import FacebookUploader
                tasks["facebook"] = executor.submit(FacebookUploader.fetch_latest_post_link, account_name, caption_snippet)

            for plat, fut in tasks.items():
                try:
                    res_url = fut.result(timeout=14)
                    if res_url:
                        post_urls[plat] = res_url
                except Exception as e:
                    console.print(f"[yellow]{plat.capitalize()} fetch error: {e}[/yellow]")

        # Save any newly discovered URLs
        if post_urls:
            cls.update_post_urls(account_name, item_key, post_urls)

        return post_urls

    @classmethod
    def read_or_generate_caption_and_meta(
        cls,
        base_file_or_dir: Path,
        category: str,
        account_name: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Reads existing caption or automatically generates engaging LLM caption with max 4 hashtags.
        """
        caption = ""
        default_db = "-7" if category == "Video" else "0"
        meta = {
            "tiktok_mentions": "",
            "instagram_mentions": "",
            "sound_mode": "favorite",
            "sound_query": "",
            "sound_db": default_db,
            "platforms": ["tiktok", "instagram", "facebook"],
            "as_draft": False
        }

        # 1. Cek jika user sudah membuat .txt atau .json manual
        if base_file_or_dir.is_file():
            txt_file = base_file_or_dir.with_suffix(".txt")
            json_file = base_file_or_dir.with_suffix(".json")
            
            if json_file.exists():
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        caption = data.get("caption", "")
                        meta.update(data)
                except Exception:
                    pass

            if not caption and txt_file.exists():
                try:
                    with open(txt_file, "r", encoding="utf-8") as f:
                        caption = f.read().strip()
                except Exception:
                    pass

        elif base_file_or_dir.is_dir():
            txt_file = base_file_or_dir / "caption.txt"
            json_file = base_file_or_dir / "meta.json"

            if json_file.exists():
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        caption = data.get("caption", "")
                        meta.update(data)
                except Exception:
                    pass

            if not caption and txt_file.exists():
                try:
                    with open(txt_file, "r", encoding="utf-8") as f:
                        caption = f.read().strip()
                except Exception:
                    pass

        # 2. JIKA CAPTION BELUM ADA -> Buat placeholder cepat tanpa memblokir scanning
        if not caption:
            caption = ""

        return caption, meta


    @classmethod
    def get_next_item_name(cls, account: str, category: str, date: str, ext: str = "") -> str:
        """
        Computes the standard sequential filename/foldername:
        e.g. video-2026-08-19-01.mp4, poster-2026-08-19-01.jpeg, carousel-2026-08-19-01
        Calculates next sequential 2-digit number based on existing items in that category and date.
        """
        target_dir = CONTENT_DIR / account / category / date
        target_dir.mkdir(parents=True, exist_ok=True)
        cat_lower = category.lower()

        existing_nums = []
        if category == "Carousel":
            for p in target_dir.iterdir():
                if p.is_dir():
                    m = re.search(rf"{cat_lower}-{re.escape(date)}-(\d+)", p.name, re.I) or re.search(r"(\d+)$", p.name)
                    if m:
                        try:
                            existing_nums.append(int(m.group(1)))
                        except Exception:
                            pass
                    else:
                        existing_nums.append(1)
        else:
            for p in target_dir.iterdir():
                if p.is_file() and not p.name.endswith(".json") and not p.name.endswith(".txt"):
                    m = re.search(rf"{cat_lower}-{re.escape(date)}-(\d+)", p.stem, re.I) or re.search(r"(\d+)$", p.stem)
                    if m:
                        try:
                            existing_nums.append(int(m.group(1)))
                        except Exception:
                            pass
                    else:
                        existing_nums.append(1)

        next_num = (max(existing_nums) + 1) if existing_nums else 1
        base_name = f"{cat_lower}-{date}-{next_num:02d}"
        if ext:
            clean_ext = ext if ext.startswith(".") else f".{ext}"
            return f"{base_name}{clean_ext}"
        return base_name

    @classmethod
    def _extract_item_timestamp(cls, item_path: Path, date_str: str, slides: Optional[List[Path]] = None) -> float:
        """
        Extracts high-precision chronological timestamp from filesystem modification timestamp (mtime),
        ensuring newly uploaded media appears at the very top of the feed.
        """
        try:
            if slides and len(slides) > 0:
                return max(s.stat().st_mtime for s in slides)
            if item_path.exists():
                return item_path.stat().st_mtime
        except Exception:
            pass

        try:
            return datetime.strptime(date_str, "%Y-%m-%d").timestamp()
        except Exception:
            return 0.0

    @classmethod
    def scan_content(cls, account_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scans content directory across accounts, categories, and dates.
        Auto-generates LLM captions with max 4 hashtags if none exists.
        """
        items = []
        accounts = [account_name] if account_name else [acc["name"] for acc in AccountManager.list_accounts()]

        for acc in accounts:
            acc_dir = CONTENT_DIR / acc
            if not acc_dir.exists():
                get_account_content_dir(acc)
                continue

            history = cls.load_history(acc)
            custom_order_keys = cls.load_custom_order(acc)
            order_lookup = {k: idx for idx, k in enumerate(custom_order_keys)}

            # 1. SCAN KATEGORI: VIDEO
            video_dir = acc_dir / "Video"
            if video_dir.exists():
                for date_folder in sorted(video_dir.iterdir()):
                    if date_folder.is_dir():
                        for vid_file in sorted(date_folder.iterdir()):
                            if vid_file.is_file() and vid_file.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS:
                                item_key = f"Video/{date_folder.name}/{vid_file.name}"
                                caption, meta = cls.read_or_generate_caption_and_meta(vid_file, "Video", acc)
                                hist_item = history.get(item_key, {})
                                uploaded_p = hist_item.get("uploaded_platforms", [])
                                uploaded_ts = hist_item.get("timestamps", {})
                                post_urls = hist_item.get("post_urls", {})
                                item_ts = cls._extract_item_timestamp(vid_file, date_folder.name)
                                mtime = vid_file.stat().st_mtime if vid_file.exists() else item_ts
                                
                                items.append({
                                    "account": acc,
                                    "category": "Video",
                                    "date": date_folder.name,
                                    "name": vid_file.name,
                                    "path": vid_file,
                                    "item_key": item_key,
                                    "caption": caption,
                                    "meta": meta,
                                    "created_at": item_ts,
                                    "mtime": mtime,
                                    "custom_order": order_lookup.get(item_key, 999999),
                                    "uploaded_platforms": uploaded_p,
                                    "uploaded_timestamps": uploaded_ts,
                                    "post_urls": post_urls,
                                    "status": "UPLOADED" if uploaded_p else "PENDING"
                                })

            # 2. SCAN KATEGORI: POSTER
            poster_dir = acc_dir / "Poster"
            if poster_dir.exists():
                for date_folder in sorted(poster_dir.iterdir()):
                    if date_folder.is_dir():
                        for pic_file in sorted(date_folder.iterdir()):
                            if pic_file.is_file() and pic_file.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                                item_key = f"Poster/{date_folder.name}/{pic_file.name}"
                                caption, meta = cls.read_or_generate_caption_and_meta(pic_file, "Poster", acc)
                                hist_item = history.get(item_key, {})
                                uploaded_p = hist_item.get("uploaded_platforms", [])
                                uploaded_ts = hist_item.get("timestamps", {})
                                post_urls = hist_item.get("post_urls", {})
                                item_ts = cls._extract_item_timestamp(pic_file, date_folder.name)
                                mtime = pic_file.stat().st_mtime if pic_file.exists() else item_ts

                                items.append({
                                    "account": acc,
                                    "category": "Poster",
                                    "date": date_folder.name,
                                    "name": pic_file.name,
                                    "path": pic_file,
                                    "item_key": item_key,
                                    "caption": caption,
                                    "meta": meta,
                                    "created_at": item_ts,
                                    "mtime": mtime,
                                    "custom_order": order_lookup.get(item_key, 999999),
                                    "uploaded_platforms": uploaded_p,
                                    "uploaded_timestamps": uploaded_ts,
                                    "post_urls": post_urls,
                                    "status": "UPLOADED" if uploaded_p else "PENDING"
                                })

            # 3. SCAN KATEGORI: CAROUSEL
            carousel_dir = acc_dir / "Carousel"
            if carousel_dir.exists():
                for date_folder in sorted(carousel_dir.iterdir()):
                    if date_folder.is_dir():
                        for car_sub in sorted(date_folder.iterdir()):
                            if car_sub.is_dir():
                                slides = [
                                    img for img in sorted(car_sub.iterdir())
                                    if img.is_file() and img.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
                                ]
                                if slides:
                                    item_key = f"Carousel/{date_folder.name}/{car_sub.name}"
                                    caption, meta = cls.read_or_generate_caption_and_meta(car_sub, "Carousel", acc)
                                    hist_item = history.get(item_key, {})
                                    uploaded_p = hist_item.get("uploaded_platforms", [])
                                    uploaded_ts = hist_item.get("timestamps", {})
                                    post_urls = hist_item.get("post_urls", {})
                                    item_ts = cls._extract_item_timestamp(car_sub, date_folder.name, slides)
                                    mtime = min(s.stat().st_mtime for s in slides) if slides else item_ts

                                    items.append({
                                        "account": acc,
                                        "category": "Carousel",
                                        "date": date_folder.name,
                                        "name": f"{car_sub.name} ({len(slides)} Slides)",
                                        "path": car_sub,
                                        "slides": slides,
                                        "item_key": item_key,
                                        "caption": caption,
                                        "meta": meta,
                                        "created_at": item_ts,
                                        "mtime": mtime,
                                        "custom_order": order_lookup.get(item_key, 999999),
                                        "uploaded_platforms": uploaded_p,
                                        "uploaded_timestamps": uploaded_ts,
                                        "post_urls": post_urls,
                                        "status": "UPLOADED" if uploaded_p else "PENDING"
                                    })

        return items

    @classmethod
    def delete_item(cls, account_name: str, category: str, date: str, item_name: str, item_key: Optional[str] = None) -> bool:
        """Safely deletes an item (video/poster file and its metadata, or carousel folder)."""
        acc_dir = CONTENT_DIR / account_name / category / date
        if not acc_dir.exists():
            return False

        if category == "Carousel":
            if item_key and "/" in item_key:
                folder_name = item_key.split("/")[-1]
            else:
                folder_name = item_name.split(" (")[0].strip()
            
            target_folder = acc_dir / folder_name
            if target_folder.exists() and target_folder.is_dir():
                import shutil
                shutil.rmtree(target_folder)
                return True
            for folder in acc_dir.iterdir():
                if folder.is_dir() and (folder.name in item_name or item_name.startswith(folder.name)):
                    import shutil
                    shutil.rmtree(folder)
                    return True
        else:
            media_file = acc_dir / item_name
            txt_file = acc_dir / f"{media_file.stem}.txt"
            json_file = acc_dir / f"{media_file.stem}.json"
            
            deleted = False
            if media_file.exists():
                media_file.unlink()
                deleted = True
            if txt_file.exists():
                try:
                    txt_file.unlink()
                except Exception:
                    pass
            if json_file.exists():
                try:
                    json_file.unlink()
                except Exception:
                    pass
            return deleted
        return False

    @classmethod
    def print_content_table(cls, account_name: Optional[str] = None):
        """Prints a beautifully formatted table of all scanned content."""
        items = cls.scan_content(account_name)
        
        table = Table(title="[bold green]MANAJEMEN KONTEN PER AKUN[/bold green]", show_lines=True)
        table.add_column("Akun", style="magenta", justify="left")
        table.add_column("Kategori", style="cyan", justify="center")
        table.add_column("Tanggal", style="yellow", justify="center")
        table.add_column("File / Konten", style="white", justify="left")
        table.add_column("Caption (Auto LLM / Custom)", style="italic dim", justify="left", max_width=40)
        table.add_column("Status Upload", justify="center")

        if not items:
            console.print(Panel(
                "[yellow]Belum ada konten ditemukan di folder content/\n"
                "Silakan letakkan video/gambar di: content/<Nama Akun>/<Video|Poster|Carousel>/<Tanggal>/[/yellow]"
            ))
            return

        for item in items:
            if item["status"] == "UPLOADED":
                status_str = f"[bold green][OK] SUKSES[/bold green]\n[dim]({', '.join(item['uploaded_platforms']).upper()})[/dim]"
            else:
                status_str = "[bold yellow]PENDING[/bold yellow]"

            table.add_row(
                item["account"],
                item["category"],
                item["date"],
                item["name"],
                item["caption"][:40] + ("..." if len(item["caption"]) > 40 else ""),
                status_str
            )

        console.print(table)

    @classmethod
    def get_platform_caption(cls, base_caption: str, platform_mentions: str = "") -> str:
        """
        Combines the main caption with platform-specific mentions / tags.
        Places mentions directly after the narrative caption text and BEFORE the hashtag block.
        Ensures usernames are properly prefixed with '@' and prevents duplicate tagging.
        """
        base_caption = (base_caption or "").strip()
        platform_mentions = (platform_mentions or "").strip()
        if not platform_mentions:
            return base_caption

        # Normalize mention tokens (e.g. "@user1, user2" -> "@user1 @user2")
        raw_tokens = [t.strip() for t in re.split(r'[\s,]+', platform_mentions) if t.strip()]
        cleaned_tokens = []
        for t in raw_tokens:
            cleaned_tokens.append(t if t.startswith("@") else f"@{t}")
        mentions_str = " ".join(cleaned_tokens)

        if not base_caption:
            return mentions_str

        # If mentions are already included in the base caption, do not duplicate
        if mentions_str.lower() in base_caption.lower():
            return base_caption

        # Detect trailing hashtag block (e.g. "\n\n#fyp #viral" or " #tag1 #tag2")
        hashtag_match = re.search(r'(\s*(?:#[a-zA-Z0-9_\u0080-\uffff]+\s*)+)$', base_caption)
        if hashtag_match:
            body_text = base_caption[:hashtag_match.start()].rstrip()
            hashtags_block = hashtag_match.group(1).strip()
            if body_text:
                return f"{body_text}\n\n{mentions_str}\n\n{hashtags_block}"
            else:
                return f"{mentions_str}\n\n{hashtags_block}"

        return f"{base_caption}\n\n{mentions_str}"

    @classmethod
    def process_content_item(
        cls,
        item: Dict[str, Any],
        platform_filter: str = "all",
        headless: bool = False,
        session_id: Optional[str] = None
    ) -> bool:
        """Uploads a specific scanned content item based on its category and connected platforms."""
        from src.publish_tracker import PublishTracker

        account = item["account"]
        category = item["category"]
        caption = item["caption"]
        meta = item["meta"]

        tt_caption = cls.get_platform_caption(caption, meta.get("tiktok_mentions", ""))
        ig_caption = cls.get_platform_caption(caption, meta.get("instagram_mentions", ""))
        fb_caption = caption

        # 1. Tentukan platform target: jika "all", deteksi platform yang sesi login sertifikasinya aktif
        if platform_filter == "all":
            target_platforms = []
            if AuthManager.is_authenticated(account, "tiktok"):
                target_platforms.append("tiktok")
            if AuthManager.is_authenticated(account, "instagram") or AuthManager.is_instagram_mobile_authenticated(account):
                target_platforms.append("instagram")
            if AuthManager.is_authenticated(account, "facebook"):
                target_platforms.append("facebook")
            if not target_platforms:
                target_platforms = ["tiktok"]
        else:
            target_platforms = [p.strip().lower() for p in platform_filter.split(",")]

        # Inisialisasi tracker sesi jika session_id tersedia
        if session_id:
            if not PublishTracker.get_session(session_id):
                PublishTracker.init_session(
                    session_id=session_id,
                    account=account,
                    item_key=item["item_key"],
                    item_name=item["name"],
                    category=category,
                    platforms=target_platforms,
                    date_str=item.get("date", "")
                )
            first_p = target_platforms[0] if target_platforms else "tiktok"
            PublishTracker.update_step(
                session_id=session_id,
                platform=first_p,
                step_name="Membuka browser visual...",
                platform_percent=10,
                log_message=f"Membuka browser visual untuk akun '{account}' ({', '.join(target_platforms).upper()})...",
                log_type="info"
            )

        console.print(Panel(
            f"[bold cyan]Memproses Upload:[/] [magenta]{account}[/] | [yellow]{category} ({item['date']})[/] | [white]{item['name']}[/]\n"
            f"[dim]Platform Target: {', '.join(target_platforms).upper()}[/dim]"
        ))

        success = True

        # 1. KATEGORI VIDEO (TikTok Studio, IG Reels, Facebook Reels)
        if category == "Video":
            video_path = item["path"]

            if "tiktok" in target_platforms:
                uploader = TikTokUploader(headless=headless)
                ok, msg, proof = uploader.upload(
                    video_path=video_path,
                    caption=tt_caption,
                    as_draft=meta.get("as_draft", False),
                    account_name=account,
                    sound_mode=meta.get("sound_mode", "favorite"),
                    tiktok_sound_query=meta.get("sound_query", ""),
                    sound_volume_db=meta.get("sound_db", "-7"),
                    tiktok_product=meta.get("tiktok_product"),
                    session_id=session_id
                )
                if ok:
                    cls.mark_as_uploaded(account, item["item_key"], "tiktok", proof)
                else:
                    success = False

            if "instagram" in target_platforms:
                uploader = InstagramUploader(headless=headless)
                ok, msg, proof = uploader.upload(
                    video_path=video_path,
                    caption=ig_caption,
                    as_reel=True,
                    account_name=account,
                    session_id=session_id
                )
                if ok:
                    cls.mark_as_uploaded(account, item["item_key"], "instagram", proof)
                else:
                    success = False

            if "facebook" in target_platforms:
                from src.facebook_uploader import FacebookUploader
                uploader = FacebookUploader(headless=headless)
                ok, msg, proof = uploader.upload(
                    video_path=video_path,
                    caption=fb_caption,
                    as_reel=True,
                    account_name=account,
                    session_id=session_id
                )
                if ok:
                    cls.mark_as_uploaded(account, item["item_key"], "facebook", proof)
                else:
                    success = False

        # 2. KATEGORI POSTER (TikTok Studio, IG Direct, Facebook Fanspage)
        elif category == "Poster":
            img_path = item["path"]

            if "tiktok" in target_platforms:
                uploader = TikTokUploader(headless=headless)
                ok, msg, proof = uploader.upload_photos(
                    photo_paths=[img_path],
                    caption=tt_caption,
                    title="",
                    as_draft=meta.get("as_draft", False),
                    account_name=account,
                    sound_mode=meta.get("sound_mode", "favorite"),
                    tiktok_sound_query=meta.get("sound_query", ""),
                    category_label="Poster",
                    session_id=session_id,
                    tiktok_product=meta.get("tiktok_product")
                )
                if ok:
                    cls.mark_as_uploaded(account, item["item_key"], "tiktok", proof)
                else:
                    success = False

            if "instagram" in target_platforms:
                uploader = InstagramUploader(headless=headless)
                ok, msg, proof = uploader.upload_media(
                    media_paths=[img_path],
                    caption=ig_caption,
                    is_reel=False,
                    account_name=account,
                    session_id=session_id
                )
                if ok:
                    cls.mark_as_uploaded(account, item["item_key"], "instagram", proof)
                else:
                    success = False

            if "facebook" in target_platforms:
                from src.facebook_uploader import FacebookUploader
                uploader = FacebookUploader(headless=headless)
                ok, msg, proof = uploader.upload_media(
                    media_paths=[img_path],
                    caption=fb_caption,
                    is_reel=False,
                    account_name=account,
                    session_id=session_id
                )
                if ok:
                    cls.mark_as_uploaded(account, item["item_key"], "facebook", proof)
                else:
                    success = False

        # 3. KATEGORI CAROUSEL (TikTok Studio, IG Direct, Facebook Fanspage)
        elif category == "Carousel":
            slides = item.get("slides", [])

            if "tiktok" in target_platforms and slides:
                uploader = TikTokUploader(headless=headless)
                ok, msg, proof = uploader.upload_photos(
                    photo_paths=slides,
                    caption=tt_caption,
                    title="",
                    as_draft=meta.get("as_draft", False),
                    account_name=account,
                    sound_mode=meta.get("sound_mode", "favorite"),
                    tiktok_sound_query=meta.get("sound_query", ""),
                    category_label="Carousel",
                    session_id=session_id,
                    tiktok_product=meta.get("tiktok_product")
                )
                if ok:
                    cls.mark_as_uploaded(account, item["item_key"], "tiktok", proof)
                else:
                    success = False

            if "instagram" in target_platforms and slides:
                uploader = InstagramUploader(headless=headless)
                ok, msg, proof = uploader.upload_media(
                    media_paths=slides,
                    caption=ig_caption,
                    is_reel=False,
                    account_name=account,
                    session_id=session_id
                )
                if ok:
                    cls.mark_as_uploaded(account, item["item_key"], "instagram", proof)
                else:
                    success = False

            if "facebook" in target_platforms and slides:
                from src.facebook_uploader import FacebookUploader
                uploader = FacebookUploader(headless=headless)
                ok, msg, proof = uploader.upload_media(
                    media_paths=slides,
                    caption=fb_caption,
                    is_reel=False,
                    account_name=account,
                    session_id=session_id
                )
                if ok:
                    cls.mark_as_uploaded(account, item["item_key"], "facebook", proof)
                else:
                    success = False

        return success

    @classmethod
    def process_all_pending(
        cls,
        account_name: Optional[str] = None,
        category_filter: Optional[str] = None,
        date_filter: Optional[str] = None,
        platform_filter: str = "all",
        headless: bool = False
    ):
        """Processes and uploads all pending items matching filters."""
        all_items = cls.scan_content(account_name)
        pending_items = [i for i in all_items if i["status"] == "PENDING"]

        if category_filter:
            pending_items = [i for i in pending_items if i["category"].lower() == category_filter.lower()]

        if date_filter:
            pending_items = [i for i in pending_items if i["date"] == date_filter]

        if not pending_items:
            console.print("[bold yellow]Tidak ada konten PENDING yang perlu diposting.[/bold yellow]")
            return

        console.print(f"[bold green]Ditemukan {len(pending_items)} konten PENDING siap diposting![/bold green]")
        for idx, item in enumerate(pending_items, 1):
            console.print(f"\n[bold cyan]─── ({idx}/{len(pending_items)}) Memproses {item['name']} ───[/bold cyan]")
            cls.process_content_item(item, platform_filter=platform_filter, headless=headless)

        console.print("\n[bold green]=== SEMUA KONTEN SELESAI DIPROSES! ===[/bold green]")
        cls.print_content_table(account_name)
