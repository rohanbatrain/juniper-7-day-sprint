# AGENTS.md — working in this repository

A seven-day, hands-on Juniper Junos lab sprint: topology-as-code on libvirt/KVM, built and
broken in public. This file is the entrypoint for any agent working here.

## Repo map

| Path | What |
| --- | --- |
| `ops/lab-gen.py` | topology TOML → config disks, qcow2 overlays, domain XML, net scripts |
| `ops/lab.sh` | lifecycle CLI: `up`, `down`, `status`, `console`, `snapshot`, `restore`, `destroy` |
| `ops/lab-bootstrap.py` | applies a node's config over its TCP console (see "Known issues") |
| `ops/lab-host-setup.sh` | one-time storage/tool setup on the lab host (root) |
| `ops/lab-net.sh` | bridges + nft isolation (root, generated) |
| `lab/topologies/*.toml` | one file per lab; nodes, links, addresses |
| `lab/nodes/init.conf.tmpl` | base Junos config rendered per node (no comments — see below) |
| `docs/build-log/day-N.md` | the public long-form write-ups posts link to |
| `day-01` … `day-07/` | daily objectives and drills |
| `artifacts/` | generated, gitignored |

The private lab book (`lab-book/`) is a **separate repository**, gitignored here. It holds
host facts, drafts and raw notes; it is not public and its URLs must never be linked.

## Ground rules

- **Verify the artifact, not the intention.** Read device state (`show …`), inspect
  generated files, compare sizes/labels/headers. Several bugs in this repo were found only
  that way (see `docs/build-log/day-0.md`).
- **Junos config files have no comment syntax.** The template must start with a real
  statement; `{# … #}` (Jinja) breaks `load`. Keep comments out of rendered configs.
- **Management addresses carry a prefix** — the topology stores a bare `mgmt_ip` and the
  renderer appends `/<mgmt_prefix>`; a bare address becomes a `/32` with no connected route.
- **Isolation is structural**: host-only bridges, no NAT, an `nft` table drops lab→host and
  all lab forwarding. Do not add an uplink to a lab bridge.
- Commits are signed; do not change the configured identity.
- Keep the public repo host-agnostic: no hostnames, real IPs, tokens.

## Running a lab (on the lab host)

```bash
python3 ops/lab-gen.py --topology lab/topologies/day-01-routing.toml   # generate
sudo bash artifacts/lab-net-up.sh                                      # bridges + nft (once)
virsh -c qemu:///system define artifacts/domains/lab-r1.xml            # define
virsh -c qemu:///system start lab-r1                                   # boot (5–15 min)
python3 ops/lab-bootstrap.py --topology lab/topologies/day-01-routing.toml --node r1
```

Nodes boot blank-ish: the console is a TCP device on `127.0.0.1:4500+n`, the serial log
lands in the node's data directory, and management access after bootstrap is SSH/NETCONF.

## Known issues

- **The vendor config disk is not consumed on vJunos 26.2** (attached and visible, never
  loaded). The console bootstrap (`ops/lab-bootstrap.py`) is the working path; the public
  build log documents the open question honestly.
- `virsh console` requires a controlling TTY and hangs in scripts — use the TCP console
  (`nc 127.0.0.1 <4500+n>`) or the log file.
- vJunos images are nested and cannot run inside a VM; the host needs nested KVM.

## Documentation duty

Every working session ends with: a `docs/build-log/day-N.md` update (public, sanitized), a
note in the private lab book, and — if a post is due — a draft in the post queue with the
build-log link ready. Do not publish claims that the repository cannot show.
