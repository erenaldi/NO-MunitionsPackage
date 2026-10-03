"""Review-only crops of a saved STEP plus the matching snapshot jobs.

Why: the snapshot renderer ignores camera `target` (and `zoom` scales only about the
model centre), so a close-up needs the geometry itself cropped around the area.
This replaces the per-pass `*_focus.py` scripts and hand-written job JSON.

Reads the saved STEP only; no geometry is authored. Every leaf is kept whole when it
lies inside the clip, dropped when disjoint, and intersected with the clip when it
straddles an edge (same rule as the R19-R21 crop scripts).
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from pathlib import Path

from cadgen import build123d as bd, read_scene, step

FACE_VIEW = {"direction": [0.3, 1, -1]}
OUTBOARD_VIEW = {"direction": [0.5, 0.7, 0.7]}
GRAZING_VIEW = {"direction": [0.96, -0.17, 0.18]}
STANDARD_VIEWS = {"face": FACE_VIEW, "outboard": OUTBOARD_VIEW, "grazing": GRAZING_VIEW}
QUALITY = {"tessellation": {"chordTolerance": 5e-05, "angleTolerance": 0.05}}


def x_window(x0, x1, half=400.0):
    """Clip box spanning X x0..x1, +-half in Y and Z (a slice of the whole body)."""
    return bd.Box(x1 - x0, 2 * half, 2 * half).translate(((x0 + x1) / 2.0, 0.0, 0.0))


def cube_at(centre, size):
    """Clip cube of edge `size` centred on `centre` (x, y, z)."""
    return bd.Box(size, size, size).translate(tuple(centre))


def radial_point(x, radius, clock_degrees):
    """(x, y, z) at `radius` from the axis, clock 0 = +Z, 90 = +Y."""
    a = math.radians(clock_degrees)
    return (x, radius * math.sin(a), radius * math.cos(a))


def crop_scene(saved, clip, label):
    """Compound of every leaf of `saved` restricted to `clip` (see module docstring)."""
    scene = read_scene(Path(saved))
    cb = clip.bounding_box()
    kept = []
    for leaf in scene.leaves():
        shape = scene.resolve(leaf.ref).shape()
        box = shape.bounding_box()
        if (box.max.X < cb.min.X or box.min.X > cb.max.X or box.max.Y < cb.min.Y or
                box.min.Y > cb.max.Y or box.max.Z < cb.min.Z or box.min.Z > cb.max.Z):
            continue
        if (cb.min.X <= box.min.X and box.max.X <= cb.max.X and cb.min.Y <= box.min.Y and
                box.max.Y <= cb.max.Y and cb.min.Z <= box.min.Z and box.max.Z <= cb.max.Z):
            part = shape
        else:
            part = shape & clip
            if part is None or part.volume < 1e-6:
                continue
            part.label = f"{leaf.label}_crop"
            part.color = shape.color
        kept.append(part)
    return bd.Compound(children=kept, label=label)


# NOTE: there is no build_crop(). cadgen needs a module-level @step-decorated model in the script that runs,
# so write a tiny crop script per pass (pattern: cad/halberd_rounded_square/src/halberd_r19_fin_roots_focus.py)
# whose model returns crop_scene(saved, clip, label); a dynamic wrapper fails with "declares no CAD model".


def snapshot_jobs(crops, views=None):
    """Snapshot job list. `crops` maps a crop STEP path to (png_prefix, [view names])."""
    jobs = []
    for step_path, (prefix, names) in crops.items():
        jobs.append({
            "input": str(step_path),
            "mode": "view",
            "outputs": [{"path": f"{prefix}_{n}.png", "camera": (views or STANDARD_VIEWS)[n]} for n in names],
            "output": {"viewLabels": False, "padding": 0.04, "sizeProfile": "diagnostic"},
            "quality": QUALITY,
        })
    return jobs


def write_jobs(path, crops, views=None):
    Path(path).write_text(json.dumps(snapshot_jobs(crops, views), indent=1), encoding="utf-8")
    return Path(path)


def render(job_path, cwd, python=None, timeout_s=300):
    """Run `cadgen snapshot --job`; returns the parsed JSON result. Raises on failure/timeout."""
    env = dict(os.environ, CADGEN_DAEMON="0")
    proc = subprocess.run([python or sys.executable, "-m", "cadgen.cli", "snapshot", "--job",
                           str(job_path), "--json"], cwd=str(cwd), env=env, capture_output=True,
                          text=True, timeout=timeout_s)
    if proc.returncode != 0:
        raise RuntimeError(proc.stdout[-800:] + proc.stderr[-400:])
    return json.loads(proc.stdout.strip().splitlines()[-1])
