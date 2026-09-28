"""Independent serialized STEP checks for local Spear boattail/one-fin studies."""

import json
import math
from pathlib import Path

from cadgen import build123d as bd, read_step


ROOT = Path(__file__).resolve().parents[1]
VARIANTS = {"Trim": 94., "Rake": 95., "Broad": 92.,
            "SketchSpan": 92., "SketchLow": 79.}
ORIGINAL = ROOT / "STEP" / "A_Spear.step"
OFFSET = 270.


def cut_volume(a, b):
    cut = a - b
    return 0. if cut is None else cut.volume


def same_solid(a, b, tolerance=.002):
    return cut_volume(a, b) < tolerance and cut_volume(b, a) < tolerance


def overlap(a, b):
    intersection = a & b
    return 0. if intersection is None else intersection.volume


def parts_from(path):
    shape = read_step(path)
    parts = {part.label: part for part in shape.children}
    assert len(parts) == len(shape.children) == 11, f"incorrect part set: {path}"
    assert all(p.is_valid and len(p.solids()) == 1 and p.volume > 0 for p in parts.values()), path
    return parts


def cap_radius_at(cap, x):
    slab = bd.Box(.12, 160., 160.).translate((x, 0, 0))
    slice_ = cap & slab
    assert slice_ is not None and slice_.volume > 0, f"no cap section at x={x}"
    bounds = slice_.bounding_box()
    return max(abs(bounds.min.Y), abs(bounds.max.Y))


def radial_max(part):
    vertices, _ = part.tessellate(.15)
    return max(math.hypot(v.Y, v.Z) for v in vertices)


def check(name, originals):
    target = ROOT / "STEP" / f"Spear_{name}_Boattail.step"
    separated_path = target.with_name(target.stem + "_Separated.step")
    assembled, apart = parts_from(target), parts_from(separated_path)
    expected = set(originals) - {"aft_fin_0"} | {"aft_fin_0_prototype"}
    assert set(assembled) == set(apart) == expected

    for label in ("body", "main_nozzle", "aft_fin_1", "aft_fin_2", "aft_fin_3"):
        assert same_solid(assembled[label], originals[label]), (name, label, "approved form changed")
    body, cap, nozzle = assembled["body"], assembled["turning_cap"], assembled["main_nozzle"]
    assert abs(cap.bounding_box().min.X + 600) < .002
    assert abs(cap.bounding_box().max.X + 420) < .002
    assert overlap(body, cap) < .001 and overlap(body, nozzle) < .001
    assert cap_radius_at(cap, -599.5) < 36., "boattail is not narrow at its aft face"
    assert cap_radius_at(cap, -485.) > 61., "boattail did not reach full shoulder"
    assert cap_radius_at(cap, -421.) > 60., "body-side cap seam narrowed"
    assert cap_radius_at(cap, -599.5) < cap_radius_at(cap, -550.) < cap_radius_at(cap, -485.)
    prototype = assembled["aft_fin_0_prototype"]
    assert overlap(prototype, body) > .001, f"{name} prototype fin detached"
    actual_tip = radial_max(prototype)
    assert abs(actual_tip - VARIANTS[name]) < .1, (name, actual_tip)
    assert actual_tip < radial_max(originals["aft_fin_0"])-4.
    if name.startswith("Sketch"):
        root, tip = prototype.bounding_box(), originals["aft_fin_0"].bounding_box()
        assert abs(root.min.X - tip.min.X) < .002, "drawing study moved the root aft boundary"
        assert abs(root.max.X - tip.max.X) < .002, "drawing study moved the root forward boundary"
        # Fin top edge vertices at the specified radial band: inspect actual
        # exported shape, not merely the source variant's parameter dictionary.
        radial_vertices = [(v.X, math.hypot(v.Y, v.Z))
                           for v in prototype.tessellate(.15)[0]]
        at_tip = [x for x, radial in radial_vertices if radial > VARIANTS[name]-.12]
        assert at_tip, "missing outer fin edge"
        assert abs(min(at_tip)-(-420.+28.)) < .1, "outer chord aft boundary differs from sketch"
        assert abs(max(at_tip)-(-420.+193.)) < .1, "outer chord forward boundary differs from sketch"
        assert abs((max(at_tip)-min(at_tip))/(root.max.X-root.min.X)-.825) < .002
    for degree in (0, 90, 180, 270):
        label = f"thruster_{degree}"
        assert overlap(assembled[label], cap) > .001, (name, label, "thruster detached")
        assert assembled[label].bounding_box().min.X > -500., (name, label, "thruster on taper")
    for label, old in assembled.items():
        shifted = label == "turning_cap" or label.startswith("thruster_")
        new = apart[label].translate((OFFSET, 0, 0)) if shifted else apart[label]
        assert same_solid(old, new), (name, label, "state changed geometry")
    assert overlap(apart["turning_cap"], body) < .001
    focus = read_step(ROOT / "STEP" / f"Spear_{name}_Fin_Focus.step")
    focus_parts = {part.label: part for part in focus.children}
    assert set(focus_parts) == {"body", "aft_fin_0_prototype"}
    assert same_solid(focus_parts["body"], body)
    assert same_solid(focus_parts["aft_fin_0_prototype"], prototype)
    cap_focus = read_step(ROOT / "STEP" / "Spear_Boattail_Cap_Focus.step")
    cap_parts = {part.label: part for part in cap_focus.children}
    assert set(cap_parts) == {"turning_cap", "thruster_0", "thruster_90",
                              "thruster_180", "thruster_270"}
    assert all(same_solid(cap_parts[label], assembled[label]) for label in cap_parts)
    return {"fin_tip_radius_mm": round(actual_tip, 3),
            "cap_aft_radius_mm": round(cap_radius_at(cap, -599.5), 3),
            "cap_shoulder_radius_mm": round(cap_radius_at(cap, -485.), 3),
            "single_fin_only": True, "main_body_unchanged": True,
            "thrusters_seated": True, "state_geometry_preserved": True}


if __name__ == "__main__":
    import sys
    keys = sys.argv[1:] or tuple(VARIANTS)
    assert set(keys) <= set(VARIANTS)
    baseline = parts_from(ORIGINAL)
    old_fin = {part.label: part for part in
               read_step(ROOT / "STEP" / "Spear_Original_Fin_Focus.step").children}
    old_cap = {part.label: part for part in
               read_step(ROOT / "STEP" / "Spear_Original_Cap_Focus.step").children}
    assert set(old_fin) == {"body", "aft_fin_0"}
    assert set(old_cap) == {"turning_cap", "thruster_0", "thruster_90",
                            "thruster_180", "thruster_270"}
    assert all(same_solid(shape, baseline[label]) for label, shape in {**old_fin, **old_cap}.items())
    report = {name: check(name, baseline) for name in keys}
    (ROOT / "reviews" / "spear_revision_checks.json").write_text(
        json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print("PASS:", ", ".join(report))
