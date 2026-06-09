"""Newline-framed JSON-RPC over TCP: threaded server + a tiny client.

Each message is a single JSON object on one line terminated by ``\\n``.
This framing is deliberately simple so the SKILL side can speak it too.
"""

import json
import socket

try:  # Python 3
    import socketserver
except ImportError:  # pragma: no cover - Python 2 fallback (unused)
    import SocketServer as socketserver  # type: ignore

import uuid

from .jsonrpc import JsonRpcError, PARSE_ERROR


class _Handler(socketserver.StreamRequestHandler):
    def handle(self):
        dispatcher = self.server.dispatcher
        for raw in self.rfile:  # iterate newline-delimited lines
            line = raw.strip()
            if not line:
                continue
            try:
                msg = json.loads(line.decode("utf-8"))
            except Exception:
                resp = {"jsonrpc": "2.0", "id": None,
                        "error": {"code": PARSE_ERROR, "message": "Parse error"}}
            else:
                resp = dispatcher.dispatch(msg)
            if resp is not None:
                self.wfile.write((json.dumps(resp) + "\n").encode("utf-8"))
                self.wfile.flush()


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, host, port, dispatcher):
        socketserver.ThreadingTCPServer.__init__(self, (host, port), _Handler)
        self.dispatcher = dispatcher


def make_server(host, port, dispatcher):
    """Create (but do not start) a threaded JSON-RPC server."""
    return _Server(host, port, dispatcher)


def call(method, params=None, host="127.0.0.1", port=47891, timeout=5.0):
    """Send one request and return its ``result`` (or raise JsonRpcError)."""
    req = {"jsonrpc": "2.0", "id": uuid.uuid4().hex, "method": method,
           "params": params or {}}
    payload = (json.dumps(req) + "\n").encode("utf-8")
    buf = b""
    sock = socket.create_connection((host, port), timeout=timeout)
    try:
        sock.settimeout(timeout)
        sock.sendall(payload)
        while b"\n" not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
    finally:
        sock.close()

    line = buf.split(b"\n", 1)[0]
    if not line:
        raise JsonRpcError(-32000, "no response from tunnel")
    resp = json.loads(line.decode("utf-8"))
    if resp.get("error"):
        e = resp["error"]
        raise JsonRpcError(e.get("code"), e.get("message"), e.get("data"))
    return resp.get("result")
