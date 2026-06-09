"""Make the tunnel package importable without installing it."""

import pathlib
import sys

_TUNNEL = pathlib.Path(__file__).resolve().parents[1] / "tunnel"
if str(_TUNNEL) not in sys.path:
    sys.path.insert(0, str(_TUNNEL))
