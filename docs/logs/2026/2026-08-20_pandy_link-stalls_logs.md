# 2026-08-20 — pandy deep-dive: recurring boat-to-operator data stalls

Deep-dive off the pandy pre-deployment log
([`2026-08-19_pandy_logs.md`](2026-08-19_pandy_logs.md)). Host: pandy (ROC
operator station). Side: field.

**Status at time of writing (2026-08-20 19:31 -04:00): ONGOING and escalating.**
Not diagnosed to root cause — this records the evidence and rules several
things out, so whoever picks it up on gabby does not have to re-derive it.

## Symptom

Operator-reported: "all the video topics delayed and the sonar displays
frozen", intermittently, for a few seconds at a time. Reported live at ~19:18.

## What is happening

All boat-originated data stops arriving, together, for 5-16 seconds, then
resumes and catches up. Measured as gaps in the arrival of
`/operator/udp_bridge/remotes/bizzy/topic_statistics` (a boat-sourced topic) in
the operator bag `operator_2026-08-20T13.27.56`:

```
19:02:24    8.0 s
19:10:10    6.0 s
19:14:26    8.8 s
19:17:28    5.3 s
19:17:33   13.7 s   <- the operator-reported freeze
19:22:03   15.0 s
19:23:01   15.8 s
19:29:54    8.8 s
```

The durations are trending upward. The first six hours of this deployment
(13:27 onward) show nothing of the kind — 356 minutes scanned, median vpn
429 kB/s, the only other anomaly being the planned 14:10:25 relaunch.

## What it is NOT

**Not the operator station.** Over the same window pandy's own udp_bridge
published 2602 `/operator/udp_bridge/topic_statistics` messages with **zero**
gaps over 3 s. Only boat-originated data stalls; locally generated diagnostics
never miss a beat.

**Not the Starlink link.** `Starlink: starlink.bizzy` reports `0.0% drop,
18-22 ms, 0.01% obstructed` continuously, straight through every stall.

**Not a boat-side process restart.** The 14:09 event earlier today was one of
those and looks completely different: rx decayed to exactly 0.0 on both paths
and stayed there for 96 s, ending with `Assuming remote udp_bridge restart` in
the operator's rosout (packet number 5076057 -> 337). These stalls produce no
such log line and recover on their own.

**Not one link failing.** This is the important one. Both stalls examined at
1 Hz resolution show ICMP loss to gabby on **a different path each time**,
while the other path is clean — and both bridge connections stop regardless:

| stall | `ping.op: gabby_vpn` | `ping.op: gabby_cell` | streams affected |
|---|---|---|---|
| 19:17:33 | **WARN 50% packet loss** | ok, 47-53 ms | **both stopped** |
| 19:23:01 | ok, 46-73 ms | **WARN 25% packet loss** | **both stopped** |

vpn and cell are physically independent bearers (Starlink and cellular). A
fault in one cannot explain the other going silent. The healthy path stops too,
every time.

Rate shape during a stall: a smooth decay to ~13% of nominal and a symmetric
recovery, which is the rate-averaging window draining after a hard stop — the
same shape as the 14:09 restart, just not reaching zero because the window does
not fully drain in 14 s.

## Hypothesis (NOT confirmed — needs gabby-side evidence)

**Head-of-line blocking in the boat's udp_bridge sender.** If a `sendto` on a
degraded connection blocks and the send loop is serialised across connections,
one sick path stalls all of them. That would defeat the purpose of running
redundant links, and it fits every observation above: the stall is common to
both connections, the trigger alternates between paths, and the operator side
and the dish are both innocent.

Stated as a hypothesis deliberately. It cannot be confirmed from pandy, and the
alternative — that something on gabby periodically blocks the whole process,
with the ICMP loss a coincidental symptom rather than the trigger — is not
excluded by anything measured here.

## What to check on gabby

1. udp_bridge CPU and thread state **during** a stall (they recur every few
   minutes, so a 5-minute `top -H` capture should catch one).
2. Whether the boat's own logs show matching 13-16 s gaps in its **receive**
   direction. If the send loop is blocked, the uplink may be affected too —
   unknown from here, and it matters: a 16 s blackout covers heartbeat and
   command_response.
3. Socket send-buffer state / whether `sendto` can block on these sockets.
4. **Timing against the 14:10:25 relaunch.** That was the first run with the
   `Connection::send` unaddressed-connection guard (udp_bridge `6d8355f`) live,
   and that guard is adjacent to this send path. The first stall recorded here
   is 19:02, well after — so this is a question to answer, not an accusation.
   Worth checking whether stalls occurred between 14:10 and 19:02 at a
   sub-3-second scale that this analysis would not have flagged.

## Method, for repeatability

The operator bag recorder (`bag_recorder_operator_launch.py`) captures
`/diagnostics`, both `topic_statistics` topics and `/rosout`, which is what made
this analysable after the fact. Reading it needs the individual `.mcap` files
passed as the URI — the bag is still being written, so it has no
`metadata.yaml` and cannot be opened as a directory. Arrival gaps in a
boat-sourced topic are the cleanest freeze detector; per-minute aggregates of
byte rates hide these entirely, because a 14 s stall inside a 60 s bucket still
leaves a healthy-looking maximum.

---
**Authored-By**: `Claude Code Agent`
**Model**: `Claude Opus 5`
