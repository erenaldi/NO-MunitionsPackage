"""Check all six serialized housing states and study-envelope consistency."""

import json
from pathlib import Path

from check_a import intersection, limits, same, saved, saved_spear


ROOT = Path(__file__).resolve().parents[1]
STUDIES = {"A": "A_Bridge", "B": "B_OpenCrown", "C": "C_SlottedShell"}
BOXES = {f"cassette_{row}_{side}" for row in ("aft", "forward")
         for side in ("port", "starboard")}


def main():
    length, diameter = None, None
    radius, length = saved_spear()
    diameter = 2*radius
    assert abs(length-1200) < .002 and abs(diameter-158.013) < .02
    baseline_boxes = None
    results = {}
    for direction, stem in STUDIES.items():
        bare, filled = (saved(f"{stem}_{state}.step") for state in ("Bare", "Filled"))
        assert set(filled) - set(bare) == BOXES and set(bare) == set(filled) - BOXES
        for name, part in bare.items():
            same(part, filled[name])
        boxes = {name: filled[name] for name in BOXES}
        if baseline_boxes is not None:
            for name, part in boxes.items():
                same(part, baseline_boxes[name])
        else:
            baseline_boxes = boxes
        centers = {name: tuple(round((a+b)/2, 3) for a, b in limits(part))
                   for name, part in boxes.items()}
        assert set(centers.values()) == {
            (x, y, -133.) for x in (-664., 664.) for y in (-95., 95.)}
        for name, part in boxes.items():
            assert tuple(round(b-a, 3) for a, b in limits(part)) == (1310., 180., 180.)
            for other_name, other in filled.items():
                if name != other_name:
                    assert intersection(part, other) < .001, (direction, name, other_name)
                    ox, oy, oz = limits(other)
                    x, y, _ = centers[name]
                    if ox[0] < x < ox[1] and oy[0] < y < oy[1]:
                        assert oz[0] >= -223-.01, (direction, name, other_name, "exit blocked")
        all_bounds = [limits(part) for part in filled.values()]
        outer = tuple((min(b[i][0] for b in all_bounds), max(b[i][1] for b in all_bounds))
                      for i in range(3))
        xyz = tuple(round(b-a, 3) for a, b in outer)
        assert xyz == (2980., 400., 223.), (direction, xyz)
        assert all(abs(limits(part)[2][0]+223) < .01
                   for name, part in filled.items() if name.endswith("_sensor_shell")
                   or name in BOXES or name.endswith("_rail")), (direction, "nonflush underside")
        for end in ("forward", "aft"):
            shell = filled[f"{end}_sensor_shell"]
            aperture = filled[f"{end}_aperture"]
            assert intersection(shell, aperture) < .001
            assert aperture.bounding_box().size.Y > 100
        for side in ("port", "starboard"):
            rail_name = (f"{side}_outer_rail" if direction == "A" else
                         f"{side}_chamfered_rail" if direction == "B" else
                         f"{side}_windowed_rail")
            bridge_name = "dorsal_bridge" if direction == "A" else "broad_dorsal_saddle"
            if direction == "B":
                assert any(intersection(filled[rail_name], filled[f"roof_arch_{x}"]) > .01
                           for x in (-1180, 0, 1180)), (direction, side, "floating rail")
            else:
                assert intersection(filled[rail_name], filled[bridge_name]) > .01, (
                    direction, side, "floating rail")
        # End faces of cut-out specimen are demonstrably distinct, not copied
        # A end housings under a new name. Negative-space identity is sampled.
        if direction == "B":
            assert not filled["central_crown"].is_inside((660, 118, -12))
            assert all(not filled[f"roof_arch_{station}"].is_inside((660, 118, -12))
                       for station in (-1180, 0, 1180))
            assert not filled["starboard_roof_shoulder"].is_inside((660, 118, -12))
        elif direction == "C":
            assert not filled["broad_dorsal_saddle"].is_inside((0, 0, -2))
            assert filled["broad_dorsal_saddle"].is_inside((0, 0, -15))
            for x in (-660, 660):
                for name in ("port_windowed_rail", "starboard_windowed_rail"):
                    sign = -1 if name.startswith("port") else 1
                    assert not filled[name].is_inside((x, sign*193, -72))
                    assert filled[name].is_inside((x, sign*193, -165))
        roof = filled["dorsal_bridge" if direction == "A" else
                      "central_crown" if direction == "B" else "broad_dorsal_saddle"]
        roof_thickness = round(roof.bounding_box().size.Z, 3)
        assert roof_thickness == (24 if direction == "B" else 30)
        if direction == "C":
            # Roof's 8 mm recessed center remains 22 mm thick at X=Y=0.
            assert not roof.is_inside((0, 0, -7.9)) and roof.is_inside((0, 0, -8.1))
        rail_thickness = round(filled["starboard_chamfered_rail" if direction == "B" else
                                      "starboard_windowed_rail" if direction == "C" else
                                      "starboard_outer_rail"].bounding_box().size.Y, 3)
        assert rail_thickness == 14
        results[direction] = {"bare_parts": len(bare), "filled_parts": len(filled),
                              "outer_xyz_mm": xyz, "centers_xyz_mm": centers,
                              "roof_full_thickness_mm": roof_thickness,
                              "side_rail_outer_thickness_mm": rail_thickness,
                              "bare_filled_housing_identical": True,
                              "four_identical_cassette_placeholders": True,
                              "four_downward_centerline_exits_open": True}

    report = {"ok": True, "spear_length_mm": round(length, 3),
              "spear_max_fin_diameter_mm": round(diameter, 3),
              "illustrative_wall_mm": 6,
              "example_transverse_half_margin_mm": round((180-12-diameter)/2, 3),
              "example_axial_half_margin_mm": round((1310-12-length)/2, 3),
              "donor_door_sweep_aircraft_pylon_fit_verified": False,
              "directions": results}
    assert report["example_transverse_half_margin_mm"] > 0
    out = ROOT / "reviews" / "Trio_Checks.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("PASS: all six saved states and four-place sample envelope")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
