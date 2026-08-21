import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table

from src.config import (
    ACCOUNTS_DIR,
    get_account_dir,
    get_account_state_file,
    slugify_account_name,
    get_safe_storage_state
)

console = Console(highlight=False, legacy_windows=False)

class AccountManager:
    """Manages multi-account profiles, metadata, and authentication states."""

    @staticmethod
    def create_or_get_account(account_name: str, description: str = "") -> Dict[str, Any]:
        """Registers a new account profile or returns existing info."""
        acc_dir = get_account_dir(account_name)
        info_file = acc_dir / "account_info.json"

        if info_file.exists():
            try:
                with open(info_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        data = {
            "name": account_name,
            "slug": slugify_account_name(account_name),
            "description": description or f"Profile for {account_name}",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "default_hashtags": [],
            "platforms": {
                "tiktok": {"connected": False},
                "instagram": {"connected": False}
            }
        }
        with open(info_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return data

    @staticmethod
    def list_accounts() -> List[Dict[str, Any]]:
        """List all accounts and their authentication status."""
        accounts = []
        if not ACCOUNTS_DIR.exists():
            return accounts

        for acc_folder in ACCOUNTS_DIR.iterdir():
            if acc_folder.is_dir() and not acc_folder.name.startswith((".", "_")):
                info_file = acc_folder / "account_info.json"
                name = acc_folder.name
                desc = ""
                if info_file.exists():
                    try:
                        with open(info_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            name = data.get("name", acc_folder.name)
                            desc = data.get("description", "")
                    except Exception:
                        pass

                tt_state = acc_folder / "tiktok_state.json"
                ig_state = acc_folder / "instagram_state.json"

                accounts.append({
                    "name": name,
                    "slug": acc_folder.name,
                    "folder": acc_folder,
                    "description": desc,
                    "tiktok_ready": tt_state.exists() and tt_state.stat().st_size > 50,
                    "instagram_ready": ig_state.exists() and ig_state.stat().st_size > 50
                })
        return accounts

    @staticmethod
    def _fetch_tiktok_profile_worker(account_name: str):
        """Worker function running in a background thread to fetch TikTok profile."""
        acc_dir = get_account_dir(account_name)
        profile_file = acc_dir / "tiktok_profile.json"
        avatar_local = acc_dir / "tiktok_avatar.jpg"
        state_file = acc_dir / "tiktok_state.json"

        if not state_file.exists():
            return

        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state_data = json.load(f)

            import requests
            session = requests.Session()
            for c in state_data.get("cookies", []):
                session.cookies.set(c["name"], c["value"], domain=c.get("domain", ".tiktok.com"))

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Referer": "https://www.tiktok.com/"
            }

            passport_res = session.get("https://www.tiktok.com/passport/web/account/info/", headers=headers, timeout=5)
            if passport_res.status_code == 200:
                p_data = passport_res.json().get("data", {})
                username = p_data.get("username")
                screen_name = p_data.get("screen_name")
                user_id = str(p_data.get("user_id", ""))

                profile_info = {
                    "username": username or screen_name,
                    "nickname": screen_name or account_name,
                    "user_id": user_id,
                    "avatar_url": "",
                    "followers": 0,
                    "likes": 0,
                    "has_local_avatar": False
                }

                target_user = username or screen_name
                if target_user:
                    try:
                        user_res = requests.get(f"https://www.tiktok.com/@{target_user}", headers=headers, timeout=5)
                        if user_res.status_code == 200:
                            start_tag = '<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"'
                            idx = user_res.text.find(start_tag)
                            if idx != -1:
                                j_start = user_res.text.find('>', idx) + 1
                                j_end = user_res.text.find('</script>', j_start)
                                u_data = json.loads(user_res.text[j_start:j_end].strip())
                                u_detail = u_data.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {})
                                u_user = u_detail.get("userInfo", {}).get("user", {})
                                u_stats = u_detail.get("userInfo", {}).get("stats", {})

                                if u_user.get("nickname"):
                                    profile_info["nickname"] = u_user.get("nickname")
                                if u_user.get("uniqueId"):
                                    profile_info["username"] = u_user.get("uniqueId")
                                avatar_url = u_user.get("avatarMedium") or u_user.get("avatarThumb") or u_user.get("avatarLarger")
                                if avatar_url:
                                    profile_info["avatar_url"] = avatar_url
                                    try:
                                        img_res = requests.get(avatar_url, headers=headers, timeout=5)
                                        if img_res.status_code == 200:
                                            with open(avatar_local, "wb") as img_f:
                                                img_f.write(img_res.content)
                                            profile_info["has_local_avatar"] = True
                                    except Exception:
                                        pass
                                profile_info["followers"] = u_stats.get("followerCount", 0)
                                profile_info["likes"] = u_stats.get("heartCount", 0)
                    except Exception:
                        pass

                if (not profile_info.get("avatar_url") or not avatar_local.exists()) and state_file.exists():
                    try:
                        from playwright.sync_api import sync_playwright
                        from src.config import DEFAULT_USER_AGENT
                        with sync_playwright() as p:
                            browser = p.chromium.launch(headless=True)
                            safe_state = get_safe_storage_state(state_file)
                            context = browser.new_context(user_agent=DEFAULT_USER_AGENT, storage_state=safe_state)
                            page = context.new_page()
                            page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=25000, wait_until="domcontentloaded")
                            page.wait_for_timeout(3000)
                            avatar_src = page.evaluate("""() => {
                                const imgs = Array.from(document.querySelectorAll('img'));
                                for (const img of imgs) {
                                    if (img.src && (img.src.includes('tiktokcdn') || img.src.includes('avatar') || img.className.toLowerCase().includes('avatar'))) {
                                        return img.src;
                                    }
                                }
                                return null;
                            }""")
                            if avatar_src:
                                profile_info["avatar_url"] = avatar_src
                                img_res = requests.get(avatar_src, headers=headers, timeout=5)
                                if img_res.status_code == 200:
                                    with open(avatar_local, "wb") as img_f:
                                        img_f.write(img_res.content)
                                    profile_info["has_local_avatar"] = True
                            browser.close()
                    except Exception:
                        pass

                with open(profile_file, "w", encoding="utf-8") as f:
                    json.dump(profile_info, f, indent=2)
        except Exception:
            pass

    @staticmethod
    def get_tiktok_profile(account_name: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Retrieves cached TikTok profile data instantly without blocking the server.
        """
        acc_dir = get_account_dir(account_name)
        profile_file = acc_dir / "tiktok_profile.json"
        avatar_local = acc_dir / "tiktok_avatar.jpg"
        state_file = acc_dir / "tiktok_state.json"

        if not state_file.exists():
            return {}

        # 1. Return cached profile if exists
        if profile_file.exists() and not force_refresh:
            try:
                with open(profile_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["has_local_avatar"] = avatar_local.exists()
                    return data
            except Exception:
                pass

        # 2. Spawn non-blocking background thread
        import threading
        t = threading.Thread(target=AccountManager._fetch_tiktok_profile_worker, args=(account_name,), daemon=True)
        t.start()

        return {}

    @staticmethod
    def print_accounts_table():
        """Displays formatted table of all registered accounts."""
        accounts = AccountManager.list_accounts()
        table = Table(title="Daftar Akun Terdaftar (accounts/)")
        table.add_column("No", justify="right", style="cyan")
        table.add_column("Nama Akun", style="bold white")
        table.add_column("Folder / Slug", style="dim")
        table.add_column("TikTok Sesi", justify="center")
        table.add_column("Instagram Sesi", justify="center")

        if not accounts:
            console.print("[yellow]Belum ada akun yang terdaftar. Gunakan: python -m src.cli account add <nama_akun>[/yellow]")
            return

        for idx, acc in enumerate(accounts, 1):
            tt_status = "[green]AKTIF[/green]" if acc["tiktok_ready"] else "[red]BELUM LOGIN[/red]"
            ig_status = "[green]AKTIF[/green]" if acc["instagram_ready"] else "[red]BELUM LOGIN[/red]"
            table.add_row(
                str(idx),
                acc["name"],
                acc["slug"],
                tt_status,
                ig_status
            )
        console.print(table)
