#!/usr/bin/env python3
"""Load generated `set` files onto fabric nodes over NETCONF, then assert the result.

    deploy.py <topology.toml> [--outdir artifacts/fabric] [--check] [--validate-only]

Per node: lock, load the .set file (merge), print the diff, `commit check`, then commit.
A second run against an unchanged node produces an empty diff and no commit — that is the
idempotence test. --check stops after the diff.

Validation is machine-decidable and exits non-zero on the first failed assertion:
  1. every node has an OSPF neighbour in state Full on each of its fabric links;
  2. every node reaches every other loopback (ping sourced from its own loopback);
  3. each leaf has 2 equal-cost next hops to the other leaf's loopback (ECMP);
  4. each leaf's overlay BGP session to the other leaf is Established;
  5. each leaf's host address reaches the other leaf's host address in VLAN 100 (VXLAN).

Credentials: LAB_USER / LAB_PASSWORD (defaults are the lab's published defaults).
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
import tomllib
from pathlib import Path

from jnpr.junos import Device
from jnpr.junos.utils.config import Config

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("gen_fabric", HERE / "gen_fabric.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

USER = os.environ.get("LAB_USER", "admin")
PASSWORD = os.environ.get("LAB_PASSWORD", "admin@123")
failures: list[str] = []


def check(ok: bool, what: str) -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {what}")
    if not ok:
        failures.append(what)


def connect(node: dict) -> Device:
    dev = Device(host=node["mgmt_ip"], user=USER, password=PASSWORD, port=830, gather_facts=False)
    dev.open()
    dev.timeout = 120
    return dev


def deploy(node: dict, outdir: Path, check_only: bool) -> None:
    path = outdir / f"{node['name']}.set"
    with connect(node) as dev, Config(dev, mode="exclusive") as cu:
        cu.load(path=str(path), format="set", merge=True)
        diff = cu.diff()
        if not diff:
            print(f"{node['name']}: no change (idempotent)")
            return
        print(f"{node['name']}: {sum(1 for l in diff.splitlines() if l.startswith('+'))} lines added")
        if check_only:
            print(diff)
            cu.rollback()
            return
        cu.commit_check()
        cu.commit(comment="day-07 gen_fabric deploy")
        print(f"{node['name']}: committed")


def ping(dev: Device, target: str, source: str, instance: str | None = None) -> bool:
    kw = {"host": target, "count": "2", "rapid": True}
    kw.update({"routing_instance": instance} if instance else {"source": source})
    r = dev.rpc.ping(**kw)
    return r.find(".//ping-success") is not None


def validate(topo: dict) -> None:
    nodes = topo["nodes"]
    leaves = [n for n in nodes if gen.role(n["name"]) == "leaf"]
    for node in nodes:
        name, lo = node["name"], gen.loopback(node)
        print(f"{name}:")
        with connect(node) as dev:
            nbrs = dev.rpc.get_ospf_neighbor_information()
            full = {n.findtext("interface-name").strip() for n in nbrs.findall(".//ospf-neighbor")
                    if n.findtext("ospf-neighbor-state").strip() == "Full"}
            want = {f"{i}.0" for i, _ in gen.ports(topo)[name]}
            check(want <= full, f"OSPF Full on {sorted(want)} (have {sorted(full)})")
            for other in nodes:
                if other is not node:
                    check(ping(dev, gen.loopback(other), lo), f"ping {other['name']} lo0 {gen.loopback(other)}")
            if node in leaves:
                for peer in (l for l in leaves if l is not node):
                    plo = gen.loopback(peer)
                    rt = dev.rpc.get_route_information(destination=f"{plo}/32", table="inet.0")
                    hops = [h for h in rt.findall(".//rt-entry[current-active]/nh") if h.findtext("to")]
                    check(len(hops) == 2, f"ECMP: {len(hops)} next hops to {peer['name']} lo0")
                    bgp = dev.rpc.get_bgp_neighbor_information(neighbor_address=plo)
                    state = (bgp.findtext(".//peer-state") or "").strip()
                    check(state == "Established", f"overlay BGP to {peer['name']}: {state or 'absent'}")
                    phost = str(gen.HOST_NET.network_address + int(peer["mgmt_ip"].rsplit(".", 1)[1]))
                    check(ping(dev, phost, "", instance="HOST"), f"VXLAN: HOST ping {peer['name']} {phost}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("topology", type=Path)
    ap.add_argument("--outdir", type=Path, default=Path("artifacts/fabric"))
    ap.add_argument("--check", action="store_true", help="show the diff, do not commit")
    ap.add_argument("--validate-only", action="store_true")
    args = ap.parse_args()
    topo = tomllib.loads(args.topology.read_text())
    if not args.validate_only:
        for node in topo["nodes"]:
            deploy(node, args.outdir, args.check)
    if not args.check:
        validate(topo)
        print(f"\n{len(failures)} failed" if failures else "\nall assertions passed")
        sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
