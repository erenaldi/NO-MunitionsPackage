"""Artifact checks for the single structured Petal intake prototype."""
import math
from pathlib import Path

from cadgen import read_step

from check_halberd_four_intake_concepts import envelope_sustainer, robust_volume


ROOT = Path(__file__).resolve().parent
TOL = 1e-4


def radial_point(x, radius, angle=45):
    radians = math.radians(angle)
    return (x, radius * math.sin(radians), radius * math.cos(radians))


def main():
    model = read_step(ROOT / "Halberd_C4_Petal_Intake_Prototype.step")
    parts = {part.label: part for part in model.children}
    body = parts["sustainer_body"]
    chines = [parts["intake_chine_port_prototype"], parts["intake_chine_starboard_prototype"]]
    floor = parts["intake_floor_1"]

    assert len(parts) == len(model.children) == 21, "prototype labels are not unique"
    assert body.is_valid and floor.is_valid and all(chine.is_valid for chine in chines)
    assert body.volume > 0 and floor.volume > 0 and all(chine.volume > 0 for chine in chines)
    assert all(chine.distance_to(body) < TOL for chine in chines), "ramp chines do not contact the body"
    assert floor.distance_to(body) < TOL, "structured intake floor does not contact the body"
    for chine in chines:
        assert robust_volume(chine, envelope_sustainer(), difference=True) < 1e-3, (
            "ramp chine exceeds the locked envelope"
        )

    body_solid = body.solids()[0]
    assert not body_solid.is_inside(radial_point(848.0, 80.0)), "forward mouth is blocked"
    assert not body_solid.is_inside(radial_point(680.0, 84.0)), "duct throat is blocked"
    assert not body_solid.is_inside(radial_point(350.0, 63.0)), "aft duct is blocked"
    assert body_solid.is_inside(radial_point(680.0, 40.0)), "central core is breached"
    assert body_solid.is_inside(radial_point(860.0, 60.0)), "duct extends beyond X850"
    print("PASS Petal intake prototype: rounded waist, contacting ramp chines, open duct, protected core")


if __name__ == "__main__":
    main()
