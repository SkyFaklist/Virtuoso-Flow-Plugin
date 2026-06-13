import hashlib
import json
import time
import uuid

VALID_STATUSES = ("queued", "running", "done", "failed", "cancelled")
TERMINAL_STATUSES = ("done", "failed", "cancelled")

TRANSITIONS = {
    "queued":    ("running", "cancelled"),
    "running":   ("done", "failed", "cancelled"),
    "done":      (),
    "failed":    (),
    "cancelled": (),
}


def _now():
    return time.time()


def _iso(ts=None):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(ts or _now()))


def compute_fingerprint(cellview, test, extra=None):
    """Fallback inputs fingerprint from cellview + test (+ optional extra).

    The authoritative fingerprint comes from the plugin's dirty-check; this is
    only used when the caller does not supply one.
    """
    payload = {"cellview": cellview or {}, "test": test or "", "extra": extra or {}}
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "fp_" + hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


def make_job(data):
    """Normalise an incoming job dict; assign id/version/status/fingerprint."""
    j = dict(data) if isinstance(data, dict) else {}
    if not j.get("job_id"):
        j["job_id"] = "job_" + uuid.uuid4().hex[:12]
    j.setdefault("schema_version", "0.1")
    j.setdefault("status", "queued")
    if not j.get("inputs_fingerprint"):
        j["inputs_fingerprint"] = compute_fingerprint(j.get("cellview"), j.get("test"))
    ts = _iso()
    j.setdefault("created_at", ts)
    j["updated_at"] = ts
    return j


def transition(job, new_status, **fields):
    """Return a copy of *job* with status set to *new_status* (+ extra fields).

    Raises ValueError if the transition is not permitted.
    """
    current = job.get("status", "queued")
    allowed = TRANSITIONS.get(current, ())
    if new_status not in allowed:
        raise ValueError("cannot transition %s -> %s (allowed: %s)"
                         % (current, new_status, allowed or "none"))
    j = dict(job)
    j.update(fields)
    j["status"] = new_status
    j["updated_at"] = _iso()
    return j
