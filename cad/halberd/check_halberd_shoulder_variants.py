"""Deterministic STEP checks for the five Halberd shoulder variants.

Reads only the exported STEP files plus the config constants from
halberd_shoulder_variants.py (VARIANTS). The build factories are never called:
every assertion measures the actual STEP geometry.

Per variant this verifies:
  - unique labels, one positive-volume valid solid per label
  - strict stage ownership at the seam (booster max.X <= seam, sustainer
    min.X >= seam) and an overall envelope of exactly +-length/2
  - actual body width/height at the seam cross-section matches the config
  - booster outer band matches the sustainer outer band across a 60 mm slab
    each side of the seam: after removing the common central cylinder of
    radius min(width,height)*0.31+8 (so the differing internal nozzle/dish
    recesses are ignored), the slabs are translated to a common origin and the
    symmetric BREP difference is compared in both directions
  - zero taper on either side: the front and rear half slabs of each band are
    congruent after the same central-cylinder removal
  - the section extent matches the full 60 mm extrusion of the config profile
    (guards the case where both full bands are congruent because both taper
    identically)
  - sustainer/booster fins contact their bodies and mounts contact the
    sustainer body
  - all four inlet cuts are open: a probe at the source cutter's middle
    station, at the actual corner centers, is clear of every part and its
    center lies inside the sustainer body's bounding box (the body-exterior
    anchor; build123d 0.11.1 has no bodyextpoint API)
  - nozzles contact their bodies (coincident boundary is acceptable) and the
    body does not intrude into the nozzle backing
"""

import json
import math
from pathlib import Path

from cadgen import build123d as bd, read_step

from halberd_shoulder_variants import VARIANTS

ROOT = Path(__file__).parent
TOL = 1e-4
VOLUME_TOL = 1e-3
SLAB = 60.0
HALF = SLAB / 2.0
CYLINDER_MARGIN = 8.0
CYLINDER_SCALE = 0.31
BACKING_PROBE = (1.0, 8.0, 8.0)
BACKING_MIN_VOLUME = 60.0
INLET_PROBE = (8.0, 6.0, 6.0)
CORNER_SIGNS = ((1, 1), (1, -1), (-1, -1), (-1, 1))


def intersection_volume(left, right):
    intersection = left & right
    return 0.0 if intersection is None else intersection.volume


def symmetric_diff_volumes(left, right):
    """Volumes of (left - right) and (right - left); both must be <= tol."""
    first = left - right
    second = right - left
    return (
        0.0 if first is None else first.volume,
        0.0 if second is None else second.volume,
    )


def crop_slab(part, x0, x1):
    box = bd.Box(x1 - x0, 2000.0, 2000.0).translate(
        ((x0 + x1) / 2.0, 0.0, 0.0), transform=True
    )
    return part & box


def outer_band(part, x0, x1, cylinder_radius):
    """Slab [x0, x1] of part with the common central cylinder removed."""
    slab = crop_slab(part, x0, x1)
    cylinder = bd.Cylinder(cylinder_radius, x1 - x0 + 2.0).rotate(
        bd.Axis.Y, 90.0
    ).translate(((x0 + x1) / 2.0, 0.0, 0.0), transform=True)
    return slab - cylinder


def check_outer_bands(parts, cfg, seam):
    """Booster vs sustainer outer contour at the seam, plus taper and extent."""
    cylinder_radius = min(cfg["width"], cfg["height"]) * CYLINDER_SCALE + CYLINDER_MARGIN
    sustainer_band = outer_band(parts["sustainer_body"], seam, seam + SLAB, cylinder_radius)
    booster_band = outer_band(parts["booster_body"], seam - SLAB, seam, cylinder_radius)
    sustainer_band = sustainer_band.moved(bd.Location((-seam, 0.0, 0.0)))
    booster_band = booster_band.moved(bd.Location((-(seam - SLAB), 0.0, 0.0)))

    full = symmetric_diff_volumes(sustainer_band, booster_band)

    front_box = bd.Box(HALF, 2000.0, 2000.0).translate((HALF / 2.0, 0.0, 0.0), transform=True)
    rear_box = bd.Box(HALF, 2000.0, 2000.0).translate(
        (HALF + HALF / 2.0, 0.0, 0.0), transform=True
    )
    shift = bd.Location((-HALF, 0.0, 0.0))
    sustainer_halves = symmetric_diff_volumes(
        sustainer_band & front_box, (sustainer_band & rear_box).moved(shift)
    )
    booster_halves = symmetric_diff_volumes(
        booster_band & front_box, (booster_band & rear_box).moved(shift)
    )

    expected = bd.loft(
        [
            bd.RectangleRounded(cfg["height"], cfg["width"], cfg["corner"])
            .rotate(bd.Axis.Y, 90.0)
            .translate((0.0, 0.0, 0.0)),
            bd.RectangleRounded(cfg["height"], cfg["width"], cfg["corner"])
            .rotate(bd.Axis.Y, 90.0)
            .translate((SLAB, 0.0, 0.0)),
        ],
        ruled=True,
    )
    expected_band = expected - bd.Cylinder(cylinder_radius, SLAB + 2.0).rotate(
        bd.Axis.Y, 90.0
    ).translate((SLAB / 2.0, 0.0, 0.0), transform=True)
    extent_sustainer = symmetric_diff_volumes(expected_band, sustainer_band)
    extent_booster = symmetric_diff_volumes(expected_band, booster_band)

    return {
        "cylinder_radius_mm": cylinder_radius,
        "full_band_mm3": {
            "sustainer_minus_booster": full[0],
            "booster_minus_sustainer": full[1],
        },
        "half_slab_sustainer_mm3": {
            "front_minus_rear": sustainer_halves[0],
            "rear_minus_front": sustainer_halves[1],
        },
        "half_slab_booster_mm3": {
            "front_minus_rear": booster_halves[0],
            "rear_minus_front": booster_halves[1],
        },
        "extrusion_match_mm3": {
            "expected_minus_sustainer": extent_sustainer[0],
            "sustainer_minus_expected": extent_sustainer[1],
            "expected_minus_booster": extent_booster[0],
            "booster_minus_expected": extent_booster[1],
        },
    }


def check_inlet_probes(parts, cfg):
    """Probe each inlet cut at the source cutter's middle station."""
    corner = cfg["corner"]
    x_mid = cfg["inlet_x"] - cfg["inlet_length"] / 2.0
    body_bounds = parts["sustainer_body"].bounding_box()
    results = []
    for index, (sy, sz) in enumerate(CORNER_SIGNS):
        y = sy * (cfg["width"] / 2.0 - corner + corner / math.sqrt(2.0))
        z = sz * (cfg["height"] / 2.0 - corner + corner / math.sqrt(2.0))
        angle = math.degrees(math.atan2(sy, sz))
        probe = (
            bd.Box(*INLET_PROBE)
            .translate((x_mid, 0.0, 0.0), transform=True)
            .rotate(bd.Axis.X, -angle)
            .translate((0.0, y, z), transform=True)
        )
        blocked_by = [
            label
            for label, part in parts.items()
            if intersection_volume(part, probe) > VOLUME_TOL
        ]
        anchored = (
            body_bounds.min.X <= x_mid <= body_bounds.max.X
            and body_bounds.min.Y <= y <= body_bounds.max.Y
            and body_bounds.min.Z <= z <= body_bounds.max.Z
        )
        results.append(
            {
                "index": index,
                "angle_degrees": angle,
                "probe_center_mm": [x_mid, y, z],
                "blocked_by": blocked_by,
                "anchored_in_body_bbox": anchored,
            }
        )
    return results


def check_nozzles(parts):
    results = {}
    for nozzle_label, body_label in (
        ("sustainer_nozzle", "sustainer_body"),
        ("booster_nozzle", "booster_body"),
    ):
        nozzle, body = parts[nozzle_label], parts[body_label]
        rear_face = nozzle.bounding_box().max.X - 4.5
        probe = bd.Box(*BACKING_PROBE).translate((rear_face, 0.0, 0.0), transform=True)
        results[nozzle_label] = {
            "distance_to_body_mm": nozzle.distance_to(body),
            "body_backing_intrusion_mm3": intersection_volume(body, probe),
            "nozzle_backing_material_mm3": intersection_volume(nozzle, probe),
        }
    return results


def check_variant(key):
    cfg = VARIANTS[key]
    half = cfg["length"] / 2.0
    seam = -cfg["length"] * 0.1
    model = read_step(ROOT / f"Halberd_{key}.step")
    parts = {part.label: part for part in model.children}
    assert model.label == key, f"{key}: model label {model.label!r}"
    assert len(parts) == len(model.children), f"{key}: duplicate labels"

    for label, part in parts.items():
        assert len(part.solids()) == 1, f"{key}/{label}: expected one closed solid"
        assert part.is_valid, f"{key}/{label}: invalid BREP"
        assert part.volume > 0.0, f"{key}/{label}: nonpositive volume"

    bounds = model.bounding_box()
    assert abs(bounds.min.X + half) < TOL, f"{key}: tail datum {bounds.min.X}"
    assert abs(bounds.max.X - half) < TOL, f"{key}: nose datum {bounds.max.X}"
    assert abs(bounds.size.X - cfg["length"]) < TOL, f"{key}: overall length"

    for label, part in parts.items():
        part_bounds = part.bounding_box()
        if label.startswith("booster_"):
            assert part_bounds.max.X <= seam + TOL, f"{key}/{label}: booster past seam"
        else:
            assert part_bounds.min.X >= seam - TOL, f"{key}/{label}: sustainer behind seam"

    thin = crop_slab(parts["sustainer_body"], seam, seam + 2.0)
    section_bounds = thin.bounding_box()
    assert abs(section_bounds.size.Y - cfg["width"]) < TOL, (
        f"{key}: seam width {section_bounds.size.Y} != {cfg['width']}"
    )
    assert abs(section_bounds.size.Z - cfg["height"]) < TOL, (
        f"{key}: seam height {section_bounds.size.Z} != {cfg['height']}"
    )

    bands = check_outer_bands(parts, cfg, seam)
    for group in ("full_band_mm3", "half_slab_sustainer_mm3",
                  "half_slab_booster_mm3", "extrusion_match_mm3"):
        for direction, volume in bands[group].items():
            assert volume <= VOLUME_TOL, f"{key}: {group}.{direction} = {volume}"

    probes = check_inlet_probes(parts, cfg)
    for probe in probes:
        assert not probe["blocked_by"], f"{key}: inlet probe {probe['index']} blocked"
        assert probe["anchored_in_body_bbox"], (
            f"{key}: inlet probe {probe['index']} outside sustainer body bbox"
        )

    for index in range(1, 5):
        assert parts[f"sustainer_fin_{index}"].distance_to(parts["sustainer_body"]) < TOL, (
            f"{key}: sustainer_fin_{index} no body contact"
        )
        assert parts[f"booster_fin_{index}"].distance_to(parts["booster_body"]) < TOL, (
            f"{key}: booster_fin_{index} no body contact"
        )
    for index in range(1, cfg["mounts"] + 1):
        assert parts[f"mount_{index}"].distance_to(parts["sustainer_body"]) < TOL, (
            f"{key}: mount_{index} no body contact"
        )

    nozzles = check_nozzles(parts)
    for nozzle_label, record in nozzles.items():
        assert record["distance_to_body_mm"] < TOL, f"{key}: {nozzle_label} disconnected"
        assert record["body_backing_intrusion_mm3"] < VOLUME_TOL, (
            f"{key}: {nozzle_label} body backing intrusion"
        )
        assert record["nozzle_backing_material_mm3"] > BACKING_MIN_VOLUME, (
            f"{key}: {nozzle_label} missing backing"
        )

    report = {
        "file": f"Halberd_{key}.step",
        "label": key,
        "part_count": len(parts),
        "labels": sorted(parts),
        "model_bbox_mm": {
            "min": list(bounds.min),
            "max": list(bounds.max),
            "size": list(bounds.size),
        },
        "seam_mm": seam,
        "seam_section_mm": {
            "width": section_bounds.size.Y,
            "height": section_bounds.size.Z,
            "config_width": cfg["width"],
            "config_height": cfg["height"],
        },
        "outer_band": bands,
        "inlet_probes": probes,
        "nozzles": nozzles,
    }
    print(
        f"PASS: {key} -- {len(parts)} uniquely labeled parts, length "
        f"{bounds.size.X:.0f} mm, seam section {section_bounds.size.Y:.0f}x"
        f"{section_bounds.size.Z:.0f} mm, outer bands match, zero taper, "
        f"{len(probes)} open inlet probes."
    )
    return report


def main():
    reports = [check_variant(key) for key in VARIANTS]
    output = {
        "ok": True,
        "generated": "2026-09-14",
        "method": (
            "60 mm slabs each side of the seam; common central cylinder of radius "
            "min(width,height)*0.31+8 removed so internal nozzle/dish recesses are "
            "ignored; slabs translated to a common origin; symmetric BREP difference "
            "compared in both directions (volume <= 1e-3 mm3); half slabs compared "
            "for zero taper; section extent matched against the full 60 mm extrusion "
            "of the config profile. Config constants read from "
            "halberd_shoulder_variants.py; build factories never called."
        ),
        "tolerances_mm3": VOLUME_TOL,
        "variants": reports,
        "scope": "CAD exterior silhouette studies; aircraft rack fit and runtime not verified",
    }
    (ROOT / "Halberd_Shoulder_Variant_Checks.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    print("PASS: all five shoulder variant checks; report written to Halberd_Shoulder_Variant_Checks.json")


if __name__ == "__main__":
    main()