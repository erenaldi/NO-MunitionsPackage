"""Saved STEP checks for the plain cylindrical cap with aft-edge fillet."""

import json
from pathlib import Path

from cadgen import build123d as bd, read_step
from cadgen.geometry import boundary_edges, self_intersections, topology_errors

from check_spear_revisions import cap_radius_at, overlap, parts_from, radial_max, same_solid


ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / "STEP"
OFFSET = 270.


def read_parts(path, count):
    model = read_step(STEP / path)
    parts = {item.label: item for item in model.children}
    assert len(parts) == len(model.children) == count, path
    assert all(len(item.solids()) == 1 and item.is_valid and item.volume > 0
               for item in parts.values()), path
    return parts


def main():
    original = parts_from(STEP / "Spear_Selected_SketchLow_Boattail.step")
    prototype = read_parts("Spear_BandedCap_Nozzle0.step", 12)
    actual = read_parts("Spear_CylinderFillet_Nozzle0.step", 12)
    apart = read_parts("Spear_CylinderFillet_Nozzle0_Separated.step", 12)
    focus = read_parts("Spear_CylinderFillet_Cap_Focus.step", 6)
    expected = set(original) | {"thruster_0_throat"}
    assert set(actual) == set(apart) == expected
    assert set(focus) == {"turning_cap", "thruster_0", "thruster_0_throat",
                          "thruster_90", "thruster_180", "thruster_270"}
    for label, part in actual.items():
        if label in original and label not in ("turning_cap", "thruster_0"):
            assert same_solid(part, original[label]), (label, "protected missile changed")
        if label in ("thruster_0", "thruster_0_throat"):
            assert same_solid(part, prototype[label]), (label, "nozzle detail changed")
        if label in focus:
            assert same_solid(part, focus[label]), (label, "focus geometry differs")
        displaced = label == "turning_cap" or label.startswith("thruster_")
        restored = apart[label].translate((OFFSET, 0, 0)) if displaced else apart[label]
        assert same_solid(part, restored), (label, "separated geometry differs")

    cap, body = actual["turning_cap"], actual["body"]
    assert abs(cap.bounding_box().min.X+600.) < .002
    assert abs(cap.bounding_box().max.X+420.) < .002
    assert overlap(cap, body) < .001 and overlap(apart["turning_cap"], body) < .001
    assert not same_solid(cap, prototype["turning_cap"]), "old banded cap reused"
    radii = {str(x): round(cap_radius_at(cap, x), 3)
             for x in (-599.5, -590., -577., -520., -470., -440., -421.)}
    assert 38. < cap_radius_at(cap, -599.5) < 48., "aft fillet not present"
    assert cap_radius_at(cap, -599.5) < cap_radius_at(cap, -590.) < cap_radius_at(cap, -577.)
    for station in (-577., -520., -470., -440., -421.):
        assert abs(cap_radius_at(cap, station)-60.76) < .03, (station, "cap not cylindrical")
    assert abs(cap_radius_at(cap, -421.)-cap_radius_at(body, -419.5)) < .1, (
        "body/cap seam no longer flush"
    )
    for label, item in (("cap", cap), ("socket collar", actual["thruster_0"]),
                        ("dark throat", actual["thruster_0_throat"]),
                        ("cap focus", focus["turning_cap"])):
        assert not topology_errors(item), (label, "invalid topology")
        assert len(item.shells()) == 1 and not boundary_edges(item.shells()[0]), (
            label, "open shell"
        )
        assert not self_intersections(item), (label, "self intersections")

    mouth = bd.Box(1, 1, 1).translate((-470., 66.5, 0.))
    lip = bd.Box(1, 1, 1).translate((-470., 67.6, 9.))
    deep = bd.Box(1, 1, 1).translate((-470., 49., 0.))
    blind = bd.Box(1, 1, 1).translate((-470., 46., 0.))
    assert overlap(mouth, cap) < .001 and overlap(mouth, actual["thruster_0"]) < .001
    assert overlap(lip, actual["thruster_0"]) > .001
    assert overlap(deep, actual["thruster_0_throat"]) > .001
    assert overlap(blind, cap) > .001
    for angle in (0, 90, 180, 270):
        assert overlap(actual[f"thruster_{angle}"], cap) > .001
    assert overlap(actual["thruster_0_throat"], cap) < .001
    bore = bd.Box(2, 2, 2).translate((-415., 0., 0.))
    assert overlap(bore, body) < .001 and overlap(bore, actual["main_nozzle"]) < .001
    envelope = max(radial_max(item) for item in actual.values())
    assert abs(envelope-79.009) < .02
    result = {"ok": True, "length_mm": 1200., "radial_envelope_mm": round(envelope, 3),
              "cap_section_radii_mm": radii, "aft_edge_fillet_nominal_mm": 22.,
              "detailed_nozzles": 1, "other_three_nozzles_original": True,
              "core_and_fins_preserved": True, "separation_shapes_preserved": True}
    (ROOT / "reviews" / "spear_cylinder_fillet_checks.json").write_text(
        json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print("PASS: flush cap cylinder, aft fillet, one detailed nozzle and staging")


if __name__ == "__main__":
    main()
