# Day 5 — Mist AI: architecture and assurance

**Goal:** understand what Mist actually observes and manages, and map it onto your own
network. No emulation today — the product is a cloud service and the honest exercise is
architecture, not a fake dashboard.

## Work

1. Architecture: access points, switches, the Mist cloud, the edge (WAN), and where telemetry
   is produced and consumed. Draw it for a real enterprise deployment.
2. What the AI does: anomaly detection, SLEs (service-level expectations), client-level
   assurance, Marvis actions. For each: what data, what decision, what action, what can go
   wrong with a false positive.
3. Map onto the lab: in the day-2 topology, which objects would Mist manage, which would it
   merely observe, and what is invisible to it? (Hint: the routers are Junos but not Mist
   hardware.)
4. If hands-on is wanted, use Juniper's free vLabs / Mist sandbox rather than pretending a
   virtual AP is a deployment.

## Deliverable

`day-05/architecture.md` — the diagram, the data-flow table (data → decision → action →
failure mode), and the honest list of what this lab cannot show you.

## Interview-shaped question

"What does Mist give an operations team that SNMP plus syslog did not?" Answer it with the
data-flow table, not a marketing sentence.
