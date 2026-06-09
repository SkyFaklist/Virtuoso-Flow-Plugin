"""End-to-end test: real TCP server + client over the JSON-RPC transport."""

import threading

import pytest


@pytest.fixture
def running_tunnel(tmp_path, monkeypatch):
    monkeypatch.setenv("VFP_HOME", str(tmp_path))
    import importlib
    import vfp_tunnel.config as cfg
    importlib.reload(cfg)
    from vfp_tunnel.daemon import Tunnel
    from vfp_tunnel.rpc.transport import make_server

    tun = Tunnel("127.0.0.1", 0)          # port 0 => ephemeral
    server = make_server("127.0.0.1", 0, tun.dispatcher)
    tun.server = server
    host, port = server.server_address[0], server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield host, port
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_status_register_list(running_tunnel):
    from vfp_tunnel.rpc.transport import call
    host, port = running_tunnel

    status = call("tunnel.status", {}, host=host, port=port)
    assert status["running"] is True
    assert status["sessions"] == 0

    reg = call("session.register", {"client": {"client": "test-client"}},
               host=host, port=port)
    sid = reg["session_id"]
    assert sid.startswith("s_")

    pong = call("session.ping", {"session_id": sid}, host=host, port=port)
    assert pong["pong"] is True

    listed = call("session.list", {}, host=host, port=port)["sessions"]
    assert [s["session_id"] for s in listed] == [sid]

    current = call("session.current", {}, host=host, port=port)["session"]
    assert current["session_id"] == sid


def test_method_not_found_over_wire(running_tunnel):
    from vfp_tunnel.rpc.transport import call
    from vfp_tunnel.rpc.jsonrpc import JsonRpcError, METHOD_NOT_FOUND
    host, port = running_tunnel
    with pytest.raises(JsonRpcError) as ei:
        call("does.not.exist", {}, host=host, port=port)
    assert ei.value.code == METHOD_NOT_FOUND
