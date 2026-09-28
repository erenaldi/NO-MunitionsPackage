"""Artifact-only checks for user's A-with-open-sidewalls correction."""

import json
from pathlib import Path

from check_a import intersection, limits, same, saved, saved_spear


ROOT = Path(__file__).resolve().parents[1]


def main():
    old = saved("A_Bridge_Bare.step")
    bare = saved("A2_OpenSides_Bare.step")
    full = saved("A2_OpenSides_Filled.step")
    assert len(old) == len(bare) == 11 and len(full) == 15
    assert set(bare) == set(old)
    boxes = {name: shape for name, shape in full.items() if name.startswith("cassette_")}
    assert len(boxes) == 4 and set(full)-set(bare) == set(boxes)
    for name, shape in bare.items():
        same(shape, full[name])
        if name not in ("port_outer_rail", "starboard_outer_rail"):
            same(shape, old[name])
    for side, sign in (("port", -1), ("starboard", 1)):
        rail = bare[f"{side}_outer_rail"]
        old_rail = old[f"{side}_outer_rail"]
        assert abs(rail.bounding_box().size.Z-19) < .01
        assert abs(limits(rail)[2][0]+43) < .01 and abs(limits(rail)[2][1]+24) < .01
        assert (rail-old_rail).volume < .001 and (old_rail-rail).volume > 0
        assert intersection(rail, bare["dorsal_bridge"]) > .01
        for row in ("aft", "forward"):
            part = boxes[f"cassette_{row}_{side}"]
            x, y, z = limits(part)
            assert (round(x[1]-x[0], 3), round(y[1]-y[0], 3),
                    round(z[1]-z[0], 3)) == (1310, 196, 180)
            assert abs(y[1]-(200 if sign == 1 else -4)) < .01
            assert abs(y[0]-(4 if sign == 1 else -200)) < .01
            assert abs(z[1]+43) < .01 and abs(z[0]+223) < .01
            for other_name, other in full.items():
                if other_name != part.label:
                    assert intersection(part, other) < .001, (part.label, other_name)
    radius, length = saved_spear()
    diameter = radius*2
    assert abs(length-1200) < .002 and abs(diameter-158.013) < .02
    wall = 6
    y_margin = (196-2*wall-diameter)/2
    x_margin = (1310-2*wall-length)/2
    assert y_margin > 0 and x_margin > 0
    for state in (bare, full):
        all_bounds = [limits(item) for item in state.values()]
        total = [round(max(span[axis][1] for span in all_bounds)-
                       min(span[axis][0] for span in all_bounds), 3)
                 for axis in range(3)]
        assert total == [2980., 400., 223.], total
    result = {"ok": True, "bare_parts": len(bare), "filled_parts": len(full),
              "outer_xyz_mm": [2980, 400, 223], "cassette_xyz_mm": [1310, 196, 180],
              "spear_length_mm": round(length, 3),
              "spear_fin_diameter_mm": round(diameter, 3),
              "illustrative_wall_mm": wall,
              "illustrative_half_width_margin_mm": round(y_margin, 3),
              "illustrative_half_axial_margin_mm": round(x_margin, 3),
              "cassette_external_sides_flush_with_sensor_ends_y_mm": [-200, 200],
              "retained_side_frame_depth_below_top_mm": 43,
              "original_A_bridge_and_sensor_geometry_preserved": True,
              "actual_donor_door_and_aircraft_clearance_verified": False}
    (ROOT / "reviews" / "A2_OpenSides_Checks.json").write_text(
        json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
