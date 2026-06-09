"""Session manager facade.

Thin for now — the daemon owns a single :class:`Registry`. This module is
the stable import point and will grow session-policy logic (timeouts,
multi-session arbitration) in later work.
"""

from .registry import Registry

__all__ = ["Registry"]
