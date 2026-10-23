# Day 4 — security: zones, filters, segmentation

Evidence: captured live on the lab on 2026-10-23, day-02 topology (r1, r2, sw1). No new nodes.

## Trust zones, on paper

| Zone | What it is | Lab object |
| --- | --- | --- |
| INTERNET | outside the lab | does not exist — no uplink |
| USERS | clients | VLAN 10, `10.10.0.0/24`, gateway `ge-0/0/1.10` on r1 |
| SERVERS | workloads | VLAN 20, `10.20.0.0/24`, gateway `ge-0/0/1.20` on r1 |
| MANAGEMENT | control plane | `fxp0` / lab-mgmt, `10.99.0.0/24` |

Setup for the day: sw1's "user host" is `irb.10 = 10.10.0.10/24` in virtual-router USER,
default via `10.10.0.1`. Its traffic must cross r1's `ge-0/0/1.10` (the users subinterface)
to reach anything in SERVERS.

Baseline, no filter yet, from USER:

- `ping 10.20.0.1`: 3/3
- `telnet 10.20.0.1 port 22` → Connected
- `telnet 10.20.0.1 port 80` → Connection refused (path open, nothing listening)

## Filter 1 — F-USERS-IN (r1, `ge-0/0/1.10` input)

Terms in order, reconstructed from the evidence term list:

```text
set firewall family inet filter F-USERS-IN term dns from protocol [ udp tcp ]
set firewall family inet filter F-USERS-IN term dns from destination-port 53
set firewall family inet filter F-USERS-IN term dns from destination-address 10.20.0.0/24
set firewall family inet filter F-USERS-IN term dns then accept

set firewall family inet filter F-USERS-IN term web from protocol tcp
set firewall family inet filter F-USERS-IN term web from destination-port [ 80 443 ]
set firewall family inet filter F-USERS-IN term web then count users-web
set firewall family inet filter F-USERS-IN term web then accept

set firewall family inet filter F-USERS-IN term icmp from protocol icmp
set firewall family inet filter F-USERS-IN term icmp then count users-icmp
set firewall family inet filter F-USERS-IN term icmp then accept

set firewall family inet filter F-USERS-IN term deny-servers from destination-address 10.20.0.0/24
set firewall family inet filter F-USERS-IN term deny-servers then count users-denied
set firewall family inet filter F-USERS-IN term deny-servers then log
set firewall family inet filter F-USERS-IN term deny-servers then syslog
set firewall family inet filter F-USERS-IN term deny-servers then discard

set firewall family inet filter F-USERS-IN term rest then accept

set interfaces ge-0/0/1 unit 10 family inet filter input F-USERS-IN
```

`commit confirmed 10` → warning: requires 'L2 and L3 Filters' license.

### Drill — verify the permit set

- **Expected:** DNS, HTTP/S and ICMP from USERS to SERVERS pass; everything else to SERVERS
  is denied and logged.
- **Actual:** `ping 10.20.0.1`: 3/3. `telnet` port 80: "Connection refused" (the TCP SYN was
  permitted through the filter and reached the box — nothing listens on 80). `telnet` port
  22: "Operation timed out" (dropped by the filter; no RST ever comes back).
- **Diagnosed:** counters confirm which path each probe took — `users-denied` 576 B / 9 pkts
  (the SYN retries from the timed-out port-22 attempt), `users-icmp` 252 B / 3, `users-web`
  64 B / 1. `show firewall log` shows the drop directly: `17:23:25 pfe D ge-0/0/1.10 TCP
  10.10.0.10 10.20.0.1` (shown ×4).
- **Fixed:** nothing to fix — the filter behaved as written. The lesson was in the
  diagnosis, not a repair: "refused" vs "timed out" already tells permit from drop before a
  counter is even read.

Drill note on step 3 of the README: `monitor traffic` was **not run** for this drill. The
evidence instead used the firewall log (`show firewall log`) plus the filter's own counters
to watch the drop — both accomplish the same diagnosis the drill asked for, but the packet
capture itself was never taken.

## Filter 2 — PROTECT-RE (r1, `lo0.0` input)

```text
set firewall family inet filter PROTECT-RE term ospf from protocol ospf
set firewall family inet filter PROTECT-RE term ospf then accept

set firewall family inet filter PROTECT-RE term mgmt from source-address 10.99.0.0/24
set firewall family inet filter PROTECT-RE term mgmt from protocol tcp
set firewall family inet filter PROTECT-RE term mgmt from destination-port [ 22 830 ]
set firewall family inet filter PROTECT-RE term mgmt then accept

set firewall family inet filter PROTECT-RE term icmp from protocol icmp
set firewall family inet filter PROTECT-RE term icmp then accept

set firewall family inet filter PROTECT-RE term established from protocol tcp
set firewall family inet filter PROTECT-RE term established from tcp-established
set firewall family inet filter PROTECT-RE term established then accept

set firewall family inet filter PROTECT-RE term deny then count re-denied
set firewall family inet filter PROTECT-RE term deny then log
set firewall family inet filter PROTECT-RE term deny then discard

set interfaces lo0 unit 0 family inet filter input PROTECT-RE
```

`commit confirmed 3`.

### Drill — protect the management plane

- **Expected:** SSH/NETCONF from the management subnet only; existing management sessions
  survive the commit; OSPF and r1's own outbound TCP replies still work.
- **Actual:** before the filter, `telnet 10.10.0.1 port 22` from USER → Connected. After:
  → Operation timed out. A **new** management SSH session opened from the host fine during
  the `commit confirmed` window (then confirmed). r2's OSPF adjacency to r1 stayed Full.
- **Diagnosed:** `re-denied` counter: 576 B / 9 pkts — USER's attempt was the thing being
  counted as denied, confirming the drop was the filter and not a path problem. The
  `established` term exists for a structural reason carried over from day 3: filters are
  stateless, so r1's own outbound TCP sessions need their replies let back in by an explicit
  rule — nothing does that automatically, unlike a stateful security group.
- **Fixed:** nothing broken — filter matched intent. The management session and OSPF both
  proved the filter admitted exactly what it should and nothing else.

## Drill 3 — break it: the shadow term

```text
set firewall family inet filter F-USERS-IN term quarantine from source-address 10.10.0.0/24
set firewall family inet filter F-USERS-IN term quarantine then discard
insert firewall family inet filter F-USERS-IN term quarantine before term dns
```

- **Expected:** a bad insert above the permits should break USER→SERVERS traffic, and the
  existing counters (`users-denied`, `users-icmp`, `users-web`) should show where.
- **Actual:** from USER, `ping 10.20.0.1`: 0/3. `show firewall filter F-USERS-IN`:
  `users-denied` 0, `users-icmp` 0, `users-web` 0 — every counter silent.
- **Diagnosed:** "every counter is zero" is itself the finding — the packet died somewhere
  not being counted. `show configuration firewall ... | display set` showed `quarantine` as
  the first term, with no counter action attached to it, so nothing it dropped was ever
  tallied anywhere. Proof: added `count shadowed` to the quarantine term → ping still 0/3 →
  `shadowed` 252 B / 3 pkts, while `users-icmp` stayed 0. The traffic was being caught by
  the new first term before it ever reached `dns`, `web` or `icmp`.
- **Fixed:** `rollback 2` → diff showed only the `quarantine` term removed → `ping
  10.20.0.1`: 3/3 again.

Note on `monitor traffic`: as in drill 1, the README's step 3 verification (`monitor
traffic` + `show log messages | last 20`) was not run as a live packet capture here either.
The diagnosis in the evidence log used the filter configuration review plus counters (adding
`count shadowed` to isolate the silent term) to find the shadow, not a traffic monitor.

## What a counter told me that a ping could not

A ping only ever answers "did it get there." It cannot say which rule let it through, which
rule dropped it, or whether a rule even has a counter attached to see it drop. "Connection
refused" vs "Operation timed out" already separates permit from drop before any counter is
read — but the counters are what turned a flat "it doesn't work" into a specific diagnosis:
`users-denied` at 576 B / 9 pkts named the exact term eating the port-22 probes, and
`re-denied` at 576 B / 9 pkts did the same for the management plane. The shadow term broke
that entirely: three counters sitting at zero, with a ping also failing, is not "nothing
happened" — it is proof that a packet died in a place with no counter at all. Only adding a
counter to the suspect term, and watching it jump to 3 packets while the terms below it
stayed at zero, located the problem. A ping tells you pass or fail. A counter tells you
where.
