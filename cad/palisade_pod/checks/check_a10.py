"""Artifact-side A10 nodding-nose, stubby-rear silhouette boundary."""

import json
from pathlib import Path

from cadgen import build123d as bd

from check_a import intersection, limits, same, saved, saved_spear


ROOT = Path(__file__).resolve().parents[1]
BOXES = {f"cassette_{row}_{side}" for row in ("aft", "forward")
         for side in ("port", "starboard")}
OUTER = (3553., 400., 223.)
FRONT_TIP_CENTRE = -217.


def slice_span(shape, x):
    slice_ = shape & bd.Box(.05, 500, 500).translate((x, 0, -111.5))
    assert slice_ is not None and slice_.volume > 0
    bounds = slice_.bounding_box()
    return (round(bounds.size.Y, 3), round(bounds.size.Z, 3),
            round(bounds.min.Z, 3), round(bounds.max.Z, 3))


def main():
    old = saved("A9_ContinuousEnds_Bare.step")
    bare = saved("A10_DroopedEnds_Bare.step")
    full = saved("A10_DroopedEnds_Filled.step")
    assert len(bare) == 9 and len(full) == 13
    assert set(bare) == set(old)
    assert set(full)-set(bare) == BOXES
    for name, shape in bare.items():
        same(shape, full[name])
        if name not in ("forward_sensor_shell", "aft_sensor_shell"):
            same(shape, old[name])
    assert not any("aperture" in name for name in full)
    assert all(abs(a-b) < .01 for a, b in
               zip(limits(bare["forward_sensor_shell"])[0], (1325, 1883)))
    assert all(abs(a-b) < .01 for a, b in
               zip(limits(bare["aft_sensor_shell"])[0], (-1670, -1325)))
    tips = {"forward": slice_span(bare["forward_sensor_shell"], 1882.97),
            "aft": slice_span(bare["aft_sensor_shell"], -1669.97)}
    for width, height, _, _ in tips.values():
        assert width < 30 and height < 16, tips
    fwd = tips["forward"]
    assert abs((fwd[2]+fwd[3])/2 - FRONT_TIP_CENTRE) < 3, tips
    assert fwd[3] < -195 and fwd[2] > -224.5, tips
    assert abs((tips["aft"][2]+tips["aft"][3])/2 + 111.5) < 4, tips
    nose = bare["forward_sensor_shell"]
    dome_roof_min = {1450.: -12., 1550.: -30., 1760.: -125., 1850.: -205.}
    for x, roof_min in dome_roof_min.items():
        _, _, low, high = slice_span(nose, x)
        assert -223.5 <= low and high <= .5, (x, low, high)
        assert high >= roof_min, (x, "roof dived below the dome", high)
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
        assert all(abs(d-t) < .5 for d, t in zip(dims, OUTER)), dims
    radius, length = saved_spear()
    assert abs(length-1200) < .002 and abs(radius*2-158.013) < .02
    report = {"ok": True, "bare_parts": len(bare), "filled_parts": len(full),
              "outer_xyz_mm": [3553, 400, 223],
              "tip_section_yz_zmin_zmax_mm": tips,
              "forward_tip_centre_z_mm": round((fwd[2]+fwd[3])/2, 3),
              "roof_law": "roof=-211mm*t^3, belly flush -223, blunt 24x12 tip",
              "roof_drop_mm": 211,
              "belly_flush_with_beam_underside": True,
              "front_fairing_length_mm": 558,
              "rear_shortening_mm": 40,
              "A9_roof_lips_four_boxes_preserved": True,
              "sensor_aperture_art_deferred": True,
              "spear_max_fin_diameter_mm": round(2*radius, 3),
              "donor_aircraft_door_clearance_verified": False}
    (ROOT / "reviews" / "A10_DroopedEnds_Checks.json").write_text(
        json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
