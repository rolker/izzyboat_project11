# 2026-08-05 — gabby log (BizzyBoat deployment 4f74fc0)

Deployment issue: 4f74fc0 — Deployment 2026-08-05: BizzyBoat dockside rebuild + ENC-costmap / live-coverage verification (git-bug; no GitHub URL from field side)
Host: gabby
Side: field
Started: 2026-08-05 13:21 -04:00

## 2026-08-05

**2026-08-05 13:22 -04:00** — Deployment mode activated on gabby (field side), attached to git-bug issue 4f74fc0 'Deployment 2026-08-05: BizzyBoat dockside rebuild + ENC-costmap / live-coverage verification' (opened dev-side 10:43 EDT, last edited 13:19). New deployment for today; the 2026-08-04 differential-drive deployment was wrapped up field-side at 20:08 with all four commits pushed. Repo on jazzy, tree clean.

**2026-08-05 13:22 -04:00** — Issue 4f74fc0 body has NO '## Logs' section. Field side is read-only on the issue, so nothing edited here. FOR DEV: add a '## Logs' section and stamp '- [gabby log](docs/logs/2026/2026-08-05_gabby_logs.md)' under it next time /start-deployment or the wrap-up runs there. Issue title is already in canonical 'Deployment <date>: <scope>' form, so no rename needed.

**2026-08-05 13:22 -04:00** — FIELD-MODE GOTCHA for wrap-up: the configured issue_sync.field_pull ('git bug pull origin') FAILS in an agent Bash subshell — 'error creating SSH agent: SSH agent requested but SSH_AUTH_SOCK not-specified'. git-bug's go-git transport requires an agent; the subshell has none. Worked around with plain git ('git fetch origin refs/bugs/*:refs/bugs/* refs/identities/*:refs/identities/*', which uses system ssh and its own keys) followed by 'rm -rf .git/git-bug/cache' to force a cache rebuild. Consider changing field_pull in .agents/deployment.yaml to the plain-git form so /start-deployment works unattended on field hosts.

**2026-08-05 13:22 -04:00** — TIMING FLAG on the rebuild backlog (issue 4f74fc0 gabby checklist item 1). This session ran 'make sync' + 'make build' at 11:45-11:47 EDT, which reported every repo 'Already up to date' EXCEPT cube_bathymetry (fast-forward 4264e38..caa3b12, survey_index_query + store_import + ADRs 0002/0003 + issue-111/115 work plans). All 5 layers then rebuilt green (70 packages; sensors layer stamp cleared manually so cube_bathymetry actually recompiled). BUT issue comment #1 states the dev-side gitcloud push of all 36 repos completed ~16:20Z = 12:20 EDT, roughly 35 min AFTER that sync. So the sync predates the dev push and the owed backlog (bizzyboat_project11 #389/#276/#380, unh_marine_autonomy uma#276 + marine_bathymetry_store, unh_marine_navigation #381, marine_charts/s57_tools#30, the depth-cost config flip #415/PR #416) is very likely NOT yet on this host. Needs a re-sync + rebuild before any nav or costmap verification. NOTE the uma PR#280 deployment note: marine_bathymetry_store's sizeof grew, so dependent packages must be rebuilt together, not selectively.
