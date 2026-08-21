import os
import re
import json
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console

console = Console(highlight=False, legacy_windows=False)

# Default LLM Endpoint configurations
DEFAULT_LLM_BASE_URL = "http://localhost:20128/v1"
DEFAULT_LLM_API_KEY = "sk-a618b4e3193e3ac0-bqifx2-c14cf732"
DEFAULT_LLM_MODEL = "ag/gemini-3.7-flash-medium"

class CaptionGenerator:
    """
    Multimodal AI Caption Generator:
    - Extracts keyframes from videos and analyzes images using LLM Vision.
    - Strictly NO EMOJIS in captions.
    - Strictly maximum 4 hashtags at the bottom.
    """

    @classmethod
    def get_env_val(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """Reads configuration from environment or local .env file."""
        val = os.getenv(key)
        if val:
            return val.strip()

        env_file = Path(".env")
        if env_file.exists():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(f"{key}="):
                            return line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception:
                pass
        return default

    @classmethod
    def strip_emojis(cls, text: str) -> str:
        """Removes all emojis and pictographic symbols from text."""
        emoji_pattern = re.compile(
            "["
            "\U00010000-\U0010ffff"
            "\u2600-\u27ff"
            "\u2300-\u23ff"
            "\u2b50-\u2b55"
            "\u200d"
            "\ufe0f"
            "]+",
            flags=re.UNICODE
        )
        cleaned = emoji_pattern.sub("", text)
        # Bersihkan spasi ganda yang tertinggal setelah emoji dihapus
        cleaned = re.sub(r" +", " ", cleaned)
        return cleaned.strip()

    @classmethod
    def sanitize_llm_caption(cls, raw_text: str, max_hashtags: int = 4) -> str:
        """
        Cleans LLM response:
        - Strips all emojis and formatting quirks.
        - Limits hashtags to strictly max_hashtags (e.g. 4).
        """
        text = raw_text.strip()
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1].strip()

        # 1. Hapus semua emoji
        text = cls.strip_emojis(text)

        # 2. Ekstrak semua hashtag
        hashtags = re.findall(r"#[A-Za-z0-9_]+", text)
        
        # 3. Hapus hashtag dari teks utama sementara
        text_without_tags = re.sub(r"#[A-Za-z0-9_]+", "", text).strip()
        text_without_tags = re.sub(r"\n{3,}", "\n\n", text_without_tags)

        # 4. Ambil maksimal 4 hashtag
        selected_tags = hashtags[:max_hashtags]
        
        if not selected_tags:
            selected_tags = ["#school", "#education", "#santrikeren", "#fyp"][:max_hashtags]

        tag_string = " ".join(selected_tags)
        return f"{text_without_tags}\n\n{tag_string}".strip()

    @classmethod
    def extract_video_frames_base64(cls, video_path: Path, max_frames: int = 3) -> List[str]:
        """Extracts representative resized frame snapshots from a video file in base64."""
        frames_b64 = []
        try:
            import cv2
            cap = cv2.VideoCapture(str(video_path))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames > 0:
                ratios = [0.2, 0.5, 0.8] if max_frames == 3 else [0.15, 0.35, 0.6, 0.85]
                for ratio in ratios[:max_frames]:
                    frame_no = int(total_frames * ratio)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
                    ret, frame = cap.read()
                    if ret:
                        h, w = frame.shape[:2]
                        new_w = 640
                        new_h = int(h * (640 / w))
                        resized = cv2.resize(frame, (new_w, new_h))
                        _, buffer = cv2.imencode(".jpg", resized, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                        frames_b64.append(base64.b64encode(buffer).decode("utf-8"))
            cap.release()
        except Exception as e:
            console.print(f"[dim yellow]Frame extraction note: {e}[/dim yellow]")
        return frames_b64

    @classmethod
    def encode_image_base64(cls, image_path: Path) -> Optional[str]:
        """Encodes an image file to base64."""
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return None

    @classmethod
    def generate_with_llm(
        cls,
        prompt: str,
        image_b64_list: Optional[List[str]] = None,
        base_url: str = DEFAULT_LLM_BASE_URL,
        api_key: str = DEFAULT_LLM_API_KEY,
        model: str = DEFAULT_LLM_MODEL
    ) -> Optional[str]:
        """Calls OpenAI-compatible multimodal endpoint."""
        try:
            from openai import OpenAI
            client = OpenAI(base_url=base_url, api_key=api_key)

            system_instruction = (
                "Anda adalah copywriter media sosial profesional untuk TikTok dan Instagram. "
                "Tugas Anda membuat caption yang sangat menarik, berbobot, ramah, dan profesional dalam Bahasa Indonesia. "
                "ATURAN MUTLAK:\n"
                "1. DILARANG MENYERTAKAN EMOJI ATAU EMOTIKON APAPUN dalam seluruh teks.\n"
                "2. Sertakan MAKSIMAL TEPAT 4 HASHTAG di baris paling bawah.\n"
                "3. Format output: HANYA teks caption dan 4 hashtag (tanpa intro atau tanda kutip)."
            )

            if image_b64_list:
                user_content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
                for b64 in image_b64_list:
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                    })
                messages = [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ]
            else:
                messages = [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ]

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=350
            )
            return response.choices[0].message.content
        except Exception as e:
            console.print(f"[dim yellow]LLM Endpoint note: {e}[/dim yellow]")
            return None

    @classmethod
    def generate_fallback_caption(cls, topic: str, category: str, account_name: str) -> str:
        """Smart persona template generator without emojis when LLM endpoint is temporarily unreachable."""
        clean_topic = topic.replace("_", " ").replace("-", " ").title()
        templates = [
            f"Momen seru dan inspiratif seputar {clean_topic} bersama {account_name}. Tetap semangat belajar dan terus berkarya.",
            f"Setiap langkah kecil adalah bagian dari perjalanan besar. Suasana hangat {clean_topic} di {account_name}.",
            f"Belajar, berproses, dan bertumbuh bersama {account_name}. Simak keseruan {clean_topic} hari ini.",
            f"Menumbuhkan generasi berakhlak dan berprestasi. Inilah kegiatan {clean_topic} di {account_name}."
        ]
        chosen = templates[len(clean_topic) % len(templates)]
        hashtags = ["#school", "#education", "#santrikeren", "#fyp"]
        return f"{chosen}\n\n{' '.join(hashtags)}"

    @classmethod
    def generate_caption(
        cls,
        item_name: str,
        category: str,
        account_name: str,
        media_path: Optional[Path] = None,
        extra_context: Optional[str] = None
    ) -> str:
        """
        Main entry point for generating captions:
        1. If media_path is provided, extracts visual frames from video / encodes images.
        2. Sends multimodal prompt to LLM (ag/gemini-3.7-flash-medium).
        3. Sanitizes output to strictly ensure NO EMOJIS and max 4 hashtags.
        """
        clean_topic = Path(item_name).stem.replace("_", " ").replace("-", " ")
        image_b64_list = []

        if media_path and media_path.exists():
            if media_path.is_file():
                suffix = media_path.suffix.lower()
                if suffix in [".mp4", ".mov", ".mkv", ".webm"]:
                    image_b64_list = cls.extract_video_frames_base64(media_path, max_frames=3)
                elif suffix in [".jpg", ".jpeg", ".png", ".webp"]:
                    b64 = cls.encode_image_base64(media_path)
                    if b64:
                        image_b64_list.append(b64)
            elif media_path.is_dir():
                slides = sorted([
                    p for p in media_path.iterdir()
                    if p.is_file() and p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
                ])
                for slide in slides[:3]:
                    b64 = cls.encode_image_base64(slide)
                    if b64:
                        image_b64_list.append(b64)

        if image_b64_list:
            prompt = (
                f"Analisis cuplikan visual di atas untuk akun '{account_name}'.\n"
                f"Kategori Konten: {category}\n"
                f"Topik/Nama File: {clean_topic}\n"
                f"{f'Konteks Tambahan: {extra_context}' if extra_context else ''}\n\n"
                f"Tugas Anda:\n"
                f"1. Buat caption media sosial yang sangat menarik dan menginspirasi berdasarkan adegan nyata di video/foto tersebut.\n"
                f"2. Gunakan Bahasa Indonesia yang natural, hangat, dan positif (1 - 3 kalimat padat).\n"
                f"3. DILARANG MENYERTAKAN EMOJI APAPUN (TIDAK BOLEH ADA EMOTIKON/SIMBOL EMOJI).\n"
                f"4. WAJIB sertakan MAKSIMAL TEPAT 4 HASHTAG di baris paling bawah.\n"
                f"5. Format output: HANYA caption dan 4 hashtag."
            )
        else:
            prompt = (
                f"Buatkan caption media sosial yang sangat menarik, engaging, dan menginspirasi untuk akun '{account_name}'.\n"
                f"Kategori Konten: {category}\n"
                f"Topik/Nama Konten: {clean_topic}\n"
                f"{f'Konteks Tambahan: {extra_context}' if extra_context else ''}\n\n"
                f"ATURAN WAJIB:\n"
                f"1. Gunakan Bahasa Indonesia yang natural, hangat, dan positif (1 - 3 kalimat padat).\n"
                f"2. DILARANG MENYERTAKAN EMOJI APAPUN (TIDAK BOLEH ADA EMOTIKON/SIMBOL EMOJI).\n"
                f"3. WAJIB HANYA sertakan MAKSIMAL TEPAT 4 HASHTAG di baris paling bawah.\n"
                f"4. Format output: HANYA hasil caption dan 4 hashtag."
            )

        base_url = cls.get_env_val("LLM_BASE_URL", DEFAULT_LLM_BASE_URL)
        api_key = cls.get_env_val("LLM_API_KEY", DEFAULT_LLM_API_KEY)
        model = cls.get_env_val("LLM_MODEL", DEFAULT_LLM_MODEL)

        raw_output = cls.generate_with_llm(
            prompt=prompt,
            image_b64_list=image_b64_list if image_b64_list else None,
            base_url=base_url,
            api_key=api_key,
            model=model
        )

        if not raw_output:
            return cls.generate_fallback_caption(clean_topic, category, account_name)

        return cls.sanitize_llm_caption(raw_output, max_hashtags=4)
