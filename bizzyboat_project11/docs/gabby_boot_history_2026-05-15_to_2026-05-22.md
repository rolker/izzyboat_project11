# gabby boot history — 2026-05-15 to 2026-05-22

Snapshot of system power-on / shutdown events on `gabby` (BizzyBoat
companion computer) for the week ending 2026-05-22. Captured to give
the battery-usage analysis agent ground-truth power-cycle intervals
without re-querying `/var/log/wtmp` on a host whose log rotation may
later evict these entries.

## Boot sessions

All times are local (US/Eastern) as recorded by `/var/log/wtmp`.

| Date       | Boot time | Session length | Kernel        | Notes                |
|------------|-----------|----------------|---------------|----------------------|
| Fri May 22 | 09:20     | still running  | 6.8.0-117     | current session      |
| Thu May 21 | 10:41     | 4h 46m         | 6.8.0-117     |                      |
| Thu May 21 | 10:38     | 1m             | 6.8.0-117     | quick reboot         |
| Wed May 20 | 08:38     | 5h 46m         | 6.8.0-117     |                      |
| Tue May 19 | 09:45     | 4h 51m         | 6.8.0-117     |                      |
| Mon May 18 | 19:52     | 36m            | 6.8.0-117     | first 6.8.0-117 boot |
| Mon May 18 | 18:01     | 1h 50m         | 6.8.0-111     |                      |
| Mon May 18 | 17:31     | 2h 20m         | 6.8.0-111     |                      |
| Mon May 18 | 11:13     | 6h 16m         | 6.8.0-111     |                      |

Mon May 18 contained four boots in ~8 hours, including a kernel
upgrade from 6.8.0-111 → 6.8.0-117. No boot activity recorded on
Sat May 16 or Sun May 17 in the window covered by `wtmp`.

`wtmp` on this host begins Wed Mar 18 22:52:15 2026 — earlier sessions
have been rotated out.

## How this was collected

```bash
last reboot -s -7days        # /var/log/wtmp, binary, read via `last`
journalctl --list-boots      # systemd-journald, /var/log/journal/
```

`last reboot` is the canonical source for boot timestamps + session
durations on this host. `journalctl --list-boots` corroborates with
boot IDs and first/last log-entry timestamps and is richer if you need
to correlate boot intervals with specific journal entries.

## Related sources for battery analysis

Inside `/var/log/` on `gabby`:

- `wtmp` — boot/login records (use `last`)
- `journal/` — full systemd journal (use `journalctl -b <N>` per boot)
- `kern.log` / `dmesg.*` — kernel messages, including power-related
  events (`ACPI`, `thermal`, USB enumerate/disconnect)
- `auth.log` — session start/stop (indirect power-state proxy)

Outside `/var/log/`, BizzyBoat's recorded bags under the standard
deployment paths will contain `/bizzy/system/voltage`,
`/bizzy/system/current`, and any battery-monitor topics aligned to
these boot intervals.
