"""Deterministic STEP checks for the Halberd pod/shoulder concept studies.

Independent of the generator scripts: this module reads only the exported STEP
files and verifies labels, solidity, datums, seam ownership, radius envelope,
contacts, and intake-cavity probes against the complete assembled model.

Probe stations are documented derivations from halberd_concept_shapes.py (the
hollow/cavity loft stations), but every assertion measures the actual STEP
geometry -- function parameters are never assumed to equal measured geometry.
"""

import json
from math import sqrt
from pathlib import Path

from cadgen import build123d as bd, read_step

ROOT = Path(__file__).parent
NOSE = 1683.5
TAIL = -1683.5
SEAM = -336.7
ENVELOPE_RADIUS = 220.0
TOL = 1e-4
VOLUME_TOL = 1e-3

POD = {
    "file": "Halberd_Concept_Pod.step",
    "label": "Halberd_Pod_Three_Intakes",
    "intake_prefix": "intake_pod",
    "intake_angles": (60, 180, 300),
    # Hollow loft station oval(580, 131, 29, 24): Z 107..155, Y +-29 at X=580.
    "intake_probe": (580.0, 0.0, 131.0),
    # Probe center must land inside the intake feature's own bounding box.
    "probe_anchor": "intake_pod",
    "counts": {"intake_pod": 3, "sustainer_fin": 3, "booster_fin": 3},
}

SHOULDER = {
    "file": "Halberd_Concept_Shoulder.step",
    "label": "Halberd_Shoulder_Four_Intakes",
    "intake_prefix": "intake_floor",
    "intake_angles": (45, 135, 225, 315),
    # Cavity loft station oval(535, 123, 23, 15): Z 100..146 at X=535; the
    # dark floor (top ~129) fills the lower cavity, so probe above it.
    "intake_probe": (535.0, 0.0, 137.0),
    # The cavity is cut into the hull, so the void lives inside the body bbox.
    "probe_anchor": "sustainer_body",
    "counts": {"intake_floor": 4, "sustainer_fin": 4, "booster_fin": 4},
}


def intersection_volume(left, right):
    intersection = left & right
    return 0.0 if intersection is None else intersection.volume


def measured_max_radius(part, tolerance=0.5):
    """Tessellated max radial extent; informational only, never an assertion."""
    vertices, _ = part.tessellate(tolerance)
    return max(sqrt(v.Y * v.Y + v.Z * v.Z) for v in vertices)


def check_common(model, parts, spec):
    """Checks shared by both concept studies."""
    for label, part in parts.items():
        assert len(part.solids()) == 1, f"{label}: expected one closed solid"
        assert part.is_valid, f"{label}: invalid BREP"
        assert part.volume > 0.0, f"{label}: nonpositive volume"

    bounds = model.bounding_box()
    assert abs(bounds.min.X - TAIL) < TOL, f"tail datum: {bounds.min.X}"
    assert abs(bounds.max.X - NOSE) < TOL, f"nose datum: {bounds.max.X}"
    assert abs(bounds.size.X - (NOSE - TAIL)) < TOL, f"overall length: {bounds.size.X}"

    for label, part in parts.items():
        part_bounds = part.bounding_box()
        if label.startswith("booster_"):
            assert part_bounds.max.X <= SEAM + TOL, f"{label}: booster past seam"
        else:
            assert part_bounds.min.X >= SEAM - TOL, f"{label}: upper part behind seam"

    for prefix, count in spec["counts"].items():
        found = sum(1 for label in parts if label.startswith(prefix + "_"))
        assert found == count, f"{prefix}: expected {count}, found {found}"

    cylinder = bd.Cylinder(ENVELOPE_RADIUS, 4000.0).rotate(bd.Axis.Y, 90.0)
    for label, part in parts.items():
        protrusion = part - cylinder
        assert protrusion is None or protrusion.volume < VOLUME_TOL, (
            f"{label}: exceeds {ENVELOPE_RADIUS} mm radius envelope"
        )

    for label in ("sustainer_body", "booster_body"):
        body_bounds = parts[label].bounding_box()
        assert abs(body_bounds.center().Y) < TOL, f"{label}: off-axis Y datum"
        assert abs(body_bounds.center().Z) < TOL, f"{label}: off-axis Z datum"
    for index in (1, 2):
        shoe = parts[f"mount_shoe_{index}"]
        assert abs(shoe.bounding_box().center().Y) < TOL, f"mount_shoe_{index}: not centered"
        assert shoe.distance_to(parts["sustainer_body"]) < TOL, f"mount_shoe_{index}: floating"

    for index in range(1, spec["counts"]["sustainer_fin"] + 1):
        assert parts[f"sustainer_fin_{index}"].distance_to(parts["sustainer_body"]) < TOL, (
            f"sustainer_fin_{index}: no body contact"
        )
    for index in range(1, spec["counts"]["booster_fin"] + 1):
        assert parts[f"booster_fin_{index}"].distance_to(parts["booster_body"]) < TOL, (
            f"booster_fin_{index}: no body contact"
        )


def check_intake_probes(parts, spec):
    """Witness volumes inside each intake cavity, checked against the whole model."""
    prefix = spec["intake_prefix"]
    anchor = spec["probe_anchor"]
    results = []
    for index, angle in enumerate(spec["intake_angles"], 1):
        probe = (
            bd.Box(8, 6, 6)
            .translate(spec["intake_probe"], transform=True)
            .rotate(bd.Axis.X, -angle)
        )
        hits = [
            label
            for label, part in parts.items()
            if intersection_volume(part, probe) > VOLUME_TOL
        ]
        assert not hits, f"{prefix}_{index}: cavity probe blocked by {hits}"
        center = probe.center()
        anchor_bounds = parts[f"{anchor}_{index}" if anchor == "intake_pod" else anchor].bounding_box()
        assert (
            anchor_bounds.min.X <= center.X <= anchor_bounds.max.X
            and anchor_bounds.min.Y <= center.Y <= anchor_bounds.max.Y
            and anchor_bounds.min.Z <= center.Z <= anchor_bounds.max.Z
        ), f"{prefix}_{index}: probe {center} outside {anchor} bounds"
        results.append({"index": index, "angle_degrees": angle, "probe_center_mm": list(center), "blocked_by": []})
    return results


def check_model(spec):
    model = read_step(ROOT / spec["file"])
    parts = {part.label: part for part in model.children}
    assert len(parts) == len(model.children), f"Duplicate labels in {spec['file']}"
    assert model.label == spec["label"], f"Model label {model.label!r} != {spec['label']!r}"

    check_common(model, parts, spec)

    prefix = spec["intake_prefix"]
    for index in range(1, spec["counts"][prefix] + 1):
        assert parts[f"{prefix}_{index}"].distance_to(parts["sustainer_body"]) < TOL, (
            f"{prefix}_{index}: no body contact"
        )

    # Closed nozzle backing must own its visible face, not share it with a gray body cap.
    for nozzle_label, body_label in (("sustainer_nozzle", "sustainer_body"),
                                    ("booster_nozzle", "booster_body")):
        nozzle, body = parts[nozzle_label], parts[body_label]
        assert nozzle.distance_to(body) < TOL, f"{nozzle_label}: disconnected"
        rear_face = nozzle.bounding_box().max.X - 4.5
        probe = bd.Box(1, 8, 8).translate((rear_face, 0, 0))
        assert intersection_volume(body, probe) < VOLUME_TOL, f"{body_label}: overlaps nozzle backing"
        assert intersection_volume(nozzle, probe) > 60, f"{nozzle_label}: missing backing"

    probes = check_intake_probes(parts, spec)

    bounds = model.bounding_box()
    report = {
        "file": spec["file"],
        "label": spec["label"],
        "part_count": len(parts),
        "labels": sorted(parts),
        "model_bbox_mm": {
            "min": list(bounds.min),
            "max": list(bounds.max),
            "size": list(bounds.size),
        },
        "seam_mm": SEAM,
        "envelope_radius_mm": ENVELOPE_RADIUS,
        "measured_max_radius_mm": {
            label: round(measured_max_radius(part), 2) for label, part in parts.items()
        },
        "intake_probes": probes,
    }
    print(f"PASS: {spec['file']} -- {len(parts)} uniquely labeled parts, "
          f"length {bounds.size.X:.1f} mm, envelope <= {ENVELOPE_RADIUS} mm, "
          f"{len(probes)} clear intake cavity probes.")
    return report


def main():
    reports = [check_model(POD), check_model(SHOULDER)]
    output = {
        "ok": True,
        "datums_mm": {"nose": NOSE, "tail": TAIL, "seam": SEAM},
        "envelope_radius_mm": ENVELOPE_RADIUS,
        "models": reports,
        "scope": "CAD exterior concept studies; aircraft rack fit and runtime not verified",
    }
    (ROOT / "Halberd_Concept_Checks.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    print("PASS: all concept checks; report written to Halberd_Concept_Checks.json")


if __name__ == "__main__":
    main()
