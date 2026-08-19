import os
import sys

# Ensure UTF-8 output encoding on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import argparse
import json
import shutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from src.account_manager import AccountManager
from src.auth_manager import AuthManager
from src.tiktok_uploader import TikTokUploader
from src.instagram_uploader import InstagramUploader
from src.meta_uploader import MetaBusinessUploader
from src.content_manager import ContentManager
from src.caption_generator import CaptionGenerator
from src.queue_manager import QueueManager
from src.validator import ContentValidator
from src.audio_processor import AudioProcessor
from src.config import QUEUE_DIR, AUDIO_PRESETS, get_account_content_dir

console = Console(highlight=False)

def main():
    parser = argparse.ArgumentParser(
        description="Content Uploader Studio CLI - Multi-Account Content & Authentication Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Perintah yang tersedia")

    # Command: account
    account_parser = subparsers.add_parser("account", help="Kelola multi-akun Instagram, TikTok & Meta Business")
    acc_sub = account_parser.add_subparsers(dest="account_action", help="Aksi akun")

    # account list
    acc_sub.add_parser("list", help="Tampilkan daftar semua akun yang terdaftar")

    # account add
    add_acc = acc_sub.add_parser("add", help="Tambah akun baru")
    add_acc.add_argument("--name", "-n", required=True, help="Nama akun unik (misal: 'Aqobah International School')")
    add_acc.add_argument("--desc", "-d", default="", help="Deskripsi akun")

    # account delete
    del_acc = acc_sub.add_parser("delete", help="Hapus akun")
    del_acc.add_argument("--name", "-n", required=True, help="Nama akun yang akan dihapus")

    # Command: content
    content_parser = subparsers.add_parser("content", help="Manajemen feed konten dan struktur folder per akun")
    cont_sub = content_parser.add_subparsers(dest="content_action", help="Aksi konten")

    # content list
    list_cont = cont_sub.add_parser("list", help="Scan dan tampilkan seluruh file konten lokal")
    list_cont.add_argument("--account", "-a", default=None, help="Filter berdasarkan nama akun tertentu")

    # content add-date
    add_date_p = cont_sub.add_parser("add-date", help="Buat folder tanggal baru untuk akun tertentu")
    add_date_p.add_argument("--account", "-a", required=True, help="Nama akun tujuan")
    add_date_p.add_argument("--date", "-d", required=True, help="Tanggal posting format YYYY-MM-DD")

    # content process
    proc_cont = cont_sub.add_parser("process", help="Proses dan upload konten yang ada di antrean")
    proc_cont.add_argument("--account", "-a", required=True, help="Nama akun target")
    proc_cont.add_argument("--category", "-c", default=None, help="Filter kategori konten (Video, Poster, Carousel)")
    proc_cont.add_argument("--date", "-d", default=None, help="Filter tanggal konten (YYYY-MM-DD)")
    proc_cont.add_argument("--item", "-i", default=None, help="Nama atau key item spesifik yang akan dipublish")
    proc_cont.add_argument("--platform", "-p", choices=["tiktok", "instagram", "facebook", "meta", "all"], default="all", help="Target platform upload")
    proc_cont.add_argument("--headless", action="store_true", help="Jalankan di background tanpa menampilkan browser")

    # Command: caption
    caption_parser = subparsers.add_parser("caption", help="AI Caption Generator menggunakan LLM")
    cap_sub = caption_parser.add_subparsers(dest="caption_action", help="Aksi caption")

    # caption generate
    cap_gen = cap_sub.add_parser("generate", help="Generate caption baru via LLM")
    cap_gen.add_argument("--topic", "-t", required=True, help="Topik atau konteks konten")
    cap_gen.add_argument("--account", "-a", default="Demo Account", help="Nama akun")
    cap_gen.add_argument("--category", "-c", choices=["Video", "Poster", "Carousel"], default="Video", help="Kategori konten")

    # Command: login
    login_parser = subparsers.add_parser("login", help="Buka browser visual untuk login akun spesifik")
    login_parser.add_argument("--account", "-a", default="default", help="Nama akun target (default: 'default')")
    login_parser.add_argument("--platform", "-p", choices=["tiktok", "instagram", "instagram-mobile", "facebook", "meta", "all"], default="all", help="Platform tujuan login")
    login_parser.add_argument("--timeout", "-t", type=int, default=600, help="Batas waktu login dalam detik (default: 600)")

    # Command: open-studio
    studio_parser = subparsers.add_parser("open-studio", help="Buka TikTok Studio, Instagram, atau Facebook di browser visual")
    studio_parser.add_argument("--account", "-a", default="default", help="Nama akun target")
    studio_parser.add_argument("--platform", "-p", choices=["tiktok", "instagram", "facebook", "meta"], default="tiktok", help="Platform")

    # Command: check-auth
    auth_parser = subparsers.add_parser("check-auth", help="Periksa status sesi login akun")
    auth_parser.add_argument("--account", "-a", default="default", help="Nama akun target (default: 'default')")
    auth_parser.add_argument("--platform", "-p", choices=["tiktok", "instagram", "facebook", "meta", "all"], default="all", help="Platform yang diperiksa")

    # Command: sound
    sound_parser = subparsers.add_parser("sound", help="Kelola dan lihat daftar sound / audio presets")
    sound_sub = sound_parser.add_subparsers(dest="sound_action", help="Aksi sound")
    sound_sub.add_parser("list", help="Lihat daftar file sound di assets/sounds/ dan preset volume")

    # Command: upload (Direct upload)
    upload_parser = subparsers.add_parser("upload", help="Upload konten langsung (Browser Maximize & Sound Editor)")
    upload_parser.add_argument("--account", "-a", default="default", help="Nama akun pengunggah (misal: 'Aqobah International School')")
    upload_parser.add_argument("--type", choices=["video", "poster", "carousel"], default="video", help="Kategori konten (video, poster, carousel)")
    upload_parser.add_argument("--file", "-f", "--video", "-v", dest="file", required=True, help="Path ke file video atau gambar")
    upload_parser.add_argument("--caption", "-c", default="", help="Teks caption dan hashtag")
    upload_parser.add_argument("--platform", "-p", choices=["tiktok", "instagram", "facebook", "meta", "all"], default="all", help="Target platform")
    upload_parser.add_argument("--draft", action="store_true", help="Simpan sebagai draft")
    upload_parser.add_argument("--headless", action="store_true", help="Jalankan di background tanpa memunculkan browser")
    upload_parser.add_argument("--sound-query", "--tiktok-sound", "-sq", default=None, help="Pencarian Sound resmi TikTok di dalam editor")
    upload_parser.add_argument("--sound-db", "--volume-db", default="-7", help="Volume musik di TikTok editor dalam dB (default: '-7')")
    upload_parser.add_argument("--sound", "-s", default=None, help="File audio background lokal")
    upload_parser.add_argument("--original-volume", "--orig-vol", type=float, default=None, help="Volume suara asli")
    upload_parser.add_argument("--music-volume", "--music-vol", type=float, default=None, help="Volume musik")
    upload_parser.add_argument("--preset", choices=list(AUDIO_PRESETS.keys()), default=None, help="Preset volume lokal")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Handlers
    if args.command == "account":
        handle_account(args)
    elif args.command == "content":
        handle_content(args)
    elif args.command == "caption":
        handle_caption(args)
    elif args.command == "login":
        handle_login(args)
    elif args.command == "open-studio":
        handle_open_studio(args)
    elif args.command == "check-auth":
        handle_check_auth(args)
    elif args.command == "sound":
        handle_sound(args)
    elif args.command == "upload":
        handle_upload(args)

def handle_open_studio(args):
    account_name = args.account
    console.print(Panel(f"[bold green]Membuka Studio Khusus Akun: [magenta]{account_name}[/magenta] ({args.platform.upper()})[/bold green]"))
    if args.platform == "tiktok":
        AuthManager.open_tiktok_studio(account_name=account_name)
    elif args.platform == "instagram":
        AuthManager.open_instagram(account_name=account_name)
    elif args.platform == "facebook":
        AuthManager.open_facebook(account_name=account_name)
    elif args.platform == "meta":
        AuthManager.open_meta_business(account_name=account_name)

def handle_caption(args):
    if args.caption_action == "generate" or not args.caption_action:
        console.print(f"[bold cyan]Menghasilkan caption untuk:[/] [yellow]{args.topic}[/] | [magenta]{args.account}[/]")
        res = CaptionGenerator.generate_caption(
            item_name=args.topic,
            category=args.category,
            account_name=args.account
        )
        print("\n========================================================")
        print("HASIL GENERATE CAPTION (MAX 4 HASHTAG):")
        print("========================================================")
        print(res)
        print("========================================================\n")

def handle_account(args):
    if args.account_action == "list" or not args.account_action:
        AccountManager.print_accounts_table()
    elif args.account_action == "add":
        data = AccountManager.create_or_get_account(args.name, description=args.desc)
        console.print(f"[bold green]Akun berhasil didaftarkan:[/] [cyan]{data['name']}[/]")
        AccountManager.print_accounts_table()

def handle_content(args):
    if args.content_action == "list" or not args.content_action:
        ContentManager.print_content_table(account_name=args.account)
    elif args.content_action == "process":
        item_target = getattr(args, "item", None)
        if item_target:
            all_items = ContentManager.scan_content(args.account)
            clean_target = item_target.split(" (")[0].strip()
            target = next((
                i for i in all_items
                if i["name"] == item_target
                or i["item_key"] == item_target
                or i["name"].startswith(clean_target)
                or clean_target in i["item_key"]
                or clean_target in i["name"]
            ), None)
            if target:
                console.print(f"[bold green]Memproses publish konten spesifik:[/] [cyan]{target['name']}[/]")
                ContentManager.process_content_item(
                    item=target,
                    platform_filter=args.platform,
                    headless=args.headless
                )
            else:
                console.print(f"[bold yellow]Konten '{item_target}' tidak ditemukan, memproses semua pending...[/bold yellow]")
                ContentManager.process_all_pending(
                    account_name=args.account,
                    category_filter=args.category,
                    date_filter=args.date,
                    platform_filter=args.platform,
                    headless=args.headless
                )
        else:
            ContentManager.process_all_pending(
                account_name=args.account,
                category_filter=args.category,
                date_filter=args.date,
                platform_filter=args.platform,
                headless=args.headless
            )
    elif args.content_action == "init-date":
        acc_dir = get_account_content_dir(args.account)
        date_str = args.date
        (acc_dir / "Video" / date_str).mkdir(parents=True, exist_ok=True)
        (acc_dir / "Poster" / date_str).mkdir(parents=True, exist_ok=True)
        (acc_dir / "Carousel" / date_str / "Carousel 1").mkdir(parents=True, exist_ok=True)
        console.print(f"[bold green][OK] Struktur folder tanggal '{date_str}' berhasil dibuat untuk akun '{args.account}'![/bold green]")
        console.print(f"Lokasi: content/{args.account}/")

def handle_login(args):
    account_name = args.account
    console.print(Panel(f"[bold green]Content Uploader - Interactive Visual Login: [magenta]{account_name}[/magenta][/bold green]"))
    platforms = ["tiktok", "instagram", "meta"] if args.platform == "all" else [args.platform]

    for p in platforms:
        if p == "tiktok":
            AuthManager.login_tiktok(account_name=account_name, timeout_seconds=args.timeout)
        elif p == "instagram":
            AuthManager.login_instagram(account_name=account_name, timeout_seconds=args.timeout)
        elif p in ["instagram-mobile", "mobile"]:
            AuthManager.login_instagram_mobile(account_name=account_name)
        elif p == "facebook":
            AuthManager.login_facebook(account_name=account_name, timeout_seconds=args.timeout)
        elif p == "meta":
            AuthManager.login_meta(account_name=account_name, timeout_seconds=args.timeout)

def handle_check_auth(args):
    account_name = args.account
    console.print(Panel(f"[bold green]Status Autentikasi Akun: [magenta]{account_name}[/magenta][/bold green]"))
    platforms = ["tiktok", "instagram", "meta"] if args.platform == "all" else [args.platform]

    for p in platforms:
        if p == "tiktok":
            ok, msg = AuthManager.verify_tiktok_session(account_name=account_name)
            status = "[green]AKTIF[/green]" if ok else "[red]TIDAK AKTIF / EXPIRED[/red]"
            console.print(f"TikTok: {status} - {msg}")
        elif p == "instagram":
            ok, msg = AuthManager.verify_instagram_session(account_name=account_name)
            status = "[green]AKTIF[/green]" if ok else "[red]TIDAK AKTIF / EXPIRED[/red]"
            console.print(f"Instagram: {status} - {msg}")
        elif p == "meta":
            ok, msg = AuthManager.verify_meta_session(account_name=account_name)
            status = "[green]AKTIF[/green]" if ok else "[red]TIDAK AKTIF / EXPIRED[/red]"
            console.print(f"Meta Business Suite: {status} - {msg}")

def handle_sound(args):
    AudioProcessor.print_sounds_and_presets()

def handle_upload(args):
    file_path = Path(args.file).resolve()
    account_name = args.account

    valid, err = ContentValidator.validate_video_file(file_path)
    if not valid:
        console.print(f"[bold red]Error:[/] {err}")
        sys.exit(1)

    upload_video_path, is_temp = AudioProcessor.process_video_audio(
        video_path=file_path,
        sound_input=args.sound,
        original_volume=args.original_volume,
        music_volume=args.music_volume,
        preset=args.preset
    )

    headless = args.headless
    platforms = ["tiktok", "instagram", "meta"] if args.platform == "all" else [args.platform]

    console.print(Panel(
        f"[bold green]Manual Upload Akun: [magenta]{account_name}[/magenta] | Target: {', '.join(platforms).upper()} | Mode: {'HEADLESS' if headless else 'FULL MAXIMIZED BROWSER'}[/bold green]"
    ))

    overall_success = True
    if "tiktok" in platforms:
        uploader = TikTokUploader(headless=headless)
        ok, msg, screen = uploader.upload(
            video_path=upload_video_path,
            caption=args.caption,
            as_draft=args.draft,
            account_name=account_name,
            tiktok_sound_query=args.sound_query,
            sound_volume_db=args.sound_db
        )
        if not ok:
            overall_success = False
            console.print(f"[red]Gagal upload ke TikTok:[/] {msg}")
        else:
            console.print(f"[green]Sukses upload ke TikTok:[/] {msg}")

    if "instagram" in platforms:
        uploader = InstagramUploader(headless=headless)
        ok, msg, screen = uploader.upload(
            video_path=upload_video_path,
            caption=args.caption,
            as_reel=(args.type == "video"),
            account_name=account_name
        )
        if not ok:
            overall_success = False
            console.print(f"[red]Gagal upload ke Instagram:[/] {msg}")
        else:
            console.print(f"[green]Sukses upload ke Instagram:[/] {msg}")

    if "meta" in platforms:
        uploader = MetaBusinessUploader(headless=headless)
        ok, msg, screen = uploader.upload(
            media_path=upload_video_path,
            caption=args.caption,
            category=args.type.capitalize(),
            account_name=account_name
        )
        if not ok:
            overall_success = False
            console.print(f"[red]Gagal upload ke Meta Business Suite:[/] {msg}")
        else:
            console.print(f"[green]Sukses upload ke Meta Business Suite (IG + FB):[//] {msg}")

    if is_temp and upload_video_path.exists():
        try:
            upload_video_path.unlink()
        except Exception:
            pass

    if not overall_success:
        sys.exit(1)

if __name__ == "__main__":
    main()
