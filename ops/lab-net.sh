#!/usr/bin/env bash
# Bring the lab network up or down. Requires root (bridges + nft).
#   sudo ops/lab-net.sh up   [topology]
#   sudo ops/lab-net.sh down [topology]
#
# The actual commands are generated from the topology by ops/lab-gen.py so the
# bridge and interface names always match the domain XML.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
action=${1:-}
TOPOLOGY=${2:-${TOPOLOGY:-$ROOT/lab/topologies/day-01-routing.toml}}

case "$action" in
  up|down) ;;
  *) echo "usage: $0 up|down [topology]" >&2; exit 2 ;;
esac

if [[ $EUID -ne 0 ]]; then
  echo "error: root required — sudo $0 $action" >&2
  exit 1
fi

python3 "$ROOT/ops/lab-gen.py" --topology "$TOPOLOGY" --net-only >/dev/null
bash "$ROOT/artifacts/lab-net-$action.sh"
