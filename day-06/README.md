# Day 6 — Data centre: spine/leaf, ECMP, EVPN-VXLAN

**Goal:** design a small data-centre fabric and get the underlay real. Requires the
`vJunos-switch` image; vJunos-switch supports EVPN-VXLAN leaf functionality, so the overlay
is reachable, not aspirational.

## Lab

```bash
make up TOPOLOGY=lab/topologies/day-06-datacenter.toml
```

Declared memory is 24576 MiB — this one needs a quiet host.

```text
        spine1 (10.99.0.31)      spine2 (10.99.0.32)
            |    \              /    |
            |     \            /     |
          leaf1 (10.99.0.41)  leaf2 (10.99.0.42)
```

Underlay links: `10.0.<spine>.<leaf>.0/30` (e.g. spine1–leaf1 = 10.0.11.0/30).

## Drill

1. Underlay: address each link, advertise loopbacks with OSPF (or eBGP, pick one and say why
   in the log). Verify every loopback is reachable from every node.
2. ECMP: verify multiple equal paths in the forwarding table; kill one spine link and watch
   reconvergence.
3. Overlay: configure an EVPN-VXLAN leaf pair — VLAN-to-VNI mapping on the leaves, EVPN
   signalling over the loopbacks — and stretch one subnet across both leaves.
4. Failure domain: shut a spine; note what changed and what did not. Write down the blast
   radius in the design note.
5. Snapshot before each failure. `make snapshot NODE=leaf1 NAME=pre-evpn`.

## Commands to know

```text
show route table inet.0 protocol ospf
show route forwarding-table
show ethernet-switching vxlan-tunnel-end-point
show evpn database
show bgp summary
show l2-learned-hosts
```

## Deliverable

`day-06/design.md` — fabric diagram, underlay/overlay addressing, failure-domain notes, and
the one thing you would do differently on real hardware.
