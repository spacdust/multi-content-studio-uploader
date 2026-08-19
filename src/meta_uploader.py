import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from rich.console import Console
from playwright.sync_api import sync_playwright

from src.config import (
    get_account_state_file,
    INSTAGRAM_BASE_URL,
    META_BUSINESS_COMPOSER_URL,
    META_BUSINESS_LOGIN_URL,
    DEFAULT_USER_AGENT,
    VIEWPORT,
    LOGS_DIR
)
from src.validator import ContentValidator

console = Console()

class MetaBusinessUploader:
    """Automates cross-posting Reels, Videos, Posters, and Carousels to Instagram and Facebook Page via Meta Business Suite."""

    def __init__(self, headless: bool = True):
        self.headless = headless

    def upload(
        self,
        media_path: str | Path | List[str | Path],
        caption: str = "",
        category: str = "Video",
        account_name: str = "default",
        scheduled_time: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Uploads content to Meta Business Suite for cross-posting to Instagram and Facebook Page.
        Returns: (success: bool, message: str, screenshot_path: Optional[str])
        """
        state_file = get_account_state_file(account_name, "meta")
        if not state_file.exists():
            return False, f"Sesi Meta Business Suite untuk akun '{account_name}' belum ada. Silakan hubungkan akun terlebih dahulu.", None

        if isinstance(media_path, list):
            file_paths = [Path(p).resolve() for p in media_path]
        else:
            file_paths = [Path(media_path).resolve()]

        for p in file_paths:
            if not p.exists():
                return False, f"File tidak ditemukan: {p}", None

        sanitized_caption = ContentValidator.sanitize_caption(caption, platform="meta")
        timestamp = int(time.time())
        screenshot_path = str(LOGS_DIR / f"meta_{account_name}_{timestamp}.png")

        console.print(f"[bold cyan]Memulai proses upload Meta Business Suite untuk Akun: [magenta]{account_name}[/magenta]...[/bold cyan]")
        console.print(f"Kategori: [yellow]{category}[/yellow] | Total File: [yellow]{len(file_paths)}[/yellow]")
        console.print(f"Caption: [italic]{sanitized_caption[:60]}...[/italic]")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    "--start-maximized" if not self.headless else "",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ]
            )
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                viewport=None if not self.headless else VIEWPORT,
                no_viewport=True if not self.headless else False,
                storage_state=str(state_file)
            )
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            page = context.new_page()

            try:
                console.print("[cyan]Membuka komposer Meta Business Suite...[/cyan]")
                page.goto(META_BUSINESS_COMPOSER_URL, timeout=60000, wait_until="domcontentloaded")
                page.wait_for_timeout(4000)

                if "login" in page.url:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return False, f"Sesi Meta Business Suite untuk '{account_name}' kadaluarsa. Silakan login ulang.", screenshot_path

                try:
                    placement_checkboxes = page.locator("input[type='checkbox']")
                    for i in range(min(placement_checkboxes.count(), 5)):
                        cb = placement_checkboxes.nth(i)
                        try:
                            if not cb.is_checked():
                                cb.check(force=True)
                        except Exception:
                            pass
                except Exception:
                    pass

                console.print("[cyan]Mengunggah file media...[/cyan]")
                file_input = page.locator("input[type='file']").first
                if file_input.count() == 0:
                    add_btn = page.locator("button:has-text('Add video'), button:has-text('Tambahkan video'), button:has-text('Add photo'), button:has-text('Tambahkan foto')").first
                    if add_btn.count() > 0:
                        add_btn.click()
                        page.wait_for_timeout(1000)
                    file_input = page.locator("input[type='file']").first

                if file_input.count() > 0:
                    if len(file_paths) == 1:
                        file_input.set_input_files(str(file_paths[0]))
                    else:
                        file_input.set_input_files([str(fp) for fp in file_paths])
                    page.wait_for_timeout(3000)
                else:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return False, "Input file tidak ditemukan di komposer Meta Business Suite.", screenshot_path

                console.print("[cyan]Memasukkan caption dan hashtag...[/cyan]")
                caption_field = page.locator("div[role='textbox'], textarea[placeholder*='Write a post'], textarea[placeholder*='Tulis postingan'], div[aria-label*='Write a post'], div[aria-label*='Tulis postingan']").first
                if caption_field.count() > 0:
                    caption_field.click()
                    page.keyboard.insert_text(sanitized_caption)
                    page.wait_for_timeout(1000)

                console.print("[cyan]Mempublikasikan konten paralel ke Instagram dan Facebook...[/cyan]")
                page.wait_for_timeout(3000)

                publish_btn = page.locator("button:has-text('Publish'), button:has-text('Terbitkan'), button:has-text('Bagikan'), div[role='button']:has-text('Publish'), div[role='button']:has-text('Terbitkan')").last
                if publish_btn.count() > 0 and publish_btn.is_enabled():
                    publish_btn.click()
                    page.wait_for_timeout(6000)
                    page.screenshot(path=screenshot_path)
                    context.storage_state(path=str(state_file))
                    browser.close()
                    return True, f"Konten berhasil diposting ke Meta Business Suite (Instagram + Facebook) untuk akun '{account_name}'!", screenshot_path
                else:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return False, "Tombol Publish di Meta Business Suite tidak aktif atau tidak ditemukan.", screenshot_path

            except Exception as e:
                try:
                    page.screenshot(path=screenshot_path)
                except Exception:
                    pass
                try:
                    browser.close()
                except Exception:
                    pass
                return False, f"Terjadi kesalahan saat upload ke Meta Business Suite: {str(e)}", screenshot_path
