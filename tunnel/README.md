# VFP Tunnel

External bridge daemon for the [Virtuoso Flow Plugin](../README.md). It
exposes a localhost JSON-RPC API (default `127.0.0.1:47891`) and a `vfp`
CLI to AI agents and scripts, and manages sessions, proposals,
transactions, simulation results, constraints, and artifacts.

**Status:** Milestones 2–3 (daemon + CLI + sessions + design-context
storage) implemented. Pure stdlib, runs on Python **3.6+** (the design
server's system python). Proposal/transaction/result/constraint methods
arrive in later milestones.

## Run

On the design server (no install needed — Python 3.6):

```bash
scripts/vfp tunnel start
scripts/vfp tunnel status
scripts/vfp session list
scripts/vfp tunnel stop
```

On a dev machine with Python 3.7+ you can also install it:

```bash
cd tunnel
pip install -e .[dev]
vfp tunnel start
```

Configuration via environment: `VFP_HOST`, `VFP_PORT`, `VFP_HOME`
(artifact root, default `./.vfp`).

## JSON-RPC methods (Milestones 2–3)

| Method | Result |
|--------|--------|
| `session.register` | `{session_id, registered_at}` from `{client}` |
| `session.ping` | `{pong, time, session_id}` (touches the session) |
| `session.status` | the session record for a `session_id` |
| `session.list` | `{sessions: [...]}` |
| `session.current` | most-recently-active session |
| `design.context.update` | store a design context (`{context}`) → `{stored, path}` |
| `design.context.get` | `{context}` — the latest stored context |
| `tunnel.status` | version, host/port, pid, uptime, session count |
| `tunnel.shutdown` | graceful stop |

Messages are JSON-RPC 2.0, one object per line (`\n`-framed) over TCP.

## Layout

```
vfp_tunnel/
  cli.py daemon.py config.py logging_config.py skillrpc.py
  rpc/{jsonrpc,transport,schemas}.py
  session/{registry,manager}.py
  design/context.py
  proposal/ transaction/ sim/ constraints/ artifact/ agent/   # later
```

See [`../schemas/`](../schemas) for the data contract.

## Tests

```bash
cd ..            # repo root
pytest tests/    # 28 passing
```
