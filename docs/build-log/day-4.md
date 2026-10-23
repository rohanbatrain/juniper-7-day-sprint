# Day 4 — filters, the management plane, and a term that went silent

*A seven-day, hands-on Juniper Junos lab — built as topology-as-code on plain libvirt/KVM.*

- Repository: [rohanbatrain/juniper-7-day-sprint](https://github.com/rohanbatrain/juniper-7-day-sprint)
- Previous: [Day 3](day-3.md)
- Notes: [day-04/notes.md](../../day-04/notes.md)

## No new topology

Same day-2 lab as day 3: r1, r2, sw1. Day 4 adds a "user host" on sw1 — `10.10.0.10/24` in
its own virtual-router, default route out through r1's `ge-0/0/1.10` — so traffic from USERS
to SERVERS has to actually cross the router being filtered, not just a gateway address on
paper.

Baseline, before any filter: ping from the user host to the servers gateway, 3/3. A telnet
to port 80 came back "Connection refused" (the path is open, nothing is listening there), a
useful contrast for later.

## Filter 1: USERS → SERVERS

A stateless filter on r1's user-facing subinterface: permit DNS, HTTP/S and ICMP to the
servers subnet, count and log everything else to that subnet, then accept the rest. Four
terms, in order, each with its own counter.

`commit confirmed 10` carried the same warning as day 3's filter — `requires 'L2 and L3
Filters' license` — which the lab image enforces anyway.

With the filter live: ping still 3/3, port 80 still "Connection refused", but port 22 now
came back "Operation timed out". That's the whole diagnosis in two words: refused means a
rule let the packet through and something answered; timed out means a rule ate it. The
counters backed it up — the denied-term counter sat at 9 packets (the SYN retries behind
that one timed-out probe), the ICMP counter at 3, the web counter at 1 — and the firewall
log showed the dropped TCP packet directly.

One deviation from the day's plan: step 3 called for watching the drop with `monitor
traffic`. That capture was never run here — the firewall log and the filter's own counters
did the job instead, and they're what the diagnosis above is built on.

## Filter 2: protecting the management plane

A second filter on `lo0`, r1's control plane: accept OSPF, accept SSH/NETCONF only from the
management subnet, accept ICMP, accept established TCP, discard and count everything else.

Before: a telnet from the user host to r1's management port connected. After: it timed out.
Meanwhile a fresh management SSH session from the actual management subnet opened without
issue, and r2's OSPF adjacency to r1 stayed Full through the whole commit. The filter did
exactly what it was told and nothing more.

The `established` term earns a callout: filters are stateless, so r1's own outbound TCP
sessions need their replies let back in by an explicit rule. A security group would do this
automatically; a Junos filter needs a line for it. Day 3 flagged the gap; day 4 is where it
has to be written down.

## Break it: the term with no counter

The drill: insert a term above the permits that quietly swallows the traffic it's supposed
to be testing. `term quarantine`, matching the users subnet, discarding, inserted before
`term dns` — and given no counter.

Result: ping from the user host went to 0/3, and every existing counter on the filter —
denied, ICMP, web — read zero. Not "low." Zero, all of them, while packets were actively
being dropped.

That's the point of the day. A silent counter isn't "nothing happened" — it's evidence that
whatever's dropping the traffic isn't being counted at all. Reading the configuration in
`set` form showed `quarantine` sitting first, with no count action. Adding one counter to
that term and re-running the ping confirmed it: the new counter jumped to 3 packets, the
others stayed at zero. `rollback 2` removed only the quarantine term and the ping came back
3/3.

The second deviation from the drill: it also asked to watch this with `monitor traffic`.
That capture wasn't run for this break either — the fix was found entirely from
configuration review and counters, which is arguably the more realistic diagnosis path when
you can't assume a packet capture is running.

## The lesson

A ping answers one question: did it get there. It can't say which term let it through or
which term ate it. "Refused" versus "timed out" already separates those two outcomes before
a single counter is checked — but it's the counters that turn "it's broken" into "it's this
term." And when every counter reads zero while the ping still fails, that's not a dead end.
It's the clue: the drop is happening somewhere nobody told the filter to count.

## Next

Day 5 — Mist (design day).
