# Day 7 — automation and DevOps

*A seven-day, hands-on Juniper Junos lab — built as topology-as-code on plain libvirt/KVM.*

- Repository: [rohanbatrain/juniper-7-day-sprint](https://github.com/rohanbatrain/juniper-7-day-sprint)
- Previous: [Day 6](day-6.md)
- Tools: [day-07/automation/](../../day-07/automation/)

## The deviation, stated up front

The day-7 brief said reuse `day-01-routing.toml` — two routers is enough to learn the
tooling. I automated the day-06 spine/leaf fabric instead: four nodes and a real EVPN
overlay are a harder, more honest test of a generator than two routers that were already
hand-configured on day 1. The fabric itself had never been hand-configured — day 7 is the
only day it exists at all, and it exists because a script wrote it.

## API first

Before any script, one NETCONF exchange by hand: `ssh -p 830 -s admin@leaf1 netconf`. The
`<hello>` lists the capabilities the box actually offers — `base:1.0`, `candidate:1.0`,
`confirmed-commit:1.0`, `validate:1.0`, `url:1.0`, `ietf-netconf-monitoring`, yang metadata —
then a `<get-config>` of `lo0` comes back as the same configuration the CLI would show. It is
the same box, a different transport. Everything downstream today is this exchange, scripted.

## The generator

`gen_fabric.py` reads `day-06-datacenter.toml` — the topology already holds every fact the
fabric needs (node names and roles, management addresses, point-to-point links in
data-port order) — and derives the rest: data ports from link order, link addresses from the
link's `/30` (spine = `.1`, leaf = `.2`), loopbacks from the management address's last octet,
OSPF area 0 with BFD on every fabric link, and, leaves only, iBGP EVPN between leaf
loopbacks, a VXLAN VTEP on `lo0`, and VLAN 100 / VNI 10100 with a host address in a
per-leaf `virtual-router`. Output is one Junos `set` file per node: 16 lines for a spine, 31
for a leaf once BFD is in.

## First deploy: validation failed, honestly

`deploy.py` locks each node, merge-loads its `.set` file, prints the diff, `commit check`s,
commits. The first run added 52, 52, 91 and 91 lines across the four nodes and committed
clean. Validation ran immediately after — and **7 assertions failed**: spine1's second
fabric link wasn't `Full` yet, leaf1's overlay BGP was still `Active`, ECMP showed one next
hop instead of two, the VXLAN host ping hadn't converged. None of that was wrong; it was
early. A fresh commit needs time to converge and the check ran before it had any. Re-run
30 seconds later: all passed. The fix wasn't to loosen the assertions, it was to give them
time — validation now retries the whole set (4 attempts, 20 s apart) and reports the last
attempt. The check is allowed to fail. It just isn't allowed to fail quietly or only once.

## Idempotence

Second `deploy.py` run against an unchanged fabric: `no change (idempotent)` on all four
nodes. No diff, no commit check, no commit.

## Ansible, and the drift it repaired

`fabric.yml` does the same load through `junipernetworks.junos.junos_config` over
`ansible.netcommon.netconf`. Run 1 against the already-deployed fabric: `changed=0` on all
four. Then a hand drift: I deleted the `ge-0/0/1` interface description on leaf1 directly on
the box. Run 2: `changed=1` on leaf1, `changed=0` on the other three — Ansible put the
description back and touched nothing else. Run 3: `changed=0` on all four again. The
generator is the source of truth; a hand edit that disagrees with it gets quietly repaired,
not fought over.

## Failing loudly

I appended a line the box cannot parse — `hello-interval banana` — and loaded it. Junos
returned an `rpc-error`, `"Invalid numeric value: 'banana'"`, exit code 2. leaf2's last
successful commit is still the day-7 deploy; nothing half-applied. A bad statement is
rejected, not partially accepted.

## The BFD change: an 8-line diff

Day 6 ended on a gap: without BFD, a dead spine took the OSPF dead interval (40 s) to detect.
The fix went through the same pipeline that built the fabric: add
`bfd-liveness-detection minimum-interval 300` / `multiplier 3` to the generator's per-link
block, regenerate, redeploy. The diff this produced was BFD and nothing else — 8 lines added
per node. Validation passed on the first attempt. `show bfd session` on leaf1 then showed 2
sessions `Up`, detect time 0.900 s. Re-running day 6's spine-shutdown drill against the new
config: 1 next hop at the first sample, under a second, instead of 40.

## check_gen.py — the part CI can run today

`check_gen.py` checks the generator's own output offline, with no lab required: every line
is a `set` statement, loopbacks are unique, each link's two ends sit inside the link's `/30`
and differ, every fabric port carries OSPF and BFD, and only leaves carry the EVPN overlay,
each with every other leaf as a BGP neighbour. Against the real topology it exits 0. I then
gave leaf2 leaf1's management address in the topology file and re-ran it: `FAIL duplicate
loopbacks`, exit 1. The check catches a bad input before anything touches the fabric.

## What still needs hands

## CI, and watching it fail once

`.github/workflows/validate.yml` now runs on every push, with no lab needed: Python compiles,
shell scripts parse, every topology parses with unique node names and management addresses,
and `check_gen.py` passes on the fabric. It went green on `main`. Then I pushed a throwaway
branch carrying the same slip as above (leaf2 given leaf1's management address), and the run
failed where it should:

```text
FAIL lab/topologies/day-06-datacenter.toml duplicate mgmt_ip ['10.99.0.31', '10.99.0.32', '10.99.0.41', '10.99.0.41']
```

Branch deleted; `main` stayed green. A check you have never seen fail is a check you are
trusting on faith.

## What still needs hands

Also unautomated: booting the nodes and standing up the lab
networks still needs the host (`make up`); the merge load this pipeline uses cannot
*delete* a statement, so removing a line from the generator doesn't remove it from a box
(a `replace`/`override` load would, deliberately not used here); and the `nft` isolation
table on the host is still root-only.

## Next

The recap: what seven days and this pipeline add up to.
