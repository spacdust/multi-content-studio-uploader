import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from rich.console import Console
from playwright.sync_api import sync_playwright

from src.config import (
    get_account_state_file,
    INSTAGRAM_BASE_URL,
    DEFAULT_USER_AGENT,
    VIEWPORT,
    LOGS_DIR
)
from src.validator import ContentValidator

console = Console()

class InstagramUploader:
    """Automates uploading Reels / Posts to Instagram via Playwright with per-account support."""

    def __init__(self, headless: bool = True):
        self.headless = headless

    def upload(
        self,
        video_path: str | Path,
        caption: str = "",
        as_reel: bool = True,
        account_name: str = "default"
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Uploads a video (Reel/Post) to Instagram for a specific account.
        Returns: (success: bool, message: str, screenshot_path: Optional[str])
        """
        path = Path(video_path).resolve()
        valid, err = ContentValidator.validate_video_file(path)
        if not valid:
            return False, err or "Invalid video", None

        state_file = get_account_state_file(account_name, "instagram")
        if not state_file.exists():
            return False, f"Sesi Instagram untuk akun '{account_name}' tidak ditemukan. Jalankan login terlebih dahulu.", None

        sanitized_caption = ContentValidator.sanitize_caption(caption, platform="instagram")
        timestamp = int(time.time())
        screenshot_path = str(LOGS_DIR / f"instagram_{account_name}_{timestamp}.png")

        console.print(f"[bold cyan]Memulai proses upload Instagram untuk Akun: [magenta]{account_name}[/magenta]...[/bold cyan]")
        console.print(f"File: [yellow]{path.name}[/yellow]")
        console.print(f"Caption: [italic]{sanitized_caption[:60]}...[/italic]")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                viewport=VIEWPORT,
                storage_state=str(state_file)
            )
            page = context.new_page()

            try:
                # 1. Buka Instagram Home
                page.goto(INSTAGRAM_BASE_URL, timeout=45000, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)

                # Cek jika diarahkan ke halaman login
                if "accounts/login" in page.url:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return False, f"Session Instagram untuk '{account_name}' kadaluarsa. Silakan login ulang.", screenshot_path

                try:
                    not_now_btn = page.locator("button:has-text('Not Now'), button:has-text('Lain Kali'), button:has-text('Jangan Sekarang')").first
                    if not_now_btn.count() > 0:
                        not_now_btn.click()
                        page.wait_for_timeout(1000)
                except Exception:
                    pass

                # 2. Cari tombol 'Create' / 'Buat' (+)
                console.print("[cyan]Membuka modal upload Instagram...[/cyan]")
                create_btn = page.locator(
                    "svg[aria-label='New post'], svg[aria-label='Postingan baru'], svg[aria-label='New Post'], "
                    "span:has-text('Create'), span:has-text('Buat'), "
                    "a[href='#']:has-text('Create'), a[href='#']:has-text('Buat')"
                ).first

                if create_btn.count() == 0:
                    create_btn = page.locator("div[role='button']:has-text('Create'), div[role='button']:has-text('Buat')").first

                if create_btn.count() > 0:
                    create_btn.click()
                    page.wait_for_timeout(2000)

                # 3. Cari input file video
                file_input = page.locator("input[type='file']").first
                if file_input.count() == 0:
                    post_submenu = page.locator("span:has-text('Post'), span:has-text('Postingan')").first
                    if post_submenu.count() > 0:
                        post_submenu.click()
                        page.wait_for_timeout(2000)
                        file_input = page.locator("input[type='file']").first

                if file_input.count() == 0:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return False, "Tidak dapat menemukan form input file upload di Instagram.", screenshot_path

                # 4. Set file video
                console.print("[yellow]Mengunggah file video ke browser...[/yellow]")
                file_input.set_input_files(str(path))
                page.wait_for_timeout(5000)

                ok_btn = page.locator("button:has-text('OK'), button:has-text('Mengerti')").first
                if ok_btn.count() > 0:
                    ok_btn.click()
                    page.wait_for_timeout(1000)

                # 5. Klik Next (Langkah Crop / Aspect Ratio)
                console.print("[dim]Navigasi ke pengaturan media...[/dim]")
                next_btn = page.locator("button:has-text('Next'), div[role='button']:has-text('Next'), button:has-text('Selanjutnya'), div[role='button']:has-text('Selanjutnya')").first
                if next_btn.count() > 0:
                    next_btn.click()
                    page.wait_for_timeout(3000)
                
                # 6. Klik Next lagi (Langkah Filter / Cover / Edit)
                next_btn = page.locator("button:has-text('Next'), div[role='button']:has-text('Next'), button:has-text('Selanjutnya'), div[role='button']:has-text('Selanjutnya')").first
                if next_btn.count() > 0:
                    next_btn.click()
                    page.wait_for_timeout(3000)

                # 7. Mengisi Caption
                if sanitized_caption:
                    console.print("[cyan]Mengisi caption Instagram...[/cyan]")
                    caption_box = page.locator(
                        "div[aria-label='Write a caption...'], div[aria-label='Tulis keterangan...'], div[role='textbox'], div[contenteditable='true']"
                    ).first

                    if caption_box.count() > 0:
                        caption_box.click()
                        page.wait_for_timeout(500)
                        caption_box.fill(sanitized_caption)
                        page.wait_for_timeout(1000)

                # 8. Klik Tombol 'Share' / 'Bagikan'
                console.print(f"[bold green]Memposting Reel ke Instagram Akun: [{account_name}]...[/bold green]")
                share_btn = page.locator(
                    "button:has-text('Share'), div[role='button']:has-text('Share'), "
                    "button:has-text('Bagikan'), div[role='button']:has-text('Bagikan')"
                ).first

                if share_btn.count() > 0:
                    share_btn.click()
                else:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return False, "Tombol 'Share' / 'Bagikan' tidak ditemukan.", screenshot_path

                # 9. Tunggu respon selesai
                console.print("[dim]Menunggu proses upload dan rendering selesai...[/dim]")
                success = False
                for _ in range(30):
                    page.wait_for_timeout(2000)
                    page_content = page.content().lower()
                    if (
                        "your reel has been shared" in page_content
                        or "your post has been shared" in page_content
                        or "telah dibagikan" in page_content
                        or "shared" in page_content
                    ):
                        success = True
                        break

                page.screenshot(path=screenshot_path)
                browser.close()

                if success:
                    console.print(f"[bold green]Video Instagram untuk [{account_name}] berhasil diposting! Bukti: {screenshot_path}[/bold green]")
                    return True, f"Video berhasil diupload ke Instagram ({account_name}).", screenshot_path
                else:
                    return True, f"Upload Instagram ({account_name}) telah dikirim (silakan periksa screenshot).", screenshot_path

            except Exception as ex:
                try:
                    page.screenshot(path=screenshot_path)
                except Exception:
                    pass
                browser.close()
                return False, f"Terjadi kesalahan saat upload Instagram: {str(ex)}", screenshot_path
