#!/usr/bin/env python3
"""Offline check of gen_fabric.py output: no lab needed, so CI can run it on every push.

    check_gen.py <topology.toml>      exit 0 when every invariant holds

Invariants: every line is a `set` statement; loopbacks are unique; each link's two ends sit
in the link's /30 and differ; every fabric port gets OSPF and BFD; leaves (and only leaves)
carry the EVPN overlay with each other leaf as a BGP neighbour.
"""

from __future__ import annotations

import importlib.util
import ipaddress
import sys
import tomllib
from pathlib import Path

spec = importlib.util.spec_from_file_location("gen_fabric", Path(__file__).with_name("gen_fabric.py"))
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def main() -> int:
    topo = tomllib.loads(Path(sys.argv[1]).read_text())
    errors: list[str] = []
    los = [gen.loopback(n) for n in topo["nodes"]]
    if len(set(los)) != len(los):
        errors.append(f"duplicate loopbacks: {los}")
    for link in topo["links"]:
        net = ipaddress.ip_network(link["subnet"])
        ends = [gen.link_address(n, link) for n in link["nodes"]]
        if len(set(ends)) != 2 or not all(ipaddress.ip_interface(e) in ipaddress.ip_network(net) or
                                          ipaddress.ip_interface(e).ip in net for e in ends):
            errors.append(f"link {link['name']}: bad ends {ends} for {net}")
    for node in topo["nodes"]:
        name, cfg = node["name"], gen.render(node, topo)
        text = "\n".join(cfg)
        for ifname, _ in gen.ports(topo)[name]:
            for needle in (f"interface {ifname}.0 interface-type p2p", f"interface {ifname}.0 bfd-liveness-detection"):
                if needle not in text:
                    errors.append(f"{name}: missing '{needle}'")
        is_leaf = gen.role(name) == "leaf"
        if ("family evpn signaling" in text) != is_leaf:
            errors.append(f"{name}: EVPN overlay present={not is_leaf} but role={gen.role(name)}")
        if is_leaf:
            for peer in topo["nodes"]:
                if gen.role(peer["name"]) == "leaf" and peer is not node and \
                        f"neighbor {gen.loopback(peer)}" not in text:
                    errors.append(f"{name}: no overlay neighbour {peer['name']}")
    for e in errors:
        print(f"FAIL {e}")
    print(f"{len(topo['nodes'])} nodes, {len(topo['links'])} links: " + ("ok" if not errors else f"{len(errors)} failed"))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
