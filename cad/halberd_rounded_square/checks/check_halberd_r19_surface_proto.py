"""Independent saved-artifact check for the R19 forward surface prototype.

Reads the saved STEP and sidecar only (plus the saved R18 access STEP as the
reference); does not import the prototype builder.
"""
import json
import math
import sys
from itertools import combinations
from pathlib import Path

from cadgen import build123d as bd, read_scene

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / "STEP" / "halberd_r19_surface_proto_forward.step"
R18 = ROOT / "STEP" / "halberd_r18_access.step"
META = ROOT / "reviews" / "halberd_r19_surface_proto.json"
REPORT = ROOT / "reviews" / "halberd_r19_surface_proto_checks.json"
HOST = "main_body_intake_r12_r19_proto"
CROP_X = (690.0, 1100.0)
TOL = 1e-4

failures = []


def fail(message):
    failures.append(message)


def parts_of(path):
    scene = read_scene(path)
    leaves = tuple(scene.leaves())
    parts = {leaf.label: scene.resolve(leaf.ref).shape() for leaf in leaves}
    if len(parts) != len(leaves):
        fail(f"{path.name}: duplicate labels")
    return scene, parts


def clock_of(shape):
    c = shape.center()
    return math.degrees(math.atan2(c.Y, c.Z)) % 360.0


def overlap(a, b):
    ba, bb = a.bounding_box(), b.bounding_box()
    if (ba.min.X > bb.max.X or bb.min.X > ba.max.X or ba.min.Y > bb.max.Y or
            bb.min.Y > ba.max.Y or ba.min.Z > bb.max.Z or bb.min.Z > ba.max.Z):
        return 0.0
    i = a & b
    return i.volume if i else 0.0


def skin_radius(shape, base, radial, start=260.0):
    """Radius of the outermost skin crossing along +radial from base (ray hit)."""
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
    # Independent sanity: just below is material, just above is not.
    if not shape.is_inside(base + radial * (radius - 0.05)) or             shape.is_inside(base + radial * (radius + 0.05)):
        raise ValueError("reference skin ray hit is not the outer skin")
    return radius


scene, proto = parts_of(PROTO)
_, r18 = parts_of(R18)
meta = json.loads(META.read_text(encoding="utf-8"))

# 1. Validity and composition.
for label, part in proto.items():
    if not part.is_valid or len(part.solids()) != 1 or part.volume <= 1e-8:
        fail(f"{label}: invalid, empty or not one solid")
if HOST not in proto:
    fail("host crop missing")
host = proto[HOST]

# 2. Retained R18 parts are unchanged (fully inside crop -> identical volume/bounds).
retained = [l for l in proto if not l.startswith("main_r19_") and l != HOST]
for label in retained:
    if label not in r18:
        fail(f"{label}: not present in saved R18 access")
        continue
    ref = r18[label]
    rb = ref.bounding_box()
    if rb.min.X >= CROP_X[0] and rb.max.X <= CROP_X[1]:
        if abs(ref.volume - proto[label].volume) > 1e-6:
            fail(f"{label}: retained part volume changed")

# 3. Host = R18 host crop minus cuts only (no gain), removal matches metadata.
clip = bd.Box(CROP_X[1] - CROP_X[0], 400, 400).translate((sum(CROP_X) / 2, 0, 0))
ref_host = r18["main_body_intake_r12"] & clip
gain = host - ref_host
if gain and gain.volume > 1e-4:
    fail(f"host gained material: {gain.volume:.5f} mm3")
removed = ref_host.volume - host.volume
if abs(removed - meta["host_volume_removed_mm3"]) > 1e-3:
    fail(f"host removal {removed:.4f} != metadata {meta['host_volume_removed_mm3']:.4f}")

# 4. Radial joint ring: 24 heads at 15 deg pitch, same axial band and radius.
ring = {l: p for l, p in proto.items()
        if l.startswith("main_joint_fastener_") or l.startswith("main_r19_joint_ring_")}
clocks = sorted(clock_of(p) for p in ring.values())
if len(ring) != 24:
    fail(f"joint ring has {len(ring)} heads, expected 24")
for i, c in enumerate(clocks):
    if abs(c - 15.0 * i) > 0.05:
        fail(f"joint ring clock {c:.3f} not on 15 deg pitch (index {i})")
ref_head = proto["main_joint_fastener_1"]
for label, head in ring.items():
    if abs(head.volume - ref_head.volume) > 1e-6:
        fail(f"{label}: head differs from accepted R16 head")
    hb = head.bounding_box()
    if abs(hb.min.X - ref_head.bounding_box().min.X) > 1e-4:
        fail(f"{label}: not in the R16 axial band")

# 5. No detail/host or detail/detail overlap.
details = [l for l in proto if l != HOST]
for label in details:
    v = overlap(proto[label], host)
    if v > TOL and not label.startswith("main_ogive"):
        fail(f"overlap {label}/host: {v:.4f} mm3")
for a, b in combinations([l for l in details if "fastener" in l or "r19" in l], 2):
    v = overlap(proto[a], proto[b])
    if v > TOL:
        fail(f"overlap {a}/{b}: {v:.4f} mm3")

# 6. Grooves exist: probe each panel outline edge midpoint just under the skin.
for pid, data in meta["panels"].items():
    clock = math.radians(data["clock_degrees"])
    radial = bd.Vector(0, math.sin(clock), math.cos(clock))
    tangent = bd.Vector(0, math.cos(clock), -math.sin(clock))
    x0, half_w = data["center_x_mm"], data["width_mm"] / 2.0
    for side in (-1, 1):
        # outer radius at the edge from the unmodified R18 host
        base = bd.Vector(x0, 0, 0) + tangent * (side * (half_w - 0.2))
        lo = skin_radius(ref_host, base, radial)
        skin = base + radial * lo
        if host.is_inside(skin - radial * 0.2):
            fail(f"{pid}: groove missing at edge side {side}")
        if not host.is_inside(skin - radial * 0.6):
            fail(f"{pid}: groove deeper than 0.4 mm at edge side {side}")
        # Interior skin must survive; probe the centre, or the nearest interior
        # point clear of every screw seat (C03 has a centre screw).
        screws = [(s["offset_x_mm"], s["offset_tangent_mm"]) for s in data["screw_sites"]]
        candidates = [(0.0, 0.0), (0.0, half_w / 2.0), (0.0, -half_w / 2.0),
                      (data["length_mm"] / 4.0, 0.0), (-data["length_mm"] / 4.0, 0.0)]
        dx, dt = next(c for c in candidates
                      if all(math.hypot(c[0] - sx, c[1] - st) > 2.5 for sx, st in screws))
        interior = bd.Vector(x0 + dx, 0, 0) + tangent * dt
        if not host.is_inside(interior + radial * (lo - 0.2)):
            fail(f"{pid}: interior panel skin was removed at ({dx}, {dt})")
    for site in data["screw_sites"]:
        if site["remaining_wall_after_seat_mm"] <= 0.25:
            fail(f"{pid}: fastener backing too thin")

# 6b. Circumferential joint seam groove: open just under the skin, closed below.
seam = meta["joint_seam_groove"]
seam_x = sum(seam["x_mm"]) / 2.0
for clock_deg in range(0, 360, 30):
    a = math.radians(clock_deg)
    radial = bd.Vector(0, math.sin(a), math.cos(a))
    base = bd.Vector(seam_x, 0, 0)
    lo = skin_radius(ref_host, base, radial)
    if host.is_inside(base + radial * (lo - 0.2)):
        fail(f"joint seam groove missing at clock {clock_deg}")
    if not host.is_inside(base + radial * (lo - seam["depth_mm"] - 0.1)):
        fail(f"joint seam groove too deep at clock {clock_deg}")

# 7. Sidecar covers every detail label.
sidecar = json.loads(PROTO.with_suffix(".step.json").read_text(encoding="utf-8"))
assigned = set(sidecar["appearance"]["assignments"])
leaf_refs = {leaf.label: leaf.ref.split("#")[-1] for leaf in scene.leaves()}
for label, ref in leaf_refs.items():
    if (label.startswith("main_r19_") or "fastener" in label) and ref not in assigned:
        fail(f"{label}: no material assignment in sidecar")

report = {
    "status": "PASS" if not failures else "FAIL",
    "failures": failures,
    "document_hash": scene.document_hash,
    "parts": len(proto),
    "ring_heads": len(ring),
    "panels": len(meta["panels"]),
    "panel_fasteners": sum(len(d["screw_sites"]) for d in meta["panels"].values()),
    "host_volume_removed_mm3": removed,
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
sys.exit(0 if not failures else 1)
