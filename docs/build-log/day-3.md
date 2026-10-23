# Day 3 — a VPC, described by a network I built by hand

*A seven-day, hands-on Juniper Junos lab — built as topology-as-code on plain libvirt/KVM.*

- Repository: [rohanbatrain/juniper-7-day-sprint](https://github.com/rohanbatrain/juniper-7-day-sprint)
- Previous: [Day 2](day-2.md)
- Design note: [day-03/design.md](../../day-03/design.md)

## No new topology

Day 3 adds no new nodes. The day-2 lab (r1, r2 and a switch) already holds every primitive a
cloud network sells, so the job was to name them:

| Cloud | The lab |
| --- | --- |
| VPC | the lab-private ranges on isolated bridges |
| subnet | VLAN 10 → `10.10.0.0/24`, VLAN 20 → `10.20.0.0/24` |
| implicit VPC router | r1's router-on-a-stick subinterfaces |
| route table + propagation | `inet.0`, filled by OSPF |
| peering | the r1–r2 link and its adjacency |
| security group / NACL | a firewall filter, terms evaluated top-down |
| internet gateway, NAT gateway | **none** — no uplink, no default route |
| control plane | `fxp0` in its own routing table, `mgmt_junos` |

The two empty rows count most. `show route 0.0.0.0/0 exact` comes back empty on both
routers. A cloud calls a subnet "private" when its route table has no path to an internet
gateway, so by that definition every subnet here is private. An internet gateway is not a
box. It is a route plus a path, and this lab has neither on purpose.

## The test: routing is not access

I put a "security group" on r1's link to r2: allow OSPF, then count and discard anything
going to the servers subnet, then accept the rest. I committed it inside a 5-minute
`commit confirmed`, then tested from r2:

| From r2 | Before | After |
| --- | --- | --- |
| ping users gateway | 2/2 | 3/3 |
| ping servers gateway | 2/2 | **0/3** |
| OSPF neighbour | Full | Full |
| route to `10.20.0.0/24` | present | **still present** |

```text
admin@r1> show firewall filter SG-SERVERS
Counters:
Name                    Bytes    Packets
denied-to-servers         252          3
```

r2 kept the route to the servers subnet and lost the ability to use it. Three pings were
sent and three packets were counted, so the filter dropped them, not the routing. A route
table tells you where something is. Whether you may go there is a separate decision.

Two details worth keeping:

- **The OSPF term goes first.** A filter that discards the routing protocol breaks the
  route table, and after that every test result is meaningless.
- **The commit warned `requires 'L2 and L3 Filters' license`.** The lab image enforced the
  filter anyway. On real hardware, that warning is a purchase order.

I never confirmed the commit. Junos rolled it back by itself five minutes later and the
servers gateway answered again, which is the day-1 seatbelt doing its job on day 3.

## The design

The [design note](../../day-03/design.md) covers the rest: a services cluster
(`10.20.0.0/24`) and a management cluster (`10.30.0.0/24`) with least privilege between them.
Management may reach services over SSH and NETCONF, services may only reply, users get the
service port and nothing else, and the peer gets nothing until a rule names it.

The gap that shapes day 4: a cloud security group is **stateful** and lets replies back in
by itself. A Junos firewall filter is stateless, so "replies only" has to be written as a
rule. Zones are where Junos gets stateful.

## Next

Day 4: security. Stateless filters written properly, zones, protecting the management plane,
and a filter term that silently swallows traffic.
