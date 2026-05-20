---
issue: 135
---

# Issue #135 — Deployment 2026-05-19: Starlink-only operation + OTH survey test

## External Review
**Status**: complete
**When**: 2026-05-20 17:30
**By**: Claude Code Agent (Claude Opus 4.7 (1M context))

**PR**: #136 — 9 review(s), 8 valid clusters, 1 false positive, 3 already addressed, 5 editorial
**CI**: no checks configured for this PR (matches existing project repo pattern)

### Actions
- [ ] **C1-3** — Update `bizzyboat_project11/config/bizzyboat.yaml` line 234 comment to reflect the current `gps_vel` config (or strike the velocity-body claim; the durable answer rides on #138 reconfig)
- [ ] **C16-20** — Add `#135` GitHub link to `docs/logs/2026/2026-05-19_gabby_logs.md` `**Deployment**:` header (dev-side curator action; field-mode host couldn't add it at write-time)
- [ ] **C25-29** — Add `#135` GitHub link to `docs/logs/2026/2026-05-19_salmon_logs.md` `**Deployment**:` header (same as gabby)
- [ ] **C23-24** — Reconcile gabby log's Phase 2 "complete / first-OTH" outcome wording (line 56) + `~14:30` mission timestamp (line 549) with dev-log reframe (line-of-sight, partial credit, recovered 14:09). Either edit gabby log directly or add a curator's reconciliation note pointing to dev log 20:48.
- [ ] **C21-22** — Decide: operator-curate gabby Summary (line 18) + Lessons Learned (line 46), OR accept as agent-draft state
- [ ] **C30-31** — Decide: operator-curate salmon Summary (line 14) + Lessons Learned (line 18), OR accept as agent-draft state
- [ ] **C32** — Add to `docs/logs/README.md` near line 13: brief clarification that field-host logs without GitHub credentials may use the git-bug ID alone, with the GitHub link added at wrap-up
- [ ] **C33** — Clarify `docs/logs/README.md` wrap-up step 3 (line 134): cherry-pick field-host commits from gitcloud into the deployment PR branch (`make sync` alone only updates the local `gitcloud/jazzy` ref, doesn't publish to GitHub)
- [ ] (Optional) Address editorial nits C6-C10 (tide/current heights + TZ tagging convention), C13-C15 (forward-references / wrap-up bullet predating reframe)
- [ ] (Optional) Dismiss C11 on the PR (false-positive flag against the canonical agent-team email)

### Already addressed (no action needed)
- C4, C5 — dev log Summary + Lessons Learned (populated in commit `df40805`)
- C12 — phase/window/activity table (current file has clean 3-column table)
- C34 — roadmap.md `#110` vs `#111` reference (full roadmap rewrite this session correctly distinguishes them)

### False positives
- C11 — git-bug identity email `roland+claude-code@ccom.unh.edu` is the canonical agent-team role-based address (`+claude-code` suffix), intentionally public in commit signatures per `.agent/scripts/set_git_identity_env.sh`. Not PII in this context.
