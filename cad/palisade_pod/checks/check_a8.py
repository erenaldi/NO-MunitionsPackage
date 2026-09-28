"""Saved A8 rounded-tip and sensor-cue regression against A7."""

import json
from pathlib import Path

from cadgen import build123d as bd

from check_a import intersection, limits, same, saved, saved_spear


ROOT = Path(__file__).resolve().parents[1]
BOXES = {f"cassette_{row}_{side}" for row in ("aft", "forward")
         for side in ("port", "starboard")}
CHANGED = {"forward_sensor_shell", "aft_sensor_shell",
           "forward_aperture", "aft_aperture"}


def tip_span(shell, x):
    sample = shell & bd.Box(.05, 500, 500).translate((x, 0, -112))
    assert sample is not None and sample.volume > 0
    box = sample.bounding_box()
    return (round(box.size.Y, 2), round(box.size.Z, 2))


def main():
    prior = saved("A7_LevelBeam_Bare.step")
    bare = saved("A8_RoundedTips_Bare.step")
    full = saved("A8_RoundedTips_Filled.step")
    assert len(prior) == len(bare) == 11 and len(full) == 15
    assert set(prior) == set(bare) == set(full)-BOXES
    for key, shape in bare.items():
        same(shape, full[key])
        if key not in CHANGED:
            same(shape, prior[key])
    front, aft = bare["forward_sensor_shell"], bare["aft_sensor_shell"]
    assert all(abs(a-b) < .01 for a, b in zip(limits(front)[0], (1325, 1790)))
    assert all(abs(a-b) < .01 for a, b in zip(limits(aft)[0], (-1710, -1325)))
    forward_tip, aft_tip = tip_span(front, 1789.97), tip_span(aft, -1709.97)
    assert 75 < forward_tip[0] < 85 and 32 < forward_tip[1] < 40, forward_tip
    assert 80 < aft_tip[0] < 90 and 36 < aft_tip[1] < 44, aft_tip
    assert front.is_inside((1775, 0, -126)) and aft.is_inside((-1695, 0, -112))
    for end, shell in (("forward", front), ("aft", aft)):
        aperture = bare[f"{end}_aperture"]
        assert round(aperture.bounding_box().size.Y, 3) == 60
        assert round(aperture.bounding_box().size.Z, 3) == 18
        assert intersection(shell, aperture) < .001
    assert bare["forward_aperture"].is_inside((1787.5, 0, -126))
    assert bare["aft_aperture"].is_inside((-1707.5, 0, -112))
    for name in BOXES:
        box = full[name]
        assert tuple(round(b-a, 3) for a, b in limits(box)) == (1310, 196, 180)
        for other_name, other in full.items():
            if other_name != name:
                assert intersection(box, other) < .001, (name, other_name)
        x, y, _ = ((a+b)/2 for a, b in limits(box))
        for frame_name, frame in bare.items():
            fx, fy, fz = limits(frame)
            if fx[0] < x < fx[1] and fy[0] < y < fy[1]:
                assert fz[0] >= -223-.01, (name, frame_name, "blocked exit")
    for parts in (bare, full):
        spans = [limits(shape) for shape in parts.values()]
        dims = [round(max(b[i][1] for b in spans)-min(b[i][0] for b in spans), 3)
                for i in range(3)]
        assert dims == [3500., 400., 223.], dims
    radius, length = saved_spear()
    assert abs(length-1200) < .002 and abs(radius*2-158.013) < .02
    result = {"ok": True, "bare_parts": len(bare), "filled_parts": len(full),
              "outer_xyz_mm": [3500, 400, 223],
              "forward_tip_section_width_height_mm": forward_tip,
              "aft_tip_section_width_height_mm": aft_tip,
              "end_sensor_cue_width_height_mm": [60, 18],
              "unchanged_A7_roof_lips_and_four_boxes": True,
              "spear_fin_diameter_mm": round(radius*2, 3),
              "actual_donor_door_aircraft_clearance_verified": False}
    (ROOT / "reviews" / "A8_RoundedTips_Checks.json").write_text(
        json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
