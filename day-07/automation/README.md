# Day 7 — the fabric as a pipeline

Structured data in, validated fabric out. Everything runs on the lab host over the
management network (`10.99.0.0/24`); no extra VM, no Docker.

| File | What |
| --- | --- |
| `gen_fabric.py` | `day-06-datacenter.toml` → one Junos `set` file per node (underlay, BFD, EVPN-VXLAN overlay) |
| `deploy.py` | loads the set files over NETCONF (PyEZ), commits, then runs machine-decidable assertions |
| `fabric.yml` + `inventory.yml` | the same load with Ansible (`junipernetworks.junos.junos_config`) |

```bash
python3 -m venv .venv && .venv/bin/pip install junos-eznc ansible-core ncclient jxmlease
.venv/bin/ansible-galaxy collection install junipernetworks.junos ansible.netcommon

.venv/bin/python day-07/automation/gen_fabric.py lab/topologies/day-06-datacenter.toml
.venv/bin/python day-07/automation/deploy.py lab/topologies/day-06-datacenter.toml --check   # diff only
.venv/bin/python day-07/automation/deploy.py lab/topologies/day-06-datacenter.toml           # commit + validate
.venv/bin/ansible-playbook -i day-07/automation/inventory.yml day-07/automation/fabric.yml   # same, via Ansible
```

## What the validation asserts

Exit code is the verdict. It retries the whole set (default 4 × 20 s) because a fresh commit
needs time to converge. The first run of this tool failed 7 assertions for exactly that reason.

1. OSPF `Full` on every fabric link of every node
2. every loopback reaches every other loopback
3. each leaf has 2 equal-cost next hops to the other leaf (ECMP)
4. the leaf-to-leaf EVPN BGP session is `Established`
5. each leaf's host address in VLAN 100 reaches the other's, across VXLAN

## Idempotent vs still needs hands

| Idempotent | Still needs hands |
| --- | --- |
| re-running `deploy.py` or `fabric.yml` on an unchanged fabric: empty diff, no commit | booting nodes and creating the lab networks (`make up`, needs the host) |
| repairing drift: a hand-deleted statement is restored, nothing else touched | **removing** a statement: the load is a merge, so deleting a line from the generator does not delete it from the box (a `replace`/`override` load would; deliberately not used on a shared box) |
| adding BFD fabric-wide: change the generator, redeploy, the diff is the BFD lines only | the `nft` isolation table (root) |
