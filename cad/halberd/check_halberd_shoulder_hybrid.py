"""Deterministic STEP checks for the selected Halberd shoulder hybrid.

Reads only the exported STEP file plus the config constants from
generate_halberd_shoulder_hybrid.py (LENGTH, HALF, SEAM, WIDTH, CORNER,
NOSE_BASE, ANGLES). The build factory is never called: every assertion
measures the actual STEP geometry.

Per the hybrid spec this verifies:
   - 19 unique labels, one positive-volume valid solid per label
  - overall envelope exactly +-LENGTH/2 and strict stage ownership at the
    seam (booster max.X <= SEAM, sustainer min.X >= SEAM)
  - seam section extents match WIDTH x WIDTH with CORNER rounding
  - booster/sustainer outer 60 mm bands match at the seam: reuses
    check_outer_bands from check_halberd_shoulder_variants.py with the
    hybrid's WIDTH/HEIGHT/CORNER config (0 difference expected)
   - circular forebody: 2 mm slabs at x=960 and x=1000 match a radius-86
    cylinder (BREP symmetric difference ~0), and the radome base at
    NOSE_BASE matches the same radius
  - rear corner progression: booster section extrema and corner radii at
    the five loft stations match the generator config, ending at CORNER=12
    equal to the sustainer's seam corner (12-corner body evidence)
  - fins/nozzles/mounts/intake floors contact their bodies
   - four clear intake cavity probes at x=650, radial 110, angles
    45/135/225/315 (derived from the source cavity loft stations)
  - nozzles contact their bodies with no body backing intrusion
"""

import json
import math
from pathlib import Path

from cadgen import build123d as bd, read_step

from check_halberd_shoulder_variants import (
    check_outer_bands,
    check_nozzles,
    crop_slab,
    intersection_volume,
    symmetric_diff_volumes,
)
from generate_halberd_shoulder_hybrid import (
    LENGTH,
    HALF,
    SEAM,
    WIDTH,
    CORNER,
    NOSE_BASE,
    ANGLES,
    NOSE_CYLINDER_RADIUS,
    TRANSITION_END_X,
)

ROOT = Path(__file__).parent
TOL = 1e-4
VOLUME_TOL = 1e-3
FOREBODY_RADIUS = 86.0
# Booster loft stations from generate_halberd_shoulder_hybrid.py:
#   section(-HALF, WIDTH*.8, WIDTH*.8, 62.4)
#   section(-HALF+240, WIDTH, WIDTH, 78)
#   section(-1000, WIDTH, WIDTH, 64)
#   section(SEAM-180, WIDTH, WIDTH, CORNER)
#   section(SEAM, WIDTH, WIDTH, CORNER)
# direction: +1 slab [x, x+0.5] (loft starts at x), -1 slab [x-0.5, x] (loft ends at x).
BOOSTER_STATIONS = (
    (-HALF, WIDTH * 0.8, 62.4, 1),
    (-HALF + 240, WIDTH, 78.0, 1),
    (-1000.0, WIDTH, 64.0, 1),
    (SEAM - 180, WIDTH, CORNER, 1),
    (SEAM, WIDTH, CORNER, -1),
)
# Covered cavity: aft x340/r117, middle x535/r116, mouth x780..815/r111.
# At x=650 the uncut 192 mm section with 32 mm corners reaches radial 122.51.
# Radial 110 is INSIDE that original skin, so an absent cut would fail this test.
PROBE_X = 650.0
PROBE_RADIAL = 110.0
INLET_PROBE = (2.0, 4.0, 4.0)


def section_extents(part, x, direction):
    """Y/Z extents of a 0.5 mm slab just inside the part at station x."""
    if direction > 0:
        slab = part & bd.Box(0.5, 2000.0, 2000.0).translate(
            (x + 0.25, 0.0, 0.0), transform=True
        )
    else:
        slab = part & bd.Box(0.5, 2000.0, 2000.0).translate(
            (x - 0.25, 0.0, 0.0), transform=True
        )
    bounds = slab.bounding_box()
    return bounds.size.Y, bounds.size.Z


def corner_radius(part, x, direction):
    """Corner radius of the rounded-square section at station x.

    Axis half-extent a comes from the slab bbox; the diagonal half-extent d
    is found by binary search along y=z. For a rounded square with corner r:
    d = sqrt(2)*a - r*(sqrt(2)-1), so r = (sqrt(2)*a - d)/(sqrt(2)-1).
    """
    width, _ = section_extents(part, x, direction)
    a = width / 2.0
    px = x + 0.25 if direction > 0 else x - 0.25
    lo, hi = 0.0, a * math.sqrt(2.0)
    for _ in range(50):
        mid = (lo + hi) / 2.0
        c = mid / math.sqrt(2.0)
        probe = bd.Box(0.5, 0.5, 0.5).translate((px, c, c), transform=True)
        if intersection_volume(part, probe) > 0.05:
            lo = mid
        else:
            hi = mid
    d = (lo + hi) / 2.0
    return a, d, (math.sqrt(2.0) * a - d) / (math.sqrt(2.0) - 1.0)


def check_circular_forebody(parts):
    """2 mm slabs at x=960/1000 vs a radius-86 cylinder; radome base match."""
    results = {}
    for x in (860.0, 900.0, 960.0, 1000.0):
        slab = crop_slab(parts["sustainer_body"], x - 1.0, x + 1.0)
        cylinder = bd.Cylinder(FOREBODY_RADIUS, 2.0).rotate(
            bd.Axis.Y, 90.0
        ).translate((x, 0.0, 0.0), transform=True)
        first, second = symmetric_diff_volumes(slab, cylinder)
        results[f"x{x:.0f}_mm3"] = {
            "slab_minus_cylinder": first,
            "cylinder_minus_slab": second,
        }
    # Body forebody end at NOSE_BASE is the loft endpoint disk(NOSE_BASE, 86).
    slab = crop_slab(parts["sustainer_body"], NOSE_BASE - 2.0, NOSE_BASE)
    cylinder = bd.Cylinder(FOREBODY_RADIUS, 2.0).rotate(
        bd.Axis.Y, 90.0
    ).translate((NOSE_BASE - 1.0, 0.0, 0.0), transform=True)
    first, second = symmetric_diff_volumes(slab, cylinder)
    results[f"x{NOSE_BASE:.0f}_mm3"] = {
        "slab_minus_cylinder": first,
        "cylinder_minus_slab": second,
    }
    return results


def check_radome_base(parts):
    """Radome base cross-section at NOSE_BASE matches the radius-86 forebody."""
    radome = parts["radome"]
    base_slab = radome & bd.Box(1.0, 2000.0, 2000.0).translate(
        (NOSE_BASE + 0.5, 0.0, 0.0), transform=True
    )
    bounds = base_slab.bounding_box()
    return {
        "base_x_mm": radome.bounding_box().min.X,
        "base_diameter_y_mm": bounds.size.Y,
        "base_diameter_z_mm": bounds.size.Z,
        "expected_diameter_mm": FOREBODY_RADIUS * 2.0,
    }


def check_rear_corner_progression(parts):
    """Booster section extrema and corner radii at the five loft stations."""
    booster = parts["booster_body"]
    results = []
    for x, expected_extent, expected_corner, direction in BOOSTER_STATIONS:
        width, height = section_extents(booster, x, direction)
        a, d, corner = corner_radius(booster, x, direction)
        results.append(
            {
                "x_mm": x,
                "section_mm": {"width": width, "height": height},
                "config_extent_mm": expected_extent,
                "corner_radius_mm": corner,
                "config_corner_mm": expected_corner,
            }
        )
    return results


def check_intake_probes(parts):
    """Probe each inlet cavity inside the nominal uncut hull at x=650/r=110."""
    body_bounds = parts["sustainer_body"].bounding_box()
    results = []
    for index, angle in enumerate(ANGLES, 1):
        y = PROBE_RADIAL * math.sin(math.radians(angle))
        z = PROBE_RADIAL * math.cos(math.radians(angle))
        probe = (
            bd.Box(*INLET_PROBE)
            .translate((PROBE_X, 0.0, 0.0), transform=True)
            .rotate(bd.Axis.X, -angle)
            .translate((0.0, y, z), transform=True)
        )
        blocked_by = [
            label
            for label, part in parts.items()
            if intersection_volume(part, probe) > VOLUME_TOL
        ]
        anchored = (
            body_bounds.min.X <= PROBE_X <= body_bounds.max.X
            and body_bounds.min.Y <= y <= body_bounds.max.Y
            and body_bounds.min.Z <= z <= body_bounds.max.Z
        )
        results.append(
            {
                "index": index,
                "angle_degrees": angle,
                "probe_center_mm": [PROBE_X, y, z],
                "blocked_by": blocked_by,
                "anchored_in_body_bbox": anchored,
            }
        )
    return results


def check_recessed_intakes(parts):
    """Photo contract: subtract corners, retain native skin, never add outer cowls."""
    assert NOSE_CYLINDER_RADIUS == 86 and TRANSITION_END_X == 850
    def square(x, width, radius):
        return bd.RectangleRounded(width,width,radius).rotate(bd.Axis.Y,90).translate((x,0,0))
    def circle(x):
        return bd.Circle(86).rotate(bd.Axis.Y,90).translate((x,0,0))
    # Independent envelope specification from the pre-cowl hybrid.
    envelope = bd.loft([square(SEAM,208,12),square(400,208,12),square(650,192,32),
                        circle(850),circle(1080)],ruled=True)
    body = parts["sustainer_body"]
    excess = robust_boolean_volume(body,envelope,difference=True)
    assert excess < VOLUME_TOL, ("body exceeds unbroken transition",excess)
    for i in range(1,5):
        assert robust_boolean_volume(parts[f"intake_floor_{i}"],envelope,difference=True) < VOLUME_TOL
    # The corrected red-outline brief explicitly forbids any forward extension.
    # Restore the complete original cylinder from X850 to the radome base.
    spine = bd.Cylinder(86,230).rotate(bd.Axis.Y,90).translate((965,0,0))
    assert robust_boolean_volume(spine,body,difference=True) < VOLUME_TOL
    central_core = bd.Cylinder(44,465).rotate(bd.Axis.Y,90).translate((582.5,0,0))
    assert robust_boolean_volume(central_core,body,difference=True) < VOLUME_TOL
    internal_paths=[]
    for i,angle in enumerate(ANGLES,1):
        aligned_body=body.rotate(bd.Axis.X,angle)
        aligned_envelope=envelope.rotate(bd.Axis.X,angle)
        samples=[]
        for station in (400,470,535,600,620):
            # This quadrant contains one complete buried passage, not the other
            # three cuts or the exposed entrance whose centroid is skin-clipped.
            slab=bd.Box(2,80,180).translate((station,0,90))
            void=(aligned_envelope & slab) - (aligned_body & slab)
            assert void is not None and void.volume > 10, (i,"missing buried passage",station)
            center=void.center(bd.CenterOf.MASS)
            assert abs(center.Y) < .01, (i,"off-plane passage",station)
            samples.append({"x_mm":station,"radial_center_mm":center.Z})
        radii=[sample["radial_center_mm"] for sample in samples]
        assert all(b-a > 1 for a,b in zip(radii,radii[1:])), (i,"passage does not move inward aft",samples)
        assert radii[0] < 80 and radii[-1] > 95, (i,"insufficient inward movement",samples)
        internal_paths.append({"index":i,"samples":samples})
    roofs=[]
    for i,angle in enumerate(ANGLES,1):
        occupied=[]
        for x,radial in ((450,133),(535,128.5)):
            witness=bd.Box(2,2,1).translate((x,0,radial)).rotate(bd.Axis.X,-angle)
            volume=intersection_volume(body,witness)
            assert volume > 3.99, (i,"lost original shoulder roof",x,volume)
            occupied.append(volume)
        for lateral in (-26,26):
            side_skin=bd.Box(2,.5,.5).translate((535,lateral,114)).rotate(bd.Axis.X,-angle)
            assert intersection_volume(body,side_skin) > .499, (i,"premature side breakout",lateral)
        clear=bd.Box(2,.5,.5).translate((795,0,86.75)).rotate(bd.Axis.X,-angle)
        for label,part in parts.items():
            assert intersection_volume(part,clear) < VOLUME_TOL, (i,"inboard opening blocked",label)
        keep=bd.Box(2,.5,.5).translate((795,0,80)).rotate(bd.Axis.X,-angle)
        assert intersection_volume(body,keep) > .499, (i,"support below ramp removed")
        roofs.append({"index":i,"native_roof_volumes_mm3":occupied})
    # Compare removed section area to the original four-intake cutter on this SAME hull.
    before=crop_slab(envelope,649,651)
    after=crop_slab(body,649,651)
    removed=robust_boolean_volume(before,after,difference=True)
    old=bd.loft([bd.Ellipse(h,w).rotate(bd.Axis.Y,90).translate((x,0,r))
                 for x,r,w,h in ((350,113,17,10),(535,123,23,15),(790,114,25,20))],ruled=True)
    old=old.rotate(bd.Axis.X,-45)
    old_removed=robust_boolean_volume(before,old)*4
    assert old_removed > 1
    assert removed > old_removed*1.3, ("corner opening not enlarged",removed,old_removed)
    return {"protruding_body_volume_mm3":excess,"round_forebody_restored_at_x_mm":850,
            "internal_paths":internal_paths,
            "native_roofs":roofs,"new_corner_area_at_650_mm2":removed/2,
            "original_cutter_area_same_hull_mm2":old_removed/2,"area_ratio":removed/old_removed}


def robust_boolean_volume(left, right, difference=False):
    """Same full-volume Boolean, with 1e-6 mm fuzz for tangent/coplanar faces.

    build123d's default parallel common operation stalls on the exact tangent
    forebody/mouth junction. No aperture inset or region is omitted here.
    """
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut
    from OCP.TopTools import TopTools_ListOfShape
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    args, tools = TopTools_ListOfShape(), TopTools_ListOfShape()
    args.Append(left.wrapped)
    tools.Append(right.wrapped)
    operation = BRepAlgoAPI_Cut() if difference else BRepAlgoAPI_Common()
    operation.SetArguments(args)
    operation.SetTools(tools)
    operation.SetRunParallel(False)
    operation.SetFuzzyValue(1e-6)
    operation.Build()
    assert operation.IsDone(), "Tangent aperture intersection failed"
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(operation.Shape(), props)
    return props.Mass()


def check_contacts(parts):
    results = {}
    for index in range(1, 5):
        results[f"sustainer_fin_{index}"] = parts[f"sustainer_fin_{index}"].distance_to(
            parts["sustainer_body"]
        )
        results[f"booster_fin_{index}"] = parts[f"booster_fin_{index}"].distance_to(
            parts["booster_body"]
        )
        results[f"intake_floor_{index}"] = parts[f"intake_floor_{index}"].distance_to(
            parts["sustainer_body"]
        )
    for index in (1, 2):
        results[f"mount_{index}"] = parts[f"mount_{index}"].distance_to(
            parts["sustainer_body"]
        )
    return results


def check_floor_blend(parts):
    """Curved continuation of the original ellipse, confined to the intake footprint."""
    solid=parts["sustainer_body"].solids()[0]
    stations=(700,730,760,780,790,800,810,820,830,840,849,849.9,850,850.1,851,900,950)
    controls=(82,82+12*(3/170),82+24*(3/170),86,86,86)
    original_cylinder=bd.Cylinder(86,100).rotate(bd.Axis.Y,90).translate((900,0,0))
    restored=crop_slab(parts["sustainer_body"],850,950)
    removed=robust_boolean_volume(original_cylinder,restored,difference=True)
    excess=robust_boolean_volume(restored,original_cylinder,difference=True)
    assert removed < VOLUME_TOL and excess < VOLUME_TOL, ("extension remains past original intake end",removed,excess)
    results=[]
    for index,angle in enumerate(ANGLES,1):
        sy,sz=math.sin(math.radians(angle)),math.cos(math.radians(angle))
        measured={}
        for x in stations:
            assert solid.is_inside((x,76*sy,76*sz)), (index,x,"missing floor")
            assert not solid.is_inside((x,95*sy,95*sz)), (index,x,"blocked blend")
            # Intersect the actual faces. Binary point classification is ambiguous
            # on the tangent seam itself (X950); it can inherit edge tolerances.
            hits=solid.find_intersection_points(bd.Axis((x,0,0),(0,sy,sz)))
            radius=min(q.Y*sy+q.Z*sz for q,_ in hits if q.Y*sy+q.Z*sz > 0)
            t=(x-790)/60
            if x<=790: expected=79+(x-620)*3/170
            elif x<850: expected=sum(math.comb(5,i)*(1-t)**(5-i)*t**i*r for i,r in enumerate(controls))
            else: expected=86
            assert abs(radius-expected)<.001, (index,x,radius,expected)
            measured[x]=radius
        # Follow the intake ellipse across the width, rejecting the previous flat ramp.
        for x in (800,820):
            for lateral in (-8,8):
                hits=solid.find_intersection_points(bd.Axis((x,lateral*sz,-lateral*sy),(0,sy,sz)))
                height=min(q.Y*sy+q.Z*sz for q,_ in hits if q.Y*sy+q.Z*sz > 0)
                expected_offset=24*(1-math.sqrt(1-(lateral/42)**2))
                assert abs(height-measured[x]-expected_offset) < .001, (index,x,"floor does not follow intake curvature",lateral)
        slope=(measured[850.1]-measured[849.9])/.2
        curvature=(measured[849.9]-2*measured[850]+measured[850.1])/.01
        assert abs(slope)<1e-4 and abs(curvature)<1e-4, (index,"non-smooth cylinder join",slope,curvature)
        results.append({"index":index,"floor_radius_by_x_mm":measured,"missing_cylinder_850_950_mm3":removed,
                        "join_slope_mm_per_mm":slope,"join_curvature_per_mm":curvature,"join_sampling_step_mm":.1})
    return results


def main():
    model = read_step(ROOT / "Halberd_Shoulder_Hybrid.step")
    parts = {part.label: part for part in model.children}
    assert model.label == "Halberd_Shoulder_Hybrid", f"model label {model.label!r}"
    assert len(parts) == len(model.children), "duplicate labels"
    expected = {"sustainer_body","booster_body","radome","sustainer_nozzle","booster_nozzle","mount_1","mount_2"}
    expected.update(f"{prefix}_{i}" for prefix in ("intake_floor","sustainer_fin","booster_fin") for i in range(1,5))
    assert set(parts) == expected, f"Missing or unexpected labels: {set(parts)^expected}"
    assert len(parts) == 19, f"expected 19 parts, found {len(parts)}"

    for label, part in parts.items():
        assert len(part.solids()) == 1, f"{label}: expected one closed solid"
        assert part.is_valid, f"{label}: invalid BREP"
        assert part.volume > 0.0, f"{label}: nonpositive volume"

    bounds = model.bounding_box()
    assert abs(bounds.min.X + HALF) < TOL, f"tail datum {bounds.min.X}"
    assert abs(bounds.max.X - HALF) < TOL, f"nose datum {bounds.max.X}"
    assert abs(bounds.size.X - LENGTH) < TOL, f"overall length {bounds.size.X}"

    for label, part in parts.items():
        part_bounds = part.bounding_box()
        if label.startswith("booster_"):
            assert part_bounds.max.X <= SEAM + TOL, f"{label}: booster past seam"
        else:
            assert part_bounds.min.X >= SEAM - TOL, f"{label}: sustainer behind seam"

    thin = crop_slab(parts["sustainer_body"], SEAM, SEAM + 2.0)
    section_bounds = thin.bounding_box()
    assert abs(section_bounds.size.Y - WIDTH) < TOL, f"seam width {section_bounds.size.Y}"
    assert abs(section_bounds.size.Z - WIDTH) < TOL, f"seam height {section_bounds.size.Z}"

    cfg = {"width": WIDTH, "height": WIDTH, "corner": CORNER}
    bands = check_outer_bands(parts, cfg, SEAM)
    for group in ("full_band_mm3", "half_slab_sustainer_mm3",
                  "half_slab_booster_mm3", "extrusion_match_mm3"):
        for direction, volume in bands[group].items():
            assert volume <= VOLUME_TOL, f"{group}.{direction} = {volume}"

    forebody = check_circular_forebody(parts)
    for station, record in forebody.items():
        for direction, volume in record.items():
            assert volume <= VOLUME_TOL, f"forebody {station}.{direction} = {volume}"

    radome_base = check_radome_base(parts)
    assert abs(radome_base["base_x_mm"] - NOSE_BASE) < TOL, (
        f"radome base x {radome_base['base_x_mm']}"
    )
    for axis in ("base_diameter_y_mm", "base_diameter_z_mm"):
        assert abs(radome_base[axis] - radome_base["expected_diameter_mm"]) < 0.1, (
            f"radome {axis} {radome_base[axis]}"
        )

    progression = check_rear_corner_progression(parts)
    for record in progression:
        assert abs(record["section_mm"]["width"] - record["config_extent_mm"]) < 0.5, (
            f"booster x={record['x_mm']} width {record['section_mm']['width']}"
        )
        assert abs(record["section_mm"]["height"] - record["config_extent_mm"]) < 0.5, (
            f"booster x={record['x_mm']} height {record['section_mm']['height']}"
        )
        assert abs(record["corner_radius_mm"] - record["config_corner_mm"]) < 2.0, (
            f"booster x={record['x_mm']} corner {record['corner_radius_mm']}"
        )
    # 12-corner body evidence: the sustainer seam corner equals the booster's.
    _, _, sustainer_seam_corner = corner_radius(parts["sustainer_body"], SEAM, 1)
    assert abs(sustainer_seam_corner - CORNER) < 2.0, (
        f"sustainer seam corner {sustainer_seam_corner}"
    )

    contacts = check_contacts(parts)
    for label, distance in contacts.items():
        assert distance < TOL, f"{label}: no body contact (distance {distance})"

    probes = check_intake_probes(parts)
    for probe in probes:
        assert not probe["blocked_by"], (
            f"inlet probe {probe['index']} blocked by {probe['blocked_by']}"
        )
        assert probe["anchored_in_body_bbox"], (
            f"inlet probe {probe['index']} outside sustainer body bbox"
        )
    recessed = check_recessed_intakes(parts)

    nozzles = check_nozzles(parts)
    for nozzle_label, record in nozzles.items():
        assert record["distance_to_body_mm"] < TOL, f"{nozzle_label} disconnected"
        assert record["body_backing_intrusion_mm3"] < VOLUME_TOL, (
            f"{nozzle_label} body backing intrusion"
        )
        assert record["nozzle_backing_material_mm3"] > 60.0, (
            f"{nozzle_label} missing backing"
        )
    floor_blend=check_floor_blend(parts)

    report = {
        "file": "Halberd_Shoulder_Hybrid.step",
        "label": "Halberd_Shoulder_Hybrid",
        "part_count": len(parts),
        "labels": sorted(parts),
        "model_bbox_mm": {
            "min": list(bounds.min),
            "max": list(bounds.max),
            "size": list(bounds.size),
        },
        "seam_mm": SEAM,
        "seam_section_mm": {
            "width": section_bounds.size.Y,
            "height": section_bounds.size.Z,
            "config_width": WIDTH,
            "config_height": WIDTH,
        },
        "outer_band": bands,
        "circular_forebody_mm3": forebody,
        "radome_base": radome_base,
        "rear_corner_progression": progression,
        "sustainer_seam_corner_mm": sustainer_seam_corner,
        "contacts_mm": contacts,
        "intake_probes": probes,
        "recessed_intakes": recessed,
        "nozzles": nozzles,
        "smooth_intake_floor": floor_blend,
    }
    output = {
        "ok": True,
        "generated": "2026-09-14",
        "method": (
            "Reads only Halberd_Shoulder_Hybrid.step plus the config constants "
            "from generate_halberd_shoulder_hybrid.py; the build factory is never "
            "called. Outer 60 mm bands reuse check_outer_bands from "
            "check_halberd_shoulder_variants.py with width=208 height=208 "
            "corner=12 (0 difference expected). Circular forebody: 2 mm BREP "
            "slabs at x=960/1000 and the body end at x=1080 compared against a "
            "radius-86 cylinder; radome base cross-section at x=1080 must be "
            "172 mm. Rear corner progression: booster section extrema and corner "
            "radii at the five loft stations (62.4 -> 78 -> 64 -> 12 -> 12) with "
            "the seam corner equal to the sustainer's 12-corner body. Intake "
            "probes at x=650, radial110; no excess beyond original transition "
            "envelope, retained native roof witnesses, curved intake continuation "
            "and complete cylinder restoration beyond the original X850 end, "
            "measured buried-void centroids decreasing radially toward the rear, "
            "inboard opening clearance and enlarged cut area against the original "
            "four-intake cutter on the same envelope."
        ),
        "tolerances_mm3": VOLUME_TOL,
        "hybrid": report,
        "scope": "CAD exterior game visuals; aircraft rack fit and runtime not verified",
    }
    (ROOT / "Halberd_Shoulder_Hybrid_Checks.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"PASS: Halberd_Shoulder_Hybrid -- {len(parts)} uniquely labeled parts, "
        f"length {bounds.size.X:.0f} mm, seam section {section_bounds.size.Y:.0f}x"
        f"{section_bounds.size.Z:.0f} mm, outer bands match, circular forebody "
        f"radius {FOREBODY_RADIUS:.0f} mm, rear corner progression 62.4->78->64->12->12, "
        f"{len(probes)} open intake probes."
    )
    print(f"PASS: zero intake protrusion, retained shoulder roofs, circular forebody restored after X850; corner area at x650 is {recessed['area_ratio']:.2f}x the original cutter on the same hull.")
    for path in recessed["internal_paths"]:
        print(f"PASS: intake {path['index']} inward-aft path: {path['samples']}")
    print("PASS: all four floors follow the original elliptical intake curvature; no extension or missing cylinder volume beyond X850.")


if __name__ == "__main__":
    main()
