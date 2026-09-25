# The seven-day plan

> **Learn → reproduce → change → break → troubleshoot → document → automate.**

Seven days, one growing topology. Every day's lab is built on yesterday's, and every drill
ends in a written note: what was expected, what happened, how it was diagnosed, what fixed it.

## Days

| Day | Focus | Hands-on | Topology |
| --- | --- | --- | --- |
| 1 | Junos fundamentals + CLI | interfaces, commit/rollback, `show` commands, first ping | r1, r2 |
| 2 | Routing + switching | static routes, longest-prefix, VLANs, trunks, inter-VLAN, OSPF | + r3, sw1, sw2 |
| 3 | Cloud networking | map VPC/VNet concepts onto the day-1/2 topology; segmentation design | reuse |
| 4 | Security | zones, firewall filters, management-plane protection, logging, deliberate breakage | reuse |
| 5 | Mist AI | architecture, WLAN/wired/WAN concepts, assurance — design work, no emulation | design |
| 6 | Data centre | spine/leaf, ECMP, EVPN-VXLAN leaf functions, failure domains | 2 spines, 2 leaves |
| 7 | Automation | Junos APIs, NETCONF, PyEZ/Ansible, config generation, validation, deployment | + control node |

## Resource profiles

Each topology declares its memory; `make up` refuses to start unless
`MemAvailable − 4 GiB` covers it.

| Topology | Nodes | Cart | RAM |
| --- | --- | --- | --- |
| `day-01-routing.toml` | 2 | r1, r2 | 10 GiB |
| day-01 extended | 3 | + r3 | 15 GiB |
| `day-02-switching.toml` | 3 | r1, r2, sw1 | 15 GiB |
| day-06 data centre | 4 | 2 spines, 2 leaves | 20 GiB |

Boot takes 5–15 minutes per node (they are nested VMs inside the VM image). Start the
topology first, then study while it boots.

## The daily loop

1. **Learn** — the day's Juniper material.
2. **Reproduce** — do exactly what the material demonstrates.
3. **Change** — modify the topology or configuration.
4. **Break** — introduce a mistake on purpose, then snapshot before you do.
5. **Troubleshoot** — find it with operational commands, not by re-reading config.
6. **Document** — write the note: expected / actual / diagnosed / fixed.
7. **Automate** — if you configured the same thing twice, generate the third.

## End state

By day 7 the repository contains: the topology-as-code toolchain, every day's configs and
notes, a spine/leaf design, and an automation path from structured data to a deployed and
validated configuration.
