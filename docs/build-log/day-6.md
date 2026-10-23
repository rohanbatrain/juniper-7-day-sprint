# Day 6 — a spine/leaf fabric, and a spine shutdown that found a real gap

*A seven-day, hands-on Juniper Junos lab — built as topology-as-code on plain libvirt/KVM.*

- Repository: [rohanbatrain/juniper-7-day-sprint](https://github.com/rohanbatrain/juniper-7-day-sprint)
- Previous: [Day 5](day-5.md)
- Design note: [day-06/design.md](../../day-06/design.md)

## Four nodes, run alongside day 2

The day-6 topology brought up spine1, spine2, leaf1 and leaf2 — all vJunos-switch 26.2R1.7 —
side by side with the still-running day-2 lab. `lab-gen.py` gained `ordinal_base` and
`link_prefix` specifically so the two labs could coexist: different MACs (02:..:0b–0e),
different console ports (4511–4514), different bridges (`lab-dc1..4`). Seven vJunos nodes on
the host at once, with ~42 GiB free afterward. The fabric booted in about 15 minutes, with
the host's load average at 16.

## Configured by the pipeline, not by hand

Everything on this fabric — underlay, overlay, BFD — came from `day-07/automation/gen_fabric.py`,
the generator built on day 7. No node here was ever hand-configured. The design: OSPF area 0
underlay on point-to-point links, loopbacks at `10.255.0.<mgmt octet>`, spine `.1` / leaf `.2`
on each `/30`; iBGP AS 65000 EVPN directly between the two leaves' loopbacks, with the spines
carrying no BGP at all ("lean spine"); VXLAN VTEP on `lo0`; VLAN 100 mapped to VNI 10100; and
`irb.100` (10.100.0.41 / .42) living in a `HOST` virtual-router instance on each leaf.

## Evidence, from leaf1

- Route to leaf2's loopback (10.255.0.42/32): OSPF metric 2, two next hops — 10.0.11.1 via
  ge-0/0/0.0 and 10.0.21.1 via ge-0/0/1.0.
- Forwarding table: a `ulst` (unilist) holding both `ucst` next hops — ECMP in the FIB, not
  just the RIB.
- VTEP state: local VTEP 10.255.0.41 on lo0.0; remote VTEP 10.255.0.42 on vtep.32769, VNID
  10100.
- EVPN database: MAC 2c:6b:f5:82:6b:f0 learned from 10.255.0.42 (IP 10.100.0.42); irb.100
  (10.100.0.41) local.
- BGP summary: neighbor 10.255.0.42, AS 65000, Establ.
- A ping across the VXLAN overlay, 10.100.0.41 → 10.100.0.42: success.

## Drill 1 — pull a local link

Disabling leaf1's ge-0/0/0 (toward spine1) dropped the route from two next hops to one, via
spine2, immediately. BGP stayed Established. 40 of 40 HOST pings across the change succeeded.
A local interface disable is carrier loss, and carrier loss is instant.

## Drill 2 — shut the spine itself

This is the one worth sitting with. Shutting both fabric ports *on spine1* left leaf1's
ge-0/0/0 reporting `up up` — the virtual bridge underneath kept carrier even with the far end
gone. leaf1 held both next hops for 37 seconds, then dropped to one at t=40 s: the OSPF
default dead-interval, with nothing shortening it. HOST pings were 4/4 the whole time,
consistent with that flow having hashed onto the surviving spine2 path — any flow that had
hashed onto spine1 would have gone dark for up to 40 seconds, invisibly, because this
particular ping test never touched it. spine2 kept both of its Full OSPF neighbours, and the
leaf-to-leaf overlay BGP session never blinked. The blast radius of a dead spine: half the
ECMP paths, never the overlay — but *detection* without BFD is an OSPF dead-interval away,
which at default settings is 40 seconds.

## The fix went through the pipeline

The generator added BFD — 300 ms × 3 — on each fabric-facing interface. The deploy diff was 8
lines per node, BFD only. Validation passed on the first attempt. `show bfd session` on leaf1
showed 2 sessions Up, detect time 0.900 s. Re-running drill 2: leaf1 dropped to one next hop
at the *first* sample taken, t=0 s — under roughly a second. 40 seconds down to under 1.

## Next

Day 7: automation. The fabric built today was never hand-configured — the generator, the
NETCONF deploy pipeline, and the validation retries that caught a real race all ran against
it instead.
