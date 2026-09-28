"""Conservative 4-round pod envelope study; not a donor-transform fit test."""

import json
import math
from pathlib import Path

from cadgen import read_step


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "STEP" / "Spear_ACMWrap.step"
NOMINAL_POD_LENGTH = 1800.  # MUNITIONS.md §12, historical visual target
NOMINAL_POD_WIDTH = 400.    # full boxy outer width / height, unverified hardware
EXAMPLE_WALL = 10.          # study assumption, not a production thickness
EXAMPLE_DIVIDER = 10.       # study assumption, not the donor's structure
EXAMPLE_CENTERS = (-90., 90.)


def max_radius(shape):
    vertices, _ = shape.tessellate(.2)
    return max(math.hypot(vertex.Y, vertex.Z) for vertex in vertices)


def main():
    model = read_step(MODEL)
    parts = {part.label: part for part in model.children}
    assert len(parts) == len(model.children) == 199
    assert {"body", "turning_cap", "main_nozzle"} <= set(parts)
    radius = max(max_radius(part) for part in parts.values())
    min_x = min(part.bounding_box().min.X for part in parts.values())
    max_x = max(part.bounding_box().max.X for part in parts.values())
    length = max_x-min_x
    assert abs(length-1200.) < .002
    assert 78.9 < radius < 79.1
    gap_axial = NOMINAL_POD_LENGTH-length
    half_inner_square = NOMINAL_POD_WIDTH/2-EXAMPLE_WALL
    center_abs = abs(EXAMPLE_CENTERS[0])
    adjacent_pitch = EXAMPLE_CENTERS[1]-EXAMPLE_CENTERS[0]
    square_wall_clearance = half_inner_square-(center_abs+radius)
    adjacent_gap = adjacent_pitch-2*radius
    square_residual_divider = adjacent_gap-EXAMPLE_DIVIDER
    circular_wall_clearance = (NOMINAL_POD_WIDTH/2-EXAMPLE_WALL)-(
        math.hypot(center_abs, center_abs)+radius)
    min_circle_diameter_with_walls = 2*(
        math.sqrt(2)*(radius+EXAMPLE_DIVIDER/2)+radius+EXAMPLE_WALL)

    assert gap_axial > 0
    assert square_wall_clearance > 0 and square_residual_divider > 0
    assert circular_wall_clearance < 0 and min_circle_diameter_with_walls > NOMINAL_POD_WIDTH
    result = {
        "source_step": MODEL.name,
        "measured_interceptor_length_mm": round(length, 3),
        "measured_radial_envelope_mm": round(radius, 3),
        "measured_diameter_envelope_mm": round(radius*2, 3),
        "nominal_pod_length_mm": NOMINAL_POD_LENGTH,
        "nominal_box_outer_width_height_mm": NOMINAL_POD_WIDTH,
        "nominal_axial_surplus_mm": round(gap_axial, 3),
        "study_wall_mm": EXAMPLE_WALL,
        "study_internal_divider_mm": EXAMPLE_DIVIDER,
        "study_square_cell_center_y_z_mm": [[y,z] for y in EXAMPLE_CENTERS for z in EXAMPLE_CENTERS],
        "box_square_pack_min_inner_wall_clearance_mm": round(square_wall_clearance, 3),
        "box_adjacent_envelope_gap_mm": round(adjacent_gap, 3),
        "box_gap_after_example_divider_mm": round(square_residual_divider, 3),
        "round_400mm_shell_study_wall_clearance_mm": round(circular_wall_clearance, 3),
        "round_shell_min_outer_diameter_for_example_walls_mm": round(min_circle_diameter_with_walls, 3),
        "donor_launcher_local_transforms_verified": False,
        "pod_skin_and_door_sweep_verified": False,
        "note": "Geometric bounding-circle packing only; not a saved AGM2_6Pod placement/clearance result."
    }
    path = ROOT / "reviews" / "spear_pod_envelope_feasibility.json"
    path.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print("PASS: numerical concept envelope; square 2x2 fits study assumptions, round shell does not")


if __name__ == "__main__":
    main()
