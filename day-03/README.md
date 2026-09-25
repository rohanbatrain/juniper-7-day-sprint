# Day 3 — Cloud networking

**Goal:** no new topology. Map cloud networking concepts onto the lab you already built, and
produce a design document rather than a config file.

## Lab

Reuse day-01 or day-02. The work product today is a design note, not a CLI transcript.

## Drill

1. Draw your own topology as a cloud would describe it: VPC/VNet → subnets → route tables →
   internet gateway vs NAT gateway → security groups. Name which lab object plays which part.
2. Answer, in writing: what is a "private subnet" in the lab? What would an internet gateway
   be, given the lab has no uplink? Where does NAT live, and why does the lab deliberately
   not have one?
3. Design a two-cluster segmentation: services cluster and management cluster, least
   privilege between them. Address it from the plan in [docs/addressing.md](../docs/addressing.md).
4. Optional: implement the segmentation with firewall filters on the day-02 topology
   (day 4 goes deeper).

## Deliverable

`day-03/design.md` — the diagram plus the mapping table, in your words. This is the post for
day 3: "how I map cloud networking concepts onto a network I built myself".

## Commands to know

Nothing new today. Practice narrating the existing ones: a design you cannot explain with a
routing table in front of you is a diagram, not a design.
