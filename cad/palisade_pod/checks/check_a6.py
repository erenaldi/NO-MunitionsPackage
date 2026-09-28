"""Saved STEP checks for the user's two-end side-silhouette markup."""

import json
from pathlib import Path

from check_a import intersection, limits, same, saved, saved_spear


ROOT = Path(__file__).resolve().parents[1]
BOXES = {f"cassette_{row}_{side}" for row in ("aft", "forward")
         for side in ("port", "starboard")}
CHANGED = {"forward_sensor_shell", "aft_sensor_shell",
           "forward_aperture", "aft_aperture"}


def main():
    old = saved("A4_LongFront_Bare.step")
    bare = saved("A6_SketchedEnds_Bare.step")
    full = saved("A6_SketchedEnds_Filled.step")
    assert len(bare) == len(old) == 11 and len(full) == 15
    assert set(bare) == set(old) == set(full)-BOXES
    for name, part in bare.items():
        same(part, full[name])
        if name not in CHANGED:
            same(part, old[name])

    front, aft = bare["forward_sensor_shell"], bare["aft_sensor_shell"]
    assert all(abs(a-b) < .01 for a, b in zip(limits(front)[0], (1325, 1790)))
    assert all(abs(a-b) < .01 for a, b in zip(limits(aft)[0], (-1710, -1325)))
    assert abs(limits(front)[0][1]-limits(old["forward_sensor_shell"])[0][1]-300) < .01
    assert abs(limits(old["aft_sensor_shell"])[0][0]-limits(aft)[0][0]-220) < .01

    # Independent section probes check lowered/blunted tips and both outward
    # apertures without assuming a drawing pixel is a physical dimension.
    assert front.is_inside((1778, 0, -117))
    assert not front.is_inside((1778, 0, -72))
    assert not front.is_inside((1778, 0, -161))
    assert aft.is_inside((-1700, 0, -112))
    assert not aft.is_inside((-1700, 0, -63))
    for end, shell in (("forward", front), ("aft", aft)):
        aperture = bare[f"{end}_aperture"]
        assert intersection(shell, aperture) < .001
        assert round(aperture.bounding_box().size.Y, 3) == 105
        assert round(aperture.bounding_box().size.Z, 3) == 32
    assert bare["forward_aperture"].is_inside((1787.5, 0, -117))
    assert bare["aft_aperture"].is_inside((-1707.5, 0, -112))

    for name in BOXES:
        part = full[name]
        assert tuple(round(b-a, 3) for a, b in limits(part)) == (1310, 196, 180)
        assert limits(part)[2] == (-223., -43.)
        for other_name, other in full.items():
            if name != other_name:
                assert intersection(part, other) < .001, (name, other_name)
        x, y, _ = ((a+b)/2 for a, b in limits(part))
        for frame_name, frame in bare.items():
            bx, by, bz = limits(frame)
            if bx[0] < x < bx[1] and by[0] < y < by[1]:
                assert bz[0] >= -223-.01, (name, frame_name, "drop blocked")
    for state in (bare, full):
        bboxes = [limits(item) for item in state.values()]
        xyz = [round(max(b[i][1] for b in bboxes)-min(b[i][0] for b in bboxes), 3)
               for i in range(3)]
        assert xyz == [3500., 400., 223.], xyz
    radius, length = saved_spear()
    assert abs(length-1200) < .002 and abs(radius*2-158.013) < .02
    result = {"ok": True, "bare_parts": len(bare), "filled_parts": len(full),
              "outer_xyz_mm": [3500, 400, 223], "forward_extension_mm": 300,
              "aft_extension_mm": 220, "front_tip_width_height_mm": [140, 53],
              "aft_tip_width_height_mm": [160, 70],
              "A4_roof_side_lips_four_boxes_preserved": True,
              "spear_fin_diameter_mm": round(radius*2, 3),
              "illustrative_width_margin_per_side_with_6mm_walls_mm":
                  round((196-12-2*radius)/2, 3),
              "actual_aircraft_and_door_clearance_verified": False}
    (ROOT / "reviews" / "A6_SketchedEnds_Checks.json").write_text(
        json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
