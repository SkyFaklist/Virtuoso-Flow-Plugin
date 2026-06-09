"""Optional JSON-Schema validation against the canonical ``schemas/`` dir.

Validation is a no-op unless the third-party ``jsonschema`` package is
installed, so the daemon stays stdlib-only on the design server (Python
3.6). Install the ``validate`` (or ``dev``) extra to enable it.
"""

import json
import os
from pathlib import Path

_CACHE = {}


def schemas_dir():
    env = os.environ.get("VFP_SCHEMAS_DIR")
    if env:
        return Path(env)
    # rpc/schemas.py -> vfp_tunnel -> tunnel -> <repo root>/schemas
    return Path(__file__).resolve().parents[3] / "schemas"


def load(name):
    """Return the parsed schema for ``<name>.schema.json`` (or None)."""
    if name in _CACHE:
        return _CACHE[name]
    path = schemas_dir() / (name + ".schema.json")
    schema = None
    if path.exists():
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            schema = None
    _CACHE[name] = schema
    return schema


def enabled():
    """True if validation can actually run (jsonschema importable)."""
    try:
        import jsonschema  # noqa: F401
        return True
    except ImportError:
        return False


def validate(name, data):
    """Validate ``data`` against ``schemas/<name>.schema.json``.

    Returns True if validated, None if skipped (jsonschema or the schema
    file unavailable). Raises ``jsonschema.ValidationError`` on a real
    violation.
    """
    try:
        import jsonschema
    except ImportError:
        return None
    schema = load(name)
    if schema is None:
        return None
    jsonschema.validate(data, schema)
    return True
