#!/usr/bin/env python3
"""Battery-sag, deceleration, and reverse-bound analysis (#124 §2).

Builds on dynamics.py. Voltage only -- BizzyBoat has no current meter
(BatteryState.current is a ~0 placeholder); never report current/watts.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from dynamics import (ANALYSIS, MS_TO_KT, load, steady_straight, circle_fit,
                      has_table)


def load_voltage(db):
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    if not has_table(con, "t_bizzy_mavros_battery"):
        con.close()
        return None
    v = pd.read_sql_query(
        "SELECT t_ns, voltage FROM t_bizzy_mavros_battery "
        "WHERE voltage > 0 ORDER BY t_ns", con)
    con.close()
    return v


def merge_voltage(d, v):
    L = d.assign(_t=pd.to_datetime(d.t_ns, unit="ns"))
    R = (v.assign(_t=pd.to_datetime(v.t_ns, unit="ns")).drop(columns="t_ns"))
    return pd.merge_asof(L.sort_values("_t"), R.sort_values("_t"),
                         on="_t", direction="nearest",
                         tolerance=pd.Timedelta("2s")).drop(columns="_t")


def battery_vs_stw(db, dt):
    """Time-binned full-throttle STW vs concurrent battery voltage."""
    d, lo, hi = load(db)
    v = load_voltage(db)
    if v is None:
        print("  (no battery topic)")
        return
    seg = steady_straight(d, 1950, 2000, dt)
    if len(seg) < 120:
        print(f"  full-throttle steady n={len(seg)} too few for time bins")
        return
    seg = merge_voltage(seg, v).dropna(subset=["voltage"])
    seg = seg.sort_values("t_ns")
    # split mission into 4 time quartiles of the full-throttle samples
    seg["q"] = pd.qcut(seg.t_ns, 4, labels=False, duplicates="drop")
    print("  quartile |  elapsed |  n  | mean V | STW(circle) | arc")
    for q, g in seg.groupby("q"):
        if len(g) < 40:
            continue
        ce, cn, R, rms, arc = circle_fit(g.ve, g.vn)
        el0 = (g.t_ns.min() - lo) / 3600e9
        el1 = (g.t_ns.max() - lo) / 3600e9
        print(f"     {int(q)}    | {el0:.2f}-{el1:.2f}h | {len(g):4d} | "
              f"{g.voltage.mean():.2f} V | {R:.2f} m/s ({R*MS_TO_KT:.2f} kt) "
              f"| {arc:.0f}deg (rms {rms:.2f})")


def decel_fits(db, dt):
    """Coast-down: throttle chopped from high to idle -> first-order decay."""
    d, lo, hi = load(db)
    use_body = "vel_x" in d.columns and d.vel_x.notna().any()
    v = d.vel_x.values if use_body else d.sog.values
    pwm = d.pwm.values
    t = d.t_ns.values
    w = max(3, int(round(3.0 / dt)))
    out = []
    i = w
    while i < len(d) - 6 * w:
        before = pwm[i - w:i].mean()
        after = pwm[i + w:i + 4 * w].mean()
        post_std = pwm[i + w:i + 6 * w].std()
        # chop to idle from a meaningfully higher throttle, then hold idle
        if before > 1680 and 1470 <= after <= 1530 and post_std < 30:
            tt = (t[i:i + 6 * w] - t[i]) / 1e9
            vv = v[i:i + 6 * w]
            v0 = vv[0]
            if v0 < 0.4:
                i += w
                continue
            try:
                def model(x, vinf, tau):
                    return vinf + (v0 - vinf) * np.exp(-x / tau)
                p, _ = curve_fit(model, tt, vv, p0=[0.1, 3.0],
                                 bounds=([-0.2, 0.3], [v0, 25.0]))
                vinf, tau = p
                rms = np.sqrt(np.mean((model(tt, *p) - vv) ** 2))
                if (v0 - vinf) >= 0.4 and tau < 22 and rms < 0.12:
                    out.append(((v0 - vinf) / tau, tau, v0, vinf, rms))
                    i += 6 * w
                    continue
            except Exception:
                pass
        i += w
    src = "velocity_body" if use_body else "gps_vel(SOG)"
    if out:
        a = np.array(out)
        print(f"  coast-down ({len(out)} chops, src={src}): "
              f"peak decel med={np.median(a[:, 0]):.2f} "
              f"max={a[:, 0].max():.2f} "
              f"m/s^2 | tau med={np.median(a[:, 1]):.1f}s | "
              f"from v med={np.median(a[:, 2]):.2f} m/s")
    else:
        print(f"  coast-down: no clean chop events (src={src})")


def reverse_bound(db):
    d, lo, hi = load(db)
    if "vel_x" not in d.columns:
        # April: body-forward unavailable; use signed SOG at reverse throttle
        rev = d[d.pwm <= 1150]
        if len(rev):
            print(f"  reverse: peak SOG at pwm<=1150 = {rev.sog.max():.2f} "
                  f"m/s (heading-uncorrected; body-frame unavailable)")
        return
    rev = d[d.pwm <= 1150]
    if len(rev):
        peak_kt = abs(rev.vel_x.min()) * MS_TO_KT
        full_rev_med = d[d.pwm <= 1050].vel_x.median()
        print(f"  reverse: peak body vel_x = {rev.vel_x.min():.2f} m/s "
              f"({peak_kt:.2f} kt); "
              f"median at full-reverse(<=1050) = {full_rev_med:.2f} m/s "
              f"[sustained straight reverse under-sampled]")


def main():
    full = {"2026-05-01": ANALYSIS / "2026-05-01_deployment.db",
            "2026-05-21": ANALYSIS / "2026-05-21_deployment.db",
            "2026-05-22": ANALYSIS / "2026-05-22_deployment.db"}
    print("=== Battery sag: full-throttle STW vs voltage over the mission ===")
    for name, db in full.items():
        d, lo, hi = load(str(db))
        dt = float(np.median(np.diff(d.t_ns)) / 1e9)
        print(f"\n# {name}")
        battery_vs_stw(str(db), dt)

    print("\n=== Deceleration (coast-down) + reverse bound ===")
    alldb = {**{"2026-04-27": ANALYSIS / "2026-04-27_nav.db"}, **full}
    for name, db in alldb.items():
        if not Path(db).exists():
            continue
        d, lo, hi = load(str(db))
        dt = float(np.median(np.diff(d.t_ns)) / 1e9)
        print(f"\n# {name}")
        decel_fits(str(db), dt)
        reverse_bound(str(db))


if __name__ == "__main__":
    main()
