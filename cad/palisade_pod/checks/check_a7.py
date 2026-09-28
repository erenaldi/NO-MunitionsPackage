"""Serialized A7 geometry: level center, smoothed sensor ends, same four cells."""

import json
from pathlib import Path

from check_a import intersection, limits, same, saved, saved_spear


ROOT = Path(__file__).resolve().parents[1]
BOXES = {f"cassette_{row}_{side}" for row in ("aft", "forward")
         for side in ("port", "starboard")}
CHANGED = {"dorsal_bridge", "forward_sensor_shell", "aft_sensor_shell"}


def main():
    prior = saved("A6_SketchedEnds_Bare.step")
    a2 = saved("A2_OpenSides_Bare.step")
    bare = saved("A7_LevelBeam_Bare.step")
    full = saved("A7_LevelBeam_Filled.step")
    assert len(bare) == len(prior) == 11 and len(full) == 15
    assert set(bare) == set(prior) == set(full)-BOXES
    for name, part in bare.items():
        same(part, full[name])
        if name not in CHANGED:
            same(part, prior[name])
    same(bare["dorsal_bridge"], a2["dorsal_bridge"])
    roof = bare["dorsal_bridge"]
    assert roof.is_inside((1200, 0, -2)), "center beam is not level through nose root"
    assert bare["forward_sensor_shell"].is_inside((1326, 0, -2))
    assert bare["aft_sensor_shell"].is_inside((-1326, 0, -2))
    for name in ("forward_sensor_shell", "aft_sensor_shell"):
        new, old = bare[name], prior[name]
        assert (new-old).volume > 1 or (old-new).volume > 1, (name, "unsmoothed")
    for end in ("forward", "aft"):
        shell, aperture = bare[f"{end}_sensor_shell"], bare[f"{end}_aperture"]
        assert intersection(shell, aperture) < .001
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
    for state in (bare, full):
        spans = [limits(item) for item in state.values()]
        bounds = [round(max(b[i][1] for b in spans)-min(b[i][0] for b in spans), 3)
                  for i in range(3)]
        assert bounds == [3500., 400., 223.], bounds
    radius, length = saved_spear()
    assert abs(length-1200) < .002 and abs(radius*2-158.013) < .02
    result = {"ok": True, "bare_parts": len(bare), "filled_parts": len(full),
              "outer_xyz_mm": [3500, 400, 223],
              "A2_level_roof_restored": True,
              "A6_sensors_apertures_side_lips_and_boxes_preserved_except_smooth_shells": True,
              "spear_max_fin_diameter_mm": round(radius*2, 3),
              "donor_door_aircraft_fit_verified": False}
    (ROOT / "reviews" / "A7_LevelBeam_Checks.json").write_text(
        json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
