"""Independent deterministic checks for the round-2 Phantom candidates.

Usage: python check_phantom_r2.py <sled|rails|dart>

Gates added by the 2026-09-20 adversarial review, each mapped to a defect that
shipped in the round-1 hybrid:

- body bbox clamp: the non-ruled loft must not crown past the 200 x 154 mm
  spec section (the hybrid measured 209.87 x 155.11 mm);
- nozzle flushness: (nozzle_lip - smooth_body) must be empty, so the ring can
  never stand proud of the tail face the way the 60 mm lip did on the
  56 mm tail semi-minor;
- wedge gates: blunt cap material near the tip plus upper-dominant material
  at the nose slab, encoding the upward-wedge art direction;
- pylon-pad clearance: no part may enter the dorsal carriage mockup zone;
- root engagement: every appendage must overlap the body wall by a real
  volume, not merely touch it (the round-1 tailplane root gap);
- the carried-over gates: datums, 125/124 mm envelopes, broad-shallow aspect,
  midbody ellipse area, open mouth, blind backing, mirrored pairs.
"""

import json
import sys
from math import pi, sqrt
from pathlib import Path

from cadgen import build123d as bd, read_step


ROOT = Path(__file__).parent

CANDIDATES = {
    "sled": {
        "step": "RDM-9_Phantom_R2_Sled.step",
        "label": "RDM-9_Phantom_R2_Sled",
        "pairs": (
            ("wing_panel_port", "wing_panel_starboard"),
            ("rf_emitter_port", "rf_emitter_starboard"),
            ("tailplane_port", "tailplane_starboard"),
        ),
        "rooted": (
            "wing_panel_port",
            "wing_panel_starboard",
            "tailplane_port",
            "tailplane_starboard",
            "dorsal_spine",
            "ventral_keel",
        ),
        "touch_only": ("nozzle_recess",),
        "extra_contact": (("rf_emitter_port", "wing_panel_port"), ("rf_emitter_starboard", "wing_panel_starboard")),
    },
    "rails": {
        "step": "RDM-9_Phantom_R2_Rails.step",
        "label": "RDM-9_Phantom_R2_Rails",
        "pairs": (
            ("midwing_port", "midwing_starboard"),
            ("rf_panel_port", "rf_panel_starboard"),
            ("tailplane_port", "tailplane_starboard"),
        ),
        "rooted": (
            "midwing_port",
            "midwing_starboard",
            "rf_panel_port",
            "rf_panel_starboard",
            "tailplane_port",
            "tailplane_starboard",
            "dorsal_fin",
            "ventral_keel",
        ),
        "touch_only": ("nozzle_recess",),
        "extra_contact": (),
        "gap_gate": ("midwing_port", "rf_panel_port", "midwing_starboard", "rf_panel_starboard"),
    },
    "dart": {
        "step": "RDM-9_Phantom_R2_Dart.step",
        "label": "RDM-9_Phantom_R2_Dart",
        "pairs": (
            ("tail_fin_port", "tail_fin_starboard"),
            ("rf_panel_port", "rf_panel_starboard"),
        ),
        "rooted": (
            "tail_fin_port",
            "tail_fin_starboard",
            "rf_panel_port",
            "rf_panel_starboard",
            "dorsal_fin",
            "ventral_fin",
        ),
        "touch_only": ("nozzle_recess",),
        "extra_contact": (),
    },
}

TOL = 1e-4
VOLUME_TOL = 1e-3
ENVELOPE_RADIUS = 125.0
DESIGN_RADIUS = 124.0
BODY_WIDTH_MAX = 201.5
BODY_HEIGHT_MAX = 155.5
ROOT_ENGAGEMENT_MM3 = 500.0
PAD = {"x_aft": -350.0, "x_fore": 350.0, "y_half": 40.0, "z_bottom": 78.0, "z_top": 132.0}


def intersection_volume(left, right):
    intersection = left & right
    return 0.0 if intersection is None else intersection.volume


def difference_volume(left, right):
    difference = left - right
    return 0.0 if difference is None else difference.volume


def max_radius(part, tolerance=0.3):
    vertices, _ = part.tessellate(tolerance)
    return max(sqrt(vertex.Y * vertex.Y + vertex.Z * vertex.Z) for vertex in vertices)


def assert_mirrored(left, right):
    left_bounds = left.bounding_box()
    right_bounds = right.bounding_box()
    assert abs(left.volume - right.volume) < VOLUME_TOL
    assert abs(left_bounds.min.X - right_bounds.min.X) < TOL
    assert abs(left_bounds.max.X - right_bounds.max.X) < TOL
    assert abs(left_bounds.min.Y + right_bounds.max.Y) < TOL
    assert abs(left_bounds.max.Y + right_bounds.min.Y) < TOL
    assert abs(left_bounds.min.Z - right_bounds.min.Z) < TOL
    assert abs(left_bounds.max.Z - right_bounds.max.Z) < TOL
    mirrored = left.mirror(bd.Plane.XZ)
    left_only = mirrored - right
    right_only = right - mirrored
    assert left_only is None or left_only.volume < VOLUME_TOL
    assert right_only is None or right_only.volume < VOLUME_TOL


def main():
    candidate = sys.argv[1]
    spec = CANDIDATES[candidate]
    step_path = ROOT / spec["step"]

    model = read_step(step_path)
    parts = {part.label: part for part in model.children}
    assert model.label == spec["label"], f"model label {model.label}"
    assert len(parts) == len(model.children), "duplicate child labels"
    expected_labels = (
        {"smooth_body", "nozzle_lip", "nozzle_recess"}
        | {label for pair in spec["pairs"] for label in pair}
        | set(spec["rooted"])
        | set(spec["touch_only"])
    )
    assert set(parts) == expected_labels, f"labels: {sorted(parts)}"

    for label, part in parts.items():
        assert len(part.solids()) == 1, f"{label}: expected one closed solid"
        assert part.is_valid, f"{label}: invalid BREP"
        assert part.volume > 0.0, f"{label}: nonpositive volume"

    bounds = model.bounding_box()
    assert abs(bounds.min.X + 1400.0) < TOL, f"tail datum {bounds.min.X}"
    assert abs(bounds.max.X - 1400.0) < TOL, f"nose datum {bounds.max.X}"
    assert abs(bounds.size.X - 2800.0) < TOL, f"length {bounds.size.X}"
    assert abs(bounds.center().Y) < TOL, f"lateral center {bounds.center().Y}"
    assert bounds.min.Y >= -125.0 - TOL and bounds.max.Y <= 125.0 + TOL
    assert bounds.min.Z >= -125.0 - TOL and bounds.max.Z <= 125.0 + TOL

    envelope = bd.Cylinder(ENVELOPE_RADIUS, 2804.0).rotate(bd.Axis.Y, 90.0)
    design_envelope = bd.Cylinder(DESIGN_RADIUS, 2804.0).rotate(bd.Axis.Y, 90.0)
    radii = {}
    for label, part in parts.items():
        protrusion = part - envelope
        assert protrusion is None or protrusion.volume < VOLUME_TOL, (
            f"{label}: exceeds 125 mm radial envelope"
        )
        design_protrusion = part - design_envelope
        assert design_protrusion is None or design_protrusion.volume < VOLUME_TOL, (
            f"{label}: exceeds 124 mm design envelope"
        )
        radii[label] = round(max_radius(part), 3)

    body = parts["smooth_body"]
    body_bounds = body.bounding_box()
    assert body_bounds.size.Y <= BODY_WIDTH_MAX, (
        f"loft crowns past the 200 mm spec width: {body_bounds.size.Y}"
    )
    assert body_bounds.size.Z <= BODY_HEIGHT_MAX, (
        f"loft crowns past the 154 mm spec height: {body_bounds.size.Z}"
    )
    assert body_bounds.size.Y > body_bounds.size.Z + 30.0, (
        f"body must read broad and shallow: {body_bounds.size.Y} x {body_bounds.size.Z} mm"
    )

    midbody_slab = bd.Box(2.0, 240.0, 200.0).translate((0.0, 0.0, 0.0))
    midbody_section_area = intersection_volume(body, midbody_slab) / 2.0
    expected_ellipse_area = pi * 100.0 * 77.0
    assert abs(midbody_section_area - expected_ellipse_area) < expected_ellipse_area * 0.005, (
        f"midbody is not the specified smooth ellipse: {midbody_section_area} mm^2"
    )

    cap_probe = bd.Box(4.0, 52.0, 10.0).translate((1398.0, 0.0, 30.0))
    cap_probe_volume = intersection_volume(body, cap_probe)
    assert cap_probe_volume > 1500.0, f"nose cap too sharp: {cap_probe_volume} mm^3"

    nose_upper = bd.Box(2.0, 240.0, 80.0).translate((1340.0, 0.0, 40.0))
    nose_lower = bd.Box(2.0, 240.0, 80.0).translate((1340.0, 0.0, -40.0))
    nose_upper_volume = intersection_volume(body, nose_upper)
    nose_lower_volume = intersection_volume(body, nose_lower)
    assert nose_upper_volume > nose_lower_volume * 1.05, (
        "nose is not an upward wedge: upper "
        f"{nose_upper_volume} mm^3 vs lower {nose_lower_volume} mm^3"
    )

    lip = parts["nozzle_lip"]
    lip_protrusion = difference_volume(lip, body)
    assert lip_protrusion < 1.0, (
        f"nozzle lip stands proud of the tail face by {lip_protrusion} mm^3"
    )
    assert intersection_volume(lip, body) > 500.0, "nozzle lip does not engage the tail face"

    pad_probe = bd.Box(
        PAD["x_fore"] - PAD["x_aft"],
        PAD["y_half"] * 2.0,
        PAD["z_top"] - PAD["z_bottom"],
        align=(bd.Align.MIN, bd.Align.CENTER, bd.Align.MIN),
    ).translate((PAD["x_aft"], 0.0, PAD["z_bottom"]))
    pad_hits = [
        label for label, part in parts.items()
        if intersection_volume(part, pad_probe) > VOLUME_TOL
    ]
    assert not pad_hits, f"parts enter the dorsal pylon-pad zone: {pad_hits}"

    for label in spec["rooted"]:
        part = parts[label]
        assert part.distance_to(body) < TOL, f"{label}: no body contact"
        engagement = intersection_volume(part, body)
        assert engagement >= ROOT_ENGAGEMENT_MM3, (
            f"{label}: root engagement only {engagement} mm^3"
        )
    for label in spec["touch_only"]:
        assert parts[label].distance_to(body) < TOL, f"{label}: no body contact"
    for inner_label, host_label in spec["extra_contact"]:
        engagement = intersection_volume(parts[inner_label], parts[host_label])
        assert engagement >= 100.0, (
            f"{inner_label}: only {engagement} mm^3 engagement with {host_label}"
        )

    for left_label, right_label in spec["pairs"]:
        assert_mirrored(parts[left_label], parts[right_label])

    gaps = {}
    if "gap_gate" in spec:
        wing_label, panel_label = spec["gap_gate"][0], spec["gap_gate"][1]
        for wing_side, panel_side in ((spec["gap_gate"][0], spec["gap_gate"][1]), (spec["gap_gate"][2], spec["gap_gate"][3])):
            wing_bounds = parts[wing_side].bounding_box()
            panel_bounds = parts[panel_side].bounding_box()
            longitudinal_gap = panel_bounds.min.X - wing_bounds.max.X
            gaps[f"{wing_side}/{panel_side}"] = longitudinal_gap
            assert longitudinal_gap >= 100.0, (
                f"{wing_side}: only {longitudinal_gap} mm longitudinal clearance from {panel_side}"
            )
            assert intersection_volume(parts[wing_side], parts[panel_side]) < VOLUME_TOL, (
                f"{wing_side}: intersects {panel_side}"
            )

    mouth_probe = bd.Box(8.0, 12.0, 12.0).translate((-1370.0, 0.0, 0.0))
    mouth_hits = [
        label for label, part in parts.items()
        if intersection_volume(part, mouth_probe) > VOLUME_TOL
    ]
    assert not mouth_hits, f"nozzle mouth blocked by {mouth_hits}"
    backing_probe = bd.Box(2.0, 12.0, 12.0).translate((-1337.0, 0.0, 0.0))
    assert intersection_volume(parts["nozzle_recess"], backing_probe) > 200.0
    assert intersection_volume(body, backing_probe) < VOLUME_TOL

    result = {
        "ok": True,
        "file": step_path.name,
        "label": model.label,
        "part_count": len(parts),
        "labels": sorted(parts),
        "model_bbox_mm": {
            "min": list(bounds.min),
            "max": list(bounds.max),
            "size": list(bounds.size),
        },
        "maximum_radius_mm": radii,
        "body_bbox_mm": {
            "width": body_bounds.size.Y,
            "height": body_bounds.size.Z,
        },
        "midbody_section_area_mm2": midbody_section_area,
        "expected_elliptical_section_area_mm2": expected_ellipse_area,
        "nose_cap_probe_volume_mm3": cap_probe_volume,
        "nose_wedge_upper_lower_mm3": [nose_upper_volume, nose_lower_volume],
        "nozzle_lip_protrusion_mm3": lip_protrusion,
        "pylon_pad_zone_violations": pad_hits,
        "bilateral_pairs_checked": [list(pair) for pair in spec["pairs"]],
        "root_engagement_mm3": {
            label: round(intersection_volume(parts[label], body), 3) for label in spec["rooted"]
        },
        "longitudinal_gaps_mm": gaps,
        "scope": "silhouette candidate only; aircraft rack fit and Unity runtime not verified",
    }
    report_path = ROOT / f"RDM-9_Phantom_R2_{candidate.capitalize()}_Checks.json"
    report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {step_path.name} -- {len(parts)} labeled valid solids, "
          "clamped loft, recessed nozzle, upward wedge, pylon-clear, bilateral appendages.")


if __name__ == "__main__":
    main()
