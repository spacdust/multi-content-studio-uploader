"""
Publish Tracker & Session Manager
Handles real-time logging, step progression, and multi-platform status tracking for content publishing.
Persists session data to JSON for cross-process communication (FastAPI server & background CLI worker).
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from threading import RLock

BASE_DIR = Path(__file__).resolve().parent.parent
SESSIONS_DIR = BASE_DIR / "logs" / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

_lock = RLock()
_in_memory_sessions: Dict[str, Dict[str, Any]] = {}

class PublishTracker:
    @staticmethod
    def _get_session_file(session_id: str) -> Path:
        return SESSIONS_DIR / f"{session_id}.json"

    @classmethod
    def init_session(
        cls,
        session_id: str,
        account: str,
        item_key: str,
        item_name: str,
        category: str,
        platforms: List[str],
        date_str: str = ""
    ) -> Dict[str, Any]:
        """Initializes a new publishing session with default multi-platform steps."""
        now_str = datetime.now().strftime("%H:%M:%S")
        
        platform_states = {}
        for p in platforms:
            platform_states[p] = {
                "status": "pending",  # pending | in_progress | completed | failed
                "percent": 0,
                "current_step": "Menunggu antrean...",
                "started_at": None,
                "completed_at": None,
                "post_url": None,
                "error": None
            }

        session_data = {
            "session_id": session_id,
            "account": account,
            "item_key": item_key,
            "item_name": item_name,
            "category": category,
            "date": date_str,
            "status": "in_progress",  # in_progress | completed | failed
            "percent": 0,
            "current_platform": platforms[0] if platforms else None,
            "current_step": "Inisialisasi bot & persiapan media...",
            "target_platforms": platforms,
            "platforms": platform_states,
            "started_at": time.time(),
            "updated_at": time.time(),
            "completed_at": None,
            "logs": [
                {
                    "time": now_str,
                    "timestamp": now_str,
                    "type": "info",
                    "platform": "system",
                    "message": f"Sesi publish '{item_name}' ({category}) dimulai untuk akun {account}."
                }
            ]
        }

        with _lock:
            _in_memory_sessions[session_id] = session_data
            cls._save_to_disk(session_id, session_data)

        return session_data

    @classmethod
    def get_session(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves session state from disk first (cross-process safe), fallback to memory."""
        if not session_id:
            return None

        file_path = cls._get_session_file(session_id)
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    with _lock:
                        _in_memory_sessions[session_id] = data
                    return data
            except Exception:
                pass

        with _lock:
            return _in_memory_sessions.get(session_id)

    @classmethod
    def update_step(
        cls,
        session_id: Optional[str],
        platform: str,
        step_name: str,
        platform_percent: int = 0,
        log_message: Optional[str] = None,
        log_type: str = "info",
        post_url: Optional[str] = None,
        is_completed: bool = False,
        is_failed: bool = False,
        error_msg: Optional[str] = None,
        percent: Optional[int] = None,
        log_msg: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Updates granular step progress and appends log message to the session."""
        if not session_id:
            return None

        eff_percent = percent if percent is not None else platform_percent
        eff_log_message = log_msg if log_msg is not None else log_message
        now_str = datetime.now().strftime("%H:%M:%S")

        with _lock:
            session = cls.get_session(session_id)
            if not session:
                return None

            session["updated_at"] = time.time()
            session["current_platform"] = platform
            session["current_step"] = step_name

            # Update target platform state
            if platform in session.get("platforms", {}):
                p_state = session["platforms"][platform]
                p_state["percent"] = min(100, max(0, eff_percent))
                p_state["current_step"] = step_name

                if p_state["status"] == "pending":
                    p_state["status"] = "in_progress"
                    p_state["started_at"] = time.time()

                if post_url:
                    p_state["post_url"] = post_url

                if is_completed:
                    p_state["status"] = "completed"
                    p_state["percent"] = 100
                    p_state["completed_at"] = time.time()
                elif is_failed:
                    p_state["status"] = "failed"
                    p_state["error"] = error_msg or "Gagal memproses upload"

            # Calculate total overall progress
            target_plats = session.get("target_platforms", [])
            if target_plats:
                total_p = sum(session["platforms"].get(p, {}).get("percent", 0) for p in target_plats)
                session["percent"] = int(total_p / len(target_plats))
            else:
                session["percent"] = platform_percent

            # Check if all platforms completed or failed
            all_done = all(
                session["platforms"].get(p, {}).get("status") in ["completed", "failed"]
                for p in target_plats
            )
            if all_done:
                has_success = any(session["platforms"].get(p, {}).get("status") == "completed" for p in target_plats)
                session["status"] = "completed" if has_success else "failed"
                session["completed_at"] = time.time()
                session["percent"] = 100 if has_success else session["percent"]

            # Append log message
            if eff_log_message:
                session.setdefault("logs", []).append({
                    "time": now_str,
                    "timestamp": now_str,
                    "type": log_type,  # info | step | success | warn | error
                    "platform": platform,
                    "message": eff_log_message
                })
                # Keep last 200 logs max
                if len(session["logs"]) > 200:
                    session["logs"] = session["logs"][-200:]

            _in_memory_sessions[session_id] = session
            cls._save_to_disk(session_id, session)
            return session

    @classmethod
    def log(cls, session_id: Optional[str], platform: str, message: str, log_type: str = "info"):
        """Appends a quick log entry without changing step percentages."""
        if not session_id:
            return
        now_str = datetime.now().strftime("%H:%M:%S")
        with _lock:
            session = cls.get_session(session_id)
            if session:
                session["updated_at"] = time.time()
                session.setdefault("logs", []).append({
                    "time": now_str,
                    "type": log_type,
                    "platform": platform,
                    "message": message
                })
                if len(session["logs"]) > 200:
                    session["logs"] = session["logs"][-200:]
                _in_memory_sessions[session_id] = session
                cls._save_to_disk(session_id, session)

    @classmethod
    def _save_to_disk(cls, session_id: str, data: Dict[str, Any]):
        try:
            file_path = cls._get_session_file(session_id)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
