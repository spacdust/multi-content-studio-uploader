import time
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console

from src.config import CONTENT_DIR
from src.account_manager import AccountManager
from src.auth_manager import AuthManager
from src.content_manager import ContentManager
from src.publish_tracker import PublishTracker

console = Console(highlight=False, legacy_windows=False)

class AutoScheduler:
    """
    Background Automated Scheduling Service:
    - Continuously watches all accounts and pending media.
    - Detects items with 'scheduled_time' timestamp in meta.json.
    - When current local time >= scheduled_time, automatically executes
      the multi-platform publish pipeline (TikTok, Instagram, Facebook).
    """

    _thread: Optional[threading.Thread] = None
    _stop_event = threading.Event()
    _is_active: bool = True
    _executing_keys = set()
    _lock = threading.Lock()
    _is_busy: bool = False
    _current_executing_item: Optional[Dict[str, Any]] = None
    _poll_interval: int = 20  # Poll every 20 seconds

    @classmethod
    def parse_scheduled_datetime(cls, sched_str: str) -> Optional[datetime]:
        """Parses scheduled_time ISO string to local naive datetime."""
        if not sched_str or not isinstance(sched_str, str):
            return None
        
        clean_str = sched_str.strip()
        # Remove timezone offset if present (e.g. +07:00 or Z) for local comparison
        clean_str = clean_str.split('+')[0].split('Z')[0]
        
        for fmt in [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M"
        ]:
            try:
                return datetime.strptime(clean_str, fmt)
            except ValueError:
                pass
        return None

    @classmethod
    def get_scheduled_items(cls) -> List[Dict[str, Any]]:
        """Scans all accounts and returns all pending scheduled items sorted by scheduled_time."""
        scheduled_list = []
        accounts = AccountManager.list_accounts()
        now = datetime.now()

        for acc in accounts:
            acc_name = acc.get("name")
            if not acc_name:
                continue

            items = ContentManager.scan_content(acc_name)
            for item in items:
                uploaded = item.get("uploaded_platforms", [])
                # If already uploaded to any or all platforms, skip
                if uploaded and len(uploaded) > 0:
                    continue

                meta = item.get("meta", {})
                sched_time_str = meta.get("scheduled_time")
                if not sched_time_str:
                    continue

                sched_dt = cls.parse_scheduled_datetime(sched_time_str)
                if not sched_dt:
                    continue

                diff_seconds = (sched_dt - now).total_seconds()
                is_due = diff_seconds <= 0

                scheduled_list.append({
                    "account": acc_name,
                    "item_key": item.get("item_key"),
                    "item_name": item.get("name"),
                    "category": item.get("category"),
                    "date": item.get("date"),
                    "scheduled_time": sched_time_str,
                    "scheduled_dt": sched_dt,
                    "diff_seconds": diff_seconds,
                    "is_due": is_due,
                    "item_data": item
                })

        scheduled_list.sort(key=lambda x: x["scheduled_dt"])
        return scheduled_list

    @classmethod
    def check_and_execute_due_items(cls):
        """Checks for due scheduled items and initiates sequential publishing."""
        if not cls._is_active:
            return

        with cls._lock:
            # Jika sedang ada proses upload yang berjalan, antrekan (jangan buka 2 browser bersamaan)
            if cls._is_busy:
                return

            scheduled_items = cls.get_scheduled_items()
            due_items = [i for i in scheduled_items if i["is_due"]]
            if not due_items:
                return

            # Ambil postingan yang paling pertama jatuh tempo (FIFO - First In, First Out)
            target = due_items[0]
            item_key = target["item_key"]
            account = target["account"]
            item_name = target["item_name"]
            item = target["item_data"]

            if item_key in cls._executing_keys:
                return

            cls._is_busy = True
            cls._executing_keys.add(item_key)
            cls._current_executing_item = target

        def runner(target_item=item, target_key=item_key, target_acc=account, target_name=item_name):
            session_id = f"sched_{int(time.time())}_{target_name[:8]}"
            try:
                console.print(f"[bold cyan][Auto-Scheduler][/bold cyan] [Jadwal] Waktu tayang tercapai untuk '{target_name}' ({target_acc})! Memulai proses publikasi otomatis...")
                PublishTracker.log(session_id, "sys", f"[Auto-Scheduler] Waktu tayang ({target_item.get('meta', {}).get('scheduled_time')}) tercapai. Menjalankan pipeline upload otomatis...", "info")
                
                ok = ContentManager.process_content_item(
                    item=target_item,
                    platform_filter="all",
                    headless=False,
                    session_id=session_id
                )
                if ok:
                    console.print(f"[bold green][Auto-Scheduler][/bold green] [OK] Publikasi terjadwal '{target_name}' ({target_acc}) BERHASIL!")
                else:
                    console.print(f"[bold yellow][Auto-Scheduler][/bold yellow] [!] Publikasi terjadwal '{target_name}' selesai dengan beberapa kendala.")
            except Exception as ex:
                console.print(f"[bold red][Auto-Scheduler Error][/bold red] Gagal mempublikasikan '{target_name}': {ex}")
            finally:
                with cls._lock:
                    cls._executing_keys.discard(target_key)
                    cls._is_busy = False
                    cls._current_executing_item = None

                # Estafet: Cek segera apakah ada postingan akun lain yang menunggu antrean akibat bentrok
                time.sleep(1.5)
                cls.check_and_execute_due_items()

        thread = threading.Thread(target=runner, daemon=True)
        thread.start()

    @classmethod
    def _worker_loop(cls):
        """Continuous background loop for the scheduler."""
        console.print("[bold green][Auto-Scheduler][/bold green] Service Auto-Scheduler background aktif dan berjalan!")
        while not cls._stop_event.is_set():
            try:
                cls.check_and_execute_due_items()
            except Exception as ex:
                console.print(f"[dim yellow][Auto-Scheduler Warning][/dim yellow] Kesalahan saat scan jadwal: {ex}")

            # Sleep with interruptible wait
            cls._stop_event.wait(cls._poll_interval)

    @classmethod
    def start(cls):
        """Starts the background scheduler thread."""
        if cls._thread is not None and cls._thread.is_alive():
            return

        cls._stop_event.clear()
        cls._thread = threading.Thread(target=cls._worker_loop, daemon=True, name="AutoSchedulerWorker")
        cls._thread.start()

    @classmethod
    def stop(cls):
        """Stops the background scheduler thread."""
        cls._stop_event.set()
        if cls._thread and cls._thread.is_alive():
            cls._thread.join(timeout=2)
        cls._thread = None
        console.print("[bold yellow][Auto-Scheduler][/bold yellow] Service Auto-Scheduler background dihentikan.")

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Returns comprehensive status of the scheduler."""
        scheduled = cls.get_scheduled_items()
        is_running = cls._thread is not None and cls._thread.is_alive()

        next_job = None
        if scheduled:
            first = scheduled[0]
            next_job = {
                "account": first["account"],
                "item_name": first["item_name"],
                "category": first["category"],
                "scheduled_time": first["scheduled_time"],
                "diff_seconds": round(first["diff_seconds"]),
                "is_due": first["is_due"]
            }

        return {
            "is_running": is_running,
            "is_active": cls._is_active,
            "is_busy": cls._is_busy,
            "current_executing": {
                "account": cls._current_executing_item["account"],
                "item_name": cls._current_executing_item["item_name"],
                "category": cls._current_executing_item["category"],
            } if cls._current_executing_item else None,
            "poll_interval_sec": cls._poll_interval,
            "total_scheduled_pending": len(scheduled),
            "executing_count": len(cls._executing_keys),
            "next_job": next_job,
            "upcoming_queue": [
                {
                    "account": s["account"],
                    "item_name": s["item_name"],
                    "category": s["category"],
                    "scheduled_time": s["scheduled_time"],
                    "diff_seconds": round(s["diff_seconds"]),
                    "is_due": s["is_due"]
                }
                for s in scheduled[:10]
            ]
        }
