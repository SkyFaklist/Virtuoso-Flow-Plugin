"""JSON-RPC 2.0 primitives and a small method dispatcher.

Each registered method is a callable taking a single ``params`` dict and
returning a JSON-serialisable result. Raise ``JsonRpcError`` for a
structured error response.
"""

import logging

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
SERVER_ERROR = -32000

log = logging.getLogger("vfp_tunnel.rpc")


class JsonRpcError(Exception):
    def __init__(self, code, message, data=None):
        super(JsonRpcError, self).__init__(message)
        self.code = code
        self.message = message
        self.data = data


def response(id_, result):
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def error(id_, code, message, data=None):
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": id_, "error": err}


class Dispatcher:
    def __init__(self):
        self._methods = {}

    def register(self, name, fn):
        self._methods[name] = fn

    def methods(self):
        return sorted(self._methods)

    def dispatch(self, msg):
        """Handle one parsed JSON-RPC message.

        Returns a response dict, or ``None`` for a notification (no id).
        """
        if (not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0"
                or "method" not in msg):
            mid = msg.get("id") if isinstance(msg, dict) else None
            return error(mid, INVALID_REQUEST, "Invalid Request")

        id_ = msg.get("id")
        method = msg.get("method")
        params = msg.get("params")
        if params is None:
            params = {}
        if not isinstance(params, dict):
            return error(id_, INVALID_PARAMS, "params must be an object")

        fn = self._methods.get(method)
        if fn is None:
            if id_ is None:
                return None
            return error(id_, METHOD_NOT_FOUND, "Method not found: %s" % method)

        try:
            result = fn(params)
        except JsonRpcError as e:
            return error(id_, e.code, e.message, e.data)
        except Exception as e:  # noqa: BLE001 - last-resort guard
            log.exception("method %s failed", method)
            return error(id_, INTERNAL_ERROR, "%s: %s" % (type(e).__name__, e))

        if id_ is None:
            return None
        return response(id_, result)
