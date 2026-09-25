# Day 7 — Automation and DevOps

**Goal:** stop typing the same configuration. Generate it from data, load it, validate it,
and make the repository run the checks for you.

## Lab

Reuse `day-01-routing.toml` (two nodes is enough). The control node is the lab host itself —
Ansible and Python run there, over the `lab-mgmt` network. No extra VM and no Docker.

## Drill

1. **API first.** One raw NETCONF exchange by hand (`ssh admin@10.99.0.11 -p 830 -s netconf`),
   read the hello, then a `<get-config>`. Notice you are speaking to the same box as the CLI.
2. **Structured data.** The topology TOML already holds the addresses. Write a small script
   that turns a node entry into a Junos interface configuration. `ops/lab-gen.py` is the
   worked example — read it before writing yours.
3. **Ansible.** With the `junipernetworks.junos` collection: a playbook that loads the
   generated config, is idempotent on the second run, and fails loudly on an unsupported line.
4. **Validation.** After loading, read the config back and assert the intended state — a
   `show configuration` diff is not an assertion, it is a human looking at a diff. Make the
   check machine-decidable.
5. **CI on the repo.** `.github/workflows/validate.yml` already checks the tooling and the
   topologies on every push. Add a check for whatever you generated today. Watch it fail
   once before you trust it.

## Commands and tools to know

```text
ssh admin@<node> -p 830 -s netconf
ansible-galaxy collection install junipernetworks.junos
ansible-playbook -i <inventory> <playbook>.yml --check --diff
python3 -m pip install junos-eznc       # PyEZ, if you prefer library calls
```

## Deliverable

`day-07/automation/` — the generator, the playbook, the validation, and a README that says
what is idempotent and what still needs hands. This is the day the sprint stops being a lab
and starts being a pipeline.
