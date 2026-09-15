"""Independent deterministic checks for the RDM-9 Phantom STEP candidates."""

import json
from math import sqrt
from pathlib import Path

from cadgen import build123d as bd, read_step


ROOT = Path(__file__).parent
NOSE_X = 1400.0
TAIL_X = -1400.0
BODY_DIAMETER = 225.0
ENVELOPE_RADIUS = 125.0
TOL = 1e-4
VOLUME_TOL = 1e-3
EXPECTED_LABELS = {"body", "lens_housing", "nozzle_lip", "nozzle_recess"}
CANDIDATES = (180, 220, 260)


def intersection_volume(left, right):
    intersection = left & right
    return 0.0 if intersection is None else intersection.volume


def measured_max_radius(part, tolerance=0.35):
    vertices, _ = part.tessellate(tolerance)
    return max(sqrt(vertex.Y * vertex.Y + vertex.Z * vertex.Z) for vertex in vertices)


def check_candidate(lens_width):
    path = ROOT / f"RDM-9_Phantom_Lens{lens_width}.step"
    model = read_step(path)
    parts = {part.label: part for part in model.children}
    expected_model_label = f"RDM-9_Phantom_Lens{lens_width}"

    assert model.label == expected_model_label, f"Unexpected model label: {model.label!r}"
    assert len(parts) == len(model.children), f"{path.name}: duplicate child labels"
    assert set(parts) == EXPECTED_LABELS, f"{path.name}: labels {sorted(parts)}"
    for label, part in parts.items():
        assert len(part.solids()) == 1, f"{path.name}/{label}: expected one closed solid"
        assert part.is_valid, f"{path.name}/{label}: invalid BREP"
        assert part.volume > 0.0, f"{path.name}/{label}: nonpositive volume"

    bounds = model.bounding_box()
    assert abs(bounds.min.X - TAIL_X) < TOL, f"{path.name}: tail datum {bounds.min.X}"
    assert abs(bounds.max.X - NOSE_X) < TOL, f"{path.name}: nose datum {bounds.max.X}"
    assert abs(bounds.size.X - 2800.0) < TOL, f"{path.name}: length {bounds.size.X}"
    assert abs(bounds.center().Y) < TOL and abs(bounds.center().Z) < TOL, (
        f"{path.name}: off-axis envelope center"
    )
    assert bounds.min.Y >= -ENVELOPE_RADIUS - TOL and bounds.max.Y <= ENVELOPE_RADIUS + TOL
    assert bounds.min.Z >= -ENVELOPE_RADIUS - TOL and bounds.max.Z <= ENVELOPE_RADIUS + TOL

    envelope = bd.Cylinder(ENVELOPE_RADIUS, 2804.0).rotate(bd.Axis.Y, 90.0)
    for label, part in parts.items():
        protrusion = part - envelope
        assert protrusion is None or protrusion.volume < VOLUME_TOL, (
            f"{path.name}/{label}: exceeds the 250 mm diameter envelope"
        )

    body_bounds = parts["body"].bounding_box()
    assert abs(body_bounds.size.Y - BODY_DIAMETER) < TOL, f"{path.name}: body Y diameter"
    assert abs(body_bounds.size.Z - BODY_DIAMETER) < TOL, f"{path.name}: body Z diameter"
    lens_bounds = parts["lens_housing"].bounding_box()
    assert abs(lens_bounds.size.X - lens_width) < TOL, (
        f"{path.name}: lens width {lens_bounds.size.X}"
    )
    assert abs(lens_bounds.size.Y - 250.0) < TOL, f"{path.name}: lens Y diameter"
    assert abs(lens_bounds.size.Z - 250.0) < TOL, f"{path.name}: lens Z diameter"
    assert abs(lens_bounds.center().X) < TOL, f"{path.name}: lens not centered at X=0"

    assert parts["lens_housing"].distance_to(parts["body"]) < TOL, (
        f"{path.name}: lens housing floats"
    )
    assert parts["nozzle_lip"].distance_to(parts["body"]) < TOL, (
        f"{path.name}: nozzle lip floats"
    )
    assert parts["nozzle_recess"].distance_to(parts["body"]) < TOL, (
        f"{path.name}: nozzle backing floats"
    )

    mouth_probe = bd.Box(8.0, 12.0, 12.0).translate((-1382.0, 0.0, 0.0))
    mouth_hits = [
        label
        for label, part in parts.items()
        if intersection_volume(part, mouth_probe) > VOLUME_TOL
    ]
    assert not mouth_hits, f"{path.name}: nozzle mouth blocked by {mouth_hits}"

    backing_probe = bd.Box(2.0, 12.0, 12.0).translate((-1357.0, 0.0, 0.0))
    assert intersection_volume(parts["nozzle_recess"], backing_probe) > 200.0, (
        f"{path.name}: dark nozzle backing is absent"
    )
    assert intersection_volume(parts["body"], backing_probe) < VOLUME_TOL, (
        f"{path.name}: body closes across dark nozzle backing"
    )

    max_radii = {label: round(measured_max_radius(part), 3) for label, part in parts.items()}
    report = {
        "file": path.name,
        "label": model.label,
        "part_count": len(parts),
        "labels": sorted(parts),
        "lens_width_mm": lens_width,
        "model_bbox_mm": {
            "min": list(bounds.min),
            "max": list(bounds.max),
            "size": list(bounds.size),
        },
        "measured_max_radius_mm": max_radii,
        "nozzle_mouth_probe_blocked_by": mouth_hits,
    }
    print(
        f"PASS: {path.name} -- 4 labeled solids, 2800.0 mm length, "
        f"{lens_width} mm lens width, radius <= 125.0 mm, open blind nozzle."
    )
    return report


def main():
    reports = [check_candidate(width) for width in CANDIDATES]
    output = {
        "ok": True,
        "datums_mm": {"nose_x": NOSE_X, "tail_x": TAIL_X, "origin_x": 0.0},
        "body_diameter_mm": BODY_DIAMETER,
        "envelope_diameter_mm": ENVELOPE_RADIUS * 2.0,
        "candidates": reports,
        "scope": "Phantom exterior silhouette; aircraft rack fit and Unity runtime not verified",
    }
    (ROOT / "RDM-9_Phantom_Checks.json").write_text(
        json.dumps(output, indent=2) + "\n",
        encoding="utf-8",
    )
    print("PASS: all Phantom silhouette checks; wrote RDM-9_Phantom_Checks.json")


if __name__ == "__main__":
    main()
