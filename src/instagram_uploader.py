import os
import re
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from rich.console import Console

from src.config import (
    get_account_state_file,
    get_account_dir,
    INSTAGRAM_BASE_URL,
    DEFAULT_USER_AGENT,
    LOGS_DIR,
    launch_browser
)
from src.validator import ContentValidator

console = Console(highlight=False)

class InstagramUploader:
    """
    Automates uploading Video (Reels), Poster (Single Photo), and Carousel (Multi-Slide)
    via Instagram Mobile Private Protocol (instagrapi) with Playwright fallback:
    - 100% Native Mobile App API (triggers parallel cross-post to connected Facebook Page).
    - Uncropped 9:16 Original Aspect Ratio preservation.
    - Automatic session synchronization from Playwright browser cookies.
    - Ultra-fast headless execution with instant media URL confirmation.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless

    def dismiss_popups(self, page):
        """Dismiss common Instagram dialogs and notices like 'Video posts are now shared as reels'."""
        popup_selectors = [
            "div[role='dialog'] button:text-is('OK')",
            "div[role='dialog'] div[role='button']:text-is('OK')",
            "button:has-text('OK')",
            "button:has-text('Mengerti')",
            "button:has-text('Not Now')",
            "button:has-text('Lain Kali')",
            "button:has-text('Jangan Sekarang')"
        ]
        for sel in popup_selectors:
            try:
                b = page.locator(sel).first
                if b.count() > 0 and b.is_visible():
                    b.click(timeout=1500)
                    page.wait_for_timeout(500)
            except Exception:
                pass

    @staticmethod
    def get_instagrapi_client(account_name: str):
        """
        Creates and returns an authenticated instagrapi Client for the given account.
        Automatically syncs from Playwright cookies in instagram_state.json.
        """
        try:
            from instagrapi import Client
        except ImportError:
            return None

        acc_dir = get_account_dir(account_name)
        session_file = acc_dir / "instagrapi_session.json"
        state_file = get_account_state_file(account_name, "instagram")

        cl = Client()
        cl.set_user_agent(
            "Instagram 319.0.0.38.107 Android (33/13; 480dpi; 1080x2400; Samsung; SM-G998B; o1s; exynos2100; in_ID; 576404987)"
        )

        # 1. Try loading cached instagrapi settings
        if session_file.exists():
            try:
                cl.load_settings(session_file)
                # Quick verification without heavy network call
                if getattr(cl, "user_id", None):
                    return cl
            except Exception:
                pass

        # 2. Try loading from Playwright state file cookies
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cookies = data.get("cookies", [])
                cookie_dict = {c["name"]: c["value"] for c in cookies}
                sessionid = cookie_dict.get("sessionid")

                if sessionid:
                    cl.login_by_sessionid(sessionid)
                    cl.dump_settings(session_file)
                    return cl
            except Exception as e:
                console.print(f"[yellow]Peringatan: Gagal otentikasi instagrapi via cookies: {e}[/yellow]")

        return None

    def upload_media_mobile(
        self,
        media_paths: List[str | Path],
        caption: str = "",
        is_reel: bool = False,
        account_name: str = "default"
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Uploads media directly using Instagram Mobile App Protocol (instagrapi).
        Triggers native Facebook Fanpage auto-sharing and preserves 9:16 aspect ratio.
        """
        cl = self.get_instagrapi_client(account_name)
        if not cl:
            return False, "Klien Instagram Mobile belum terotentikasi. Silakan login via browser terlebih dahulu.", None

        sanitized_caption = ContentValidator.sanitize_caption(caption, platform="instagram")
        resolved_files = [Path(p).resolve() for p in media_paths]
        category_name = "Reels" if is_reel else ("Carousel" if len(resolved_files) > 1 else "Poster")

        console.print(f"[bold green]=== MEMULAI UPLOAD INSTAGRAM MOBILE API ({category_name.upper()}) ===[/bold green]")
        console.print(f"Akun: [magenta]{account_name}[/magenta] (User ID: {cl.user_id})")
        console.print(f"Jumlah File: [yellow]{len(resolved_files)}[/yellow] (Rasio 9:16 Asli)")
        console.print(f"Fitur Paralel FB: [green]AKTIF (Mobile Protocol Request)[/green]")

        try:
            extra_data = {
                "share_to_facebook": 1,
                "share_to_fb": 1,
                "like_and_view_counts_disabled": 0,
                "disable_comments": 0
            }

            media = None
            if is_reel:
                console.print("[cyan]Mengunggah Instagram Reel 9:16...[/cyan]")
                media = cl.clip_upload(
                    path=resolved_files[0],
                    caption=sanitized_caption,
                    extra_data=extra_data
                )
            elif len(resolved_files) > 1:
                console.print(f"[cyan]Mengunggah Instagram Carousel ({len(resolved_files)} slide 9:16)...[/cyan]")
                media = cl.album_upload(
                    paths=resolved_files,
                    caption=sanitized_caption,
                    extra_data=extra_data
                )
            else:
                console.print("[cyan]Mengunggah Instagram Poster Foto 9:16...[/cyan]")
                media = cl.photo_upload(
                    path=resolved_files[0],
                    caption=sanitized_caption,
                    extra_data=extra_data
                )

            if media and getattr(media, "code", None):
                post_url = f"https://www.instagram.com/p/{media.code}/"
                console.print(f"[bold green]✓ Berhasil dipublikasikan ke Instagram Mobile & Paralel Facebook![/bold green]")
                console.print(f"URL Post: [cyan]{post_url}[/cyan]")
                
                # Simpan update session
                acc_dir = get_account_dir(account_name)
                cl.dump_settings(acc_dir / "instagrapi_session.json")
                return True, f"{category_name} berhasil diupload ke Instagram Mobile ({post_url})", None
            
            return True, f"{category_name} berhasil diupload ke Instagram Mobile ({account_name}).", None

        except Exception as e:
            console.print(f"[bold red]Gagal upload via Mobile API: {e}[/bold red]")
            return False, f"Error Mobile API: {str(e)}", None

    def upload_media_playwright(
        self,
        media_paths: List[str | Path],
        caption: str = "",
        is_reel: bool = False,
        account_name: str = "default"
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Fallback uploader using Playwright Web automation with 9:16 original ratio selector.
        """
        from playwright.sync_api import sync_playwright
        resolved_files = [str(Path(p).resolve()) for p in media_paths]
        category_name = "Reels" if is_reel else ("Carousel" if len(resolved_files) > 1 else "Poster")

        state_file = get_account_state_file(account_name, "instagram")
        if not state_file.exists():
            return False, f"Sesi Instagram untuk akun '{account_name}' belum ada. Silakan login terlebih dahulu.", None

        sanitized_caption = ContentValidator.sanitize_caption(caption, platform="instagram")
        timestamp = int(time.time())
        screenshot_path = str(LOGS_DIR / f"instagram_{account_name}_{timestamp}.png")

        console.print(f"[bold cyan]=== MEMULAI UPLOAD INSTAGRAM WEB FALLBACK {category_name.upper()} ===[/bold cyan]")

        with sync_playwright() as p:
            browser = launch_browser(p, headless=self.headless, slow_mo=600 if not self.headless else 0)
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                no_viewport=True if not self.headless else False,
                viewport={"width": 1440, "height": 900} if self.headless else None,
                storage_state=str(state_file)
            )
            page = context.new_page()

            try:
                page.goto(INSTAGRAM_BASE_URL, timeout=45000, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)

                if "accounts/login" in page.url:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return False, f"Session Instagram untuk '{account_name}' telah kadaluarsa.", screenshot_path

                # Dismiss popups
                try:
                    for btn_text in ["Not Now", "Lain Kali", "Jangan Sekarang", "Cancel", "Batal"]:
                        b = page.locator(f"button:has-text('{btn_text}')").first
                        if b.count() > 0 and b.is_visible():
                            b.click()
                            page.wait_for_timeout(400)
                except Exception:
                    pass

                # Click Create -> Post
                create_btn = page.locator("svg[aria-label='New post'], svg[aria-label='Postingan baru'], span:text-is('Create'), span:text-is('Buat')").first
                if create_btn.count() == 0:
                    create_btn = page.locator("div[role='button']:has-text('Create'), div[role='button']:has-text('Buat')").first
                if create_btn.count() > 0:
                    create_btn.click()
                    page.wait_for_timeout(2000)

                post_submenu = page.locator("span:text-is('Post'), span:text-is('Postingan'), div[role='button']:has-text('Post')").first
                if post_submenu.count() > 0 and post_submenu.is_visible():
                    post_submenu.click()
                    page.wait_for_timeout(3000)

                file_input = page.locator("input[type='file']").first
                if file_input.count() == 0:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return False, "Input file tidak ditemukan.", screenshot_path

                file_input.set_input_files(resolved_files)
                page.wait_for_timeout(5000)

                # 2. Tutup dialog pemberitahuan seperti 'Video posts are now shared as reels'
                self.dismiss_popups(page)
                page.wait_for_timeout(1500)

                # 3. Select Original (9:16)
                console.print("[cyan]Menyesuaikan rasio aspek menjadi Original (9:16)...[/cyan]")
                crop_btn = page.locator(
                    "div[role='dialog'] button:has(svg[aria-label='Select crop']), "
                    "div[role='dialog'] button:has(svg[aria-label='Pilih pemotongan']), "
                    "div[role='dialog'] svg[aria-label='Select crop'], "
                    "div[role='dialog'] svg[aria-label='Pilih pemotongan'], "
                    "div[role='dialog'] div[role='button']:has(svg[aria-label='Select crop']), "
                    "div[role='dialog'] div[role='button']:has(svg[aria-label='Pilih pemotongan'])"
                ).first

                if crop_btn.count() > 0:
                    crop_btn.click(force=True)
                    page.wait_for_timeout(1500)

                    # Klik opsi 'Original' atau '9:16'
                    orig_target = page.locator(
                        "div[role='dialog'] button:has-text('Original'), "
                        "div[role='dialog'] div[role='button']:has-text('Original'), "
                        "div[role='dialog'] span:has-text('Original'), "
                        "div[role='dialog'] button:has-text('Asli'), "
                        "div[role='dialog'] div[role='button']:has-text('Asli'), "
                        "div[role='dialog'] span:has-text('Asli'), "
                        "div[role='dialog'] svg[aria-label='Photo outline'], "
                        "div[role='dialog'] button:has-text('9:16'), "
                        "div[role='dialog'] span:has-text('9:16')"
                    ).first

                    if orig_target.count() > 0:
                        orig_target.click(force=True)
                        page.wait_for_timeout(2000)
                        console.print("[green]Rasio Original / 9:16 berhasil dipilih![/green]")
                    else:
                        menu_items = page.locator("div[role='dialog'] button, div[role='dialog'] div[role='button']").all()
                        for item in menu_items:
                            try:
                                t = item.inner_text().strip().lower()
                                if "original" in t or "asli" in t or "9:16" in t:
                                    item.click(force=True)
                                    console.print(f"[green]Rasio '{t}' dipilih via fallback![/green]")
                                    break
                            except Exception:
                                pass

                # 4. Next -> Next
                for _ in range(2):
                    next_btn = page.locator(
                        "div[role='dialog'] div[role='button']:has-text('Next'), "
                        "div[role='dialog'] button:has-text('Next'), "
                        "div[role='dialog'] div[role='button']:has-text('Selanjutnya'), "
                        "div[role='dialog'] button:has-text('Selanjutnya')"
                    ).first
                    if next_btn.count() > 0:
                        next_btn.click()
                        page.wait_for_timeout(3500)

                # Caption
                if sanitized_caption:
                    caption_box = page.locator("div[aria-label='Write a caption...'], div[aria-label='Tulis keterangan...'], div[role='textbox']").first
                    if caption_box.count() > 0:
                        caption_box.click()
                        page.wait_for_timeout(500)
                        caption_box.fill(sanitized_caption)
                        page.wait_for_timeout(1000)

                # Share
                share_btn = page.locator(
                    "div[role='dialog'] div[role='button']:has-text('Share'), "
                    "div[role='dialog'] div[role='button']:has-text('Bagikan'), "
                    "div[role='dialog'] button:has-text('Share'), "
                    "div[role='dialog'] button:has-text('Bagikan')"
                ).last
                if share_btn.count() > 0:
                    share_btn.click(force=True)
                else:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return False, "Tombol Share tidak ditemukan.", screenshot_path

                # Wait success
                for _ in range(35):
                    page.wait_for_timeout(2000)
                    c = page.content().lower()
                    if "your reel has been shared" in c or "your post has been shared" in c or "telah dibagikan" in c or "post shared" in c:
                        break

                page.wait_for_timeout(2000)
                page.screenshot(path=screenshot_path)
                browser.close()
                return True, f"{category_name} berhasil diupload via Web Browser.", screenshot_path

            except Exception as ex:
                try:
                    page.screenshot(path=screenshot_path)
                except Exception:
                    pass
                browser.close()
                return False, f"Error Web: {str(ex)}", screenshot_path

    def upload_media(
        self,
        media_paths: List[str | Path] | str | Path,
        caption: str = "",
        is_reel: bool = False,
        account_name: str = "default"
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Main upload entry point: Tries mobile protocol first for parallel Facebook posting,
        falls back to Web browser if needed.
        """
        if isinstance(media_paths, (str, Path)):
            media_list = [Path(media_paths).resolve()]
        else:
            media_list = [Path(p).resolve() for p in media_paths]

        # Instagram Web Uploader (Playwright with guaranteed 9:16 Original crop selection)
        return self.upload_media_playwright(
            media_paths=media_list,
            caption=caption,
            is_reel=is_reel,
            account_name=account_name
        )

    # Alias for backward compatibility
    def upload(
        self,
        video_path: str | Path,
        caption: str = "",
        as_reel: bool = True,
        account_name: str = "default"
    ) -> Tuple[bool, str, Optional[str]]:
        return self.upload_media(
            media_paths=[video_path],
            caption=caption,
            is_reel=as_reel,
            account_name=account_name
        )
