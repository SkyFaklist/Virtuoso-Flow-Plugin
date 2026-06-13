import threading

import pytest


# ---- model ----------------------------------------------------------

def test_make_job_defaults():
    from vfp_tunnel.sim.job import make_job
    j = make_job({"cellview": {"lib": "L", "cell": "C", "view": "schematic"},
                  "test": "ac"})
    assert j["status"] == "queued"
    assert j["schema_version"] == "0.1"
    assert j["job_id"].startswith("job_")
    assert j["inputs_fingerprint"].startswith("fp_")


def test_fingerprint_stable_and_distinct():
    from vfp_tunnel.sim.job import compute_fingerprint
    cv = {"lib": "L", "cell": "C", "view": "schematic"}
    assert compute_fingerprint(cv, "ac") == compute_fingerprint(cv, "ac")
    assert compute_fingerprint(cv, "ac") != compute_fingerprint(cv, "tran")


def test_caller_fingerprint_wins():
    from vfp_tunnel.sim.job import make_job
    j = make_job({"test": "ac", "inputs_fingerprint": "fp_fromdirtycheck"})
    assert j["inputs_fingerprint"] == "fp_fromdirtycheck"


def test_transition_rules():
    from vfp_tunnel.sim.job import make_job, transition
    j = make_job({"test": "ac"})
    r = transition(j, "running")
    assert r["status"] == "running"
    d = transition(r, "done", result_id="r_1")
    assert d["status"] == "done" and d["result_id"] == "r_1"
    with pytest.raises(ValueError):
        transition(d, "running")            # done is terminal
    with pytest.raises(ValueError):
        transition(make_job({}), "done")    # queued -> done not allowed


# ---- store + freshness guard ----------------------------------------

@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("VFP_HOME", str(tmp_path))
    import importlib
    import vfp_tunnel.config as cfg
    importlib.reload(cfg)
    import vfp_tunnel.sim.job_store as m
    importlib.reload(m)
    return m.JobStore()


def test_store_lifecycle_and_persist(tmp_path, monkeypatch):
    monkeypatch.setenv("VFP_HOME", str(tmp_path))
    import importlib
    import vfp_tunnel.config as cfg
    importlib.reload(cfg)
    import vfp_tunnel.sim.job_store as m
    importlib.reload(m)
    s = m.JobStore()
    j = s.create({"job_id": "job_x", "test": "ac"})
    s.mark_running("job_x")
    s.mark_done("job_x", result_id="r_9")
    assert m.JobStore().get("job_x")["status"] == "done"   # persisted


def test_freshness_guard(store):
    fp = "fp_same"
    store.create({"job_id": "job_old", "test": "ac", "inputs_fingerprint": fp})
    store.mark_running("job_old")
    store.mark_done("job_old", result_id="r_1")
    # a queued job with the same fingerprint is NOT "fresh done"
    store.create({"job_id": "job_q", "test": "ac", "inputs_fingerprint": fp})
    fresh = store.fresh_done(fp)
    assert fresh["job_id"] == "job_old"
    assert store.fresh_done("fp_other") is None


def test_cancel_and_unknown(store):
    store.create({"job_id": "job_c", "test": "ac"})
    assert store.cancel("job_c")["status"] == "cancelled"
    with pytest.raises(KeyError):
        store.mark_running("job_nope")


# ---- RPC over TCP ---------------------------------------------------

@pytest.fixture
def running_tunnel(tmp_path, monkeypatch):
    monkeypatch.setenv("VFP_HOME", str(tmp_path))
    import importlib
    import vfp_tunnel.config as cfg
    importlib.reload(cfg)
    for mod in ("vfp_tunnel.sim.job_store", "vfp_tunnel.sim.manager",
                "vfp_tunnel.event.manager"):
        importlib.reload(importlib.import_module(mod))
    from vfp_tunnel.daemon import Tunnel
    from vfp_tunnel.rpc.transport import make_server

    tun = Tunnel("127.0.0.1", 0)
    server = make_server("127.0.0.1", 0, tun.dispatcher)
    tun.server = server
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield host, port
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


_CV = {"lib": "RFCOPA", "cell": "XOPA", "view": "schematic"}


def test_rpc_job_lifecycle_and_events(running_tunnel):
    from vfp_tunnel.rpc.transport import call
    host, port = running_tunnel

    res = call("job.create", {"job": {"cellview": _CV, "test": "ac_loopgain"}},
               host=host, port=port)
    assert res["reused"] is False
    jid = res["job"]["job_id"]
    assert res["job"]["status"] == "queued"

    call("job.mark_running", {"job_id": jid}, host=host, port=port)
    done = call("job.mark_done", {"job_id": jid, "result_id": "r_42"},
                host=host, port=port)
    assert done["job"]["status"] == "done"
    assert done["job"]["result_id"] == "r_42"

    types = [e["type"] for e in call("event.list", {}, host=host, port=port)["events"]]
    assert "job.created" in types and "job.done" in types


def test_rpc_freshness_reuse(running_tunnel):
    from vfp_tunnel.rpc.transport import call
    host, port = running_tunnel
    # first job: run to done
    jid = call("job.create", {"job": {"cellview": _CV, "test": "ac"}},
               host=host, port=port)["job"]["job_id"]
    call("job.mark_running", {"job_id": jid}, host=host, port=port)
    call("job.mark_done", {"job_id": jid, "result_id": "r_1"}, host=host, port=port)

    # identical inputs + reuse (default) => returns the done job, no new job
    again = call("job.create", {"job": {"cellview": _CV, "test": "ac"}},
                 host=host, port=port)
    assert again["reused"] is True
    assert again["job"]["job_id"] == jid

    # reuse=false => a fresh queued job
    forced = call("job.create", {"job": {"cellview": _CV, "test": "ac"}, "reuse": False},
                  host=host, port=port)
    assert forced["reused"] is False
    assert forced["job"]["status"] == "queued"


def test_rpc_unknown_job_raises(running_tunnel):
    from vfp_tunnel.rpc.transport import call
    from vfp_tunnel.rpc.jsonrpc import JsonRpcError
    from vfp_tunnel.rpc import errors
    host, port = running_tunnel
    with pytest.raises(JsonRpcError) as ei:
        call("job.get", {"job_id": "job_nope"}, host=host, port=port)
    assert ei.value.code == errors.NOT_FOUND
