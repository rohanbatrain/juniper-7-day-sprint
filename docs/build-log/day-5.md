# Day 5 — Mist AI: what the cloud does with telemetry

*A seven-day, hands-on Juniper Junos lab — built as topology-as-code on plain libvirt/KVM.*

- Repository: [rohanbatrain/juniper-7-day-sprint](https://github.com/rohanbatrain/juniper-7-day-sprint)
- Previous: [Day 4](day-4.md)
- Architecture note: [day-05/architecture.md](../../day-05/architecture.md)

## No emulation today

Mist is a cloud service, not a Junos image. There is nothing to boot and nothing to
`commit confirmed`. Pretending a virtual AP is a Mist deployment would be the opposite of
day 1's rule — verify the artifact, not the intention — so today's work is architecture:
read Juniper's own Mist documentation, draw the real pipeline, and map it honestly onto the
lab that already exists.

## The pipeline, in one sentence

Telemetry is produced at the edge — access points, EX switches, SRX/SSR WAN devices — and
every decision about it is made in the cloud. The device streams state; it does not decide
anything. Mist's own platform material describes this as a microservices architecture
specifically so decision logic (new SLE types, new anomaly models) ships without touching
the device at all.

## The data-flow table, not a feature list

The brief asked for data → decision → action → failure mode for five capabilities: SLEs,
anomaly detection, client-level assurance / dynamic packet capture, Marvis Actions, and the
Marvis conversational interface. The full table is in
[day-05/architecture.md](../../day-05/architecture.md); four of the five rows have a
documented false-positive path — the fifth, dynamic packet capture, is marked unconfirmed
because the only Juniper documentation page found for it returned a 404 when fetched on
2026-10-23. Juniper's own Marvis material claims LSTM/RNN anomaly-detection models tuned to
>95% efficacy — which is itself an admission that the other <5% is a real failure mode, not
a hypothetical one.

## Mapped onto the lab, honestly

The day-2 topology — `r1`, `r2` (vJunos-router), `sw1` (vJunos-switch, presenting as a
virtual EX9214) — is Junos. None of it is Mist-managed hardware, and none of it is
Mist-claimable: there is no Mist agent, no cloud adoption token, and (for the routers) no
Mist-supported product family at all. SRX and Session Smart Router are the WAN-edge products
Mist AI documents; a generic vJunos-router is neither. The honest categories from the brief —
managed, merely observed, invisible — collapse for this lab mostly into the third one. The
switch counters and OSPF state from days 2–3 are visible locally over SSH; none of it is
visible to a Mist cloud that was never told this lab exists.

## What this lab cannot show

No Mist-managed device, no streaming telemetry reaching a cloud decision engine, no learned
baseline (anomaly detection needs days-to-weeks of normal behavior; this lab lives for an
afternoon), and no live false positive — the failure modes in the table are reasoned from
the documented mechanism, not observed, because nothing here runs the mechanism. Juniper's
own free vLabs / Mist sandbox is the honest path to hands-on contact with the real product;
a virtual router is not a substitute for it.

## The interview question

"What does Mist give an operations team that SNMP plus syslog did not?" SNMP and syslog
already deliver the *data* column — a counter, a log line. They stop there: no threshold
tied to user experience, no root-cause attribution, no action. Mist's contribution is
everything downstream of that first column — decision (SLE classification, anomaly scoring)
and action (Marvis Actions, self-driving remediation) — continuously, without a human
reading the data first. The honest second half: that decision layer is also where Mist's own
new failure mode lives. SNMP and syslog can be noisy or incomplete, but they never
misattribute a root cause, because they never infer one.

## Next

Day 6: spine/leaf and an EVPN overlay — two spines, two leaves, ECMP, back on real topology
rather than a vendor cloud.
