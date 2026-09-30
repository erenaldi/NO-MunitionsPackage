"""Independent saved-artifact check for the R19 full-body surface detailing.

Reads the saved R19 STEP + sidecar and metadata, and the saved R18 access STEP
as the reference. Does not import the R19 builders.
"""
import json
import math
import sys
from pathlib import Path

from cadgen import build123d as bd, read_scene

ROOT = Path(__file__).resolve().parents[1]
R19 = ROOT / "STEP" / "halberd_r19_surface.step"
R18 = ROOT / "STEP" / "halberd_r18_access.step"
META = ROOT / "reviews" / "halberd_r19_surface.json"
REPORT = ROOT / "reviews" / "halberd_r19_surface_checks.json"
HOSTS = ("main_body_intake_r12", "booster_body")
GROUP = "r19_surface_hardware"
CLEARANCE = 2.0
TOL = 1e-4
failures = []


def fail(message):
    failures.append(message)


def leaves(path):
    scene = read_scene(path)
    rows = tuple(scene.leaves())
    parts = {row.label: scene.resolve(row.ref).shape() for row in rows}
    if len(parts) != len(rows):
        fail(f"{path.name}: duplicate leaf labels")
    return scene, rows, parts


def frame(clock):
    a = math.radians(clock)
    return bd.Vector(0, math.sin(a), math.cos(a)), bd.Vector(0, math.cos(a), -math.sin(a))


def skin_radius(shape, base, radial, start=260.0):
    """Outermost skin crossing along +radial from base (independent ray hit)."""
    from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter
    from OCP.gce import gce_MakeLin

    origin = base + radial * start
    hits = BRepIntCurveSurface_Inter()
    hits.Init(shape.wrapped, gce_MakeLin(bd.Axis(origin, -radial).wrapped).Value(), 1e-7)
    ws = []
    while hits.More():
        if hits.W() >= 0.0:
            ws.append(hits.W())
        hits.Next()
    if not ws:
        raise ValueError("reference skin ray missed")
    radius = start - min(ws)
    if not shape.is_inside(base + radial * (radius - 0.05)) or \
            shape.is_inside(base + radial * (radius + 0.05)):
        raise ValueError("reference skin ray hit is not the outer skin")
    return radius


def boxes_near(a, b, margin):
    ba, bb = a.bounding_box(), b.bounding_box()
    return not (ba.min.X - margin > bb.max.X or bb.min.X - margin > ba.max.X or
                ba.min.Y - margin > bb.max.Y or bb.min.Y - margin > ba.max.Y or
                ba.min.Z - margin > bb.max.Z or bb.min.Z - margin > ba.max.Z)


scene, rows, parts = leaves(R19)
_, _, ref = leaves(R18)
meta = json.loads(META.read_text(encoding="utf-8"))

# 1. Validity.
for label, part in parts.items():
    if not part.is_valid or len(part.solids()) != 1 or part.volume <= 1e-8:
        fail(f"{label}: invalid, empty or not one solid")

# 2. Composition: every R18 leaf present except the declared F05 replacements;
# new leaves are exactly the metadata hardware + raised parts.
replaced = set(meta.get("replaced_r18_labels", []))
if set(ref) - set(parts) != replaced:
    fail(f"R18 leaves missing beyond declared replacements: "
         f"{sorted(set(ref) - set(parts) - replaced)[:5]}; "
         f"replacements still present: {sorted(replaced & set(parts))}")
new = set(parts) - set(ref)
hardware_new = set(meta["hardware_labels"])
raised_new = set(meta.get("raised_labels", []))
if new != hardware_new | raised_new:
    fail(f"new leaves != metadata hardware+raised ({len(new)} vs "
         f"{len(hardware_new | raised_new)})")

# 3. Retained R18 parts unchanged.
for label, part in ref.items():
    if label in HOSTS or label not in parts:
        continue
    if abs(part.volume - parts[label].volume) > 1e-6 or \
            (part.center() - parts[label].center()).length > 1e-6:
        fail(f"{label}: retained R18 part changed")

# 4. Hosts: only material removed; removal matches metadata.
for host in HOSTS:
    gain = parts[host] - ref[host]
    if gain and gain.volume > 1e-3:
        fail(f"{host}: gained {gain.volume:.4f} mm3")
    removed = ref[host].volume - parts[host].volume
    # Volume integration on the 85e6 mm3 main body is only good to ~4e-9
    # relative: the in-memory and saved hosts had identical faces (2284) and an
    # empty Boolean difference both ways yet differed by 0.35 mm3 (2026-09-29).
    # Geometry defects are caught by the Boolean gain, overlap and probe checks.
    tolerance = max(5e-3, 1e-8 * ref[host].volume)
    if abs(removed - meta["host_volume_removed_mm3"][host]) > tolerance:
        fail(f"{host}: removed {removed:.4f} != metadata {meta['host_volume_removed_mm3'][host]:.4f}")

# 5. Hardware: no overlap with any part; >= clearance from R18 detail parts.
details = [p for label, p in ref.items() if label not in HOSTS and label not in replaced]
for label in sorted(new):
    head = parts[label]
    host = parts["booster_body" if label.startswith("booster") else "main_body_intake_r12"]
    if host.is_inside(head.center()):
        fail(f"{label}: centre inside host skin")
    inter = head & host
    if inter and inter.volume > TOL:
        fail(f"{label}: overlaps host by {inter.volume:.4f} mm3")
    for other in details:
        if not boxes_near(head, other, CLEARANCE):
            continue
        if other.label.startswith("main_joint_fastener_"):
            continue  # nose ring continues the R16 heads at 15 deg pitch
        if head.distance_to(other) < CLEARANCE - 1e-6:
            fail(f"{label}: within {CLEARANCE} mm of {other.label}")
for a in sorted(new):
    for b in sorted(new):
        if a < b and boxes_near(parts[a], parts[b], 0.0):
            inter = parts[a] & parts[b]
            if inter and inter.volume > TOL:
                fail(f"overlap {a}/{b}")

# 5b. Raised parts: seated on the skin (touching, no overlap) at their height.
for label in sorted(raised_new):
    part = parts[label]
    host = parts["booster_body" if label.startswith("booster") else "main_body_intake_r12"]
    if part.distance_to(host) > 0.01:
        fail(f"{label}: not seated on the host skin")
for pid, d in meta.get("raised", {}).items():
    label = next((l for l in raised_new if f"_r19_{pid}_" in l), None)
    if label is None:
        fail(f"raised {pid}: part missing")
        continue
    host_label = "booster_body" if d["stage"] == "booster" else "main_body_intake_r12"
    radial, tangent = frame(d["clock_degrees"])
    base = bd.Vector(d["center_x_mm"], 0, 0) + tangent * d["tangent_offset_mm"]
    r0 = skin_radius(ref[host_label], base, radial)
    top = max((bd.Vector(v) - base).dot(radial) for v in parts[label].vertices())
    if abs(top - r0 - d["height_mm"]) > 0.02:
        fail(f"raised {pid}: height {top - r0:.3f} != {d['height_mm']}")
f05 = meta.get("f05")
if f05:
    for label in sorted(l for l in raised_new if "_F05_" in l or "_F05M_" in l):
        box = parts[label].bounding_box()
        height = f05["terminal_height_mm"] if "terminal" in label else f05["strip_height_mm"]
        top = -box.min.Z - 100.0 if "_F05_" in label else box.max.Z - 100.0
        if abs(top - height) > 0.02:
            fail(f"{label}: height {top:.3f} != {height}")
        if "_F05M_" in label:
            twin = parts.get(label.replace("_F05M_", "_F05_"))
            if twin is None or abs(twin.volume - parts[label].volume) > 1e-4 or                     abs(twin.bounding_box().min.Z + box.max.Z) > 1e-4:
                fail(f"{label}: not the XY mirror of its underside twin")

# 6. Rings: counts and axial band.
for ring_id, info in meta["rings"].items():
    prefix = "main_r19_joint_ring_fastener_" if ring_id == "nose" else f"_r19_{ring_id}_"
    heads = [l for l in new if prefix in l]
    if ring_id == "nose":
        heads += [l for l in parts if l.startswith("main_joint_fastener_")]
    if len(heads) != info["heads"]:
        fail(f"ring {ring_id}: {len(heads)} heads != metadata {info['heads']}")
    xs = [parts[l].center().X for l in heads]
    if xs and max(xs) - min(xs) > 1.0:
        fail(f"ring {ring_id}: heads not in one axial band ({min(xs):.2f}..{max(xs):.2f})")

# 7. Panel grooves open at the outline, closed below 0.4 mm, interior intact.
for pid, d in meta["panels"].items():
    host_label = "booster_body" if d["stage"] == "booster" else "main_body_intake_r12"
    host, reference = parts[host_label], ref[host_label]
    radial, tangent = frame(d["clock_degrees"])
    x0, t0, half_w = d["center_x_mm"], d.get("tangent_offset_mm", 0.0), d["width_mm"] / 2.0
    for side in (-1, 1):
        base = bd.Vector(x0, 0, 0) + tangent * (t0 + side * (half_w - 0.2))
        r = skin_radius(reference, base, radial)
        if host.is_inside(base + radial * (r - 0.2)):
            fail(f"{pid}: groove missing at side {side}")
        if not host.is_inside(base + radial * (r - 0.6)):
            fail(f"{pid}: groove deeper than 0.4 mm at side {side}")
    screws = [(s["offset_x_mm"], s["offset_tangent_mm"] - t0) for s in d["screw_sites"]]
    # Interior probe clear of every screw seat; the last candidates sit 1 mm
    # inside the outline (inside the 0.4 mm groove) for tiny centre-screw caps.
    inner = half_w - 1.0
    candidates = [(0.0, 0.0), (0.0, half_w / 2.0), (0.0, -half_w / 2.0),
                  (d["length_mm"] / 4.0, 0.0), (-d["length_mm"] / 4.0, 0.0),
                  (0.0, inner), (0.0, -inner)]
    slots = meta.get("louvres", {}).get(pid)
    def in_slot(c):
        # Vent slots are cut on purpose; the interior probe must avoid them too.
        return bool(slots) and any(
            abs(c[0] - sdx) < slots["slot_width_mm"] / 2.0 + 0.5 and
            abs(c[1]) < slots["slot_length_mm"] / 2.0 + 0.5
            for sdx in slots["slot_x_offsets_mm"])
    clear = [c for c in candidates
             if all(math.hypot(c[0] - sx, c[1] - st) > 2.5 for sx, st in screws)
             and not in_slot(c)]
    if not clear:
        fail(f"{pid}: no interior probe point clear of screw seats")
        continue
    dx, dt = clear[0]
    base = bd.Vector(x0 + dx, 0, 0) + tangent * (t0 + dt)
    r = skin_radius(reference, base, radial)
    if not host.is_inside(base + radial * (r - 0.2)):
        fail(f"{pid}: interior skin removed at ({dx}, {dt})")

# 7b. Vent slots: open 0.3 mm under the skin, closed below their 0.6 mm depth.
for pid, v in meta.get("louvres", {}).items():
    host_label = "booster_body" if v["stage"] == "booster" else "main_body_intake_r12"
    host, reference = parts[host_label], ref[host_label]
    radial, tangent = frame(v["clock_degrees"])
    for dx in v["slot_x_offsets_mm"]:
        base = bd.Vector(v["center_x_mm"] + dx, 0, 0) + tangent * v["tangent_offset_mm"]
        r = skin_radius(reference, base, radial)
        if host.is_inside(base + radial * (r - 0.3)):
            fail(f"{pid}: slot missing at dx {dx:.1f}")
        if not host.is_inside(base + radial * (r - v["slot_depth_mm"] - 0.3)):
            fail(f"{pid}: slot deeper than {v['slot_depth_mm']} mm at dx {dx:.1f}")

# 8. Seams: open just under the skin all around, closed 0.5 mm down.
for seam_id, s in meta["seams"].items():
    host_label = "booster_body" if seam_id.startswith("RB") else "main_body_intake_r12"
    host, reference = parts[host_label], ref[host_label]
    x = sum(s["x_mm"]) / 2.0
    for clock in range(0, 360, 30):
        radial, _ = frame(clock)
        base = bd.Vector(x, 0, 0)
        r = skin_radius(reference, base, radial)
        if host.is_inside(base + radial * (r - 0.2)):
            fail(f"seam {seam_id}: missing at clock {clock}")
        if not host.is_inside(base + radial * (r - 0.5)):
            fail(f"seam {seam_id}: deeper than 0.4 mm at clock {clock}")

# 9. Sidecar: hardware is metal; R18 leaves keep their R18 materials.
side19 = json.loads(R19.with_suffix(".step.json").read_text(encoding="utf-8"))["appearance"]
side18 = json.loads(R18.with_suffix(".step.json").read_text(encoding="utf-8"))["appearance"]
by_label19 = {r.label: r.ref.split("#")[-1] for r in rows}
_, rows18, _ = leaves(R18)
by_label18 = {r.label: r.ref.split("#")[-1] for r in rows18}
for label in new:
    mat = side19["assignments"].get(by_label19[label])
    want = "Service cover paint" if label in raised_new else "Small metallic hardware"
    if not mat or side19["materials"][mat].get("name") != want:
        fail(f"{label}: not assigned {want} ({mat})")
for label, occ in by_label18.items():
    if label in replaced:
        continue
    m18 = side18["assignments"].get(occ)
    m19 = side19["assignments"].get(by_label19.get(label, ""))
    n18 = side18["materials"].get(m18, {}).get("name") if m18 else None
    n19 = side19["materials"].get(m19, {}).get("name") if m19 else None
    if n18 != n19:
        fail(f"{label}: material changed {n18} -> {n19}")

report = {
    "status": "PASS" if not failures else "FAIL",
    "failures": failures[:60],
    "failure_count": len(failures),
    "document_hash": scene.document_hash,
    "leaves": len(parts),
    "new_hardware": len(hardware_new),
    "raised_parts": len(raised_new),
    "replaced_r18": sorted(replaced),
    "panels": len(meta["panels"]),
    "rings": {k: v["heads"] for k, v in meta["rings"].items()},
    "seams": list(meta["seams"]),
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
sys.exit(0 if not failures else 1)
