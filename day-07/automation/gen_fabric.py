#!/usr/bin/env python3
"""Topology TOML -> Junos `set` configuration for the day-06 spine/leaf fabric.

The topology already holds every fact the fabric needs: node names and roles, management
addresses, and the point-to-point links in data-port order. This script derives the rest:

- data ports: a node's Nth link (in file order) is ge-0/0/(N-1), as ops/lab-gen.py wires it;
- link addresses: the spine end is .1 of the /30, the leaf end .2;
- loopbacks: 10.255.0.<last octet of the management address> (spine1 = 10.255.0.31);
- underlay: OSPF area 0, point-to-point links with BFD (300 ms x 3), loopbacks passive;
- overlay (leaves only): iBGP EVPN between the leaf loopbacks, VXLAN VTEP on lo0, one
  stretched VLAN (100, VNI 10100) with an irb host address in a virtual-router per leaf.

Usage: gen_fabric.py <topology.toml> [--node NAME] [--outdir DIR]
Writes <outdir>/<node>.set (one `set` line per statement) and prints a summary.
"""

from __future__ import annotations

import argparse
import ipaddress
import sys
import tomllib
from pathlib import Path

ASN = 65000
VLAN_ID, VNI, VLAN_NAME = 100, 10100, "v100"
HOST_NET = ipaddress.ip_network("10.100.0.0/24")


def role(name: str) -> str:
    for r in ("spine", "leaf"):
        if name.startswith(r):
            return r
    raise SystemExit(f"node {name}: unknown role (expected spine* or leaf*)")


def loopback(node: dict) -> str:
    return f"10.255.0.{node['mgmt_ip'].rsplit('.', 1)[1]}"


def ports(topo: dict) -> dict[str, list[tuple[str, dict]]]:
    """node -> [(interface, link)], in the order lab-gen.py attaches the bridges."""
    out: dict[str, list[tuple[str, dict]]] = {n["name"]: [] for n in topo["nodes"]}
    for link in topo["links"]:
        for name in link["nodes"]:
            out[name].append((f"ge-0/0/{len(out[name])}", link))
    return out


def link_address(name: str, link: dict) -> str:
    net = ipaddress.ip_network(link["subnet"])
    if net.prefixlen != 30:
        raise SystemExit(f"link {link['name']}: expected a /30, got {net}")
    first, second = list(net.hosts())
    return f"{first if role(name) == 'spine' else second}/30"


def render(node: dict, topo: dict) -> list[str]:
    name, lo = node["name"], loopback(node)
    nodes = {n["name"]: n for n in topo["nodes"]}
    lines = [
        f"set interfaces lo0 unit 0 family inet address {lo}/32",
        f"set routing-options router-id {lo}",
        f"set routing-options autonomous-system {ASN}",
        "set protocols ospf area 0.0.0.0 interface lo0.0 passive",
    ]
    for ifname, link in ports(topo)[name]:
        lines += [
            f"set interfaces {ifname} description {link['name']}",
            f"set interfaces {ifname} unit 0 family inet address {link_address(name, link)}",
            f"set protocols ospf area 0.0.0.0 interface {ifname}.0 interface-type p2p",
            # a virtual link keeps carrier when the far end goes away; without BFD the only
            # detector is the 40 s OSPF dead interval (measured on day 6)
            f"set protocols ospf area 0.0.0.0 interface {ifname}.0 bfd-liveness-detection minimum-interval 300",
            f"set protocols ospf area 0.0.0.0 interface {ifname}.0 bfd-liveness-detection multiplier 3",
        ]
    lines.append("set policy-options policy-statement ECMP then load-balance per-packet")
    lines.append("set routing-options forwarding-table export ECMP")

    if role(name) == "leaf":
        peers = [loopback(n) for n in topo["nodes"] if role(n["name"]) == "leaf" and n["name"] != name]
        host_ip = HOST_NET.network_address + int(node["mgmt_ip"].rsplit(".", 1)[1])
        lines += [
            "set protocols bgp group overlay type internal",
            f"set protocols bgp group overlay local-address {lo}",
            "set protocols bgp group overlay family evpn signaling",
            *(f"set protocols bgp group overlay neighbor {p}" for p in peers),
            "set protocols evpn encapsulation vxlan",
            "set protocols evpn extended-vni-list all",
            "set switch-options vtep-source-interface lo0.0",
            f"set switch-options route-distinguisher {lo}:1",
            f"set switch-options vrf-target target:{ASN}:1",
            f"set vlans {VLAN_NAME} vlan-id {VLAN_ID}",
            f"set vlans {VLAN_NAME} vxlan vni {VNI}",
            f"set vlans {VLAN_NAME} l3-interface irb.{VLAN_ID}",
            f"set interfaces irb unit {VLAN_ID} family inet address {host_ip}/{HOST_NET.prefixlen}",
            "set routing-instances HOST instance-type virtual-router",
            f"set routing-instances HOST interface irb.{VLAN_ID}",
        ]
    assert all(l.startswith("set ") for l in lines)
    return lines


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("topology", type=Path)
    ap.add_argument("--node")
    ap.add_argument("--outdir", type=Path, default=Path("artifacts/fabric"))
    args = ap.parse_args()
    topo = tomllib.loads(args.topology.read_text())
    targets = [n for n in topo["nodes"] if args.node in (None, n["name"])]
    if not targets:
        sys.exit(f"no node named {args.node}")
    args.outdir.mkdir(parents=True, exist_ok=True)
    for node in targets:
        lines = render(node, topo)
        (args.outdir / f"{node['name']}.set").write_text("\n".join(lines) + "\n")
        print(f"{node['name']:7} {role(node['name']):5} lo0 {loopback(node):12} {len(lines):3} lines")


if __name__ == "__main__":
    main()
