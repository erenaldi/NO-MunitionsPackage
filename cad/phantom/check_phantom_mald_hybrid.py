"""Independent deterministic checks for the compact MALD-inspired Phantom."""

import json
from math import pi, sqrt
from pathlib import Path

from cadgen import build123d as bd, read_step


ROOT = Path(__file__).parent
STEP_PATH = ROOT / "RDM-9_Phantom_MALD_Hybrid.step"
EXPECTED_MODEL_LABEL = "RDM-9_Phantom_MALD_Hybrid"
EXPECTED_LABELS = {
    "smooth_body",
    "rf_panel_port",
    "rf_panel_starboard",
    "midwing_port",
    "midwing_starboard",
    "tailplane_port",
    "tailplane_starboard",
    "dorsal_fin",
    "ventral_keel",
    "nozzle_lip",
    "nozzle_recess",
}
CONTACT_PARTS = EXPECTED_LABELS - {"smooth_body"}
PAIRS = (
    ("rf_panel_port", "rf_panel_starboard"),
    ("midwing_port", "midwing_starboard"),
    ("tailplane_port", "tailplane_starboard"),
)
TOL = 1e-4
VOLUME_TOL = 1e-3
ENVELOPE_RADIUS = 125.0
DESIGN_RADIUS = 124.0


def intersection_volume(left, right):
    intersection = left & right
    return 0.0 if intersection is None else intersection.volume


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
    model = read_step(STEP_PATH)
    parts = {part.label: part for part in model.children}
    assert model.label == EXPECTED_MODEL_LABEL
    assert len(parts) == len(model.children), "duplicate child labels"
    assert set(parts) == EXPECTED_LABELS, f"labels: {sorted(parts)}"

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
    radii = {}
    for label, part in parts.items():
        protrusion = part - envelope
        assert protrusion is None or protrusion.volume < VOLUME_TOL, (
            f"{label}: exceeds 125 mm radial envelope"
        )
        radii[label] = round(max_radius(part), 3)

    body = parts["smooth_body"]
    body_bounds = body.bounding_box()
    assert body_bounds.size.Y > body_bounds.size.Z + 30.0, (
        f"body must read broad and shallow: {body_bounds.size.Y} x {body_bounds.size.Z} mm"
    )

    nose_probe = bd.Box(4.0, 30.0, 24.0).translate((1398.0, 0.0, 0.0))
    nose_probe_volume = intersection_volume(body, nose_probe)
    assert nose_probe_volume > 2500.0, f"nose cap too sharp: {nose_probe_volume} mm^3"

    midbody_slab = bd.Box(2.0, 240.0, 200.0).translate((0.0, 0.0, 0.0))
    midbody_section_area = intersection_volume(body, midbody_slab) / 2.0
    expected_ellipse_area = pi * 100.0 * 77.0
    assert abs(midbody_section_area - expected_ellipse_area) < expected_ellipse_area * 0.005, (
        f"midbody is not the specified smooth ellipse: {midbody_section_area} mm^2"
    )
    corner_probe = bd.Box(2.0, 2.0, 2.0).translate((0.0, 90.0, 50.0))
    assert intersection_volume(body, corner_probe) < VOLUME_TOL, "midbody retains angular shoulders"

    design_envelope = bd.Cylinder(DESIGN_RADIUS, 2804.0).rotate(bd.Axis.Y, 90.0)
    for label in EXPECTED_LABELS:
        protrusion = parts[label] - design_envelope
        assert protrusion is None or protrusion.volume < VOLUME_TOL, (
            f"{label}: exceeds 124 mm design envelope"
        )

    for label in CONTACT_PARTS:
        assert parts[label].distance_to(body) < TOL, f"{label}: no body contact"
    for left_label, right_label in PAIRS:
        assert_mirrored(parts[left_label], parts[right_label])
    wing_panel_gaps = {}
    for wing_label, panel_label in (
        ("midwing_port", "rf_panel_port"),
        ("midwing_starboard", "rf_panel_starboard"),
    ):
        wing_bounds = parts[wing_label].bounding_box()
        panel_bounds = parts[panel_label].bounding_box()
        longitudinal_gap = panel_bounds.min.X - wing_bounds.max.X
        wing_panel_gaps[wing_label] = longitudinal_gap
        assert longitudinal_gap >= 100.0, (
            f"{wing_label}: only {longitudinal_gap} mm longitudinal clearance from {panel_label}"
        )
        assert intersection_volume(parts[wing_label], parts[panel_label]) < VOLUME_TOL, (
            f"{wing_label}: intersects {panel_label}"
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
        "file": STEP_PATH.name,
        "label": model.label,
        "part_count": len(parts),
        "labels": sorted(parts),
        "model_bbox_mm": {
            "min": list(bounds.min),
            "max": list(bounds.max),
            "size": list(bounds.size),
        },
        "maximum_radius_mm": radii,
        "body_aspect_mm": {
            "width": body_bounds.size.Y,
            "height": body_bounds.size.Z,
        },
        "nose_cap_probe_volume_mm3": nose_probe_volume,
        "midbody_section_area_mm2": midbody_section_area,
        "expected_elliptical_section_area_mm2": expected_ellipse_area,
        "design_envelope_radius_mm": DESIGN_RADIUS,
        "nozzle_mouth_probe_blocked_by": mouth_hits,
        "bilateral_pairs_checked": [list(pair) for pair in PAIRS],
        "wing_panel_longitudinal_gap_mm": wing_panel_gaps,
        "scope": "compact MALD-inspired exterior; aircraft rack fit and Unity runtime not verified",
    }
    (ROOT / "RDM-9_Phantom_MALD_Hybrid_Checks.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "PASS: RDM-9_Phantom_MALD_Hybrid.step -- 11 labeled valid solids, "
        "2800 mm length, smooth elliptical body, radius <= 125 mm, bilateral appendages, blind nozzle."
    )


if __name__ == "__main__":
    main()
