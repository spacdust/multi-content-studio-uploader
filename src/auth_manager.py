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
                    return any(c.get("name") in ["sessionid", "sessionid_ss", "sid_tt"] for c in cookies)
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
                storage_state=str(state_file) if state_file.exists() else None
            )
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
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
                    has_session = any(c["name"] in ["sessionid", "sessionid_ss", "sid_tt"] for c in cookies)
                    current_url = page.url

                    if has_session and ("login" not in current_url or "creator-center" in current_url or "tiktokstudio" in current_url):
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
        """Checks if instagram session cookies exist and are valid."""
        if AuthManager.is_instagram_authenticated(account_name):
            return True, f"Session Instagram akun '{account_name}' AKTIF!"
        return False, f"Session Instagram akun '{account_name}' belum login / belum ada."

    @staticmethod
    def verify_meta_session(account_name: str = "default") -> Tuple[bool, str]:
        """Checks if Meta Business Suite session cookies exist and are valid."""
        if AuthManager.is_meta_authenticated(account_name):
            return True, f"Session Meta Business Suite akun '{account_name}' AKTIF (Siap Cross-Post IG & FB)!"
        return False, f"Session Meta Business Suite akun '{account_name}' belum login / belum ada."
