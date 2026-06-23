#!/usr/bin/env bash
#
# pull_boat_logs.sh — pull data/logs from boat compute hosts (gabby, mercat)
# to this operator station via rsync over SSH, with link-aware bandwidth caps.
#
# Why rsync (not an SMB mount): rsync is incremental (only new/changed files
# after the first pull), resumable (--partial), and bandwidth-limited
# (--bwlimit) out of the box. gabby's ~/data/logs alone was ~77 GB, so a
# repeatable incremental pull over a possibly thin field link is exactly
# rsync's wheelhouse. SMB would need cifs-utils on this host plus a Samba
# share on the boat, and gives none of that cleanly.
#
# Two paths to the boat (see docs/bizzyboat_network.md):
#   wifi      — direct WiFi bridge, ~1 ms, fast (uncapped)
#   wireguard — WireGuard/NETMAP VPN via BenCloud over Starlink, ~37 ms,
#               reached through the ".vpn" aliases. Bandwidth-capped: Starlink
#               *upload* (what the boat does when we pull) is only ~10-20 Mbit/s
#               and shared with telemetry/video, so default 500k.
# Do the first bulk pull over WiFi; the capped VPN is for incremental top-ups
# or when WiFi is down.
#
# Auth: targets are plain ~/.ssh/config Host aliases; the config supplies each
# host's address, User, and IdentityFile, so this script commits no key path,
# address, or username. The ".vpn" aliases must be covered by the same stanza
# as the wifi alias (e.g. `Host gabby gabby.vpn`, `Host mercat mercat.vpn`).
#
# mercat is native Windows 11 (rsync 3.4.4 via MSYS; OpenSSH default shell is
# PowerShell — verified the rsync handshake works anyway). Pulling *from*
# Windows uses a no-perms/no-owner profile + --modify-window to avoid spurious
# permission churn and 1 s mtime mismatches. Windows paths are MSYS-style
# (C:\Users\... -> /c/Users/...).
#
# Usage:
#   pull_boat_logs.sh [HOST ...] [options]
#   pull_boat_logs.sh                 # all hosts over WiFi (default)
#   pull_boat_logs.sh gabby           # just gabby
#   pull_boat_logs.sh gabby -n        # dry run (show what would transfer)
#   pull_boat_logs.sh mercat --link wireguard --bwlimit 250k
#
# Options:
#   --link {wifi|wireguard|auto}   path to use (default: wifi; auto = first reachable)
#   --bwlimit RATE     rsync --bwlimit (e.g. 500k, 1m). Overrides per-link default.
#   --dest DIR         destination root (default: $HOME/data/logs)
#   --ros-log          also pull ~/.ros/log from Linux hosts (off by default)
#   -n, --dry-run      pass --dry-run to rsync (no transfer)
#   --list             print the host/link/source table and exit
#   -h, --help         this help
#
set -euo pipefail

# --------------------------------------------------------------------------
# Configuration — edit here to add hosts, paths, or links.
# --------------------------------------------------------------------------
declare -A HOST_OS=( [gabby]=linux [mercat]=windows )

# Per (host:link) SSH alias. These are plain ~/.ssh/config Host aliases — the
# config supplies the address, User, and IdentityFile, so no key, IP, or
# username is committed here. The ".vpn" aliases reach the NETMAP VPN path and
# must be covered by the same ssh_config stanza as the wifi alias.
declare -A ALIAS=(
  [gabby:wifi]=gabby
  [gabby:wireguard]=gabby.vpn
  [mercat:wifi]=mercat
  [mercat:wireguard]=mercat.vpn
)

# Source dirs per host (arrays so paths with spaces are safe). Linux paths are
# relative to the remote home; Windows paths are absolute MSYS-style.
declare -a SRC_gabby=( "data/logs" )
# Entry form: "remote/path" or "remote/path|dest-label" (label defaults to the
# path's basename). Paths may contain spaces; they won't contain '|'.
declare -a SRC_mercat=(
  "/c/Users/admin/Documents/SoundSpeedCasts|SoundSpeedCasts" # AML casts: raw .aml, .svp/.asvp/.csv
  "/c/Users/admin/QPS-Data/Projects|QPS-Projects"            # Qinsy survey projects: .db/.qpd/.dyngrid
  # NB: C:\Users\Public\Documents\QPS is the Qinsy *app* (charts/manuals), NOT survey data — do not pull.
)
# Optional extra for Linux hosts, enabled with --ros-log.
ROS_LOG_DIR=".ros/log"

# Per-host rsync exclude patterns (one --exclude per entry, applied to all of
# that host's sources). mercat's Qinsy projects hold large .qpd raw-data files
# we don't want on the operator station — the .db/.dyngrid alongside them are
# what we use. Patterns are rsync filter rules (match by basename or path).
declare -a EXCLUDE_gabby=()
declare -a EXCLUDE_mercat=( "*.qpd" )

# Auto-detect tries these in order, using the first reachable address.
LINK_ORDER=(wifi wireguard)

# Default bandwidth cap per link ("" = uncapped). --bwlimit overrides.
declare -A DEFAULT_BWLIMIT=( [wifi]="" [wireguard]=500k )

# --------------------------------------------------------------------------
LINK=wifi
BWLIMIT_OVERRIDE=""
BWLIMIT_SET=0
DEST_ROOT="$HOME/data/logs"
PULL_ROS_LOG=0
DRY_RUN=0
HOSTS=()

err()  { printf 'pull_boat_logs: %s\n' "$*" >&2; }
warn() { printf 'pull_boat_logs: WARN: %s\n' "$*" >&2; }
die()  { err "$*"; exit 1; }

# Lean ssh for reachability probes; key/user/address all come from ~/.ssh/config.
ssh_base=(ssh -o BatchMode=yes -o ConnectTimeout=8)

usage() {
  sed -n '3,/^set -euo pipefail/p' "$0" | sed '$d; s/^# \{0,1\}//'
}

host_sources() {  # host -> prints one "path[|label]" entry per line
  local host="$1"
  local -n arr="SRC_$host"
  printf '%s\n' "${arr[@]}"
  [[ $PULL_ROS_LOG -eq 1 && "${HOST_OS[$host]}" == linux ]] && printf '%s\n' "$ROS_LOG_DIR|ros-log"
}

print_table() {
  printf '%-8s %-8s %-10s %s\n' HOST OS LINK ALIAS
  local h l key
  for h in "${!HOST_OS[@]}"; do
    for l in "${LINK_ORDER[@]}"; do
      key="$h:$l"
      [[ -n "${ALIAS[$key]:-}" ]] &&
        printf '%-8s %-8s %-10s %s\n' "$h" "${HOST_OS[$h]}" "$l" "${ALIAS[$key]}"
    done
    local -n arr="SRC_$h"
    printf '%-8s sources: %s\n' "$h" "${arr[*]}"
  done
}

# --------------------------------------------------------------------------
# Arg parsing
# --------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --link)       LINK="${2:?--link needs a value}"; shift 2 ;;
    --bwlimit)    BWLIMIT_OVERRIDE="${2:?--bwlimit needs a value}"; BWLIMIT_SET=1; shift 2 ;;
    --dest)       DEST_ROOT="${2:?--dest needs a value}"; shift 2 ;;
    --ros-log)    PULL_ROS_LOG=1; shift ;;
    -n|--dry-run) DRY_RUN=1; shift ;;
    --list)       print_table; exit 0 ;;
    -h|--help)    usage; exit 0 ;;
    --)           shift; while [[ $# -gt 0 ]]; do HOSTS+=("$1"); shift; done ;;
    -*)           die "unknown option: $1 (try --help)" ;;
    *)            HOSTS+=("$1"); shift ;;
  esac
done

case "$LINK" in wifi|wireguard|auto) ;; *) die "invalid --link: $LINK" ;; esac
[[ ${#HOSTS[@]} -eq 0 ]] && mapfile -t HOSTS < <(printf '%s\n' "${!HOST_OS[@]}" | sort)

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
ssh_reachable() {  # alias  (uses `hostname`: exists + exit 0 on Linux and PowerShell)
  "${ssh_base[@]}" "$1" hostname >/dev/null 2>&1
}

resolve_link() {  # host -> "link alias" (honors $LINK / auto), or empty
  local host="$1" l key
  if [[ "$LINK" != auto ]]; then
    key="$host:$LINK"
    [[ -n "${ALIAS[$key]:-}" ]] && printf '%s %s' "$LINK" "${ALIAS[$key]}"
    return
  fi
  for l in "${LINK_ORDER[@]}"; do
    key="$host:$l"
    [[ -z "${ALIAS[$key]:-}" ]] && continue
    if ssh_reachable "${ALIAS[$key]}"; then
      printf '%s %s' "$l" "${ALIAS[$key]}"; return
    fi
  done
}

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
rc=0
for host in "${HOSTS[@]}"; do
  [[ -n "${HOST_OS[$host]:-}" ]] || { err "unknown host '$host' (try --list)"; rc=1; continue; }

  link=""; target=""
  read -r link target < <(resolve_link "$host") || true
  if [[ -z "$target" ]]; then
    [[ "$LINK" == auto ]] \
      && err "$host: no link reachable (tried: ${LINK_ORDER[*]})" \
      || err "$host: link '$LINK' has no configured alias"
    rc=1; continue
  fi

  os="${HOST_OS[$host]}"

  # Bandwidth: explicit override wins, else per-link default.
  if [[ $BWLIMIT_SET -eq 1 ]]; then bw="$BWLIMIT_OVERRIDE"; else bw="${DEFAULT_BWLIMIT[$link]:-}"; fi

  # rsync flag assembly.
  case "$os" in
    linux)   arch=(-a) ;;
    windows) arch=(-rlt --no-perms --no-owner --no-group --modify-window=1) ;;
    *)       err "$host: unknown os '$os'"; rc=1; continue ;;
  esac
  # --info=progress2 = overall transfer progress; name1 = print each file as it
  # transfers (per-file visibility). Together: filenames scroll by + a running total.
  common=(-h --partial --partial-dir=.rsync-partial --info=progress2,name1 --mkpath)
  extra=()
  extra+=(-z)                                   # always compress: wifi links aren't always strong
  [[ -n "$bw" ]]        && extra+=(--bwlimit="$bw")
  [[ $DRY_RUN -eq 1 ]]  && extra+=(--dry-run)
  # Per-host excludes (e.g. mercat's *.qpd raw-data files). Empty host arrays
  # add nothing.
  declare -n host_excludes="EXCLUDE_$host"
  for pat in "${host_excludes[@]}"; do extra+=(--exclude="$pat"); done
  ssh_cmd="ssh -o ConnectTimeout=8"     # lean: key/user from ~/.ssh/config

  printf '\n=== %s (%s) via %s [%s]%s ===\n' \
    "$host" "$os" "$link" "$target" "$([[ $DRY_RUN -eq 1 ]] && echo '  DRY RUN')"

  while IFS= read -r entry; do
    [[ -z "$entry" ]] && continue
    src="${entry%%|*}"
    if [[ "$entry" == *"|"* ]]; then label="${entry##*|}"; else label="$(basename "$src")"; fi
    dest="$DEST_ROOT/$host/$label"
    printf -- '-> %s:%s/  ==>  %s/  (bwlimit=%s)\n' "$target" "$src" "$dest" "${bw:-none}"
    if rsync "${arch[@]}" "${common[@]}" "${extra[@]}" -e "$ssh_cmd" "$target:$src/" "$dest/"; then
      rs=0
    else
      rs=$?
    fi
    # 23/24 are partial-transfer codes, NOT failures: live acquisition (QINSy)
    # holds the current file open/locked (23 = unreadable) or keeps writing it
    # (24 = vanished/changed mid-read). rsync transfers every closed/done file
    # and skips the busy one; --partial keeps any progress so a later run (after
    # QINSy closes it) completes it. Treat as a warning, don't fail the run.
    case "$rs" in
      0) : ;;
      23|24) warn "$host: '$src' partial (rsync $rs) — some files still being written/locked by acquisition; done files transferred, busy ones will sync on a later run" ;;
      *) err "$host: rsync of '$src' failed (exit $rs)"; rc=1 ;;
    esac
  done < <(host_sources "$host")
done

exit "$rc"
