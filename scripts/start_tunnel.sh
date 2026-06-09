#!/usr/bin/env bash
# Start the VFP Tunnel daemon (convenience wrapper around `vfp tunnel start`).
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$here/vfp" tunnel start "$@"
