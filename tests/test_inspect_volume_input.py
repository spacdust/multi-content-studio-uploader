import os
import time
from pathlib import Path
from rich.console import Console
from playwright.sync_api import sync_playwright

from src.config import (
    get_account_state_file,
    TIKTOK_UPLOAD_URL,
    DEFAULT_USER_AGENT,
    LOGS_DIR
)

console = Console(highlight=False)

def inspect_top_card_and_volume_input(account_name: str = "Aqobah International School"):
    state_file = get_account_state_file(account_name, "tiktok")
    screenshot_path = str(LOGS_DIR / "debug_volume_input_inspect.png")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = browser.new_context(
            user_agent=DEFAULT_USER_AGENT,
            viewport={"width": 1920, "height": 1080},
            storage_state=str(state_file)
        )
        page = context.new_page()
        page.goto(TIKTOK_UPLOAD_URL, timeout=45000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        # Upload video
        file_input = page.locator("input[type='file']").first
        if file_input.count() > 0:
            sample_video = Path("sample_test.mp4").resolve()
            file_input.set_input_files(str(sample_video))
            page.wait_for_timeout(6000)

        # Dismiss Got it
        for _ in range(2):
            got_it = page.locator("button:has-text('Got it'), button:has-text('Mengerti')").first
            if got_it.count() > 0 and got_it.is_visible():
                got_it.click()
                page.wait_for_timeout(500)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)

        # Open Sounds editor
        sounds_btn = page.locator("button.editor-entrance[data-button-name='sounds'], button[data-button-name='sounds']").first
        sounds_btn.click()
        page.wait_for_timeout(4000)

        # Dismiss modal inside editor
        for _ in range(2):
            modal_btn = page.locator("button:has-text('Got it'), button:has-text('Mengerti')").first
            if modal_btn.count() > 0 and modal_btn.is_visible():
                modal_btn.click()
                page.wait_for_timeout(500)

        # Search sounds
        search_box = page.locator("input[placeholder*='Search sounds'], input[placeholder*='search sounds']").first
        if search_box.count() > 0:
            search_box.click()
            search_box.fill("school")
            page.keyboard.press("Enter")
            page.wait_for_timeout(3000)

        # 1. SORT CARDS BY Y-COORDINATE TO GUARANTEE THE TOPMOST CARD
        console.print("=== MENGURUTKAN SOUND CARDS BERDASARKAN Y (ATAS KE BAWAH) ===")
        candidates = page.locator("div:has(> img), div:has-text('00:'), div:has-text('01:'), div:has-text('02:')").all()
        valid_cards = []
        for c in candidates:
            box = c.bounding_box()
            if box and box["x"] >= 50 and box["x"] < 450 and box["y"] >= 160 and box["width"] > 100:
                valid_cards.append((box["y"], box, c))

        # Sort by Y ascending (nilai Y terkecil = paling atas)
        valid_cards.sort(key=lambda item: item[0])
        console.print(f"Total card musik valid ditemukan: {len(valid_cards)}")
        for idx, (y, box, c) in enumerate(valid_cards):
            console.print(f"  [{idx}] Y={y:.1f} | Box: ({box['x']:.1f}, {box['y']:.1f}, w={box['width']:.1f}, h={box['height']:.1f})")

        # Topmost card
        if valid_cards:
            top_y, top_box, top_card = valid_cards[0]
            target_x = top_box["x"] + top_box["width"] - 20
            target_y = top_box["y"] + (top_box["height"] / 2)
            console.print(f"\n>> MENGKLIK TOMBOL '+' PADA LAGU PALING ATAS #{0} DI ({target_x:.1f}, {target_y:.1f})...")
            page.mouse.move(target_x, target_y)
            page.wait_for_timeout(300)
            page.mouse.click(target_x, target_y)
            page.wait_for_timeout(4000)

        # 2. INSPEKSI INPUT VOLUME DI PANEL AUDIO KANAN
        console.print("\n=== MENGINSPEKSI SEMUA INPUT DI AREA PANEL AUDIO KANAN ===")
        # Cari elemen di sekitar teks "Volume" atau "dB"
        inputs_near_volume = page.locator("input").all()
        for idx, inp in enumerate(inputs_near_volume):
            box = inp.bounding_box()
            if box and box["x"] > 1000:
                html = inp.evaluate("el => el.outerHTML")
                console.print(f"Input [{idx}] at ({box['x']:.1f}, {box['y']:.1f}, w={box['width']:.1f}, h={box['height']:.1f}):")
                console.print(f"  HTML: {html}")

        # Coba mengisi -7 ke input volume yang ditemukan
        # Cari input yang dekat dengan teks "dB"
        db_input = page.locator("div:has-text('Volume') input, input[class*='input'], input[role='spinbutton']").first
        if db_input.count() > 0:
            console.print("\nMencoba mengisi -7 ke db_input...")
            db_input.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            db_input.fill("-7")
            page.keyboard.press("Enter")
            page.wait_for_timeout(1000)

        page.screenshot(path=screenshot_path)
        console.print(f"[OK] Screenshot tersimpan di: {screenshot_path}")
        browser.close()

if __name__ == "__main__":
    inspect_top_card_and_volume_input()
