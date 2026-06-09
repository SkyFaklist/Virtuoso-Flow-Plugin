# Development Notes

## Repository structure decision

**Monorepo** (both `skill/` and `tunnel/` in this repository), decided
2026-06-09.

Rationale: the SKILL plugin and the Python tunnel share one contract
(the JSON-RPC method set + the five schemas under `schemas/`). During the
MVP this contract changes frequently and must change atomically on both
sides — a monorepo makes that a single reviewed commit and keeps
end-to-end testing/demo to a single checkout.

The door to splitting `tunnel/` into its own repository later stays open:
`git subtree split` (or `git filter-repo`) extracts it with history
cheaply. Splitting first and merging later would be harder. The shared
`schemas/` directory is structured to become the split point's shared
dependency.

## Milestone status

| # | Milestone | Status |
|---|-----------|--------|
| 1 | Virtuoso plugin skeleton (menu, dashboard, lib/cell/view) | **done** |
| 2 | VFP Tunnel skeleton (CLI, JSON-RPC, session) | **tunnel done**; SKILL rpc client (M2b) next |
| 3 | Design context export | not started |
| 4 | Proposal workflow | not started |
| 5 | Transactional parameter modification + rollback | not started |
| 6 | Result + constraint display | not started |
| 7 | ADE/Spectre integration | not started |

## Milestone 1 — what's implemented

- `skill/vfp_utils.il` — runtime state (DPL), logging, cellview helpers.
- `skill/vfp_init.il` — `vfpLoad` / `vfpInit` / `vfpUnload` / `vfpGetVersion`.
- `skill/vfp_menu.il` — "Virtuoso Flow" menu; CIW + schematic install.
- `skill/vfp_dashboard.il` — dashboard form; live lib/cell/view.
- The remaining `skill/vfp_*.il` files are loadable stubs whose function
  signatures match `project.md` §8 and log "not implemented yet".

## Milestone 2 — what's implemented (tunnel side)

Python daemon + `vfp` CLI, **stdlib-only and Python 3.6+** (the design
server runs CentOS 7 / 3.6.8, and the tunnel must run there so the
in-Virtuoso SKILL client can reach it on localhost).

- `tunnel/vfp_tunnel/rpc/jsonrpc.py` — JSON-RPC 2.0 dispatcher.
- `tunnel/vfp_tunnel/rpc/transport.py` — newline-framed JSON over TCP:
  threaded server + a small blocking client.
- `tunnel/vfp_tunnel/session/registry.py` — session registry (in-memory +
  JSON persistence under `.vfp/sessions/`).
- `tunnel/vfp_tunnel/daemon.py` — `Tunnel`: methods + lifecycle/state file.
  Methods: `session.register/ping/status/list/current`,
  `tunnel.status/shutdown`.
- `tunnel/vfp_tunnel/cli.py` — `vfp tunnel start|stop|status`,
  `vfp session list|current`, `vfp ping`.
- `scripts/vfp` — runs the CLI without installing (sets `PYTHONPATH`);
  the no-install path for the 3.6 server. `start_tunnel.sh`/`stop_tunnel.sh`
  wrap it.

Default endpoint `127.0.0.1:47891` (override via `--host/--port` or
`VFP_HOST/VFP_PORT`); artifact root `./.vfp` (override via `VFP_HOME`).
`tunnel start` spawns the daemon detached (cross-platform: `start_new_session`
on POSIX, `DETACHED_PROCESS` on Windows) and polls `tunnel.status` until ready.

Verified: `pytest tests/` (15 passing) on Windows 3.14, plus a full CLI
smoke test (start→status→register→ping→list→stop) on **both** Windows 3.14
and the server's Python 3.6.8.

**Next (M2b):** SKILL-side `vfp_rpc_client.il` — speak the same
newline-framed JSON-RPC from inside Virtuoso (likely via an `ipcBeginProcess`
helper, since base SKILL has no raw TCP sockets) and wire the dashboard
Connect/Refresh to `session.register` / `tunnel.status`.

## SKILL implementation notes

- **Self-locating load.** `vfp_init.il` and `scripts/load_vfp.il` resolve
  their own directory via `get_filename(piport)` (the input port of the
  file being loaded), so module loading does not depend on Virtuoso's
  current working directory. Override with the global `VFP_SKILL_DIR` if
  needed.
- **Menu install.** Inserted into the CIW banner with `hiInsertBannerMenu`
  at a large index (append). For schematic windows a post-install trigger
  is registered via `deRegUserTriggers("schematic" nil nil 'fn)` — note
  the post-install trigger is the **4th** argument.
- **Menu removal.** `vfpUnregisterMenu` finds the menu's position with
  `hiGetBannerMenus` and deletes it via `hiDeleteBannerMenu`, per window.
- **Dashboard fields.** Read-only `hiCreateStringField`s for lib/cell/view
  and an `hiCreateMLTextField` for the result/constraint summary; values
  are refreshed by assigning `form->fieldSym->value`.
- **Cellview probing.** Use the `win->editCellView` *property* (quiet,
  nil for non-graphic windows) — not `geGetEditCellView(win)`, which
  emits a `GE-2067` warning when called on the CIW or a form window.
  `errset` does not suppress that warning because it is a warning, not an
  error.

## API reference

The Cadence SKILL reference for IC23.1 is bundled under
`docs/IC231_gui_plugin_docs/` (skuiref = UI, sklangref = language,
skdfref = design framework, etc.). Prefer it over guessing signatures.
