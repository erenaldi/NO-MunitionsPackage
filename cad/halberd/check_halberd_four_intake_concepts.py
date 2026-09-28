"""Artifact-only checks for the four locked-envelope Halberd concepts."""
import json
import math
from pathlib import Path

from cadgen import build123d as bd, read_step

from halberd_shoulder_variants import section


ROOT = Path(__file__).resolve().parent
LENGTH = 3367.0
HALF = LENGTH / 2.0
SEAM = -336.7
NOSE_BASE = 1080.0
ANGLES = (45, 135, 225, 315)
TOL = 1e-4
VOLUME_TOL = 1e-3

FILES = {
    "Razorback": "Halberd_C1_Razorback.step",
    "Manta": "Halberd_C2_Manta.step",
    "Citadel": "Halberd_C3_Citadel.step",
    "Petal": "Halberd_C4_Petal.step",
}

PROBES = {
    "Razorback": ((380.0, 72.0), (780.0, 102.0)),
    "Manta": ((340.0, 69.0), (780.0, 102.0)),
    "Citadel": ((400.0, 74.0), (780.0, 101.0)),
    "Petal": ((350.0, 60.0), (820.0, 82.0)),
}


def disk(x, radius):
    return bd.Circle(radius).rotate(bd.Axis.Y, 90).translate((x, 0, 0))


def envelope_sustainer():
    return bd.loft([
        section(SEAM, 208, 208, 12), section(400, 208, 208, 12),
        section(650, 192, 192, 32), disk(850, 86), disk(NOSE_BASE, 86),
    ], ruled=True)


def envelope_booster():
    return bd.loft([
        section(-HALF, 166.4, 166.4, 62.4),
        section(-HALF + 240, 208, 208, 78),
        section(-1000, 208, 208, 64),
        section(SEAM - 180, 208, 208, 12),
        section(SEAM, 208, 208, 12),
    ], ruled=True)


def robust_volume(left, right, difference=False):
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut
    from OCP.TopTools import TopTools_ListOfShape
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps

    arguments, tools = TopTools_ListOfShape(), TopTools_ListOfShape()
    arguments.Append(left.wrapped)
    tools.Append(right.wrapped)
    operation = BRepAlgoAPI_Cut() if difference else BRepAlgoAPI_Common()
    operation.SetArguments(arguments)
    operation.SetTools(tools)
    operation.SetRunParallel(False)
    operation.SetFuzzyValue(1e-6)
    operation.Build()
    assert operation.IsDone(), "Boolean measurement failed"
    properties = GProp_GProps()
    BRepGProp.VolumeProperties_s(operation.Shape(), properties)
    return properties.Mass()


def radial_point(x, radius, angle):
    radians = math.radians(angle)
    return (x, radius * math.sin(radians), radius * math.cos(radians))


def check_one(key, filename):
    model = read_step(ROOT / filename)
    parts = {part.label: part for part in model.children}
    expected = {
        "sustainer_body", "booster_body", "radome", "sustainer_nozzle",
        "booster_nozzle", "mount_1", "mount_2",
    }
    expected.update(
        f"{prefix}_{index}"
        for prefix in ("intake_floor", "sustainer_fin", "booster_fin")
        for index in range(1, 5)
    )
    assert len(parts) == len(model.children) == 19, f"{key}: labels are not unique"
    assert set(parts) == expected, f"{key}: unexpected labels {set(parts) ^ expected}"
    for label, part in parts.items():
        assert len(part.solids()) == 1, f"{key}/{label}: expected one solid"
        assert part.is_valid, f"{key}/{label}: invalid BREP"
        assert part.volume > 0, f"{key}/{label}: nonpositive volume"

    bounds = model.bounding_box()
    assert abs(bounds.min.X + HALF) < TOL, f"{key}: tail datum {bounds.min.X}"
    assert abs(bounds.max.X - HALF) < TOL, f"{key}: nose datum {bounds.max.X}"
    assert abs(bounds.size.X - LENGTH) < TOL, f"{key}: length {bounds.size.X}"

    for label, part in parts.items():
        part_bounds = part.bounding_box()
        if label.startswith("booster_"):
            assert part_bounds.max.X <= SEAM + TOL, f"{key}/{label}: crosses stage seam"
        else:
            assert part_bounds.min.X >= SEAM - TOL, f"{key}/{label}: crosses stage seam"

    body_excess = robust_volume(parts["sustainer_body"], envelope_sustainer(), difference=True)
    booster_excess = robust_volume(parts["booster_body"], envelope_booster(), difference=True)
    assert body_excess < VOLUME_TOL, f"{key}: body exceeds locked envelope by {body_excess} mm3"
    assert booster_excess < VOLUME_TOL, f"{key}: booster exceeds locked envelope by {booster_excess} mm3"
    floor_excess = {}
    for index in range(1, 5):
        label = f"intake_floor_{index}"
        floor_excess[label] = robust_volume(parts[label], envelope_sustainer(), difference=True)
        assert floor_excess[label] < VOLUME_TOL, f"{key}/{label}: projects outside envelope"

    body = parts["sustainer_body"].solids()[0]
    aft, front = PROBES[key]
    intake_probes = []
    for index, angle in enumerate(ANGLES, 1):
        aft_point = radial_point(*aft, angle)
        front_point = radial_point(*front, angle)
        core_point = radial_point(front[0], 40.0, angle)
        protected_point = radial_point(900.0, 65.0, angle)
        assert not body.is_inside(aft_point), f"{key}/intake {index}: aft path blocked"
        assert not body.is_inside(front_point), f"{key}/intake {index}: mouth blocked"
        assert body.is_inside(core_point), f"{key}/intake {index}: central core breached"
        assert body.is_inside(protected_point), f"{key}/intake {index}: cut extends beyond X850"
        intake_probes.append({
            "index": index,
            "angle_degrees": angle,
            "aft_void_mm": aft_point,
            "front_void_mm": front_point,
            "front_radius_minus_aft_radius_mm": front[1] - aft[1],
        })
    assert front[1] > aft[1] + 20.0, f"{key}: intake does not run inward toward aft"

    floor_volumes = [parts[f"intake_floor_{index}"].volume for index in range(1, 5)]
    assert max(floor_volumes) - min(floor_volumes) < VOLUME_TOL, f"{key}: intake symmetry drift"

    contacts = {}
    for index in range(1, 5):
        for prefix, body_label in (("intake_floor", "sustainer_body"),
                                   ("sustainer_fin", "sustainer_body"),
                                   ("booster_fin", "booster_body")):
            label = f"{prefix}_{index}"
            contacts[label] = parts[label].distance_to(parts[body_label])
            assert contacts[label] < TOL, f"{key}/{label}: disconnected by {contacts[label]} mm"
    for index in (1, 2):
        label = f"mount_{index}"
        contacts[label] = parts[label].distance_to(parts["sustainer_body"])
        assert contacts[label] < TOL, f"{key}/{label}: disconnected by {contacts[label]} mm"
    for label, body_label in (("sustainer_nozzle", "sustainer_body"),
                              ("booster_nozzle", "booster_body")):
        contacts[label] = parts[label].distance_to(parts[body_label])
        assert contacts[label] < TOL, f"{key}/{label}: disconnected"

    max_radius = max(
        math.hypot(y, z)
        for part in parts.values()
        for y in (part.bounding_box().min.Y, part.bounding_box().max.Y)
        for z in (part.bounding_box().min.Z, part.bounding_box().max.Z)
    )
    # The selected hybrid's same conservative bbox-corner metric is 244.925 mm.
    assert max_radius <= 244.93, f"{key}: radial envelope {max_radius}"
    return {
        "file": filename,
        "part_count": len(parts),
        "bounds_mm": {"min": list(bounds.min), "max": list(bounds.max)},
        "body_excess_mm3": body_excess,
        "booster_excess_mm3": booster_excess,
        "intake_floor_excess_mm3": floor_excess,
        "intake_probes": intake_probes,
        "contacts_mm": contacts,
        "maximum_bbox_corner_radius_mm": max_radius,
    }


def main():
    report = {key: check_one(key, filename) for key, filename in FILES.items()}
    output = {
        "ok": True,
        "generated": "2026-09-21",
        "scope": "concept-stage exterior CAD; no aerodynamic or runtime claim",
        "concepts": report,
    }
    path = ROOT / "Halberd_Four_Intake_Concept_Checks.json"
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    for key, record in report.items():
        print(f"PASS {key}: {record['part_count']} parts, max radius {record['maximum_bbox_corner_radius_mm']:.3f} mm")
    print(path)


if __name__ == "__main__":
    main()
