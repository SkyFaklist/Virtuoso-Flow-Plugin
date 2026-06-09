"""Session manager facade.

Thin for now — the daemon owns a single :class:`Registry`. This module
exists as the documented entry point (project.md section 9) and will grow
session-policy logic (timeouts, multi-session arbitration) in later work.
"""

from .registry import Registry

__all__ = ["Registry"]
