"""In-memory session registry with JSON persistence under ``.vfp/sessions``.

A session represents one connected client (typically a Virtuoso Flow Plugin
instance). Records are kept in memory and mirrored to disk so the daemon can
recover them across restarts.
"""

import json
import threading
import time
import uuid

from ..config import ensure_dirs, sessions_dir


def _now():
    return time.time()


def _iso(ts):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(ts))


class Registry:
    def __init__(self):
        self._sessions = {}
        self._lock = threading.Lock()
        self._load()

    # ---- persistence ----
    def _load(self):
        d = sessions_dir()
        if not d.exists():
            return
        for f in d.glob("*.json"):
            try:
                rec = json.loads(f.read_text(encoding="utf-8"))
                sid = rec.get("session_id")
                if sid:
                    self._sessions[sid] = rec
            except (OSError, ValueError):
                continue

    def _persist(self, rec):
        try:
            ensure_dirs()
            p = sessions_dir() / (rec["session_id"] + ".json")
            p.write_text(json.dumps(rec, indent=2), encoding="utf-8")
        except OSError:
            pass

    # ---- operations ----
    def register(self, client):
        sid = "s_" + uuid.uuid4().hex[:12]
        ts = _now()
        rec = {
            "session_id": sid,
            "client": client or {},
            "created_at": _iso(ts),
            "last_seen": _iso(ts),
            "_created_ts": ts,
            "_last_ts": ts,
        }
        with self._lock:
            self._sessions[sid] = rec
        self._persist(rec)
        return rec

    def touch(self, sid):
        with self._lock:
            rec = self._sessions.get(sid)
            if rec is None:
                return None
            ts = _now()
            rec["last_seen"] = _iso(ts)
            rec["_last_ts"] = ts
        self._persist(rec)
        return rec

    def get(self, sid):
        return self._sessions.get(sid)

    def list(self):
        return sorted(self._sessions.values(),
                      key=lambda r: r.get("_created_ts", 0))

    def current(self):
        if not self._sessions:
            return None
        return max(self._sessions.values(),
                   key=lambda r: r.get("_last_ts", 0))

    @staticmethod
    def public(rec):
        """Strip internal (underscore-prefixed) keys for the wire."""
        if rec is None:
            return None
        return {k: v for k, v in rec.items() if not k.startswith("_")}
