# Windows field-agent notes (mercat)

First-pass notes from bringing the `ros2_agent_workspace` up on **mercat**, a
Windows machine on the boat, for the project11 boats (BizzyBoat / IzzyBoat).
Written 2026-06-03 by the Claude Code agent during initial setup. Treat as a
living reference for the next agent that lands on a Windows host.

## TL;DR

mercat is a **field logging / utilities station**, not a build host. It does
**not** run ROS — ROS runs on **gabby** (Linux, also on the boat). On mercat you
write deployment logs and small utilities, commit them, and push to
`unh_echoboats_project11` over `git@gitcloud`. That's the whole job.

## Environment

- **Native Windows 11 Pro**, build 10.0.26200. Hostname `mercat`.
- **This is NOT WSL.** There is no Linux subsystem in play — no `wsl`, no distro,
  `WSL_DISTRO_NAME` is unset. Everything below runs against native Windows.
- **Two shells, know which you're in:**
  - The Claude Code harness defaults to **PowerShell 7.6.2 (Core / pwsh)** —
    this is the primary shell. Use PowerShell syntax (`$env:VAR`, `$null`,
    backtick line-continuation), not bash-isms.
  - The workspace automation is all bash (`.sh`), which runs under **Git Bash /
    MINGW64** (also installed). `uname` there reports `MINGW64_NT-10.0-26200`.
    This is where the workspace `scripts/*.sh` actually execute.
  - Both are native Windows. Neither is WSL.
- **No ROS toolchain on this box** — `vcs`, `colcon`, `ros2`, and `make` are all
  absent. `python3` resolves to the Windows Store shim. Do **not** attempt
  `make build` / `colcon build` here; that work belongs on gabby.

## Field mode

Both the workspace repo and this project repo have `origin` on **gitcloud**, so
they are in **field mode** (see `.agent/scripts/field_mode.sh`):

- Commit directly to the default branch (`jazzy`) and push to `origin` — **no
  GitHub PR ceremony** (there is no GitHub remote here).
- Access repos only through git operations against `git@gitcloud:field/<repo>.git`
  (clone / fetch / push). **Do not open an interactive `ssh gitcloud` shell** —
  `field@gitcloud` is a real Ubuntu account, and shell access wasn't asked for.
- Pre-commit hooks still apply where present; never `--no-verify`. (This repo has
  no `.pre-commit-config.yaml`, and `pre-commit` isn't installed on mercat, so
  commits to `jazzy` aren't blocked by a `no-commit-to-branch` hook.)

## Workspace / manifest checkout

- Manifest repo: `git@gitcloud:field/unh_echoboats_project11.git` @ `jazzy`
  (Pattern B — `config/bootstrap.yaml` has `layer: platforms`, so the manifest
  repo *is* the platforms-layer project repo). This is the same manifest gabby
  uses.
- It was checked out with a **plain `git clone`** into its canonical location,
  `layers/main/platforms_ws/src/unh_echoboats_project11`, because `vcs` (the
  normal importer) isn't available. `layers/` is gitignored by the workspace, so
  the workspace tree stays clean.
- The full `setup_layers.sh` / `make build` bootstrap was **deliberately skipped**
  — it's both unnecessary (no ROS build here) and a poor fit on Windows (below).

## Windows gotchas found during setup

- **`ln -s` does not create symlinks in MINGW** — it *copies* the target. So the
  standard `configs/manifest -> <repo>/config` symlink that `setup_layers.sh`
  makes would become a stale copy, and the script's `[ -L ]` idempotency check
  would re-bootstrap every run. We skipped the symlink (not needed for logging).
  If a real link is ever required, use a Windows directory junction instead:
  `cmd /c "mklink /J <link> <target>"` (works without admin).
- **`curl file://` wants Windows-style paths** — `file:///c/Users/...` failed;
  it expects `C:/Users/...`. Relevant only if you try to feed `setup_layers.sh`
  a local `bootstrap.yaml`; easier to just `git clone` the manifest directly.
- **gitcloud is SSH-only here** — no HTTP raw-file endpoint was reachable, so the
  default "`curl` the `bootstrap.yaml` from a URL" flow doesn't apply on the boat
  network. Clone over `git@gitcloud` instead.

## git-bug (how deployment info is shared)

Deployment issues propagate as **git-bug** data (git refs) via gitcloud. On mercat:

- **Installed:** git-bug **v0.10.1** (matches the workspace pin in
  `bootstrap.sh`) at `~/.local/bin/git-bug.exe` — on PATH, no admin needed.
  Downloaded from the GitHub release asset `git-bug_windows_amd64.exe`. Works as
  both `git-bug` and `git bug`. Identity created as the agent.
- **`git bug pull origin` does NOT work on Windows.** git-bug's embedded Go git
  client (go-git) demands a Windows SSH agent ("could not detect Pageant or
  Windows native SSH agent") *and* doesn't read `~/.ssh/config`, so it can't
  resolve the `gitcloud` host alias. Command-line MINGW `git` has neither
  problem.
- **Workaround — sync git-bug refs with system git, then clear the cache:**

  ```bash
  REPO=layers/main/platforms_ws/src/unh_echoboats_project11
  git -C "$REPO" fetch origin 'refs/bugs/*:refs/bugs/*' 'refs/identities/*:refs/identities/*'
  rm -rf "$REPO/.git/git-bug/cache"        # REQUIRED — git bug won't see direct ref updates otherwise
  git -C "$REPO" bug bug --label deployment --status open
  git -C "$REPO" bug bug show <id>
  ```

  Without the cache clear, `git bug bug` reports 0 even though the refs are
  present. Pushing bug edits back would likewise need
  `git push origin 'refs/bugs/*:refs/bugs/*'` via system git, not `git bug push`.

## Commit identity

Always author agent work as the **Claude Code agent**, never as the operator.
Because each shell invocation is a fresh subshell (env exports don't persist),
pass the identity per commit:

```bash
git -c user.name="Claude Code Agent" \
    -c user.email="roland+claude-code@ccom.unh.edu" \
    commit -m "..."
```

## Deployment logs

Per-host deployment logs live at:

```
docs/logs/<year>/<YYYY-MM-DD>_<host>_logs.md      # e.g. docs/logs/2026/2026-06-03_mercat_logs.md
```

`/start-deployment` reads `.agents/deployment.yaml`, detects field mode, and sets
up the per-host log + issue sync. See the workspace deployment-mode docs (ADR-0014
and `.agent/knowledge/deployment_mode.md`) for the lifecycle and urgency contract.

## Account / profile quirk (important)

The Claude Code agent process runs as **`mercat\field`** (`whoami` → `mercat\field`,
SID `…-1001`), but `USERPROFILE` and the Git-Bash `HOME` point at
**`C:\Users\admin`**. Consequences:

- `~` in Git Bash, `~/.ssh/config`, and `~/.local/bin` (where `git-bug.exe` lives)
  all resolve under **`C:\Users\admin`**, not a `field` profile dir.
- The `field` user's own **HKCU hive is locked down** — writes are denied even
  when the process is elevated (both PowerShell `New-ItemProperty` and `reg.exe`
  return *Access denied*).
- **Takeaway:** for any machine config that must stick, prefer **machine-wide
  `HKLM` policy keys**, not per-user `HKCU` tweaks — the latter can't be written
  from the agent context here.

## Machine-config tweaks applied

### Disabling desktop weather & news (Widgets)

Windows 11 25H2 shows weather on the taskbar plus a news/weather board via the
**Widgets** feature (the `MicrosoftWindows.Client.WebExperience` pack). Operators
who RDP in don't need it. Disable it **machine-wide** (every account, survives the
HKCU lockdown above):

```powershell
# elevated PowerShell
$dsh = 'HKLM:\SOFTWARE\Policies\Microsoft\Dsh'
if (-not (Test-Path $dsh)) { New-Item -Path $dsh -Force | Out-Null }
New-ItemProperty -Path $dsh -Name 'AllowNewsAndInterests' -Value 0 -PropertyType DWord -Force
```

- This is the documented GPO/MDM **"Allow widgets"** policy. `0` removes the
  taskbar entry point *and* the widgets board for all users.
- Takes effect at the **next sign-in / RDP reconnect**. For immediate effect in a
  live session, restart the shell: `Stop-Process -Name explorer` (auto-restarts;
  only refreshes taskbar/desktop, doesn't drop the RDP connection or other apps).
- The per-user toggle `HKCU\…\Explorer\Advanced\TaskbarDa = 0` is **not usable
  here** (HKCU lockdown) and is redundant once the policy above is set.
- **Not** touched: lock-screen widgets / Windows Spotlight — RDP sessions don't
  show the lock screen, so they're irrelevant to operators. Disable separately
  (also via HKLM policy) if a console user ever needs it.

*Applied on mercat 2026-06-03.*
