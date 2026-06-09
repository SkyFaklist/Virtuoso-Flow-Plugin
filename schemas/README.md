# `schemas/` — the VFP contract (canonical)

This directory is the **single source of truth** for the data contract
shared between the Virtuoso Flow Plugin (SKILL) and VFP Tunnel (Python).
Each file is a self-contained [JSON Schema](https://json-schema.org)
(draft 2020-12), version `0.1`.

| Schema | File | Used by |
|--------|------|---------|
| Design context | [`context.schema.json`](context.schema.json) | `design.context.update` (Milestone 3) |
| Proposal | [`proposal.schema.json`](proposal.schema.json) | `proposal.*` (Milestone 4) |
| Transaction | [`transaction.schema.json`](transaction.schema.json) | `transaction.*` (Milestone 5) |
| Result | [`result.schema.json`](result.schema.json) | `result.*` (Milestone 6) |
| Constraint file | [`constraint.schema.json`](constraint.schema.json) | `constraint.check` (Milestone 6) |

Worked examples live in [`../examples/rfc_classab_opa`](../examples/rfc_classab_opa)
(`sample_context.json`, `sample_proposal.json`, `constraints.yaml`).

## Validation

These schemas are the authoritative definitions. The tunnel daemon is
deliberately **stdlib-only** (it runs on the design server's Python 3.6),
so schema validation is **optional**: `tunnel/vfp_tunnel/rpc/schemas.py`
validates payloads with [`jsonschema`](https://pypi.org/project/jsonschema/)
when it is installed, and skips validation otherwise. Install it with the
`dev`/`validate` extra to enable it in development and CI.

## Why a top-level `schemas/`?

The plugin and tunnel co-evolve this contract. Keeping it in one place
(rather than duplicated under `skill/` and `tunnel/`) means:

- a contract change is one edit, reviewed once;
- if VFP Tunnel is later split into its own repository (via
  `git subtree split`), this directory is the natural shared dependency.

See [`../docs/development_notes.md`](../docs/development_notes.md) for the
repository-structure decision.
