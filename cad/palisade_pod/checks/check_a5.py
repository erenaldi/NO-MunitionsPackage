"""A5 front-cover study: independently read serialized states and A4 baseline."""

import json
from pathlib import Path

from check_a import intersection, limits, same, saved, saved_spear


ROOT = Path(__file__).resolve().parents[1]


def main():
    baseline = saved("A4_LongFront_Bare.step")
    bare = saved("A5_ShoulderFront_Bare.step")
    full = saved("A5_ShoulderFront_Filled.step")
    boxes = {key: part for key, part in full.items() if key.startswith("cassette_")}
    assert len(baseline) == len(bare) == 11 and len(full) == 15
    assert set(bare) == set(baseline) == set(full)-set(boxes)
    for key, part in bare.items():
        same(part, full[key])
        if key != "dorsal_bridge":
            same(part, baseline[key])
    roof = bare["dorsal_bridge"]
    old_roof = baseline["dorsal_bridge"]
    assert (old_roof-roof).volume < .01, "A4 roof material lost"
    assert (roof-old_roof).volume > 10000, "missing long front cover"
    assert roof.is_inside((500, 0, -2))
    assert not roof.is_inside((700, 0, 15)), "raised shoulder began too early"
    assert roof.is_inside((810, 0, 20)), "raised shoulder absent"
    assert not roof.is_inside((810, 0, 30)), "excess above sample roof"
    assert roof.is_inside((1150, 0, 11)), "shoulder does not span foredeck"
    assert not roof.is_inside((1324, 0, 0)), "nose junction remains full height"
    for side in ("port", "starboard"):
        assert intersection(roof, bare[f"{side}_outer_rail"]) > .01
    for name, part in boxes.items():
        assert round(part.bounding_box().size.Y, 3) == 196
        for frame_name, frame in bare.items():
            assert intersection(part, frame) < .001, (name, frame_name)
    dims = []
    for state in (bare, full):
        spans = [limits(shape) for shape in state.values()]
        size = [round(max(b[i][1] for b in spans)-min(b[i][0] for b in spans), 3)
                for i in range(3)]
        assert size == [2980., 400., 251.], size
        dims = size
    radius, length = saved_spear()
    assert abs(length-1200) < .002 and abs(radius*2-158.013) < .02
    result = {"ok": True, "bare_parts": len(bare), "filled_parts": len(full),
              "outer_xyz_mm": dims, "foredeck_start_end_x_mm": [740, 1325],
              "front_sensor_end_x_mm": 1490,
              "front_cover_is_additive_to_A4_roof": True,
              "A4_front_sensor_rear_sensor_lips_and_four_boxes_identical": True,
              "spear_max_fin_diameter_mm": round(2*radius, 3),
              "donor_door_sweep_aircraft_fit_verified": False}
    (ROOT / "reviews" / "A5_ShoulderFront_Checks.json").write_text(
        json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
