"""Independent serialized A-study check; no source-model factory imported."""

import json
import math
from itertools import combinations
from pathlib import Path

from cadgen import read_step
from cadgen.geometry import boundary_edges, topology_errors


ROOT = Path(__file__).resolve().parents[1]
SPEAR = ROOT.parent / "palisade_interceptor" / "STEP" / "Spear_ACMWrap.step"


def saved(name):
    shape = read_step(ROOT / "STEP" / name)
    result = {part.label: part for part in shape.children}
    assert len(result) == len(shape.children), (name, "duplicate labels")
    assert all(part.is_valid and len(part.solids()) == 1 and part.volume > 0
               for part in result.values()), (name, "invalid solids")
    for label, part in result.items():
        assert not topology_errors(part), (name, label, "topology errors")
        assert len(part.shells()) == 1 and not boundary_edges(part.shells()[0]), (
            name, label, "open shell")
    return result


def limits(part):
    box = part.bounding_box()
    return ((box.min.X, box.max.X), (box.min.Y, box.max.Y), (box.min.Z, box.max.Z))


def intersection(a, b):
    # Bounding-box early out avoids many irrelevant OCCT booleans.
    pa, pb = limits(a), limits(b)
    if any(max(x[0], y[0]) >= min(x[1], y[1]) - 0.0001 for x, y in zip(pa, pb)):
        return 0.0
    common = a & b
    return common.volume if common is not None else 0.0


def same(a, b):
    assert abs(a.volume - b.volume) < 0.001
    assert (a-b).volume < 0.001 and (b-a).volume < 0.001


def main():
    bare = saved("A_Bridge_Bare.step")
    filled = saved("A_Bridge_Filled.step")
    assert len(bare) == 11 and len(filled) == 15
    assert set(bare) == set(filled) - {
        "cassette_aft_port", "cassette_aft_starboard",
        "cassette_forward_port", "cassette_forward_starboard"}
    for name, part in bare.items():
        same(part, filled[name])

    boxes = {key: value for key, value in filled.items() if key.startswith("cassette_")}
    centers = {}
    for name, box in boxes.items():
        spans = limits(box)
        assert all(abs((b-a)-target) < .01 for (a, b), target in
                   zip(spans, (1310, 180, 180))), (name, spans)
        center = tuple(round((a+b)/2, 3) for a, b in spans)
        centers[name] = center
        assert center[0] in (-664., 664.) and center[1] in (-95., 95.)
        assert center[2] == -133.
        # Bottom face is an exit datum: the lower half-space at this Y/X
        # contains neither a housing part nor a second-tier cassette.
        for other_name, other in filled.items():
            if other_name == name:
                continue
            assert intersection(box, other) < 0.001, (name, other_name, "overlap")
            ox, oy, oz = limits(other)
            if ox[0] < center[0] < ox[1] and oy[0] < center[1] < oy[1]:
                assert oz[0] >= -223 - .01, (name, other_name, "blocked underside")
    assert len(set(centers.values())) == 4
    assert len({round(box.volume, 3) for box in boxes.values()}) == 1
    for a, b in combinations(boxes.values(), 2):
        assert intersection(a, b) == 0

    spear = saved_spear()
    radius, length = spear
    assert abs(length-1200) < .002 and abs(2*radius-158.013) < .02
    # Example allowance: 6 mm per cassette side/end. Vertical cavity 168 mm.
    wall = 6.
    inner_y = 180-2*wall
    inner_x = 1310-2*wall
    inner_z = 180-2*wall
    transverse_margin = (min(inner_y, inner_z)-2*radius)/2
    axial_margin = (inner_x-length)/2
    assert transverse_margin > 0 and axial_margin > 0
    port, starboard = limits(boxes["cassette_aft_port"]), limits(boxes["cassette_aft_starboard"])
    aft, fore = limits(boxes["cassette_aft_port"]), limits(boxes["cassette_forward_port"])
    transverse_skin_gap = starboard[1][0]-port[1][1]
    axial_skin_gap = fore[0][0]-aft[0][1]
    assert abs(transverse_skin_gap-10) < .01 and abs(axial_skin_gap-18) < .01

    all_bounds = [limits(part) for part in filled.values()]
    outer = tuple((min(b[i][0] for b in all_bounds), max(b[i][1] for b in all_bounds))
                  for i in range(3))
    dimensions = [round(b-a, 3) for a, b in outer]
    assert dimensions == [2980., 400., 223.]
    assert all(abs(limits(part)[2][0]+223) < .01 for name, part in filled.items()
               if name.startswith("cassette_") or name.endswith("_outer_rail")
               or name.endswith("_sensor_shell")), "underside is not flush"
    for end in ("forward", "aft"):
        shell = bare[f"{end}_sensor_shell"]
        aperture = bare[f"{end}_aperture"]
        assert intersection(shell, aperture) < .001
        assert abs(aperture.bounding_box().size.Y-105) < .01
    assert abs(bare["dorsal_bridge"].bounding_box().size.Z-30) < .01
    for side in ("port", "starboard"):
        assert intersection(bare["dorsal_bridge"], bare[f"{side}_outer_rail"]) > 0
    assert abs(bare["starboard_outer_rail"].bounding_box().size.Y-14) < .01

    result = {"ok": True, "bare_parts": len(bare), "filled_parts": len(filled),
              "outer_xyz_mm": dimensions, "four_centers_xyz_mm": centers,
              "spear_length_mm": round(length, 3), "spear_fin_diameter_mm": round(2*radius, 3),
              "study_cassette_wall_mm": wall,
              "minimum_sample_transverse_inner_margin_mm": round(transverse_margin, 3),
              "minimum_sample_axial_inner_margin_mm": round(axial_margin, 3),
              "measured_transverse_skin_gap_mm": round(transverse_skin_gap, 3),
              "measured_axial_skin_gap_mm": round(axial_skin_gap, 3),
              "actual_AGM2_stations_door_sweeps_pylon_aircraft_fit_verified": False}
    path = ROOT / "reviews" / "A_Bridge_Checks.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


def saved_spear():
    shape = read_step(SPEAR)
    assert len(shape.children) == 199
    parts = shape.children
    min_x = min(item.bounding_box().min.X for item in parts)
    max_x = max(item.bounding_box().max.X for item in parts)
    radius = max(math.hypot(vertex.Y, vertex.Z)
                 for item in parts for vertex in item.tessellate(.2)[0])
    return radius, max_x-min_x


if __name__ == "__main__":
    main()
