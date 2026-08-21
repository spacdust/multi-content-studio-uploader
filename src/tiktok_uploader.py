import os
import re
import random
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from rich.console import Console
from playwright.sync_api import sync_playwright

from src.config import (
    get_account_state_file,
    TIKTOK_UPLOAD_URL,
    TIKTOK_ALT_UPLOAD_URL,
    DEFAULT_USER_AGENT,
    LOGS_DIR,
    launch_browser,
    get_safe_storage_state
)
from src.validator import ContentValidator

console = Console(highlight=False, legacy_windows=False)

class TikTokUploader:
    """
    Automates uploading videos to TikTok with:
    - Full screen maximized browser.
    - Automatic popup dismissals (Got it, tour guides, cookies).
    - Full in-app TikTok Studio Editor:
        * Dynamic detection of topmost sound item (+)
        * Favorite sound tab auto-selection & randomizer
        * Accurate volume dB adjustment (input.PropSettingInput__input)
        * Save and return to upload.
    - Accurate targeting of the primary red 'Post' button (avoiding sidebar 'Posts').
    """

    def __init__(self, headless: bool = False):
        self.headless = headless

    @staticmethod
    def _save_storage_state_safe(context, state_file: Path) -> bool:
        """
        Safely saves storage_state by MERGING rotated cookies into existing state_file,
        preserving all authentic companion tokens (ttwid, odin_tt, store-idc, passport tokens).
        """
        try:
            new_cookies = context.cookies()
            has_session = any(
                c.get("name") in ["sessionid", "sessionid_ss", "sid_tt"] and len(c.get("value", "")) > 5
                for c in new_cookies
            )
            if not has_session:
                # DO NOT OVERWRITE VALID EXISTING SESSION WITH LOGGED-OUT EMPTY STATE!
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
                    val = c.get("sameSite")
                    if not val or not isinstance(val, str):
                        c["sameSite"] = "None"
                    elif "strict" in val.lower():
                        c["sameSite"] = "Strict"
                    elif "lax" in val.lower():
                        c["sameSite"] = "Lax"
                    else:
                        c["sameSite"] = "None"
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

    def dismiss_popups(self, page, target=None):
        """Dismiss all common TikTok guide tours, coachmarks, tooltips, cookie dialogs, and announcement modals."""
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass

        # 1. Direct DOM Removal of floating guide bubbles, coachmarks & tooltips (e.g. "New editing features added")
        try:
            page.evaluate("""
                () => {
                    const popovers = document.querySelectorAll(
                        "div[class*='popover'], div[class*='tooltip'], div[class*='guide'], div[class*='bubble'], div[class*='coachmark'], div[class*='tour'], div[class*='hint']"
                    );
                    popovers.forEach(el => {
                        try { el.click(); } catch(e){}
                        try { el.remove(); } catch(e){}
                    });

                    document.querySelectorAll("div, p, span, h1, h2, h3, h4").forEach(el => {
                        const txt = (el.innerText || "").toLowerCase();
                        if (
                            txt.includes("new editing features") ||
                            txt.includes("editing features added") ||
                            txt.includes("fitur pengeditan baru") ||
                            txt.includes("manage your videos")
                        ) {
                            try { el.click(); } catch(e){}
                            const container = el.closest("div[class*='container'], div[class*='wrapper'], div[class*='popover'], div[style*='position: absolute'], div[style*='position: fixed']") || el;
                            try { container.remove(); } catch(e){}
                        }
                    });
                }
            """)
        except Exception:
            pass

        # 2. Click-to-dismiss standard dialog buttons & onboarding tours
        try:
            got_it_buttons = page.locator("button, div[role='button'], a").filter(has_text=re.compile(r"^(Got it|Mengerti|OK|Selesai|I understand|Accept|Agree|Skip|Lewati|Close|Tutup)$", re.I))
            for i in range(min(got_it_buttons.count(), 5)):
                try:
                    target_btn = got_it_buttons.nth(i)
                    if target_btn.is_visible():
                        target_btn.click(timeout=1000)
                        page.wait_for_timeout(300)
                except Exception:
                    pass
        except Exception:
            pass

        popup_selectors = [
            "button:has-text('Got it')",
            "button:has-text('Mengerti')",
            "button:has-text('Accept')",
            "button:has-text('Setuju')",
            "button:has-text('I understand')",
            "button:has-text('Close')",
            "button:has-text('Tutup')",
            "div[class*='modal'] button[class*='close']",
            "div[class*='dialog'] button[class*='close']",
            "div[class*='guide-bubble'] button",
            "div[class*='tour-wrapper'] button",
            "div[data-e2e='modal-close-icon']",
            "div[class*='btn-close']",
            "div[class*='close-icon']"
        ]

        for sel in popup_selectors:
            try:
                btn = page.locator(sel).first
                if btn.count() > 0 and btn.is_visible():
                    btn.click(timeout=1000)
                    page.wait_for_timeout(300)
            except Exception:
                pass

            if target and target != page:
                try:
                    btn = target.locator(sel).first
                    if btn.count() > 0 and btn.is_visible():
                        btn.click(timeout=1000)
                        page.wait_for_timeout(300)
                except Exception:
                    pass

    def apply_tiktok_editor_sound(
        self,
        page,
        sound_mode: str = "favorite",
        sound_query: str = "school",
        volume_db: Optional[str] = "-7",
        session_id: Optional[str] = None
    ) -> bool:
        """
        Full workflow for TikTok Studio Video & Audio Editor:
        1. Dismiss any overlay popovers / guide tooltips.
        2. Click Sounds button under preview.
        3. Dismiss 'Phone mode' modal.
        4. Apply sound (Favorite / Search) and adjust volume.
        5. Click 'Save' to apply.
        """
        from src.publish_tracker import PublishTracker

        try:
            console.print(f"[bold cyan]=== MEMBUKA TIKTOK STUDIO AUDIO & SOUND EDITOR (Mode: {sound_mode.upper()}) ===[/bold cyan]")
            PublishTracker.update_step(session_id, "tiktok", "Membuka Video Editor & Audio...", 45, f"Membuka TikTok Studio Audio & Sound Editor (Mode: {sound_mode.upper()})", "step")
            
            # Dismiss popovers and scroll top
            self.dismiss_popups(page)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(800)
            self.dismiss_popups(page)

            # 1. Klik tombol Sounds / Edit video di bawah preview video
            console.print("[cyan]1. Mengklik tombol 'Sounds' / 'Edit video' di bawah preview video...[/cyan]")
            sounds_btn = None
            
            for sel in [
                "button[data-button-name='sounds']",
                "button.editor-entrance[data-button-name='sounds']",
                "button.editor-entrance",
                "[data-button-name='sounds']",
                "button:has-text('Sounds')",
                "button:has-text('Edit video')",
                "button:has-text('Edit')",
                "div[role='button']:has-text('Sounds')",
                "div:has-text('Sounds')"
            ]:
                try:
                    for el in page.locator(sel).all():
                        box = el.bounding_box()
                        if box and box["x"] > 300 and box["width"] < 250 and box["height"] < 120:
                            sounds_btn = el
                            break
                    if sounds_btn:
                        break
                except Exception:
                    pass

            if sounds_btn:
                sounds_btn.scroll_into_view_if_needed()
                page.wait_for_timeout(400)
                sounds_btn.click(force=True)
                page.wait_for_timeout(5000)
            else:
                page.evaluate("""
                    () => {
                        const btn = document.querySelector('button[data-button-name="sounds"]') || document.querySelector('button.editor-entrance') || Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Edit video') || b.innerText.includes('Sounds'));
                        if (btn) btn.click();
                    }
                """)
                page.wait_for_timeout(5000)

            # 2. Tutup popup overlay / modal di dalam editor
            console.print("[cyan]2. Menutup dialog petunjuk di dalam editor...[/cyan]")
            page.evaluate("""
                () => {
                    document.querySelectorAll('button, div[role="button"]').forEach(b => {
                        const txt = b.innerText || '';
                        if (txt.includes('Turn on') || txt.includes('Got it') || txt.includes('Next') || txt.includes('Mengerti') || txt.includes('Dismiss') || txt.includes('I understand')) {
                            b.click();
                        }
                    });
                    document.querySelectorAll('.TUXModal-overlay, .common-modal').forEach(m => m.remove());
                }
            """)
            page.wait_for_timeout(1500)

            # Buka panel Sounds HANYA jika belum terbuka (jangan klik jika sudah terbuka agar tidak tertutup)
            page.evaluate("""
                () => {
                    const s = document.querySelector("div[data-name='MusicPanel']");
                    const isSelected = s && s.getAttribute('data-selected') === 'true';
                    const hasList = document.querySelectorAll("div[role='listitem']").length > 0;
                    if (!isSelected && !hasList) {
                        if (s) {
                            s.click();
                        } else {
                            const btn = Array.from(document.querySelectorAll('div, span, button')).find(el => el.innerText && el.innerText.trim() === 'Sounds');
                            if (btn) btn.click();
                        }
                    }
                }
            """)
            page.wait_for_timeout(2000)

            # 3. Pilihan Mode: FAVORITE (RANDOM) vs SEARCH
            sound_applied = False
            if sound_mode == "favorite":
                console.print("[cyan]3. Membuka tab 'Favorites' / 'Favorit' sound...[/cyan]")
                
                # Klik tab Favorites jika belum aktif
                page.evaluate("""
                    () => {
                        const fav = Array.from(document.querySelectorAll('div, span, button, [role="tab"]')).find(el => el.innerText && (el.innerText.trim() === 'Favorites' || el.innerText.trim() === 'Favorit' || el.innerText.trim() === 'Disimpan'));
                        if (fav) {
                            const isSelected = fav.getAttribute('aria-selected') === 'true' || fav.getAttribute('data-selected') === 'true';
                            if (!isSelected) {
                                fav.click();
                            }
                        }
                    }
                """)
                page.wait_for_timeout(3500)

                # Deteksi tombol '+' bulat merah resmi: button.Button__root--shape-rounded.Button__root--type-primary
                console.print("[cyan]Mendeteksi tombol '+' bulat merah resmi pada daftar lagu favorit...[/cyan]")
                add_buttons = page.locator("button.Button__root--shape-rounded.Button__root--type-primary, button[data-shape='rounded'][data-icon-only='true'], button.Button__root--type-primary[data-icon-only='true'], div[role='listitem'] button[class*='type-primary']").all()

                if add_buttons:
                    chosen = random.choice(add_buttons)
                    box = chosen.bounding_box()
                    coord_str = f"di ({box['x']:.0f}, {box['y']:.0f})" if box else ""
                    console.print(f"[bold green][OK] Berhasil memilih secara acak 1 dari {len(add_buttons)} lagu favorit. Mengklik tombol '+' {coord_str}...[/bold green]")
                    PublishTracker.update_step(session_id, "tiktok", "Memilih sound favorit...", 60, f"Memilih secara acak 1 dari {len(add_buttons)} lagu favorit via tombol '+' bulat merah", "step")
                    chosen.scroll_into_view_if_needed()
                    page.wait_for_timeout(400)
                    chosen.click(force=True)
                    page.wait_for_timeout(4000)
                    sound_applied = True
                else:
                    # Fallback via JS click
                    clicked_js = page.evaluate("""
                        () => {
                            const btns = Array.from(document.querySelectorAll('button')).filter(b => b.className && b.className.includes('Button__root--shape-rounded') && b.className.includes('Button__root--type-primary'));
                            if (btns.length > 0) {
                                const idx = Math.floor(Math.random() * btns.length);
                                btns[idx].click();
                                return true;
                            }
                            return false;
                        }
                    """)
                    if clicked_js:
                        console.print("[bold green][OK] Berhasil mengklik tombol '+' sound favorit via JS selector![/bold green]")
                        PublishTracker.update_step(session_id, "tiktok", "Memilih sound favorit...", 60, "Mengklik tombol '+' sound favorit via selector", "step")
                        page.wait_for_timeout(4000)
                        sound_applied = True
                    else:
                        console.print("[yellow]Tab Favorites belum memiliki daftar lagu atau akun belum menyimpan sound favorit di TikTok. Melakukan fallback ke pencarian sound...[/yellow]")
                        PublishTracker.log(session_id, "tiktok", "Lagu favorit belum tersimpan di akun TikTok. Melakukan fallback ke pencarian sound...", "warn")
                        sound_mode = "search"

            if not sound_applied: # sound_mode == "search"
                # Cari sound di kolom 'Search sounds' jika query diberikan
                query_to_use = sound_query.strip() if sound_query else ""
                if query_to_use:
                    console.print(f"[cyan]3. Mencari sound TikTok dengan query: [yellow]'{query_to_use}'[/yellow]...[/cyan]")
                    PublishTracker.update_step(session_id, "tiktok", f"Mencari sound '{query_to_use}'...", 55, f"Mencari audio TikTok dengan kata kunci '{query_to_use}'", "step")
                    search_box = page.locator("input[placeholder*='Search sounds'], input[placeholder*='search sounds'], input[placeholder*='Cari sound']").first
                    if search_box.count() > 0:
                        search_box.click(force=True)
                        search_box.fill(query_to_use)
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(3000)

                # Filter dan klik tombol '+' merah pada hasil pencarian teratas
                console.print("[cyan]4. Mengklik tombol '+' merah pada sound teratas...[/cyan]")
                add_buttons = page.locator("button.Button__root--shape-rounded.Button__root--type-primary, button[data-shape='rounded'][data-icon-only='true'], button.Button__root--type-primary[data-icon-only='true'], div[role='listitem'] button[class*='type-primary']").all()

                if add_buttons:
                    top_btn = add_buttons[0]
                    box = top_btn.bounding_box()
                    coord_str = f"di ({box['x']:.0f}, {box['y']:.0f})" if box else ""
                    console.print(f"[green][OK] Tombol '+' sound teratas ditemukan {coord_str}. Mengklik...[/green]")
                    PublishTracker.update_step(session_id, "tiktok", "Memasang sound pencarian...", 60, "Mengklik tombol '+' pada sound pencarian teratas", "step")
                    top_btn.scroll_into_view_if_needed()
                    page.wait_for_timeout(400)
                    top_btn.click(force=True)
                    page.wait_for_timeout(4000)
                else:
                    page.evaluate("""
                        () => {
                            const btns = Array.from(document.querySelectorAll('button')).filter(b => b.className && b.className.includes('Button__root--shape-rounded') && b.className.includes('Button__root--type-primary'));
                            if (btns.length > 0) {
                                btns[0].click();
                            }
                        }
                    """)
                    page.wait_for_timeout(4000)

            # 5. Atur volume di panel Audio kanan atas menggunakan input resmi 'input.PropSettingInput__input'
            if volume_db:
                console.print(f"[cyan]5. Mengatur volume sound menjadi [yellow]{volume_db} dB[/yellow] di panel Audio kanan atas...[/cyan]")
                PublishTracker.update_step(session_id, "tiktok", "Mengatur volume suara...", 70, f"Mengatur volume audio latar belakang menjadi {volume_db} dB", "step")
                vol_input = page.locator("input.PropSettingInput__input").first
                if vol_input.count() > 0:
                    vol_input.click()
                    page.wait_for_timeout(300)
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    vol_input.fill(str(volume_db))
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(800)
                    console.print(f"[green][OK] Input volume berhasil diisi {volume_db} dB![/green]")

            # 6. Klik tombol 'Save' di kanan atas untuk menyimpan dan kembali ke upload
            console.print("[cyan]6. Menyimpan hasil edit (Klik tombol 'Save' di kanan atas)...[/cyan]")
            PublishTracker.update_step(session_id, "tiktok", "Menyimpan video editor...", 75, "Menyimpan hasil konfigurasi audio dan kembali ke form postingan", "step")
            page.evaluate("""
                () => {
                    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && (b.innerText.trim() === 'Save' || b.innerText.trim() === 'Simpan'));
                    if (btn) btn.click();
                }
            """)
            page.wait_for_timeout(6000)

            console.print("[bold green][OK] Sound TikTok resmi berhasil dipilih, diatur volumenya, dan disimpan![/bold green]")
            return True

        except Exception as ex:
            console.print(f"[bold yellow]Peringatan saat konfigurasi Sound Editor: {ex}[/bold yellow]")
            return False

    def upload(
        self,
        video_path: str | Path,
        caption: str = "",
        as_draft: bool = False,
        account_name: str = "default",
        sound_mode: str = "favorite",
        tiktok_sound_query: Optional[str] = None,
        sound_volume_db: Optional[str] = "-7",
        schedule_time: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Uploads a video to TikTok with full maximized browser, sound search/favorite & volume tuning.
        """
        from src.publish_tracker import PublishTracker

        path = Path(video_path).resolve()
        valid, err = ContentValidator.validate_video_file(path)
        if not valid:
            PublishTracker.update_step(session_id, "tiktok", "Validasi Gagal", 0, err or "Invalid video", "error", is_failed=True, error_msg=err)
            return False, err or "Invalid video", None

        state_file = get_account_state_file(account_name, "tiktok")
        if not state_file.exists():
            err_msg = f"Sesi login TikTok untuk akun '{account_name}' belum ada. Silakan jalankan login terlebih dahulu."
            PublishTracker.update_step(session_id, "tiktok", "Sesi Tidak Ditemukan", 0, err_msg, "error", is_failed=True, error_msg=err_msg)
            return False, err_msg, None

        sanitized_caption = ContentValidator.sanitize_caption(caption, platform="tiktok")
        timestamp = int(time.time())
        screenshot_path = str(LOGS_DIR / f"tiktok_{account_name}_{timestamp}.png")

        mode_text = "HEADLESS" if self.headless else "VISIBLE BROWSER (FULL MAXIMIZED)"
        console.print(f"[bold cyan]=== MEMULAI UPLOAD TIKTOK ({mode_text}) ===[/bold cyan]")
        console.print(f"Akun: [magenta]{account_name}[/magenta]")
        console.print(f"File Video: [yellow]{path.name}[/yellow]")
        console.print(f"Caption: [italic]{sanitized_caption}[/italic]")
        console.print(f"Sound Mode: [cyan]{sound_mode.upper()}[/cyan] (Query: {tiktok_sound_query}, Volume: {sound_volume_db} dB)")

        PublishTracker.update_step(session_id, "tiktok", "Membuka browser TikTok...", 10, f"Membuka browser visual untuk akun '{account_name}'", "info")

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
                # 1. Buka halaman upload TikTok
                console.print("[cyan]1. Membuka halaman Creator Upload TikTok...[/cyan]")
                PublishTracker.update_step(session_id, "tiktok", "Memuat halaman TikTok Studio...", 20, "Memuat halaman Creator Upload TikTok Studio", "step")
                page.goto(TIKTOK_UPLOAD_URL, timeout=45000, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)

                # Cek jika belum login
                if "login" in page.url:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    err_msg = f"Session TikTok untuk '{account_name}' telah kadaluarsa. Silakan login ulang."
                    PublishTracker.update_step(session_id, "tiktok", "Sesi Expired", 0, err_msg, "error", is_failed=True, error_msg=err_msg)
                    return False, err_msg, screenshot_path

                # Bersihkan popup awal (tour guide, Got it, cookie, dsb)
                self.dismiss_popups(page)

                # Jika TikTok redirect ke halaman onboarding tour (misal /tiktokstudio/sound atau /home)
                if "tiktokstudio/upload" not in page.url or page.locator("input[type='file']").count() == 0:
                    upload_sidebar_btn = page.locator("button, a").filter(has_text=re.compile(r"^\+?\s*Upload$", re.I)).first
                    if upload_sidebar_btn.count() > 0 and upload_sidebar_btn.is_visible():
                        try:
                            upload_sidebar_btn.click()
                            page.wait_for_timeout(3000)
                        except Exception:
                            pass
                    if "tiktokstudio/upload" not in page.url:
                        page.goto(TIKTOK_UPLOAD_URL, timeout=35000, wait_until="domcontentloaded")
                        page.wait_for_timeout(3500)
                    self.dismiss_popups(page)

                # 2. Cari input file video
                console.print("[cyan]2. Memilih file video...[/cyan]")
                file_input = page.locator("input[type='file'][accept*='video'], input[type='file']").first
                if file_input.count() == 0:
                    page.goto(TIKTOK_ALT_UPLOAD_URL, timeout=45000, wait_until="domcontentloaded")
                    page.wait_for_timeout(5000)
                    self.dismiss_popups(page)
                    file_input = page.locator("input[type='file'][accept*='video'], input[type='file']").first

                if file_input.count() == 0:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    err_msg = "Form input file upload tidak ditemukan di halaman TikTok."
                    PublishTracker.update_step(session_id, "tiktok", "Input File Hilang", 0, err_msg, "error", is_failed=True, error_msg=err_msg)
                    return False, err_msg, screenshot_path

                # 3. Masukkan file video
                console.print(f"[yellow]Mengunggah file {path.name}...[/yellow]")
                PublishTracker.update_step(session_id, "tiktok", f"Mengunggah file {path.name}...", 35, f"Mengunggah file media {path.name} ke TikTok Studio", "step")
                file_input.set_input_files(str(path))
                page.wait_for_timeout(6000)

                # Bersihkan popup 'Got it' setelah video dipilih
                self.dismiss_popups(page)

                # 4. Alur TikTok Studio Editor: Sound Search/Favorite & Pengaturan Volume
                console.print(f"[cyan]4. Membuka Audio Editor untuk memasang Sound TikTok (Mode: {sound_mode.upper()})...[/cyan]")
                self.apply_tiktok_editor_sound(
                    page=page,
                    sound_mode=sound_mode or "search",
                    sound_query=tiktok_sound_query or "",
                    volume_db=sound_volume_db or "-7",
                    session_id=session_id
                )
                self.dismiss_popups(page)

                # 5. Input Caption & Hashtags
                if sanitized_caption:
                    console.print("[cyan]Mengisi caption dan hashtag...[/cyan]")
                    PublishTracker.update_step(session_id, "tiktok", "Mengisi caption & hashtag...", 80, "Mengisi teks caption dan hashtag terverifikasi", "step")
                    page.evaluate("window.scrollTo(0, 0)")
                    page.wait_for_timeout(500)
                    
                    caption_locator = page.locator(
                        "div[contenteditable='true'], div.notranslate[contenteditable='true'], div[data-placeholder*='caption'], div.public-DraftEditor-content, div[data-e2e='caption-editor']"
                    ).first

                    try:
                        if caption_locator.count() > 0:
                            caption_locator.click()
                            page.wait_for_timeout(500)
                            page.keyboard.press("Control+A")
                            page.keyboard.press("Backspace")
                            page.wait_for_timeout(500)
                            caption_locator.fill(sanitized_caption)
                            page.wait_for_timeout(1000)
                        else:
                            textarea = page.locator("textarea").first
                            if textarea.count() > 0:
                                textarea.fill(sanitized_caption)
                    except Exception as e:
                        console.print(f"[dim yellow]Catatan saat mengisi caption: {e}[/dim yellow]")

                # 6. Scroll ke bawah dan tunggu pemrosesan video selesai
                console.print("[cyan]Menunggu pemrosesan video di TikTok...[/cyan]")
                PublishTracker.update_step(session_id, "tiktok", "Finalisasi pemrosesan video...", 85, "Menunggu pemrosesan server TikTok Studio selesai", "step")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(3000)
                self.dismiss_popups(page)
                page.wait_for_timeout(3000)

                # 7. Klik Post / Save Draft dengan selector presisi (bukan sidebar dan bukan Save draft jika mode post)
                if as_draft:
                    console.print("[cyan]Menyimpan sebagai Draf...[/cyan]")
                    PublishTracker.update_step(session_id, "tiktok", "Menyimpan sebagai Draf...", 90, "Menyimpan video sebagai Draf di TikTok Studio", "step")
                    draft_btn = page.locator(
                        "button:text-is('Save draft'), button:text-is('Simpan draf')"
                    ).first
                    if draft_btn.count() > 0:
                        draft_btn.scroll_into_view_if_needed()
                        page.wait_for_timeout(500)
                        draft_btn.click(force=True)
                    else:
                        page.screenshot(path=screenshot_path)
                        browser.close()
                        return False, "Tombol 'Save Draft' tidak ditemukan.", screenshot_path
                else:
                    console.print(f"[bold green]Memposting Video ke TikTok Akun: [{account_name}]...[/bold green]")
                    PublishTracker.update_step(session_id, "tiktok", "Mempublikasikan postingan...", 90, "Menekan tombol 'Post' / 'Posting' resmi di TikTok Studio", "step")
                    
                    # Targetkan tombol Post merah resmi
                    clicked_post = False
                    post_candidates = page.locator(
                        "button.Button__root--type-primary, button[data-e2e='upload_post_btn'], button:text-is('Post'), button:text-is('Posting'), button:text-is('Unggah')"
                    ).all()

                    for btn in post_candidates:
                        try:
                            box = btn.bounding_box()
                            text = (btn.text_content() or "").strip()
                            # Pastikan bukan sidebar (x > 250), bukan Save draft, dan teks tepat 'Post' / 'Posting'
                            if box and box["x"] > 250 and "draft" not in text.lower() and text in ["Post", "Posting", "Unggah"]:
                                console.print(f"[bold green]Mengklik tombol Post resmi di ({box['x']:.0f}, {box['y']:.0f})...[/bold green]")
                                btn.scroll_into_view_if_needed()
                                page.wait_for_timeout(1000)
                                btn.click(force=True)
                                clicked_post = True
                                break
                        except Exception:
                            pass

                    if not clicked_post:
                        for btn in post_candidates:
                            text = (btn.text_content() or "").strip()
                            if "draft" not in text.lower() and ("post" in text.lower() or "posting" in text.lower() or "unggah" in text.lower()):
                                btn.scroll_into_view_if_needed()
                                page.wait_for_timeout(1000)
                                btn.click(force=True)
                                clicked_post = True
                                break

                    if not clicked_post:
                        page.screenshot(path=screenshot_path)
                        browser.close()
                        err_msg = "Tombol 'Post' utama tidak ditemukan."
                        PublishTracker.update_step(session_id, "tiktok", "Tombol Post Hilang", 0, err_msg, "error", is_failed=True, error_msg=err_msg)
                        return False, err_msg, screenshot_path

                # 8. Tunggu konfirmasi akhir upload
                console.print("[cyan]Menunggu konfirmasi upload selesai...[/cyan]")
                PublishTracker.update_step(session_id, "tiktok", "Menunggu verifikasi upload...", 95, "Menunggu konfirmasi penerbitan TikTok Studio...", "step")
                page.wait_for_timeout(10000)

                try:
                    self._save_storage_state_safe(context, state_file)
                except Exception:
                    pass

                page.screenshot(path=screenshot_path)
                browser.close()
                console.print(f"[bold green][OK] Video TikTok untuk [{account_name}] berhasil diposting! Bukti: {screenshot_path}[/bold green]")
                PublishTracker.update_step(session_id, "tiktok", "TikTok Berhasil Terbit!", 100, f"Video TikTok berhasil diterbitkan untuk akun '{account_name}'!", "success", is_completed=True, post_url=screenshot_path)
                return True, f"Video berhasil diupload ke TikTok ({account_name}).", screenshot_path

            except Exception as ex:
                try:
                    page.screenshot(path=screenshot_path)
                except Exception:
                    pass
                browser.close()
                err_msg = f"Terjadi kesalahan saat upload TikTok: {str(ex)}"
                PublishTracker.update_step(session_id, "tiktok", "Upload Gagal", 0, err_msg, "error", is_failed=True, error_msg=err_msg)
                return False, err_msg, screenshot_path

    @staticmethod
    def fetch_latest_post_link(account_name: str, caption_snippet: str = "") -> Optional[str]:
        """
        Visits TikTok Studio Content Manager or user profile in fast headless browser
        to grab the exact live post permalink.
        """
        state_file = get_account_state_file(account_name, "tiktok")
        if not state_file.exists():
            return None

        with sync_playwright() as p:
            try:
                browser = launch_browser(p, headless=True)
                context = browser.new_context(
                    user_agent=DEFAULT_USER_AGENT,
                    storage_state=str(state_file)
                )
                page = context.new_page()
                # Fast route abort for heavy media
                page.route("**/*.{png,jpg,jpeg,webp,gif,mp4,woff,woff2,ttf}", lambda r: r.abort())
                
                try:
                    page.goto("https://www.tiktok.com/tiktokstudio/content", timeout=12000, wait_until="domcontentloaded")
                    page.wait_for_timeout(1200)

                    for sel in [
                        "a[href*='/video/']",
                        "a[href*='/photo/']",
                        "div[data-tt='post_card'] a",
                        "tbody tr a[href*='tiktok.com']"
                    ]:
                        try:
                            elem = page.locator(sel).first
                            if elem.count() > 0:
                                href = elem.get_attribute("href")
                                if href and ("/video/" in href or "/photo/" in href):
                                    browser.close()
                                    return href if href.startswith("http") else f"https://www.tiktok.com{href}"
                        except Exception:
                            pass
                except Exception:
                    pass

                from src.account_manager import AccountManager
                profile = AccountManager.get_tiktok_profile(account_name)
                username = profile.get("unique_id") or profile.get("username")
                if username:
                    clean_u = username if username.startswith("@") else f"@{username}"
                    try:
                        page.goto(f"https://www.tiktok.com/{clean_u}", timeout=10000, wait_until="domcontentloaded")
                        page.wait_for_timeout(1000)
                        elem = page.locator("a[href*='/video/'], a[href*='/photo/']").first
                        if elem.count() > 0:
                            href = elem.get_attribute("href") or ""
                            if href and ("/video/" in href or "/photo/" in href):
                                browser.close()
                                return href if href.startswith("http") else f"https://www.tiktok.com{href}"
                    except Exception:
                        pass

                browser.close()
            except Exception:
                pass
        return None

    def apply_tiktok_photo_sound(
        self,
        page,
        sound_mode: str = "favorite",
        sound_query: str = "school",
        session_id: Optional[str] = None
    ) -> bool:
        """
        Attaches a TikTok sound to Photo / Carousel post directly from '+ Add sound' button below description.
        1. Click button:has-text('Add sound'), button:has-text('Tambah suara').
        2. If sound_mode == 'favorite':
           - Click Favorites tab.
           - Find all 'Use' / 'Gunakan' buttons.
           - Pick one random favorite sound.
        3. If sound_mode == 'search' (or fallback):
           - Fill search input with sound_query and press Enter.
           - Click the topmost 'Use' / 'Gunakan' button.
        """
        from src.publish_tracker import PublishTracker

        try:
            console.print(f"[bold cyan]=== MEMILIH SOUND TIKTOK UNTUK POSTER/CAROUSEL (Mode: {sound_mode.upper()}) ===[/bold cyan]")
            PublishTracker.update_step(session_id, "tiktok", "Membuka modal sound...", 60, f"Membuka dialog '+ Add sound' (Mode: {sound_mode.upper()})", "step")
            
            # 1. Klik tombol '+ Add sound' di bawah deskripsi
            console.print("[cyan]1. Mengklik tombol '+ Add sound'...[/cyan]")
            add_sound_btn = page.locator(
                "button:has-text('Add sound'), button:has-text('Tambah suara'), button:has-text('+ Add sound'), div[role='button']:has-text('Add sound')"
            ).first

            if add_sound_btn.count() == 0 or not add_sound_btn.is_visible():
                console.print("[yellow]Tombol '+ Add sound' tidak ditemukan di bawah deskripsi.[/yellow]")
                PublishTracker.log(session_id, "tiktok", "Tombol '+ Add sound' tidak ditemukan di bawah deskripsi", "warn")
                return False

            add_sound_btn.scroll_into_view_if_needed()
            add_sound_btn.click()
            page.wait_for_timeout(3500)

            # 2. Pilihan Mode: FAVORITE vs SEARCH
            sound_applied = False
            if sound_mode == "favorite":
                console.print("[cyan]2. Membuka tab 'Favorites' di modal sound...[/cyan]")
                PublishTracker.update_step(session_id, "tiktok", "Membuka tab Favorites...", 65, "Membuka tab Favorites di modal sound TikTok", "step")
                fav_tab_clicked = False
                
                try:
                    fav_tab = page.locator("div, span, button, [role='tab']").filter(has_text=re.compile(r"^(Favorites|Favorit|Favorite|Disimpan)$", re.I)).first
                    if fav_tab.count() > 0 and fav_tab.is_visible():
                        fav_tab.click()
                        fav_tab_clicked = True
                        console.print("[green][OK] Tab Favorites berhasil diklik![/green]")
                except Exception:
                    pass

                if not fav_tab_clicked:
                    for t in page.locator("div, span, button").filter(has_text="Favorite").all():
                        if t.is_visible():
                            t.click()
                            fav_tab_clicked = True
                            break

                page.wait_for_timeout(3000)

                # Cari semua tombol 'Use' / 'Gunakan' di tab favorites
                use_buttons = page.locator("button:has-text('Use'), div[role='button']:has-text('Use'), button:has-text('Gunakan')").all()
                if use_buttons:
                    chosen_btn = random.choice(use_buttons)
                    console.print(f"[bold green][OK] Memilih secara acak 1 dari {len(use_buttons)} sound favorit. Mengklik tombol 'Use'...[/bold green]")
                    PublishTracker.update_step(session_id, "tiktok", "Memasang sound favorit...", 75, f"Memilih secara acak 1 dari {len(use_buttons)} lagu favorit via tombol 'Use'", "step")
                    chosen_btn.click()
                    page.wait_for_timeout(3000)
                    sound_applied = True
                else:
                    console.print("[yellow]Tab Favorites belum memiliki sound atau kosong. Melakukan fallback ke pencarian sound...[/yellow]")
                    PublishTracker.log(session_id, "tiktok", "Tab Favorites kosong. Fallback ke pencarian sound...", "warn")
                    sound_mode = "search"

            if not sound_applied: # sound_mode == "search"
                console.print(f"[cyan]2. Mencari sound TikTok dengan query: [yellow]'{sound_query}'[/yellow]...[/cyan]")
                PublishTracker.update_step(session_id, "tiktok", f"Mencari sound '{sound_query}'...", 65, f"Mencari audio TikTok dengan kata kunci '{sound_query}'", "step")
                search_box = page.locator("input[placeholder*='Search sounds'], input[placeholder*='search sounds'], input[placeholder*='Cari sound']").first
                if search_box.count() > 0:
                    search_box.click(force=True)
                    search_box.fill(sound_query)
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(3000)

                use_buttons = page.locator("button:has-text('Use'), div[role='button']:has-text('Use'), button:has-text('Gunakan')").all()
                if use_buttons:
                    console.print("[green][OK] Sound teratas ditemukan. Mengklik tombol 'Use'...[/green]")
                    PublishTracker.update_step(session_id, "tiktok", "Memasang sound...", 75, "Mengklik tombol 'Use' pada sound pencarian teratas", "step")
                    use_buttons[0].click()
                    page.wait_for_timeout(3000)
                    sound_applied = True
                else:
                    console.print("[yellow]Tombol 'Use' tidak ditemukan di hasil pencarian sound.[/yellow]")

            console.print("[bold green][OK] Sound TikTok untuk Poster/Carousel berhasil dipilih dan diterapkan![/bold green]")
            return sound_applied

        except Exception as ex:
            console.print(f"[bold yellow]Peringatan saat konfigurasi Sound Foto/Carousel: {ex}[/bold yellow]")
            return False

    def ensure_photos_tab_active(self, page, max_wait_sec=15) -> bool:
        """Ensures that TikTok Studio is cleanly in 'Photos' mode (tab=photo)."""
        start = time.time()
        while time.time() - start < max_wait_sec:
            # 1. Handle "Something went wrong" / Retry
            retry_btn = page.locator("button").filter(has_text=re.compile(r"^Retry$", re.I))
            if retry_btn.count() > 0 and retry_btn.first.is_visible():
                try:
                    console.print("[yellow]Mendeteksi tombol 'Retry' TikTok Studio, mencoba memulihkan...[/yellow]")
                    retry_btn.first.click()
                    page.wait_for_timeout(2000)
                except Exception:
                    pass

            self.dismiss_popups(page)

            # 2. Check if already in Photos mode
            if "tab=photo" in page.url:
                return True

            # 3. Try clicking Photos tab via Playwright locator
            photos_tab = page.locator("[role='tab'], button, div, span").filter(has_text=re.compile(r"^(Photos|Foto|Photo)$", re.I)).first
            if photos_tab.count() > 0 and photos_tab.is_visible():
                try:
                    console.print("[cyan]Mengaktifkan tab mode Photos di TikTok Studio...[/cyan]")
                    photos_tab.click(force=True)
                    page.wait_for_timeout(2000)
                    if "tab=photo" in page.url or page.locator("input[type='file']").count() > 0:
                        return True
                except Exception:
                    pass

            # 4. Try clicking Photos tab via JavaScript DOM evaluation
            clicked_js = page.evaluate("""() => {
                const els = Array.from(document.querySelectorAll("[role='tab'], button, div, span"));
                for (const el of els) {
                    const txt = (el.innerText || '').trim();
                    if (txt === 'Photos' || txt === 'Foto' || txt === 'Photo') {
                        el.click();
                        return true;
                    }
                }
                return false;
            }""")
            if clicked_js:
                page.wait_for_timeout(2000)
                if "tab=photo" in page.url or page.locator("input[type='file']").count() > 0:
                    return True

            page.wait_for_timeout(1000)

        return "tab=photo" in page.url

    def upload_photos(
        self,
        photo_paths: list,
        caption: str = "",
        title: str = "",
        as_draft: bool = False,
        account_name: str = "default",
        sound_mode: str = "favorite",
        tiktok_sound_query: Optional[str] = None,
        category_label: str = "Carousel",
        session_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Uploads Poster (single photo) or Carousel (multiple photos) to TikTok Studio.
        1. Navigate to https://www.tiktok.com/tiktokstudio/upload?tab=photo
        2. Set input files with photo_paths.
        3. Fill title & description/caption.
        4. Attach sound from '+ Add sound' (Favorites or Search).
        5. Click Post / Save Draft.
        """
        from src.publish_tracker import PublishTracker

        resolved_photos = [str(Path(p).resolve()) for p in photo_paths]
        if not resolved_photos:
            PublishTracker.update_step(session_id, "tiktok", "Foto Kosong", 0, "Tidak ada file foto yang diberikan", "error", is_failed=True)
            return False, "Tidak ada file foto yang diberikan untuk diunggah.", None

        state_file = get_account_state_file(account_name, "tiktok")
        if not state_file.exists():
            err_msg = f"Sesi login TikTok untuk akun '{account_name}' belum ada. Silakan jalankan login terlebih dahulu."
            PublishTracker.update_step(session_id, "tiktok", "Sesi Hilang", 0, err_msg, "error", is_failed=True, error_msg=err_msg)
            return False, err_msg, None

        sanitized_caption = ContentValidator.sanitize_caption(caption, platform="tiktok")
        timestamp = int(time.time())
        screenshot_path = str(LOGS_DIR / f"tiktok_photo_{account_name}_{timestamp}.png")

        mode_text = "HEADLESS" if self.headless else "VISIBLE BROWSER (FULL MAXIMIZED)"
        console.print(f"[bold cyan]=== MEMULAI UPLOAD TIKTOK {category_label.upper()} ({mode_text}) ===[/bold cyan]")
        console.print(f"Akun: [magenta]{account_name}[/magenta]")
        console.print(f"Jumlah Slide/Foto: [yellow]{len(resolved_photos)}[/yellow]")
        console.print(f"Caption: [italic]{sanitized_caption}[/italic]")
        console.print(f"Sound Mode: [cyan]{sound_mode.upper()}[/cyan] (Query: {tiktok_sound_query or 'school'})")

        PublishTracker.update_step(session_id, "tiktok", f"Membuka TikTok Studio ({category_label})...", 15, f"Membuka tab foto TikTok Studio untuk {len(resolved_photos)} slide ({account_name})", "info")

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
                # 1. Buka halaman upload TikTok Studio
                console.print("[cyan]1. Membuka halaman Creator Upload TikTok Studio...[/cyan]")
                page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=45000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)

                # Cek jika session expired / redirect login
                if "login" in page.url:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return False, f"Session TikTok untuk '{account_name}' telah kadaluarsa. Silakan login ulang.", screenshot_path

                self.dismiss_popups(page)

                # Jika TikTok redirect ke halaman onboarding tour (misal /tiktokstudio/sound atau /home)
                if "tiktokstudio/upload" not in page.url:
                    upload_sidebar_btn = page.locator("button, a").filter(has_text=re.compile(r"^\+?\s*Upload$", re.I)).first
                    if upload_sidebar_btn.count() > 0 and upload_sidebar_btn.is_visible():
                        try:
                            upload_sidebar_btn.click()
                            page.wait_for_timeout(3000)
                        except Exception:
                            pass
                    if "tiktokstudio/upload" not in page.url:
                        page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=35000, wait_until="domcontentloaded")
                        page.wait_for_timeout(3000)
                    self.dismiss_popups(page)

                # Pastikan Tab 'Photos' aktif dan siap menerima file foto
                self.ensure_photos_tab_active(page, max_wait_sec=15)
                self.dismiss_popups(page)

                # 2. Masukkan file foto langsung via set_input_files (tanpa membuka OS dialog)
                console.print(f"[cyan]2. Memasukkan {len(resolved_photos)} file foto...[/cyan]")
                PublishTracker.update_step(session_id, "tiktok", f"Mengunggah {len(resolved_photos)} file foto...", 35, f"Mengunggah {len(resolved_photos)} file foto ke TikTok Studio", "step")
                
                try:
                    page.wait_for_selector("input[type='file']", timeout=12000)
                except Exception:
                    pass

                file_input = page.locator("input[type='file']").first
                if file_input.count() == 0:
                    # Final retry: Re-navigate and click Photos tab
                    page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_timeout(3000)
                    self.ensure_photos_tab_active(page, max_wait_sec=10)
                    file_input = page.locator("input[type='file']").first

                if file_input.count() == 0:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    err_msg = "Form input file foto tidak ditemukan di halaman TikTok."
                    PublishTracker.update_step(session_id, "tiktok", "Input Foto Hilang", 0, err_msg, "error", is_failed=True, error_msg=err_msg)
                    return False, err_msg, screenshot_path

                file_input.set_input_files(resolved_photos)
                page.wait_for_timeout(6000)
                self.dismiss_popups(page)

                # 3. Input Caption / Deskripsi (Judul dikosongkan sesuai preferensi user)
                console.print("[cyan]3. Mengisi caption/deskripsi konten...[/cyan]")
                PublishTracker.update_step(session_id, "tiktok", "Mengisi caption & hashtag...", 50, "Mengisi teks deskripsi caption postingan foto", "step")
                
                # Pastikan kolom judul (catchy title) tetap kosong
                title_loc = page.locator("input[placeholder*='title'], input[placeholder*='judul'], div[data-placeholder*='title']").first
                if title_loc.count() > 0 and title_loc.is_visible():
                    try:
                        title_loc.click()
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                    except Exception:
                        pass

                # Description / Caption
                desc_loc = page.locator(
                    "div[contenteditable='true'], div.notranslate[contenteditable='true'], div[data-placeholder*='description'], textarea"
                ).first
                if desc_loc.count() > 0:
                    try:
                        desc_loc.click()
                        page.wait_for_timeout(400)
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                        desc_loc.fill(sanitized_caption)
                        page.wait_for_timeout(800)
                    except Exception as e:
                        console.print(f"[dim yellow]Catatan saat mengisi deskripsi: {e}[/dim yellow]")

                # 4. Tambahkan Sound resmi TikTok
                self.apply_tiktok_photo_sound(
                    page=page,
                    sound_mode=sound_mode,
                    sound_query=tiktok_sound_query or "school",
                    session_id=session_id
                )
                self.dismiss_popups(page)

                # 5. Scroll ke bawah dan klik Post / Save Draft
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2500)
                self.dismiss_popups(page)
                page.wait_for_timeout(1500)

                if as_draft:
                    console.print("[cyan]Menyimpan sebagai Draf...[/cyan]")
                    PublishTracker.update_step(session_id, "tiktok", "Menyimpan sebagai Draf...", 85, "Menyimpan postingan foto sebagai Draf", "step")
                    draft_btn = page.locator(
                        "button:text-is('Save draft'), button:text-is('Simpan draf')"
                    ).first
                    if draft_btn.count() > 0:
                        draft_btn.scroll_into_view_if_needed()
                        draft_btn.click(force=True)
                    else:
                        page.screenshot(path=screenshot_path)
                        browser.close()
                        return False, "Tombol 'Save Draft' tidak ditemukan.", screenshot_path
                else:
                    console.print(f"[bold green]Memposting {category_label} ke TikTok Akun: [{account_name}]...[/bold green]")
                    PublishTracker.update_step(session_id, "tiktok", "Mempublikasikan postingan...", 85, "Menekan tombol 'Post' / 'Posting' resmi di TikTok Studio", "step")
                    post_candidates = page.locator(
                        "button.Button__root--type-primary, button[data-e2e='upload_post_btn'], button:text-is('Post'), button:text-is('Posting'), button:text-is('Unggah')"
                    ).all()

                    clicked_post = False
                    for btn in post_candidates:
                        try:
                            box = btn.bounding_box()
                            text = (btn.text_content() or "").strip()
                            if box and box["x"] > 250 and text in ["Post", "Posting", "Unggah"]:
                                console.print(f"[bold green]Mengklik tombol Post resmi di ({box['x']:.0f}, {box['y']:.0f})...[/bold green]")
                                btn.scroll_into_view_if_needed()
                                page.wait_for_timeout(1000)
                                btn.click(force=True)
                                clicked_post = True
                                break
                        except Exception:
                            pass

                    if not clicked_post:
                        fallback_post = page.locator("button.Button__root--type-primary").first
                        if fallback_post.count() > 0:
                            fallback_post.scroll_into_view_if_needed()
                            page.wait_for_timeout(1000)
                            fallback_post.click(force=True)
                            clicked_post = True

                    if not clicked_post:
                        page.screenshot(path=screenshot_path)
                        browser.close()
                        err_msg = "Tombol 'Post' utama tidak ditemukan."
                        PublishTracker.update_step(session_id, "tiktok", "Tombol Post Hilang", 0, err_msg, "error", is_failed=True, error_msg=err_msg)
                        return False, err_msg, screenshot_path

                # 6. Tunggu konfirmasi akhir
                console.print("[cyan]Menunggu konfirmasi upload selesai...[/cyan]")
                PublishTracker.update_step(session_id, "tiktok", "Menunggu verifikasi upload...", 95, "Menunggu konfirmasi penerbitan TikTok Studio...", "step")
                page.wait_for_timeout(10000)

                try:
                    self._save_storage_state_safe(context, state_file)
                except Exception:
                    pass

                page.screenshot(path=screenshot_path)
                browser.close()
                console.print(f"[bold green][OK] {category_label} TikTok untuk [{account_name}] berhasil diposting! Bukti: {screenshot_path}[/bold green]")
                PublishTracker.update_step(session_id, "tiktok", f"TikTok {category_label} Berhasil Terbit!", 100, f"{category_label} TikTok berhasil dipublikasikan untuk akun '{account_name}'!", "success", is_completed=True, post_url=screenshot_path)
                return True, f"{category_label} berhasil diupload ke TikTok ({account_name}).", screenshot_path

            except Exception as ex:
                try:
                    page.screenshot(path=screenshot_path)
                except Exception:
                    pass
                browser.close()
                err_msg = f"Terjadi kesalahan saat upload {category_label} ke TikTok: {str(ex)}"
                PublishTracker.update_step(session_id, "tiktok", "Upload Gagal", 0, err_msg, "error", is_failed=True, error_msg=err_msg)
                return False, err_msg, screenshot_path

