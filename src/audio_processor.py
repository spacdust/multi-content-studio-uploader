import os
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from rich.console import Console
from rich.table import Table

from src.config import (
    SOUNDS_DIR,
    TEMP_DIR,
    SUPPORTED_AUDIO_EXTENSIONS,
    AUDIO_PRESETS
)

console = Console(highlight=False, legacy_windows=False)

class AudioProcessor:
    """Manages audio mixing, background music overlay, and volume adjustments for video content."""

    @staticmethod
    def list_available_sounds() -> List[Dict[str, Any]]:
        """List all audio files stored in assets/sounds/."""
        sounds = []
        if not SOUNDS_DIR.exists():
            return sounds

        for file in SOUNDS_DIR.iterdir():
            if file.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS:
                size_mb = round(file.stat().st_size / (1024 * 1024), 2)
                sounds.append({
                    "name": file.name,
                    "stem": file.stem,
                    "path": file,
                    "size_mb": size_mb,
                    "format": file.suffix.lower()
                })
        return sounds

    @staticmethod
    def print_sounds_and_presets():
        """Displays formatted tables for available sounds and audio presets."""
        sounds = AudioProcessor.list_available_sounds()
        sound_table = Table(title="Daftar Sound / Background Music (assets/sounds/)")
        sound_table.add_column("No", justify="right", style="cyan")
        sound_table.add_column("Nama File Audio", style="bold white")
        sound_table.add_column("Format", style="green")
        sound_table.add_column("Ukuran (MB)", justify="right", style="dim")

        if not sounds:
            console.print("[yellow]Folder 'assets/sounds/' masih kosong. Anda bisa meletakkan file .mp3 / .wav di sana.[/yellow]")
        else:
            for idx, s in enumerate(sounds, 1):
                sound_table.add_row(str(idx), s["name"], s["format"], str(s["size_mb"]))
            console.print(sound_table)

        preset_table = Table(title="Preset Volume Sesuai Jenis Konten (--preset)")
        preset_table.add_column("Nama Preset", style="bold magenta")
        preset_table.add_column("Suara Asli", style="cyan")
        preset_table.add_column("Musik (BGM)", style="green")
        preset_table.add_column("Keterangan", style="white")

        for key, p in AUDIO_PRESETS.items():
            orig_pct = f"{int(p['original_vol'] * 100)}%"
            music_pct = f"{int(p['music_vol'] * 100)}%"
            preset_table.add_row(key, orig_pct, music_pct, p["description"])
        console.print(preset_table)

    @staticmethod
    def resolve_sound_path(sound_input: str | Path) -> Optional[Path]:
        """Resolves sound file from direct path or filename in assets/sounds/."""
        if not sound_input:
            return None
        
        direct_path = Path(sound_input)
        if direct_path.exists() and direct_path.is_file():
            return direct_path.resolve()

        # Check inside SOUNDS_DIR
        for candidate in SOUNDS_DIR.iterdir():
            if candidate.name.lower() == str(sound_input).lower() or candidate.stem.lower() == str(sound_input).lower():
                return candidate.resolve()
        
        return None

    @staticmethod
    def check_has_audio(video_path: Path) -> bool:
        """Checks if the video has an existing audio stream using ffmpeg."""
        try:
            cmd = [
                "ffmpeg", "-i", str(video_path),
                "-hide_banner"
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
            return "Audio:" in result.stderr
        except Exception:
            return True

    @classmethod
    def process_video_audio(
        cls,
        video_path: str | Path,
        sound_input: Optional[str | Path] = None,
        original_volume: Optional[float] = None,
        music_volume: Optional[float] = None,
        preset: Optional[str] = None
    ) -> Tuple[Path, bool]:
        """
        Mixes and adjusts audio volumes.
        Returns: (output_video_path, is_temporary)
        """
        video_file = Path(video_path).resolve()
        if not video_file.exists():
            raise FileNotFoundError(f"File video tidak ditemukan: {video_file}")

        # Apply preset defaults if specified
        orig_vol = 1.0
        mus_vol = 0.25

        if preset:
            preset_key = preset.lower().strip()
            if preset_key in AUDIO_PRESETS:
                orig_vol = AUDIO_PRESETS[preset_key]["original_vol"]
                mus_vol = AUDIO_PRESETS[preset_key]["music_vol"]
                console.print(f"[bold cyan]Menggunakan Audio Preset:[/] [green]{preset_key}[/] ({AUDIO_PRESETS[preset_key]['description']})")
            else:
                console.print(f"[yellow]Preset '{preset}' tidak ditemukan. Menggunakan nilai default.[/yellow]")

        # Override with explicit values if provided
        if original_volume is not None:
            orig_vol = float(original_volume)
        if music_volume is not None:
            mus_vol = float(music_volume)

        sound_file = cls.resolve_sound_path(sound_input) if sound_input else None

        # If no sound added and original volume is 100%, no processing needed
        if not sound_file and orig_vol == 1.0:
            return video_file, False

        console.print(f"[bold yellow]Menyesuaikan audio konten...[/bold yellow]")
        console.print(f"• Volume Suara Asli: [cyan]{int(orig_vol * 100)}%[/cyan]")
        if sound_file:
            console.print(f"• Musik Latar (BGM): [green]{sound_file.name}[/] pada volume [cyan]{int(mus_vol * 100)}%[/cyan]")

        output_file = TEMP_DIR / f"mix_{int(time.time())}_{video_file.name}"
        has_orig_audio = cls.check_has_audio(video_file)

        if sound_file:
            # Mixing original audio + background music
            if has_orig_audio and orig_vol > 0.0:
                # Dual audio mixing
                filter_complex = (
                    f"[0:a]volume={orig_vol}[a0];"
                    f"[1:a]volume={mus_vol}[a1];"
                    f"[a0][a1]amix=inputs=2:duration=first:dropout_transition=2[aout]"
                )
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(video_file),
                    "-stream_loop", "-1",
                    "-i", str(sound_file),
                    "-filter_complex", filter_complex,
                    "-map", "0:v",
                    "-map", "[aout]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-shortest",
                    str(output_file)
                ]
            else:
                # Video has no audio or original audio is muted (0.0) -> Use only background sound
                filter_complex = f"[1:a]volume={mus_vol}[aout]"
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(video_file),
                    "-stream_loop", "-1",
                    "-i", str(sound_file),
                    "-filter_complex", filter_complex,
                    "-map", "0:v",
                    "-map", "[aout]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-shortest",
                    str(output_file)
                ]
        else:
            # Only adjust original video volume
            if orig_vol == 0.0:
                # Remove audio track
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(video_file),
                    "-an",
                    "-c:v", "copy",
                    str(output_file)
                ]
            else:
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(video_file),
                    "-filter:a", f"volume={orig_vol}",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    str(output_file)
                ]

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
        if res.returncode != 0:
            console.print(f"[bold red]Gagal memproses audio dengan ffmpeg:[/] {res.stderr[:200]}")
            return video_file, False

        console.print(f"[bold green][OK] Audio berhasil dimixing ke:[/] {output_file.name}")
        return output_file, True
