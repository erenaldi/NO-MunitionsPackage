"""Deterministic checks for the detailed AAM-44 Halberd CAD master."""

import math
from pathlib import Path

from cadgen import build123d as bd, read_step

from generate_halberd_detailed import (
    BODY_RADIUS,
    BOOSTER_FIN_AFT_X,
    BOOSTER_FIN_FORWARD_X,
    BOOSTER_FIN_RADIUS,
    BOOSTER_NOZZLE_CHAMBER_RADIUS,
    BOOSTER_NOZZLE_EXIT_RADIUS,
    BOOSTER_NOZZLE_LINER_THICKNESS,
    BOOSTER_NOZZLE_START_X,
    BOOSTER_NOZZLE_THROAT_RADIUS,
    BOOSTER_NOZZLE_THROAT_X,
    HALF_LENGTH,
    INTAKE_AZIMUTHS,
    INTAKE_DUCT_AFT_X,
    INTAKE_DUCT_DEPTH,
    INTAKE_FRONT_X,
    INTAKE_HEIGHT_SCALE,
    INTAKE_LIP_MIN_THICKNESS,
    INTAKE_MOUTH_HEIGHT,
    INTAKE_MOUTH_WIDTH,
    INTAKE_THROAT_HEIGHT,
    INTAKE_THROAT_WIDTH,
    LENGTH,
    MOUNT_CONDUIT_HEIGHT,
    MOUNT_CONDUIT_LENGTH,
    MOUNT_CONDUIT_WIDTH,
    MOUNT_LUG_HEIGHT,
    MOUNT_LUG_LENGTH,
    MOUNT_LUG_STATIONS,
    MOUNT_LUG_WIDTH,
    MOUNT_RAIL_HEIGHT,
    MOUNT_RAIL_LENGTH,
    MOUNT_RAIL_WIDTH,
    SEAM_X,
    SUSTAINER_FIN_ROOT_AFT_X,
    SUSTAINER_FIN_TIP_FORWARD_X,
)


BODY_LABELS = {
    "ramjet_body",
    "forward_body",
    "seeker_section",
    "radome",
}
HARDWARE_LABELS = {
    "stage_joint_band",
    "ramjet_joint_band",
    "forward_joint_band",
    "dorsal_launch_rail",
    "suspension_lug_1",
    "suspension_lug_2",
    "dorsal_wiring_conduit",
}
BOOSTER_LABELS = {
    "booster_body",
    "booster_forward_collar",
    "booster_nozzle_outer",
    "booster_nozzle_inner",
    "booster_nozzle_recess",
}


def angle_from_dorsal(part):
    center = part.center()
    return math.degrees(math.atan2(center.Y, center.Z)) % 360.0


def assert_rotational_match(parts, prefix):
    reference = parts[f"{prefix}_1"]
    for index, azimuth in enumerate(INTAKE_AZIMUTHS, 1):
        aligned = parts[f"{prefix}_{index}"].rotate(
            bd.Axis.X, azimuth - INTAKE_AZIMUTHS[0]
        )
        volume_tolerance = max(1e-5, reference.volume * 1e-8)
        assert abs(aligned.volume - reference.volume) < volume_tolerance, prefix
        assert (aligned.bounding_box().min - reference.bounding_box().min).length < 1e-5, prefix
        assert (aligned.bounding_box().max - reference.bounding_box().max).length < 1e-5, prefix


def centered_box(center, size):
    return bd.Box(*size).translate(center, transform=True)


def intersection_volume(left, right):
    intersection = left & right
    return 0.0 if intersection is None else intersection.volume


def main():
    source = Path(__file__).with_name("AAM-44_Halberd_Detailed.step")
    model = read_step(source)
    parts = {part.label: part for part in model.children}
    assert len(parts) == 41, f"Expected 41 labeled parts, found {len(parts)}"
    assert len(parts) == len(model.children), "Duplicate Halberd part labels"

    expected = BODY_LABELS | HARDWARE_LABELS | BOOSTER_LABELS | {"sustainer_nozzle"}
    for index in range(1, 4):
        expected.update(
            {
                f"intake_ramp_{index}",
                f"intake_lip_{index}",
                f"intake_duct_{index}",
                f"intake_cheek_{index}_1",
                f"intake_cheek_{index}_2",
                f"sustainer_fin_{index}",
                f"booster_fin_{index}",
                f"booster_fin_root_{index}",
            }
        )
    assert set(parts) == expected, f"Unexpected labels: {set(parts) ^ expected}"

    bounds = model.bounding_box()
    assert abs(bounds.min.X + HALF_LENGTH) < 1e-4
    assert abs(bounds.max.X - HALF_LENGTH) < 1e-4
    assert abs(bounds.size.X - LENGTH) < 1e-4
    ramjet_bounds = parts["ramjet_body"].bounding_box()
    assert abs(ramjet_bounds.size.Y - BODY_RADIUS * 2.0) < 1e-4
    assert abs(ramjet_bounds.size.Z - BODY_RADIUS * 2.0) < 1e-4
    assert abs(ramjet_bounds.min.X - SEAM_X) < 1e-4
    assert abs(parts["booster_body"].bounding_box().max.X - SEAM_X) < 1e-4

    nozzle_outer = parts["booster_nozzle_outer"]
    nozzle_inner = parts["booster_nozzle_inner"]
    nozzle_recess = parts["booster_nozzle_recess"]
    assert len(nozzle_outer.solids()) == 1 and nozzle_outer.volume > 0.0
    assert len(nozzle_inner.solids()) == 1 and nozzle_inner.volume > 0.0
    assert len(nozzle_recess.solids()) == 1 and nozzle_recess.volume > 0.0
    assert abs(nozzle_outer.bounding_box().min.X + HALF_LENGTH) < 1e-4
    assert abs(nozzle_inner.bounding_box().min.X + HALF_LENGTH) < 1e-4
    assert abs(nozzle_outer.bounding_box().max.X - BOOSTER_NOZZLE_START_X) < 1e-4
    assert abs(nozzle_inner.bounding_box().max.X - BOOSTER_NOZZLE_START_X) < 1e-4
    assert nozzle_outer.distance_to(nozzle_inner) < 1e-5
    assert nozzle_inner.distance_to(nozzle_recess) < 1e-5
    recess_bounds = nozzle_recess.bounding_box()
    assert abs((recess_bounds.min.X + recess_bounds.max.X) * 0.5 - BOOSTER_NOZZLE_THROAT_X) < 1e-4
    assert abs(recess_bounds.size.X - 3.0) < 1e-4
    assert abs(
        recess_bounds.size.Y
        - 2.0 * (BOOSTER_NOZZLE_THROAT_RADIUS - BOOSTER_NOZZLE_LINER_THICKNESS)
    ) < 1e-4
    nozzle_probes = (
        (-1682.0, BOOSTER_NOZZLE_EXIT_RADIUS - BOOSTER_NOZZLE_LINER_THICKNESS - 5.0),
        (
            BOOSTER_NOZZLE_THROAT_X,
            BOOSTER_NOZZLE_THROAT_RADIUS - BOOSTER_NOZZLE_LINER_THICKNESS - 2.0,
        ),
        (-1512.0, BOOSTER_NOZZLE_CHAMBER_RADIUS - BOOSTER_NOZZLE_LINER_THICKNESS - 8.0),
    )
    for x, radius in nozzle_probes:
        probe = bd.Cylinder(radius, 2.0).rotate(bd.Axis.Y, 90.0).translate(
            (x - 1.0, 0.0, 0.0), transform=True
        )
        assert intersection_volume(nozzle_outer, probe) < 1e-5
        assert intersection_volume(nozzle_inner, probe) < 1e-5

    for index, expected_angle in enumerate(INTAKE_AZIMUTHS, 1):
        actual = angle_from_dorsal(parts[f"intake_lip_{index}"])
        error = abs((actual - expected_angle + 180.0) % 360.0 - 180.0)
        assert error < 0.01, (index, actual, expected_angle)
    upper_angles = sorted(
        [angle_from_dorsal(parts["intake_lip_1"]), angle_from_dorsal(parts["intake_lip_3"])]
    )
    assert abs(upper_angles[0] - 60.0) < 0.01
    assert abs(upper_angles[1] - 300.0) < 0.01

    rail_center = parts["dorsal_launch_rail"].center()
    assert abs(rail_center.Y) < 1e-5
    assert rail_center.Z > BODY_RADIUS
    rail_bounds = parts["dorsal_launch_rail"].bounding_box()
    assert abs(rail_bounds.size.X - MOUNT_RAIL_LENGTH) < 1e-4
    assert abs(rail_bounds.size.Y - MOUNT_RAIL_WIDTH) < 1e-4
    assert abs(rail_bounds.max.Z - (BODY_RADIUS + MOUNT_RAIL_HEIGHT)) < 1e-4
    for index, expected_x in enumerate(MOUNT_LUG_STATIONS, 1):
        lug_name = f"suspension_lug_{index}"
        center = parts[lug_name].center()
        assert abs(center.Y) < 1e-5 and center.Z > BODY_RADIUS
        lug_bounds = parts[lug_name].bounding_box()
        assert abs((lug_bounds.min.X + lug_bounds.max.X) * 0.5 - expected_x) < 1e-4
        assert abs(lug_bounds.size.X - MOUNT_LUG_LENGTH) < 1e-4
        assert abs(lug_bounds.size.Y - MOUNT_LUG_WIDTH) < 1e-4
        assert abs(lug_bounds.max.Z - (BODY_RADIUS + MOUNT_LUG_HEIGHT)) < 1e-4
    conduit_bounds = parts["dorsal_wiring_conduit"].bounding_box()
    assert abs(conduit_bounds.size.X - MOUNT_CONDUIT_LENGTH) < 1e-4
    assert abs(conduit_bounds.size.Y - MOUNT_CONDUIT_WIDTH) < 1e-4
    assert abs(conduit_bounds.max.Z - (BODY_RADIUS + MOUNT_CONDUIT_HEIGHT)) < 1e-4

    for prefix in (
        "intake_ramp",
        "intake_lip",
        "intake_duct",
        "sustainer_fin",
        "booster_fin",
        "booster_fin_root",
    ):
        assert_rotational_match(parts, prefix)
    for side in (1, 2):
        reference = parts[f"intake_cheek_1_{side}"]
        for index, azimuth in enumerate(INTAKE_AZIMUTHS, 1):
            aligned = parts[f"intake_cheek_{index}_{side}"].rotate(
                bd.Axis.X, azimuth - INTAKE_AZIMUTHS[0]
            )
            tolerance = max(1e-5, reference.volume * 1e-8)
            assert abs(aligned.volume - reference.volume) < tolerance
            assert (aligned.bounding_box().min - reference.bounding_box().min).length < 1e-5
            assert (aligned.bounding_box().max - reference.bounding_box().max).length < 1e-5

    for index in range(1, 4):
        intake_parts = [
            parts[f"intake_ramp_{index}"],
            parts[f"intake_lip_{index}"],
            parts[f"intake_duct_{index}"],
            parts[f"intake_cheek_{index}_1"],
            parts[f"intake_cheek_{index}_2"],
        ]
        assert all(len(part.solids()) == 1 and part.volume > 0.0 for part in intake_parts)
        assert parts[f"intake_duct_{index}"].distance_to(parts[f"intake_lip_{index}"]) < 1e-5
        assert parts[f"intake_ramp_{index}"].distance_to(parts[f"intake_lip_{index}"]) < 1e-5
        for side in (1, 2):
            assert parts[f"intake_cheek_{index}_{side}"].distance_to(parts[f"intake_duct_{index}"]) < 1e-5

        azimuth = INTAKE_AZIMUTHS[index - 1]
        aligned_duct = parts[f"intake_duct_{index}"].rotate(bd.Axis.X, azimuth)
        for side in (1, 2):
            aligned_cheek = parts[f"intake_cheek_{index}_{side}"].rotate(bd.Axis.X, azimuth)
            contact = aligned_duct & aligned_cheek
            assert contact is not None and contact.volume > 1.0
            for station in (55.0, 180.0, 360.0, 590.0, 725.0):
                slab = centered_box((station, 0.0, BODY_RADIUS + 24.0), (6.0, 100.0, 150.0))
                assert intersection_volume(contact, slab) > 0.1

        probes = (
            centered_box((785.0, 0.0, 131.0), (4.0, 14.0, 6.0)),
            centered_box((610.0, 0.0, 121.0), (8.0, 10.0, 5.0)),
            centered_box((360.0, 0.0, 113.0), (8.0, 8.0, 4.0)),
            centered_box((150.0, 0.0, 105.0), (8.0, 6.0, 3.0)),
        )
        for probe in probes:
            probe = probe.rotate(bd.Axis.X, -azimuth)
            for intake_part in intake_parts:
                assert intersection_volume(intake_part, probe) < 1e-5

        lip_bounds = parts[f"intake_lip_{index}"].bounding_box()
        duct_bounds = parts[f"intake_duct_{index}"].bounding_box()
        assert lip_bounds.max.X >= INTAKE_FRONT_X - 1e-5
        assert duct_bounds.min.X <= INTAKE_DUCT_AFT_X + 1e-5
        assert lip_bounds.max.X - duct_bounds.min.X >= INTAKE_DUCT_DEPTH - 1e-5

        sustainer_fin = parts[f"sustainer_fin_{index}"]
        assert len(sustainer_fin.solids()) == 1
        assert sustainer_fin.distance_to(parts["ramjet_body"]) < 1e-5
        assert sustainer_fin.distance_to(parts[f"intake_ramp_{index}"]) < 1e-5
        assert sustainer_fin.distance_to(parts[f"intake_duct_{index}"]) < 1e-5
        assert duct_bounds.min.X <= SUSTAINER_FIN_TIP_FORWARD_X + 1e-5
        assert sustainer_fin.bounding_box().min.X >= SUSTAINER_FIN_ROOT_AFT_X - 1e-5
        assert sustainer_fin.bounding_box().min.X - SEAM_X >= 36.0
        assert parts[f"booster_fin_{index}"].distance_to(parts["booster_body"]) < 1e-5
        assert parts[f"booster_fin_root_{index}"].distance_to(parts["booster_body"]) < 1e-5
        assert parts[f"booster_fin_{index}"].distance_to(parts[f"booster_fin_root_{index}"]) < 1e-5

        aligned_booster_fin = parts[f"booster_fin_{index}"].rotate(bd.Axis.X, azimuth)
        booster_fin_bounds = aligned_booster_fin.bounding_box()
        assert abs(booster_fin_bounds.min.X - BOOSTER_FIN_AFT_X) < 1e-4
        assert abs(booster_fin_bounds.max.X - BOOSTER_FIN_FORWARD_X) < 1e-4
        assert abs(booster_fin_bounds.max.Z - BOOSTER_FIN_RADIUS) < 1e-4

    assert INTAKE_MOUTH_WIDTH >= 65.0 and INTAKE_MOUTH_HEIGHT >= 39.0
    assert INTAKE_THROAT_WIDTH >= 40.0 and INTAKE_THROAT_HEIGHT >= 21.0
    assert INTAKE_LIP_MIN_THICKNESS >= 5.0
    assert abs(INTAKE_HEIGHT_SCALE - 0.85) < 1e-9
    reference_lip = parts["intake_lip_1"].rotate(bd.Axis.X, INTAKE_AZIMUTHS[0])
    assert abs(reference_lip.bounding_box().max.Z - (BODY_RADIUS + 57.5 * INTAKE_HEIGHT_SCALE)) < 1e-4
    for index in (1, 3):
        assert parts[f"intake_lip_{index}"].distance_to(parts["dorsal_launch_rail"]) >= 20.0

    print("PASS: 41 uniquely labeled Halberd parts are present and classified.")
    print(f"PASS: centered {LENGTH / 1000:.3f} m envelope and {BODY_RADIUS * 2 / 1000:.3f} m body diameter.")
    print(f"PASS: upper stage and detachable booster meet at X={SEAM_X / 1000:.4f} m.")
    print("PASS: three ramp intakes, sustainer fins, and booster fins retain exact 120-degree clocking.")
    print("PASS: compact Kris-style rail and suspension shoes retain the original axial stations.")
    print("PASS: each sustainer fin joins its intake ramp and body while retaining at least 36 mm seam clearance.")
    print("PASS: intake ducts meet their lips and sustainer fins; all booster-fin roots contact the booster body.")
    print("PASS: both intake cheeks remain joined to each duct at five stations along the full taper.")
    print("PASS: aerofoiled shoulder-strake booster fins retain their axial stations and 218 mm radial envelope.")
    print("PASS: swept trapezoidal mouths and four probed duct stations remain open across the 745 mm passage.")
    print("PASS: intake stand-off above the mounting surface is reduced by 15% while retaining at least 5 mm lip thickness.")
    print("PASS: both upper intake cowls retain at least 20 mm clearance from the dorsal launch rail.")
    print("PASS: the booster nozzle's red liner terminates at a dark throat-sized closure disk.")


if __name__ == "__main__":
    main()
