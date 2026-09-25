# Architecture

The lab is a small fleet of libvirt/KVM virtual machines on one Linux host, wired together
with Linux bridges and driven by a thin toolchain in `ops/`.

## Why libvirt and not containerlab

Juniper's free `vJunos-*` images are **nested** — the outer VM starts a nested VM for the
control plane — and Juniper explicitly does not support launching them from inside another
VM. They must run first-level on the host. That removes the usual containerlab path
(vrnetlab containers wrap a QEMU process; the images remain bare-metal-only either way) and
leaves `qemu`/`libvirt` as the zero-daemon option: no Docker daemon, no privileged
containers, no new services. See [decisions/0001](decisions/0001-libvirt-over-containerlab.md).

## A node

Each topology node becomes one libvirt domain:

| Property | Value | Notes |
| --- | --- | --- |
| name | `lab-<node>` | prefixed so lab domains are obvious |
| vCPU | 4 | 3 for the forwarding plane + 1 for the control plane |
| memory | 5120 MiB | Juniper's documented minimum |
| CPU | `host-passthrough` | the nested control-plane VM needs `vmx`/`svm` exposed |
| disk | qcow2 overlay on a read-only base | `snapshot`/`restore` per node |
| config | 32 MiB raw FAT disk, label `vmm-data` | contains `config/juniper.conf` |
| NICs | virtio, first is management | port *n* maps to `ge-0/0/(n-1)` |
| console | pty serial | `virsh console lab-<node>` |
| autostart | never | the lab is started deliberately, every time |
| CPU shares | low | the desktop and any production VMs on the host win contention |

The config disk is attached over USB storage — the mechanism the vendor image expects — and
holds one tarball, `vmm-config.tgz`, containing `config/juniper.conf`. Bootstrapping a node
is therefore a file edit plus a regenerate; no console typing required.

## Networking

- `lab-mgmt` — host bridge with address `10.99.0.1/24`. Nodes get static management
  addresses from the topology. This is the only network attached to the host.
- `lab-l<n>` — one bridge per link in the topology, no address on the host. A virtual patch
  panel: each link is its own broadcast domain.
- There is **no uplink and no NAT**. A lab node has no route off the lab.

## Isolation

An `nft` table (`inet lab_iso`) is installed while the lab runs:

- input: new connections from `lab-mgmt` to the host are dropped (replies to host-initiated
  sessions are allowed, so `ssh` *to* a node and `virsh console` work);
- forward: any packet entering or leaving a `lab-*` interface is dropped.

The brute-force complement is structural: the bridges have no uplink, so there is nothing to
route to. The nft rules matter because the host has IP forwarding enabled for other guests.

## Storage

```text
/home/lab/                     owned <user>:<qemu-runtime-group>, mode 2770
├── images/                    vJunos base qcow2 images (read-only)
└── domains/                   per node
    ├── disk.qcow2             overlay, persists across up/down
    └── config.img             32 MiB FAT config disk, regenerated per `generate`
```

Artifacts that belong to the toolchain (domain XML, net scripts) are written to
`artifacts/` inside the repo and are gitignored.

## Lifecycle

| Command | Effect |
| --- | --- |
| `make generate` | topology → config disks, overlays, domain XML, net scripts |
| `make up` | memory gate, net-up, `virsh define` + `virsh start` every node |
| `make snapshot` / `make restore` | qcow2 snapshots per node — the break/fix loop |
| `make down` | graceful shutdown; disks and configs persist (the pause) |
| `make destroy` | undefine domains, delete node disks, tear the bridges down |

The tooling refuses to start a topology whose declared memory exceeds
`MemAvailable − 4 GiB`; a lab must never be the reason the host swappers.
