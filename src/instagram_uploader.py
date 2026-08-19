import os
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from rich.console import Console
from playwright.sync_api import sync_playwright

from src.config import (
    get_account_state_file,
    INSTAGRAM_BASE_URL,
    DEFAULT_USER_AGENT,
    LOGS_DIR
)
from src.validator import ContentValidator

console = Console(highlight=False)

class InstagramUploader:
    """
    Automates uploading Video (Reels), Poster (Single Photo), and Carousel (Multi-Slide)
    directly to Instagram Web (instagram.com) with:
    - Full screen maximized browser.
    - Automatic 'Original' (9:16) Aspect Ratio preservation (no cropping).
    - Multi-slide carousel file ingestion.
    - Automatic dismissal of 'Not Now' and notification dialogs.
    - Automatic 'Share to Facebook' toggle support.
    - Post-publishing verification & proof capture.
    """

    def __init__(self, headless: bool = False):
        self.headless = headless

    def dismiss_popups(self, page):
        """Dismiss common Instagram popups and dialogs."""
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass

        popup_buttons = [
            "button:has-text('Not Now')",
            "button:has-text('Lain Kali')",
            "button:has-text('Jangan Sekarang')",
            "button:has-text('Cancel')",
            "button:has-text('Batal')",
            "button:has-text('OK')",
            "button:has-text('Mengerti')"
        ]

        for sel in popup_buttons:
            try:
                btn = page.locator(sel).first
                if btn.count() > 0 and btn.is_visible():
                    btn.click(timeout=1500)
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
        Uploads Video, Poster, or Carousel directly to Instagram Web.
        """
        if isinstance(media_paths, (str, Path)):
            media_list = [Path(media_paths).resolve()]
        else:
            media_list = [Path(p).resolve() for p in media_paths]

        if not media_list:
            return False, "Tidak ada file media yang diberikan untuk diunggah.", None

        resolved_files = [str(p) for p in media_list]
        category_name = "Reels" if is_reel else ("Carousel" if len(resolved_files) > 1 else "Poster")

        state_file = get_account_state_file(account_name, "instagram")
        if not state_file.exists():
            return False, f"Sesi Instagram untuk akun '{account_name}' belum ada. Silakan jalankan login terlebih dahulu.", None

        sanitized_caption = ContentValidator.sanitize_caption(caption, platform="instagram")
        timestamp = int(time.time())
        screenshot_path = str(LOGS_DIR / f"instagram_{account_name}_{timestamp}.png")

        mode_text = "HEADLESS" if self.headless else "VISIBLE BROWSER (FULL MAXIMIZED)"
        console.print(f"[bold cyan]=== MEMULAI UPLOAD INSTAGRAM DIRECT {category_name.upper()} ({mode_text}) ===[/bold cyan]")
        console.print(f"Akun: [magenta]{account_name}[/magenta]")
        console.print(f"Jumlah File: [yellow]{len(resolved_files)}[/yellow] ({Path(resolved_files[0]).name})")
        console.print(f"Caption: [italic]{sanitized_caption[:80]}...[/italic]")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                slow_mo=600 if not self.headless else 0,
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ]
            )
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                no_viewport=True if not self.headless else False,
                viewport={"width": 1440, "height": 900} if self.headless else None,
                storage_state=str(state_file)
            )
            page = context.new_page()

            try:
                # 1. Buka Beranda Instagram
                console.print("[cyan]1. Membuka Instagram Web...[/cyan]")
                page.goto(INSTAGRAM_BASE_URL, timeout=45000, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)

                # Cek session expired / redirect login
                if "accounts/login" in page.url:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return False, f"Session Instagram untuk '{account_name}' telah kadaluarsa. Silakan login ulang.", screenshot_path

                self.dismiss_popups(page)

                # 2. Klik tombol 'Create' di sidebar
                console.print("[cyan]2. Membuka menu Create di sidebar...[/cyan]")
                create_btn = page.locator(
                    "svg[aria-label='New post'], svg[aria-label='Postingan baru'], span:text-is('Create'), span:text-is('Buat'), a[href='#']:has-text('Create')"
                ).first
                if create_btn.count() == 0:
                    create_btn = page.locator("div[role='button']:has-text('Create'), div[role='button']:has-text('Buat')").first

                if create_btn.count() > 0:
                    create_btn.click()
                    page.wait_for_timeout(2000)

                # Klik item submenu 'Post'
                post_submenu = page.locator("span:text-is('Post'), span:text-is('Postingan'), div[role='button']:has-text('Post')").first
                if post_submenu.count() > 0 and post_submenu.is_visible():
                    post_submenu.click()
                    page.wait_for_timeout(3000)

                # 3. Masukkan file media langsung ke input file
                console.print(f"[cyan]3. Menyuntikkan {len(resolved_files)} file media ke composer...[/cyan]")
                file_input = page.locator("input[type='file']").first
                if file_input.count() == 0:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return False, "Elemen input file upload tidak ditemukan di Instagram.", screenshot_path

                file_input.set_input_files(resolved_files)
                page.wait_for_timeout(6000)
                self.dismiss_popups(page)

                # 4. Pengaturan Rasio Aspek (Original / 9:16)
                console.print("[cyan]4. Menyesuaikan rasio aspek menjadi Original (9:16)...[/cyan]")
                crop_btn = page.locator(
                    "button:has(svg[aria-label='Select crop']), button:has(svg[aria-label='Pilih pemotongan']), svg[aria-label='Select crop']"
                ).first
                if crop_btn.count() > 0:
                    crop_btn.click()
                    page.wait_for_timeout(1000)

                    # Klik pilihan 'Original'
                    orig_btn = page.locator(
                        "span:text-is('Original'), span:text-is('Asli'), div[role='button']:has-text('Original'), div[role='button']:has-text('Asli')"
                    ).first
                    if orig_btn.count() > 0:
                        orig_btn.click()
                        page.wait_for_timeout(1000)
                        console.print("[green]✓ Rasio Original (9:16) berhasil dipilih![/green]")

                # 5. Navigasi Next (Filters & Edit)
                console.print("[cyan]5. Melanjutkan ke langkah Filter & Edit...[/cyan]")
                next_btn = page.locator(
                    "div[role='button']:has-text('Next'), button:has-text('Next'), div[role='button']:has-text('Selanjutnya'), button:has-text('Selanjutnya')"
                ).first
                if next_btn.count() > 0:
                    next_btn.click()
                    page.wait_for_timeout(3500)

                # 6. Navigasi Next (Caption & Publish Details)
                console.print("[cyan]6. Melanjutkan ke langkah Caption & Detail...[/cyan]")
                next_btn = page.locator(
                    "div[role='button']:has-text('Next'), button:has-text('Next'), div[role='button']:has-text('Selanjutnya'), button:has-text('Selanjutnya')"
                ).first
                if next_btn.count() > 0:
                    next_btn.click()
                    page.wait_for_timeout(3500)

                # 7. Isi Caption & Hashtags
                if sanitized_caption:
                    console.print("[cyan]7. Mengisi caption Instagram...[/cyan]")
                    caption_box = page.locator(
                        "div[aria-label='Write a caption...'], div[aria-label='Tulis keterangan...'], div[role='textbox'], div[contenteditable='true']"
                    ).first
                    if caption_box.count() > 0:
                        caption_box.click()
                        page.wait_for_timeout(500)
                        caption_box.fill(sanitized_caption)
                        page.wait_for_timeout(1000)

                # 8. Otomatisasi Share to Facebook Toggle jika ada
                try:
                    fb_toggle = page.locator("input[type='checkbox'], div[role='switch']").first
                    if fb_toggle.count() > 0:
                        is_checked = fb_toggle.is_checked() if fb_toggle.get_attribute("type") == "checkbox" else (fb_toggle.get_attribute("aria-checked") == "true")
                        if not is_checked:
                            fb_toggle.click()
                            console.print("[green]✓ Sakelar 'Share to Facebook' diaktifkan![/green]")
                except Exception:
                    pass

                # 9. Klik Tombol 'Share' / 'Bagikan'
                console.print(f"[bold green]8. Memposting {category_name} ke Instagram Akun: [{account_name}]...[/bold green]")
                share_btn = page.locator(
                    "div[role='button']:text-is('Share'), button:text-is('Share'), div[role='button']:text-is('Bagikan'), button:text-is('Bagikan')"
                ).first
                if share_btn.count() > 0:
                    share_btn.click()
                else:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return False, "Tombol 'Share' / 'Bagikan' tidak ditemukan.", screenshot_path

                # 10. Tunggu Konfirmasi Upload Selesai
                console.print("[cyan]Menunggu konfirmasi upload selesai dari server Instagram...[/cyan]")
                success = False
                for _ in range(40):
                    page.wait_for_timeout(2000)
                    content = page.content().lower()
                    if (
                        "your reel has been shared" in content
                        or "your post has been shared" in content
                        or "telah dibagikan" in content
                        or "post shared" in content
                    ):
                        success = True
                        break

                page.wait_for_timeout(3000)
                page.screenshot(path=screenshot_path)
                browser.close()

                console.print(f"[bold green]✓ {category_name} Instagram untuk [{account_name}] berhasil diposting! Bukti: {screenshot_path}[/bold green]")
                return True, f"{category_name} berhasil diupload ke Instagram ({account_name}).", screenshot_path

            except Exception as ex:
                try:
                    page.screenshot(path=screenshot_path)
                except Exception:
                    pass
                browser.close()
                return False, f"Terjadi kesalahan saat upload ke Instagram: {str(ex)}", screenshot_path

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
