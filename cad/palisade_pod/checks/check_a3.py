"""Saved STEP checks for front-only fairing revision against approved A2 sides."""

import json
from pathlib import Path

from check_a import intersection, limits, same, saved, saved_spear


ROOT = Path(__file__).resolve().parents[1]


def main():
    old = saved("A2_OpenSides_Bare.step")
    bare = saved("A3_MountFront_Bare.step")
    full = saved("A3_MountFront_Filled.step")
    focus = saved("A3_MountFront_Focus.step")
    assert set(focus) == {"forward_sensor_shell", "forward_aperture"}
    assert len(old) == len(bare) == 11 and len(full) == 15
    assert set(old) == set(bare) == set(full)-{
        "cassette_aft_port", "cassette_aft_starboard",
        "cassette_forward_port", "cassette_forward_starboard"}
    for label in bare:
        same(bare[label], full[label])
        if label != "forward_sensor_shell":
            same(bare[label], old[label])
    fairing = bare["forward_sensor_shell"]
    for label in focus:
        same(focus[label], bare[label])
    assert (fairing-old["forward_sensor_shell"]).volume < .001
    assert (old["forward_sensor_shell"]-fairing).volume > 1000
    assert all(abs(actual-expected) < .01 for actual, expected in
               zip(limits(fairing)[0], (1325., 1490.))), limits(fairing)[0]
    assert not fairing.is_inside((1480, 160, -111.5))
    assert fairing.is_inside((1360, 150, -111.5))
    assert not fairing.is_inside((1489, 0, -113))
    assert bare["forward_aperture"].is_inside((1487.5, 0, -113))
    assert intersection(fairing, bare["forward_aperture"]) < .001
    boxes = {name: shape for name, shape in full.items() if name.startswith("cassette_")}
    assert len(boxes) == 4
    for label, part in boxes.items():
        assert round(part.bounding_box().size.Y, 3) == 196
        for frame_label, frame in bare.items():
            assert intersection(part, frame) < .001, (label, frame_label)
    radius, length = saved_spear()
    assert abs(length-1200) < .002 and abs(2*radius-158.013) < .02
    for state in (bare, full):
        spans = [limits(item) for item in state.values()]
        dims = [round(max(b[i][1] for b in spans)-min(b[i][0] for b in spans), 3)
                for i in range(3)]
        assert dims == [2980., 400., 223.], dims
    result = {"ok": True, "bare_parts": len(bare), "filled_parts": len(full),
              "unchanged_A2_roof_side_rails_rear_sensor_four_cells": True,
              "forward_only_taper_inside_A2_hull": True,
              "outer_xyz_mm": [2980, 400, 223],
              "approved_spear_max_fin_diameter_mm": round(radius*2, 3),
              "donor_door_and_aircraft_clearance_verified": False}
    (ROOT / "reviews" / "A3_MountFront_Checks.json").write_text(
        json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
