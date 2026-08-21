import time
import json
import os
from pathlib import Path
from typing import Tuple, Optional, Dict
from rich.console import Console
from playwright.sync_api import sync_playwright

from src.config import (
    get_account_dir,
    get_account_state_file,
    TIKTOK_UPLOAD_URL,
    TIKTOK_LOGIN_URL,
    INSTAGRAM_BASE_URL,
    INSTAGRAM_LOGIN_URL,
    META_BUSINESS_LOGIN_URL,
    META_BUSINESS_HOME_URL,
    META_BUSINESS_COMPOSER_URL,
    DEFAULT_USER_AGENT,
    VIEWPORT,
    launch_browser,
    get_safe_storage_state
)
from src.account_manager import AccountManager

console = Console(highlight=False, legacy_windows=False)

class AuthManager:
    """Manages interactive non-headless visual login and persistent sessions per account."""

    @staticmethod
    def _normalize_samesite(val) -> str:
        """Playwright requires sameSite to be exactly 'Strict', 'Lax', or 'None'."""
        if not val or not isinstance(val, str):
            return "None"
        v = val.strip().lower()
        if "strict" in v:
            return "Strict"
        elif "lax" in v:
            return "Lax"
        else:
            return "None"

    @staticmethod
    def _save_storage_state_safe(context, state_file: Path) -> bool:
        """
        Safely saves storage_state by MERGING rotated cookies into existing state_file,
        preserving all authentic companion tokens (ttwid, odin_tt, store-idc, passport tokens).
        """
        try:
            new_cookies = context.cookies()
            has_session = any(
                c.get("name") in ["sessionid", "sessionid_ss", "sid_tt", "c_user", "ds_user_id"] and len(c.get("value", "")) > 5
                for c in new_cookies
            )
            if not has_session:
                return False

            existing_cookies_map = {}
            if state_file.exists() and state_file.stat().st_size > 50:
                try:
                    with open(state_file, "r", encoding="utf-8") as f:
                        old_state = json.load(f)
                    for c in old_state.get("cookies", []):
                        if c.get("name"):
                            existing_cookies_map[c["name"]] = c
                except Exception:
                    pass

            for c in new_cookies:
                name = c.get("name")
                if name:
                    c["sameSite"] = AuthManager._normalize_samesite(c.get("sameSite"))
                    existing_cookies_map[name] = c

            state = {
                "cookies": list(existing_cookies_map.values()),
                "origins": []
            }

            state_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_file = state_file.with_suffix(".tmp")
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
            tmp_file.replace(state_file)
            return True
        except Exception:
            return False

    @staticmethod
    def is_tiktok_authenticated(account_name: str = "default") -> bool:
        state_file = get_account_state_file(account_name, "tiktok")
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cookies = data.get("cookies", [])
                    return any(c.get("name") in ["sessionid", "sessionid_ss", "sid_tt", "passport_auth_status", "uid_tt", "sid_guard"] for c in cookies)
            except Exception:
                pass
        return False

    @staticmethod
    def is_instagram_authenticated(account_name: str = "default") -> bool:
        state_file = get_account_state_file(account_name, "instagram")
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cookies = data.get("cookies", [])
                    return any(c.get("name") in ["sessionid", "ds_user_id"] for c in cookies)
            except Exception:
                pass
        return False

    @staticmethod
    def is_facebook_authenticated(account_name: str = "default") -> bool:
        state_file = get_account_state_file(account_name, "facebook")
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cookies = data.get("cookies", [])
                    return any(c.get("name") in ["c_user", "xs"] for c in cookies)
            except Exception:
                pass
        return False

    @staticmethod
    def is_meta_authenticated(account_name: str = "default") -> bool:
        state_file = get_account_state_file(account_name, "meta")
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cookies = data.get("cookies", [])
                    # c_user, xs for Facebook; sessionid, ds_user_id for Instagram in Meta Suite
                    return any(c.get("name") in ["c_user", "xs", "sessionid", "ds_user_id"] for c in cookies)
            except Exception:
                pass
        return False

    @classmethod
    def is_authenticated(cls, account_name: str = "default", platform: str = "tiktok") -> bool:
        plat = platform.lower()
        if plat == "tiktok":
            return cls.is_tiktok_authenticated(account_name)
        elif plat in ["instagram", "instagram-mobile", "mobile"]:
            return cls.is_instagram_authenticated(account_name)
        elif plat == "facebook":
            return cls.is_facebook_authenticated(account_name)
        elif plat in ["meta", "meta_business"]:
            return cls.is_meta_authenticated(account_name)
        return False

    @classmethod
    def is_instagram_mobile_authenticated(cls, account_name: str = "default") -> bool:
        return cls.is_instagram_authenticated(account_name)

    @classmethod
    def verify_facebook_session(cls, account_name: str = "default") -> Tuple[bool, str]:
        ok = cls.is_facebook_authenticated(account_name)
        return (ok, "Sesi Facebook aktif" if ok else "Belum login Facebook")

    @staticmethod
    def open_tiktok_studio(account_name: str = "default", timeout_seconds: int = 7200) -> bool:
        """
        Opens TikTok Studio in a fully MAXIMIZED visible browser using the saved session state of the specified account.
        Keeps running until user closes the window. Automatically saves refreshed cookies upon closing.
        """
        AccountManager.create_or_get_account(account_name)
        state_file = get_account_state_file(account_name, "tiktok")
        is_auth = AuthManager.is_tiktok_authenticated(account_name)

        console.print(f"[bold yellow]=== MEMBUKA TIKTOK STUDIO MAXIMIZED (SESI AKUN) ===[/bold yellow]")
        console.print(f"Target Akun: [magenta]{account_name}[/magenta]")
        console.print(f"State File: [cyan]{state_file}[/cyan]")

        with sync_playwright() as p:
            browser = launch_browser(p, headless=False)
            safe_state = get_safe_storage_state(state_file) if is_auth else None
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                no_viewport=True,
                viewport=None,
                storage_state=safe_state
            )
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            page = context.new_page()
            
            target_url = "https://www.tiktok.com/tiktokstudio/upload" if is_auth else "https://www.tiktok.com/login"
            console.print(f"[cyan]Mengarahkan browser ke: {target_url}[/cyan]")
            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
            except Exception:
                pass

            try:
                page.bring_to_front()
            except Exception:
                pass

            console.print(f"[green]Browser TikTok Studio aktif untuk akun [{account_name}]. Tutup jendela jika sudah selesai.[/green]")
            start_time = time.time()
            last_save_time = time.time()

            while time.time() - start_time < timeout_seconds:
                try:
                    if page.is_closed() or not context.pages:
                        break
                    
                    # Gentle periodic save every 30s without executing scripts in page
                    if time.time() - last_save_time > 30:
                        AuthManager._save_storage_state_safe(context, state_file)
                        last_save_time = time.time()

                    page.wait_for_timeout(1000)
                except Exception:
                    break

            try:
                AuthManager._save_storage_state_safe(context, state_file)
                browser.close()
            except Exception:
                pass
            return True

    @staticmethod
    def open_instagram(account_name: str = "default", timeout_seconds: int = 7200) -> bool:
        """
        Opens Instagram in a fully MAXIMIZED visible browser using the saved session state of the specified account.
        Keeps running until user closes the window. Automatically saves refreshed cookies upon closing.
        """
        AccountManager.create_or_get_account(account_name)
        state_file = get_account_state_file(account_name, "instagram")
        is_auth = AuthManager.is_instagram_authenticated(account_name)

        console.print(f"[bold yellow]=== MEMBUKA INSTAGRAM MAXIMIZED (SESI AKUN) ===[/bold yellow]")
        console.print(f"Target Akun: [magenta]{account_name}[/magenta]")
        console.print(f"State File: [cyan]{state_file}[/cyan]")

        with sync_playwright() as p:
            browser = launch_browser(p, headless=False)
            safe_state = get_safe_storage_state(state_file) if is_auth else None
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                no_viewport=True,
                viewport=None,
                storage_state=safe_state
            )
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            page = context.new_page()
            
            target_url = "https://www.instagram.com/" if is_auth else "https://www.instagram.com/accounts/login/"
            console.print(f"[cyan]Mengarahkan browser ke: {target_url}[/cyan]")
            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
            except Exception:
                pass

            try:
                page.bring_to_front()
            except Exception:
                pass

            console.print(f"[green]Browser Instagram aktif untuk akun [{account_name}]. Tutup jendela jika sudah selesai.[/green]")
            start_time = time.time()
            last_save_time = time.time()

            while time.time() - start_time < timeout_seconds:
                try:
                    if page.is_closed() or not context.pages:
                        break
                    
                    # Gentle periodic save every 30s without executing scripts in page
                    if time.time() - last_save_time > 30:
                        try:
                            cookies = context.cookies()
                            has_session = any(c["name"] in ["sessionid", "ds_user_id"] for c in cookies)
                            if has_session:
                                context.storage_state(path=str(state_file))
                        except Exception:
                            pass
                        last_save_time = time.time()

                    page.wait_for_timeout(1000)
                except Exception:
                    break

            try:
                cookies = context.cookies()
                has_session = any(c["name"] in ["sessionid", "ds_user_id"] for c in cookies)
                if has_session:
                    context.storage_state(path=str(state_file))
                browser.close()
            except Exception:
                pass
            return True

    @staticmethod
    def open_facebook(account_name: str = "default", timeout_seconds: int = 7200) -> bool:
        """
        Opens Facebook in a fully MAXIMIZED visible browser using the saved session state of the specified account.
        Keeps running until user closes the window. Automatically saves refreshed cookies upon closing.
        """
        AccountManager.create_or_get_account(account_name)
        state_file = get_account_state_file(account_name, "facebook")
        is_auth = AuthManager.is_facebook_authenticated(account_name)

        console.print(f"[bold yellow]=== MEMBUKA FACEBOOK FANSPAGE MAXIMIZED (SESI AKUN) ===[/bold yellow]")
        console.print(f"Target Akun: [magenta]{account_name}[/magenta]")
        console.print(f"State File: [cyan]{state_file}[/cyan]")

        with sync_playwright() as p:
            browser = launch_browser(p, headless=False)
            safe_state = get_safe_storage_state(state_file) if is_auth else None
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                no_viewport=True,
                viewport=None,
                storage_state=safe_state
            )
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            page = context.new_page()
            
            target_url = "https://www.facebook.com/" if is_auth else "https://www.facebook.com/login"
            console.print(f"[cyan]Mengarahkan browser ke: {target_url}[/cyan]")
            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
                page.bring_to_front()
            except Exception:
                pass

            console.print(f"[green]Browser Facebook aktif untuk akun [{account_name}]. Tutup jendela jika sudah selesai.[/green]")
            start_time = time.time()
            last_save_time = time.time()

            while time.time() - start_time < timeout_seconds:
                try:
                    if page.is_closed() or not context.pages:
                        break
                    
                    if time.time() - last_save_time > 30:
                        try:
                            cookies = context.cookies()
                            has_session = any(c["name"] in ["c_user", "xs"] for c in cookies)
                            if has_session:
                                context.storage_state(path=str(state_file))
                        except Exception:
                            pass
                        last_save_time = time.time()

                    page.wait_for_timeout(1000)
                except Exception:
                    break

            try:
                cookies = context.cookies()
                has_session = any(c["name"] in ["c_user", "xs"] for c in cookies)
                if has_session:
                    context.storage_state(path=str(state_file))
                browser.close()
            except Exception:
                pass
            return True

    @staticmethod
    def login_facebook(account_name: str = "default", timeout_seconds: int = 600) -> bool:
        """
        Open a visible (headed) maximized Chromium browser for the user to log into Facebook manually.
        Automatically saves the session state once logged in.
        """
        AccountManager.create_or_get_account(account_name)
        state_file = get_account_state_file(account_name, "facebook")

        console.print(f"[bold yellow]=== MEMBUKA BROWSER VISUAL LOGIN FACEBOOK ===[/bold yellow]")
        console.print(f"Target Akun: [magenta]{account_name}[/magenta]")
        console.print("[cyan]Jendela browser sedang dibuka di layar Anda. Silakan login ke Facebook / Halaman Fanspage.[/cyan]")

        with sync_playwright() as p:
            browser = launch_browser(p, headless=False)
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                no_viewport=True,
                viewport=None,
                storage_state=str(state_file) if state_file.exists() else None
            )
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            page = context.new_page()
            try:
                page.goto("https://www.facebook.com/login", wait_until="domcontentloaded", timeout=45000)
                page.bring_to_front()
            except Exception:
                pass

            console.print(f"[green]Menunggu Anda login di browser (Batas waktu: {timeout_seconds} detik)...[/green]")
            start_time = time.time()
            logged_in = False

            while time.time() - start_time < timeout_seconds:
                try:
                    if page.is_closed():
                        break
                    cookies = context.cookies()
                    has_session = any(c["name"] in ["c_user", "xs"] for c in cookies)
                    current_url = page.url

                    if has_session and "login" not in current_url:
                        console.print(f"[bold green][OK] Login Facebook Berhasil Terdeteksi untuk [{account_name}]![/bold green]")
                        time.sleep(2)
                        context.storage_state(path=str(state_file))
                        console.print(f"[bold cyan]Sesi berhasil disimpan ke: {state_file}[/bold cyan]")
                        logged_in = True
                        break
                    time.sleep(1)
                except Exception:
                    break

            try:
                browser.close()
            except Exception:
                pass

            if not logged_in:
                console.print(f"[yellow]Browser ditutup atau waktu login selesai.[/yellow]")
            return logged_in

    @classmethod
    def refresh_tiktok_session(cls, account_name: str) -> Tuple[bool, str]:
        """
        Tests the saved session against TikTok Studio in a quick headless browser,
        captures the live server-refreshed cookies (msToken, odin_tt, etc.),
        updates tiktok_state.json safely, and fetches account profile info.
        """
        state_file = get_account_state_file(account_name, "tiktok")
        if not state_file.exists():
            return False, f"Berkas sesi TikTok untuk '{account_name}' belum ditemukan."

        try:
            with sync_playwright() as p:
                browser = launch_browser(p, headless=True)
                safe_state = get_safe_storage_state(state_file)
                context = browser.new_context(
                    user_agent=DEFAULT_USER_AGENT,
                    storage_state=safe_state,
                    no_viewport=True
                )
                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                page = context.new_page()
                try:
                    page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_timeout(3500)
                    
                    final_url = page.url
                    if "login" in final_url:
                        browser.close()
                        return False, "Sesi TikTok telah kedaluwarsa atau ditolak oleh server TikTok. Silakan perbarui cookie dari browser."

                    # Live session confirmed! Capture and save the fresh rotated cookies
                    cls._save_storage_state_safe(context, state_file)
                finally:
                    try:
                        browser.close()
                    except Exception:
                        pass

            # Trigger non-blocking profile update
            try:
                AccountManager.get_tiktok_profile(account_name, force_refresh=True)
            except Exception:
                pass

            return True, "Sesi TikTok aktif dan berhasil diperbarui!"
        except Exception as e:
            return False, f"Gagal memverifikasi sesi: {str(e)}"

    @classmethod
    def import_tiktok_sessionid(cls, account_name: str, session_data: str) -> Tuple[bool, str]:
        """
        Imports cookie data from multiple formats (JSON array from Cookie-Editor, Cookie Header string, Netscape, or single sessionid),
        synthesizes required security tokens, verifies the session live against TikTok Studio,
        and automatically persists the fresh refreshed state.
        """
        raw = (session_data or "").strip()
        if not raw:
            return False, "Data session cookie tidak boleh kosong."

        now_ts = int(time.time()) + 30 * 86400  # 30 days expiry
        cookies_map = {}

        # 1. Check if JSON format (Cookie-Editor, EditThisCookie, J2TEAM, StorageState JSON)
        is_json = False
        if (raw.startswith("[") and raw.endswith("]")) or (raw.startswith("{") and raw.endswith("}")):
            try:
                parsed_json = json.loads(raw)
                is_json = True
                if isinstance(parsed_json, dict):
                    if "cookies" in parsed_json and isinstance(parsed_json["cookies"], list):
                        parsed_json = parsed_json["cookies"]
                    else:
                        parsed_json = [{"name": k, "value": str(v)} for k, v in parsed_json.items()]
                if isinstance(parsed_json, list):
                    for item in parsed_json:
                        if isinstance(item, dict) and "name" in item and "value" in item:
                            c_name = str(item["name"]).strip()
                            c_val = str(item["value"]).strip()
                            if c_name and c_val:
                                domain = item.get("domain") or ".tiktok.com"
                                if not domain.startswith("."):
                                    domain = "." + domain
                                exp = item.get("expirationDate") or item.get("expires")
                                try:
                                    exp = int(float(exp)) if exp else now_ts
                                except Exception:
                                    exp = now_ts
                                cookies_map[c_name] = {
                                    "name": c_name,
                                    "value": c_val,
                                    "domain": domain,
                                    "path": item.get("path", "/"),
                                    "expires": exp,
                                    "httpOnly": item.get("httpOnly", c_name in ["sessionid", "sessionid_ss", "sid_tt", "sid_guard"]),
                                    "secure": item.get("secure", True),
                                    "sameSite": item.get("sameSite", "None") or "None"
                                }
            except Exception:
                is_json = False

        # 2. Check if Netscape HTTP Cookie file format
        if not cookies_map and "\t" in raw and not is_json:
            lines = raw.splitlines()
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) >= 7:
                    dom, _, path, sec, exp, name, val = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6]
                    try:
                        exp_ts = int(float(exp)) if exp else now_ts
                    except Exception:
                        exp_ts = now_ts
                    cookies_map[name.strip()] = {
                        "name": name.strip(),
                        "value": val.strip(),
                        "domain": dom.strip(),
                        "path": path.strip() or "/",
                        "expires": exp_ts,
                        "httpOnly": name in ["sessionid", "sessionid_ss", "sid_tt", "sid_guard"],
                        "secure": sec.lower() == "true",
                        "sameSite": "None"
                    }

        # 3. Check if Cookie Header string format (key=val; key2=val2 or multiline)
        if not cookies_map and (";" in raw or "=" in raw) and not is_json:
            clean_raw = raw.replace("\r\n", "; ").replace("\n", "; ")
            pairs = [p.strip() for p in clean_raw.split(";") if "=" in p]
            for pair in pairs:
                k, v = pair.split("=", 1)
                k = k.strip()
                v = v.strip()
                if k and v:
                    cookies_map[k] = {
                        "name": k,
                        "value": v,
                        "domain": ".tiktok.com",
                        "path": "/",
                        "expires": now_ts,
                        "httpOnly": k in ["sessionid", "sessionid_ss", "sid_tt", "sid_guard"],
                        "secure": True,
                        "sameSite": "None"
                    }

        # 4. Single sessionid token provided
        if not cookies_map and len(raw) > 5 and " " not in raw:
            session_val = raw
            for c_name in ["sessionid", "sessionid_ss", "sid_tt", "sid_guard"]:
                cookies_map[c_name] = {
                    "name": c_name,
                    "value": session_val,
                    "domain": ".tiktok.com",
                    "path": "/",
                    "expires": now_ts,
                    "httpOnly": True,
                    "secure": True,
                    "sameSite": "None"
                }

        if not cookies_map:
            return False, "Format cookie tidak dikenali. Silakan tempel Header String atau JSON Cookie-Editor."

        # Check if sessionid or sid_tt is present
        session_cookie = cookies_map.get("sessionid") or cookies_map.get("sessionid_ss") or cookies_map.get("sid_tt")
        if not session_cookie or len(session_cookie["value"]) < 8:
            return False, "Cookie 'sessionid' tidak ditemukan dalam data yang dimasukkan. Pastikan akun sudah login di browser sebelum menyalin cookie."

        session_val = session_cookie["value"]
        # Ensure companion essential cookies exist
        if "sessionid" not in cookies_map:
            cookies_map["sessionid"] = {**session_cookie, "name": "sessionid"}
        if "sessionid_ss" not in cookies_map:
            cookies_map["sessionid_ss"] = {**session_cookie, "name": "sessionid_ss"}
        if "sid_tt" not in cookies_map:
            cookies_map["sid_tt"] = {**session_cookie, "name": "sid_tt"}
        if "sid_guard" not in cookies_map:
            cookies_map["sid_guard"] = {**session_cookie, "name": "sid_guard"}

        # Region fallback
        if "store-idc" not in cookies_map:
            cookies_map["store-idc"] = {
                "name": "store-idc",
                "value": "alisg",
                "domain": ".tiktok.com",
                "path": "/",
                "expires": now_ts,
                "httpOnly": True,
                "secure": False,
                "sameSite": "None"
            }
        if "store-country-code" not in cookies_map:
            cookies_map["store-country-code"] = {
                "name": "store-country-code",
                "value": "id",
                "domain": ".tiktok.com",
                "path": "/",
                "expires": now_ts,
                "httpOnly": True,
                "secure": False,
                "sameSite": "None"
            }

        cookies_list = list(cookies_map.values())
        state_data = {
            "cookies": cookies_list,
            "origins": []
        }

        AccountManager.create_or_get_account(account_name)
        state_file = get_account_state_file(account_name, "tiktok")
        state_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2)

            # Trigger non-blocking background profile & avatar fetch
            import threading
            threading.Thread(target=AccountManager.get_tiktok_profile, args=(account_name, True), daemon=True).start()

            return True, f"Sesi TikTok untuk '{account_name}' berhasil disimpan dan terhubung aktif!"
        except Exception as e:
            return False, f"Gagal menyimpan sesi: {str(e)}"

    @classmethod
    def login_tiktok(cls, account_name: str = "default", timeout_seconds: int = 600) -> bool:
        """
        Open a visible (headed) maximized native Google Chrome browser for the user to log into TikTok.
        Uses persistent browser profile and full anti-automation bypass to ensure QR code scan,
        Google SSO, and Phone login work instantly without getting stuck.
        """
        AccountManager.create_or_get_account(account_name)
        state_file = get_account_state_file(account_name, "tiktok")
        acc_dir = get_account_dir(account_name)
        profile_dir = acc_dir / "tiktok_browser_profile"
        profile_dir.mkdir(parents=True, exist_ok=True)

        console.print(f"[bold yellow]=== MEMBUKA BROWSER VISUAL LOGIN TIKTOK ===[/bold yellow]")
        console.print(f"Target Akun: [magenta]{account_name}[/magenta]")
        console.print("[cyan]Jendela browser sedang dibuka di layar Anda. Silakan scan QR atau login dengan Google/Email/Nomor HP.[/cyan]")

        with sync_playwright() as p:
            try:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir),
                    channel="chrome",
                    headless=False,
                    user_agent=DEFAULT_USER_AGENT,
                    no_viewport=True,
                    viewport=None,
                    locale="id-ID",
                    timezone_id="Asia/Jakarta",
                    args=[
                        "--start-maximized",
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-infobars",
                        "--no-default-browser-check"
                    ],
                    ignore_default_args=["--enable-automation"]
                )
            except Exception:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir),
                    headless=False,
                    user_agent=DEFAULT_USER_AGENT,
                    no_viewport=True,
                    viewport=None,
                    locale="id-ID",
                    timezone_id="Asia/Jakarta",
                    args=[
                        "--start-maximized",
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox"
                    ],
                    ignore_default_args=["--enable-automation"]
                )

            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['id-ID', 'id', 'en-US', 'en']
                });
            """)

            page = context.pages[0] if context.pages else context.new_page()
            try:
                page.goto("https://www.tiktok.com/login", wait_until="domcontentloaded", timeout=45000)
                page.bring_to_front()
            except Exception:
                pass

            console.print(f"[green]Menunggu Anda login di browser (Batas waktu: {timeout_seconds} detik)...[/green]")
            start_time = time.time()
            logged_in = False

            while time.time() - start_time < timeout_seconds:
                try:
                    active_pages = [pg for pg in context.pages if not pg.is_closed()]
                    if not active_pages:
                        break
                    
                    cookies = context.cookies()
                    has_session = any(c["name"] in ["sessionid", "sessionid_ss", "sid_tt", "passport_auth_status", "uid_tt", "sid_guard"] for c in cookies)

                    if has_session:
                        console.print(f"[bold green][OK] Login TikTok Berhasil Terdeteksi untuk [{account_name}]![/bold green]")
                        time.sleep(2)
                        context.storage_state(path=str(state_file))
                        console.print(f"[bold cyan]Sesi berhasil disimpan ke: {state_file}[/bold cyan]")
                        try:
                            AccountManager.get_tiktok_profile(account_name, force_refresh=True)
                        except Exception:
                            pass
                        logged_in = True
                        break
                    time.sleep(1)
                except Exception:
                    break

            try:
                cookies = context.cookies()
                if has_session:
                    context.storage_state(path=str(state_file))
                    try:
                        AccountManager.get_tiktok_profile(account_name, force_refresh=True)
                    except Exception:
                        pass
                    logged_in = True
                context.close()
            except Exception:
                pass

            if not logged_in:
                console.print(f"[yellow]Browser ditutup atau waktu login selesai.[/yellow]")
            return logged_in

    @staticmethod
    def login_instagram(account_name: str = "default", timeout_seconds: int = 600) -> bool:
        """
        Open a visible (headed) maximized Chromium browser for the user to log into Instagram manually.
        Automatically saves the session state once logged in.
        """
        AccountManager.create_or_get_account(account_name)
        state_file = get_account_state_file(account_name, "instagram")

        console.print(f"[bold yellow]=== MEMBUKA BROWSER VISUAL LOGIN INSTAGRAM ===[/bold yellow]")
        console.print(f"Target Akun: [magenta]{account_name}[/magenta]")
        console.print("[cyan]Jendela browser sedang dibuka di layar Anda. Silakan login ke Instagram.[/cyan]")

        with sync_playwright() as p:
            browser = launch_browser(p, headless=False)
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                no_viewport=True,
                viewport=None,
                storage_state=str(state_file) if state_file.exists() else None
            )
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            page = context.new_page()
            try:
                page.goto(INSTAGRAM_LOGIN_URL, wait_until="domcontentloaded", timeout=45000)
                page.bring_to_front()
            except Exception:
                pass

            console.print(f"[green]Menunggu Anda login di browser (Batas waktu: {timeout_seconds} detik)...[/green]")
            start_time = time.time()
            logged_in = False

            while time.time() - start_time < timeout_seconds:
                try:
                    if page.is_closed():
                        break
                    cookies = context.cookies()
                    has_session = any(c["name"] in ["sessionid", "ds_user_id"] for c in cookies)
                    current_url = page.url

                    if has_session and "accounts/login" not in current_url:
                        console.print(f"[bold green][OK] Login Instagram Berhasil Terdeteksi untuk [{account_name}]![/bold green]")
                        time.sleep(1.5)
                        context.storage_state(path=str(state_file))
                        console.print(f"[bold cyan]Sesi berhasil disimpan ke: {state_file}[/bold cyan]")
                        logged_in = True
                        break
                    time.sleep(1)
                except Exception:
                    break

            try:
                browser.close()
            except Exception:
                pass

            if not logged_in:
                console.print(f"[yellow]Browser ditutup atau waktu login selesai.[/yellow]")
            return logged_in

    @staticmethod
    def open_meta_business(account_name: str = "default", timeout_seconds: int = 7200) -> bool:
        """
        Opens Meta Business Suite in a fully MAXIMIZED visible browser using the saved session state of the specified account.
        Keeps running until user closes the window. Automatically saves refreshed cookies upon closing.
        """
        AccountManager.create_or_get_account(account_name)
        state_file = get_account_state_file(account_name, "meta")
        is_auth = AuthManager.is_meta_authenticated(account_name)

        console.print(f"[bold yellow]=== MEMBUKA META BUSINESS SUITE MAXIMIZED (SESI AKUN) ===[/bold yellow]")
        console.print(f"Target Akun: [magenta]{account_name}[/magenta]")
        console.print(f"State File: [cyan]{state_file}[/cyan]")

        with sync_playwright() as p:
            browser = launch_browser(p, headless=False)
            safe_state = get_safe_storage_state(state_file) if is_auth else None
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                no_viewport=True,
                viewport=None,
                storage_state=safe_state
            )
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            page = context.new_page()
            
            target_url = META_BUSINESS_HOME_URL if is_auth else META_BUSINESS_LOGIN_URL
            console.print(f"[cyan]Mengarahkan browser ke: {target_url}[/cyan]")
            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
            except Exception:
                pass

            try:
                page.bring_to_front()
            except Exception:
                pass

            console.print(f"[green]Browser Meta Business Suite aktif untuk akun [{account_name}]. Tutup jendela jika sudah selesai.[/green]")
            start_time = time.time()
            last_save_time = time.time()

            while time.time() - start_time < timeout_seconds:
                try:
                    if page.is_closed() or not context.pages:
                        break
                    
                    if time.time() - last_save_time > 30:
                        try:
                            cookies = context.cookies()
                            has_session = any(c["name"] in ["c_user", "xs", "sessionid", "ds_user_id"] for c in cookies)
                            if has_session:
                                context.storage_state(path=str(state_file))
                        except Exception:
                            pass
                        last_save_time = time.time()

                    page.wait_for_timeout(1000)
                except Exception:
                    break

            try:
                cookies = context.cookies()
                has_session = any(c["name"] in ["c_user", "xs", "sessionid", "ds_user_id"] for c in cookies)
                if has_session:
                    context.storage_state(path=str(state_file))
                browser.close()
            except Exception:
                pass
            return True

    @staticmethod
    def login_meta(account_name: str = "default", timeout_seconds: int = 600) -> bool:
        """
        Open a visible (headed) maximized Chromium browser for the user to log into Meta Business Suite.
        Supports logging in via Instagram or Facebook account.
        Automatically saves the session state once logged in.
        """
        AccountManager.create_or_get_account(account_name)
        state_file = get_account_state_file(account_name, "meta")

        console.print(f"[bold yellow]=== MEMBUKA BROWSER VISUAL LOGIN META BUSINESS SUITE ===[/bold yellow]")
        console.print(f"Target Akun: [magenta]{account_name}[/magenta]")
        console.print("[cyan]Silakan login menggunakan akun Instagram atau Facebook Anda di jendela browser yang terbuka.[/cyan]")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ]
            )
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                no_viewport=True,
                viewport=None,
                storage_state=str(state_file) if state_file.exists() else None
            )
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            page = context.new_page()
            try:
                page.goto(META_BUSINESS_LOGIN_URL, wait_until="domcontentloaded", timeout=45000)
                page.bring_to_front()
            except Exception:
                pass

            console.print(f"[green]Menunggu Anda login di browser (Batas waktu: {timeout_seconds} detik)...[/green]")
            start_time = time.time()
            logged_in = False

            while time.time() - start_time < timeout_seconds:
                try:
                    if page.is_closed():
                        break
                    cookies = context.cookies()
                    has_session = any(c["name"] in ["c_user", "xs", "sessionid", "ds_user_id"] for c in cookies)
                    current_url = page.url

                    if has_session and ("login" not in current_url or "business.facebook.com/latest" in current_url):
                        console.print(f"[bold green][OK] Login Meta Business Suite Berhasil Terdeteksi untuk [{account_name}]![/bold green]")
                        time.sleep(2)
                        context.storage_state(path=str(state_file))
                        console.print(f"[bold cyan]Sesi berhasil disimpan ke: {state_file}[/bold cyan]")
                        logged_in = True
                        break
                    time.sleep(1)
                except Exception:
                    break

            try:
                browser.close()
            except Exception:
                pass

            if not logged_in:
                console.print(f"[yellow]Browser ditutup atau waktu login selesai.[/yellow]")
            return logged_in

    @staticmethod
    def verify_tiktok_session(account_name: str = "default", headless: bool = True) -> Tuple[bool, str]:
        state_file = get_account_state_file(account_name, "tiktok")
        if not state_file.exists():
            return False, f"Session state belum ada untuk akun '{account_name}'. Jalankan login terlebih dahulu."
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=headless,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                )
                safe_state = get_safe_storage_state(state_file)
                context = browser.new_context(
                    user_agent=DEFAULT_USER_AGENT,
                    viewport=VIEWPORT,
                    storage_state=safe_state
                )
                page = context.new_page()
                page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)

                if "login" in page.url:
                    browser.close()
                    return False, f"Session TikTok untuk '{account_name}' belum valid / expired. Perlu login ulang."
                
                is_upload_page = page.locator("iframe, input[type='file'], div[data-tt='upload_btn']").count() > 0 or "creator-center" in page.url or "tiktokstudio" in page.url
                browser.close()
                if is_upload_page:
                    return True, f"Session TikTok akun '{account_name}' AKTIF dan siap upload!"
                return False, f"Tidak dapat memverifikasi halaman upload TikTok akun '{account_name}'."
        except Exception as e:
            return False, f"Gagal verifikasi session TikTok: {str(e)}"

    @staticmethod
    def verify_instagram_session(account_name: str = "default") -> Tuple[bool, str]:
        """Checks if instagram session cookies or mobile session exist and are valid."""
        if AuthManager.is_instagram_authenticated(account_name) or AuthManager.is_instagram_mobile_authenticated(account_name):
            return True, f"Session Instagram akun '{account_name}' AKTIF!"
        return False, f"Session Instagram akun '{account_name}' belum login / belum ada."

    @staticmethod
    def is_instagram_mobile_authenticated(account_name: str = "default") -> bool:
        """Checks if an authenticated instagrapi session exists."""
        acc_dir = get_account_dir(account_name)
        session_file = acc_dir / "instagrapi_session.json"
        if session_file.exists():
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return bool(data.get("authorization_data", {}).get("ds_user_id")) or bool(data.get("user_id"))
            except Exception:
                pass
        return False

    @staticmethod
    def login_instagram_mobile(
        account_name: str = "default",
        username: Optional[str] = None,
        password: Optional[str] = None,
        verification_code: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Logs in via instagrapi (Instagram Android Mobile App Protocol) and saves instagrapi_session.json.
        """
        try:
            from instagrapi import Client
            from instagrapi.exceptions import TwoFactorRequired, ChallengeRequired, BadPassword
        except ImportError:
            return False, "Library instagrapi belum terpasang. Jalankan 'pip install instagrapi'."

        acc_dir = get_account_dir(account_name)
        session_file = acc_dir / "instagrapi_session.json"

        cl = Client()
        cl.set_user_agent(
            "Instagram 319.0.0.38.107 Android (33/13; 480dpi; 1080x2400; Samsung; SM-G998B; o1s; exynos2100; in_ID; 576404987)"
        )

        if not username:
            import getpass
            console.print(Panel(f"[bold green]LOGIN INSTAGRAM MOBILE API (Android Protocol)[/bold green]\nAkun Target: [cyan]{account_name}[/cyan]"))
            username = input("Masukkan Username/Email Instagram: ").strip()
            password = getpass.getpass("Masukkan Password Instagram: ").strip()

        try:
            console.print(f"[cyan]Menghubungi server Instagram Mobile untuk @{username}...[/cyan]")
            cl.login(username, password, verification_code=verification_code or "")
            cl.dump_settings(session_file)
            console.print(f"[bold green][OK] Berhasil Login Instagram Mobile untuk @{username}![/bold green]")
            console.print(f"Sesi tersimpan di: {session_file}")
            return True, f"Berhasil login Instagram Mobile untuk @{username}"
        except TwoFactorRequired:
            if verification_code:
                try:
                    cl.two_factor_login(verification_code)
                    cl.dump_settings(session_file)
                    console.print(f"[bold green][OK] Berhasil Login 2FA Instagram Mobile![/bold green]")
                    return True, "Berhasil login 2FA Instagram Mobile"
                except Exception as e:
                    return False, f"Gagal 2FA: {str(e)}"
            
            # Interactive CLI prompt fallback
            import sys
            if sys.stdin.isatty():
                code = input("Masukkan Kode 2FA (SMS / Authenticator): ").strip()
                try:
                    cl.two_factor_login(code)
                    cl.dump_settings(session_file)
                    console.print(f"[bold green][OK] Berhasil Login 2FA Instagram Mobile![/bold green]")
                    return True, "Berhasil login 2FA Instagram Mobile"
                except Exception as e:
                    return False, f"Gagal 2FA: {str(e)}"
            return False, "2FA_REQUIRED: Akun mengaktifkan 2FA. Silakan masukkan kode verifikasi 2FA."
        except ChallengeRequired as e:
            console.print(f"[yellow]Instagram meminta verifikasi tambahan (Challenge Required): {e}[/yellow]")
            return False, f"Verifikasi tambahan diperlukan oleh Instagram: {str(e)}"
        except BadPassword:
            return False, "Password Instagram salah."
        except Exception as e:
            return False, f"Gagal login Instagram Mobile: {str(e)}"
