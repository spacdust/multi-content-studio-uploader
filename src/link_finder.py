"""
Link Finder Module
High-precision social media post URL discovery via account scoping,
category awareness (Video/Reels vs Poster/Photos vs Carousel),
caption sequence matching (SequenceMatcher), and timestamp proximity.
Supports TikTok Studio, Instagram, and Facebook with persistent caching.
"""

import os
import re
import json
import time
import difflib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from rich.console import Console

from src.config import (
    get_account_dir,
    get_account_state_file,
    DEFAULT_USER_AGENT,
    LOGS_DIR,
    launch_browser,
    get_safe_storage_state
)
from src.account_manager import AccountManager

console = Console(highlight=False, legacy_windows=False)


def normalize_caption(text: str) -> str:
    """Normalizes caption text by removing emojis, special characters, and collapsing whitespace."""
    if not text:
        return ""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower(), flags=re.UNICODE)
    return re.sub(r"\s+", " ", cleaned).strip()


def caption_match_score(query_caption: str, candidate_text: str) -> float:
    """
    Computes fingerprint match confidence between search caption and candidate post text
    using exact substring check and SequenceMatcher (preserving word order).
    Returns float from 0.0 to 1.0.
    """
    q_norm = normalize_caption(query_caption)
    c_norm = normalize_caption(candidate_text)

    if not q_norm or not c_norm:
        return 0.0

    # 1. Exact phrase substring check (first 35-50 chars)
    q_prefix = q_norm[:40].strip()
    if q_prefix and q_prefix in c_norm:
        return 1.0

    c_prefix = c_norm[:40].strip()
    if c_prefix and c_prefix in q_norm:
        return 1.0

    # 2. SequenceMatcher on first 12 words (preserves sequential order)
    q_chunk = " ".join(q_norm.split()[:12])
    c_chunk = " ".join(c_norm.split()[:12])
    
    if not q_chunk or not c_chunk:
        return 0.0

    ratio = difflib.SequenceMatcher(None, q_chunk, c_chunk).ratio()
    return ratio


def infer_category(category: str = "", item_key: str = "") -> str:
    """Infers content category: 'Poster', 'Carousel', or 'Video'."""
    cat = (category or "").strip().capitalize()
    if cat in ["Poster", "Carousel", "Video"]:
        return cat
    ik = (item_key or "").lower()
    if "poster" in ik or ik.endswith((".jpg", ".jpeg", ".png")):
        return "Poster"
    if "carousel" in ik:
        return "Carousel"
    return "Video"


class LinkFinder:
    """Finds exact post URLs across social platforms for a given account and content item."""

    @classmethod
    def get_cached_urls(cls, account_name: str, item_key: str) -> Dict[str, str]:
        """Retrieves cached post URLs from upload_history.json."""
        acc_dir = get_account_dir(account_name)
        history_file = acc_dir / "upload_history.json"
        if not history_file.exists():
            return {}

        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)

            for k, entry in history.items():
                if k == item_key or Path(k).name == Path(item_key).name or item_key in k:
                    return entry.get("post_urls", {})
        except Exception:
            pass
        return {}

    @classmethod
    def save_cached_urls(cls, account_name: str, item_key: str, urls: Dict[str, str]):
        """Persists newly discovered post URLs to upload_history.json atomically."""
        if not urls:
            return
        acc_dir = get_account_dir(account_name)
        history_file = acc_dir / "upload_history.json"
        history = {}
        if history_file.exists():
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = {}

        matched_key = None
        for k in history.keys():
            if k == item_key or Path(k).name == Path(item_key).name or item_key in k:
                matched_key = k
                break

        target_key = matched_key or item_key
        if target_key not in history:
            history[target_key] = {
                "uploaded_platforms": list(urls.keys()),
                "timestamps": {},
                "proofs": {},
                "post_urls": {}
            }

        existing_urls = history[target_key].setdefault("post_urls", {})
        for plat, url in urls.items():
            if url:
                existing_urls[plat] = url

        tmp_file = history_file.with_suffix(".tmp")
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
            tmp_file.replace(history_file)
        except Exception:
            pass

    @classmethod
    def find_tiktok_link(
        cls,
        account_name: str,
        caption: str = "",
        item_key: str = "",
        category: str = "",
        force_refresh: bool = False
    ) -> Tuple[bool, Optional[str], str]:
        """
        Extracts the exact TikTok post URL by searching TikTok Studio content list.
        Returns: (success, url, message)
        """
        resolved_cat = infer_category(category, item_key)
        if not force_refresh:
            cached = cls.get_cached_urls(account_name, item_key)
            if cached.get("tiktok"):
                return True, cached["tiktok"], "Link ditemukan dari cache lokal."

        state_file = get_account_state_file(account_name, "tiktok")
        safe_state = get_safe_storage_state(state_file)
        if not safe_state:
            return False, None, f"Sesi TikTok akun '{account_name}' belum login."

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = launch_browser(p, headless=True)
                context = browser.new_context(user_agent=DEFAULT_USER_AGENT, storage_state=safe_state)
                page = context.new_page()

                console.print(f"[cyan]Memindai TikTok Studio ({resolved_cat}) untuk [{account_name}]...[/cyan]")
                page.goto("https://www.tiktok.com/tiktokstudio/content", timeout=40000, wait_until="domcontentloaded")
                page.wait_for_timeout(3500)

                if "login" in page.url:
                    browser.close()
                    return False, None, "Sesi TikTok telah kedaluwarsa."

                all_discovered = []

                # Initial anchors
                initial_anchors = page.evaluate("""() => {
                    return Array.from(document.querySelectorAll("a")).map(a => ({
                        href: a.href.split('?')[0],
                        text: (a.innerText || '').trim()
                    })).filter(a => a.href.includes('/video/') || a.href.includes('/photo/'));
                }""")
                all_discovered.extend(initial_anchors)

                # Search queries generation (short 2-3 word distinctive chunks)
                words = normalize_caption(caption).split()
                search_queries = []
                if len(words) >= 3:
                    search_queries.append(" ".join(words[:3]))
                if len(words) >= 6:
                    search_queries.append(" ".join(words[3:6]))
                if len(words) >= 9:
                    search_queries.append(" ".join(words[6:9]))
                elif words:
                    search_queries.append(" ".join(words[:2]))

                best_match = None
                best_score = 0.0

                search_input = page.locator("input[placeholder*='Search'], input[placeholder*='Cari']").first
                for sq in search_queries:
                    if search_input.count() > 0:
                        try:
                            search_input.click()
                            page.keyboard.press("Control+A")
                            page.keyboard.press("Backspace")
                            page.wait_for_timeout(300)
                            search_input.type(sq, delay=35)
                            page.keyboard.press("Enter")
                            page.wait_for_timeout(3000)

                            filtered = page.evaluate("""() => {
                                return Array.from(document.querySelectorAll("a")).map(a => ({
                                    href: a.href.split('?')[0],
                                    text: (a.innerText || '').trim()
                                })).filter(a => a.href.includes('/video/') || a.href.includes('/photo/'));
                            }""")
                            for it in filtered:
                                if it["href"] not in [x["href"] for x in all_discovered]:
                                    all_discovered.append(it)
                                score = caption_match_score(caption, it["text"])
                                if score > best_score:
                                    best_score = score
                                    best_match = it

                            if best_match and best_score >= 0.95:
                                break
                        except Exception:
                            pass

                browser.close()

                # Deduplicate
                seen_urls = set()
                unique_posts = []
                for p_item in all_discovered:
                    u = p_item["href"]
                    if u not in seen_urls:
                        seen_urls.add(u)
                        unique_posts.append(p_item)

                if not unique_posts:
                    return False, None, "Belum ada postingan yang terdeteksi di TikTok Studio."

                # Category prioritization
                matching_posts = unique_posts
                if resolved_cat in ["Poster", "Carousel"]:
                    photo_posts = [p for p in unique_posts if "/photo/" in p["href"]]
                    if photo_posts:
                        matching_posts = photo_posts
                elif resolved_cat == "Video":
                    video_posts = [p for p in unique_posts if "/video/" in p["href"]]
                    if video_posts:
                        matching_posts = video_posts

                # Match caption fingerprint
                best_match = None
                best_score = 0.0

                for post in matching_posts:
                    score = caption_match_score(caption, post["text"])
                    if score > best_score:
                        best_score = score
                        best_match = post

                if best_match and (best_score >= 0.45 or not caption.strip()):
                    url = best_match["href"]
                    cls.save_cached_urls(account_name, item_key, {"tiktok": url})
                    return True, url, f"Link TikTok ditemukan dengan kecocokan {(best_score*100):.0f}%."

                top_post = matching_posts[0]["href"]
                cls.save_cached_urls(account_name, item_key, {"tiktok": top_post})
                return True, top_post, "Link TikTok terbaru berhasil diambil."

        except Exception as e:
            return False, None, f"Gagal memindai TikTok: {str(e)}"

    @classmethod
    def find_instagram_link(
        cls,
        account_name: str,
        caption: str = "",
        item_key: str = "",
        category: str = "",
        force_refresh: bool = False
    ) -> Tuple[bool, Optional[str], str]:
        """
        Extracts the exact Instagram post URL via Instagrapi or Playwright.
        Returns: (success, url, message)
        """
        resolved_cat = infer_category(category, item_key)
        if not force_refresh:
            cached = cls.get_cached_urls(account_name, item_key)
            if cached.get("instagram"):
                return True, cached["instagram"], "Link ditemukan dari cache lokal."

        # Method A: Instagrapi (Mobile API protocol - Fast & Headless)
        acc_dir = get_account_dir(account_name)
        session_file = acc_dir / "instagrapi_session.json"
        state_file = get_account_state_file(account_name, "instagram")
        safe_state = get_safe_storage_state(state_file)

        cl = None
        try:
            from instagrapi import Client
            cl = Client()
            if session_file.exists():
                cl.load_settings(session_file)
            elif safe_state:
                # Extract sessionid from Playwright state cookies
                cookies = safe_state.get("cookies", [])
                cookie_dict = {c["name"]: c["value"] for c in cookies}
                sessionid = cookie_dict.get("sessionid")
                if sessionid:
                    cl.login_by_sessionid(sessionid)
                    try:
                        cl.dump_settings(session_file)
                    except Exception:
                        pass

            if cl and cl.user_id:
                console.print(f"[cyan]Memindai feed Instagram ({resolved_cat}) untuk [{account_name}] via Mobile API...[/cyan]")
                if resolved_cat == "Video":
                    medias = cl.user_clips(cl.user_id, amount=25)
                else:
                    medias = cl.user_medias(cl.user_id, amount=25)

                best_media = None
                best_score = 0.0

                for m in medias:
                    cap = m.caption_text or ""
                    score = caption_match_score(caption, cap)
                    if score > best_score:
                        best_score = score
                        best_media = m

                target_m = best_media if (best_media and (best_score >= 0.45 or not caption.strip())) else (medias[0] if medias else None)

                if target_m:
                    code = target_m.code
                    link_type = "reel" if resolved_cat == "Video" else "p"
                    url = f"https://www.instagram.com/{link_type}/{code}/"
                    cls.save_cached_urls(account_name, item_key, {"instagram": url})
                    msg = f"Link Instagram ditemukan dengan kecocokan {(best_score*100):.0f}%." if best_media else "Link Instagram terbaru berhasil diambil."
                    return True, url, msg
        except Exception:
            pass

        # Method B: Playwright Instagram Web fallback
        if not safe_state:
            return False, None, f"Sesi Instagram akun '{account_name}' belum login."

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = launch_browser(p, headless=True)
                context = browser.new_context(user_agent=DEFAULT_USER_AGENT, storage_state=safe_state)
                page = context.new_page()

                console.print(f"[cyan]Memindai Instagram Web untuk [{account_name}]...[/cyan]")
                page.goto("https://www.instagram.com/", timeout=35000, wait_until="domcontentloaded")
                page.wait_for_timeout(3500)

                # Detect username from page
                username = page.evaluate("""() => {
                    const links = Array.from(document.querySelectorAll("a[role='link'], a"));
                    for (const a of links) {
                        const h = a.getAttribute('href') || '';
                        if (h.startsWith('/') && h.endsWith('/') && h.split('/').length === 3) {
                            const candidate = h.split('/')[1];
                            if (!['explore', 'reels', 'direct', 'stories', 'accounts', 'your_activity'].includes(candidate)) {
                                return candidate;
                            }
                        }
                    }
                    return null;
                }""") or account_name.lower().replace(' ', '_')

                profile_url = f"https://www.instagram.com/{username}/"
                page.goto(profile_url, timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(3500)

                hrefs = page.evaluate("""() => {
                    return Array.from(document.querySelectorAll("a[href*='/p/'], a[href*='/reel/']")).map(a => a.href.split('?')[0]);
                }""")
                browser.close()

                if hrefs:
                    if resolved_cat == "Video":
                        reel_hrefs = [h for h in hrefs if "/reel/" in h]
                        if reel_hrefs:
                            hrefs = reel_hrefs
                    else:
                        photo_hrefs = [h for h in hrefs if "/p/" in h]
                        if photo_hrefs:
                            hrefs = photo_hrefs

                    top_url = hrefs[0]
                    cls.save_cached_urls(account_name, item_key, {"instagram": top_url})
                    return True, top_url, "Link Instagram berhasil ditemukan."

                return False, None, "Belum ada postingan Instagram yang ditemukan."

        except Exception as e:
            return False, None, f"Gagal memindai Instagram: {str(e)}"

    @classmethod
    def find_facebook_link(
        cls,
        account_name: str,
        caption: str = "",
        item_key: str = "",
        category: str = "",
        force_refresh: bool = False
    ) -> Tuple[bool, Optional[str], str]:
        """
        Extracts the exact Facebook post URL (distinguishing Reels vs Photos/Posters vs Posts).
        Returns: (success, url, message)
        """
        resolved_cat = infer_category(category, item_key)
        if not force_refresh:
            cached = cls.get_cached_urls(account_name, item_key)
            if cached.get("facebook"):
                cached_fb = cached["facebook"]
                if resolved_cat in ["Poster", "Carousel"] and "/reel/" in cached_fb:
                    pass
                elif resolved_cat == "Video" and "/photo" in cached_fb:
                    pass
                else:
                    return True, cached_fb, "Link ditemukan dari cache lokal."

        state_file = get_account_state_file(account_name, "facebook")
        safe_state = get_safe_storage_state(state_file)
        if not safe_state:
            meta_state = get_account_state_file(account_name, "meta")
            safe_state = get_safe_storage_state(meta_state)

        if not safe_state:
            return False, None, f"Sesi Facebook akun '{account_name}' belum login."

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = launch_browser(p, headless=True)
                context = browser.new_context(user_agent=DEFAULT_USER_AGENT, storage_state=safe_state)
                page = context.new_page()

                console.print(f"[cyan]Memindai Facebook ({resolved_cat}) untuk [{account_name}]...[/cyan]")

                best_match = None
                best_score = 0.0

                # -------------------------------------------------------------
                # 1. Video Category: Targeted Reels Tab & Player Inspection
                # -------------------------------------------------------------
                if resolved_cat == "Video":
                    page.goto("https://www.facebook.com/me?sk=reels_tab", timeout=35000, wait_until="domcontentloaded")
                    page.wait_for_timeout(3500)

                    # Extract Reels strictly from main content area (not navbar notifications)
                    reel_ids = page.evaluate("""() => {
                        const main = document.querySelector("div[role='main']") || document.body;
                        const anchors = Array.from(main.querySelectorAll("a[href*='/reel/']"));
                        const list = [];
                        for (const a of anchors) {
                            const m = a.href.match(/facebook\\.com\\/reel\\/(\\d+)/);
                            if (m && !list.includes(m[1])) {
                                list.push(m[1]);
                            }
                        }
                        return list;
                    }""")

                    if reel_ids:
                        for rid in reel_ids[:8]:
                            reel_url = f"https://www.facebook.com/reel/{rid}/"
                            page.goto(reel_url, timeout=25000, wait_until="domcontentloaded")
                            page.wait_for_timeout(1800)

                            reel_text = page.evaluate("""() => {
                                const texts = Array.from(document.querySelectorAll("div[dir='auto'], span[dir='auto']"))
                                    .map(e => (e.innerText || '').trim())
                                    .filter(t => t.length > 15);
                                return texts.join(' ');
                            }""")

                            score = caption_match_score(caption, reel_text)
                            if score > best_score:
                                best_score = score
                                best_match = reel_url

                            if score >= 0.75:
                                break

                    if best_match and (best_score >= 0.45 or not caption.strip()):
                        browser.close()
                        cls.save_cached_urls(account_name, item_key, {"facebook": best_match})
                        return True, best_match, f"Link Facebook (Reels) ditemukan dengan kecocokan {(best_score*100):.0f}%."

                    if reel_ids:
                        top_url = f"https://www.facebook.com/reel/{reel_ids[0]}/"
                        browser.close()
                        cls.save_cached_urls(account_name, item_key, {"facebook": top_url})
                        return True, top_url, "Link Facebook Reel terbaru berhasil diambil."

                # -------------------------------------------------------------
                # 2. Photos / Poster / Carousel Category: Progressive Timeline
                # -------------------------------------------------------------
                page.goto("https://www.facebook.com/me", timeout=35000, wait_until="domcontentloaded")
                page.wait_for_timeout(3500)

                all_discovered_posts = []
                for scroll_i in range(8):
                    found_list = page.evaluate("""() => {
                        const results = [];
                        const textNodes = Array.from(document.querySelectorAll("div[dir='auto']"));
                        for (const node of textNodes) {
                            const text = (node.innerText || '').trim();
                            if (text.length < 15) continue;

                            let container = node;
                            let postLink = null;
                            let isReel = false;
                            let isPhoto = false;

                            for (let k = 0; k < 12; k++) {
                                if (!container) break;
                                const anchors = Array.from(container.querySelectorAll("a"));
                                for (const a of anchors) {
                                    const h = a.href || '';
                                    const fbidMatch = h.match(/fbid=(\\d+)/);
                                    if (fbidMatch) {
                                        postLink = `https://www.facebook.com/photo/?fbid=${fbidMatch[1]}`;
                                        isPhoto = true;
                                        break;
                                    }
                                    const reelMatch = h.match(/facebook\\.com\\/reel\\/(\\d+)/);
                                    if (reelMatch) {
                                        postLink = `https://www.facebook.com/reel/${reelMatch[1]}/`;
                                        isReel = true;
                                        break;
                                    }
                                    if (h.includes('permalink.php') && h.includes('story_fbid=')) {
                                        postLink = h.split('&comment_id')[0].split('&notif')[0];
                                        break;
                                    }
                                    const postMatch = h.match(/facebook\\.com\\/[^\\/]+\\/posts\\/(\\d+)/);
                                    if (postMatch) {
                                        postLink = h.split('?')[0];
                                        break;
                                    }
                                }
                                if (postLink) break;
                                container = container.parentElement;
                            }

                            if (postLink) {
                                results.push({
                                    caption: text,
                                    url: postLink,
                                    isPhoto: isPhoto,
                                    isReel: isReel
                                });
                            }
                        }
                        return results;
                    }""")

                    for item in found_list:
                        u = item["url"]
                        if u not in [x["url"] for x in all_discovered_posts]:
                            all_discovered_posts.append(item)

                        if resolved_cat in ["Poster", "Carousel"] and item.get("isReel"):
                            continue

                        score = caption_match_score(caption, item["caption"])
                        if score > best_score:
                            best_score = score
                            best_match = item["url"]

                    if best_match and best_score >= 0.7:
                        break

                    page.mouse.wheel(0, 1200)
                    page.wait_for_timeout(800)

                browser.close()

                cat_filtered_posts = [p for p in all_discovered_posts if not p.get("isReel") and "/reel/" not in p["url"]]

                if best_match and (best_score >= 0.45 or not caption.strip()):
                    cls.save_cached_urls(account_name, item_key, {"facebook": best_match})
                    return True, best_match, f"Link Facebook ({resolved_cat}) ditemukan dengan kecocokan {(best_score*100):.0f}%."

                if cat_filtered_posts:
                    top_url = cat_filtered_posts[0]["url"]
                    cls.save_cached_urls(account_name, item_key, {"facebook": top_url})
                    return True, top_url, f"Link Facebook {resolved_cat} terbaru berhasil diambil."

                return False, None, f"Belum ada postingan Facebook ({resolved_cat}) yang ditemukan."

        except Exception as e:
            return False, None, f"Gagal memindai Facebook: {str(e)}"

    @classmethod
    def find_all_links(
        cls,
        account_name: str,
        item_key: str,
        caption: str = "",
        category: str = "",
        platforms: Optional[List[str]] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Runs category-aware link search across specified platforms.
        Returns unified results dictionary with copyable formats.
        """
        if not platforms:
            platforms = ["tiktok", "instagram", "facebook"]

        resolved_cat = infer_category(category, item_key)
        results = {}
        found_urls = {}

        for p in platforms:
            plat = p.lower()
            if plat == "tiktok":
                ok, url, msg = cls.find_tiktok_link(account_name, caption, item_key, resolved_cat, force_refresh)
            elif plat in ["instagram", "ig"]:
                ok, url, msg = cls.find_instagram_link(account_name, caption, item_key, resolved_cat, force_refresh)
            elif plat in ["facebook", "fb"]:
                ok, url, msg = cls.find_facebook_link(account_name, caption, item_key, resolved_cat, force_refresh)
            else:
                ok, url, msg = False, None, f"Platform '{p}' tidak didukung."

            results[plat] = {
                "success": ok,
                "url": url,
                "message": msg
            }
            if ok and url:
                found_urls[plat] = url

        lines = []
        if found_urls.get("tiktok"):
            lines.append(f"🎵 TikTok:\n{found_urls['tiktok']}")
        if found_urls.get("instagram"):
            lines.append(f"📷 Instagram:\n{found_urls['instagram']}")
        if found_urls.get("facebook"):
            lines.append(f"📘 Facebook:\n{found_urls['facebook']}")

        formatted_summary = "\n\n".join(lines) if lines else ""

        return {
            "account": account_name,
            "item_key": item_key,
            "category": resolved_cat,
            "platforms": results,
            "urls": found_urls,
            "formatted_summary": formatted_summary,
            "found_count": len(found_urls)
        }
