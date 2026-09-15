"""Independent deterministic checks for the compact MALD-inspired Phantom."""

import json
from math import sqrt
from pathlib import Path

from cadgen import build123d as bd, read_step


ROOT = Path(__file__).parent
STEP_PATH = ROOT / "RDM-9_Phantom_MALD_Hybrid.step"
EXPECTED_MODEL_LABEL = "RDM-9_Phantom_MALD_Hybrid"
EXPECTED_LABELS = {
    "faceted_body",
    "rf_panel_port",
    "rf_panel_starboard",
    "dorsal_intake_cowl",
    "dorsal_intake_recess",
    "midwing_port",
    "midwing_starboard",
    "tailplane_port",
    "tailplane_starboard",
    "dorsal_fin",
    "ventral_keel",
    "nozzle_lip",
    "nozzle_recess",
}
CONTACT_PARTS = EXPECTED_LABELS - {"faceted_body"}
PAIRS = (
    ("rf_panel_port", "rf_panel_starboard"),
    ("midwing_port", "midwing_starboard"),
    ("tailplane_port", "tailplane_starboard"),
)
TOL = 1e-4
VOLUME_TOL = 1e-3
ENVELOPE_RADIUS = 125.0


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

    body = parts["faceted_body"]
    for label in CONTACT_PARTS:
        assert parts[label].distance_to(body) < TOL, f"{label}: no body contact"
    for left_label, right_label in PAIRS:
        assert_mirrored(parts[left_label], parts[right_label])
    for wing_label, panel_label in (
        ("midwing_port", "rf_panel_port"),
        ("midwing_starboard", "rf_panel_starboard"),
    ):
        assert intersection_volume(parts[wing_label], parts[panel_label]) < VOLUME_TOL, (
            f"{wing_label}: intersects {panel_label}"
        )

    intake_probe = bd.Box(12.0, 12.0, 8.0).translate((470.0, 0.0, 107.0))
    intake_hits = [
        label for label, part in parts.items()
        if intersection_volume(part, intake_probe) > VOLUME_TOL
    ]
    assert not intake_hits, f"intake aperture blocked by {intake_hits}"

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
        "intake_aperture_probe_blocked_by": intake_hits,
        "nozzle_mouth_probe_blocked_by": mouth_hits,
        "bilateral_pairs_checked": [list(pair) for pair in PAIRS],
        "scope": "compact MALD-inspired exterior; aircraft rack fit and Unity runtime not verified",
    }
    (ROOT / "RDM-9_Phantom_MALD_Hybrid_Checks.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "PASS: RDM-9_Phantom_MALD_Hybrid.step -- 13 labeled valid solids, "
        "2800 mm length, radius <= 125 mm, bilateral appendages, clear intake, blind nozzle."
    )


if __name__ == "__main__":
    main()
