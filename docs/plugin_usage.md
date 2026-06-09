# Virtuoso Flow Plugin — Usage

## Requirements

- Cadence Virtuoso (developed against the IC23.1 SKILL API).
- VFP Tunnel running (see the [tunnel README](../tunnel/README.md)) for
  Connect / Export Context.

## Loading

In the Virtuoso **CIW**, either run the one-shot loader:

```lisp
load("/path/to/Virtuoso-Flow-Plugin/scripts/load_vfp.il")
```

or load the entry point and initialize manually:

```lisp
load("/path/to/Virtuoso-Flow-Plugin/skill/vfp_init.il")
vfpInit()
```

> Use forward slashes in SKILL paths, even on Windows.

### What you should see

- The CIW prints:
  `[VFP ...] Virtuoso Flow Plugin 0.1.0 initialized. Menu: "Virtuoso Flow".`
- A **Virtuoso Flow** pulldown menu appears in the CIW banner (and in any
  schematic window you open afterwards).
- `Virtuoso Flow → Open Dashboard` opens a panel showing:
  - VFP Tunnel connection status,
  - the current library / cell / view,
  - placeholders for ADE test and latest result,
  - **Connect / Export / Refresh / Rollback** buttons.

Open a schematic, then click **Refresh** on the dashboard — the
lib/cell/view fields update to the schematic you are editing.

## Connect and export context

With the tunnel running:

1. Click **Connect** — registers the Virtuoso session; the status field
   shows `Connected (s_…)` and a one-line tunnel summary.
2. With a schematic open, click **Export** — sends the schematic's
   instances, parameters, and connectivity to the tunnel. Verify on the
   tunnel host with `scripts/vfp context show`.

## Status

Milestones 1–3 are implemented: menu + dashboard + lib/cell/view
(M1), tunnel **Connect** (M2), and **Export Context** (M3). The remaining
buttons/menu items — Proposals, Apply, Rollback, Run Test — currently log
a "not implemented yet" message; they are wired up in later milestones.
See [`development_notes.md`](development_notes.md) for the roadmap.

## Unloading

```lisp
vfpUnload()
```

Removes the menu (from the CIW and schematic windows) and closes the
dashboard.

## Useful entry points

| SKILL | Effect |
|-------|--------|
| `vfpInit()` | Load modules, init state, install menu. |
| `vfpOpenDashboard()` | Open / raise the dashboard. |
| `vfpUpdateDashboard()` | Refresh dashboard fields from the current window. |
| `vfpConnect()` | Register the Virtuoso session with VFP Tunnel. |
| `vfpExportDesignContext()` | Send the current schematic context to the tunnel. |
| `vfpUnload()` | Remove menu and close dashboard. |
| `vfpGetVersion()` | Plugin version string. |
