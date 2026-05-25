#!/usr/bin/env python3
"""BizzyBoat performance characterization (unh_echoboats_project11#124 §2).

Reusable across deployments. Universal signals present in every bag:
  - PWM throttle : t_bizzy_mavros_rc_out.ch_0  (ESC; ch_1 mirrors)
  - ground vel   : t_bizzy_mavros_global_position_raw_gps_vel  (ENU m/s)
                   vel_x = east, vel_y = north  -> SOG, COG
Higher-quality cross-check where present (05-01 onward):
  - body twist   : t_bizzy_mavros_local_position_velocity_body (EKF, m/s)

Current removal: at a fixed throttle the boat's ground-velocity vector is
  v_ground = STW * (unit heading-through-water) + current
so over many headings the (ve, vn) samples trace a circle of radius STW
centred on the current vector. An algebraic circle fit to the steady,
straight, fixed-throttle cloud yields STW (speed through water) and the
current vector together -- no per-pair heading matching required.
"""
from __future__ import annotations
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

MS_TO_KT = 1.94384
ANALYSIS = Path.home() / "data/logs/analysis"


def has_table(con, name):
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def circle_fit(ve, vn):
    """Algebraic (Kasa) circle fit. Returns (cur_e, cur_n, R, rms, arc_deg)."""
    ve = np.asarray(ve, float)
    vn = np.asarray(vn, float)
    A = np.c_[2 * ve, 2 * vn, np.ones(len(ve))]
    b = ve ** 2 + vn ** 2
    (ce, cn, c), *_ = np.linalg.lstsq(A, b, rcond=None)
    R = float(np.sqrt(max(c + ce * ce + cn * cn, 0.0)))
    rms = float(np.sqrt(np.mean(
        (np.hypot(ve - ce, vn - cn) - R) ** 2)))
    # heading coverage of the cloud relative to the fitted centre
    ang = np.degrees(np.arctan2(vn - cn, ve - ce)) % 360
    arc = _arc_span(ang)
    return float(ce), float(cn), R, rms, arc


def _arc_span(ang):
    """Largest gap complement: how many degrees of arc the points span."""
    s = np.sort(ang % 360)
    if len(s) < 2:
        return 0.0
    gaps = np.diff(np.r_[s, s[0] + 360])
    return float(360 - gaps.max())


def load(db):
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    meta = dict(con.execute("SELECT key,value FROM _bag_meta").fetchall())
    rc = pd.read_sql_query(
        "SELECT t_ns, ch_0 AS pwm FROM t_bizzy_mavros_rc_out ORDER BY t_ns",
        con)
    gv = pd.read_sql_query(
        "SELECT t_ns, vel_x AS ve, vel_y AS vn "
        "FROM t_bizzy_mavros_global_position_raw_gps_vel ORDER BY t_ns", con)
    vb = None
    if has_table(con, "t_bizzy_mavros_local_position_velocity_body"):
        vb = pd.read_sql_query(
            "SELECT t_ns, vel_x, omega_z "
            "FROM t_bizzy_mavros_local_position_velocity_body ORDER BY t_ns",
            con)
    con.close()

    def _ns(key, default):
        v = meta.get(key)
        try:
            return int(v)
        except (TypeError, ValueError):
            return int(default)
    lo = _ns("launch_t_ns", rc.t_ns.min())
    hi = _ns("recovery_t_ns", rc.t_ns.max())
    # Fall back to full bag range only when the launch/recovery detector
    # produced a degenerate window (missing / 'null' / near-zero -- e.g.
    # April bags lack /global altitude). 2 min guards a real short run
    # from being expanded into on-deck/crane segments.
    if hi - lo < 120e9:
        lo, hi = int(rc.t_ns.min()), int(rc.t_ns.max())

    def asof(left, right):
        L = left.assign(_t=pd.to_datetime(left.t_ns, unit="ns"))
        R = (right.assign(_t=pd.to_datetime(right.t_ns, unit="ns"))
             .drop(columns="t_ns"))
        m = pd.merge_asof(L.sort_values("_t"), R.sort_values("_t"),
                          on="_t", direction="nearest",
                          tolerance=pd.Timedelta("200ms"))
        return m.drop(columns="_t")

    d = asof(gv, rc)
    if vb is not None:
        d = asof(d, vb)
    d = d[(d.t_ns >= lo) & (d.t_ns <= hi)].dropna(
        subset=["pwm", "ve", "vn"]).reset_index(drop=True)
    d["sog"] = np.hypot(d.ve, d.vn)
    d["cog"] = np.degrees(np.arctan2(d.ve, d.vn)) % 360
    return d, lo, hi


def steady_straight(d, pwm_lo, pwm_hi, dt):
    """Steady (stable PWM & SOG) and straight (low heading change) samples."""
    w = max(3, int(round(3.0 / dt)))
    pwm_ptp = d.pwm.rolling(w, center=True).apply(np.ptp, raw=True)
    sog_std = d.sog.rolling(w, center=True).std()
    # heading rate from COG (unwrapped) -- straight if it barely changes
    cog_u = np.unwrap(np.radians(d.cog.values))
    cog_rate = np.abs(np.gradient(cog_u, d.t_ns.values / 1e9))
    m = ((d.pwm >= pwm_lo) & (d.pwm <= pwm_hi)
         & (pwm_ptp <= 25) & (sog_std <= 0.07)
         & (cog_rate < 0.1) & (d.sog > 0.05))
    return d[m]


def fit_speed(d, label, pwm_lo, pwm_hi, dt):
    seg = steady_straight(d, pwm_lo, pwm_hi, dt)
    if len(seg) < 40:
        print(f"  {label:18s} pwm[{pwm_lo}-{pwm_hi}]: "
              f"only {len(seg)} steady samples -- skip")
        return None
    ce, cn, R, rms, arc = circle_fit(seg.ve, seg.vn)
    cur = np.hypot(ce, cn)
    cur_dir = np.degrees(np.arctan2(ce, cn)) % 360  # compass set-direction
    # naive (uncorrected) max/median SOG for contrast
    print(f"  {label:18s} pwm[{pwm_lo}-{pwm_hi}] n={len(seg):5d} "
          f"arc={arc:3.0f}deg | STW={R:.2f} m/s ({R*MS_TO_KT:.2f} kt) "
          f"cur={cur:.2f} m/s twd {cur_dir:.0f}deg "
          f"| rawSOG med={seg.sog.median():.2f} max={seg.sog.max():.2f} "
          f"(rms {rms:.3f})")
    return dict(label=label, n=len(seg), arc=arc, stw=R, cur=cur,
                cur_dir=cur_dir, rms=rms, sog_med=seg.sog.median())


def accel_fits(d, dt):
    """First-order surge fits on clean throttle step-ups (strict gate)."""
    w = max(3, int(round(3.0 / dt)))
    pwm = d.pwm.values
    t = d.t_ns.values
    use_body = "vel_x" in d.columns and d.vel_x.notna().any()
    v = (d.vel_x.values if use_body
         else (d.sog.values * np.sign(d.pwm.values - 1500)))
    out = []
    i = w
    while i < len(d) - 6 * w:
        before = pwm[i - w:i].mean()
        after = pwm[i + w:i + 4 * w].mean()
        post_std = pwm[i + w:i + 6 * w].std()
        # require a near-idle start (not a reverse-to-forward transition)
        if 1470 <= before <= 1560 and (after - before) >= 200 \
                and post_std < 40:
            tt = (t[i:i + 6 * w] - t[i]) / 1e9
            vv = v[i:i + 6 * w]
            v0 = vv[0]
            try:
                def model(x, vinf, tau):
                    return v0 + (vinf - v0) * (1 - np.exp(-x / tau))
                p, _ = curve_fit(model, tt, vv, p0=[vv[-1], 3.0],
                                 bounds=([v0 - 0.1, 0.3], [4.0, 25.0]))
                vinf, tau = p
                rms = np.sqrt(np.mean((model(tt, *p) - vv) ** 2))
                if (vinf - v0) >= 0.5 and tau < 22 and rms < 0.12:
                    out.append((after, vinf - v0, tau,
                                (vinf - v0) / tau, rms))
                    i += 6 * w
                    continue
            except (RuntimeError, ValueError):
                pass  # curve_fit non-convergence / bad input = no clean event
        i += w
    return out, ("velocity_body" if use_body else "gps_vel(signed SOG)")


def analyze(db):
    label = Path(db).stem.replace("_deployment", "").replace("_nav", "")
    d, lo, hi = load(db)
    dt = float(np.median(np.diff(d.t_ns)) / 1e9)
    dur = (hi - lo) / 3600e9
    has_body = "vel_x" in d.columns
    print(f"\n### {label}  ({dur:.2f} h, {len(d)} samples, ~{1/dt:.1f} Hz, "
          f"body_vel={'yes' if has_body else 'NO'})")
    print(" max-speed (circle-fit current removal):")
    res = {}
    res["fwd_max"] = fit_speed(d, "FWD max (>=1950)", 1950, 2000, dt)
    res["fwd_mid"] = fit_speed(d, "FWD mid (1750-1850)", 1750, 1850, dt)
    res["rev_max"] = fit_speed(d, "REV max (<=1100)", 1000, 1100, dt)
    fits, vsrc = accel_fits(d, dt)
    if fits:
        arr = np.array(fits)  # cols: after_pwm, dV, tau, surge, rms
        hard = arr[arr[:, 0] >= 1850]
        ramp = arr[arr[:, 0] < 1850]
        print(f" acceleration (src={vsrc}):")
        if len(hard):
            print(f"   hard launch (->pwm>=1850, n={len(hard)}): "
                  f"peak surge med={np.median(hard[:, 3]):.2f} "
                  f"max={hard[:, 3].max():.2f} m/s^2, "
                  f"tau med={np.median(hard[:, 2]):.1f}s, "
                  f"dV med={np.median(hard[:, 1]):.2f}")
        if len(ramp):
            print(f"   survey ramp (->pwm<1850, n={len(ramp)}): "
                  f"peak surge med={np.median(ramp[:, 3]):.2f} m/s^2, "
                  f"tau med={np.median(ramp[:, 2]):.1f}s, "
                  f"dV med={np.median(ramp[:, 1]):.2f}")
    else:
        print(f" acceleration: no clean step-ups (src={vsrc})")
    return label, res, fits


if __name__ == "__main__":
    # No args -> every available per-deployment DB (full + focused nav).
    dbs = sys.argv[1:] or [
        str(p) for p in (sorted(ANALYSIS.glob("2026-*_deployment.db"))
                         + sorted(ANALYSIS.glob("2026-*_nav.db")))
    ]
    for db in dbs:
        if Path(db).exists():
            analyze(db)
        else:
            print(f"\n### {db}: MISSING")
