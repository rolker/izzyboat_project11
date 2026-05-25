#!/usr/bin/env python3
"""BizzyBoat turning performance (#124 §2 turn-radius item).

Question: the helm clamps cmd_vel angular.z at max_yaw_speed=0.5 rad/s
(bizzyboat.yaml). Is that a placeholder, and what can the boat actually do?

Signals (05-01+ have velocity_body.omega_z = measured yaw rate):
  - yaw rate   : t_bizzy_mavros_local_position_velocity_body.omega_z (rad/s)
  - speed      : same table vel_x (body-forward, m/s)
  - steering   : t_bizzy_mavros_rc_out.ch_2  (servo PWM; ch_3 == ch_2)
  - throttle   : ch_0
  - mode       : t_bizzy_mavros_state.mode  (GUIDED clamped / MANUAL not)
"""
from __future__ import annotations
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ANALYSIS = Path.home() / "data/logs/analysis"


def asof(left, right, tol="200ms", direction="nearest"):
    L = left.assign(_t=pd.to_datetime(left.t_ns, unit="ns"))
    R = (right.assign(_t=pd.to_datetime(right.t_ns, unit="ns"))
         .drop(columns="t_ns"))
    m = pd.merge_asof(L.sort_values("_t"), R.sort_values("_t"), on="_t",
                      direction=direction, tolerance=pd.Timedelta(tol))
    return m.drop(columns="_t")


def load(db):
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    meta = dict(con.execute("SELECT key,value FROM _bag_meta").fetchall())
    vb = pd.read_sql_query(
        "SELECT t_ns, vel_x, omega_z FROM "
        "t_bizzy_mavros_local_position_velocity_body ORDER BY t_ns", con)
    rc = pd.read_sql_query(
        "SELECT t_ns, ch_0 AS thr, ch_2 AS steer FROM "
        "t_bizzy_mavros_rc_out ORDER BY t_ns", con)
    has_state = con.execute(
        "SELECT 1 FROM sqlite_master WHERE name='t_bizzy_mavros_state'"
    ).fetchone()
    st = (pd.read_sql_query(
        "SELECT t_ns, mode FROM t_bizzy_mavros_state ORDER BY t_ns", con)
        if has_state else None)
    con.close()

    def _ns(k, d):
        try:
            return int(meta[k])
        except (KeyError, TypeError, ValueError):
            return int(d)
    lo = _ns("launch_t_ns", vb.t_ns.min())
    hi = _ns("recovery_t_ns", vb.t_ns.max())
    if hi - lo < 120e9:
        lo, hi = int(vb.t_ns.min()), int(vb.t_ns.max())

    d = asof(vb, rc)
    if st is not None:
        d = asof(d, st, tol="2s", direction="backward")
    d = d[(d.t_ns >= lo) & (d.t_ns <= hi)].dropna(
        subset=["omega_z", "steer"]).reset_index(drop=True)
    return d


def analyze(db):
    label = Path(db).stem.replace("_deployment", "").replace("_nav", "")
    d = load(db)
    dt = float(np.median(np.diff(d.t_ns)) / 1e9)
    print(f"\n### {label}  ({len(d)} samples, ~{1/dt:.1f} Hz)")

    # --- 1. yaw rate by mode: clamped (GUIDED) vs physical (MANUAL) --------
    if "mode" in d.columns:
        print(" yaw rate |omega_z| by mode (rad/s):")
        for mode, g in d.groupby("mode"):
            if len(g) < 50 or mode in ("", None):
                continue
            w_abs = g.omega_z.abs()
            print(f"   {mode:8s} n={len(g):6d}  "
                  f"p99={w_abs.quantile(0.99):.2f}  max={w_abs.max():.2f}  "
                  f"mean_spd={g.vel_x.mean():.2f}")

    # --- 2. steering center (zero-yaw PWM) ---------------------------------
    straight = d[(d.omega_z.abs() < 0.03) & (d.thr > 1600)]
    center = straight.steer.median() if len(straight) > 50 else 1500.0
    print(f" steering center (zero-yaw, fwd): {center:.0f} PWM")

    # --- 3. vectored-thrust steering authority ----------------------------
    # Steering turns the thrusters, so yaw moment ~ thrust(throttle) x
    # sin(thruster angle). Throttle (thrust), NOT boat speed, is the driver
    # (a rudder would need water flow; this pivots at zero speed).
    d["defl"] = d.steer - center
    d["defl_bin"] = (d.defl / 150).round() * 150
    thr_edges = [1500, 1650, 1800, 2001]
    thr_lbl = ["thr1500-1650", "thr1650-1800", "thr1800-2000"]
    d["thr_bin"] = pd.cut(d.thr, thr_edges, labels=thr_lbl, right=False)
    g = d[(d.defl.abs() <= 525) & d.thr_bin.notna()]
    piv = g.pivot_table(values="omega_z", index="thr_bin",
                        columns="defl_bin", aggfunc="median")
    cnt = g.pivot_table(values="omega_z", index="thr_bin",
                        columns="defl_bin", aggfunc="size")
    piv = piv.where(cnt >= 25)  # blank cells with <25 samples
    print(" median yaw (rad/s) by throttle x steering deflection (PWM):")
    print(piv.round(2).to_string())
    # demonstrate throttle (thrust) drives yaw at fixed steering:
    fix = d[(d.defl.between(150, 350))]
    print(" at fixed steering (+150..+350 PWM), yaw vs throttle:")
    for lbl, gg in fix.groupby("thr_bin", observed=True):
        if len(gg) >= 25:
            print(f"   {lbl}: yaw={gg.omega_z.median():+.2f} rad/s "
                  f"(n={len(gg)}, mean_spd={gg.vel_x.mean():.2f} m/s)")
    pk = d.loc[d.omega_z.abs().idxmax()]
    print(f" peak-yaw sample: |yaw|={abs(pk.omega_z):.2f} rad/s at "
          f"thr={pk.thr:.0f}, defl={pk.defl:+.0f} PWM, spd={pk.vel_x:.2f} m/s "
          f"-> vectored-thrust pivot, not speed-driven")

    # --- 4. turn radius R = speed / |omega| on sustained turns -------------
    yr = d.omega_z.abs()
    sustained = d[(yr > 0.3) & (d.vel_x.abs() > 0.4)].copy()
    if len(sustained):
        sustained["R"] = sustained.vel_x.abs() / sustained.omega_z.abs()
        print(f" sustained turns (|omega|>0.3, spd>0.4): n={len(sustained)}")
        print(f"   turn radius: min={sustained.R.min():.1f} m  "
              f"median={sustained.R.median():.1f} m  "
              f"p10={sustained.R.quantile(0.10):.1f} m")
        peak_spd = float(d.loc[yr.idxmax(), "vel_x"])
        print(f"   peak |yaw| {yr.max():.2f} rad/s at spd "
              f"{peak_spd:.2f} m/s -> R={abs(peak_spd) / yr.max():.1f} m")
    # radius the 0.5 clamp imposes at cruise vs physical
    print(f" radius @ cruise 1.52 m/s: clamp(0.5)={1.52/0.5:.1f} m, "
          f"@0.8 rad/s={1.52/0.8:.1f} m, @0.97={1.52/0.97:.1f} m")


if __name__ == "__main__":
    dbs = sys.argv[1:] or [
        str(p) for p in sorted(ANALYSIS.glob("2026-*_deployment.db"))]
    for db in dbs:
        if Path(db).exists():
            analyze(db)
