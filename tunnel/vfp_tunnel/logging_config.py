"""Logging setup for VFP Tunnel (console + ``.vfp/logs/vfp_tunnel.log``)."""

import logging

from .config import ensure_dirs, log_dir

_CONFIGURED = set()


def get_logger(name="vfp_tunnel", to_file=True, level=logging.INFO):
    logger = logging.getLogger(name)
    if name in _CONFIGURED:
        return logger
    logger.setLevel(level)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    if to_file:
        try:
            ensure_dirs()
            fh = logging.FileHandler(str(log_dir() / "vfp_tunnel.log"))
            fh.setFormatter(fmt)
            logger.addHandler(fh)
        except OSError:
            pass
    _CONFIGURED.add(name)
    return logger
