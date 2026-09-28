"""Independent deterministic checks for the HKP-1 Palisade interceptor silhouette."""

import json
import math
from pathlib import Path

from cadgen import build123d as bd, read_step


ROOT = Path(__file__).parent
STEP_PATH = ROOT / "HKP-1_Palisade_Interceptor.step"
EXPECTED_MODEL_LABEL = "HKP-1_Palisade_Interceptor"
EXPECTED_LABELS = {
    "body",
    "turning_cap",
    "main_nozzle",
    "stabilizer_45",
    "stabilizer_135",
    "stabilizer_225",
    "stabilizer_315",
    "nozzle_0",
    "nozzle_90",
    "nozzle_180",
    "nozzle_270",
}
BODY_CONTACT = {"turning_cap", "main_nozzle"} | {
    f"stabilizer_{angle}" for angle in (45, 135, 225, 315)
}
CAP_CONTACT = {f"nozzle_{angle}" for angle in (0, 90, 180, 270)}
STAB_ORDER = ("stabilizer_45", "stabilizer_135", "stabilizer_225", "stabilizer_315")
NOZZLE_ORDER = ("nozzle_0", "nozzle_90", "nozzle_180", "nozzle_270")
TOL = 1e-4
VOLUME_TOL = 1e-3
ENVELOPE_RADIUS = 85.0
BODY_RADIUS = 70.0
CAP_LENGTH = 170.0
BODY_AFT = -600.0 + CAP_LENGTH


def intersection_volume(left, right):
    intersection = left & right
    return 0.0 if intersection is None else intersection.volume


def max_radius(part, tolerance=0.3):
    vertices, _ = part.tessellate(tolerance)
    return max(math.sqrt(vertex.Y * vertex.Y + vertex.Z * vertex.Z) for vertex in vertices)


def assert_rotated(left, right, angle):
    rotated = left.rotate(bd.Axis.X, angle)
    left_bounds = rotated.bounding_box()
    right_bounds = right.bounding_box()
    assert abs(rotated.volume - right.volume) < VOLUME_TOL
    assert abs(left_bounds.min.X - right_bounds.min.X) < TOL
    assert abs(left_bounds.max.X - right_bounds.max.X) < TOL
    assert abs(left_bounds.min.Y - right_bounds.min.Y) < TOL
    assert abs(left_bounds.max.Y - right_bounds.max.Y) < TOL
    assert abs(left_bounds.min.Z - right_bounds.min.Z) < TOL
    assert abs(left_bounds.max.Z - right_bounds.max.Z) < TOL


def centroid_azimuth(part):
    center = part.bounding_box().center()
    return math.degrees(math.atan2(center.Z, center.Y)) % 360.0


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
    assert abs(bounds.min.X + 600.0) < TOL, f"tail datum {bounds.min.X}"
    assert abs(bounds.max.X - 600.0) < TOL, f"nose datum {bounds.max.X}"
    assert abs(bounds.size.X - 1200.0) < TOL, f"length {bounds.size.X}"
    assert abs(bounds.center().Y) < TOL, f"lateral center {bounds.center().Y}"
    assert abs(bounds.center().Z) < TOL, f"vertical center {bounds.center().Z}"

    envelope = bd.Cylinder(ENVELOPE_RADIUS, 1204.0).rotate(bd.Axis.Y, 90.0)
    radii = {}
    for label, part in parts.items():
        protrusion = part - envelope
        assert protrusion is None or protrusion.volume < VOLUME_TOL, (
            f"{label}: exceeds {ENVELOPE_RADIUS} mm radial envelope"
        )
        radii[label] = round(max_radius(part), 3)

    body = parts["body"]
    cap = parts["turning_cap"]
    body_bounds = body.bounding_box()
    assert abs(body_bounds.min.X - BODY_AFT) < TOL, f"body aft datum {body_bounds.min.X}"
    assert abs(body_bounds.max.X - 600.0) < TOL, f"body nose datum {body_bounds.max.X}"
    assert abs(max_radius(body) - BODY_RADIUS) < TOL, "body radius"

    cap_bounds = cap.bounding_box()
    assert abs(cap_bounds.min.X + 600.0) < TOL, f"cap aft datum {cap_bounds.min.X}"
    assert abs(cap_bounds.max.X - BODY_AFT) < TOL, f"cap forward datum {cap_bounds.max.X}"
    assert abs(cap_bounds.size.X - CAP_LENGTH) < TOL, f"cap length {cap_bounds.size.X}"
    assert abs(max_radius(cap) - BODY_RADIUS) < TOL, "cap radius"

    for label in BODY_CONTACT:
        assert parts[label].distance_to(body) < TOL, f"{label}: no body contact"
    for label in CAP_CONTACT:
        assert parts[label].distance_to(cap) < TOL, f"{label}: no cap contact"

    for index in range(1, 4):
        assert_rotated(parts[STAB_ORDER[0]], parts[STAB_ORDER[index]], 90.0 * index)
        assert_rotated(parts[NOZZLE_ORDER[0]], parts[NOZZLE_ORDER[index]], 90.0 * index)
    for label in STAB_ORDER:
        assert abs(centroid_azimuth(parts[label]) - float(label.split("_")[1])) < 2.0, (
            f"{label}: wrong azimuth"
        )
    for label in NOZZLE_ORDER:
        assert abs(centroid_azimuth(parts[label]) - float(label.split("_")[1])) < 1.0, (
            f"{label}: wrong azimuth"
        )

    assert intersection_volume(cap, body) < VOLUME_TOL, "cap intersects body (cap must be detachable"

    mouth_probe = bd.Box(10.0, 10.0, 10.0).translate((BODY_AFT, 0.0, 0.0))
    mouth_hits = [
        label for label, part in parts.items()
        if intersection_volume(part, mouth_probe) > VOLUME_TOL
    ]
    assert set(mouth_hits) == {"turning_cap", "main_nozzle"}, (
        f"nozzle mouth not concealed solely by cap: {mouth_hits}"
    )

    recess_probe = bd.Box(10.0, 10.0, 10.0).translate((-410.0, 0.0, 0.0))
    recess_hits = [
        label for label, part in parts.items()
        if intersection_volume(part, recess_probe) > VOLUME_TOL
    ]
    assert recess_hits == ["main_nozzle"], f"recess center blocked by {recess_hits}"

    annulus_probe = bd.Box(10.0, 10.0, 10.0).translate((-410.0, 38.0, 0.0))
    annulus_hits = [
        label for label, part in parts.items()
        if intersection_volume(part, annulus_probe) > VOLUME_TOL
    ]
    assert not annulus_hits, f"recess annulus blocked by {annulus_hits}"

    nose_inner_probe = bd.Box(10.0, 10.0, 10.0).translate((565.0, 50.0, 0.0))
    nose_inner_hits = [
        label for label, part in parts.items()
        if intersection_volume(part, nose_inner_probe) > VOLUME_TOL
    ]
    assert nose_inner_hits == ["body"], f"nose not solid near tip: {nose_inner_hits}"
    nose_outer_probe = bd.Box(10.0, 10.0, 10.0).translate((565.0, 70.0, 0.0))
    nose_outer_hits = [
        label for label, part in parts.items()
        if intersection_volume(part, nose_outer_probe) > VOLUME_TOL
    ]
    assert not nose_outer_hits, f"nose not rounded (full radius at X=565): {nose_outer_hits}"

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
        "body_radius_mm": BODY_RADIUS,
        "cap_length_mm": CAP_LENGTH,
        "nozzle_mouth_probe_blocked_by": mouth_hits,
        "recess_center_probe_hits": recess_hits,
        "recess_annulus_probe_hits": annulus_hits,
        "nose_inner_probe_hits": nose_inner_hits,
        "nose_outer_probe_hits": nose_outer_hits,
        "cap_detachable": True,
        "scope": "silhouette candidate; aircraft rack fit and Unity runtime not verified",
    }
    (ROOT / "HKP-1_Palisade_Checks.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "PASS: HKP-1_Palisade_Interceptor.step -- 11 labeled valid solids, "
        "1200 mm length centered on X, radius <= 85 mm, 4-fold symmetry, "
        "cap contact, concealed recessed main nozzle, detachable cap."
    )


if __name__ == "__main__":
    main()