#!/usr/bin/env python3
"""BizzyBoat course-keeping / cross-track error on straight legs (#124 §2).

True XTE: perpendicular distance from the boat's track to the planned path.
The plan is published in `bizzy/map_tide` and odom in `bizzy/odom`; per the
logged TF these frames are horizontally coincident (odom->map_tide
translation = 0,0,-23.5 — vertical tide datum only), so plan x/y and odom
x/y are directly comparable with no transform.

Filtered to straight (low yaw rate), moving, GUIDED-mode samples — i.e.
autonomous straight-line following, which is what "course-keeping" means.
"""
from __future__ import annotations
import os
import re
import sqlite3
import sys

import numpy as np
import pandas as pd

ANALYSIS = os.path.expanduser("~/data/logs/analysis")
_PT = re.compile(r"Point\(x=([-0-9.e]+), y=([-0-9.e]+)")


def load(db):
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    meta = dict(con.execute("SELECT key,value FROM _bag_meta").fetchall())
    odom = pd.read_sql_query(
        "SELECT t_ns, pos_x, pos_y, vel_x, omega_z FROM t_bizzy_odom "
        "ORDER BY t_ns", con)
    plans = con.execute(
        "SELECT t_ns, json FROM t_bizzy_plan WHERE json IS NOT NULL "
        "AND length(json) > 50 ORDER BY t_ns").fetchall()
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
    lo = _ns("launch_t_ns", odom.t_ns.min())
    hi = _ns("recovery_t_ns", odom.t_ns.max())
    if hi - lo < 120e9:
        lo, hi = int(odom.t_ns.min()), int(odom.t_ns.max())

    # parse each plan json -> Nx2 polyline of (x, y)
    plan_t = np.array([t for t, _ in plans])
    plan_xy = [np.array(_PT.findall(j), float) for _, j in plans]

    if st is not None:
        L = odom.assign(_t=pd.to_datetime(odom.t_ns, unit="ns"))
        R = (st.assign(_t=pd.to_datetime(st.t_ns, unit="ns"))
             .drop(columns="t_ns"))
        odom = pd.merge_asof(L.sort_values("_t"), R.sort_values("_t"),
                             on="_t", direction="backward",
                             tolerance=pd.Timedelta("2s")).drop(columns="_t")
    odom = odom[(odom.t_ns >= lo) & (odom.t_ns <= hi)].reset_index(drop=True)
    return odom, plan_t, plan_xy


def pt_to_polyline(px, py, poly):
    """Min perpendicular distance from point(s) to a polyline (Nx2)."""
    a = poly[:-1]
    b = poly[1:]
    ab = b - a
    ab2 = (ab ** 2).sum(1)
    ab2[ab2 == 0] = 1e-9
    out = np.empty(len(px))
    for i in range(len(px)):
        ap = np.column_stack((px[i] - a[:, 0], py[i] - a[:, 1]))
        t = np.clip((ap * ab).sum(1) / ab2, 0, 1)
        proj = a + t[:, None] * ab
        d = np.hypot(px[i] - proj[:, 0], py[i] - proj[:, 1])
        out[i] = d.min()
    return out


def analyze(db):
    label = os.path.basename(db).split("_")[0]
    odom, plan_t, plan_xy = load(db)
    dt = float(np.median(np.diff(odom.t_ns)) / 1e9)
    # straight + moving + GUIDED
    m = (odom.omega_z.abs() < 0.05) & (odom.vel_x > 0.5)
    if "mode" in odom.columns:
        m &= (odom["mode"] == "GUIDED")  # .mode is a DataFrame method!
    seg = odom[m].copy()
    print(f"\n### {label}: {len(seg)} straight/moving/GUIDED samples "
          f"(~{1/dt:.0f} Hz)")
    if len(seg) < 100 or len(plan_t) == 0:
        print("  insufficient data")
        return

    # active plan index per sample (most recent plan at or before t_ns)
    idx = np.searchsorted(plan_t, seg.t_ns.values, side="right") - 1
    seg = seg[idx >= 0]
    idx = idx[idx >= 0]
    xte = np.empty(len(seg))
    px = seg.pos_x.values
    py = seg.pos_y.values
    for pi in np.unique(idx):
        poly = plan_xy[pi]
        if len(poly) < 2:
            xte[idx == pi] = np.nan
            continue
        sel = idx == pi
        xte[sel] = pt_to_polyline(px[sel], py[sel], poly)
    # Per-leg metrics on contiguous straight runs (gap > 2 s breaks a leg).
    # Two measures per leg:
    #   resid  = RMS perpendicular scatter about the leg's own best-fit line
    #            (track-holding *precision*; plan-independent, robust).
    #   planx  = RMS distance to the active planned path (adds bias from the
    #            commanded line; noisier — stale/multi-line plan matching).
    seg = seg.assign(xte=xte)
    seg["run"] = (seg.t_ns.diff() > 2e9).cumsum()
    legs = []
    for _, g in seg.groupby("run"):
        dur = (g.t_ns.iloc[-1] - g.t_ns.iloc[0]) / 1e9
        if dur < 8 or len(g) < 30:
            continue
        xy = np.column_stack((g.pos_x.values, g.pos_y.values))
        xy = xy - xy.mean(0)
        # smaller-singular-vector projection = perpendicular residual
        _, _, vt = np.linalg.svd(xy, full_matrices=False)
        resid = xy @ vt[1]
        gx = g.xte.values
        gx = gx[np.isfinite(gx) & (gx < 10.0)]
        legs.append((dur, np.sqrt(np.mean(resid ** 2)), resid.max(),
                     np.sqrt(np.mean(gx ** 2)) if len(gx) else np.nan,
                     len(g)))
    if not legs:
        print("  no sustained straight legs")
        return
    a = np.array(legs)  # dur, resid_rms, resid_max, planx_rms, n
    print(f"  {len(legs)} straight legs >=8s | track-holding RMS (about own "
          f"line): median={np.median(a[:, 1]):.2f} m, "
          f"best={a[:, 1].min():.2f}, worst={a[:, 1].max():.2f}")
    px_rms = a[np.isfinite(a[:, 3]), 3]
    if len(px_rms):
        print(f"  XTE vs planned path (incl. bias): median-leg-RMS="
              f"{np.median(px_rms):.2f} m, worst={px_rms.max():.2f} m")


if __name__ == "__main__":
    dbs = sys.argv[1:] or [
        f"{ANALYSIS}/2026-05-01_deployment.db",
        f"{ANALYSIS}/2026-05-21_deployment.db",
        f"{ANALYSIS}/2026-05-22_deployment.db",
    ]
    for db in dbs:
        if os.path.exists(db):
            analyze(db)
