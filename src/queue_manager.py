import os
import json
import shutil
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table

from src.config import (
    QUEUE_DIR,
    POSTED_DIR,
    FAILED_DIR,
    LOGS_DIR,
    SUPPORTED_VIDEO_EXTENSIONS
)
from src.tiktok_uploader import TikTokUploader
from src.instagram_uploader import InstagramUploader
from src.audio_processor import AudioProcessor

console = Console(highlight=False, legacy_windows=False)

class QueueManager:
    """Manages processing video upload queues, batch uploads, audio mixing, and archiving."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.tiktok_uploader = TikTokUploader(headless=headless)
        self.instagram_uploader = InstagramUploader(headless=headless)

    def list_queue(self) -> List[Dict[str, Any]]:
        """List all pending items in the queue directory."""
        items = []
        if not QUEUE_DIR.exists():
            return items

        for file_path in QUEUE_DIR.iterdir():
            if file_path.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS:
                meta_file = file_path.with_suffix(".json")
                metadata = {}
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                    except Exception:
                        pass

                items.append({
                    "video_path": file_path,
                    "name": file_path.name,
                    "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
                    "caption": metadata.get("caption", file_path.stem),
                    "platform": metadata.get("platform", "all").lower(),
                    "as_draft": metadata.get("as_draft", False),
                    "sound": metadata.get("sound", None),
                    "original_volume": metadata.get("original_volume", None),
                    "music_volume": metadata.get("music_volume", None),
                    "preset": metadata.get("preset", None),
                    "meta_path": meta_file if meta_file.exists() else None
                })
        return items

    def print_queue_table(self):
        """Displays formatted table of items in the queue."""
        items = self.list_queue()
        table = Table(title="Daftar Antrean Video (queue/)")
        table.add_column("No", justify="right", style="cyan")
        table.add_column("Nama File", style="bold white")
        table.add_column("Ukuran (MB)", justify="right", style="green")
        table.add_column("Target Platform", style="magenta")
        table.add_column("Sound / Preset", style="yellow")
        table.add_column("Caption", style="dim")

        if not items:
            console.print("[yellow]Antrean kosong. Letakkan file video di folder 'queue/' untuk memproses.[/yellow]")
            return

        for idx, item in enumerate(items, 1):
            sound_info = item["preset"] or (Path(item["sound"]).name if item["sound"] else "Original")
            table.add_row(
                str(idx),
                item["name"],
                str(item["size_mb"]),
                item["platform"],
                sound_info,
                item["caption"][:30] + ("..." if len(item["caption"]) > 30 else "")
            )
        console.print(table)

    def process_queue(self, platform_filter: str = "all") -> Dict[str, Any]:
        """
        Processes all queued items with optional sound mixing.
        Moves successfully uploaded files to 'posted/' and failed to 'failed/'.
        """
        items = self.list_queue()
        if not items:
            console.print("[yellow]Tidak ada video dalam antrean untuk diproses.[/yellow]")
            return {"total": 0, "success": 0, "failed": 0}

        results = {"total": len(items), "success": 0, "failed": 0, "details": []}

        for item in items:
            video_path: Path = item["video_path"]
            meta_path: Optional[Path] = item["meta_path"]
            caption = item["caption"]
            target_platform = item["platform"]
            as_draft = item["as_draft"]

            if platform_filter != "all" and target_platform not in ["all", platform_filter]:
                continue

            console.print(f"\n[bold blue]=== Memproses: {video_path.name} ===[/bold blue]")

            # Process audio / sound adjustments if configured
            upload_video_path, is_temp = AudioProcessor.process_video_audio(
                video_path=video_path,
                sound_input=item["sound"],
                original_volume=item["original_volume"],
                music_volume=item["music_volume"],
                preset=item["preset"]
            )

            platforms_to_run = []
            if target_platform in ["all", "tiktok"] and (platform_filter in ["all", "tiktok"]):
                platforms_to_run.append("tiktok")
            if target_platform in ["all", "instagram"] and (platform_filter in ["all", "instagram"]):
                platforms_to_run.append("instagram")

            item_success = True
            platform_logs = {}

            for plat in platforms_to_run:
                if plat == "tiktok":
                    ok, msg, screen = self.tiktok_uploader.upload(
                        video_path=upload_video_path,
                        caption=caption,
                        as_draft=as_draft
                    )
                    platform_logs["tiktok"] = {"success": ok, "message": msg, "screenshot": screen}
                    if not ok:
                        item_success = False

                elif plat == "instagram":
                    ok, msg, screen = self.instagram_uploader.upload(
                        video_path=upload_video_path,
                        caption=caption,
                        as_reel=True
                    )
                    platform_logs["instagram"] = {"success": ok, "message": msg, "screenshot": screen}
                    if not ok:
                        item_success = False

            # Clean up temp audio processed video if created
            if is_temp and upload_video_path.exists():
                try:
                    upload_video_path.unlink()
                except Exception:
                    pass

            # Archive / Move original files
            timestamp_str = time.strftime("%Y%m%d_%H%M%S")
            if item_success:
                dest_dir = POSTED_DIR / timestamp_str
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(video_path), str(dest_dir / video_path.name))
                if meta_path and meta_path.exists():
                    shutil.move(str(meta_path), str(dest_dir / meta_path.name))
                
                # Write receipt log
                receipt_path = dest_dir / "upload_receipt.json"
                with open(receipt_path, "w", encoding="utf-8") as f:
                    json.dump({"timestamp": timestamp_str, "platforms": platform_logs}, f, indent=2)

                results["success"] += 1
                console.print(f"[bold green][OK] Selesai & dipindahkan ke: {dest_dir}[/bold green]")
            else:
                dest_dir = FAILED_DIR / timestamp_str
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(video_path), str(dest_dir / video_path.name))
                if meta_path and meta_path.exists():
                    shutil.move(str(meta_path), str(dest_dir / meta_path.name))
                
                error_log_path = dest_dir / "error_log.json"
                with open(error_log_path, "w", encoding="utf-8") as f:
                    json.dump({"timestamp": timestamp_str, "platforms": platform_logs}, f, indent=2)

                results["failed"] += 1
                console.print(f"[bold red]✗ Gagal & dipindahkan ke: {dest_dir}[/bold red]")

            results["details"].append({
                "file": video_path.name,
                "status": "success" if item_success else "failed",
                "logs": platform_logs
            })

        return results
