"""Check full-circumference ACM blind-port pattern from saved STEP states."""

import json
import math
from itertools import combinations
from pathlib import Path

from cadgen import build123d as bd, read_step
from cadgen.geometry import boundary_edges, self_intersections, topology_errors

from check_spear_revisions import cap_radius_at, overlap, radial_max, same_solid


ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / "STEP"
ROW_X = (-568., -550., -532., -514., -496., -478.)
AROUND = 16
R = 54.56
CAP_SHIFT = 270.


def parts(name, count):
    shape = read_step(STEP / name)
    result = {item.label: item for item in shape.children}
    assert len(result) == len(shape.children) == count, (name, "missing/duplicate label")
    assert all(len(item.solids()) == 1 and item.is_valid and item.volume > 0
               for item in result.values()), (name, "invalid solid")
    return result


def main():
    baseline = parts("Spear_UniformBarrel.step", 12)
    full = parts("Spear_ACMWrap.step", 199)
    separated = parts("Spear_ACMWrap_Separated.step", 199)
    focus = parts("Spear_ACMWrap_Cap_Focus.step", 193)
    labels = {f"acm_{kind}_{row}_{col}"
              for kind in ("rim", "core") for row in range(len(ROW_X))
              for col in range(AROUND)}
    expected = {"body", "main_nozzle", "turning_cap"} | {
        f"aft_fin_{index}" for index in range(4)} | labels
    assert set(full) == set(separated) == expected
    assert set(focus) == {"turning_cap"} | labels
    assert not any(label.startswith("thruster_") for label in full)
    for label in ("body", "main_nozzle", "aft_fin_0", "aft_fin_1", "aft_fin_2", "aft_fin_3"):
        assert same_solid(full[label], baseline[label]), (label, "approved missile changed")

    cap, body, nozzle = (full[name] for name in ("turning_cap", "body", "main_nozzle"))
    assert abs(cap.bounding_box().min.X+600.) < .002
    assert abs(cap.bounding_box().max.X+470.) < .002
    assert overlap(cap, body) < .001 and overlap(separated["turning_cap"], body) < .001
    front = cap & bd.Box(.2, 120., 120.).translate((-470.5, 0, 0))
    expected_front = math.pi*R*R*.2
    assert front is not None and abs(front.volume-expected_front) < .03
    for x in (-577., -471.):
        measured = cap_radius_at(cap, x)
        assert abs(measured-R) < .02, (x, measured, "cap lost cylindrical outer perimeter")
    # The perforated rows legitimately remove the cardinal-axis extrema,
    # shrinking an axis-aligned Y/Z bbox by a fraction of a millimetre.
    for x in (-535., -500.):
        measured = cap_radius_at(cap, x)
        assert R-.5 < measured <= R+.02, (x, measured, "port row carved too much skin")
    assert not topology_errors(cap), "cap failed topology"
    assert len(cap.shells()) == 1 and not boundary_edges(cap.shells()[0]), "cap shell open"
    assert not self_intersections(cap), "cap self-intersection"

    centers = []
    for row, x in enumerate(ROW_X):
        for col in range(AROUND):
            angle = math.radians(col*360/AROUND+(row%2)*360/(2*AROUND))
            rim = full[f"acm_rim_{row}_{col}"]
            core = full[f"acm_core_{row}_{col}"]
            assert abs(rim.bounding_box().center().X-x) < .002
            assert abs(core.bounding_box().center().X-x) < .002
            assert radial_max(rim) < R-1.5 and radial_max(core) < R-1.5
            # Inspect each serialized port: empty skin, solid blind floor,
            # fitted dark center and no protruding insert.
            def point(radial):
                return (x, radial*math.cos(angle), radial*math.sin(angle))
            assert not cap.is_inside(point(R-.4)), (row, col, "missing blind opening")
            assert cap.is_inside(point(R-9.)), (row, col, "port pierced through")
            assert core.is_inside(point(R-3.)), (row, col, "missing dark center")
            assert overlap(rim, core) < .001, (row, col, "ring covers center")
            centers.append(rim.bounding_box().center())
    nearest = min((a-b).length for a, b in combinations(centers, 2))
    assert nearest > 12.5, ("overlapping/too-close port stations", nearest)
    assert min(ROW_X)-5.3 > -578. and max(ROW_X)+5.3 < -470.

    for label, shape in full.items():
        if label in focus:
            assert same_solid(shape, focus[label]), (label, "cap focus differs")
        moved = label == "turning_cap" or label.startswith("acm_")
        restored = separated[label].translate((CAP_SHIFT, 0, 0)) if moved else separated[label]
        assert same_solid(shape, restored), (label, "separated state changed")
    for label in ("acm_rim_0_0", "acm_core_0_0", "acm_rim_5_15", "acm_core_5_15"):
        candidate = full[label]
        assert not topology_errors(candidate)
        assert len(candidate.shells()) == 1 and not boundary_edges(candidate.shells()[0])
        assert not self_intersections(candidate)
    motor_bore = bd.Box(2., 2., 2.).translate((-465., 0., 0.))
    assert overlap(motor_bore, body) < .001 and overlap(motor_bore, nozzle) < .001
    envelope = max(radial_max(item) for item in full.values())
    assert abs(envelope-79.006) < .02
    result = {"ok": True, "full_parts": len(full), "focus_parts": len(focus),
              "axial_rows": len(ROW_X), "ports_per_row": AROUND,
              "total_blind_ports": len(centers),
              "minimum_insert_center_spacing_mm": round(nearest, 3),
              "cap_front_section_mm3": round(front.volume, 3),
              "radial_envelope_mm": round(envelope, 3),
              "all_saved_port_centers_blind": True,
              "approved_body_fins_main_nozzle_unchanged": True,
              "all_saved_stage_components_preserved": True}
    (ROOT / "reviews" / "spear_acm_wrap_checks.json").write_text(
        json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print("PASS: all-around ACM cap, 96 blind ports, intact Spear and stage")


if __name__ == "__main__":
    main()
