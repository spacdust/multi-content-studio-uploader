import os
import json
import time
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

console = Console(highlight=False)

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
    def load_history(cls, account_name: str) -> Dict[str, Any]:
        """Loads upload history for an account."""
        hist_file = cls.get_history_file(account_name)
        try:
            with open(hist_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @classmethod
    def mark_as_uploaded(cls, account_name: str, item_key: str, platform: str, proof_path: Optional[str] = None):
        """Marks a content item as successfully uploaded."""
        hist_file = cls.get_history_file(account_name)
        history = cls.load_history(account_name)
        
        if item_key not in history:
            history[item_key] = {"uploaded_platforms": [], "timestamps": {}, "proofs": {}}

        if platform not in history[item_key]["uploaded_platforms"]:
            history[item_key]["uploaded_platforms"].append(platform)

        history[item_key]["timestamps"][platform] = time.strftime("%Y-%m-%d %H:%M:%S")
        if proof_path:
            history[item_key]["proofs"][platform] = str(proof_path)

        with open(hist_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

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
        meta = {
            "sound_mode": "search",
            "sound_query": "school",
            "sound_db": "-7",
            "platforms": ["tiktok", "instagram"],
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

            # 1. SCAN KATEGORI: VIDEO
            video_dir = acc_dir / "Video"
            if video_dir.exists():
                for date_folder in sorted(video_dir.iterdir()):
                    if date_folder.is_dir():
                        for vid_file in sorted(date_folder.iterdir()):
                            if vid_file.is_file() and vid_file.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS:
                                item_key = f"Video/{date_folder.name}/{vid_file.name}"
                                caption, meta = cls.read_or_generate_caption_and_meta(vid_file, "Video", acc)
                                uploaded_p = history.get(item_key, {}).get("uploaded_platforms", [])
                                
                                items.append({
                                    "account": acc,
                                    "category": "Video",
                                    "date": date_folder.name,
                                    "name": vid_file.name,
                                    "path": vid_file,
                                    "item_key": item_key,
                                    "caption": caption,
                                    "meta": meta,
                                    "uploaded_platforms": uploaded_p,
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
                                uploaded_p = history.get(item_key, {}).get("uploaded_platforms", [])

                                items.append({
                                    "account": acc,
                                    "category": "Poster",
                                    "date": date_folder.name,
                                    "name": pic_file.name,
                                    "path": pic_file,
                                    "item_key": item_key,
                                    "caption": caption,
                                    "meta": meta,
                                    "uploaded_platforms": uploaded_p,
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
                                    uploaded_p = history.get(item_key, {}).get("uploaded_platforms", [])

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
                                        "uploaded_platforms": uploaded_p,
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
    def process_content_item(cls, item: Dict[str, Any], platform_filter: str = "all", headless: bool = False) -> bool:
        """Uploads a specific scanned content item based on its category and connected platforms."""
        account = item["account"]
        category = item["category"]
        caption = item["caption"]
        meta = item["meta"]

        # 1. Tentukan platform target: jika "all", deteksi hanya platform yang sesi loginsertifikasinya aktif
        if platform_filter == "all":
            target_platforms = []
            if AuthManager.is_authenticated(account, "tiktok"):
                target_platforms.append("tiktok")
            if AuthManager.is_authenticated(account, "instagram"):
                target_platforms.append("instagram")
            if AuthManager.is_authenticated(account, "meta"):
                target_platforms.append("meta")
            if not target_platforms:
                target_platforms = ["tiktok"]
        else:
            target_platforms = [p.strip().lower() for p in platform_filter.split(",")]

        console.print(Panel(
            f"[bold cyan]Memproses Upload:[/] [magenta]{account}[/] | [yellow]{category} ({item['date']})[/] | [white]{item['name']}[/]\n"
            f"[dim]Platform Target: {', '.join(target_platforms).upper()}[/dim]"
        ))

        success = True

        # 1. KATEGORI VIDEO (TikTok Studio, IG Reels, Meta Suite)
        if category == "Video":
            video_path = item["path"]

            if "tiktok" in target_platforms:
                uploader = TikTokUploader(headless=headless)
                ok, msg, proof = uploader.upload(
                    video_path=video_path,
                    caption=caption,
                    as_draft=meta.get("as_draft", False),
                    account_name=account,
                    sound_mode=meta.get("sound_mode", "search"),
                    tiktok_sound_query=meta.get("sound_query", "school"),
                    sound_volume_db=meta.get("sound_db", "-7")
                )
                if ok:
                    cls.mark_as_uploaded(account, item["item_key"], "tiktok", proof)
                else:
                    success = False

            if "instagram" in target_platforms:
                uploader = InstagramUploader(headless=headless)
                ok, msg, proof = uploader.upload(
                    video_path=video_path,
                    caption=caption,
                    as_reel=True,
                    account_name=account
                )
                if ok:
                    cls.mark_as_uploaded(account, item["item_key"], "instagram", proof)
                else:
                    success = False

            if "meta" in target_platforms:
                from src.meta_uploader import MetaBusinessUploader
                uploader = MetaBusinessUploader(headless=headless)
                ok, msg, proof = uploader.upload_media(
                    account_name=account,
                    media_paths=[video_path],
                    caption=caption,
                    is_reel=True
                )
                if ok:
                    cls.mark_as_uploaded(account, item["item_key"], "meta", proof)
                else:
                    success = False

        # 2. KATEGORI POSTER (TikTok Studio, Meta Suite, IG Direct)
        elif category == "Poster":
            img_path = item["path"]

            if "tiktok" in target_platforms:
                uploader = TikTokUploader(headless=headless)
                ok, msg, proof = uploader.upload_photos(
                    photo_paths=[img_path],
                    caption=caption,
                    title="",
                    as_draft=meta.get("as_draft", False),
                    account_name=account,
                    sound_mode=meta.get("sound_mode", "search"),
                    tiktok_sound_query=meta.get("sound_query", "school"),
                    category_label="Poster"
                )
                if ok:
                    cls.mark_as_uploaded(account, item["item_key"], "tiktok", proof)
                else:
                    success = False

            if "instagram" in target_platforms:
                uploader = InstagramUploader(headless=headless)
                ok, msg, proof = uploader.upload(
                    video_path=img_path,
                    caption=caption,
                    as_reel=False,
                    account_name=account
                )
                if ok:
                    cls.mark_as_uploaded(account, item["item_key"], "instagram", proof)
                else:
                    success = False

            if "meta" in target_platforms:
                from src.meta_uploader import MetaBusinessUploader
                uploader = MetaBusinessUploader(headless=headless)
                ok, msg, proof = uploader.upload_media(
                    account_name=account,
                    media_paths=[img_path],
                    caption=caption,
                    is_reel=False
                )
                if ok:
                    cls.mark_as_uploaded(account, item["item_key"], "meta", proof)
                else:
                    success = False

        # 3. KATEGORI CAROUSEL (TikTok Studio, Meta Suite, IG Direct)
        elif category == "Carousel":
            slides = item.get("slides", [])

            if "tiktok" in target_platforms and slides:
                uploader = TikTokUploader(headless=headless)
                ok, msg, proof = uploader.upload_photos(
                    photo_paths=slides,
                    caption=caption,
                    title="",
                    as_draft=meta.get("as_draft", False),
                    account_name=account,
                    sound_mode=meta.get("sound_mode", "search"),
                    tiktok_sound_query=meta.get("sound_query", "school"),
                    category_label="Carousel"
                )
                if ok:
                    cls.mark_as_uploaded(account, item["item_key"], "tiktok", proof)
                else:
                    success = False

            if "instagram" in target_platforms and slides:
                uploader = InstagramUploader(headless=headless)
                ok, msg, proof = uploader.upload(
                    video_path=slides[0],
                    caption=caption,
                    as_reel=False,
                    account_name=account
                )
                if ok:
                    cls.mark_as_uploaded(account, item["item_key"], "instagram", proof)
                else:
                    success = False

            if "meta" in target_platforms and slides:
                from src.meta_uploader import MetaBusinessUploader
                uploader = MetaBusinessUploader(headless=headless)
                ok, msg, proof = uploader.upload_media(
                    account_name=account,
                    media_paths=slides,
                    caption=caption,
                    is_reel=False
                )
                if ok:
                    cls.mark_as_uploaded(account, item["item_key"], "meta", proof)
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
