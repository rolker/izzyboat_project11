#!/usr/bin/env python3
"""Generate a landscape preview SVG of BizzyBoat hydro payload offsets.

Coordinates in cm, base_link at origin. REP-103: +x fwd, +y port, +z up.
"""
from __future__ import annotations
import math

# --- Geometry constants (cm) ----------------------------------------
HULL_LENGTH_FWD = 120
HULL_LENGTH_AFT = -120
HULL_BEAM = 90
HULL_BOTTOM_Z = -5
RAIL_Z = 89
MAST_TOP_Z = 142
UPRIGHT_X_FWD = 30
UPRIGHT_X_AFT = -40
CUAV_HOLDER_H = 7.5
TRIMBLE_STUD_H = 2.0

# AutoNav box (from URDF): x∈[-110.5, -87.5], y∈[-14, +14], z∈[-1, +13]
AN_X_MIN, AN_X_MAX = -110.5, -87.5
AN_Y_MIN, AN_Y_MAX = -14, 14
AN_Z_MIN, AN_Z_MAX = -1, 13

# SENSORS: name, x, y, z, color, label_angle_deg (tuned to reduce overlap)
# IMU is inside AutoNav (not drawn separately). Camera tower is structural (drawn
# as a gray mast line, not labeled as a sensor).
SENSORS = [
    ('base_link',   0,      0,  0,                         '#e00000',  -60),
    ('SBG',         -60,    0,  2.5,                       '#8a0000',  150),
    ('Trimble fwd', 99.0,   0,  RAIL_Z + TRIMBLE_STUD_H,   '#d4a018',   65),
    ('Trimble aft', -106.5, 0,  RAIL_Z + TRIMBLE_STUD_H,   '#d4a018',  115),
    ('CUAV fwd',    83.5,   0,  RAIL_Z + CUAV_HOLDER_H,    '#303030',   50),
    ('CUAV aft',    -83.5,  0,  RAIL_Z + CUAV_HOLDER_H,    '#303030',  130),
    ('OAK×4',       31,     0,  141,                       '#0aa',      80),
    ('USB cam',     105,    0,  89,                        '#2a9df4',   35),
    ('AutoNav',     -99,    0,  6,                         '#996633',  125),
    ('M3',          -23,    0,  -14.5,                     '#1e66c8',  -95),
    ('Fin',         5,      0,  -12.3,                     '#444',     -50),
    ('SVS',         -45,    25, -5.5,                      '#bd00bd',   95),
]

SHAPES = {
    'M3':         {'kind': 'cylinder_v', 'd': 15,  'h': 15,  'reference': 'bottom'},
    'CUAV fwd':   {'kind': 'cylinder_v', 'd': 2.5, 'h': 4.5, 'reference': 'bottom'},
    'CUAV aft':   {'kind': 'cylinder_v', 'd': 2.5, 'h': 4.5, 'reference': 'bottom'},
    'Trimble fwd':{'kind': 'cylinder_v', 'd': 14,  'h': 7,   'reference': 'bottom'},
    'Trimble aft':{'kind': 'cylinder_v', 'd': 14,  'h': 7,   'reference': 'bottom'},
    'SBG':        {'kind': 'box', 'L': 5, 'W': 5, 'H': 5, 'reference': 'back_bottom'},
    'SVS':        {'kind': 'cylinder_y', 'd': 3,   'L': 12,  'reference': 'tip_pos'},
    'Fin':        {'kind': 'box', 'L': 8, 'W': 3, 'H': 5,  'reference': 'bottom'},
    'OAK×4':      {'kind': 'oak_cross',  'd': 6},
    'USB cam':    {'kind': 'cylinder_h', 'd': 4,   'L': 8,   'reference': 'back'},
    'AutoNav':    {'kind': 'autonav_box'},
    'base_link':  {'kind': 'crosshair'},
}

HOLDERS = {
    'CUAV fwd':    {'W': 6,  'H': CUAV_HOLDER_H, 'kind': 'rect'},
    'CUAV aft':    {'W': 6,  'H': CUAV_HOLDER_H, 'kind': 'rect'},
    'Trimble fwd': {'W': 1.2, 'H': TRIMBLE_STUD_H, 'kind': 'stud'},
    'Trimble aft': {'W': 1.2, 'H': TRIMBLE_STUD_H, 'kind': 'stud'},
}

# --- Layout constants ------------------------------------------------
PX_PER_CM = 2.5
MARGIN = 30
TITLE_H = 46
LEGEND_W = 290
PANEL_GAP = 100   # wide so side-view right-side dimensions don't bleed into the right column

# Extents
TOP_X_MIN, TOP_X_MAX = -135, 135
TOP_Y_MIN, TOP_Y_MAX = -85, 85
SIDE_X_MIN, SIDE_X_MAX = -135, 135
SIDE_Z_MIN, SIDE_Z_MAX = -55, 170
DETAIL_X_MIN, DETAIL_X_MAX = -60, 25
DETAIL_Z_MIN, DETAIL_Z_MAX = -45, 20
DETAIL_SCALE = 2.5

def cm_px(r, s=1.0): return (r[1] - r[0]) * PX_PER_CM * s
TOP_W = cm_px((TOP_X_MIN, TOP_X_MAX));   TOP_H = cm_px((TOP_Y_MIN, TOP_Y_MAX))
SIDE_W = cm_px((SIDE_X_MIN, SIDE_X_MAX)); SIDE_H = cm_px((SIDE_Z_MIN, SIDE_Z_MAX))
DETAIL_W = cm_px((DETAIL_X_MIN, DETAIL_X_MAX), DETAIL_SCALE)
DETAIL_H = cm_px((DETAIL_Z_MIN, DETAIL_Z_MAX), DETAIL_SCALE)

# Landscape layout: top + side stacked on left, detail + legend stacked on right
LEFT_COL_W = max(TOP_W, SIDE_W)
RIGHT_COL_W = max(DETAIL_W, LEGEND_W)
TOTAL_W = LEFT_COL_W + RIGHT_COL_W + 3*MARGIN + PANEL_GAP
TOTAL_H = TITLE_H + TOP_H + SIDE_H + 3*MARGIN

# --- SVG helpers -----------------------------------------------------
def _a(attrs): return ' '.join(f'{k}="{v}"' for k, v in attrs.items())
def rect(x, y, w, h, **a): return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" {_a(a)}/>'
def circ(cx, cy, r, **a):  return f'<circle cx="{cx}" cy="{cy}" r="{r}" {_a(a)}/>'
def line(x1, y1, x2, y2, **a): return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" {_a(a)}/>'
def text(x, y, s, **a): return f'<text x="{x}" y="{y}" {_a(a)}>{s}</text>'
def path(d, **a): return f'<path d="{d}" {_a(a)}/>'
def group(children, **a): return f'<g {_a(a)}>\n  ' + '\n  '.join(children) + '\n</g>'
def polygon(pts_xy, **a):
    d = 'M ' + ' L '.join(f'{x},{y}' for x, y in pts_xy) + ' Z'
    return path(d, **a)

# Coord transforms
def top_x(x): return (x - TOP_X_MIN) * PX_PER_CM
def top_y(y): return (TOP_Y_MAX - y) * PX_PER_CM
def side_x(x): return (x - SIDE_X_MIN) * PX_PER_CM
def side_y(z): return (SIDE_Z_MAX - z) * PX_PER_CM
def detail_x(x): return (x - DETAIL_X_MIN) * PX_PER_CM * DETAIL_SCALE
def detail_y(z): return (DETAIL_Z_MAX - z) * PX_PER_CM * DETAIL_SCALE

# --- CAD dimension helper -------------------------------------------
def cad_dim_h(x_a, x_b, y_above, tx_a, tx_b, label, text_above=True, font=10):
    """Horizontal (in-image) CAD dimension between pixel x columns x_a and x_b,
    with horizontal dim line at pixel y = y_above. Extension lines drop from
    the feature y-coords (tx_a, tx_b) up to y_above."""
    parts = []
    ext = 6  # extension past dim line
    # Extension lines
    parts.append(line(x_a, tx_a, x_a, y_above - ext, stroke='#444',
                      **{'stroke-width': '0.55'}))
    parts.append(line(x_b, tx_b, x_b, y_above - ext, stroke='#444',
                      **{'stroke-width': '0.55'}))
    # Dimension line with arrowheads
    parts.append(line(x_a, y_above, x_b, y_above, stroke='#222',
                      **{'stroke-width': '0.9', 'marker-start': 'url(#arr)',
                         'marker-end': 'url(#arr)'}))
    # Label
    cx = (x_a + x_b)/2
    ty = y_above - 3 if text_above else y_above + 12
    parts.append(text(cx, ty, label,
                      **{'font-size': str(font), 'fill': '#111',
                         'text-anchor': 'middle', 'font-weight': '500'}))
    return parts

def cad_dim_v(y_a, y_b, x_right, fy_a, fy_b, label, font=10):
    """Vertical CAD dimension between pixel y rows y_a, y_b, dim line at x_right.
    Extension lines extend horizontally from features (fy_a, fy_b) to x_right."""
    parts = []
    ext = 6
    parts.append(line(fy_a, y_a, x_right + ext, y_a, stroke='#444',
                      **{'stroke-width': '0.55'}))
    parts.append(line(fy_b, y_b, x_right + ext, y_b, stroke='#444',
                      **{'stroke-width': '0.55'}))
    parts.append(line(x_right, y_a, x_right, y_b, stroke='#222',
                      **{'stroke-width': '0.9', 'marker-start': 'url(#arr)',
                         'marker-end': 'url(#arr)'}))
    parts.append(text(x_right + 4, (y_a + y_b)/2 + 3, label,
                      **{'font-size': str(font), 'fill': '#111',
                         'font-weight': '500'}))
    return parts

# --- Shape drawers --------------------------------------------------
def draw_shape(view, name, x, y, z, color, px_per_cm):
    shape = SHAPES.get(name)
    if not shape: return []
    k = shape['kind']
    tx, ty = {
        'top':    (top_x, top_y),
        'side':   (side_x, side_y),
        'detail': (detail_x, detail_y),
    }[view]
    out = []

    if k == 'cylinder_v':
        d = shape['d']; h = shape['h']
        ref = shape['reference']
        if view == 'top':
            out.append(circ(tx(x), ty(y), d/2 * px_per_cm,
                            fill=color, stroke='black',
                            **{'stroke-width': '0.6', 'fill-opacity': '0.8'}))
        else:
            if ref == 'bottom': z0, z1 = z, z + h
            elif ref == 'top':  z0, z1 = z - h, z
            else:               z0, z1 = z - h/2, z + h/2
            out.append(rect(tx(x - d/2), ty(z1),
                            d * px_per_cm, h * px_per_cm,
                            fill=color, stroke='black',
                            **{'stroke-width': '0.6', 'fill-opacity': '0.8'}))

    elif k == 'cylinder_h':
        # Horizontal cylinder along +x (e.g. forward-looking camera)
        d = shape['d']; L = shape['L']; ref = shape['reference']
        if ref == 'back': x0, x1 = x - L, x
        else:             x0, x1 = x - L/2, x + L/2
        if view == 'top':
            out.append(rect(tx(x0), ty(y + d/2),
                            L * px_per_cm, d * px_per_cm,
                            fill=color, stroke='black',
                            **{'stroke-width': '0.6', 'fill-opacity': '0.8',
                               'rx': '4', 'ry': '4'}))
        else:
            out.append(rect(tx(x0), ty(z + d/2),
                            L * px_per_cm, d * px_per_cm,
                            fill=color, stroke='black',
                            **{'stroke-width': '0.6', 'fill-opacity': '0.8',
                               'rx': '4', 'ry': '4'}))

    elif k == 'cylinder_y':
        # Horizontal cylinder along y (e.g. SVS mounted athwartship).
        # reference 'tip_pos': sensing tip at (x, +y_ref, z); body extends in −y.
        d = shape['d']; L = shape['L']; ref = shape['reference']
        if ref == 'tip_pos':
            y0, y1 = y - L, y     # body from (y-L) to (y); tip at y1
            tip_y = y1
        elif ref == 'tip_neg':
            y0, y1 = y, y + L
            tip_y = y0
        else:
            y0, y1 = y - L/2, y + L/2
            tip_y = y
        if view == 'top':
            out.append(rect(tx(x - d/2), ty(y1),
                            d * px_per_cm, (y1 - y0) * px_per_cm,
                            fill=color, stroke='black',
                            **{'stroke-width': '0.6', 'fill-opacity': '0.85',
                               'rx': '2', 'ry': '2'}))
            # Small marker at the sensing tip
            out.append(circ(tx(x), ty(tip_y), 1.2 * px_per_cm,
                            fill='white', stroke=color,
                            **{'stroke-width': '0.8'}))
            # Cable direction indicator (short line from cable end toward y=0)
            cable_y = y0 if ref == 'tip_pos' else y1
            cable_target_y = 0 if (cable_y > 0) else 0  # toward centerline
            dy = cable_target_y - cable_y
            dy_len = min(abs(dy) * 0.3, 6)  # short arrow
            out.append(line(tx(x), ty(cable_y),
                            tx(x), ty(cable_y + (-dy_len if dy < 0 else dy_len)),
                            stroke=color, **{'stroke-width': '1',
                                              'marker-end': 'url(#oak_arr)'}))
        else:
            # End-on view: small filled circle
            out.append(circ(tx(x), ty(z), d/2 * px_per_cm,
                            fill=color, stroke='black',
                            **{'stroke-width': '0.6', 'fill-opacity': '0.85'}))

    elif k == 'box':
        L = shape['L']; W = shape['W']; H = shape['H']; ref = shape['reference']
        if view == 'top':
            if ref == 'back_bottom': x0, x1 = x, x + L
            else:                     x0, x1 = x - L/2, x + L/2
            y0, y1 = y - W/2, y + W/2
            out.append(rect(tx(x0), ty(y1),
                            (x1-x0) * px_per_cm, (y1-y0) * px_per_cm,
                            fill=color, stroke='black',
                            **{'stroke-width': '0.6', 'fill-opacity': '0.8'}))
        else:
            if ref == 'back_bottom':
                x0, x1, z0, z1 = x, x + L, z, z + H
            elif ref == 'top':
                x0, x1, z0, z1 = x - L/2, x + L/2, z - H, z
            elif ref == 'bottom':
                x0, x1, z0, z1 = x - L/2, x + L/2, z, z + H
            else:
                x0, x1, z0, z1 = x - L/2, x + L/2, z - H/2, z + H/2
            out.append(rect(tx(x0), ty(z1),
                            (x1-x0) * px_per_cm, (z1-z0) * px_per_cm,
                            fill=color, stroke='black',
                            **{'stroke-width': '0.6', 'fill-opacity': '0.8'}))

    elif k == 'autonav_box':
        # Fixed-position box from URDF
        if view == 'top':
            out.append(rect(tx(AN_X_MIN), ty(AN_Y_MAX),
                            (AN_X_MAX - AN_X_MIN) * px_per_cm,
                            (AN_Y_MAX - AN_Y_MIN) * px_per_cm,
                            fill=color, stroke='black',
                            **{'stroke-width': '0.8', 'fill-opacity': '0.6'}))
        else:
            out.append(rect(tx(AN_X_MIN), ty(AN_Z_MAX),
                            (AN_X_MAX - AN_X_MIN) * px_per_cm,
                            (AN_Z_MAX - AN_Z_MIN) * px_per_cm,
                            fill=color, stroke='black',
                            **{'stroke-width': '0.8', 'fill-opacity': '0.6'}))

    elif k == 'oak_cross':
        # OAK cluster: a small circle with 4 short arrows radiating
        d = shape['d']
        if view == 'top':
            cx, cy = tx(x), ty(y)
            r = d/2 * px_per_cm
            out.append(circ(cx, cy, r, fill=color, stroke='black',
                            **{'stroke-width': '0.6'}))
            arm = r * 2.2
            for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                out.append(line(cx, cy, cx + dx*arm, cy - dy*arm,
                                stroke=color, **{'stroke-width': '1.4',
                                                  'marker-end': 'url(#oak_arr)'}))
        else:
            out.append(circ(tx(x), ty(z), d/2 * px_per_cm, fill=color,
                            stroke='black', **{'stroke-width': '0.6'}))

    elif k == 'mast':
        d = shape['d']
        if view == 'top':
            out.append(circ(tx(x), ty(y), d/2 * px_per_cm, fill=color,
                            stroke='black', **{'stroke-width': '0.6'}))
        else:
            out.append(line(tx(x), ty(RAIL_Z), tx(x), ty(z),
                            stroke=color, **{'stroke-width': str(d * px_per_cm * 0.5)}))

    elif k == 'point_small':
        out.append(circ(tx(x), ty(y if view == 'top' else z), 3,
                        fill=color, stroke='black', **{'stroke-width': '0.5'}))

    elif k == 'crosshair':
        cx = tx(x); cy = ty(y if view == 'top' else z)
        out.append(line(cx-7, cy, cx+7, cy, stroke=color, **{'stroke-width': '1.2'}))
        out.append(line(cx, cy-7, cx, cy+7, stroke=color, **{'stroke-width': '1.2'}))
        out.append(circ(cx, cy, 2.2, fill=color))
    return out

def draw_holder(view, name, x, y, z, px_per_cm):
    holder = HOLDERS.get(name)
    if not holder: return []
    W = holder['W']; H = holder['H']
    kind = holder.get('kind', 'rect')
    if view == 'top':
        tx, ty = top_x, top_y
        if kind == 'stud':
            return [circ(tx(x), ty(y), W/2 * px_per_cm, fill='#999',
                         stroke='#555', **{'stroke-width': '0.4'})]
        return [rect(tx(x - W/2), ty(y + W/2),
                     W * px_per_cm, W * px_per_cm,
                     fill='white', stroke='#666', **{'stroke-width': '0.5'})]
    tx, ty = (side_x, side_y) if view == 'side' else (detail_x, detail_y)
    if kind == 'stud':
        return [line(tx(x), ty(RAIL_Z), tx(x), ty(RAIL_Z + H),
                     stroke='#555', **{'stroke-width': '1.2'})]
    return [rect(tx(x - W/2), ty(RAIL_Z + H),
                 W * px_per_cm, H * px_per_cm,
                 fill='white', stroke='#666', **{'stroke-width': '0.5'})]

# Per-sensor leader lengths (px) to spread the central cluster vertically
LEADER_LEN = {
    'base_link':   16,
    'SBG':         45,
    'M3':          40,
    'Fin':         55,
    'SVS':         40,
    'AutoNav':     40,
    'OAK×4':       32,
    'USB cam':     20,
    'Trimble fwd': 28,
    'Trimble aft': 28,
    'CUAV fwd':    22,
    'CUAV aft':    22,
}

def leader_and_label(cx, cy, name, angle_deg, leader=None, font=10):
    if leader is None:
        leader = LEADER_LEN.get(name, 26)
    rad = math.radians(angle_deg)
    lx = cx + leader * math.cos(rad)
    ly = cy - leader * math.sin(rad)
    if -90 < angle_deg < 90:   anchor, tx_off = 'start', 3
    elif 90 < angle_deg < 270 or angle_deg < -90: anchor, tx_off = 'end', -3
    else: anchor, tx_off = 'middle', 0
    return [
        line(cx, cy, lx, ly, stroke='#555', **{'stroke-width': '0.5'}),
        text(lx + tx_off, ly + 4, name,
             **{'font-size': str(font), 'fill': '#111', 'text-anchor': anchor,
                'font-weight': '500'}),
    ]

# --- Views ----------------------------------------------------------
def view_top():
    parts = []
    # Hull outline
    parts.append(rect(top_x(HULL_LENGTH_AFT), top_y(HULL_BEAM/2),
                      (HULL_LENGTH_FWD - HULL_LENGTH_AFT) * PX_PER_CM,
                      HULL_BEAM * PX_PER_CM,
                      fill='#fafcfd', stroke='#333',
                      **{'stroke-width': '1', 'rx': '20', 'ry': '20'}))
    # Centerline
    parts.append(line(top_x(HULL_LENGTH_AFT), top_y(0),
                      top_x(HULL_LENGTH_FWD), top_y(0),
                      stroke='#aaa', **{'stroke-width': '0.6', 'stroke-dasharray': '6,3,1,3'}))
    # Center rail
    parts.append(line(top_x(-105), top_y(0), top_x(105), top_y(0),
                      stroke='#bbb', **{'stroke-width': '5', 'stroke-linecap': 'round',
                                         'opacity': '0.6'}))
    # Axis labels
    parts.append(text(top_x(HULL_LENGTH_FWD) + 8, top_y(0) + 4, '+x bow',
                      **{'font-size': '10', 'fill': '#777'}))
    parts.append(text(top_x(HULL_LENGTH_AFT) - 8, top_y(0) + 4, '−x stern',
                      **{'font-size': '10', 'fill': '#777', 'text-anchor': 'end'}))
    parts.append(text(top_x(0), top_y(HULL_BEAM/2) - 8, '+y port',
                      **{'font-size': '10', 'fill': '#777', 'text-anchor': 'middle'}))
    parts.append(text(top_x(0), top_y(-HULL_BEAM/2) + 20, '−y stbd',
                      **{'font-size': '10', 'fill': '#777', 'text-anchor': 'middle'}))
    # Structural: camera tower position (top view = small circle on centerline)
    parts.append(circ(top_x(31), top_y(0), 4, fill='#aaa', stroke='#666',
                      **{'stroke-width': '0.6'}))
    parts.append(text(top_x(31) + 7, top_y(0) + 22, 'mast',
                      **{'font-size': '8.5', 'fill': '#888', 'font-style': 'italic'}))
    # Holders before sensors
    for n, x, y, z, c, a in SENSORS:
        parts += draw_holder('top', n, x, y, z, PX_PER_CM)
    # Sensor shapes + leaders
    for n, x, y, z, c, a in SENSORS:
        parts += draw_shape('top', n, x, y, z, c, PX_PER_CM)
        parts += leader_and_label(top_x(x), top_y(y), n, a)
    # IMU marker inside the AutoNav box (no leader — inline note)
    parts.append(circ(top_x(-99), top_y(0), 2, fill='#ff6600'))
    parts.append(text(top_x(-99) + 4, top_y(0) + 12, 'Cube',
                      **{'font-size': '8', 'fill': '#ff6600',
                         'font-style': 'italic'}))
    # CAD dimensions — Trimble baseline
    dim_y = top_y(HULL_BEAM/2) - 22
    parts += cad_dim_h(top_x(-106.5), top_x(99.0), dim_y,
                       top_y(0), top_y(0),
                       '205.5 cm (Trimble baseline)', text_above=True)
    # CUAV baseline (below the centerline)
    dim_y2 = top_y(-HULL_BEAM/2) + 30
    parts += cad_dim_h(top_x(-83.5), top_x(83.5), dim_y2,
                       top_y(0), top_y(0),
                       '167 cm (CUAV baseline)', text_above=True)
    # SVS port offset (y direction)
    svs_x_px = top_x(-45)
    dim_x = top_x(-45) - 35
    parts += cad_dim_v(top_y(0), top_y(25), dim_x,
                       svs_x_px, svs_x_px,
                       '25 cm (SVS port)')
    parts.append(text(5, -8, 'TOP VIEW (XY)', **{'font-size': '12',
                                                  'font-weight': 'bold', 'fill': '#222'}))
    return parts

def view_side():
    parts = []
    # Hull outline (shallow)
    pts = [(side_x(HULL_LENGTH_FWD), side_y(0)),
           (side_x(HULL_LENGTH_FWD - 10), side_y(HULL_BOTTOM_Z)),
           (side_x(HULL_LENGTH_AFT + 10), side_y(HULL_BOTTOM_Z)),
           (side_x(HULL_LENGTH_AFT), side_y(0))]
    parts.append(polygon(pts, fill='#fafcfd', stroke='#333',
                         **{'stroke-width': '1'}))
    # Close top of hull
    parts.append(line(side_x(HULL_LENGTH_AFT), side_y(0),
                      side_x(HULL_LENGTH_FWD), side_y(0),
                      stroke='#333', **{'stroke-width': '1'}))
    # Rail
    parts.append(line(side_x(-105), side_y(RAIL_Z), side_x(105), side_y(RAIL_Z),
                      stroke='#bbb', **{'stroke-width': '5',
                                         'stroke-linecap': 'round', 'opacity': '0.6'}))
    # Cages (simplified)
    for ux in (-100, 100):
        parts.append(line(side_x(ux), side_y(0), side_x(ux), side_y(77),
                          stroke='#bbb', **{'stroke-width': '2'}))
    parts.append(line(side_x(-100), side_y(77), side_x(100), side_y(77),
                      stroke='#bbb', **{'stroke-width': '2'}))
    # Camera tower + camera bracket (structural, not labeled as sensor)
    parts.append(line(side_x(31), side_y(RAIL_Z), side_x(31), side_y(MAST_TOP_Z),
                      stroke='#888', **{'stroke-width': '2'}))
    parts.append(line(side_x(24), side_y(141), side_x(38), side_y(141),
                      stroke='#888', **{'stroke-width': '1.5'}))
    parts.append(text(side_x(31) + 10, side_y(115),
                      'mast (factory WiFi ext.)',
                      **{'font-size': '8.5', 'fill': '#888',
                         'font-style': 'italic'}))
    # Reference lines
    parts.append(line(side_x(SIDE_X_MIN), side_y(0), side_x(SIDE_X_MAX), side_y(0),
                      stroke='#888', **{'stroke-width': '0.6', 'stroke-dasharray': '6,3,1,3'}))
    parts.append(line(side_x(SIDE_X_MIN), side_y(HULL_BOTTOM_Z),
                      side_x(SIDE_X_MAX), side_y(HULL_BOTTOM_Z),
                      stroke='#ccc', **{'stroke-width': '0.5', 'stroke-dasharray': '2,2'}))
    parts.append(text(side_x(SIDE_X_MIN) + 4, side_y(HULL_BOTTOM_Z) - 2,
                      f'hull bottom ≈ z={HULL_BOTTOM_Z} (approx)',
                      **{'font-size': '9', 'fill': '#888'}))
    parts.append(text(side_x(SIDE_X_MIN) + 4, side_y(0) - 2, 'z=0 hull floor',
                      **{'font-size': '9', 'fill': '#888'}))
    parts.append(text(side_x(SIDE_X_MIN) + 4, side_y(RAIL_Z) - 2,
                      'rail top z=89 [EST]',
                      **{'font-size': '9', 'fill': '#888'}))
    parts.append(text(side_x(HULL_LENGTH_FWD) + 8, side_y(0) + 4, '+x',
                      **{'font-size': '10', 'fill': '#777'}))
    parts.append(text(side_x(-95), side_y(MAST_TOP_Z) - 2, '+z',
                      **{'font-size': '10', 'fill': '#777'}))
    # Holders + shapes
    for n, x, y, z, c, a in SENSORS:
        parts += draw_holder('side', n, x, y, z, PX_PER_CM)
    for n, x, y, z, c, a in SENSORS:
        parts += draw_shape('side', n, x, y, z, c, PX_PER_CM)
        parts += leader_and_label(side_x(x), side_y(z), n, a)
    # IMU marker inside the AutoNav box (side view, not a labeled sensor)
    parts.append(circ(side_x(-99), side_y(5), 2.5, fill='#ff6600'))
    parts.append(text(side_x(-99) + 4, side_y(5) + 3, 'Cube',
                      **{'font-size': '8', 'fill': '#ff6600',
                         'font-style': 'italic'}))
    # CAD dimensions — rail + camera tower heights on right side
    dim_x = side_x(SIDE_X_MAX) + 20
    parts += cad_dim_v(side_y(0), side_y(RAIL_Z), dim_x,
                       side_x(105), side_x(105), '89 cm')
    parts += cad_dim_v(side_y(0), side_y(MAST_TOP_Z), dim_x + 50,
                       side_x(31), side_x(31), '142 cm')
    parts.append(text(5, -8, 'SIDE VIEW (XZ) — port side',
                      **{'font-size': '12', 'font-weight': 'bold', 'fill': '#222'}))
    return parts

def view_detail():
    parts = []
    pts = [(detail_x(DETAIL_X_MAX), detail_y(0)),
           (detail_x(DETAIL_X_MAX), detail_y(HULL_BOTTOM_Z)),
           (detail_x(DETAIL_X_MIN), detail_y(HULL_BOTTOM_Z)),
           (detail_x(DETAIL_X_MIN), detail_y(0))]
    parts.append(polygon(pts, fill='#fafcfd', stroke='#333',
                         **{'stroke-width': '1'}))
    parts.append(line(detail_x(DETAIL_X_MIN), detail_y(0),
                      detail_x(DETAIL_X_MAX), detail_y(0),
                      stroke='#888', **{'stroke-width': '0.6', 'stroke-dasharray': '6,3,1,3'}))
    # Grid
    for x_g in range(DETAIL_X_MIN, DETAIL_X_MAX + 1, 5):
        parts.append(line(detail_x(x_g), detail_y(DETAIL_Z_MIN),
                          detail_x(x_g), detail_y(DETAIL_Z_MAX),
                          stroke='#eee', **{'stroke-width': '0.35'}))
        if x_g % 10 == 0:
            parts.append(text(detail_x(x_g), detail_y(DETAIL_Z_MIN) + 12,
                              f'{x_g}', **{'font-size': '7.5', 'fill': '#aaa',
                                           'text-anchor': 'middle'}))
    for z_g in range(DETAIL_Z_MIN, DETAIL_Z_MAX + 1, 5):
        parts.append(line(detail_x(DETAIL_X_MIN), detail_y(z_g),
                          detail_x(DETAIL_X_MAX), detail_y(z_g),
                          stroke='#eee', **{'stroke-width': '0.35'}))
        if z_g % 10 == 0:
            parts.append(text(detail_x(DETAIL_X_MIN) - 3, detail_y(z_g) + 3,
                              f'{z_g}', **{'font-size': '7.5', 'fill': '#aaa',
                                           'text-anchor': 'end'}))
    # Shapes (only under-hull payload cluster)
    for n, x, y, z, c, a in SENSORS:
        if not (DETAIL_X_MIN <= x <= DETAIL_X_MAX): continue
        if not (DETAIL_Z_MIN <= z <= DETAIL_Z_MAX): continue
        parts += draw_shape('detail', n, x, y, z, c, PX_PER_CM * DETAIL_SCALE)
        if n == 'SVS':
            cx0, cy0 = detail_x(x), detail_y(z)
            parts.append(text(cx0 + 3, cy0 - 14, 'y=+25 port',
                              **{'font-size': '8.5', 'fill': '#bd00bd',
                                 'font-style': 'italic'}))
        cx, cy = detail_x(x), detail_y(z)
        # Stagger labels: SBG up-left, M3 down, Fin up-right, SVS up-left
        if n == 'SBG':   lab_dx, lab_dy = 25, -20
        elif n == 'M3':  lab_dx, lab_dy = 28, 25
        elif n == 'Fin': lab_dx, lab_dy = 22, -20
        elif n == 'SVS': lab_dx, lab_dy = -25, -20
        else:            lab_dx, lab_dy = 18, -10
        parts.append(line(cx, cy, cx + lab_dx, cy + lab_dy,
                          stroke='#555', **{'stroke-width': '0.5'}))
        anchor = 'end' if lab_dx < 0 else 'start'
        parts.append(text(cx + lab_dx + (3 if lab_dx > 0 else -3),
                          cy + lab_dy + 3,
                          f'{n} ({x:+.0f},{z:+.1f})',
                          **{'font-size': '10', 'fill': '#111',
                             'font-weight': '500', 'text-anchor': anchor}))
    # 28 cm M3↔Fin dimension (CAD style)
    dim_y = detail_y(-40)
    parts += cad_dim_h(detail_x(-23), detail_x(5), dim_y,
                       detail_y(-14.5), detail_y(-12.3),
                       '28 cm (M3 ↔ Fairing Fin)', text_above=True)
    parts.append(text(5, -8,
                      'DETAIL — under-hull cluster (×2.5)',
                      **{'font-size': '12', 'font-weight': 'bold', 'fill': '#222'}))
    return parts

def legend():
    parts = []
    y = 0
    parts.append(text(0, y, 'Legend / status',
                      **{'font-size': '13', 'font-weight': 'bold', 'fill': '#111'})); y += 18
    parts.append(text(0, y, 'cm, base_link at origin. REP-103: +x fwd, +y port, +z up.',
                      **{'font-size': '10', 'fill': '#333'})); y += 18
    notes = {
        'base_link':   'hull floor, center screw',
        'SBG':         'Ellipse-D-G4A2-B1 SN 000034256; COM4 @115200; rpy=(π,0,0)',
        'Trimble fwd': 'GNSS/MSK puck on 2 cm stud (SBG input)',
        'Trimble aft': 'GNSS/MSK puck on 2 cm stud (SBG input)',
        'CUAV fwd':    'C-RTK 2HP puck on 7.5 cm holder (Cube)',
        'CUAV aft':    'C-RTK 2HP puck on 7.5 cm holder (Cube)',
        'OAK×4':       'fwd/port/stbd/aft, 5° down',
        'USB cam':     'forward bullet cam at rail end',
        'AutoNav':     'enclosure; Cube FCU + IMU inside',
        'M3':          'Kongsberg M3; ~15×15 cm',
        'Fin':         'factory Fairing Fin; bottom z=−12.3',
        'SVS':         'AML 6000 m, SN 11357; COM3 @9600; y=+25 port',
    }
    for name, x, yy, z, color, ang in SENSORS:
        parts.append(circ(6, y - 3, 3.5, fill=color, stroke='black',
                          **{'stroke-width': '0.5'}))
        parts.append(text(18, y, f'{name} ({x:+.1f}, {yy:+.1f}, {z:+.1f})',
                          **{'font-size': '9.5', 'fill': '#222',
                             'font-weight': '500'})); y += 11
        if name in notes:
            parts.append(text(18, y, notes[name],
                              **{'font-size': '8.5', 'fill': '#777'})); y += 12
        else:
            y += 3
    y += 6
    for s in [
        'Rail top z=89 cm [EST] — z derivations inherit',
        'Boat pitch on cart: 1.39° nose-down (transient)',
        'Hull / mast outlines stylized for layout',
    ]:
        parts.append(text(0, y, s, **{'font-size': '9', 'fill': '#777'})); y += 12
    return parts

def build_svg():
    defs = '''<defs>
  <marker id="arr" viewBox="0 0 10 10" refX="5" refY="5"
          markerWidth="5" markerHeight="5" orient="auto-start-reverse">
    <path d="M 0 0 L 10 5 L 0 10 Z" fill="#222"/>
  </marker>
  <marker id="oak_arr" viewBox="0 0 10 10" refX="8" refY="5"
          markerWidth="4" markerHeight="4" orient="auto">
    <path d="M 0 0 L 10 5 L 0 10 Z" fill="#0aa"/>
  </marker>
</defs>'''
    top_g = group(view_top(),
                  transform=f'translate({MARGIN}, {TITLE_H + MARGIN})')
    side_g = group(view_side(),
                   transform=f'translate({MARGIN}, {TITLE_H + TOP_H + 2*MARGIN})')
    right_x = MARGIN + LEFT_COL_W + PANEL_GAP
    detail_g = group(view_detail(),
                     transform=f'translate({right_x}, {TITLE_H + MARGIN})')
    legend_g = group(legend(),
                     transform=f'translate({right_x}, {TITLE_H + MARGIN + DETAIL_H + MARGIN})')
    title = text(MARGIN, TITLE_H - 14,
                 'BizzyBoat hydro payload — offsets preview (2026-04-22)',
                 **{'font-size': '16', 'font-weight': 'bold', 'fill': '#111'})
    subtitle = text(MARGIN, TITLE_H + 4,
                    'All positions in cm relative to base_link (hull-floor center screw). Shapes to approximate scale.',
                    **{'font-size': '10', 'fill': '#555'})
    border = rect(2, 2, TOTAL_W - 4, TOTAL_H - 4, fill='none',
                  stroke='#333', **{'stroke-width': '1'})
    title_block_y = TOTAL_H - 18
    title_block = text(TOTAL_W - MARGIN, title_block_y,
                       'DRAWN: Claude Code Agent · SCALE: varies · UNITS: cm · STATUS: preview',
                       **{'font-size': '9', 'fill': '#555', 'text-anchor': 'end',
                          'font-style': 'italic'})
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {TOTAL_W} {TOTAL_H}"
     width="{TOTAL_W}" height="{TOTAL_H}" font-family="sans-serif">
<rect width="{TOTAL_W}" height="{TOTAL_H}" fill="white"/>
{defs}
{border}
{title}
{subtitle}
{top_g}
{side_g}
{detail_g}
{legend_g}
{title_block}
</svg>
'''

if __name__ == '__main__':
    import os
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'bizzyboat_offsets.svg')
    with open(out, 'w') as f:
        f.write(build_svg())
    print(f'wrote {out}')
