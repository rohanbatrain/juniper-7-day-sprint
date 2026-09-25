# Day 2 — Routing and switching, seriously

**Goal:** L2 that behaves like a real access layer, L3 that routes between VLANs, and OSPF
across the routers.

## Lab

```bash
make up TOPOLOGY=lab/topologies/day-02-switching.toml
```

Requires `vJunos-switch-*.qcow2` in `/home/lab/images`. Declared memory is 19456 MiB.

| Node | Management | Role |
| --- | --- | --- |
| lab-r1 | 10.99.0.11 | router, inter-VLAN gateway, OSPF |
| lab-r2 | 10.99.0.12 | router, OSPF neighbour |
| lab-sw1 | 10.99.0.21 | access switch: VLAN 10 USERS, VLAN 20 SERVERS |

## Drill

1. On sw1: create VLANs 10 and 20, put two access ports in each, trunk the uplink to r1.
2. On r1: trunk toward sw1, IRB interfaces for both VLANs, verify hosts ping their gateway.
3. Break the trunk: drop the VLAN from the allowed list. Diagnose from both ends.
4. Bring up OSPF on the r1–r2 /30 and both loopbacks; verify adjacencies and routes.
5. Change an OSPF cost, watch the path change; roll the change back with `rollback`.
6. Snapshot first with `make snapshot NODE=sw1 NAME=pre-vlan`; break things freely.

## Commands to know

```text
show ethernet-switching table
show vlans
show interfaces ge-0/0/1.0 detail          # trunk: many VLAN tags
show spanning-tree bridge
show ospf neighbor / show ospf interface / show route protocol ospf
monitor traffic interface ge-0/0/0          # watch, then stop with Ctrl-C
```

## Log

Per drill: expected / actual / diagnosed / fixed. Day 2 is where "I can click it in a GUI"
stops being an excuse.
