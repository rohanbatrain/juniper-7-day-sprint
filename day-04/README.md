# Day 4 — Security: zones, filters, segmentation

**Goal:** take the network you built and attack it conceptually. Then break connectivity on
purpose and diagnose the denial from the logs.

## Lab

Reuse `day-02-switching.toml`. No new nodes.

## Drill

1. Define trust zones on paper: INTERNET (outside), USERS (VLAN 10), SERVERS (VLAN 20),
   MANAGEMENT (fxp0 / lab-mgmt).
2. Write a stateless firewall filter for r1 that permits only DNS, HTTP/S and ICMP from USERS
   to SERVERS, and logs drops. Apply it inbound on the user-facing interface.
3. Verify the permit set, then watch a drop with `monitor traffic` and with the filter's
   `log` action (`show log messages | last 20`).
4. Protect the management plane: a `lo0` filter that permits SSH/NETCONF from the management
   subnet only. Apply it. Confirm you are still connected — then snapshot and try a wider rule.
5. **Break it:** add a term above the permits that silently shadows them. Diagnose why
   "the user can't reach the server" while the counters say nothing.
6. Roll back with `rollback` or `make restore`.

## Commands to know

```text
show configuration firewall
show firewall
show firewall log
show log messages | match "FILTER"
show interfaces ge-0/0/0 extensive | match "Input errors"
```

## Log

Per drill: expected / actual / diagnosed / fixed. Note specifically what a *counter* told you
that a *ping* could not — that is the point of the day.
