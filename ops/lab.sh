#!/usr/bin/env bash
# Juniper 7-Day Sprint — lab lifecycle CLI. Run from anywhere in the repo.
#
#   lab.sh up [topology]          memory gate, generate, net-up (sudo), define+start
#   lab.sh down [topology]        graceful pause (disks persist)
#   lab.sh status [topology]      domains + management addresses
#   lab.sh console NODE           serial console on lab-<NODE>
#   lab.sh ssh NODE               ssh admin@<mgmt-ip>
#   lab.sh snapshot NODE NAME     qcow2 snapshot
#   lab.sh restore NODE NAME      revert to snapshot
#   lab.sh net-up [topology]      bridges + nft only (sudo)
#   lab.sh net-down [topology]    remove bridges + nft (sudo)
#   lab.sh generate [topology]    artifacts only
#   lab.sh destroy [topology]     remove domains and disks, tear down net (asks)
#   lab.sh lint                   shellcheck + python + TOML checks
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
GEN="$ROOT/ops/lab-gen.py"
SYS=(virsh -c qemu:///system)

usage() { sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; }

topology_arg() {
  local topo=${1:-${TOPOLOGY:-$ROOT/lab/topologies/day-01-routing.toml}}
  [[ -f $topo ]] || { echo "error: no topology at $topo" >&2; exit 1; }
  printf '%s\n' "$topo"
}

topo_query() { python3 - "$1" <<PY
import sys, tomllib
topo = tomllib.load(open(sys.argv[1], "rb"))
nodes = topo["nodes"]
print($2)
PY
}

nodes_of() { topo_query "$1" '" ".join(n["name"] for n in nodes)'; }
mgmt_ip() { topo_query "$1" 'next(n["mgmt_ip"] for n in nodes if n["name"] == "'"$2"'")'; }

cmd_up() {
  local topo; topo=$(topology_arg "${1:-}")
  python3 "$GEN" --topology "$topo" --check
  python3 "$GEN" --topology "$topo"
  if ! ip link show lab-mgmt >/dev/null 2>&1; then
    echo "==> lab network up (sudo)"
    sudo bash "$ROOT/artifacts/lab-net-up.sh"
  fi
  local n dom
  for n in $(nodes_of "$topo"); do
    dom="lab-$n"
    if "${SYS[@]}" dominfo "$dom" >/dev/null 2>&1; then
      echo "== $dom already defined (make destroy + up to apply structural XML changes)"
    else
      "${SYS[@]}" define "$ROOT/artifacts/domains/$dom.xml" >/dev/null
      echo "== defined $dom"
    fi
    if [[ $("${SYS[@]}" domstate "$dom" 2>/dev/null || echo undefined) == running ]]; then
      echo "== $dom already running"
    else
      "${SYS[@]}" start "$dom" >/dev/null
      echo "== started $dom"
    fi
  done
  echo
  echo "nodes boot in 5-15 min.  watch: make console NODE=r1   status: make status"
}

cmd_down() {
  local topo; topo=$(topology_arg "${1:-}")
  local n dom state running
  for n in $(nodes_of "$topo"); do
    dom="lab-$n"
    state=$("${SYS[@]}" domstate "$dom" 2>/dev/null || echo undefined)
    if [[ $state != running ]]; then
      echo "== $dom ($state)"
      continue
    fi
    "${SYS[@]}" shutdown "$dom" && echo "== shutting down $dom"
  done
  for _ in $(seq 1 30); do
    running=""
    for n in $(nodes_of "$topo"); do
      dom="lab-$n"
      [[ $("${SYS[@]}" domstate "$dom" 2>/dev/null || echo undefined) == running ]] && running+="$dom "
    done
    [[ -z $running ]] && { echo "== all lab domains stopped"; return 0; }
    sleep 4
  done
  echo "warning: still running: $running" >&2
  echo "hint: if the guest ignores ACPI, power it off from its console first:" >&2
  echo "      request system power-off" >&2
  exit 1
}

cmd_status() {
  local topo; topo=$(topology_arg "${1:-}")
  "${SYS[@]}" list --all | sed -n '1,2p'
  "${SYS[@]}" list --all | grep -E 'lab-' || echo "  (no lab domains defined)"
  echo
  local n
  for n in $(nodes_of "$topo"); do
    printf '  %-12s %s\n' "lab-$n" "$(mgmt_ip "$topo" "$n")"
  done
}

cmd_console() { "${SYS[@]}" console "lab-${1:?usage: lab.sh console NODE}"; }

cmd_ssh() {
  local n=${1:?usage: lab.sh ssh NODE} topo
  topo=$(topology_arg "${2:-}")
  exec ssh -o StrictHostKeyChecking=accept-new "admin@$(mgmt_ip "$topo" "$n")"
}

cmd_snapshot() {
  local n=${1:?usage: lab.sh snapshot NODE NAME} name=${2:?usage: lab.sh snapshot NODE NAME}
  "${SYS[@]}" snapshot-create-as "lab-$n" "$name" --description "lab.sh snapshot"
}

cmd_restore() {
  local n=${1:?usage: lab.sh restore NODE NAME} name=${2:?usage: lab.sh restore NODE NAME}
  "${SYS[@]}" snapshot-revert "lab-$n" "$name"
}

cmd_net() {
  local action=$1 topo; shift
  topo=$(topology_arg "${1:-}")
  python3 "$GEN" --topology "$topo" --net-only
  sudo bash "$ROOT/artifacts/lab-net-$action.sh"
}

cmd_generate() { local topo; topo=$(topology_arg "${1:-}"); shift; python3 "$GEN" --topology "$topo" "$@"; }

cmd_destroy() {
  local topo; topo=$(topology_arg "${1:-}")
  echo "this removes these domains and their disks:"
  nodes_of "$topo" | tr ' ' '\n' | sed 's/^/  lab-/'
  read -r -p "continue? [y/N] " answer
  [[ $answer == [yY]* ]] || { echo aborted; exit 1; }
  local n dom
  for n in $(nodes_of "$topo"); do
    dom="lab-$n"
    "${SYS[@]}" destroy "$dom" 2>/dev/null || true
    "${SYS[@]}" undefine "$dom" 2>/dev/null || true
    rm -rf "${LAB_DATA:-/home/lab}/domains/$n"
    echo "== removed $dom"
  done
  if ip link show lab-mgmt >/dev/null 2>&1; then
    sudo bash "$ROOT/artifacts/lab-net-down.sh"
  fi
}

cmd_lint() {
  shellcheck "$ROOT"/ops/*.sh
  python3 -m py_compile "$GEN"
  python3 - "$ROOT" <<'PY'
import glob, sys, tomllib
files = sorted(glob.glob(sys.argv[1] + "/lab/topologies/*.toml"))
assert files, "no topologies found"
for f in files:
    tomllib.load(open(f, "rb"))
    print("ok:", f)
PY
}

case ${1:-help} in
  up)       shift; cmd_up "$@" ;;
  down)     shift; cmd_down "$@" ;;
  status)   shift; cmd_status "$@" ;;
  console)  shift; cmd_console "$@" ;;
  ssh)      shift; cmd_ssh "$@" ;;
  snapshot) shift; cmd_snapshot "$@" ;;
  restore)  shift; cmd_restore "$@" ;;
  net-up)   shift; cmd_net up "$@" ;;
  net-down) shift; cmd_net down "$@" ;;
  generate) shift; cmd_generate "$@" ;;
  destroy)  shift; cmd_destroy "$@" ;;
  lint)     cmd_lint ;;
  help|-h|--help) usage ;;
  *) echo "unknown command: ${1}" >&2; usage; exit 2 ;;
esac
