"""Unit tests for the JSON-RPC dispatcher."""

from vfp_tunnel.rpc.jsonrpc import (Dispatcher, JsonRpcError, INVALID_PARAMS,
                                    INVALID_REQUEST, METHOD_NOT_FOUND)


def make_dispatcher():
    d = Dispatcher()
    d.register("echo", lambda params: {"echo": params.get("msg")})
    d.register("boom", _boom)
    return d


def _boom(params):
    raise JsonRpcError(INVALID_PARAMS, "bad params", data={"got": params})


def req(method, params=None, id_=1):
    msg = {"jsonrpc": "2.0", "id": id_, "method": method}
    if params is not None:
        msg["params"] = params
    return msg


def test_result_roundtrip():
    d = make_dispatcher()
    resp = d.dispatch(req("echo", {"msg": "hi"}))
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    assert resp["result"] == {"echo": "hi"}
    assert "error" not in resp


def test_method_not_found():
    resp = make_dispatcher().dispatch(req("nope"))
    assert resp["error"]["code"] == METHOD_NOT_FOUND


def test_invalid_request_missing_method():
    d = make_dispatcher()
    resp = d.dispatch({"jsonrpc": "2.0", "id": 7})
    assert resp["error"]["code"] == INVALID_REQUEST
    assert resp["id"] == 7


def test_invalid_request_wrong_version():
    resp = make_dispatcher().dispatch({"jsonrpc": "1.0", "method": "echo", "id": 1})
    assert resp["error"]["code"] == INVALID_REQUEST


def test_params_must_be_object():
    resp = make_dispatcher().dispatch(req("echo", [1, 2, 3]))
    assert resp["error"]["code"] == INVALID_PARAMS


def test_jsonrpc_error_propagates_data():
    resp = make_dispatcher().dispatch(req("boom", {"x": 1}))
    assert resp["error"]["code"] == INVALID_PARAMS
    assert resp["error"]["message"] == "bad params"
    assert resp["error"]["data"] == {"got": {"x": 1}}


def test_notification_returns_none():
    d = make_dispatcher()
    # no id => notification => no response
    assert d.dispatch({"jsonrpc": "2.0", "method": "echo", "params": {"msg": "x"}}) is None


def test_notification_unknown_method_is_silent():
    d = make_dispatcher()
    assert d.dispatch({"jsonrpc": "2.0", "method": "nope"}) is None


def test_default_params_empty_dict():
    d = Dispatcher()
    d.register("noparams", lambda params: {"n": len(params)})
    resp = d.dispatch(req("noparams"))
    assert resp["result"] == {"n": 0}
