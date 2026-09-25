# Disclosure

This sprint is documented in public. These are the rules for what may appear in a post,
screenshot, diagram or commit.

## Never in public

- Hostnames, IP addresses, ports or DNS names of any real machine or network.
- SSH configuration, keys, tokens, agent output, connection strings.
- Terminal screenshots with a prompt that reveals a username, hostname or working path
  outside this repository.
- Anything from a private or employer network: topologies, addresses or configurations.
- Real credentials of any kind. The lab's own throwaway login (`admin` / `admin@123`) is the
  only credential that ever appears, and it appears only because it is vendor-default.

## Safe by construction

- The addressing plan in [addressing.md](addressing.md) — all lab-private (`10.x`).
- Topology diagrams generated from the TOML topologies in this repository.
- The toolchain and its output, which name only `lab-*` objects.

## Screenshot checklist

1. Prompt shows no host identity (the lab tooling avoids printing it; shells may not).
2. No other windows, tabs, notifications or panes.
3. Addresses visible on screen are 10.x per the addressing plan.
4. Blur pass over anything uncertain — a blurred edge costs nothing, a leak cannot be undone.

## Framing

Write as an individual learning in public, not as a vendor or an employer. Claims about what
was done are supported by a commit in this repository; claims about what was learned are
personal and labelled as such.
