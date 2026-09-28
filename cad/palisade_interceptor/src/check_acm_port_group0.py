"""Artifact-side gate for one PAC-3-inspired six-port ACM cap group."""

import json
import math
from itertools import combinations
from pathlib import Path

from cadgen import build123d as bd, read_step
from cadgen.geometry import boundary_edges, self_intersections, topology_errors

from check_spear_revisions import overlap, radial_max, same_solid


ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / "STEP"
OFFSET = 270.
ANGLES = (-8., 8.)
STATIONS = (-549., -535., -521.)
CAP_RADIUS = 54.56


def load(name, count):
    model = read_step(STEP / name)
    parts = {item.label: item for item in model.children}
    assert len(model.children) == len(parts) == count, (name, "duplicate/missing label")
    assert all(len(item.solids()) == 1 and item.is_valid and item.volume > 0
               for item in parts.values()), (name, "invalid solid")
    return parts


def check():
    original = load("Spear_UniformBarrel.step", 12)
    assembled = load("Spear_ACMPortGroup0.step", 22)
    separated = load("Spear_ACMPortGroup0_Separated.step", 22)
    focus = load("Spear_ACMPortGroup0_Cap_Focus.step", 16)
    inserts = {f"acm_0_{kind}_{index}" for kind in ("rim", "core") for index in range(6)}
    expected = set(original)-{"thruster_0", "thruster_0_throat"} | inserts
    assert set(assembled) == set(separated) == expected
    assert set(focus) == {"turning_cap", "thruster_90", "thruster_180", "thruster_270"} | inserts
    for label in original:
        if label not in ("turning_cap", "thruster_0", "thruster_0_throat"):
            assert same_solid(assembled[label], original[label]), (label, "protected form changed")
    body, cap, nozzle = (assembled[label] for label in ("body", "turning_cap", "main_nozzle"))
    assert abs(cap.bounding_box().min.X + 600.) < .002
    assert abs(cap.bounding_box().max.X + 470.) < .002
    assert overlap(body, cap) < .001 and overlap(separated["turning_cap"], body) < .001
    # All six bores are at X<=-521. A grazing snapshot can suggest an open
    # notch at the front rim; test its actual saved section independently.
    near_seam = cap & bd.Box(.2, 120., 120.).translate((-470.5, 0, 0))
    full_cylinder_section_mm3 = math.pi*CAP_RADIUS*CAP_RADIUS*.2
    assert near_seam is not None and abs(near_seam.volume-full_cylinder_section_mm3) < .03, (
        "unintended cut at cap's forward face", near_seam.volume, full_cylinder_section_mm3
    )

    port_facts = []
    for index, (x, theta) in enumerate((x, t) for x in STATIONS for t in ANGLES):
        angle = math.radians(theta)
        rim, core = (assembled[f"acm_0_{kind}_{index}"] for kind in ("rim", "core"))
        assert abs(rim.bounding_box().center().X-x) < .002
        assert abs(core.bounding_box().center().X-x) < .002
        assert radial_max(rim) < CAP_RADIUS-1.5, (index, "rim protrudes above skin")
        assert radial_max(core) < CAP_RADIUS-1.5, (index, "dark center protrudes")
        assert overlap(rim, cap) < .001 and overlap(core, cap) < .001
        assert overlap(rim, core) < .001
        assert rim.distance_to(cap) < .002 and core.distance_to(cap) < .002
        center = bd.Vector(x, math.cos(angle), math.sin(angle))
        hole = bd.Box(1., 1., 1.).translate((center.X, center.Y*CAP_RADIUS, center.Z*CAP_RADIUS))
        blind = bd.Box(1., 1., 1.).translate((center.X, center.Y*(CAP_RADIUS-9.),
                                               center.Z*(CAP_RADIUS-9.)))
        core_probe = bd.Box(1., 1., 1.).translate((center.X, center.Y*(CAP_RADIUS-3.),
                                                    center.Z*(CAP_RADIUS-3.)))
        assert overlap(hole, cap) < .001 and overlap(blind, cap) > .001
        assert overlap(core_probe, core) > .001
        for component in (rim, core):
            assert not topology_errors(component), (index, "bad insert topology")
            assert len(component.shells()) == 1 and not boundary_edges(component.shells()[0])
        port_facts.append({"x_mm": x, "clock_deg": theta,
                           "rim_max_radius_mm": round(radial_max(rim), 3)})
    for a, b in combinations((assembled[label] for label in sorted(inserts)), 2):
        assert overlap(a, b) < .001, "adjacent ACM inserts collide"

    assert not topology_errors(cap) and len(cap.shells()) == 1
    assert not boundary_edges(cap.shells()[0]) and not self_intersections(cap)
    main_bore = bd.Box(2, 2, 2).translate((-465., 0., 0.))
    assert overlap(main_bore, body) < .001 and overlap(main_bore, nozzle) < .001
    for label, part in assembled.items():
        if label in focus:
            assert same_solid(part, focus[label]), (label, "isolated cap mismatches")
        moved = label == "turning_cap" or label.startswith(("thruster_", "acm_"))
        restored = separated[label].translate((OFFSET, 0, 0)) if moved else separated[label]
        assert same_solid(part, restored), (label, "stage state changed geometry")
    envelope = max(radial_max(part) for part in assembled.values())
    assert abs(envelope-79.006) < .02
    result = {"ok": True, "base": "Spear_UniformBarrel.step",
              "single_group_port_count": 6, "unmodified_basic_motor_groups": 3,
              "full_parts": len(assembled), "focus_parts": len(focus),
              "motor_group_ports": port_facts, "radial_envelope_mm": round(envelope, 3),
              "forward_cap_slice_mm3": round(near_seam.volume, 3),
              "main_missile_preserved": True, "blind_recesses": True,
              "stage_shapes_preserved": True}
    (ROOT / "reviews" / "spear_acm_port_group0_checks.json").write_text(
        json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print("PASS: 6 inset ports in one ACM group; Spear and other 3 groups preserved")


if __name__ == "__main__":
    check()
