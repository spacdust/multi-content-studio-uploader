import os
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from rich.console import Console
from playwright.sync_api import sync_playwright

from src.config import (
    get_account_state_file,
    DEFAULT_USER_AGENT,
    LOGS_DIR,
    launch_browser
)
from src.validator import ContentValidator

console = Console(highlight=False)

class FacebookUploader:
    """
    Automates uploading Video (Reels), Poster (Single Photo), and Multi-Photo Carousel
    directly to Facebook Fanpage (facebook.com) using the account's authenticated Facebook session.
    """

    def __init__(self, headless: bool = False):
        self.headless = headless

    def dismiss_popups(self, page):
        """Dismiss common Facebook popups and overlays."""
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass

        for sel in [
            "div[aria-label='Close']",
            "div[aria-label='Tutup']",
            "button:has-text('Not Now')",
            "button:has-text('Lain Kali')",
            "button:has-text('OK')"
        ]:
            try:
                b = page.locator(sel).first
                if b.count() > 0 and b.is_visible():
                    b.click(timeout=1000)
                    page.wait_for_timeout(400)
            except Exception:
                pass

    def upload_media(
        self,
        media_paths: List[str | Path] | str | Path,
        caption: str = "",
        is_reel: bool = False,
        account_name: str = "default"
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Uploads media directly to Facebook Fanpage.
        """
        if isinstance(media_paths, (str, Path)):
            media_list = [Path(media_paths).resolve()]
        else:
            media_list = [Path(p).resolve() for p in media_paths]

        if not media_list:
            return False, "Tidak ada file media yang diberikan untuk Facebook.", None

        state_file = get_account_state_file(account_name, "facebook")
        if not state_file.exists():
            return False, f"Sesi Facebook untuk akun '{account_name}' belum ada. Silakan login terlebih dahulu.", None

        resolved_files = [str(p) for p in media_list]
        category_name = "Reels" if is_reel else ("Carousel" if len(resolved_files) > 1 else "Poster")
        sanitized_caption = ContentValidator.sanitize_caption(caption, platform="facebook")
        timestamp = int(time.time())
        screenshot_path = str(LOGS_DIR / f"facebook_{account_name}_{timestamp}.png")

        mode_text = "HEADLESS" if self.headless else "VISIBLE BROWSER (FULL MAXIMIZED)"
        console.print(f"[bold cyan]=== MEMULAI UPLOAD FACEBOOK FANSPAGE {category_name.upper()} ({mode_text}) ===[/bold cyan]")
        console.print(f"Akun: [magenta]{account_name}[/magenta]")
        console.print(f"Jumlah File: [yellow]{len(resolved_files)}[/yellow]")

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
                if is_reel:
                    # 1. Buka Beranda Facebook
                    console.print("[cyan]1. Membuka Beranda Facebook...[/cyan]")
                    page.goto("https://www.facebook.com/", timeout=45000, wait_until="domcontentloaded")
                    page.wait_for_timeout(4000)

                    if "login" in page.url:
                        page.screenshot(path=screenshot_path)
                        browser.close()
                        return False, f"Session Facebook untuk '{account_name}' telah kadaluarsa.", screenshot_path

                    self.dismiss_popups(page)

                    # 2. Tekan ikon MERAH Reel di sebelah kanan 'Apa yang Anda pikirkan'
                    console.print("[cyan]2. Membuka dialog pembuatan Reel (ikon merah paling kanan)...[/cyan]")
                    photo_video_btn = page.locator(
                        "div[aria-label='Reel'], "
                        "div[aria-label='Buat Reel'], "
                        "div[aria-label='Reels'], "
                        "div[role='button']:has-text('Reel')"
                    ).first

                    if photo_video_btn.count() == 0:
                        photo_video_btn = page.locator("div[role='main'] div[aria-label='Reel']").first

                    if photo_video_btn.count() > 0:
                        photo_video_btn.click(force=True)
                        page.wait_for_timeout(2500)

                    # 3. Upload Video
                    console.print("[cyan]3. Menyuntikkan file video...[/cyan]")
                    file_input = page.locator("input[type='file']").first
                    if file_input.count() == 0:
                        page.screenshot(path=screenshot_path)
                        browser.close()
                        return False, "Input file video tidak ditemukan di Facebook.", screenshot_path

                    file_input.set_input_files([resolved_files[0]])
                    page.wait_for_timeout(5000)

                    # 4. Next Button 1 (Ke Edit reel)
                    console.print("[cyan]4. Melanjutkan ke Edit reel...[/cyan]")
                    next_btn1 = page.locator(
                        "div[role='dialog'] div[role='button']:has-text('Berikutnya'), "
                        "div[role='dialog'] div[aria-label='Berikutnya'], "
                        "div[role='button']:has-text('Berikutnya'), "
                        "div[aria-label='Berikutnya']"
                    ).last
                    if next_btn1.count() > 0:
                        next_btn1.click(force=True)
                        page.wait_for_timeout(3500)

                    # 5. Next Button 2 (Ke Pengaturan reel)
                    console.print("[cyan]5. Melanjutkan ke Pengaturan reel...[/cyan]")
                    next_btn2 = page.locator(
                        "div[role='dialog'] div[role='button']:has-text('Berikutnya'), "
                        "div[role='dialog'] div[aria-label='Berikutnya'], "
                        "div[role='button']:has-text('Berikutnya'), "
                        "div[aria-label='Berikutnya']"
                    ).last
                    if next_btn2.count() > 0:
                        next_btn2.click(force=True)
                        page.wait_for_timeout(3500)

                    # 6. Isi Caption di Pengaturan Reel
                    if sanitized_caption:
                        console.print("[cyan]6. Mengisi deskripsi caption Reel Facebook...[/cyan]")
                        desc_box = page.locator(
                            "div[role='main'] div[role='textbox'], "
                            "div[role='form'] div[role='textbox'], "
                            "div[role='main'] div[contenteditable='true'], "
                            "div[role='dialog'] div[role='textbox'], "
                            "div[data-lexical-editor='true']"
                        ).last
                        if desc_box.count() > 0:
                            desc_box.click(force=True)
                            page.wait_for_timeout(500)
                            page.keyboard.type(sanitized_caption)
                            page.wait_for_timeout(1000)

                    # 7. Publish / Kirim
                    console.print("[bold green]7. Mempublikasikan Reel ke Halaman Facebook...[/bold green]")
                    publish_btn = page.locator(
                        "div[role='button']:has-text('Kirim'), div[aria-label='Kirim'], "
                        "div[role='button']:has-text('Posting'), div[aria-label='Posting'], "
                        "div[role='button']:has-text('Terbitkan'), div[aria-label='Terbitkan'], "
                        "div[role='button']:has-text('Publish'), div[aria-label='Publish']"
                    ).last
                    if publish_btn.count() > 0:
                        publish_btn.click(force=True)
                    else:
                        page.screenshot(path=screenshot_path)
                        browser.close()
                        return False, "Tombol Kirim/Posting Reel Facebook tidak ditemukan.", screenshot_path

                    # 8. Tunggu konfirmasi
                    page.wait_for_timeout(10000)
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return True, f"Facebook Reel berhasil diposting untuk '{account_name}'.", screenshot_path

                else:
                    # 1. Buka Beranda Facebook
                    console.print("[cyan]1. Membuka Facebook Feed...[/cyan]")
                    page.goto("https://www.facebook.com/", timeout=45000, wait_until="domcontentloaded")
                    page.wait_for_timeout(5000)

                    if "login" in page.url:
                        page.screenshot(path=screenshot_path)
                        browser.close()
                        return False, f"Session Facebook untuk '{account_name}' telah kadaluarsa.", screenshot_path

                    self.dismiss_popups(page)

                    # 2. Tekan ikon HIJAU Foto/video sebelah kanan 'Apa yang Anda pikirkan'
                    console.print("[cyan]2. Membuka dialog postingan foto (ikon hijau Foto/video)...[/cyan]")
                    create_post_btn = page.locator(
                        "div[aria-label='Foto/video'], "
                        "div[role='button']:has-text('Foto/video'), "
                        "div[role='button']:has-text('Photo/video'), "
                        "span:has-text('Apa yang Anda pikirkan'), "
                        "span:has-text('What\\'s on your mind')"
                    ).first
                    if create_post_btn.count() > 0:
                        create_post_btn.click(force=True)
                        page.wait_for_timeout(2500)

                    # 3. Input Files
                    console.print(f"[cyan]3. Menyuntikkan {len(resolved_files)} file media...[/cyan]")
                    file_input = page.locator("input[type='file']").first
                    if file_input.count() > 0:
                        file_input.set_input_files(resolved_files)
                        page.wait_for_timeout(4000)

                    # 4. Isi Caption langsung di awal tepat di atas gambar
                    if sanitized_caption:
                        console.print("[cyan]4. Mengisi teks caption di awal di atas gambar...[/cyan]")
                        caption_box = page.locator(
                            "div[role='dialog'] span:has-text('Apa yang Anda pikirkan'), "
                            "div[role='dialog'] div:has-text('Apa yang Anda pikirkan'), "
                            "div[role='dialog'] div[contenteditable='true'], "
                            "div[role='dialog'] div[data-lexical-editor='true'], "
                            "div[role='dialog'] div[role='textbox']"
                        ).last
                        if caption_box.count() > 0:
                            caption_box.click(force=True)
                            page.wait_for_timeout(500)
                            page.keyboard.type(sanitized_caption)
                            page.wait_for_timeout(1500)

                    # 5. Klik Berikutnya
                    console.print("[cyan]5. Melanjutkan ke Pengaturan postingan (Berikutnya)...[/cyan]")
                    next_post_btn = page.locator(
                        "div[role='dialog'] div[role='button']:has-text('Berikutnya'), "
                        "div[role='dialog'] div[aria-label='Berikutnya'], "
                        "div[role='dialog'] div[role='button']:has-text('Next'), "
                        "div[role='dialog'] div[aria-label='Next'], "
                        "div[role='button']:has-text('Berikutnya')"
                    ).last
                    if next_post_btn.count() > 0 and next_post_btn.is_visible():
                        next_post_btn.click(force=True)
                        page.wait_for_timeout(3500)

                    # 6. Klik Kirim / Posting
                    console.print("[bold green]6. Mempublikasikan ke Halaman Facebook...[/bold green]")
                    post_btn = page.locator(
                        "div[role='dialog'] div[role='button']:has-text('Kirim'), "
                        "div[role='dialog'] div[aria-label='Kirim'], "
                        "div[role='dialog'] div[role='button']:has-text('Posting'), "
                        "div[role='dialog'] div[aria-label='Posting'], "
                        "div[role='dialog'] div[role='button']:has-text('Post'), "
                        "div[role='dialog'] div[aria-label='Post'], "
                        "div[role='button']:has-text('Kirim'), "
                        "div[role='button']:has-text('Posting')"
                    ).last
                    if post_btn.count() > 0:
                        post_btn.click(force=True)
                    else:
                        page.screenshot(path=screenshot_path)
                        browser.close()
                        return False, "Tombol Posting Facebook tidak ditemukan.", screenshot_path

                    page.wait_for_timeout(10000)
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return True, f"{category_name} berhasil diposting ke Facebook ({account_name}).", screenshot_path

            except Exception as ex:
                try:
                    page.screenshot(path=screenshot_path)
                except Exception:
                    pass
                browser.close()
                return False, f"Terjadi kesalahan upload Facebook: {str(ex)}", screenshot_path

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
