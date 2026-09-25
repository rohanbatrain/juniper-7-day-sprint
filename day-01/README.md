# Day 1 — Junos fundamentals + CLI

**Goal:** two routers, one link, and the operational commands every later day assumes.

## Lab

```bash
make up            # lab/topologies/day-01-routing.toml is the default
make status
make console NODE=r1
```

| Node | Management | Data port | Your address |
| --- | --- | --- | --- |
| lab-r1 | 10.99.0.11 | ge-0/0/0 | 10.0.12.1/30 |
| lab-r2 | 10.99.0.12 | ge-0/0/0 | 10.0.12.2/30 |

Login `admin` / `admin@123`. Boot takes 5–15 minutes (the images are nested VMs); start the
topology first and read while it boots.

## Drill

1. Configure `ge-0/0/0` and `lo0` on both routers; `commit`.
2. `ping 10.0.12.2` from r1 and back. First packet lost? Say why.
3. Enter configuration mode, change the address, and commit with `commit confirmed 2`. Do
   nothing. Watch it roll back. Do it again and confirm before the timer.
4. Make a wrong change and `delete` it — inspect `show | compare` before committing.
5. **Break it:** give r2 the wrong prefix length. Find it with `show interfaces terse` and
   `show route`; fix it without rebooting anything.

## Commands to know

```text
show | compare
show interfaces terse
show interfaces ge-0/0/0 detail
show route
show configuration | display set
commit check / commit / commit confirmed N / rollback N
edit / set / delete / top / up
request system power-off      # the polite way to stop a node
```

## Reference

`lab/configs/day-01/r1.conf` and `r2.conf` are the finished articles — compare only after
you have done it yourself.

## Log

Write what happened, per drill: expected / actual / how you diagnosed it / what fixed it.
This is the raw material for the day-1 post.
