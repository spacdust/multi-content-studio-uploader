import unittest
from unittest.mock import MagicMock, patch
import re

from src.tiktok_uploader import TikTokUploader

class TestTikTokContentCheckModal(unittest.TestCase):
    def setUp(self):
        self.uploader = TikTokUploader(headless=True)

    def test_dismiss_content_check_modal_clicks_aktifkan(self):
        """Verifikasi bahwa dialog 'Aktifkan pemeriksaan konten otomatis' terdeteksi dan diklik 'Aktifkan'"""
        mock_page = MagicMock()
        mock_modal = MagicMock()
        mock_btn_aktif = MagicMock()

        # Modal terdeteksi
        mock_modal.count.return_value = 1
        mock_modal.is_visible.return_value = True

        # Tombol 'Aktifkan' ditemukan
        mock_btn_aktif.count.return_value = 1
        mock_btn_aktif.is_visible.return_value = True

        mock_modal.locator.return_value.filter.return_value.first = mock_btn_aktif
        mock_page.locator.return_value.filter.return_value.first = mock_modal
        mock_page.evaluate.return_value = False

        self.uploader.dismiss_popups(mock_page)

        # Pastikan btn_aktif diklik
        mock_btn_aktif.click.assert_called_with(force=True)

    def test_post_dialog_evaluator_ignores_content_check_modal(self):
        """Verifikasi evaluator JS di dismiss_popups mengabaikan modal pemeriksaan konten dan tidak return lebih awal"""
        mock_page = MagicMock()
        # Modal terdeteksi tapi tombolnya sudah tidak ada
        mock_page.locator.return_value.filter.return_value.first.count.return_value = 0
        mock_page.locator.return_value.filter.return_value.first.is_visible.return_value = False

        # is_post_dialog_open evaluator return False
        mock_page.evaluate.return_value = False

        self.uploader.dismiss_popups(mock_page)

        # Escape harus tetap dipanggil jika tidak ada post dialog
        mock_page.keyboard.press.assert_called_with("Escape")

    def test_apply_tiktok_product_link_smart_selection(self):
        """Verifikasi bahwa pencarian tidak memotong judul di '-' dan evaluator memilih varian yang tepat"""
        mock_page = MagicMock()
        mock_page.evaluate.side_effect = [
            None,  # joyride
            None,  # scrollTo
            {"status": "ok", "bestIndex": 1, "bestScore": 1200, "bestRowText": "Inspired by Danhil Blu - Shift & CO. Rp40.500"}  # eval_result
        ]

        def create_mock_loc():
            loc = MagicMock()
            loc.count.return_value = 1
            loc.first = loc
            loc.last = loc
            loc.is_disabled.return_value = False
            loc.locator.side_effect = lambda *a, **k: create_mock_loc()
            return loc

        mock_search_input = create_mock_loc()
        mock_empty_msg = create_mock_loc()
        mock_empty_msg.count.return_value = 0

        mock_target_radio = create_mock_loc()
        mock_radios = create_mock_loc()
        mock_radios.nth.return_value = mock_target_radio

        mock_add_btn = create_mock_loc()
        mock_add_btn.text_content.return_value = "+ Tambah"

        mock_next_btn = create_mock_loc()
        mock_final_btn = create_mock_loc()

        def locator_side_effect(selector, *args, **kwargs):
            m = create_mock_loc()
            if "Tambah" in selector and "button" in selector:
                m.all.return_value = [mock_add_btn]
                m.first = mock_add_btn
                m.last = mock_final_btn
                return m
            if "Berikutnya" in selector or "Next" in selector:
                m.first = mock_next_btn
                m.last = mock_next_btn
                return m
            if "TUXTextInput" in selector:
                return mock_search_input
            if "text='Tidak ada produk'" in selector:
                return mock_empty_msg
            if ".TUXRadio" in selector:
                return mock_radios
            return m

        mock_page.locator.side_effect = locator_side_effect

        product = {
            "enabled": True,
            "product_id": "1735755227997111955",
            "title": "Inspired by Danhil Blu - Shift & CO. Parfum - Parfum Pria Aroma Fresh Maskulin 30ml",
            "custom_title": "ANTI BAU BADAN",
            "format_price": "Rp40.500"
        }

        ok = self.uploader.apply_tiktok_product_link(mock_page, product)
        self.assertTrue(ok)

        # Verifikasi bahwa input search diisi dengan kata kunci yang memuat Shift & CO (bukan hanya 'Inspired by Danhil Blu')
        search_calls = mock_search_input.fill.call_args_list
        self.assertTrue(any("Shift & CO" in call[0][0] for call in search_calls))

        # Verifikasi bahwa radio index ke-1 (bestIndex dari eval) yang diklik
        mock_radios.nth.assert_called_with(1)
        mock_target_radio.click.assert_called_with(force=True)

if __name__ == "__main__":
    unittest.main()

