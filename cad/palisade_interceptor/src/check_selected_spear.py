"""Serialized-artifact gate for the user-selected fourfold Spear revision."""

import json
from pathlib import Path

from cadgen import build123d as bd

from check_spear_revisions import cap_radius_at, overlap, parts_from, radial_max, same_solid


ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / "STEP"
OFFSET = 270.


def main():
    original = parts_from(STEP / "A_Spear.step")
    preview = parts_from(STEP / "Spear_SketchLow_Boattail.step")
    assembled = parts_from(STEP / "Spear_Selected_SketchLow_Boattail.step")
    separated = parts_from(STEP / "Spear_Selected_SketchLow_Boattail_Separated.step")
    expected = {"body", "main_nozzle", "turning_cap"} | {
        f"thruster_{n}" for n in (0, 90, 180, 270)
    } | {f"aft_fin_{index}" for index in range(4)}
    assert set(assembled) == set(separated) == expected
    for name in ("body", "main_nozzle"):
        assert same_solid(assembled[name], original[name]), (name, "selected A core changed")
    for name in ("turning_cap", "thruster_0", "thruster_90", "thruster_180", "thruster_270"):
        assert same_solid(assembled[name], preview[name]), (name, "approved local cap changed")
    assert same_solid(assembled["aft_fin_0"], preview["aft_fin_0_prototype"])

    body, cap, nozzle = assembled["body"], assembled["turning_cap"], assembled["main_nozzle"]
    assert abs(cap.bounding_box().min.X+600.) < .002
    assert abs(cap.bounding_box().max.X+420.) < .002
    assert abs(body.bounding_box().min.X+420.) < .002
    assert abs(body.bounding_box().max.X-600.) < .002
    assert cap_radius_at(cap, -599.5) < 36.
    assert cap_radius_at(cap, -485.) > 61.
    assert overlap(body, cap) < .001 and overlap(nozzle, body) < .001
    assert overlap(separated["turning_cap"], body) < .001

    lip = bd.Box(2, 2, 2).translate((-415., 27., 0.))
    bore = bd.Box(2, 2, 2).translate((-415., 0., 0.))
    cover = bd.Box(2, 2, 2).translate((-422., 0., 0.))
    assert overlap(lip, nozzle) > .001 and overlap(bore, body) < .001
    assert overlap(bore, nozzle) < .001 and overlap(cover, cap) > .001

    fin0 = assembled["aft_fin_0"]
    tip_radius = radial_max(fin0)
    assert abs(tip_radius-79.) < .1
    for index in range(4):
        part = assembled[f"aft_fin_{index}"]
        assert overlap(part, body) > .001, f"fin {index} has no body root"
        assert overlap(part, cap) < .001, f"fin {index} bridges separable cap"
        assert abs(radial_max(part)-tip_radius) < .01
        assert same_solid(fin0.rotate(bd.Axis.X, 90*index), part), f"fin {index} not fourfold"
    for n in (0, 90, 180, 270):
        assert overlap(assembled[f"thruster_{n}"], cap) > .001

    for name, old in assembled.items():
        new = separated[name]
        restored = new.translate((OFFSET, 0, 0)) if name == "turning_cap" or name.startswith("thruster_") else new
        assert same_solid(old, restored), (name, "separated shape changed")
    envelope = max(radial_max(part) for part in assembled.values())
    assert abs(envelope-tip_radius) < .01
    result = {"ok": True, "assembled": "Spear_Selected_SketchLow_Boattail.step",
              "separated": "Spear_Selected_SketchLow_Boattail_Separated.step",
              "parts": len(assembled), "length_mm": 1200.,
              "radial_envelope_mm": round(envelope, 3),
              "fin_tip_mm": round(tip_radius, 3),
              "cap_aft_radius_mm": round(cap_radius_at(cap, -599.5), 3),
              "fourfold_fin_equivalence": True, "stage_shapes_preserved": True}
    (ROOT / "reviews" / "spear_selected_checks.json").write_text(
        json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print("PASS: selected Spear fourfold fins, boattail and both stage states")


if __name__ == "__main__":
    main()
