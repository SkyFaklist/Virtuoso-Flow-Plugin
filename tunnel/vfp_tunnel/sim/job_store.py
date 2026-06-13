import json
import threading

from ..config import ensure_dirs, jobs_dir
from .job import make_job, transition


class JobStore:
    """Simulation jobs: in-memory + JSON persistence under .vfp/jobs.

    The freshness guard (``fresh_done``) lets the daemon reuse a completed job
    whose inputs_fingerprint matches, instead of re-running an identical sim.
    """

    def __init__(self):
        self._jobs = {}
        self._lock = threading.Lock()
        self._load()

    # ---- persistence ------------------------------------------------
    def _load(self):
        d = jobs_dir()
        if not d.exists():
            return
        for f in d.glob("*.json"):
            try:
                j = json.loads(f.read_text(encoding="utf-8"))
                jid = j.get("job_id")
                if jid:
                    self._jobs[jid] = j
            except (OSError, ValueError):
                continue

    def _persist(self, j):
        try:
            ensure_dirs()
            (jobs_dir() / (j["job_id"] + ".json")).write_text(
                json.dumps(j, indent=2), encoding="utf-8")
        except OSError:
            pass

    # ---- operations -------------------------------------------------
    def add(self, job):
        jid = job.get("job_id")
        if not jid:
            raise ValueError("job missing job_id")
        with self._lock:
            if jid in self._jobs:
                raise ValueError("duplicate job_id: %s" % jid)
            self._jobs[jid] = job
        self._persist(job)
        return job

    def create(self, data):
        return self.add(make_job(data))

    def get(self, job_id):
        return self._jobs.get(job_id)

    def list(self, status=None):
        with self._lock:
            items = list(self._jobs.values())
        if status:
            items = [j for j in items if j.get("status") == status]
        return sorted(items, key=lambda j: j.get("created_at", ""), reverse=True)

    def fresh_done(self, fingerprint):
        """Most recent *done* job with this inputs_fingerprint, or None.

        This is the freshness guard: identical fingerprint => the sim result is
        still valid, so the caller can reuse it instead of re-running.
        """
        if not fingerprint:
            return None
        done = [j for j in self.list(status="done")
                if j.get("inputs_fingerprint") == fingerprint]
        return done[0] if done else None

    def mark_running(self, job_id):
        return self._set(job_id, "running")

    def mark_done(self, job_id, result_id=None, run_id=None):
        fields = {}
        if result_id is not None:
            fields["result_id"] = result_id
        if run_id is not None:
            fields["run_id"] = run_id
        return self._set(job_id, "done", **fields)

    def mark_failed(self, job_id, error=None):
        return self._set(job_id, "failed", **({"error": error} if error else {}))

    def cancel(self, job_id):
        return self._set(job_id, "cancelled")

    # ---- helpers ----------------------------------------------------
    def _set(self, job_id, new_status, **fields):
        with self._lock:
            j = self._jobs.get(job_id)
            if j is None:
                raise KeyError("unknown job_id: %s" % job_id)
            updated = transition(j, new_status, **fields)
            self._jobs[job_id] = updated
        self._persist(updated)
        return updated
