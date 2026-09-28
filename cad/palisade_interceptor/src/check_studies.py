"""Artifact-side checks for assembled and separated Palisade concept STEP files."""

import json
import math
from pathlib import Path

from cadgen import build123d as bd, read_step


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "A": ("Spear", 1200., 180., 11),
    "B": ("Shoulder", 1120., 215., 15),
    "C": ("Facet", 1280., 230., 11),
}
CAP_OFFSET = 270.
TOL = .002


def overlap(a, b):
    result = a & b
    return 0. if result is None else result.volume


def assert_close(a, b, label, tolerance=TOL):
    assert abs(a-b) < tolerance, f"{label}: expected {b}, observed {a}"


def check(key):
    name, length, cap_length, count = EXPECTED[key]
    base = ROOT / "STEP" / f"{key}_{name}"
    model, apart = read_step(base.with_suffix(".step")), read_step(base.with_name(base.name+"_Separated.step"))
    groups = []
    for variant in (model, apart):
        parts = {p.label: p for p in variant.children}
        assert len(parts) == count == len(variant.children), f"{key}: missing or duplicate component"
        expected = {"body", "turning_cap", "main_nozzle"} | {
            f"thruster_{angle}" for angle in (0, 90, 180, 270)
        } | {f"aft_fin_{i}" for i in range(4)}
        if key == "B":
            expected |= {f"fore_fin_{i}" for i in range(4)}
        assert set(parts) == expected, f"{key}: unexpected labels {sorted(set(parts)^expected)}"
        for label, part in parts.items():
            assert len(part.solids()) == 1 and part.is_valid and part.volume > 0, (key, label)
        groups.append(parts)
    joined, separated = groups
    body, cap, nozzle = joined["body"], joined["turning_cap"], joined["main_nozzle"]
    bb, cb = body.bounding_box(), cap.bounding_box()
    seam = -length/2 + cap_length
    assert_close(cb.min.X, -length/2, "aft limit")
    assert_close(cb.max.X, seam, "cap seam")
    assert_close(bb.min.X, seam, "body seam")
    assert_close(bb.max.X, length/2, "nose limit")
    assert overlap(body, cap) < .001, f"{key}: cap crosses the main body"
    assert nozzle.bounding_box().min.X >= seam-TOL, f"{key}: nozzle protrudes into cap"
    assert nozzle.bounding_box().max.X < seam+55, f"{key}: nozzle escapes cavity"
    assert overlap(nozzle, body) < .001, f"{key}: main nozzle buried in body material"

    for label, fin in joined.items():
        if label.startswith(("aft_fin_", "fore_fin_")):
            assert overlap(fin, body) > .001, f"{key}: detached {label}"
        if label.startswith("thruster_"):
            assert overlap(fin, cap) > .001, f"{key}: detached {label}"

    # Check actual solids at the nozzle's exposed annulus and vacant bore;
    # the cap occludes the whole opening in the assembled state.
    tube_r = max(abs(nozzle.bounding_box().max.Y), abs(nozzle.bounding_box().min.Y))
    annulus = bd.Box(2, 3, 3).translate((seam+5, tube_r*.82, 0))
    bore = bd.Box(2, 3, 3).translate((seam+5, 0, 0))
    cap_occluder = bd.Box(2, 3, 3).translate((seam-2, 0, 0))
    assert overlap(annulus, nozzle) > .001, f"{key}: missing visible nozzle lip"
    assert overlap(bore, nozzle) < .001 and overlap(bore, body) < .001, f"{key}: main bore blocked"
    assert overlap(cap_occluder, cap) > .001, f"{key}: cap not covering nozzle"

    for label in joined:
        old, new = joined[label], separated[label]
        ob, nb = old.bounding_box(), new.bounding_box()
        moved = label == "turning_cap" or label.startswith("thruster_")
        assert_close(nb.min.X, ob.min.X-(CAP_OFFSET if moved else 0), f"{label} placement")
        for axis in ("Y", "Z"):
            assert_close(getattr(nb.min, axis), getattr(ob.min, axis), f"{label} {axis} placement")
        assert_close(new.volume, old.volume, f"{label} unchanged volume")
        restored = new.translate((CAP_OFFSET, 0, 0)) if moved else new
        lost = old - restored
        gained = restored - old
        assert (lost is None or lost.volume < .002) and (gained is None or gained.volume < .002), (
            key, label, "component geometry changed between states"
        )
    assert overlap(separated["turning_cap"], body) < .001
    return {"label": model.label, "length_mm": length, "cap_length_mm": cap_length,
            "radial_envelope_mm": max(math.hypot(v.Y, v.Z) for part in joined.values()
                                       for v in part.tessellate(.5)[0]),
            "solids": count, "state_geometry_preserved": True,
            "body_cap_disjoint": True, "nozzle_open_after_separation": True}


if __name__ == "__main__":
    import sys
    keys = sys.argv[1:] or ("A", "B", "C")
    assert set(keys) <= set(EXPECTED), f"unknown concept(s): {keys}"
    report = {key: check(key) for key in keys}
    (ROOT / "reviews" / "checks.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print("PASS:", ", ".join(f"{key} ({data['solids']} solids)" for key, data in report.items()))
