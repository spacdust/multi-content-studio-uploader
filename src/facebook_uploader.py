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
    launch_browser,
    get_safe_storage_state
)
from src.validator import ContentValidator

console = Console(highlight=False, legacy_windows=False)

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

    def handle_post_confirmation(self, page, max_wait_sec: int = 15):
        """
        Monitors post-submission state on Facebook.
        If popups like 'Menyelenggarakan acara?' appear:
        Clicks 'Terbitkan Postingan Asli' / 'Publish Original Post' to ensure the post is published.
        """
        console.print("[cyan]Menunggu dan memantau konfirmasi penerbitan Facebook...[/cyan]")
        start_t = time.time()
        while time.time() - start_t < max_wait_sec:
            # 1. Cek tombol 'Terbitkan Postingan Asli' / 'Publish Original Post'
            original_post_btn = page.locator(
                "div[role='dialog'] div[role='button']:has-text('Terbitkan Postingan Asli'), "
                "div[role='dialog'] div[aria-label='Terbitkan Postingan Asli'], "
                "div[role='button']:has-text('Terbitkan Postingan Asli'), "
                "button:has-text('Terbitkan Postingan Asli'), "
                "div[role='dialog'] div[role='button']:has-text('Publish Original Post'), "
                "div[role='dialog'] div[aria-label='Publish Original Post'], "
                "div[role='button']:has-text('Publish Original Post'), "
                "button:has-text('Publish Original Post'), "
                "span:has-text('Terbitkan Postingan Asli')"
            ).first
            if original_post_btn.count() > 0 and original_post_btn.is_visible():
                console.print("[bold green][OK] Terdeteksi popup event/konfirmasi Facebook. Mengklik 'Terbitkan Postingan Asli'...[/bold green]")
                original_post_btn.click(force=True)
                page.wait_for_timeout(3500)
                break

            # 2. Cek modal popups sekunder (Lanjutkan / Selesai / Not Now / Lain Kali)
            for sel in [
                "div[role='dialog'] div[role='button']:has-text('Selesai')",
                "div[role='dialog'] div[role='button']:has-text('Done')",
                "div[role='dialog'] div[role='button']:has-text('Not Now')",
                "div[role='dialog'] div[role='button']:has-text('Lain Kali')"
            ]:
                try:
                    btn = page.locator(sel).first
                    if btn.count() > 0 and btn.is_visible():
                        btn.click(timeout=1000)
                        page.wait_for_timeout(2000)
                        break
                except Exception:
                    pass

            page.wait_for_timeout(1000)

    def upload_media(
        self,
        media_paths: List[str | Path] | str | Path,
        caption: str = "",
        is_reel: bool = False,
        account_name: str = "default",
        session_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Uploads media directly to Facebook Fanpage.
        """
        from src.publish_tracker import PublishTracker

        if isinstance(media_paths, (str, Path)):
            media_list = [Path(media_paths).resolve()]
        else:
            media_list = [Path(p).resolve() for p in media_paths]

        if not media_list:
            PublishTracker.update_step(session_id, "facebook", "Media Kosong", 0, "Tidak ada file media yang diberikan", "error", is_failed=True)
            return False, "Tidak ada file media yang diberikan untuk Facebook.", None

        state_file = get_account_state_file(account_name, "facebook")
        if not state_file.exists():
            err_msg = f"Sesi Facebook untuk akun '{account_name}' belum ada. Silakan login terlebih dahulu."
            PublishTracker.update_step(session_id, "facebook", "Sesi Hilang", 0, err_msg, "error", is_failed=True, error_msg=err_msg)
            return False, err_msg, None

        resolved_files = [str(p) for p in media_list]
        category_name = "Reels" if is_reel else ("Carousel" if len(resolved_files) > 1 else "Poster")
        sanitized_caption = ContentValidator.sanitize_caption(caption, platform="facebook")
        timestamp = int(time.time())
        screenshot_path = str(LOGS_DIR / f"facebook_{account_name}_{timestamp}.png")

        mode_text = "HEADLESS" if self.headless else "VISIBLE BROWSER (FULL MAXIMIZED)"
        console.print(f"[bold cyan]=== MEMULAI UPLOAD FACEBOOK FANSPAGE {category_name.upper()} ({mode_text}) ===[/bold cyan]")
        console.print(f"Akun: [magenta]{account_name}[/magenta]")
        console.print(f"Jumlah File: [yellow]{len(resolved_files)}[/yellow]")

        PublishTracker.update_step(session_id, "facebook", "Membuka browser Facebook...", 15, f"Membuka halaman Facebook untuk akun '{account_name}'", "info")

        with sync_playwright() as p:
            browser = launch_browser(p, headless=self.headless, slow_mo=600 if not self.headless else 0)
            safe_state = get_safe_storage_state(state_file)
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                no_viewport=True if not self.headless else False,
                viewport={"width": 1440, "height": 900} if self.headless else None,
                storage_state=safe_state
            )
            page = context.new_page()

            try:
                if is_reel:
                    # 1. Buka Beranda Facebook
                    console.print("[cyan]1. Membuka Beranda Facebook...[/cyan]")
                    PublishTracker.update_step(session_id, "facebook", "Memuat Beranda Facebook...", 25, "Memuat halaman utama Facebook", "step")
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
                    PublishTracker.update_step(session_id, "facebook", "Mengunggah video ke Facebook...", 40, f"Mengunggah file video {Path(resolved_files[0]).name} ke Facebook Reel", "step")
                    file_input = page.locator("input[type='file']").first
                    if file_input.count() == 0:
                        page.screenshot(path=screenshot_path)
                        browser.close()
                        err_msg = "Input file video tidak ditemukan di Facebook."
                        PublishTracker.update_step(session_id, "facebook", "Input Hilang", 0, err_msg, "error", is_failed=True, error_msg=err_msg)
                        return False, err_msg, screenshot_path

                    file_input.set_input_files([resolved_files[0]])
                    page.wait_for_timeout(5000)

                    # 4. Next Button 1 (Ke Edit reel)
                    console.print("[cyan]4. Melanjutkan ke Edit reel...[/cyan]")
                    PublishTracker.update_step(session_id, "facebook", "Konfigurasi Reel Facebook...", 55, "Melanjutkan ke konfigurasi reel", "step")
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
                        PublishTracker.update_step(session_id, "facebook", "Mengisi caption Reel...", 75, "Mengisi teks caption dan hashtag di Reel Facebook", "step")
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
                    PublishTracker.update_step(session_id, "facebook", "Mempublikasikan Reel...", 85, "Menekan tombol 'Kirim' / 'Posting' Reel Facebook", "step")
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
                        err_msg = "Tombol Kirim/Posting Reel Facebook tidak ditemukan."
                        PublishTracker.update_step(session_id, "facebook", "Tombol Kirim Hilang", 0, err_msg, "error", is_failed=True, error_msg=err_msg)
                        return False, err_msg, screenshot_path

                    # 8. Tunggu konfirmasi dan tangani popup event ('Terbitkan Postingan Asli')
                    PublishTracker.update_step(session_id, "facebook", "Menunggu konfirmasi Facebook...", 95, "Memantau konfirmasi penerbitan Facebook & popup dialog...", "step")
                    self.handle_post_confirmation(page, max_wait_sec=15)
                    page.wait_for_timeout(3000)
                    try:
                        context.storage_state(path=str(state_file))
                    except Exception:
                        pass
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    PublishTracker.update_step(session_id, "facebook", "Facebook Reel Berhasil Terbit!", 100, f"Facebook Reel untuk akun '{account_name}' berhasil diposting!", "success", is_completed=True, post_url=screenshot_path)
                    return True, f"Facebook Reel berhasil diposting untuk '{account_name}'.", screenshot_path

                else:
                    # 1. Buka Beranda Facebook
                    console.print("[cyan]1. Membuka Facebook Feed...[/cyan]")
                    PublishTracker.update_step(session_id, "facebook", "Memuat Beranda Facebook...", 25, "Memuat halaman utama Facebook", "step")
                    page.goto("https://www.facebook.com/", timeout=45000, wait_until="domcontentloaded")
                    page.wait_for_timeout(5000)

                    if "login" in page.url:
                        page.screenshot(path=screenshot_path)
                        browser.close()
                        err_msg = f"Session Facebook untuk '{account_name}' telah kadaluarsa."
                        PublishTracker.update_step(session_id, "facebook", "Sesi Expired", 0, err_msg, "error", is_failed=True, error_msg=err_msg)
                        return False, err_msg, screenshot_path

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
                    PublishTracker.update_step(session_id, "facebook", f"Mengunggah {len(resolved_files)} file media...", 45, f"Mengunggah {len(resolved_files)} file {category_name} ke Facebook", "step")
                    file_input = page.locator("input[type='file']").first
                    if file_input.count() > 0:
                        file_input.set_input_files(resolved_files)
                        page.wait_for_timeout(4000)

                    # 4. Isi Caption langsung di awal tepat di atas gambar
                    if sanitized_caption:
                        console.print("[cyan]4. Mengisi teks caption di awal di atas gambar...[/cyan]")
                        PublishTracker.update_step(session_id, "facebook", "Mengisi caption Facebook...", 70, "Mengisi teks keterangan caption postingan Facebook", "step")
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
                    PublishTracker.update_step(session_id, "facebook", "Mempublikasikan postingan...", 85, "Menekan tombol Posting / Kirim Facebook", "step")
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
                        err_msg = "Tombol Posting Facebook tidak ditemukan."
                        PublishTracker.update_step(session_id, "facebook", "Tombol Posting Hilang", 0, err_msg, "error", is_failed=True, error_msg=err_msg)
                        return False, err_msg, screenshot_path

                    # 7. Tunggu konfirmasi dan tangani popup event ('Terbitkan Postingan Asli')
                    PublishTracker.update_step(session_id, "facebook", "Menunggu verifikasi upload...", 95, "Memantau konfirmasi penerbitan Facebook...", "step")
                    self.handle_post_confirmation(page, max_wait_sec=15)
                    page.wait_for_timeout(3000)
                    try:
                        context.storage_state(path=str(state_file))
                    except Exception:
                        pass
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    PublishTracker.update_step(session_id, "facebook", "Facebook Berhasil Terbit!", 100, f"{category_name} berhasil diposting ke Facebook untuk akun '{account_name}'!", "success", is_completed=True, post_url=screenshot_path)
                    return True, f"{category_name} berhasil diposting ke Facebook ({account_name}).", screenshot_path

            except Exception as ex:
                try:
                    page.screenshot(path=screenshot_path)
                except Exception:
                    pass
                browser.close()
                err_msg = f"Terjadi kesalahan upload Facebook: {str(ex)}"
                PublishTracker.update_step(session_id, "facebook", "Upload Gagal", 0, err_msg, "error", is_failed=True, error_msg=err_msg)
                return False, err_msg, screenshot_path

    # Alias for backward compatibility
    def upload(
        self,
        video_path: str | Path,
        caption: str = "",
        as_reel: bool = True,
        account_name: str = "default",
        session_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        return self.upload_media(
            media_paths=[video_path],
            caption=caption,
            is_reel=as_reel,
            account_name=account_name,
            session_id=session_id
        )

    @staticmethod
    def fetch_latest_post_link(account_name: str, caption_snippet: str = "") -> Optional[str]:
        """
        Visits the user's OWN Facebook Fanspage profile (never other people's feed)
        and matches by caption keywords or grabs the newest published post/reel permalink.
        """
        state_file = get_account_state_file(account_name, "facebook")
        if not state_file.exists():
            return None

        with sync_playwright() as p:
            try:
                browser = launch_browser(p, headless=True)
                safe_state = get_safe_storage_state(state_file)
                context = browser.new_context(
                    user_agent=DEFAULT_USER_AGENT,
                    storage_state=safe_state
                )
                page = context.new_page()
                page.route("**/*.{mp4,webm}", lambda r: r.abort())
                
                try:
                    page.goto("https://www.facebook.com/me", timeout=15000, wait_until="domcontentloaded")
                    page.wait_for_timeout(2000)
                    me_url = page.url
                    reels_url = f"{me_url}&sk=reels_tab" if "?" in me_url else f"{me_url}/reels"
                    page.goto(reels_url, timeout=15000, wait_until="domcontentloaded")
                    page.wait_for_timeout(2000)
                except Exception:
                    pass

                post_anchors = page.locator("a").all()
                candidates = []
                for pa in post_anchors:
                    href = pa.get_attribute("href") or ""
                    m = re.search(r"/(reel|videos|posts)/([0-9A-Za-z_-]{4,})", href)
                    if m:
                        link = f"https://www.facebook.com/{m.group(1)}/{m.group(2)}/"
                        if link not in candidates:
                            candidates.append(link)

                if candidates:
                    browser.close()
                    return candidates[0]

                browser.close()
            except Exception:
                pass
        return None
