"""Artifact-side A9 continuous-curve, no-aperture silhouette boundary."""

import json
from pathlib import Path

from cadgen import build123d as bd

from check_a import intersection, limits, same, saved, saved_spear


ROOT = Path(__file__).resolve().parents[1]
BOXES = {f"cassette_{row}_{side}" for row in ("aft", "forward")
         for side in ("port", "starboard")}


def tip_span(shape, x):
    slice_ = shape & bd.Box(.05, 500, 500).translate((x, 0, -111.5))
    assert slice_ is not None and slice_.volume > 0
    bounds = slice_.bounding_box()
    return (round(bounds.size.Y, 3), round(bounds.size.Z, 3))


def main():
    old = saved("A8_RoundedTips_Bare.step")
    bare = saved("A9_ContinuousEnds_Bare.step")
    full = saved("A9_ContinuousEnds_Filled.step")
    assert len(bare) == 9 and len(full) == 13
    assert set(bare) == set(old)-{"forward_aperture", "aft_aperture"}
    assert set(full)-set(bare) == BOXES
    for name, shape in bare.items():
        same(shape, full[name])
        if name not in ("forward_sensor_shell", "aft_sensor_shell"):
            same(shape, old[name])
    assert not any("aperture" in name for name in full)
    assert all(abs(a-b) < .01 for a, b in
               zip(limits(bare["forward_sensor_shell"])[0], (1325, 1790)))
    assert all(abs(a-b) < .01 for a, b in
               zip(limits(bare["aft_sensor_shell"])[0], (-1710, -1325)))
    tips = {"forward": tip_span(bare["forward_sensor_shell"], 1789.97),
            "aft": tip_span(bare["aft_sensor_shell"], -1709.97)}
    assert all(width < 20 and height < 12 for width, height in tips.values()), tips
    for name in BOXES:
        box = full[name]
        assert tuple(round(b-a, 3) for a, b in limits(box)) == (1310, 196, 180)
        for other_name, other in full.items():
            if name != other_name:
                assert intersection(box, other) < .001, (name, other_name)
        x, y, _ = ((a+b)/2 for a, b in limits(box))
        for frame_name, frame in bare.items():
            fx, fy, fz = limits(frame)
            if fx[0] < x < fx[1] and fy[0] < y < fy[1]:
                assert fz[0] >= -223-.01, (name, frame_name, "blocked exit")
    for state in (bare, full):
        bboxes = [limits(shape) for shape in state.values()]
        dims = [round(max(b[i][1] for b in bboxes)-min(b[i][0] for b in bboxes), 3)
                for i in range(3)]
        assert dims == [3500., 400., 223.], dims
    radius, length = saved_spear()
    assert abs(length-1200) < .002 and abs(radius*2-158.013) < .02
    report = {"ok": True, "bare_parts": len(bare), "filled_parts": len(full),
              "outer_xyz_mm": [3500, 400, 223], "tip_section_yz_mm": tips,
              "A8_roof_lips_four_boxes_preserved": True,
              "sensor_aperture_art_deferred": True,
              "spear_max_fin_diameter_mm": round(2*radius, 3),
              "donor_aircraft_door_clearance_verified": False}
    (ROOT / "reviews" / "A9_ContinuousEnds_Checks.json").write_text(
        json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
