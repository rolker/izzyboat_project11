#!/usr/bin/env python3
"""Generate an approximate EchoBoat 240 hull mesh as STL.

The hull is modeled as a flat-bottomed monohull with a tapered bow
and blunt stern. Dimensions are from the EchoBoat 240 manual:
  Length: 2.40m, Beam: 0.90m, Hull depth: 0.30m

The mesh origin is at the base_link reference point (center screw
hole in the hull floor, z=0 at deck surface). The hull bottom is
at z=-depth and the deck is at z=0.

Usage:
    python3 generate_hull_mesh.py [output_path]

Default output: ../meshes/hull.stl (relative to this script)
"""

import sys
from pathlib import Path

import numpy as np
import trimesh


def generate_hull():
    """Create an approximate EchoBoat 240 hull mesh."""
    # Hull dimensions (meters)
    length = 2.40
    beam = 0.90
    depth = 0.30

    # base_link is roughly amidships — estimated 1.2m from bow, 1.2m from stern
    bow_fwd = 1.20   # distance from origin to bow tip
    stern_aft = 1.20  # distance from origin to transom

    # Bow taper starts about 0.6m before the bow tip
    bow_taper_start = bow_fwd - 0.60
    half_beam = beam / 2.0

    # Build hull as a set of cross-sections (waterlines), then loft
    # We'll use a simpler approach: construct the hull from vertices
    # defining the outline at several stations along the length

    # Stations from stern to bow (x coordinates)
    stations = [
        -stern_aft,        # transom (stern)
        -stern_aft + 0.10, # just forward of transom
        -0.30,             # aft of amidships
        0.0,               # amidships (origin)
        0.30,              # forward of amidships
        bow_taper_start,   # bow taper begins
        bow_fwd - 0.30,    # mid-taper
        bow_fwd - 0.10,    # near bow
        bow_fwd,           # bow tip
    ]

    # Half-beam at each station (hull narrows toward bow)
    half_beams = [
        half_beam * 0.95,  # stern is slightly narrower
        half_beam,
        half_beam,
        half_beam,
        half_beam,
        half_beam,         # taper starts
        half_beam * 0.70,  # narrowing
        half_beam * 0.35,  # narrow
        0.02,              # bow tip (nearly pointed)
    ]

    # Build vertices: for each station, create 4 corners
    # (port-bottom, starboard-bottom, starboard-top, port-top)
    vertices = []
    for x, hb in zip(stations, half_beams):
        vertices.extend([
            [x, hb, -depth],      # port bottom
            [x, -hb, -depth],     # starboard bottom
            [x, -hb, 0.0],       # starboard top (deck, z=0)
            [x, hb, 0.0],        # port top (deck, z=0)
        ])

    # Also add bottom vertices with slight V-shape for realism
    # (the hull has a shallow V bottom, deeper at center)
    # We'll keep it simple with flat bottom for now

    vertices = np.array(vertices)
    faces = []

    n_stations = len(stations)

    # Side faces between adjacent stations
    for i in range(n_stations - 1):
        base = i * 4
        next_base = (i + 1) * 4
        for j in range(4):
            j_next = (j + 1) % 4
            # Two triangles per quad
            v0 = base + j
            v1 = base + j_next
            v2 = next_base + j_next
            v3 = next_base + j
            faces.append([v0, v1, v2])
            faces.append([v0, v2, v3])

    # Stern transom face (close the back)
    faces.append([0, 1, 2])
    faces.append([0, 2, 3])

    # Bow tip face (close the front) — last station
    bow_base = (n_stations - 1) * 4
    faces.append([bow_base, bow_base + 2, bow_base + 1])
    faces.append([bow_base, bow_base + 3, bow_base + 2])

    faces = np.array(faces)
    hull_mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    hull_mesh.fix_normals()

    # Add deck (top face) — close the top between all stations
    deck_verts = []
    deck_faces = []
    vert_offset = len(hull_mesh.vertices)

    for i in range(n_stations):
        base = i * 4
        # Top vertices are indices 2 (starboard) and 3 (port)
        deck_verts.append(vertices[base + 3])  # port top
        deck_verts.append(vertices[base + 2])  # starboard top

    deck_verts = np.array(deck_verts)

    for i in range(n_stations - 1):
        p0 = vert_offset + i * 2       # port current
        s0 = vert_offset + i * 2 + 1   # starboard current
        p1 = vert_offset + (i + 1) * 2     # port next
        s1 = vert_offset + (i + 1) * 2 + 1  # starboard next
        deck_faces.append([p0, s0, s1])
        deck_faces.append([p0, s1, p1])

    # Bottom face
    bottom_verts = []
    bottom_offset = vert_offset + len(deck_verts)

    for i in range(n_stations):
        base = i * 4
        bottom_verts.append(vertices[base])      # port bottom
        bottom_verts.append(vertices[base + 1])   # starboard bottom

    bottom_verts = np.array(bottom_verts)
    bottom_faces = []

    for i in range(n_stations - 1):
        p0 = bottom_offset + i * 2
        s0 = bottom_offset + i * 2 + 1
        p1 = bottom_offset + (i + 1) * 2
        s1 = bottom_offset + (i + 1) * 2 + 1
        bottom_faces.append([p0, s1, s0])
        bottom_faces.append([p0, p1, s1])

    all_verts = np.vstack([hull_mesh.vertices, deck_verts, bottom_verts])
    all_faces = np.vstack([
        hull_mesh.faces,
        np.array(deck_faces),
        np.array(bottom_faces),
    ])

    complete_hull = trimesh.Trimesh(vertices=all_verts, faces=all_faces)
    complete_hull.fix_normals()
    complete_hull.merge_vertices()

    return complete_hull


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
