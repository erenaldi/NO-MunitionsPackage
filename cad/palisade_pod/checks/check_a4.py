"""Saved geometry regression for the longer, height-tapering front study."""

import json
from pathlib import Path

from check_a import intersection, limits, same, saved, saved_spear


ROOT = Path(__file__).resolve().parents[1]


def main():
    previous = saved("A3_MountFront_Bare.step")
    bare = saved("A4_LongFront_Bare.step")
    full = saved("A4_LongFront_Filled.step")
    assert len(bare) == len(previous) == 11 and len(full) == 15
    assert set(previous) == set(bare) == set(full)-{
        "cassette_aft_port", "cassette_aft_starboard",
        "cassette_forward_port", "cassette_forward_starboard"}
    for label, part in bare.items():
        same(part, full[label])
        if label not in ("dorsal_bridge", "forward_sensor_shell"):
            same(part, previous[label])
    bridge, front = bare["dorsal_bridge"], bare["forward_sensor_shell"]
    assert (bridge-previous["dorsal_bridge"]).volume < .01
    assert (previous["dorsal_bridge"]-bridge).volume > 1000
    assert (front-previous["forward_sensor_shell"]).volume < .01
    assert (previous["forward_sensor_shell"]-front).volume > 1000
    assert bridge.is_inside((500, 0, -2))
    assert not bridge.is_inside((1250, 0, -2))
    assert bridge.is_inside((1250, 0, -24))
    assert not front.is_inside((1485, 0, -45))
    assert front.is_inside((1480, 0, -115))
    assert not front.is_inside((1489, 0, -113))  # recessed sensor face
    assert bare["forward_aperture"].is_inside((1487.5, 0, -113))
    for side in ("port", "starboard"):
        assert intersection(bridge, bare[f"{side}_outer_rail"]) > .01
    assert intersection(front, bare["forward_aperture"]) < .001
    for name, part in full.items():
        if name.startswith("cassette_"):
            for frame_name, frame in bare.items():
                assert intersection(part, frame) < .001, (name, frame_name)
            assert limits(part)[2] == (-223., -43.)
    for parts in (bare, full):
        spans = [limits(item) for item in parts.values()]
        assert [round(max(b[i][1] for b in spans)-min(b[i][0] for b in spans), 3)
                for i in range(3)] == [2980., 400., 223.]
    radius, length = saved_spear()
    assert abs(length-1200) < .002 and abs(radius*2-158.013) < .02
    report = {"ok": True, "bare_parts": len(bare), "filled_parts": len(full),
              "outer_xyz_mm": [2980, 400, 223],
              "long_taper_start_end_x_mm": [649.9, 1490],
              "front_face_width_height_mm": [270, 125],
              "rear_A2_side_lips_apertures_four_boxes_preserved": True,
              "approved_spear_fin_diameter_mm": round(radius*2, 3),
              "actual_rack_door_sweep_aircraft_fit_verified": False}
    (ROOT / "reviews" / "A4_LongFront_Checks.json").write_text(
        json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
