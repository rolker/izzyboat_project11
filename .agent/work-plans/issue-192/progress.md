---
issue: 192
---

# Issue #192 — Adopt workspace /start-deployment skill (.agents/deployment.yaml + docs/logs/README.md shrink)

## Integrated Review
**Status**: complete
**When**: 2026-05-28 11:40 -04:00
**By**: Claude Code Agent (Claude Opus 4.7 (1M context))

**PR**: #194 at `494474e`
**Sources**: 1 (Copilot R1 @ `494474e`) — no prior `progress.md`, no human reviews, no conversation comments
**Cross-source confirmations**: 0
**CI**: none configured on this project repo

### Findings
- [x] (must-fix, Copilot R1) Invalid git-bug subcommands — `git bug ls` and `git bug show` don't exist in this git-bug version; correct is `git bug bug --label ... --status open` and `git bug bug show <ID>`. Would have failed on the first field-side invocation at issue lookup (no fallback). — `.agents/deployment.yaml:45-46` **(resolved in `a734adb`; corrected commands verified by listing both open deployment-labeled bugs and showing #186 detail)**
- [x] (must-fix, Copilot R1) `dev_push` missing the bridge-pull step. New GitHub issues are not in local git-bug refs until `git bug bridge pull github` runs; just `git bug push gitcloud` doesn't propagate them. — `.agents/deployment.yaml:47` **(resolved in `a734adb` — now `git bug bridge pull github && git bug push gitcloud`; verified bridge-pull imported real comment updates)**
- [x] (operator-call, Copilot R1) Host roster wrong about salmon (memory `project_field_hosts_no_github_creds.md`: salmon is field-mode historically), missing `deadpool` (the current dev host). Per operator decision (option B), dropped the `hosts:` block entirely — schema treats it as informational only, `field_mode.sh` is authoritative per repo, and the dual roles drift faster than a static roster is useful. — `.agents/deployment.yaml:26-31` **(resolved in `a734adb`)**

### Trial observation
This was the first invocation of `/start-deployment` after merging it to `main` upstream — followed immediately by `/triage-reviews 194` when the skill correctly stopped at step 1 (config missing on `jazzy`, since PR #194 hadn't merged). Copilot R1 caught all three of the must-fix items that the in-deployment trial note on [#186](https://github.com/rolker/unh_echoboats_project11/issues/186) specifically called out for field-side observation — meaning the pre-merge review cycle replaced what would otherwise have been a deployment-day discovery, *before* it could break a live run. The skill's stop-at-step-1 behavior also worked exactly as designed (clear message pointing at the template + schema doc).

### False positives
None.
