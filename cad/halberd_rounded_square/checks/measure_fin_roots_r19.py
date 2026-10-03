"""F07/F08 feasibility: measure the main-fin and booster-fin roots on saved R19.

Read-only against STEP/halberd_r19_surface.step and reviews/halberd_r19_surface.json.
Writes reviews/halberd_r19_fin_roots.json. Builds no geometry for the model.

Method (per fin, per side of the blade, at axial stations every STATION_STEP mm):
- cross-section the blade and the adjacent skin faces with the plane X = x;
- root point = where the blade outline meets the adjacent skin in that section;
- walk the adjacent skin section away from the blade (arc length d from the root);
- classify the skin (face geom type, in-section turning angle), and measure
  clearance from every walked point to existing details: all non-host leaves
  (R18 hatches, R19 heads/raised parts, F05 strips, rings), R19 engraved panel
  outlines/interiors (from the saved metadata plan) and circumferential seams /
  the stage split (axial distance).
Main fins: test a 20 x 8 mm seat (axial x across, starting SEAT_LAND mm from the
root edge). Booster fins: test a 3 mm collar band starting at the root edge.
Fit rule: >= 2 mm clearance to existing details and seams.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from cadgen import build123d as bd, read_scene

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "shared"))
from surface_detail import skin_point  # noqa: E402

STEP_PATH = ROOT / "STEP" / "halberd_r19_surface.step"
META = ROOT / "reviews" / "halberd_r19_surface.json"
OUT = ROOT / "reviews" / "halberd_r19_fin_roots.json"

MAIN_HOST, BOOSTER_HOST = "main_body_intake_r12", "booster_body"
STAGE_SPLIT_X = -1123.3
CLEARANCE = 2.0
BAND = 30.0                 # adjacent-skin band studied beside the root
STATION_STEP = 2.0
SAMPLE = 0.2                # section discretisation (mm)
WALK_STEP = 0.5             # walked-point spacing (mm)
SEAT_LEN, SEAT_W, SEAT_LAND = 20.0, 8.0, 2.0      # main-fin seat (F07)
COLLAR_W = 3.0                                    # booster collar band (F08)
GROOVE_HALF = 0.2


# ----------------------------------------------------------------------------
# geometry helpers

def frame(clock):
    a = math.radians(clock)
    return np.array([0.0, math.sin(a), math.cos(a)]), np.array([0.0, math.cos(a), -math.sin(a)])


def section_points(face, x):
    """Points (N,3) of the face's section with plane X = x, discretised."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
    from OCP.gp import gp_Pln, gp_Pnt, gp_Dir
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.GCPnts import GCPnts_UniformAbscissa
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_EDGE
    from OCP.TopoDS import TopoDS

    sec = BRepAlgoAPI_Section(face.wrapped, gp_Pln(gp_Pnt(x, 0, 0), gp_Dir(1, 0, 0)), False)
    sec.Approximation(True)
    sec.Build()
    pts = []
    exp = TopExp_Explorer(sec.Shape(), TopAbs_EDGE)
    while exp.More():
        curve = BRepAdaptor_Curve(TopoDS.Edge_s(exp.Current()))
        ua = GCPnts_UniformAbscissa(curve, SAMPLE)
        if ua.IsDone() and ua.NbPoints() >= 2:
            for i in range(1, ua.NbPoints() + 1):
                p = curve.Value(ua.Parameter(i))
                pts.append((p.X(), p.Y(), p.Z()))
        p0, p1 = curve.Value(curve.FirstParameter()), curve.Value(curve.LastParameter())
        pts.append((p0.X(), p0.Y(), p0.Z()))
        pts.append((p1.X(), p1.Y(), p1.Z()))
        exp.Next()
    return np.array(pts).reshape(-1, 3)


def hull2(points):
    pts = sorted(set(map(tuple, np.round(points, 6))))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def inside_hull(hull, pts2, eps=1e-6):
    hull = np.array(hull)
    n = len(hull)
    inside = np.ones(len(pts2), dtype=bool)
    for i in range(n):
        a, b = hull[i], hull[(i + 1) % n]
        c = (b[0] - a[0]) * (pts2[:, 1] - a[1]) - (b[1] - a[1]) * (pts2[:, 0] - a[0])
        inside &= c >= -eps
    return inside


def walk(points, tags, start, away, limit):
    """Greedy ordered walk over an unordered section point set from `start`.

    `away` is a 3D direction for the first step. Returns [(d, point, tag)].
    """
    tree = cKDTree(points)
    visited = np.zeros(len(points), dtype=bool)
    out = [(0.0, start, None)]
    cur, d = start, 0.0
    first = True
    while d < limit:
        idx = tree.query_ball_point(cur, 1.0)
        cand = [i for i in idx if not visited[i] and np.linalg.norm(points[i] - cur) > 1e-6]
        if first:
            cand = [i for i in cand if np.dot(points[i] - cur, away) > 0.0] or cand
        if not cand:
            break
        j = min(cand, key=lambda i: np.linalg.norm(points[i] - cur))
        step = np.linalg.norm(points[j] - cur)
        for k in tree.query_ball_point(cur, step + 1e-9):
            visited[k] = True
        d += step
        cur = points[j]
        out.append((d, cur, tags[j]))
        first = False
    return out


def resample(path, spacing, limit):
    """Path points at d = 0, spacing, ... (nearest walked point)."""
    ds = np.array([p[0] for p in path])
    rows = []
    for target in np.arange(0.0, limit + 1e-9, spacing):
        if target > ds[-1] + 0.6:
            break
        i = int(np.argmin(abs(ds - target)))
        rows.append((float(target), path[i][1], path[i][2]))
    return rows


def turning(rows):
    """Cumulative in-section direction change (deg) along the walked rows."""
    angles = [0.0]
    dirs = []
    for (_, a, _), (_, b, _) in zip(rows, rows[1:]):
        v = b - a
        n = np.linalg.norm(v)
        dirs.append(v / n if n > 1e-9 else (dirs[-1] if dirs else v))
    total = 0.0
    for u, v in zip(dirs, dirs[1:]):
        total += math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(u, v))))))
        angles.append(total)
    angles.append(total)
    return angles[:len(rows)]


# ----------------------------------------------------------------------------
# obstacles

class Obstacles:
    def __init__(self, leaves, plan_items, seams, hosts):
        self.leaves = leaves                        # [(label, shape, bbox)]
        self.panels = plan_items                    # [dict with frame + outline pts]
        self.seams = seams                          # [(name, x0, x1)]
        self.hosts = hosts

    def leaf_clearance(self, p, reach=BAND + 10.0):
        best = (math.inf, None)
        for label, shape, (lo, hi) in self.leaves:
            gap = np.maximum(np.maximum(lo - p, p - hi), 0.0)
            lower = float(np.linalg.norm(gap))
            if lower >= min(best[0], reach):
                continue
            dist = shape.distance_to(bd.Vector(*p))
            if dist < best[0]:
                best = (dist, label)
        return best

    def panel_clearance(self, p, reach=BAND + 10.0):
        best = (math.inf, None)
        for panel in self.panels:
            if abs(p[0] - panel["x"]) > panel["reach"] + reach:
                continue
            if panel["contains"](p):
                return (0.0, f"panel {panel['id']} (inside outline)")
            d = float(panel["tree"].query(p)[0]) - GROOVE_HALF
            if d < best[0]:
                best = (d, f"panel {panel['id']} ({panel['kind']}, clock {panel['clock']:g})")
        return best

    def seam_clearance(self, x):
        best = (math.inf, None)
        for name, x0, x1 in self.seams:
            d = 0.0 if x0 <= x <= x1 else min(abs(x - x0), abs(x - x1))
            if d < best[0]:
                best = (d, name)
        return best

    def clearance(self, p):
        rows = [self.leaf_clearance(p), self.panel_clearance(p)]
        dist, label = min(rows, key=lambda r: r[0])
        sd, sname = self.seam_clearance(p[0])
        return {"detail": (dist, label), "seam": (sd, sname)}


def panel_obstacle(item, host):
    clock, x0, t0 = item["clock"], item["x"], item["tangent"]
    length, width, kind = item["length"], item["width"], item["kind"]
    radial, tangent = frame(clock)
    outline = []
    if kind == "round":
        r = length / 2.0
        outline = [(r * math.cos(a), r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 64, endpoint=False)]
    else:
        hl, hw = length / 2.0, width / 2.0
        for s in np.linspace(-1, 1, max(8, int(length))):
            outline += [(s * hl, -hw), (s * hl, hw)]
        for s in np.linspace(-1, 1, max(4, int(width))):
            outline += [(-hl, s * hw), (hl, s * hw)]
    pts = []
    for dx, dt in outline:
        try:
            pts.append(np.array(tuple(skin_point(host, x0 + dx, t0 + dt, clock)["point"])))
        except ValueError:
            continue
    centre = np.array(tuple(skin_point(host, x0, t0, clock)["point"]))
    r_skin = float(np.dot(centre, radial))

    def contains(p, radial=radial, tangent=tangent):
        dx, dt = p[0] - x0, float(np.dot(p, tangent)) - t0
        if abs(float(np.dot(p, radial)) - r_skin) > 6.0:
            return False
        if kind == "round":
            return math.hypot(dx, dt) < length / 2.0
        return abs(dx) < length / 2.0 and abs(dt) < width / 2.0

    return {"id": item["id"], "kind": kind, "clock": clock, "x": x0,
            "reach": max(length, width) / 2.0 + 2.0, "tree": cKDTree(np.array(pts)),
            "contains": contains}


# ----------------------------------------------------------------------------
# per-fin measurement

def fin_clock(shape):
    c = shape.bounding_box().center()
    return round(math.degrees(math.atan2(c.Y, c.Z)) % 360.0, 3)


def near_faces(shape, lo, hi, pad):
    out = []
    for i, f in enumerate(shape.faces()):
        b = f.bounding_box()
        if (b.max.X < lo[0] - pad or b.min.X > hi[0] + pad or b.max.Y < lo[1] - pad or
                b.min.Y > hi[1] + pad or b.max.Z < lo[2] - pad or b.min.Z > hi[2] + pad):
            continue
        out.append((i, f, (b.min.X, b.max.X)))
    return out


def gather(faces, x, tag):
    pts, tags = [], []
    for i, f, (x0, x1) in faces:
        if not (x0 - 1e-6 <= x <= x1 + 1e-6):
            continue
        p = section_points(f, x)
        if len(p):
            pts.append(p)
            tags += [(tag, i, str(f.geom_type).split(".")[-1])] * len(p)
    return (np.vstack(pts) if pts else np.zeros((0, 3))), tags


def measure_station(x, kind, clock, blade_faces, skin_sets, base_faces, host_faces_for_hull):
    """Returns per-side walks and the root thickness at station x, or None."""
    radial, tangent = frame(clock)
    if kind == "main":
        fin_pts, _ = gather(blade_faces, x, "fin")
        skin_pts, skin_tags = gather(skin_sets[0], x, "host")
        if len(fin_pts) < 3 or not len(skin_pts):
            return None
        to2 = lambda P: np.c_[P @ tangent, P @ radial]
        hull = hull2(to2(fin_pts))
        inside = inside_hull(hull, to2(skin_pts))
        if not inside.any():
            return None
        under = skin_pts[inside]
        t_under = under @ tangent
        roots = {+1: under[int(np.argmax(t_under))], -1: under[int(np.argmin(t_under))]}
        keep = ~inside
        avail, avail_tags = skin_pts[keep], [t for t, k in zip(skin_tags, keep) if k]
    else:
        blade, _ = gather(blade_faces, x, "blade")
        if len(blade) < 2:
            return None
        roots = {}
        for s in (+1, -1):
            side = blade[(blade @ tangent) * s > 0]
            if not len(side):
                return None
            roots[s] = side[int(np.argmin(side @ radial))]
        fair_pts, fair_tags = gather(skin_sets[0], x, "fairing")
        body_pts, body_tags = gather(skin_sets[1], x, "booster_body")
        base_pts, _ = gather(base_faces, x, "base")
        if len(base_pts) and len(body_pts):
            d, _ = cKDTree(base_pts).query(body_pts)
            keep = d > 0.15
            # also drop body points under the fairing footprint (between base points)
            body_pts = body_pts[keep]
            body_tags = [t for t, k in zip(body_tags, keep) if k]
        parts = [p for p in (fair_pts, body_pts) if len(p)]
        avail = np.vstack(parts) if parts else np.zeros((0, 3))
        avail_tags = fair_tags + body_tags
    thickness = float(np.linalg.norm(roots[+1] - roots[-1]))
    walks = {}
    for s in (+1, -1):
        root = roots[s]
        d0 = float(cKDTree(avail).query(root)[0]) if len(avail) else math.inf
        path = walk(avail, avail_tags, root, tangent * s, BAND + 1.0) if d0 < 1.0 else [(0.0, root, None)]
        walks[s] = {"root": root, "gap_to_skin": d0, "rows": resample(path, WALK_STEP, BAND)}
    return {"x": x, "thickness": thickness, "walks": walks,
            "mid_offset": float(((roots[+1] + roots[-1]) / 2.0) @ tangent)}


def side_summary(stations, side, obstacles, kind):
    """Skin type, free area, nearest details and seat/collar fit on one side."""
    geom_types, sources, flat_extents, turn30, gaps = {}, {}, [], [], []
    free_area, band_area, walk_short = 0.0, 0.0, []
    nearest = (math.inf, None)
    seam_root = (math.inf, None)
    clear_at = {}   # x -> list of (d, detail clearance, seam clearance)
    for st in stations:
        w = st["walks"][side]
        rows = w["rows"]
        gaps.append(w["gap_to_skin"])
        if rows[-1][0] < BAND - 0.6:
            walk_short.append([st["x"], rows[-1][0]])
        ang = turning(rows)
        flat = next((r[0] for r, a in zip(rows, ang) if a > 2.0), rows[-1][0])
        flat_extents.append(flat)
        turn30.append(ang[-1])
        cl = []
        for (d, p, tag), a in zip(rows, ang):
            if tag:
                geom_types[tag[2]] = geom_types.get(tag[2], 0) + 1
                sources[tag[0]] = sources.get(tag[0], 0) + 1
            c = obstacles.clearance(p)
            cl.append((d, c["detail"][0], c["seam"][0], c["detail"][1], c["seam"][1]))
            if c["detail"][0] < nearest[0]:
                nearest = (c["detail"][0], c["detail"][1], st["x"], d)
            band_area += STATION_STEP * WALK_STEP
            if c["detail"][0] >= CLEARANCE and c["seam"][0] >= CLEARANCE:
                free_area += STATION_STEP * WALK_STEP
        sc = obstacles.seam_clearance(st["x"])
        if sc[0] < seam_root[0]:
            seam_root = sc
        clear_at[st["x"]] = cl

    xs = sorted(clear_at)
    result = {
        "skin_face_types_hit": geom_types,
        "skin_sources_hit": sources,
        "flat_extent_from_root_mm": {"min": min(flat_extents), "max": max(flat_extents),
                                     "note": "arc length from root edge before the in-section direction turns > 2 deg"},
        "in_section_turn_over_30mm_deg": {"min": min(turn30), "max": max(turn30)},
        "root_point_to_skin_gap_mm_max": max(gaps),
        "walk_shorter_than_band": walk_short[:10],
        "band_area_mm2": round(band_area, 1),
        "free_area_mm2": round(free_area, 1),
        "nearest_detail": {"clearance_mm": round(nearest[0], 3), "label": nearest[1],
                           "at_x_mm": nearest[2], "at_arc_from_root_mm": nearest[3]},
        "root_station_nearest_seam": {"axial_clearance_mm": round(seam_root[0], 3),
                                      "seam": seam_root[1]},
    }

    def window_fit(x_lo, x_hi, d_lo, d_hi):
        dets, seams = [], []
        for x in xs:
            if x_lo <= x <= x_hi:
                for d, cd, cs, lab, sname in clear_at[x]:
                    if d_lo <= d <= d_hi:
                        dets.append((cd, lab))
                        seams.append((cs, sname))
        # seam clearance is axial: use window ends against seams exactly
        s_lo, s_hi = obstacles.seam_clearance(x_lo), obstacles.seam_clearance(x_hi)
        seam_min = min(s_lo, s_hi, key=lambda r: r[0])
        for name, a, b in obstacles.seams:
            if x_lo <= a <= x_hi or x_lo <= b <= x_hi:
                seam_min = (0.0, name)
        det_min = min(dets, key=lambda r: r[0]) if dets else (math.inf, None)
        return det_min, seam_min

    if kind == "main":
        windows = []
        x0, x1 = xs[0], xs[-1]
        c = x0 + SEAT_LEN / 2.0
        while c <= x1 - SEAT_LEN / 2.0 + 1e-9:
            det, seam = window_fit(c - SEAT_LEN / 2.0, c + SEAT_LEN / 2.0,
                                   SEAT_LAND, SEAT_LAND + SEAT_W)
            # seat must lie on skin beside the root on every station of the window
            ok_skin = all(clear_at[x][-1][0] >= SEAT_LAND + SEAT_W - 0.6
                          for x in xs if c - SEAT_LEN / 2.0 <= x <= c + SEAT_LEN / 2.0)
            fits = det[0] >= CLEARANCE and seam[0] >= CLEARANCE and ok_skin
            windows.append((c, fits, det, seam))
            c += STATION_STEP
        runs, cur = [], None
        for c, fits, _, _ in windows:
            if fits and cur is None:
                cur = [c, c]
            elif fits:
                cur[1] = c
            elif cur:
                runs.append(cur)
                cur = None
        if cur:
            runs.append(cur)
        worst = min(windows, key=lambda w: w[2][0])
        result["seat_20x8"] = {
            "seat_definition": f"{SEAT_LEN} mm axial x {SEAT_W} mm across the skin, inner edge {SEAT_LAND} mm from the root edge",
            "fits_anywhere": bool(runs),
            "fit_windows_centre_x_mm": [[round(a, 1), round(b, 1)] for a, b in runs],
            "fraction_of_chord_centres_that_fit": round(sum(w[1] for w in windows) / len(windows), 3),
            "worst_window": {"centre_x_mm": round(worst[0], 1), "detail_clearance_mm": round(worst[2][0], 3),
                             "detail": worst[2][1], "seam_clearance_mm": round(worst[3][0], 3),
                             "seam": worst[3][1]},
            "min_detail_clearance_over_fitting_windows_mm": round(min((w[2][0] for w in windows if w[1]), default=math.nan), 3),
        }
    else:
        det, seam = window_fit(xs[0], xs[-1], 0.0, COLLAR_W)
        det_zone, _ = window_fit(xs[0], xs[-1], 0.0, COLLAR_W + CLEARANCE)
        # fairing flank width (arc on the fairing before the walk leaves it)
        widths = []
        for st in stations:
            rows = st["walks"][side]["rows"]
            on = [r[0] for r in rows if r[2] and r[2][0] == "fairing"]
            widths.append((st["x"], max(on) if on else 0.0))
        on_fair = [w for x, w in widths if w > 0]
        result["collar_band_3mm"] = {
            "band_definition": f"{COLLAR_W} mm band on the adjacent skin starting at the root edge, full root length",
            "min_detail_clearance_band_mm": round(det[0], 3), "nearest_detail_to_band": det[1],
            "min_detail_clearance_band_plus_2mm_zone_mm": round(det_zone[0], 3),
            "seam_axial_clearance_mm": round(seam[0], 3), "seam": seam[1],
            "fits": bool(det[0] >= CLEARANCE and seam[0] >= CLEARANCE),
            "fairing_arc_beside_root_mm": {
                "stations_on_fairing": len(on_fair),
                "stations_on_body_only": len(widths) - len(on_fair),
                "min": round(min(on_fair), 2) if on_fair else None,
                "max": round(max(on_fair), 2) if on_fair else None,
                "x_range_on_fairing": [min(x for x, w in widths if w > 0), max(x for x, w in widths if w > 0)] if on_fair else None,
            },
        }
    return result


def measure_fin(label, kind, parts, obstacles):
    fin = parts[label]
    clock = fin_clock(fin)
    radial, tangent = frame(clock)
    b = fin.bounding_box()
    lo, hi = (b.min.X, b.min.Y, b.min.Z), (b.max.X, b.max.Y, b.max.Z)
    if kind == "main":
        host = parts[MAIN_HOST]
        blade_faces = [(i, f, (f.bounding_box().min.X, f.bounding_box().max.X)) for i, f in enumerate(fin.faces())]
        skin_sets = [near_faces(host, lo, hi, BAND + 15.0)]
        base_faces = []
        outside = fin - host
        foot = [f for f in outside.faces()
                if np.dot(np.array(tuple(f.normal_at(f.center()))), radial) < -0.5]
        foot = max(foot, key=lambda f: f.area)
        fb = foot.bounding_box()
        x_range = (fb.min.X, fb.max.X)
        footprint = {"face_geom_type": str(foot.geom_type).split(".")[-1],
                     "area_mm2": round(foot.area, 2),
                     "x_range_mm": [round(fb.min.X, 3), round(fb.max.X, 3)],
                     "embedded_volume_mm3": round(fin.volume - outside.volume, 2),
                     "source": "face of (fin - host) lying on the host skin"}
    else:
        body = parts[BOOSTER_HOST]
        blade_ids, base_ids, fair_ids = [], [], []
        for i, f in enumerate(fin.faces()):
            fbb = f.bounding_box()
            n = np.array(tuple(f.normal_at(f.center())))
            reach = max(abs(fbb.max.Y), abs(fbb.min.Y)) * 0 + float(
                np.dot(np.array((0.0, fbb.center().Y, fbb.center().Z)), radial))
            r_top = max(float(np.dot(np.array((0.0, y, z)), radial))
                        for y in (fbb.min.Y, fbb.max.Y) for z in (fbb.min.Z, fbb.max.Z))
            if str(f.geom_type).endswith("CYLINDER") and np.dot(n, radial) < -0.5:
                base_ids.append(i)
            elif abs(fbb.max.X - fbb.min.X) < 1e-6:
                continue                       # end caps (stage-split face, tiny steps)
            elif abs(np.dot(n, tangent)) > 0.98 and r_top > 175.0:
                blade_ids.append(i)
            elif np.dot(n, radial) > 0.98 and f.area < 400.0:
                blade_ids.append(i)            # blade tip
            else:
                fair_ids.append(i)
        faces = fin.faces()
        fx = lambda i: (faces[i].bounding_box().min.X, faces[i].bounding_box().max.X)
        blade_faces = [(i, faces[i], fx(i)) for i in blade_ids]
        skin_sets = [[(i, faces[i], fx(i)) for i in fair_ids], near_faces(body, lo, hi, BAND + 15.0)]
        base_faces = [(i, faces[i], fx(i)) for i in base_ids]
        bx = [fx(i) for i in blade_ids]
        x_range = (min(a for a, _ in bx), max(b2 for _, b2 in bx))
        footprint = {"blade_face_ids": blade_ids, "fairing_face_ids": fair_ids, "base_face_ids": base_ids,
                     "x_range_mm": [round(x_range[0], 3), round(x_range[1], 3)],
                     "source": "blade faces (|n.tangent| > 0.98, reach > 175 mm radius) of the fin+fairing leaf"}

    stations = []
    x = x_range[0] + 0.5
    while x <= x_range[1] - 0.5 + 1e-9:
        st = measure_station(x, kind, clock, blade_faces, skin_sets, base_faces, None)
        if st:
            stations.append(st)
        x += STATION_STEP
    if not stations:
        raise ValueError((label, "no root stations measured"))
    th = [s["thickness"] for s in stations]
    imax = int(np.argmax(th))
    entry = {
        "leaf": label, "stage": "main" if kind == "main" else "booster", "clock_deg": clock,
        "fin_leaf_bbox_mm": [list(map(lambda v: round(v, 3), lo)), list(map(lambda v: round(v, 3), hi))],
        "root_footprint": dict(footprint, **{
            "measured_station_x_mm": [round(stations[0]["x"], 2), round(stations[-1]["x"], 2)],
            "root_chord_mm": round(x_range[1] - x_range[0], 3),
            "thickness_at_root_mm": {"max": round(th[imax], 3), "at_x_mm": round(stations[imax]["x"], 2),
                                     "min_measured": round(min(th), 3),
                                     "profile_every_10mm": [[round(s["x"], 1), round(s["thickness"], 3)]
                                                            for s in stations[::5]]},
            "blade_mid_plane_offset_mm": {"min": round(min(s["mid_offset"] for s in stations), 3),
                                          "max": round(max(s["mid_offset"] for s in stations), 3)},
            "root_outline_samples": {
                side: [[round(v, 3) for v in s["walks"][sgn]["root"]] for s in stations[::10]]
                for side, sgn in (("plus_tangent", +1), ("minus_tangent", -1))},
            "root_end_seam_clearance_mm": {
                "aft": dict(zip(("axial_clearance_mm", "seam"), obstacles.seam_clearance(x_range[0]))),
                "fwd": dict(zip(("axial_clearance_mm", "seam"), obstacles.seam_clearance(x_range[1]))),
            },
        }),
        "sides": {},
    }
    for side, sgn in (("plus_tangent", +1), ("minus_tangent", -1)):
        entry["sides"][side] = side_summary(stations, sgn, obstacles, kind)
    # surface type label
    types = set()
    for s in entry["sides"].values():
        if kind == "booster" and s["skin_sources_hit"].get("fairing"):
            types.add("fairing")
        turn = s["in_section_turn_over_30mm_deg"]["max"]
        flat_min = s["flat_extent_from_root_mm"]["min"]
        types.add("flat" if flat_min >= BAND - 1.0 else "curved" if turn > 2.0 else "flat")
    entry["adjacent_skin_within_30mm"] = sorted(types)
    return entry


def main():
    scene = read_scene(STEP_PATH)
    rows = tuple(scene.leaves())
    parts = {r.label: scene.resolve(r.ref).shape() for r in rows}
    if len(parts) != len(rows):
        raise ValueError("duplicate leaf labels in R19 STEP")
    meta = json.loads(META.read_text(encoding="utf-8"))
    main_fins = sorted(l for l in parts if l.startswith("main_fin_"))
    booster_fins = sorted(l for l in parts if l.startswith("booster_fin_fairing_"))
    if len(main_fins) != 4 or len(booster_fins) != 4:
        raise ValueError(("unexpected fin count", main_fins, booster_fins))
    r17 = [l for l in parts if "r17" in l.lower()]
    skip = {MAIN_HOST, BOOSTER_HOST, "main_ogive"}

    def leaf_list(exclude):
        out = []
        for l, s in parts.items():
            if l in skip or l == exclude:
                continue
            bb = s.bounding_box()
            out.append((l, s, (np.array((bb.min.X, bb.min.Y, bb.min.Z)),
                               np.array((bb.max.X, bb.max.Y, bb.max.Z)))))
        return out

    seams = [(f"seam_{k}", v["x_mm"][0], v["x_mm"][1]) for k, v in meta["seams"].items()]
    seams.append(("stage_split", STAGE_SPLIT_X, STAGE_SPLIT_X))
    hosts = {"main": parts[MAIN_HOST], "booster": parts[BOOSTER_HOST]}
    near_fins = [p for p in meta["plan"] if p["kind"] in ("rect", "round", "louvre")
                 and (p["x"] < -760.0 or p["stage"] == "booster")]
    panels = [panel_obstacle(p, hosts[p["stage"]]) for p in near_fins]

    fins = []
    for label in main_fins:
        obs = Obstacles(leaf_list(label), panels, seams, hosts)
        fins.append(measure_fin(label, "main", parts, obs))
        print("measured", label, flush=True)
    for label in booster_fins:
        obs = Obstacles(leaf_list(label), panels, seams, hosts)
        fins.append(measure_fin(label, "booster", parts, obs))
        print("measured", label, flush=True)

    report = {
        "source_step": "STEP/halberd_r19_surface.step",
        "source_document_hash": scene.document_hash,
        "metadata": "reviews/halberd_r19_surface.json",
        "units": "mm, degrees; +X noseward; clock 0 = +Z, 90 = +Y",
        "method": __doc__.strip().splitlines()[3:16],
        "thresholds": {"clearance_mm": CLEARANCE, "band_mm": BAND, "station_step_mm": STATION_STEP,
                       "walk_spacing_mm": WALK_STEP, "main_seat_mm": [SEAT_LEN, SEAT_W],
                       "main_seat_land_from_root_mm": SEAT_LAND, "booster_collar_width_mm": COLLAR_W},
        "existing_details_considered": {
            "leaves": len(parts) - len(skip) - 1,
            "panel_outlines_from_plan": [p["id"] for p in near_fins],
            "seams_and_split": [[n, a, b] for n, a, b in seams],
            "r17_root_hardware_leaves_in_r19_step": r17,
            "r17_note": ("No R17 fin-root strip/heads exist in the R19 STEP; they live only in the "
                         "R17 local review coupons (src/halberd_r17_interface_shapes.py: 52 x 9 mm "
                         "0.8 mm-pocket inset strip with 4 slotted heads on the main_fin_1 / "
                         "booster_fin_fairing_1 blade face)."),
        },
        "fins": fins,
        "limitations": [
            "Free area is a sampled estimate: stations every 2 mm in X, 0.5 mm arc steps across the skin.",
            "Engraved panels are not separate leaves; their outlines come from the metadata plan and are re-projected onto the saved skin.",
            "Clearance to leaves is exact B-rep point distance at sample points; between samples it can be up to ~1 mm smaller.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2, default=float) + "\n", encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
