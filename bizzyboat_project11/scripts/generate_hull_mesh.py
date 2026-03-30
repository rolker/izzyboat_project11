#!/usr/bin/env python3
"""Generate an approximate EchoBoat 240 hull mesh as STL.

The hull is modeled as a flat-bottomed monohull with a tapered bow,
blunt stern, and gunwale walls above the deck. Dimensions are from
the EchoBoat 240 manual:
  Length: 2.40m, Beam: 0.90m, Hull depth: 0.30m

The mesh origin is at the base_link reference point (center screw
hole in the hull floor, z=0 at deck surface). The hull bottom is
at z=-depth, the deck (interior floor) is at z=0, and the gunwale
tops rise from ~0.25m amidships to ~0.35m at the bow (bow rake).

Cross-section at each station is a U-shape (bathtub profile):

    8---------3       outer gunwale (z=gwh)
    |         |
    7--     --4       inner gunwale (z=gwh)
       |   |
       6---5          inner deck (z=0)
       |   |
    9---------2       outer deck level (z=0)
       |   |
    0---------1       outer bottom (z=-depth)

Usage:
    python3 generate_hull_mesh.py [output_path]

Default output: ../meshes/hull.stl (relative to this script)
"""

import sys
from pathlib import Path

import numpy as np
import trimesh


def generate_hull():
    """Create an approximate EchoBoat 240 hull mesh with gunwales."""
    # Hull dimensions (meters)
    beam = 0.90
    depth = 0.30        # hull below deck
    wall = 0.04         # hull wall thickness
    half_beam = beam / 2.0

    # base_link is roughly amidships — estimated 1.2m from bow, 1.2m from stern
    bow_fwd = 1.20
    stern_aft = 1.20

    # Bow taper starts about 0.6m before the bow tip
    bow_taper_start = bow_fwd - 0.60

    # Stations from stern to bow (x coordinates)
    stations_x = [
        -stern_aft,         # transom (stern)
        -stern_aft + 0.10,  # just forward of transom
        -0.30,              # aft of amidships
        0.0,                # amidships (origin)
        0.30,               # forward of amidships
        bow_taper_start,    # bow taper begins
        bow_fwd - 0.30,     # mid-taper
        bow_fwd - 0.10,     # near bow
        bow_fwd,            # bow tip
    ]

    # Half-beam at each station (hull narrows toward bow)
    half_beams = [
        half_beam * 0.95,   # stern is slightly narrower
        half_beam,
        half_beam,
        half_beam,
        half_beam,
        half_beam,          # taper starts
        half_beam * 0.70,   # narrowing
        half_beam * 0.35,   # narrow
        0.02,               # bow tip (nearly pointed)
    ]

    # Gunwale height above deck (z=0) at each station — bow rake
    # From photos and side-view diagrams, the gunwale rises toward the bow.
    gunwale_heights = [
        0.25,   # stern transom
        0.25,
        0.25,
        0.25,   # amidships
        0.25,
        0.27,   # starting to rise toward bow
        0.30,
        0.33,
        0.35,   # bow tip (highest point)
    ]

    n_stations = len(stations_x)
    vpn = 10  # vertices per station (U-shaped cross-section)
    vertices = []

    for i in range(n_stations):
        x = stations_x[i]
        hb = half_beams[i]
        gwh = gunwale_heights[i]
        hbi = max(hb - wall, 0.001)  # inner half-beam (clamped for narrow bow)

        # 10 vertices per station forming U-shaped cross-section
        vertices.extend([
            [x,  hb,   -depth],  # 0: outer port bottom
            [x, -hb,   -depth],  # 1: outer stbd bottom
            [x, -hb,    0.0],    # 2: outer stbd at deck level
            [x, -hb,    gwh],    # 3: outer stbd gunwale top
            [x, -hbi,   gwh],    # 4: inner stbd gunwale top
            [x, -hbi,   0.0],    # 5: inner stbd deck
            [x,  hbi,   0.0],    # 6: inner port deck
            [x,  hbi,   gwh],    # 7: inner port gunwale top
            [x,  hb,    gwh],    # 8: outer port gunwale top
            [x,  hb,    0.0],    # 9: outer port at deck level
        ])

    vertices = np.array(vertices)
    faces = []

    # Longitudinal faces between adjacent stations.
    # Each edge around the 10-vertex perimeter generates a quad strip.
    perimeter_edges = [
        (0, 1),  # outer bottom
        (1, 2),  # outer stbd below deck
        (2, 3),  # outer stbd above deck
        (3, 4),  # gunwale cap stbd
        (4, 5),  # inner stbd wall
        (5, 6),  # deck floor
        (6, 7),  # inner port wall
        (7, 8),  # gunwale cap port
        (8, 9),  # outer port above deck
        (9, 0),  # outer port below deck
    ]

    # The perimeter is CW in the YZ plane, so winding must be
    # (A, C, B) and (A, D, C) for outward-facing normals.
    for i in range(n_stations - 1):
        b = i * vpn
        nb = (i + 1) * vpn
        for e0, e1 in perimeter_edges:
            faces.append([b + e0, nb + e1, b + e1])
            faces.append([b + e0, nb + e0, nb + e1])

    # End caps: stern and bow are solid walls (outer rectangle only).
    # Double-sided so they're visible from both inside and outside.

    # Stern transom
    b = 0
    faces.append([b + 0, b + 1, b + 8])  # outward (-x)
    faces.append([b + 1, b + 3, b + 8])
    faces.append([b + 0, b + 8, b + 1])  # inward (+x)
    faces.append([b + 1, b + 8, b + 3])

    # Bow tip
    b = (n_stations - 1) * vpn
    faces.append([b + 0, b + 8, b + 1])  # outward (+x)
    faces.append([b + 1, b + 8, b + 3])
    faces.append([b + 0, b + 1, b + 8])  # inward (-x)
    faces.append([b + 1, b + 3, b + 8])

    faces = np.array(faces)
    hull_mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    hull_mesh.fix_normals()
    hull_mesh.merge_vertices()

    return hull_mesh


def main():
    script_dir = Path(__file__).parent
    default_output = script_dir.parent / 'meshes' / 'hull.stl'

    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    hull = generate_hull()
    hull.export(str(output_path))
    print(f'Hull mesh written to {output_path}')
    print(f'  Vertices: {len(hull.vertices)}')
    print(f'  Faces: {len(hull.faces)}')
    bounds = hull.bounds
    print(f'  Bounds: x=[{bounds[0][0]:.2f}, {bounds[1][0]:.2f}]'
          f' y=[{bounds[0][1]:.2f}, {bounds[1][1]:.2f}]'
          f' z=[{bounds[0][2]:.2f}, {bounds[1][2]:.2f}]')


if __name__ == '__main__':
    main()
