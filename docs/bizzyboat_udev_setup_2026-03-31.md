# Issue #26 — BizzyBoat udev rules for stable USB device symlinks

**Issue**: https://github.com/rolker/unh_echoboats_project11/issues/26
**Worktree**: `/home/roland/project11/layers/worktrees/issue-unh_echoboats_project11-26`
**Project repo**: `platforms_ws/src/unh_echoboats_project11/bizzyboat_project11/`
**Branch**: `feature/issue-26` (from `jazzy`)

## Devices

| Device | Vendor:Product | Serial | Symlink |
|--------|---------------|--------|---------|
| CubeOrange FCU (MAVLink) | `2dae:1016` | `43001E000A51323237373236` | `/dev/fcu` (interface 00) |
| CubeOrange FCU (SLCAN) | `2dae:1016` | `43001E000A51323237373236` | `/dev/fcu_slcan` (interface 02) |
| Arduino CTD winch | `2341:0043` | `342343139313512040B1` | `/dev/winch` |
| Factory USB camera | `32e4:9230` | (none) | no symlink — backup camera, use default `/dev/videoN` |

## Decisions

- **FCU symlink**: `/dev/fcu` — update `core_launch.py` default from `/dev/ttyACM0:57600` to `/dev/fcu:57600`
- **Winch symlink**: `/dev/winch` (not `ctd_winch` — simpler, only one winch)
- **USB camera**: no udev rule needed — it's the only V4L2 device and just a backup; default `/dev/videoN` is fine
- **ModemManager exclusion**: add for both serial devices (FCU + winch)
- **FCU SLCAN**: `/dev/fcu_slcan` — second CubeOrange interface for DroneCAN peripheral management
- **Rules file**: three entries (FCU MAVLink, FCU SLCAN, winch)

## Progress Log

### 2026-03-31 — Session start
- Created worktree for issue #26
- Package structure: `bizzyboat_project11/config/` exists, will add `udev/` subfolder
- Grepped launch files: only `core_launch.py:29` references a device path (`/dev/ttyACM0:57600` for FCU)
- No launch file references for winch or USB camera
- Settled on symlink names (see Decisions above)
### 2026-03-31 — Device verification on gabby
- `lsusb` confirmed all three devices present with expected vendor:product IDs
- `udevadm info` confirmed serials match issue exactly:
  - ttyACM0: Arduino winch (`2341:0043`, serial `342343139313512040B1`, USB port `1-5`)
  - ttyACM1: CubeOrange FCU (`2dae:1016`, serial `43001E000A51323237373236`, USB port `1-6`)

### 2026-03-31 — Rules created and deployed
- Created `bizzyboat_project11/config/udev/99-bizzyboat.rules` (2 rules + ModemManager exclusion)
- Updated `core_launch.py:29` default from `/dev/ttyACM0:57600` to `/dev/fcu:57600`
- SCP'd rules to gabby, installed to `/etc/udev/rules.d/`, reloaded udev
- Verified symlinks active:
  - `/dev/fcu` -> `ttyACM2` (FCU re-enumerated after trigger — proves symlink stability)
  - `/dev/winch` -> `ttyACM0`

### 2026-03-31 — Unplug/replug test
- Unplugged both FCU and Arduino, re-plugged FCU only
  - `/dev/fcu` -> `ttyACM1` — came back immediately
  - `/dev/winch` — correctly absent (Arduino not plugged in)
  - syslog confirmed: kernel saw disconnect for both (`usb 1-5`, `usb 1-6`), only FCU reconnected
- Re-seated Arduino (first attempt didn't register — loose cable)
  - `/dev/winch` -> `ttyACM2` — came back after firm re-seat
  - `/dev/fcu` -> `ttyACM1` — unchanged, still stable
- Underlying `ttyACM` numbers shifted across all tests; symlinks always pointed to the correct device

### 2026-03-31 — CubeOrange dual-interface fix
- Initial rules used `ATTRS{bInterfaceNumber}` to distinguish MAVLink vs SLCAN interfaces
- This failed: udev `ATTRS` can only match attributes from one parent device level,
  and `bInterfaceNumber` and `serial` are at different parent levels
- Fixed by switching to `ENV{}` properties (`ID_USB_INTERFACE_NUM`, `ID_USB_VENDOR_ID`,
  `ID_USB_SERIAL_SHORT`) which are all available at the device level
- Redeployed and verified:
  - `/dev/fcu` -> `ttyACM0` (MAVLink, interface 00)
  - `/dev/fcu_slcan` -> `ttyACM1` (SLCAN, interface 02)
  - `/dev/winch` -> `ttyACM2`

### 2026-03-31 — FCU parameter baseline capture
- MAVProxy initial attempt with chained `--cmd` failed: commands ran before connection established
  - Lesson: take small steps with MAVProxy, verify each before proceeding
- Connected with `mavproxy.py --master=/dev/fcu,57600`, waited for heartbeat + param fetch
- `param save /tmp/bizzyboat_fcu_baseline.param` — saved 935 parameters
- SCP'd back to `config/fcu/bizzyboat_fcu_baseline.param`
- MAVProxy exit: `quit` and `exit` not recognized; Ctrl-C via tmux (`C-c`) works

## Notes
- Working collaboratively via tmux on gabby — all tmux commands require user approval before sending
- Arduino USB connection can be finicky — ensure firm cable seat during deployment
- MAVProxy: don't chain commands via `--cmd`, run interactively one step at a time
- MAVProxy exit: use Ctrl-C (programmatic `tmux send-keys C-c`), not `quit` or `exit`
