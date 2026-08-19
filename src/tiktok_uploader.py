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
    launch_browser
)
from src.validator import ContentValidator

console = Console(highlight=False)

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

    def dismiss_popups(self, page, target=None):
        """Dismiss all common TikTok guide tours, cookie dialogs, and announcement modals."""
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass

        popup_selectors = [
            "button:has-text('Got it')",
            "button:has-text('Mengerti')",
            "button:has-text('Accept')",
            "button:has-text('Setuju')",
            "button:has-text('I understand')",
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
                    btn.click(timeout=1500)
                    page.wait_for_timeout(400)
            except Exception:
                pass

            if target and target != page:
                try:
                    btn = target.locator(sel).first
                    if btn.count() > 0 and btn.is_visible():
                        btn.click(timeout=1500)
                        page.wait_for_timeout(400)
                except Exception:
                    pass

    def apply_tiktok_editor_sound(
        self,
        page,
        sound_mode: str = "search",
        sound_query: str = "school",
        volume_db: Optional[str] = "-7"
    ) -> bool:
        """
        Full workflow for TikTok Studio Video & Audio Editor:
        1. Click button.editor-entrance[data-button-name='sounds'] under preview.
        2. Dismiss 'Phone mode' modal.
        3. If sound_mode == 'favorite':
           - Click Favorites / Favorit tab with precision selectors.
           - Pick one random favorite sound card from the list.
        4. If sound_mode == 'search' (or favorite fallback):
           - Fill input[placeholder*='Search sounds'], press Enter.
           - Pick topmost sound card.
        5. Set volume in dB (e.g. -7 dB) in input.PropSettingInput__input on the top-right Audio panel.
        6. Click 'Save' in top right to apply and return to upload form.
        """
        try:
            console.print(f"[bold cyan]=== MEMBUKA TIKTOK STUDIO AUDIO & SOUND EDITOR (Mode: {sound_mode.upper()}) ===[/bold cyan]")
            
            # Scroll ke paling atas agar tombol editor di bawah preview terlihat
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(1000)

            # 1. Klik tombol Sounds di bawah preview video
            console.print("[cyan]1. Mengklik tombol 'Sounds' di bawah preview video...[/cyan]")
            sounds_btn = page.locator("button.editor-entrance[data-button-name='sounds'], button[data-button-name='sounds']").first
            if sounds_btn.count() == 0:
                candidate_btns = page.locator("button, div[role='button']").filter(has_text="Sounds").all()
                for b in candidate_btns:
                    box = b.bounding_box()
                    if box and box["x"] > 600 and box["y"] > 200:
                        sounds_btn = b
                        break

            if sounds_btn.count() > 0:
                sounds_btn.scroll_into_view_if_needed()
                sounds_btn.click()
                page.wait_for_timeout(4500)
            else:
                console.print("[yellow]Tombol Sounds tidak ditemukan di bawah preview.[/yellow]")
                return False

            # 2. Tutup popup modal 'Phone mode' / dialog di dalam editor jika muncul
            console.print("[cyan]2. Menutup dialog petunjuk di dalam editor...[/cyan]")
            for _ in range(3):
                modal_btn = page.locator("button:has-text('Got it'), button:has-text('Mengerti'), button:has-text('I understand')").first
                if modal_btn.count() > 0 and modal_btn.is_visible():
                    modal_btn.click()
                    page.wait_for_timeout(800)
                self.dismiss_popups(page)

            # 3. Pilihan Mode: FAVORITE (RANDOM) vs SEARCH
            sound_applied = False
            if sound_mode == "favorite":
                console.print("[cyan]3. Membuka tab 'Favorites' / 'Favorit' sound...[/cyan]")
                fav_tab_clicked = False
                
                # Strategi 1: Role tab dengan regex nama favorit
                try:
                    for rt in page.locator("[role='tab']").all():
                        txt = rt.inner_text().strip()
                        if re.search(r"favorit|favorite|disimpan", txt, re.I):
                            rt.scroll_into_view_if_needed()
                            rt.click(force=True)
                            fav_tab_clicked = True
                            console.print(f"[green]✓ Tab Favorites ditemukan via role=tab ('{txt}') dan berhasil diklik![/green]")
                            break
                except Exception:
                    pass

                # Strategi 2: Text matching pada tombol/div tab spesifik di area drawer kiri
                if not fav_tab_clicked:
                    for tag in ["button", "span", "div", "p"]:
                        try:
                            matches = page.locator(tag).filter(has_text=re.compile(r"^(Favorites|Favorit|Favorite|Disimpan)$", re.I)).all()
                            for m in matches:
                                box = m.bounding_box()
                                if box and box["x"] < 400 and box["y"] < 250 and box["width"] < 200 and box["height"] < 60:
                                    m.scroll_into_view_if_needed()
                                    m.click(force=True)
                                    fav_tab_clicked = True
                                    console.print(f"[green]✓ Tab Favorites ditemukan via text '{tag}' di ({box['x']:.0f}, {box['y']:.0f}) dan berhasil diklik![/green]")
                                    break
                            if fav_tab_clicked:
                                break
                        except Exception:
                            pass

                # Strategi 3: Filter elemen yang memuat 'favorit' di koordinat tab atas drawer
                if not fav_tab_clicked:
                    try:
                        candidate_elements = page.locator("div, span, button").filter(has_text=re.compile(r"favorit", re.I)).all()
                        for elem in candidate_elements:
                            box = elem.bounding_box()
                            if box and box["x"] < 400 and box["y"] < 250 and box["width"] < 200 and box["height"] < 60:
                                page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                                fav_tab_clicked = True
                                console.print(f"[green]✓ Tab Favorites diklik via koordinat mouse ({box['x'] + box['width']/2:.0f}, {box['y'] + box['height']/2:.0f})![/green]")
                                break
                    except Exception:
                        pass

                page.wait_for_timeout(3500)

                # Cari semua item lagu yang muncul di tab Favorites
                console.print("[cyan]Mendeteksi daftar lagu di tab Favorites...[/cyan]")
                sound_cards = []
                
                # Cek elemen sound card di panel kiri
                candidates = page.locator("div[class*='item'], div[class*='Item'], div[class*='card'], div[class*='Card'], div:has(> img)").all()
                for c in candidates:
                    try:
                        box = c.bounding_box()
                        if box and box["x"] >= 10 and box["x"] < 450 and box["y"] >= 120 and box["y"] < 800 and box["height"] >= 35 and box["height"] <= 90 and box["width"] >= 180:
                            sound_cards.append(box)
                    except Exception:
                        pass

                # Fallback pencarian dengan durasi
                if not sound_cards:
                    duration_elems = page.locator("div, span, p").filter(has_text=re.compile(r"0[0-9]:[0-5][0-9]")).all()
                    for de in duration_elems:
                        try:
                            box = de.bounding_box()
                            if box and box["x"] >= 10 and box["x"] < 450 and box["y"] >= 120 and box["y"] < 800:
                                sound_cards.append(box)
                        except Exception:
                            pass

                if sound_cards:
                    chosen_box = random.choice(sound_cards)
                    hover_x = chosen_box["x"] + chosen_box["width"] / 2
                    hover_y = chosen_box["y"] + chosen_box["height"] / 2
                    page.mouse.move(hover_x, hover_y)
                    page.wait_for_timeout(400)

                    target_x = chosen_box["x"] + chosen_box["width"] - 22
                    target_y = chosen_box["y"] + (chosen_box["height"] / 2)
                    console.print(f"[bold green]✓ Berhasil memilih 1 sound favorit secara acak (dari {len(sound_cards)} lagu). Mengklik tombol '+' di ({target_x:.0f}, {target_y:.0f})...[/bold green]")
                    page.mouse.click(target_x, target_y)
                    page.wait_for_timeout(4000)
                    sound_applied = True
                else:
                    console.print("[yellow]Tab Favorites belum memiliki daftar lagu atau akun belum menyimpan sound favorit di TikTok. Melakukan fallback ke pencarian sound...[/yellow]")
                    sound_mode = "search"

            if not sound_applied: # sound_mode == "search"
                # Cari sound di kolom 'Search sounds'
                console.print(f"[cyan]3. Mencari sound TikTok dengan query: [yellow]'{sound_query}'[/yellow]...[/cyan]")
                search_box = page.locator("input[placeholder*='Search sounds'], input[placeholder*='search sounds'], input[placeholder*='Cari sound']").first
                if search_box.count() > 0:
                    search_box.click(force=True)
                    search_box.fill(sound_query)
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(3000)

                # Filter dan urutkan card lagu individual
                console.print("[cyan]4. Mengklik tombol '+' pada sound paling atas...[/cyan]")
                candidates = page.locator("div:has(> img), div:has-text('00:'), div:has-text('01:'), div:has-text('02:')").all()
                valid_items = []
                for c in candidates:
                    try:
                        box = c.bounding_box()
                        if box and box["x"] >= 10 and box["x"] < 450 and box["y"] >= 150 and box["height"] >= 35 and box["height"] <= 90 and box["width"] >= 180:
                            valid_items.append(box)
                    except Exception:
                        pass

                if valid_items:
                    valid_items.sort(key=lambda b: b["y"])
                    top_box = valid_items[0]
                    target_x = top_box["x"] + top_box["width"] - 22
                    target_y = top_box["y"] + (top_box["height"] / 2)
                    console.print(f"[green]✓ Sound teratas ditemukan (Y={top_box['y']:.1f}). Mengklik '+' di ({target_x:.1f}, {target_y:.1f})...[/green]")
                    page.mouse.move(target_x, target_y)
                    page.wait_for_timeout(300)
                    page.mouse.click(target_x, target_y)
                    page.wait_for_timeout(4000)
                else:
                    console.print("[yellow]Fallback click tombol '+'...[/yellow]")
                    page.mouse.click(270, 230)
                    page.wait_for_timeout(4000)

            # 5. Atur volume di panel Audio kanan atas menggunakan input resmi 'input.PropSettingInput__input'
            if volume_db:
                console.print(f"[cyan]5. Mengatur volume sound menjadi [yellow]{volume_db} dB[/yellow] di panel Audio kanan atas...[/cyan]")
                vol_input = page.locator("input.PropSettingInput__input").first
                if vol_input.count() > 0:
                    vol_input.click()
                    page.wait_for_timeout(300)
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    vol_input.fill(str(volume_db))
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(800)
                    console.print(f"[green]✓ Input volume berhasil diisi {volume_db} dB![/green]")

            # 6. Klik tombol 'Save' di kanan atas untuk menyimpan dan kembali ke upload
            console.print("[cyan]6. Menyimpan hasil edit (Klik tombol 'Save' di kanan atas)...[/cyan]")
            save_btn = page.locator("button:has-text('Save'), button:has-text('Simpan')").first
            if save_btn.count() > 0 and save_btn.is_visible():
                save_btn.click()
                page.wait_for_timeout(5000)

            console.print("[bold green]✓ Sound TikTok resmi berhasil dipilih, diatur volumenya, dan disimpan![/bold green]")
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
        sound_mode: str = "search",
        tiktok_sound_query: Optional[str] = None,
        sound_volume_db: Optional[str] = "-7",
        schedule_time: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Uploads a video to TikTok with full maximized browser, sound search/favorite & volume tuning.
        """
        path = Path(video_path).resolve()
        valid, err = ContentValidator.validate_video_file(path)
        if not valid:
            return False, err or "Invalid video", None

        state_file = get_account_state_file(account_name, "tiktok")
        if not state_file.exists():
            return False, f"Sesi login TikTok untuk akun '{account_name}' belum ada. Silakan jalankan login terlebih dahulu.", None

        sanitized_caption = ContentValidator.sanitize_caption(caption, platform="tiktok")
        timestamp = int(time.time())
        screenshot_path = str(LOGS_DIR / f"tiktok_{account_name}_{timestamp}.png")

        mode_text = "HEADLESS" if self.headless else "VISIBLE BROWSER (FULL MAXIMIZED)"
        console.print(f"[bold cyan]=== MEMULAI UPLOAD TIKTOK ({mode_text}) ===[/bold cyan]")
        console.print(f"Akun: [magenta]{account_name}[/magenta]")
        console.print(f"File Video: [yellow]{path.name}[/yellow]")
        console.print(f"Caption: [italic]{sanitized_caption}[/italic]")
        console.print(f"Sound Mode: [cyan]{sound_mode.upper()}[/cyan] (Query: {tiktok_sound_query}, Volume: {sound_volume_db} dB)")

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
                # 1. Buka halaman upload TikTok
                console.print("[cyan]1. Membuka halaman Creator Upload TikTok...[/cyan]")
                page.goto(TIKTOK_UPLOAD_URL, timeout=45000, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)

                # Cek jika belum login
                if "login" in page.url:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return False, f"Session TikTok untuk '{account_name}' telah kadaluarsa. Silakan login ulang.", screenshot_path

                # Bersihkan popup awal (tour guide, Got it, cookie, dsb)
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
                    return False, "Form input file upload tidak ditemukan di halaman TikTok.", screenshot_path

                # 3. Masukkan file video
                console.print(f"[yellow]Mengunggah file {path.name}...[/yellow]")
                file_input.set_input_files(str(path))
                page.wait_for_timeout(6000)

                # Bersihkan popup 'Got it' setelah video dipilih
                self.dismiss_popups(page)

                # 4. Alur TikTok Studio Editor: Sound Search/Favorite & Pengaturan Volume
                if sound_mode == "favorite" or tiktok_sound_query:
                    self.apply_tiktok_editor_sound(
                        page=page,
                        sound_mode=sound_mode,
                        sound_query=tiktok_sound_query or "school",
                        volume_db=sound_volume_db
                    )
                    self.dismiss_popups(page)

                # 5. Input Caption & Hashtags
                if sanitized_caption:
                    console.print("[cyan]Mengisi caption dan hashtag...[/cyan]")
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
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(5000)

                # 7. Klik Post / Save Draft dengan selector presisi (bukan sidebar)
                if as_draft:
                    console.print("[cyan]Menyimpan sebagai Draf...[/cyan]")
                    draft_btn = page.locator(
                        "button.Button__root:text-is('Save draft'), button:text-is('Save draft'), button:text-is('Simpan draf')"
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
                    
                    # Targetkan tombol Post merah resmi (class Button__root--type-primary, bukan menu sidebar Posts)
                    post_candidates = page.locator(
                        "button.Button__root--type-primary, button[data-e2e='upload_post_btn'], button:text-is('Post'), button:text-is('Posting'), button:text-is('Unggah')"
                    ).all()

                    clicked_post = False
                    for btn in post_candidates:
                        try:
                            box = btn.bounding_box()
                            text = (btn.text_content() or "").strip()
                            # Pastikan bukan sidebar (x > 250) dan teks tepat 'Post' / 'Posting' (bukan 'Posts')
                            if box and box["x"] > 250 and text in ["Post", "Posting", "Unggah"]:
                                console.print(f"[bold green]Mengklik tombol Post resmi di ({box['x']}, {box['y']})...[/bold green]")
                                btn.scroll_into_view_if_needed()
                                page.wait_for_timeout(1000)
                                btn.click(force=True)
                                clicked_post = True
                                break
                        except Exception:
                            pass

                    if not clicked_post:
                        # Fallback jika selector spesifik tidak kena
                        fallback_post = page.locator("button.Button__root--type-primary").first
                        if fallback_post.count() > 0:
                            fallback_post.scroll_into_view_if_needed()
                            page.wait_for_timeout(1000)
                            fallback_post.click(force=True)
                            clicked_post = True

                    if not clicked_post:
                        page.screenshot(path=screenshot_path)
                        browser.close()
                        return False, "Tombol 'Post' utama tidak ditemukan.", screenshot_path

                # 8. Tunggu konfirmasi akhir upload
                console.print("[cyan]Menunggu konfirmasi upload selesai...[/cyan]")
                page.wait_for_timeout(10000)

                page.screenshot(path=screenshot_path)
                browser.close()
                console.print(f"[bold green]✓ Video TikTok untuk [{account_name}] berhasil diposting! Bukti: {screenshot_path}[/bold green]")
                return True, f"Video berhasil diupload ke TikTok ({account_name}).", screenshot_path

            except Exception as ex:
                try:
                    page.screenshot(path=screenshot_path)
                except Exception:
                    pass
                browser.close()
                return False, f"Terjadi kesalahan saat upload TikTok: {str(ex)}", screenshot_path

    def apply_tiktok_photo_sound(
        self,
        page,
        sound_mode: str = "search",
        sound_query: str = "school",
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
        try:
            console.print(f"[bold cyan]=== MEMILIH SOUND TIKTOK UNTUK POSTER/CAROUSEL (Mode: {sound_mode.upper()}) ===[/bold cyan]")
            
            # 1. Klik tombol '+ Add sound' di bawah deskripsi
            console.print("[cyan]1. Mengklik tombol '+ Add sound'...[/cyan]")
            add_sound_btn = page.locator(
                "button:has-text('Add sound'), button:has-text('Tambah suara'), button:has-text('+ Add sound'), div[role='button']:has-text('Add sound')"
            ).first

            if add_sound_btn.count() == 0 or not add_sound_btn.is_visible():
                console.print("[yellow]Tombol '+ Add sound' tidak ditemukan di bawah deskripsi.[/yellow]")
                return False

            add_sound_btn.scroll_into_view_if_needed()
            add_sound_btn.click()
            page.wait_for_timeout(3500)

            # 2. Pilihan Mode: FAVORITE vs SEARCH
            sound_applied = False
            if sound_mode == "favorite":
                console.print("[cyan]2. Membuka tab 'Favorites' di modal sound...[/cyan]")
                fav_tab_clicked = False
                
                try:
                    fav_tab = page.locator("div, span, button, [role='tab']").filter(has_text=re.compile(r"^(Favorites|Favorit|Favorite|Disimpan)$", re.I)).first
                    if fav_tab.count() > 0 and fav_tab.is_visible():
                        fav_tab.click()
                        fav_tab_clicked = True
                        console.print("[green]✓ Tab Favorites berhasil diklik![/green]")
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
                    console.print(f"[bold green]✓ Memilih secara acak 1 dari {len(use_buttons)} sound favorit. Mengklik tombol 'Use'...[/bold green]")
                    chosen_btn.click()
                    page.wait_for_timeout(3000)
                    sound_applied = True
                else:
                    console.print("[yellow]Tab Favorites belum memiliki sound atau kosong. Melakukan fallback ke pencarian sound...[/yellow]")
                    sound_mode = "search"

            if not sound_applied: # sound_mode == "search"
                console.print(f"[cyan]2. Mencari sound TikTok dengan query: [yellow]'{sound_query}'[/yellow]...[/cyan]")
                search_box = page.locator("input[placeholder*='Search sounds'], input[placeholder*='search sounds'], input[placeholder*='Cari sound']").first
                if search_box.count() > 0:
                    search_box.click(force=True)
                    search_box.fill(sound_query)
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(3000)

                use_buttons = page.locator("button:has-text('Use'), div[role='button']:has-text('Use'), button:has-text('Gunakan')").all()
                if use_buttons:
                    console.print("[green]✓ Sound teratas ditemukan. Mengklik tombol 'Use'...[/green]")
                    use_buttons[0].click()
                    page.wait_for_timeout(3000)
                    sound_applied = True
                else:
                    console.print("[yellow]Tombol 'Use' tidak ditemukan di hasil pencarian sound.[/yellow]")

            console.print("[bold green]✓ Sound TikTok untuk Poster/Carousel berhasil dipilih dan diterapkan![/bold green]")
            return sound_applied

        except Exception as ex:
            console.print(f"[bold yellow]Peringatan saat konfigurasi Sound Foto/Carousel: {ex}[/bold yellow]")
            return False

    def upload_photos(
        self,
        photo_paths: list,
        caption: str = "",
        title: str = "",
        as_draft: bool = False,
        account_name: str = "default",
        sound_mode: str = "search",
        tiktok_sound_query: Optional[str] = None,
        category_label: str = "Carousel"
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Uploads Poster (single photo) or Carousel (multiple photos) to TikTok Studio.
        1. Navigate to https://www.tiktok.com/tiktokstudio/upload?tab=photo
        2. Set input files with photo_paths.
        3. Fill title & description/caption.
        4. Attach sound from '+ Add sound' (Favorites or Search).
        5. Click Post / Save Draft.
        """
        resolved_photos = [str(Path(p).resolve()) for p in photo_paths]
        if not resolved_photos:
            return False, "Tidak ada file foto yang diberikan untuk diunggah.", None

        state_file = get_account_state_file(account_name, "tiktok")
        if not state_file.exists():
            return False, f"Sesi login TikTok untuk akun '{account_name}' belum ada. Silakan jalankan login terlebih dahulu.", None

        sanitized_caption = ContentValidator.sanitize_caption(caption, platform="tiktok")
        timestamp = int(time.time())
        screenshot_path = str(LOGS_DIR / f"tiktok_photo_{account_name}_{timestamp}.png")

        mode_text = "HEADLESS" if self.headless else "VISIBLE BROWSER (FULL MAXIMIZED)"
        console.print(f"[bold cyan]=== MEMULAI UPLOAD TIKTOK {category_label.upper()} ({mode_text}) ===[/bold cyan]")
        console.print(f"Akun: [magenta]{account_name}[/magenta]")
        console.print(f"Jumlah Slide/Foto: [yellow]{len(resolved_photos)}[/yellow]")
        console.print(f"Caption: [italic]{sanitized_caption}[/italic]")
        console.print(f"Sound Mode: [cyan]{sound_mode.upper()}[/cyan] (Query: {tiktok_sound_query or 'school'})")

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
                # 1. Buka halaman upload Foto TikTok Studio
                console.print("[cyan]1. Membuka halaman Creator Upload Photos TikTok...[/cyan]")
                page.goto("https://www.tiktok.com/tiktokstudio/upload?tab=photo", timeout=45000, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)

                # Cek jika session expired / redirect login
                if "login" in page.url:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return False, f"Session TikTok untuk '{account_name}' telah kadaluarsa. Silakan login ulang.", screenshot_path

                self.dismiss_popups(page)

                # Pastikan tab Photos aktif jika belum di URL tab=photo
                if "tab=photo" not in page.url:
                    photos_tab = page.locator("[role='tab'], button").filter(has_text=re.compile(r"^Photos$", re.I)).first
                    if photos_tab.count() > 0 and photos_tab.is_visible():
                        photos_tab.click()
                        page.wait_for_timeout(1500)

                # 2. Masukkan file foto langsung via set_input_files (tanpa membuka OS dialog)
                console.print(f"[cyan]2. Memasukkan {len(resolved_photos)} file foto...[/cyan]")
                file_input = page.locator("input[type='file']").first
                if file_input.count() == 0:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return False, "Form input file foto tidak ditemukan di halaman TikTok.", screenshot_path

                file_input.set_input_files(resolved_photos)
                page.wait_for_timeout(6000)
                self.dismiss_popups(page)

                # 3. Input Caption / Deskripsi (Judul dikosongkan sesuai preferensi user)
                console.print("[cyan]3. Mengisi caption/deskripsi konten...[/cyan]")
                
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
                    sound_query=tiktok_sound_query or "school"
                )
                self.dismiss_popups(page)

                # 5. Scroll ke bawah dan klik Post / Save Draft
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(4000)

                if as_draft:
                    console.print("[cyan]Menyimpan sebagai Draf...[/cyan]")
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
                        return False, "Tombol 'Post' utama tidak ditemukan.", screenshot_path

                # 6. Tunggu konfirmasi akhir
                console.print("[cyan]Menunggu konfirmasi upload selesai...[/cyan]")
                page.wait_for_timeout(10000)

                page.screenshot(path=screenshot_path)
                browser.close()
                console.print(f"[bold green]✓ {category_label} TikTok untuk [{account_name}] berhasil diposting! Bukti: {screenshot_path}[/bold green]")
                return True, f"{category_label} berhasil diupload ke TikTok ({account_name}).", screenshot_path

            except Exception as ex:
                try:
                    page.screenshot(path=screenshot_path)
                except Exception:
                    pass
                browser.close()
                return False, f"Terjadi kesalahan saat upload {category_label} ke TikTok: {str(ex)}", screenshot_path

