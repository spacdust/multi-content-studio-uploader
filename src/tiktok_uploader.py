import os
import re
import json
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
        Safely saves storage_state using Playwright's native context.storage_state(),
        preserving all domain-specific cookies, security tokens, and localStorage origins.
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

            state_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_file = state_file.with_suffix(".tmp")
            context.storage_state(path=str(tmp_file))
            tmp_file.replace(state_file)
            return True
        except Exception:
            return False

    def dismiss_popups(self, page, target=None):
        """Dismiss all common TikTok guide tours, coachmarks, tooltips, cookie dialogs, and announcement modals."""
        # Proteksi: Jangan dismiss jika sedang tampil modal konfirmasi post (misal 'Video sedang diproses' / 'Post anyway')
        try:
            is_post_dialog_open = page.evaluate("""
                () => {
                    const dialogs = document.querySelectorAll("div[role='dialog'], div[class*='modal'], div[class*='Modal'], div[class*='TUXModal']");
                    for (const d of dialogs) {
                        const t = (d.innerText || '').toLowerCase();
                        if (
                            t.includes('proses') ||
                            t.includes('process') ||
                            t.includes('hak cipta') ||
                            t.includes('copyright') ||
                            t.includes('post anyway') ||
                            t.includes('tetap posting')
                        ) {
                            return true;
                        }
                    }
                    return false;
                }
            """)
            if is_post_dialog_open:
                return
        except Exception:
            pass

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

    def handle_post_confirmation_popups(self, page, session_id: Optional[str] = None) -> bool:
        """
        Detects and automatically confirms modals that appear when posting on TikTok Studio:
        - "Video is still being processed. Post anyway?" / "Video Anda masih diproses. Tetap posting?"
        - "Copyright check in progress. Post anyway?" / "Pemeriksaan hak cipta sedang berlangsung."
        - "High-definition video processing" / "Pemrosesan HD"
        - General modal asking to confirm or proceed with publishing.

        Returns True if a confirmation popup was detected and clicked.
        """
        from src.publish_tracker import PublishTracker

        handled = False
        modal_selectors = [
            "div[role='dialog']",
            "div[class*='TUXModal']",
            "div[class*='modal']",
            "div[class*='dialog']",
            "div[class*='Modal-container']",
            "div.common-modal"
        ]

        high_priority_patterns = [
            re.compile(r"^(Post anyway|Tetap posting|Posting sekarang|Post now|Continue to post|Lanjutkan posting|Tetap unggah|Posting tetap)$", re.I),
            re.compile(r"(post anyway|tetap posting|posting sekarang|post now|lanjutkan posting|tetap unggah)", re.I)
        ]
        fallback_confirm_patterns = [
            re.compile(r"^(Post|Posting|Unggah|Lanjutkan|Continue|Confirm|Konfirmasi|OK|Mengerti)$", re.I)
        ]

        # 1. Check inside active dialogs / modals via Playwright locators
        for m_sel in modal_selectors:
            try:
                modals = page.locator(m_sel).all()
                for modal in modals:
                    if not modal.is_visible():
                        continue

                    modal_text = (modal.inner_text() or "").lower()
                    is_processing_or_confirm = any(kw in modal_text for kw in [
                        "proses", "process", "hak cipta", "copyright", "anyway",
                        "tetap", "lanjutkan", "continue", "upload", "unggah", "post", "posting"
                    ])

                    if is_processing_or_confirm:
                        clean_preview = modal_text[:80].replace("\n", " ")
                        console.print(f"[bold yellow][TikTok Popup] Mendeteksi dialog konfirmasi posting: '{clean_preview}...'[/bold yellow]")
                        PublishTracker.log(
                            session_id,
                            "tiktok",
                            f"Mendeteksi dialog konfirmasi ('{clean_preview}...'). Menekan 'Tetap posting / Post anyway'...",
                            "step"
                        )

                        # Step 1A: Look for explicit 'Post anyway' / 'Tetap posting' buttons
                        for pat in high_priority_patterns:
                            btn = modal.locator("button, div[role='button']").filter(has_text=pat).first
                            if btn.count() > 0 and btn.is_visible():
                                btn_txt = (btn.inner_text() or "").strip()
                                console.print(f"[bold green][TikTok Popup] Mengklik tombol konfirmasi: '{btn_txt}'...[/bold green]")
                                btn.click(force=True)
                                page.wait_for_timeout(1500)
                                handled = True
                                break

                        if handled:
                            break

                        # Step 1B: Primary colored button inside dialog (ByteDance TUX primary button)
                        primary_btn = modal.locator(
                            "button.Button__root--type-primary, button[class*='primary'], button[data-e2e*='confirm'], button[data-e2e*='post']"
                        ).first
                        if primary_btn.count() > 0 and primary_btn.is_visible():
                            btn_txt = (primary_btn.inner_text() or "").strip()
                            console.print(f"[bold green][TikTok Popup] Mengklik tombol primary dialog: '{btn_txt}'...[/bold green]")
                            primary_btn.click(force=True)
                            page.wait_for_timeout(1500)
                            handled = True
                            break

                        # Step 1C: Fallback confirm pattern (avoiding Cancel / Batal)
                        for pat in fallback_confirm_patterns:
                            btn = modal.locator("button, div[role='button']").filter(has_text=pat).first
                            if btn.count() > 0 and btn.is_visible():
                                btn_txt = (btn.inner_text() or "").strip()
                                if btn_txt.lower() not in ["cancel", "batal", "wait", "tunggu", "kembali"]:
                                    console.print(f"[bold green][TikTok Popup] Mengklik fallback button: '{btn_txt}'...[/bold green]")
                                    btn.click(force=True)
                                    page.wait_for_timeout(1500)
                                    handled = True
                                    break
            except Exception:
                pass

            if handled:
                break

        # 2. Check directly on whole page if modal wrapper didn't match
        if not handled:
            for pat in high_priority_patterns:
                try:
                    btn = page.locator("button, div[role='button']").filter(has_text=pat).first
                    if btn.count() > 0 and btn.is_visible():
                        btn_txt = (btn.inner_text() or "").strip()
                        console.print(f"[bold green][TikTok Popup] Mengklik tombol konfirmasi halaman: '{btn_txt}'...[/bold green]")
                        PublishTracker.log(session_id, "tiktok", f"Mengklik tombol konfirmasi: '{btn_txt}'", "step")
                        btn.click(force=True)
                        page.wait_for_timeout(1500)
                        handled = True
                        break
                except Exception:
                    pass

        # 3. Native JavaScript DOM evaluation fallback
        if not handled:
            try:
                js_handled = page.evaluate("""
                    () => {
                        const dialogs = document.querySelectorAll("div[role='dialog'], div[class*='modal'], div[class*='Modal'], div[class*='TUXModal'], div[class*='popover']");
                        for (const dlg of dialogs) {
                            const txt = (dlg.innerText || '').toLowerCase();
                            if (
                                txt.includes('proses') ||
                                txt.includes('process') ||
                                txt.includes('hak cipta') ||
                                txt.includes('copyright') ||
                                txt.includes('anyway') ||
                                txt.includes('tetap posting')
                            ) {
                                const buttons = Array.from(dlg.querySelectorAll('button, div[role="button"]'));
                                const confirmBtn = buttons.find(b => {
                                    const bTxt = (b.innerText || '').toLowerCase();
                                    return (
                                        bTxt.includes('tetap posting') ||
                                        bTxt.includes('post anyway') ||
                                        bTxt.includes('posting sekarang') ||
                                        bTxt.includes('post now') ||
                                        bTxt.includes('lanjutkan') ||
                                        bTxt.includes('continue') ||
                                        bTxt.includes('tetap unggah')
                                    );
                                }) || buttons.find(b => (b.className || '').includes('primary'));

                                if (confirmBtn) {
                                    confirmBtn.click();
                                    return true;
                                }
                            }
                        }
                        return false;
                    }
                """)
                if js_handled:
                    console.print("[bold green][TikTok Popup] Berhasil mengonfirmasi dialog posting via DOM evaluate![/bold green]")
                    PublishTracker.log(session_id, "tiktok", "Berhasil mengklik konfirmasi posting (DOM evaluate)", "step")
                    page.wait_for_timeout(1500)
                    handled = True
            except Exception:
                pass

        return handled

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

        if str(sound_mode).lower() in ["none", "no_sound", "nosound", "no sound", "off", "disable", "disabled"]:
            console.print("[bold cyan][No Sound] Mode No Sound dipilih: Melewati penambahan musik/sound TikTok Studio.[/bold cyan]")
            PublishTracker.update_step(session_id, "tiktok", "Mode No Sound...", 50, "Melewati pemilihan musik/sound TikTok (Original audio only)", "info")
            return True

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

    def apply_tiktok_product_link(
        self,
        page,
        tiktok_product: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> bool:
        """
        Adds a TikTok Shop Yellow Cart product link to the video upload in TikTok Studio.
        Flow:
        1. Find and click "+ Tambah" / "+ Add" under "Tambah tautan" (Add link).
        2. In the first popup (select Link type: Product), click "Berikutnya" / "Next".
        3. In the product list modal ("Tambah tautan produk"):
           - Search keyword or product title in search input if needed.
           - Select the matching product row / .TUXRadio.
           - Click "Berikutnya" / "Next".
        4. In step 2 ("Nama produk"):
           - Clear and type custom product name (custom_title, max 30 chars).
           - Click final "Tambah" / "Add" button.
        """
        from src.publish_tracker import PublishTracker
        try:
            prod_id = str(tiktok_product.get("product_id") or "").strip()
            prod_title = str(tiktok_product.get("title") or "").strip()
            custom_title = str(tiktok_product.get("custom_title") or prod_title[:30]).strip()
            if not custom_title:
                custom_title = prod_title[:30]
            custom_title = custom_title[:30]

            console.print(f"[cyan][TikTok Shop] Memulai penambahan Keranjang Kuning: '{prod_title}' (Label: '{custom_title}')...[/cyan]")
            PublishTracker.update_step(session_id, "tiktok", "Menambahkan Keranjang Kuning...", 82, f"Membuka modal tautan produk untuk '{custom_title}'...", "step")

            # 1. Pastikan overlay Joyride / guide bersih
            try:
                page.evaluate("document.querySelectorAll('.react-joyride__overlay, #react-joyride-portal, [data-test-id=\"overlay\"]').forEach(e => e.remove());")
            except Exception:
                pass

            # Scroll ke area Tambah tautan
            page.evaluate("window.scrollTo(0, 500)")
            page.wait_for_timeout(1000)

            # Cari tombol Tambah tautan (+ Tambah / + Add)
            add_btn = None
            candidates = page.locator("button:has-text('Tambah'), button:has-text('Add')").all()
            for btn in candidates:
                txt = (btn.text_content() or "").strip()
                if txt in ["Tambah", "Add", "+ Tambah", "+ Add"]:
                    add_btn = btn
                    break

            if not add_btn:
                add_btn = page.locator("div:has-text('+ Tambah'):not(:has-text('Tambah tautan')), div[class*='add-btn']").first

            if not add_btn or add_btn.count() == 0:
                console.print("[dim yellow][TikTok Shop] Tombol '+ Tambah' tautan tidak ditemukan di halaman.[/dim yellow]")
                return False

            console.print("[cyan][TikTok Shop] Mengklik tombol '+ Tambah' tautan...[/cyan]")
            add_btn.scroll_into_view_if_needed()
            page.wait_for_timeout(500)
            add_btn.click(force=True)
            page.wait_for_timeout(2500)

            # 2. Klik "Berikutnya" / "Next" pada popup jenis tautan
            next_btn = page.locator("button:has-text('Berikutnya'), button:has-text('Next')").first
            if next_btn.count() > 0:
                console.print("[cyan][TikTok Shop] Mengklik 'Berikutnya' pada popup jenis tautan...[/cyan]")
                next_btn.click(force=True)
                page.wait_for_timeout(4000)

            # 3. Cari dan pilih produk di modal
            search_input = page.locator("input[class*='TUXTextInputCore-input'], input[placeholder*='Cari produk'], input[placeholder*='Search products']").first
            if search_input.count() > 0:
                search_term = prod_title.split("-")[0].strip() if "-" in prod_title else prod_title[:20].strip()
                if search_term:
                    console.print(f"[cyan][TikTok Shop] Mencari produk dengan kata kunci: '{search_term}'...[/cyan]")
                    search_input.click()
                    search_input.fill(search_term)
                    page.wait_for_timeout(400)
                    search_input.press("Enter")
                    page.wait_for_timeout(3000)

            # Cari radio button produk
            radio_selected = False
            if prod_id:
                try:
                    target_row_radio = page.locator(f"tr:has-text('{prod_id}') .TUXRadio, div:has-text('{prod_id}') .TUXRadio").first
                    if target_row_radio.count() > 0:
                        target_row_radio.click(force=True)
                        radio_selected = True
                except Exception:
                    pass

            if not radio_selected:
                radio = page.locator(".TUXRadio").first
                if radio.count() > 0:
                    console.print("[cyan][TikTok Shop] Memilih radio produk pertama di daftar...[/cyan]")
                    radio.click(force=True)
                    radio_selected = True

            if not radio_selected:
                console.print("[dim yellow][TikTok Shop] Gagal memilih produk di modal.[/dim yellow]")
                return False

            page.wait_for_timeout(1000)

            # 4. Klik "Berikutnya" / "Next" di pojok kanan bawah modal
            modal_next_btn = page.locator("button:has-text('Berikutnya'), button:has-text('Next')").last
            if modal_next_btn.count() > 0 and not modal_next_btn.is_disabled():
                console.print("[cyan][TikTok Shop] Mengklik 'Berikutnya' menuju pengaturan nama produk...[/cyan]")
                modal_next_btn.click(force=True)
                page.wait_for_timeout(2500)
            else:
                console.print("[dim yellow][TikTok Shop] Tombol 'Berikutnya' masih disabled.[/dim yellow]")
                return False

            # 5. Ketik custom product name (maksimal 30 karakter)
            console.print(f"[cyan][TikTok Shop] Mengetik nama keranjang kuning: '{custom_title}'...[/cyan]")
            PublishTracker.update_step(session_id, "tiktok", "Menamai Keranjang Kuning...", 84, f"Menamai produk dengan '{custom_title}'...", "step")

            modal_dialog = page.locator("div[role='dialog'], .TUXModal").last
            title_input = modal_dialog.locator("input").first
            if title_input.count() > 0:
                title_input.click()
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                page.wait_for_timeout(200)
                title_input.fill(custom_title)
                page.wait_for_timeout(500)

            # 6. Klik tombol "Tambah" / "Add" final
            final_tambah_btn = modal_dialog.locator("button:has-text('Tambah'), button:has-text('Add')").last
            if final_tambah_btn.count() > 0:
                console.print("[bold green][TikTok Shop] Mengklik tombol final 'Tambah' produk keranjang kuning![/bold green]")
                final_tambah_btn.click(force=True)
                page.wait_for_timeout(3000)
                PublishTracker.log(session_id, "tiktok", f"✓ Produk Keranjang Kuning '{custom_title}' berhasil ditambahkan ke video!", "success")
                return True
            else:
                console.print("[dim yellow][TikTok Shop] Tombol final 'Tambah' tidak ditemukan.[/dim yellow]")
                return False

        except Exception as ex:
            console.print(f"[dim yellow][TikTok Shop Warning] Gagal menambahkan keranjang kuning: {ex}[/dim yellow]")
            PublishTracker.log(session_id, "tiktok", f"Catatan: Keranjang kuning dilewati karena kendala UI ({ex})", "warning")
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
        session_id: Optional[str] = None,
        tiktok_product: Optional[Dict[str, Any]] = None
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
                storage_state=safe_state,
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
            """)
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
                    from src.auth_manager import AuthManager
                    AuthManager.invalidate_session(account_name, "tiktok")
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
                    
                    try:
                        self.fill_tiktok_caption_with_mentions(page, sanitized_caption, session_id=session_id)
                    except Exception as e:
                        console.print(f"[dim yellow]Catatan saat mengisi caption: {e}[/dim yellow]")

                # 5.5. Tambahkan Keranjang Kuning / Tautan Produk TikTok Shop jika diaktifkan
                if tiktok_product and tiktok_product.get("enabled"):
                    console.print("[cyan]5.5. Memasang tautan produk Keranjang Kuning TikTok Shop...[/cyan]")
                    self.apply_tiktok_product_link(page, tiktok_product, session_id=session_id)
                    page.wait_for_timeout(2000)
                    self.dismiss_popups(page)

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

                # 8. Tunggu konfirmasi akhir upload & antisipasi popup konfirmasi ("Video sedang diproses", "Hak cipta", dsb)
                console.print("[cyan]Menunggu verifikasi upload & mengantisipasi popup konfirmasi...[/cyan]")
                PublishTracker.update_step(session_id, "tiktok", "Menunggu verifikasi upload...", 92, "Menunggu konfirmasi penerbitan TikTok Studio & memeriksa popup...", "step")

                max_wait_seconds = 120
                poll_start = time.time()
                is_published = False

                while time.time() - poll_start < max_wait_seconds:
                    page.wait_for_timeout(1500)
                    elapsed = int(time.time() - poll_start)

                    # A. Cek dan tangani dialog konfirmasi popup (misal 'Video sedang diproses' -> 'Tetap posting')
                    confirmed_popup = self.handle_post_confirmation_popups(page, session_id=session_id)
                    if confirmed_popup:
                        console.print("[bold green][TikTok] Berhasil mengonfirmasi popup posting ('Tetap posting / Post anyway')![/bold green]")
                        PublishTracker.log(session_id, "tiktok", "Konfirmasi popup TikTok ('Tetap posting / Post anyway') berhasil ditekan!", "success")
                        page.wait_for_timeout(2500)

                    # B. Cek indikator sukses redirect URL
                    current_url = page.url
                    if "/tiktokstudio/content" in current_url or "/content" in current_url or "/manage" in current_url:
                        console.print(f"[bold green][TikTok] Terdeteksi redirect sukses ke {current_url}![/bold green]")
                        is_published = True
                        break

                    # C. Cek indikator sukses teks / modal sukses di halaman
                    try:
                        success_indicator = page.locator(
                            "div:has-text('Your video has been uploaded'), div:has-text('Video Anda telah diunggah'), div:has-text('Manage your posts'), div:has-text('Kelola postingan'), div:has-text('Upload another video'), div:has-text('Unggah video lain'), button:has-text('Manage your posts'), button:has-text('Upload another video')"
                        ).first
                        if success_indicator.count() > 0 and success_indicator.is_visible():
                            console.print("[bold green][TikTok] Terdeteksi notifikasi sukses upload![/bold green]")
                            is_published = True
                            break
                    except Exception:
                        pass

                    # D. Jika tombol Post utama masih aktif di layar setelah 12 detik dan tidak ada popup, coba klik ulang
                    if elapsed > 12 and not confirmed_popup and elapsed % 15 == 0:
                        try:
                            post_btn_retry = page.locator("button.Button__root--type-primary, button:text-is('Post'), button:text-is('Posting')").first
                            if post_btn_retry.count() > 0 and post_btn_retry.is_visible():
                                box = post_btn_retry.bounding_box()
                                if box and box["x"] > 250:
                                    console.print("[cyan]Mencoba klik ulang tombol Post...[/cyan]")
                                    post_btn_retry.click(force=True)
                                    page.wait_for_timeout(2000)
                        except Exception:
                            pass

                    # Update step timer
                    calc_prog = min(98, 92 + int((elapsed / max_wait_seconds) * 6))
                    PublishTracker.update_step(
                        session_id,
                        "tiktok",
                        f"Memverifikasi upload TikTok ({elapsed}s)...",
                        calc_prog,
                        f"Menunggu verifikasi TikTok Studio ({elapsed}s / maks {max_wait_seconds}s)...",
                        "step"
                    )

                if not is_published:
                    self.handle_post_confirmation_popups(page, session_id=session_id)
                    page.wait_for_timeout(2000)
                    # Cek sekali lagi apakah redirect atau teks sukses sudah muncul
                    current_url = page.url
                    if "/tiktokstudio/content" in current_url or "/content" in current_url or "/manage" in current_url:
                        is_published = True

                if not is_published:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    err_msg = f"Upload TikTok timeout setelah {max_wait_seconds} detik. Konfirmasi penerbitan belum diterima."
                    console.print(f"[bold red][TikTok Gagal][/bold red] {err_msg}")
                    PublishTracker.update_step(session_id, "tiktok", "Upload Gagal", 0, err_msg, "error", is_failed=True, error_msg=err_msg)
                    return False, err_msg, screenshot_path

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

        if str(sound_mode).lower() in ["none", "no_sound", "nosound", "no sound", "off", "disable", "disabled"]:
            console.print("[bold cyan][No Sound] Mode No Sound dipilih: Melewati penambahan musik Poster/Carousel TikTok.[/bold cyan]")
            PublishTracker.update_step(session_id, "tiktok", "Mode No Sound...", 65, "Melewati penambahan musik Poster/Carousel TikTok", "info")
            return True

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

    def fill_tiktok_caption_with_mentions(
        self,
        page,
        caption: str,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Fills the TikTok caption / description editor with interactive auto-tagging support.
        Detects any @username mentions in the caption.
        Instead of typing '@username' directly as plain text, it:
        1. Types text before the mention.
        2. Clicks the '@ Mention' button in the caption typing toolbar.
        3. Types the target username so TikTok searches for the account.
        4. Selects the matched account from the suggestion dropdown (or presses Enter).
        5. Continues with the rest of the caption seamlessly without unwanted double spaces.
        """
        from src.publish_tracker import PublishTracker

        caption_editor = page.locator(
            "div[contenteditable='true'], div.notranslate[contenteditable='true'], div[data-placeholder*='caption'], div[data-placeholder*='description'], div.public-DraftEditor-content, div[data-e2e='caption-editor']"
        ).first

        if caption_editor.count() == 0:
            textarea = page.locator("textarea").first
            if textarea.count() > 0:
                textarea.fill(caption)
            return True

        caption_editor.click()
        page.wait_for_timeout(300)
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        page.wait_for_timeout(300)

        # Regex for mention tag @username (excluding email addresses)
        mention_pattern = r'((?<![a-zA-Z0-9_])@[a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*)'
        has_mention = bool(re.search(mention_pattern, caption))

        if not has_mention:
            # Skenario biasa tanpa mention: ketik per baris dengan Shift+Enter
            lines = caption.split("\n")
            for idx, line in enumerate(lines):
                if line:
                    page.keyboard.type(line, delay=15)
                if idx < len(lines) - 1:
                    page.keyboard.press("Shift+Enter")
                    page.wait_for_timeout(100)
            page.wait_for_timeout(500)
            return True

        # Skenario dengan Mention (@): parser segmen interaktif
        console.print("[cyan][Auto-Tag TikTok] Mendeteksi mention pengguna (@) di caption... Mengaktifkan alur klik @mention.[/cyan]")
        PublishTracker.log(session_id, "tiktok", "Mendeteksi @mention di caption. Menjalankan auto-tag interaktif...", "info")

        parts = re.split(mention_pattern, caption)
        just_inserted_mention = False

        for part in parts:
            if not part:
                continue

            if part.startswith("@"):
                uname = part[1:]
                console.print(f"[bold cyan][Auto-Tag] Menambahkan mention: @{uname}...[/bold cyan]")
                PublishTracker.log(session_id, "tiktok", f"Auto-tagging mention: @{uname}", "step")

                # 1. Cari tombol @ Mention di toolbar editor TikTok Studio
                mention_btn = page.locator(
                    "#web-creation-caption-mention-button, button[aria-label='@mention'], button:has-text('Mention'), div[aria-label*='mention']"
                ).first

                if mention_btn.count() > 0 and mention_btn.is_visible():
                    mention_btn.click()
                    page.wait_for_timeout(350)
                else:
                    # Fallback jika tombol toolbar tidak terlihat: ketik @ manual untuk memicu dropdown
                    page.keyboard.type("@", delay=50)
                    page.wait_for_timeout(350)

                # 2. Ketik nama pengguna (username)
                page.keyboard.type(uname, delay=70)
                page.wait_for_timeout(1300)

                # 3. Tangani dropdown saran / suggestion popover
                suggestions = page.locator("div[class*='mention-suggestion-item']")
                if suggestions.count() > 0:
                    matched = False
                    for i in range(min(suggestions.count(), 6)):
                        sugg = suggestions.nth(i)
                        try:
                            sugg_text = sugg.inner_text().lower()
                            if uname.lower() in sugg_text:
                                sugg.click()
                                matched = True
                                page.wait_for_timeout(600)
                                break
                        except Exception:
                            pass
                    if not matched:
                        # Tekan Enter untuk memilih saran teratas / terfokus
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(600)
                else:
                    # Jika tidak ada saran dari TikTok (misal username tidak ditemukan), tekan Space agar teks berlanjut
                    page.keyboard.press("Space")
                    page.wait_for_timeout(400)

                just_inserted_mention = True
            else:
                # Jika segmen sebelumnya adalah mention, hindari spasi ganda (karena TikTok otomatis menyisipkan 1 spasi setelah mention)
                if just_inserted_mention and part.startswith(" "):
                    part = part[1:]
                just_inserted_mention = False

                if part:
                    lines = part.split("\n")
                    for idx, line in enumerate(lines):
                        if line:
                            page.keyboard.type(line, delay=15)
                        if idx < len(lines) - 1:
                            page.keyboard.press("Shift+Enter")
                            page.wait_for_timeout(100)

        page.wait_for_timeout(800)
        return True

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
        session_id: Optional[str] = None,
        tiktok_product: Optional[Dict[str, Any]] = None
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
                storage_state=safe_state,
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
            """)
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
                    from src.auth_manager import AuthManager
                    AuthManager.invalidate_session(account_name, "tiktok")
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
                if sanitized_caption:
                    try:
                        self.fill_tiktok_caption_with_mentions(page, sanitized_caption, session_id=session_id)
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

                # 4.5. Tambahkan Keranjang Kuning / Tautan Produk TikTok Shop jika diaktifkan
                if tiktok_product and tiktok_product.get("enabled"):
                    console.print("[cyan]4.5. Memasang tautan produk Keranjang Kuning TikTok Shop...[/cyan]")
                    self.apply_tiktok_product_link(page, tiktok_product, session_id=session_id)
                    page.wait_for_timeout(2000)
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

                # 6. Tunggu konfirmasi akhir upload & antisipasi dialog konfirmasi jika muncul
                console.print("[cyan]Menunggu verifikasi upload & mengantisipasi popup konfirmasi...[/cyan]")
                PublishTracker.update_step(session_id, "tiktok", "Menunggu verifikasi upload...", 92, "Menunggu konfirmasi penerbitan TikTok Studio & memeriksa popup...", "step")

                max_wait_seconds = 75
                poll_start = time.time()
                is_published = False

                while time.time() - poll_start < max_wait_seconds:
                    page.wait_for_timeout(1500)
                    elapsed = int(time.time() - poll_start)

                    # A. Cek popup konfirmasi
                    confirmed_popup = self.handle_post_confirmation_popups(page, session_id=session_id)
                    if confirmed_popup:
                        console.print(f"[bold green][TikTok] Berhasil mengonfirmasi popup posting {category_label}![/bold green]")
                        PublishTracker.log(session_id, "tiktok", f"Konfirmasi popup posting {category_label} berhasil ditekan!", "success")
                        page.wait_for_timeout(2500)

                    # B. Cek redirect URL
                    current_url = page.url
                    if "/tiktokstudio/content" in current_url or "/content" in current_url or "/manage" in current_url:
                        console.print(f"[bold green][TikTok] Terdeteksi redirect sukses ke {current_url}![/bold green]")
                        is_published = True
                        break

                    # C. Cek banner / teks sukses
                    try:
                        success_indicator = page.locator(
                            "div:has-text('Your photo has been uploaded'), div:has-text('Foto Anda telah diunggah'), div:has-text('Your video has been uploaded'), div:has-text('Video Anda telah diunggah'), div:has-text('Manage your posts'), div:has-text('Kelola postingan'), div:has-text('Upload another video'), div:has-text('Unggah video lain'), button:has-text('Manage your posts'), button:has-text('Upload another video')"
                        ).first
                        if success_indicator.count() > 0 and success_indicator.is_visible():
                            console.print(f"[bold green][TikTok] Terdeteksi notifikasi sukses upload {category_label}![/bold green]")
                            is_published = True
                            break
                    except Exception:
                        pass

                    calc_prog = min(98, 92 + int((elapsed / max_wait_seconds) * 6))
                    PublishTracker.update_step(
                        session_id,
                        "tiktok",
                        f"Memverifikasi upload {category_label} ({elapsed}s)...",
                        calc_prog,
                        f"Menunggu verifikasi TikTok Studio ({elapsed}s / maks {max_wait_seconds}s)...",
                        "step"
                    )

                if not is_published:
                    self.handle_post_confirmation_popups(page, session_id=session_id)
                    page.wait_for_timeout(2000)
                    current_url = page.url
                    if "/tiktokstudio/content" in current_url or "/content" in current_url or "/manage" in current_url:
                        is_published = True

                if not is_published:
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    err_msg = f"Upload TikTok {category_label} timeout setelah {max_wait_seconds} detik. Konfirmasi penerbitan belum diterima."
                    console.print(f"[bold red][TikTok Gagal][/bold red] {err_msg}")
                    PublishTracker.update_step(session_id, "tiktok", "Upload Gagal", 0, err_msg, "error", is_failed=True, error_msg=err_msg)
                    return False, err_msg, screenshot_path

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

