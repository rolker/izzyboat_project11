# 2026-06-16 — salmon log (BizzyBoat deployment #6a53346)

Deployment issue: 6a53346 — Deployment 2026-06-16: Lake Massabesic standard survey day (git-bug; no GitHub URL on field side)
Host: salmon
Side: field
Started: 2026-06-16 11:29 -04:00

> **Stamp this `salmon` log link under the deployment issue's `## Logs` section from dev next time `/start-deployment` runs there.** Field side is read-only on the issue (no `gh`, `issue_sync` has no edit verb); the issue body currently lists only the dev log.

**2026-06-16 13:05 -04:00** — Field change: pull_boat_logs.sh now always passes rsync -z (was non-wifi-only). Operator wants compression on wifi too — link not always strong. Committed jazzy d09afe7; not yet pushed to gitcloud.

**2026-06-16 17:09 -04:00** — Back at the dock. Survey run complete (operator-reported).

**2026-06-16 17:17 -04:00** — Wrap-up (salmon session). Survey day ended without incident — no errors logged this session. Field change pull_boat_logs.sh (rsync -z always) committed + pushed to gitcloud jazzy (091a687) after rebasing onto another host's udp_bridge queue-size config + PR #290 merge. Working tree clean, jazzy up to date with origin.

**Deferred to dev side / follow-up:**
- Deployment issue #6a53346 `## Hosts in use` still reads _TBD_ — salmon was the operator station this run; record from dev (field side is read-only on the issue).
- Stamp the salmon log link under the issue's `## Logs` (currently lists only the dev log) next dev-side `/start-deployment`.
- `pull_qps_data.sh` (rclone/SFTP, mercat) has no compression. Low priority — QPS/QINSy raw is largely incompressible — but worth a look if mercat pulls over a thin link.

