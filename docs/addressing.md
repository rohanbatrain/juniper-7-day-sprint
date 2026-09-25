# Addressing plan

All addresses are lab-private. Nothing in this plan touches a real network.

## Management

`10.99.0.0/24` on the `lab-mgmt` bridge. The host is `.1`; nodes are static.

| Node | Address | Role |
| --- | --- | --- |
| host | 10.99.0.1 | gateway out of the lab is *not* provided; console access |
| lab-r1 | 10.99.0.11 | router |
| lab-r2 | 10.99.0.12 | router |
| lab-r3 | 10.99.0.13 | router |
| lab-sw1 | 10.99.0.21 | switch |
| lab-sw2 | 10.99.0.22 | switch |
| lab-spine1 | 10.99.0.31 | spine |
| lab-spine2 | 10.99.0.32 | spine |
| lab-leaf1 | 10.99.0.41 | leaf |
| lab-leaf2 | 10.99.0.42 | leaf |

The digits are deliberately mnemonic: routers `1x`, switches `2x`, spines `3x`, leaves `4x`.

## Point-to-point links

`10.0.AB.0/30`, where `A` and `B` are the node numbers of the two endpoints.

| Link | Subnet | Endpoints |
| --- | --- | --- |
| r1–r2 | 10.0.12.0/30 | .1 / .2 |
| r2–r3 | 10.0.23.0/30 | .1 / .2 |
| r1–r3 | 10.0.13.0/30 | .1 / .2 (added on day 2 for OSPF) |

## Loopbacks

`10.255.0.X/32`, one per router (`X` = node number). Loopbacks are the OSPF router-id
anchors and the first thing to ping when an adjacency is up but routes are not.

## VLANs (day 2 onward)

| VLAN | Name | Subnet | Purpose |
| --- | --- | --- | --- |
| 10 | USERS | 10.10.0.0/24 | access ports |
| 20 | SERVERS | 10.20.0.0/24 | access ports |
| 30 | MANAGEMENT | 10.30.0.0/24 | out-of-band (mirrors `lab-mgmt` in spirit, not in path) |

## Conventions

- Host addressing: `.1` of every link subnet; the lower-numbered node is `.1` unless the
  exercise says otherwise.
- Every configuration committed in this repo uses these ranges. If a screenshot shows
  anything else, it does not belong in a post.
