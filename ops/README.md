# ops — the lab toolchain

Four pieces, all plain text:

| File | Runs as | Purpose |
| --- | --- | --- |
| `lab-host-setup.sh` | root, once | create `/home/lab`, check tools, print what is missing |
| `lab-gen.py` | user | topology TOML → overlays, config disks, domain XML, net scripts |
| `lab-net.sh` | root | install/remove the bridges and the `lab_iso` nft table |
| `lab.sh` | user | the lifecycle CLI: `up`, `down`, `status`, `console`, `snapshot`, … |

Everything generated lands in `artifacts/` (gitignored) and everything stateful lands in
`/home/lab/` (or `$LAB_DATA`).

## Requirements on the lab host

- `qemu`, `libvirt` with the user in the `libvirt` group
- `python3` ≥ 3.11 (stdlib `tomllib`), `qemu-img`, `tar`
- `mkfs.vfat` (dosfstools) and `mcopy` (mtools) — the config disk is a FAT image, and
  mtools writes it without loop-mounting
- nested KVM enabled (`kvm_intel.nested=1` or `kvm_amd.nested=1`) — the vendor images are
  nested and will not boot without it

## Typical flow

```bash
sudo LAB_OWNER=$USER bash ops/lab-host-setup.sh
make up          # gate → generate → net-up (sudo) → define + start
make status
make console NODE=r1
make snapshot NODE=r1 NAME=pre-ospf
make down        # graceful pause; disks persist
make destroy     # removes domains, disks and the lab network
```
