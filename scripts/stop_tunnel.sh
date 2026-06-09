#!/usr/bin/env bash
# Stop the VFP Tunnel daemon (convenience wrapper around `vfp tunnel stop`).
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$here/vfp" tunnel stop "$@"
