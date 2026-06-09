"""Tests for the session registry (uses an isolated VFP_HOME)."""

import importlib


def fresh_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("VFP_HOME", str(tmp_path))
    # config reads VFP_HOME lazily, but reload to be safe under reuse.
    import vfp_tunnel.config as cfg
    importlib.reload(cfg)
    import vfp_tunnel.session.registry as reg
    importlib.reload(reg)
    return reg.Registry()


def test_register_and_list(tmp_path, monkeypatch):
    r = fresh_registry(tmp_path, monkeypatch)
    rec = r.register({"client": "virtuoso-flow-plugin"})
    assert rec["session_id"].startswith("s_")
    listed = r.list()
    assert len(listed) == 1
    assert listed[0]["session_id"] == rec["session_id"]


def test_public_strips_internal_keys(tmp_path, monkeypatch):
    r = fresh_registry(tmp_path, monkeypatch)
    rec = r.register({"client": "x"})
    pub = r.public(rec)
    assert "_created_ts" not in pub and "_last_ts" not in pub
    assert pub["session_id"] == rec["session_id"]


def test_current_is_most_recently_seen(tmp_path, monkeypatch):
    r = fresh_registry(tmp_path, monkeypatch)
    a = r.register({"client": "a"})
    b = r.register({"client": "b"})
    assert r.current()["session_id"] == b["session_id"]
    r.touch(a["session_id"])
    assert r.current()["session_id"] == a["session_id"]


def test_persistence_reload(tmp_path, monkeypatch):
    r = fresh_registry(tmp_path, monkeypatch)
    rec = r.register({"client": "persist"})
    # a brand-new registry should recover the session from disk
    import vfp_tunnel.session.registry as reg
    r2 = reg.Registry()
    assert any(s["session_id"] == rec["session_id"] for s in r2.list())
