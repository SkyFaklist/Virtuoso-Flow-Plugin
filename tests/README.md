# Tests

Python tests for VFP Tunnel and the shared schemas (28 passing).
`conftest.py` puts the in-repo `tunnel/` package on `sys.path`, so no
install is required.

Current suites:

- `test_jsonrpc.py` — JSON-RPC dispatcher (results, errors, notifications)
- `test_session.py` — session registry (persistence, current/touch)
- `test_tunnel_rpc.py` — end-to-end server + client roundtrip
- `test_skillrpc.py` — SKILL s-expression encoder
- `test_schemas.py` — schema validity + example conformance
- `test_context.py` — design-context store + `design.context.*` RPC

Later milestones add `test_transaction.py`, `test_constraints.py`,
`test_artifact_store.py`.

Run from the repository root:

```bash
pip install jsonschema pyyaml pytest   # or: pip install -e tunnel[dev]
pytest tests/
```
