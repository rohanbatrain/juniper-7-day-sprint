# 0001 — Run the lab on libvirt directly, not containerlab

Status: accepted (2026-09-26)

## Context

The lab needs virtual Juniper routers and switches. The two candidate runtimes were:

1. **containerlab** with vrnetlab images — the community-standard way to run network labs.
2. **libvirt/KVM** directly, with the same vendor qcow2 images and hand-rolled wiring.

Two facts decide it:

- Juniper's free `vJunos-router` and `vJunos-switch` images are **nested**: the outer VM
  boots a nested VM for the control plane. The vendor documentation is explicit that they
  cannot be launched from inside a VM, and their recommended deployments are QEMU-KVM with
  libvirt (or bare-metal EVE-NG). That constraint applies to both runtimes — vrnetlab wraps
  a QEMU process in a container, but the image still runs on the physical host.
- The lab host already runs QEMU/libvirt for other work, and its hardening posture is
  "unprivileged QEMU processes, no services where none are needed". containerlab requires a
  Docker daemon and runs its nodes in privileged containers; both are new root-level
  machinery on a host whose design intentionally avoids it.

## Decision

Run the lab as **first-level libvirt domains on the existing KVM stack**, driven by a small
toolchain in `ops/`. No Docker daemon, no container runtime, no new services.

## Consequences

- The lab inherits the host's existing trust model: QEMU runs as the unprivileged runtime
  user that libvirt already uses, storage lives in a dedicated directory with group access,
  and there is no shared filesystem path into any guest.
- Topology ergonomics (veth wiring, lifecycle, link impairments) that containerlab provides
  are reimplemented in ~400 lines of shell + Python. `virsh` covers lifecycle; bridges cover
  wiring; `virsh console` covers access; qcow2 snapshots cover the break/fix loop.
- We lose containerlab features we have not needed yet (link impairments, `graph`). If a day
  requires them, that is a new decision with a named cost.
- The toolchain is plain text and reviewable; every generated artifact lands in `artifacts/`
  and is gitignored.

## Rejected alternatives

- **containerlab on the lab host.** Rejected on the daemon/privilege cost above, not on
  capability.
- **containerlab inside a VM.** Impossible: the images cannot run inside a VM.
- **vMX / vQFX.** Heavier memory footprints and licence friction for no learning benefit at
  this scale. `vJunos-router`/`vJunos-switch` are free of feature licences and are the
  current generation of the same idea.
