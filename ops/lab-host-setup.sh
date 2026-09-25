#!/usr/bin/env bash
# One-time lab host preparation. Idempotent.
#   sudo LAB_OWNER=$USER bash ops/lab-host-setup.sh
#
# Creates the lab data directory and verifies the tools the toolchain needs.
# The directory's group is the user libvirt runs QEMU as, so domains can open the disks.
set -euo pipefail

DATA_DIR=${LAB_DATA:-/home/lab}
OWNER=${LAB_OWNER:-${SUDO_USER:-$(id -un)}}
GROUP=${LAB_GROUP:-}
QEMU_USER=

if [[ -z "$GROUP" && -r /etc/libvirt/qemu.conf ]]; then
  QEMU_USER=$(sed -n 's/^[[:space:]]*user[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' /etc/libvirt/qemu.conf | tail -1)
  GROUP=$(sed -n 's/^[[:space:]]*group[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' /etc/libvirt/qemu.conf | tail -1)
fi
GROUP=${GROUP:-libvirt}

if [[ $EUID -ne 0 ]]; then
  echo "error: run as root (sudo) — creating $DATA_DIR and setting ownership" >&2
  exit 1
fi

if ! getent group "$GROUP" >/dev/null; then
  echo "error: group '$GROUP' does not exist; set LAB_GROUP explicitly" >&2
  exit 1
fi

install -d -o "$OWNER" -g "$GROUP" -m 2770 "$DATA_DIR" "$DATA_DIR/images" "$DATA_DIR/domains"

echo "== storage"
echo "   $DATA_DIR  (owner $OWNER, group $GROUP, mode 2770)"
echo "   libvirt runs QEMU as user '${QEMU_USER:-unknown}' — the group is what grants disk access"

echo "== required tools"
missing=()
for tool in virsh qemu-img python3 tar mkfs.vfat mcopy; do
  if command -v "$tool" >/dev/null 2>&1; then
    echo "   ok      $tool"
  else
    echo "   MISSING $tool"
    missing+=("$tool")
  fi
done

if ((${#missing[@]})); then
  echo
  echo "Install the missing tools, then re-run:"
  echo "   Debian/Ubuntu: apt-get install dosfstools mtools qemu-utils libvirt-clients python3"
  echo "   Arch:          pacman -S dosfstools mtools qemu-full libvirt python"
  exit 1
fi

echo "== nested KVM"
nested=""
for f in /sys/module/kvm_intel/parameters/nested /sys/module/kvm_amd/parameters/nested; do
  [[ -r "$f" ]] && nested=$(cat "$f")
done
case "$nested" in
  Y|1|y) echo "   ok — nested KVM enabled" ;;
  "")    echo "   unknown — no kvm_intel/kvm_amd nested parameter found" ;;
  *)     echo "   WARNING: nested KVM is '$nested' — the vendor images will not boot" ;;
esac

echo "== libvirt round-trip"
virsh -c qemu:///system version | sed 's/^/   /'

echo
echo "ready. Put vendor images in $DATA_DIR/images, then: make up"
