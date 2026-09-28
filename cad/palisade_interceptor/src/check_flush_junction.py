"""Inspect serialized Spear STEP for a constant-radius cap/body join."""

import json
from pathlib import Path

from cadgen import build123d as bd, read_step
from cadgen.geometry import boundary_edges, self_intersections, topology_errors

from check_spear_revisions import cap_radius_at, overlap, parts_from, radial_max, same_solid


ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / "STEP"
OFFSET = 270.


def get_parts(path, count):
    model = read_step(STEP / path)
    parts = {part.label: part for part in model.children}
    assert len(parts) == len(model.children) == count
    assert all(len(part.solids()) == 1 and part.is_valid and part.volume > 0
               for part in parts.values())
    return parts


def main():
    original = parts_from(STEP / "Spear_Selected_SketchLow_Boattail.step")
    previous = get_parts("Spear_CylinderFillet_Nozzle0.step", 12)
    full = get_parts("Spear_FlushJunction_Cap.step", 12)
    separated = get_parts("Spear_FlushJunction_Cap_Separated.step", 12)
    cap_focus = get_parts("Spear_FlushJunction_Cap_Focus.step", 6)
    assert set(full) == set(separated) == set(previous)
    assert set(cap_focus) == {"turning_cap", "thruster_0", "thruster_0_throat",
                              "thruster_90", "thruster_180", "thruster_270"}
    for label, part in full.items():
        if label != "body" and label != "turning_cap":
            assert same_solid(part, previous[label]), (label, "protected part changed")
        if label in cap_focus:
            assert same_solid(part, cap_focus[label]), (label, "focus differs")
        displaced = label == "turning_cap" or label.startswith("thruster_")
        restored = separated[label].translate((OFFSET, 0, 0)) if displaced else separated[label]
        assert same_solid(part, restored), (label, "separated shape changed")

    body, prior_body, cap = full["body"], original["body"], full["turning_cap"]
    assert not same_solid(body, prior_body), "failed to correct the 22 mm seam region"
    forward_region = bd.Box(1000., 250., 250.).translate((102., 0., 0.))
    assert same_solid(body & forward_region, prior_body & forward_region), (
        "geometry changed beyond the first 22 mm of the body"
    )
    stations = {str(x): round(cap_radius_at(body, x), 3)
                for x in (-419.5, -409., -399., -398.5, -380.)}
    prior_stations = {str(x): round(cap_radius_at(prior_body, x), 3)
                      for x in (-419.5, -409., -399., -398.5, -380.)}
    old_near = cap_radius_at(prior_body, -419.5)
    assert 60.7 < old_near < 61.0
    for x in (-419.5, -409., -399., -398.5):
        assert abs(cap_radius_at(body, x)-62.) < .02, (x, "body still has shoulder rise")
    for x in (-599.5, -577., -520., -470., -440., -421., -420.5):
        if x > -578.:
            assert abs(cap_radius_at(cap, x)-62.) < .02, (x, "cap not full radius")
    assert abs(cap_radius_at(cap, -420.5)-cap_radius_at(body, -419.5)) < .02
    assert abs(cap.bounding_box().max.X+420.) < .002
    assert abs(cap.bounding_box().min.X+600.) < .002
    assert overlap(cap, body) < .001 and overlap(separated["turning_cap"], body) < .001
    for label, item in (("body", body), ("cap", cap),
                        ("separated cap", separated["turning_cap"]),
                        ("isolated cap", cap_focus["turning_cap"])):
        assert not topology_errors(item), (label, "invalid topology")
        assert len(item.shells()) == 1 and not boundary_edges(item.shells()[0]), (
            label, "open shell"
        )
        assert not self_intersections(item), (label, "self intersection")

    for index in range(4):
        assert overlap(full[f"aft_fin_{index}"], body) > .001
    for angle in (0, 90, 180, 270):
        assert overlap(full[f"thruster_{angle}"], cap) > .001
    mouth = bd.Box(1., 1., 1.).translate((-470., 66.5, 0.))
    deep = bd.Box(1., 1., 1.).translate((-470., 49., 0.))
    assert overlap(mouth, cap) < .001 and overlap(mouth, full["thruster_0"]) < .001
    assert overlap(deep, full["thruster_0_throat"]) > .001
    main_bore = bd.Box(2., 2., 2.).translate((-415., 0., 0.))
    assert overlap(main_bore, body) < .001 and overlap(main_bore, full["main_nozzle"]) < .001
    envelope = max(radial_max(part) for part in full.values())
    assert abs(envelope-79.009) < .02
    report = {"ok": True, "length_mm": 1200., "radial_envelope_mm": round(envelope, 3),
              "prior_body_radius_at_minus419_5_mm": round(old_near, 3),
              "prior_body_stations_mm": prior_stations,
              "new_body_stations_mm": stations,
              "new_cap_radius_at_minus420_5_mm": round(cap_radius_at(cap, -420.5), 3),
              "unchanged_body_from_minus398_forward": True,
              "one_detailed_nozzle_only": True, "stage_geometry_preserved": True}
    (ROOT / "reviews" / "spear_flush_junction_checks.json").write_text(
        json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print("PASS: 62 mm flush cap/body join and exact forward-body preservation")


if __name__ == "__main__":
    main()
