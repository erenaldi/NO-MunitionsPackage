"""Equivalence test for cad/shared/{check_kit,review_crop,root_geometry}.py.

Pulls the ORIGINAL function/class source out of the committed R20 checker and R20
builder with `ast` (those files run on import, so they cannot be imported) and
compares the shared versions against them on the saved R20 model. Read-only
except for one temp crop STEP under tmp/. Prints stage times; budget 6 min.
"""
import ast
import math
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT.parent / "shared"))

from cadgen import build123d as bd  # noqa: E402
import check_kit as ck  # noqa: E402
import review_crop as rc  # noqa: E402
import root_geometry as rg  # noqa: E402
from surface_detail import clock_frame, skin_point  # noqa: E402

R20 = ROOT / "STEP" / "halberd_r20_fin_seats.step"
R20_MAIN_FOCUS = ROOT / "STEP" / "halberd_r20_fin_seats_main_focus.step"
failures = []
stages = ck.Stages(stage_budget_s=150, total_budget_s=360)


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print("FAIL", msg, flush=True)


def original_namespace(path, names, extra=None):
    """exec only the named top-level defs/classes of `path`; returns the namespace."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    keep = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
    ns = {"bd": bd, "math": math, "skin_point": skin_point, "clock_frame": clock_frame}
    ns.update(extra or {})
    exec(compile(ast.Module(body=keep, type_ignores=[]), str(path), "exec"), ns)
    return ns


stages.stage("load R20")
rep = ck.Report()
scene, rows, parts = ck.load_leaves(R20, rep)
check(not rep.failures, f"load_leaves: {rep.failures}")
check(len(parts) == len(rows) == 359, f"leaf count {len(parts)} != 359")

stages.stage("check_kit vs original checker functions")
old = original_namespace(HERE / "check_halberd_r20_fin_seats.py",
                         {"precise_volume", "closed_and_clean", "ray_skin", "boxes_near", "frame"})
for label in ("main_fin_1", "main_r20_F07_1p_cover", "main_r20_F07_1p_fastener_1"):
    a, b = old["precise_volume"](parts[label]), ck.precise_volume(parts[label])
    check(abs(a - b) < 1e-9, f"precise_volume {label}: {a} vs {b}")
for label in ("main_r20_F07_1p_cover", "main_r20_F07_1p_fastener_1"):
    check(old["closed_and_clean"](parts[label]) == ck.closed_and_clean(parts[label]),
          f"closed_and_clean {label}")
o, t = old["frame"](45.0)
n, tt = ck.frame(45.0)
check((o - n).length < 1e-12 and (t - tt).length < 1e-12, "frame mismatch")
check(old["boxes_near"](parts["main_fin_1"], parts["main_fin_2"], 2.0) ==
      ck.boxes_near(parts["main_fin_1"], parts["main_fin_2"], 2.0), "boxes_near mismatch")
# ray_skin: single shape equal to original, multi-shape nearest crossing
host = parts["main_body_intake_r12"]
outward, _ = clock_frame(100.0)
pt = bd.Vector(-900.0, 0, 0) + outward * 40.0
check((old["ray_skin"](host, pt, outward) - ck.ray_skin(host, pt, outward)).length < 1e-9,
      "ray_skin single shape mismatch")
multi = ck.ray_skin([parts["main_fin_1"], host], pt, outward)
check((multi - ck.ray_skin(host, pt, outward)).length < 1e-9 or multi.dot(outward) >= ck.ray_skin(host, pt, outward).dot(outward) - 1e-9,
      "ray_skin multi-shape should be nearest crossing")
# leaves_unchanged: identical set is clean; a changed host is reported
check(ck.leaves_unchanged(parts, parts) == [], "leaves_unchanged(parts, parts) not empty")
fake = dict(parts)
fake["main_fin_1"] = parts["main_fin_2"]
check([b[0] for b in ck.leaves_unchanged(parts, fake)] == ["main_fin_1"], "leaves_unchanged missed a change")
# crop + closed_and_clean on a crop is far cheaper than the whole body
crop = ck.crop_shape(host, ck.box_around(-995.0, -945.0))
check(crop is not None and crop.volume > 0, "crop_shape empty")
ck.closed_and_clean(crop)
try:
    s2 = ck.Stages(stage_budget_s=0.0, total_budget_s=10)
    import time
    time.sleep(0.05)
    s2.stage("x")
    check(False, "Stages did not raise over budget")
except TimeoutError:
    pass

stages.stage("review_crop vs saved R20 main crop")
clip = rc.x_window(-1130.0, -840.0)
new_crop = rc.crop_scene(R20, clip, "verify_crop")
saved_scene = ck.load_leaves(R20_MAIN_FOCUS)[2]
new_leaves = [c for c in new_crop.children]
check(len(new_leaves) == len(saved_scene), f"crop leaf count {len(new_leaves)} != {len(saved_scene)}")
vol_new = sum(c.volume for c in new_leaves)
vol_old = sum(s.volume for s in saved_scene.values())
check(abs(vol_new - vol_old) < 1e-3, f"crop volume {vol_new} vs {vol_old}")
jobs = rc.snapshot_jobs({"STEP/x.step": ("reviews/X", ["face", "grazing"])})
check(jobs[0]["outputs"][0]["path"] == "reviews/X_face.png" and len(jobs[0]["outputs"]) == 2, "snapshot_jobs shape")
check(rc.radial_point(-970.0, 138.8, 45.0)[1] > 0, "radial_point")

stages.stage("root_geometry vs R20 RootSide")
oldrg = original_namespace(ROOT / "src" / "halberd_r20_fin_seats.py",
                           {"_bisect", "RootSide"},
                           {"SEAT_X": -970.0, "INNER_HALF": 10.0})
R19 = Path(r"C:\Users\erena\Desktop\Nuclear Option Munitions Package\cad\halberd_rounded_square\STEP\halberd_r19_surface.step")
ref19 = ck.load_leaves(R19)[2]   # the original builder cut its seats from the R19 host
crop20 = ref19["main_body_intake_r12"] & bd.Box(50.0, 600.0, 600.0).translate((-970.0, 0.0, 0.0))
fin1 = ref19["main_fin_1"]
a = oldrg["RootSide"](crop20, fin1, 45.0, +1)
b = rg.RootSide(crop20, fin1, 45.0, +1, centre_x=-970.0, half_span=10.0)
for x in (-975.0, -970.0, -962.0):
    check(abs(a.edge(x) - b.edge(x)) < 1e-9, f"edge({x})")
    check(abs(a.crease_t(x) - b.crease_t(x)) < 1e-9, f"crease_t({x})")
for u, w in ((0.0, 2.25), (4.0, 6.0), (-6.0, 11.0)):
    check((a.point(u, w) - b.point(u, w)).length < 1e-9, f"point({u},{w})")
check(len(rg.blade_faces(fin1, 45.0)) >= 4, "blade_faces")
check(rg.local_crop_box(45.0, (-995.0, -945.0), (-30.0, 30.0), (90.0, 150.0)).volume > 0, "local_crop_box")
check(len(rg.densify(rg.chamfered([(0, 0), (10, 0), (10, 5), (0, 5)], 1.0), 1.0)) > 8, "densify/chamfered")

stages.done()
print("RESULT", "PASS" if not failures else f"FAIL ({len(failures)})", flush=True)
sys.exit(1 if failures else 0)
