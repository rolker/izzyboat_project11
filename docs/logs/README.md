# Deployment logs convention

Per-deployment, per-host log files. Each agent writes its own file; no
coordination needed for parallel agents on different hosts.

## File layout

```
docs/logs/<year>/<YYYY-MM-DD>_<label>_logs.md
```

- **`<year>`** — UTC year of the deployment start date
- **`<YYYY-MM-DD>`** — UTC date of the deployment **start**, not the
  date of the writing. A multi-day deployment uses one file across all
  its days; sections inside can have date sub-headers when crossing
  UTC midnight.
- **`<label>`** —
  - `dev` literal when the agent is in a **GitHub-origin** clone
    (workspace dev workstation, agent has GitHub access). The hostname
    of the dev machine is intentionally not encoded — the role matters,
    the specific dev box doesn't.
  - `hostname -s` when the agent is in a **field-origin** clone (e.g.,
    gitcloud). Stable per-machine identity (`gabby`, `mercat`, `lr30`,
    etc.).
  - The dev-vs-field distinction matches `field_mode.sh --describe` on
    the project repo, so the label can be derived programmatically.

Examples:

- `docs/logs/2026/2026-04-24_gabby_logs.md` — agent on the boat-side
  Linux host during the 2026-04-24 deployment (gitcloud origin)
- `docs/logs/2026/2026-04-24_dev_logs.md` — agent on a dev machine
  doing pre-deploy or wrap-up work for the 2026-04-24 deployment
- `docs/logs/2026/2026-05-12_lr30_logs.md` — agent on LR30 during a
  multi-day deployment that started 2026-05-12

## File header

Every log file starts with:

```markdown
# <Platform> deployment log — <label> — <YYYY-MM-DD>

**Host**: <hostname or "dev">
**Operator**: <human> + <agent identity, e.g. "Claude Code Agent (Claude Opus 4.7)">
**Mode**: dev (github origin) | field (gitcloud origin) | field (other)
**Deployment**: #<deployment-issue-number> (link)
```

Then sections by topic, in chronological order within the deployment.

## Lifecycle

### Deployment start

1. User prompts the dev agent at start of day. Agent reads
   `docs/roadmap.md` and the open task issues, proposes the day's items.
2. User confirms. Agent opens a **deployment issue** with the agreed
   item list in the body, creates a worktree (via
   `.agent/scripts/worktree_create.sh --issue <N>`), opens a draft PR.
3. Agent initializes the day's log file in the worktree with the header
   above. Issue body links to the file (and to any other host files as
   they appear).
4. On any field machine that wakes up, the user tells the agent
   "continue with existing log" or "start new". Agent acts accordingly.
   Field machines do not open GitHub issues themselves; the dev side's
   deployment issue is the single source of truth.

### During

- The "logger" agent on each host owns appends to that host's log.
  When other agents on the same host do work, the logger summarizes
  them (often at user request).
- Multi-day deployments append to the same file under date sub-headers,
  no rotation.
- Cross-host work (e.g., dev SSHs into salmon) is logged in the
  **agent's own host's file**, not the target's. The file describes
  work done by an agent, not work done to a host.

### Wrap-up

1. User signals: "wrap up the deployment" / "close out".
2. Field machines push their logs to gitcloud at end of session.
3. Dev pulls those into the worktree branch.
4. Dev agent reviews the full deployment, opens follow-up task issues
   for any genuine carry-forward, updates `docs/roadmap.md` with
   anything that's "do this someday but not now".
5. Dev pushes, gets the PR ready for review, merges.
6. Merging closes the deployment issue.

### Deferred / no-issue items → roadmap

If a deployment surfaces work that's:

- Not bounded enough to be a focused task issue, **or**
- Not on deck for the next deployment

…it goes on `docs/roadmap.md`, not into a placeholder issue. The
roadmap is the carry-over mechanism between deployments. The next
deployment's planner reads the roadmap to pick what to fold in.

## What to write in a log

The log captures **what an agent did and what it learned**, in enough
detail that a future agent (or human) can pick up cold. Strong sample:
[`2026-04-24_gabby_logs.md`](2026/2026-04-24_gabby_logs.md) — currently
under the legacy `gabby_2026-04-24.md` filename, will be renamed to
match this convention on next deployment.

Useful sections (use what fits, skip what doesn't):

- **Summary** — 2–3 sentences at the top
- **Numbered topic sections** — actual work done, with file paths and
  line numbers
- **Issues encountered + diagnoses**
- **Pending on operator** / **Handoff** — cross-host coordination
- **Files touched** — repos and paths changed (helps future grep)

Avoid:

- Restating what the diff shows; describe **why** and **what was
  learned**
- Long bag-data dumps in the log itself — analysis goes in the log,
  raw data stays in `~/data/logs/`
- Multi-paragraph design discussions — those belong on the
  deployment issue or a focused task issue

## Anti-pattern: the monolithic log

`docs/bizzyboat_deployment_log.md` (frozen, see header at the top of
that file) is what this convention replaces. It accumulated 5 weeks of
content into 3500 lines, mixing per-session detail with umbrella-style
milestones. Hard to navigate, hard to scope changes against, hard to
close.

The per-deployment per-host model fixes this by giving each unit of
work its own bounded artifact.

## Future automation

This convention is a candidate for a Claude Code skill that handles:

- Today's filename derivation (UTC date, `field_mode.sh --describe`)
- Initialization with header
- Append API for structured entries
- Summarization of peer agents' work (commits, branches, PRs)
- End-of-deployment handoff (move items to roadmap / open task issues
  / update deployment-issue body)

Until that skill exists, agents follow this README manually.
