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
    VIEWPORT
)
from src.account_manager import AccountManager

console = Console(highlight=False)

class AuthManager:
    """Manages interactive non-headless visual login and persistent sessions per account."""

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
                storage_state=str(state_file) if is_auth and state_file.exists() else None
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
                    active_pages = [pg for pg in context.pages if not pg.is_closed()]
                    if not active_pages:
                        break
                    
                    # Gentle periodic save every 30s without executing scripts in page
                    if time.time() - last_save_time > 30:
                        try:
                            cookies = context.cookies()
                            has_session = any(c["name"] in ["sessionid", "sessionid_ss", "sid_tt"] for c in cookies)
                            if has_session:
                                context.storage_state(path=str(state_file))
                        except Exception:
                            pass
                        last_save_time = time.time()

                    time.sleep(1)
                except Exception:
                    break

            try:
                cookies = context.cookies()
                has_session = any(c["name"] in ["sessionid", "sessionid_ss", "sid_tt"] for c in cookies)
                if has_session:
                    context.storage_state(path=str(state_file))
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
                storage_state=str(state_file) if is_auth and state_file.exists() else None
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
                    active_pages = [pg for pg in context.pages if not pg.is_closed()]
                    if not active_pages:
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

                    time.sleep(1)
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
                storage_state=str(state_file) if is_auth and state_file.exists() else None
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
                    active_pages = [pg for pg in context.pages if not pg.is_closed()]
                    if not active_pages:
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

                    time.sleep(1)
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
                        console.print(f"[bold green]✓ Login Facebook Berhasil Terdeteksi untuk [{account_name}]![/bold green]")
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
    def login_tiktok(account_name: str = "default", timeout_seconds: int = 600) -> bool:
        """
        Open a visible (headed) maximized Chromium browser for the user to log into TikTok manually.
        Automatically saves the session state once logged in.
        """
        AccountManager.create_or_get_account(account_name)
        state_file = get_account_state_file(account_name, "tiktok")

        console.print(f"[bold yellow]=== MEMBUKA BROWSER VISUAL LOGIN TIKTOK ===[/bold yellow]")
        console.print(f"Target Akun: [magenta]{account_name}[/magenta]")
        console.print("[cyan]Jendela browser sedang dibuka di layar Anda. Silakan login ke TikTok.[/cyan]")

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
                locale="id-ID",
                timezone_id="Asia/Jakarta"
            )
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['id-ID', 'id', 'en-US', 'en']
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """)
            page = context.new_page()
            try:
                page.goto(TIKTOK_LOGIN_URL, wait_until="domcontentloaded", timeout=45000)
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
                    has_session = any(c["name"] in ["sessionid", "sessionid_ss", "sid_tt", "passport_auth_status", "uid_tt", "sid_guard"] for c in cookies)

                    if has_session:
                        console.print(f"[bold green]✓ Login TikTok Berhasil Terdeteksi untuk [{account_name}]![/bold green]")
                        time.sleep(1.5)
                        context.storage_state(path=str(state_file))
                        console.print(f"[bold cyan]Sesi berhasil disimpan ke: {state_file}[/bold cyan]")
                        logged_in = True
                        break
                    time.sleep(1)
                except Exception:
                    break

            try:
                cookies = context.cookies()
                has_session = any(c["name"] in ["sessionid", "sessionid_ss", "sid_tt", "passport_auth_status", "uid_tt", "sid_guard"] for c in cookies)
                if has_session:
                    context.storage_state(path=str(state_file))
                    logged_in = True
                browser.close()
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
                        console.print(f"[bold green]✓ Login Instagram Berhasil Terdeteksi untuk [{account_name}]![/bold green]")
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
                storage_state=str(state_file) if is_auth and state_file.exists() else None
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
                    active_pages = [pg for pg in context.pages if not pg.is_closed()]
                    if not active_pages:
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

                    time.sleep(1)
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
                        console.print(f"[bold green]✓ Login Meta Business Suite Berhasil Terdeteksi untuk [{account_name}]![/bold green]")
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
                context = browser.new_context(
                    user_agent=DEFAULT_USER_AGENT,
                    viewport=VIEWPORT,
                    storage_state=str(state_file)
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
            console.print(f"[bold green]✓ Berhasil Login Instagram Mobile untuk @{username}![/bold green]")
            console.print(f"Sesi tersimpan di: {session_file}")
            return True, f"Berhasil login Instagram Mobile untuk @{username}"
        except TwoFactorRequired:
            if verification_code:
                try:
                    cl.two_factor_login(verification_code)
                    cl.dump_settings(session_file)
                    console.print(f"[bold green]✓ Berhasil Login 2FA Instagram Mobile![/bold green]")
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
                    console.print(f"[bold green]✓ Berhasil Login 2FA Instagram Mobile![/bold green]")
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
