"""STEP-round-trip regression and interface checks for Ballista RC1.

Run normally for acceptance, or --diagnose for bounds/contact evidence during
source repair. Diagnostic output is never an acceptance result.
"""

import argparse
import json
from math import cos, radians, sin, sqrt
from pathlib import Path

from cadgen import build123d as bd, read_step
from ballista_geometry import (
    AGM68_ENVELOPE, BODY_HEIGHT, BODY_WIDTH, HALF_LENGTH, LATERAL_SCALE,
    LENGTH, NOZZLE_EXIT_X, NOZZLE_DEPTH, SEEKER_GLASS_FRONT,
    SEEKER_WINDOW_WIDTH, SEEKER_WINDOW_HEIGHT, TAIL_RADIUS, WING_ANGLE,
    WING_CHORD, WING_THICKNESS, WING_LENGTH, WING_PIVOT_X, WING_PIVOT_Y, WING_PIVOT_Z,
    WING_RECESS_SHIFT, WING_STOWED_ANGLE, semantic_group,
)

SC = LATERAL_SCALE

ROOT = Path(__file__).parent
TOL = 1e-4
VOLUME_TOL = 1e-3
COMMON_LABELS = {
    "Body", "SeekerWindow", "SeekerBezel", "SeekerSeal", "HybridNozzle", "NozzleExitLip",
    "NozzleRecess", "NozzleRetention", "WingBayLeft", "WingBayRight",
    "MountRail", "ForwardLug", "AftLug", "DorsalUmbilicalCover",
    "WingLeft", "WingRight", "WingLeftPivotCap", "WingRightPivotCap",
    "VentralServiceCover", "SeekerIdentificationBand",
} | {f"Tail{kind}{i}" for kind in ("Control", "Root") for i in range(1,5)} | {
    f"{kind}{side}" for kind in ("AftService", "Avionics", "StowageEdge")
    for side in ("Left", "Right")
} | {f"Intake{side}{kind}" for side in ("Left", "Right")
     for kind in ("Duct", "Ramp", "Splitter1", "Splitter2")} | {
    f"PanelFastener{side}_{x}_{z:g}" for side in ("Left", "Right")
    for x in (-751, -585, 383, 577) for z in (-34*SC, 34*SC)
}


def _parts(model):
    result = {p.label: p for p in model.children}
    assert len(result) == len(model.children), "Duplicate occurrence labels"
    assert set(result) == COMMON_LABELS, f"Label drift: {set(result)^COMMON_LABELS}"
    return result


def _bounds(shape):
    b = shape.bounding_box()
    return {"min": list(b.min), "max": list(b.max), "size": list(b.size)}


def _overlap(a, b):
    intersection = a.intersect(b)
    return 0.0 if intersection is None else sum(s.volume for s in intersection.solids())


def _box_gap(a, b):
    """Conservative Euclidean lower bound; cannot hide a collision."""
    aa, bb = a.bounding_box(), b.bounding_box()
    return sqrt(sum(max(0, amin-bmax, bmin-amax)**2
                    for amin,amax,bmin,bmax in zip(aa.min,aa.max,bb.min,bb.max)))


def _clearance_lower_bound(a, b, required):
    lower = _box_gap(a,b)
    # Exact BREP distance only when enclosing boxes cannot prove clearance.
    return lower if lower >= required else a.distance_to(b)


def _same_geometry(a, b, message):
    # Symmetric difference verifies actual shape, not just equal bbox/volume.
    difference = abs(a.volume + b.volume - 2*_overlap(a,b))
    assert difference < max(VOLUME_TOL, a.volume*1e-8), f"{message}: {difference} mm3"


def _near(a, b, message):
    assert abs(a-b) < TOL, f"{message}: {a} != {b}"


def _common(model, parts):
    for label, p in parts.items():
        assert len(p.solids()) == 1, f"{label}: expected one closed solid"
        assert p.is_valid, f"{label}: invalid BREP"
        assert p.volume > 0, f"{label}: nonpositive volume"
        semantic_group(label)
    b = parts["Body"].bounding_box()
    _near(b.min.X, -HALF_LENGTH, "body tail")
    _near(b.max.X, HALF_LENGTH, "body nose")
    _near(b.size.Y, BODY_WIDTH, "body width")
    _near(b.size.Z, BODY_HEIGHT, "body height")
    _near(b.center().X, 0, "body pivot X")
    _near(b.center().Y, 0, "body pivot Y")
    _near(b.center().Z, 0, "body pivot Z")
    _near(model.bounding_box().size.X, LENGTH, "full length")
    glass = parts["SeekerWindow"].bounding_box()
    _near(glass.max.X, SEEKER_GLASS_FRONT, "glass recessed face")
    _near(glass.size.Y, SEEKER_WINDOW_WIDTH, "glass width")
    _near(glass.size.Z, SEEKER_WINDOW_HEIGHT, "glass height")
    assert _overlap(parts["SeekerWindow"], parts["Body"]) < VOLUME_TOL
    assert _overlap(parts["SeekerWindow"], parts["SeekerBezel"]) < VOLUME_TOL
    assert parts["SeekerSeal"].distance_to(parts["SeekerWindow"]) < TOL
    assert parts["SeekerSeal"].distance_to(parts["SeekerBezel"]) < TOL
    # Visible optical path from outside to just in front of the glass.
    # Match the faceted optic rather than testing a rectangle across its clipped
    # corners. This octagon checks MORE area than the old clipped box.
    x, w, h, c = SEEKER_GLASS_FRONT+0.01, 60.5*SC, 45.0*SC, 20.0*SC
    face = bd.Face(bd.Wire.make_polygon([(x,-w+c,-h),(x,w-c,-h),(x,w,-h+c),
                    (x,w,h-c),(x,w-c,h),(x,-w+c,h),(x,-w,h-c),(x,-w,-h+c)], close=True))
    sight = bd.Solid.extrude(face, (HALF_LENGTH-x+2, 0, 0))
    for label in ("Body", "SeekerBezel", "SeekerSeal"):
        assert _overlap(sight, parts[label]) < VOLUME_TOL, f"Blocked seeker: {label}"
    # A central clear corridor must extend through the modeled nozzle cavity.
    bore = bd.Cylinder(30*SC, NOZZLE_DEPTH-3).rotate(bd.Axis.Y,90).translate(
        (NOZZLE_EXIT_X+(NOZZLE_DEPTH-3)/2,0,0))
    for label in ("Body", "HybridNozzle", "NozzleExitLip", "NozzleRetention", "NozzleRecess"):
        assert _overlap(bore, parts[label]) < VOLUME_TOL, f"Blocked nozzle: {label}"
    assert _overlap(parts["HybridNozzle"], parts["Body"]) < VOLUME_TOL
    _near(parts["HybridNozzle"].bounding_box().min.X, NOZZLE_EXIT_X, "exhaust datum")
    for i in range(1,5):
        assert parts[f"TailRoot{i}"].distance_to(parts["Body"]) < TOL
        assert parts[f"TailControl{i}"].distance_to(parts[f"TailRoot{i}"]) < TOL
    for label in ("MountRail", "ForwardLug", "AftLug", "DorsalUmbilicalCover"):
        owner = "MountRail" if label in ("ForwardLug", "AftLug") else "Body"
        assert parts[label].distance_to(parts[owner]) < TOL, f"Floating {label}"
    for name in ("Left", "Right"):
        assert parts[f"WingBay{name}"].distance_to(parts["Body"]) < TOL, f"Floating wing bay {name}"
        wing = parts[f"Wing{name}"].bounding_box()
        _near(wing.center().Z, WING_PIVOT_Z, "recessed wing datum")
        assert wing.min.Z < -BODY_HEIGHT/2 < wing.max.Z, "Wing must straddle nominal underside skin"
        assert 0.4 < (wing.max.Z+BODY_HEIGHT/2)/wing.size.Z < 0.7, "Wing recess fraction"
        _near(parts[f"WingBay{name}"].bounding_box().max.Z, -120.0*SC, "recessed bay seat")
    _check_intakes(parts)
    _check_recess_smoothing(parts["Body"])


def _check_recess_smoothing(body):
    """Verify real curved BREP faces in the pocket zone after STEP round-trip."""
    counts = {2.0*SC:0, 3.0*SC:0, 6.0*SC:0}
    for face in body.faces():
        b = face.bounding_box()
        if (b.min.X > -620 and b.max.X < 490 and b.max.Z < -118*SC
                and face.geom_type == bd.GeomType.CYLINDER):
            for radius in counts:
                if abs(face.radius-radius) < TOL:
                    counts[radius] += 1
    for radius,count in counts.items():
        assert count >= 2, f"Missing mirrored {radius/SC:.4g} mm (scaled) pocket blends: {counts}"
    print(f"Wing-recess cylindrical blend faces (scaled radii): {counts}",flush=True)


def _check_intakes(parts):
    for side,name in ((-1,"Left"),(1,"Right")):
        duct = parts[f"Intake{name}Duct"]
        ramp = parts[f"Intake{name}Ramp"]
        b = duct.bounding_box()
        _near(b.center().X,-668.0,"intake center after 200 mm forward relocation")
        _near(parts[f"AftService{name}"].bounding_box().center().X,-668.0,"relocated intake frame")
        _near(b.size.Y,42.0*SC,"intake shell depth")
        assert b.size.X > 140 and b.size.Z > 80*SC, "Intake opening scale drift"
        assert _overlap(duct,parts["Body"]) < VOLUME_TOL, "Body intrudes into intake liner"
        assert duct.distance_to(parts[f"AftService{name}"]) < TOL, "Intake lip/frame separation"
        for x in (-751,-585):
            for z in (-34*SC, 34*SC):
                fastener = parts[f"PanelFastener{name}_{x}_{z:g}"]
                assert fastener.distance_to(duct) > 4, "Intake lip masks panel fastener"
                assert fastener.distance_to(parts[f"AftService{name}"]) < TOL, "Fastener detached from relocated frame"
        assert ramp.distance_to(duct) < TOL, "Unsupported intake ramp"
        for i in (1,2):
            divider = parts[f"Intake{name}Splitter{i}"]
            assert divider.distance_to(ramp) < TOL, "Unsupported intake splitter"
        # Independent witness volumes inside all three mouths. These penetrate
        # beneath the hull surface: a painted slot or blocked pocket fails.
        for z in (-23.0*SC,0.0,23.0*SC):
            opening = bd.Box(16,25*SC,6*SC).translate((-693,side*138.5*SC,z))
            for label in ("Body",f"AftService{name}",f"Intake{name}Duct",
                          f"Intake{name}Ramp",f"Intake{name}Splitter1",f"Intake{name}Splitter2"):
                assert _overlap(opening,parts[label]) < VOLUME_TOL, f"Blocked intake {name}/{z}: {label}"
        former_socket = bd.Box(30,25*SC,20*SC).translate((-868,side*130*SC,0))
        _near(_overlap(former_socket,parts["Body"]),former_socket.volume,"former intake recess must be healed")
    for kind in ("Duct","Ramp","Splitter1","Splitter2"):
        _same_geometry(parts[f"IntakeRight{kind}"].mirror(bd.Plane.XZ),
                       parts[f"IntakeLeft{kind}"],f"Intake symmetry: {kind}")


def _poses(stowed, deployed):
    for label, part in stowed.items():
        print(f"Pose/identity: {label}", flush=True)
        group = semantic_group(label)
        if group not in ("wing_left", "wing_right"):
            _same_geometry(part, deployed[label], f"Fixed geometry changed: {label}")
            continue
        side = -1 if group == "wing_left" else 1
        axis = bd.Axis((WING_PIVOT_X, side*WING_PIVOT_Y, WING_PIVOT_Z), (0,0,1))
        expected = part.rotate(axis, -side*WING_ANGLE)
        _same_geometry(expected, deployed[label], f"Incorrect rigid pose: {label}")
    for parts in (stowed, deployed):
        _same_geometry(parts["WingRight"].mirror(bd.Plane.XZ), parts["WingLeft"], "wing symmetry")
        _same_geometry(parts["WingRightPivotCap"].mirror(bd.Plane.XZ),
                       parts["WingLeftPivotCap"], "wing cap symmetry")
        for i in range(2,5):
            _same_geometry(parts["TailControl1"].rotate(bd.Axis.X, 90*(i-1)),
                            parts[f"TailControl{i}"], "tail pattern")


def _check_folded_alignment(parts):
    """Independent cross-sections detect taper, yaw, roll and unfilled side space."""
    _near(WING_STOWED_ANGLE,0,"folded rotation")
    _near(WING_ANGLE,45,"swept deployment angle")
    for side,name in ((-1,"Left"),(1,"Right")):
        wing = parts[f"Wing{name}"]
        b = wing.bounding_box()
        _near(b.min.X,-580,"folded aft endpoint")
        _near(b.max.X,425,"folded forward endpoint")
        _near(b.size.Y,WING_CHORD,"full-chord folded wing")
        _near(b.size.Z,WING_THICKNESS,"unrolled folded section")
        _near(b.center().Y,side*WING_PIVOT_Y,"folded panel lateral center")
        edge_gap = BODY_WIDTH/2-max(abs(b.min.Y),abs(b.max.Y))
        assert 0.8 < edge_gap < 1.7, f"Excessive side gap or protrusion: {name}: {edge_gap}"
        for x in (-500,-250,0,300,390):
            probe = bd.Box(0.2,400,80*SC).translate((x,0,WING_PIVOT_Z))
            sections = wing.intersect(probe).solids()
            assert len(sections) == 1, f"Missing wing cross-section at {x}"
            section = sections[0].bounding_box()
            _near(section.size.Y,WING_CHORD,f"parallel chord at X={x}")
            _near(section.center().Y,side*WING_PIVOT_Y,f"no folded yaw at X={x}")
            _near(section.center().Z,WING_PIVOT_Z,f"no folded pitch at X={x}")
    center_gap = parts["WingRight"].bounding_box().min.Y-parts["WingLeft"].bounding_box().max.Y
    _near(center_gap,21*SC,"folded center clearance")


def _deployment_clearance(stowed):
    """Sampled animation regression, not a continuous swept-volume proof."""
    minimum = float("inf")
    pair_minimum = float("inf")
    samples = []
    # Full blade-to-hull, opposite blade, tail and fixed cover checks.
    # Pivot housings deliberately include the axle entering each wing root.
    obstacles = [p for label,p in stowed.items() if semantic_group(label)
                 not in ("wing_left", "wing_right") and not label.startswith("WingBay")]
    # First prove the tray spaces empty in the exported hull. Their half-space
    # bounds then certify clearance without expensive whole-hull distance calls.
    for side in (-1,1):
        # Inscribed box in the widened rounded tray; spans the curved cutter's
        # lateral dilation but stays inside its original axial/top tangency lines.
        tray_witness = bd.Box(1080,194*SC,66.5*SC).translate((-60,side*101*SC,-166.75*SC))
        assert _overlap(tray_witness,stowed["Body"]) < VOLUME_TOL, "Blocked wing recess"
    body_box = stowed["Body"].bounding_box()
    assert body_box.min.Z > -200*SC and max(abs(body_box.min.Y),abs(body_box.max.Y)) < 198*SC
    for angle in range(0,int(WING_ANGLE)+1,5):
        print(f"Deployment clearance: {angle} degrees", flush=True)
        blades = []
        for side,name in ((-1,"Left"),(1,"Right")):
            axis = bd.Axis((WING_PIVOT_X,side*WING_PIVOT_Y,WING_PIVOT_Z),(0,0,1))
            wing = stowed[f"Wing{name}"].rotate(axis, -side*angle)
            wb = wing.bounding_box()
            tray_gap = min(wb.min.X+600,480-wb.max.X,
                           wb.min.Y-4 if side > 0 else -4-wb.max.Y,
                           -133.5*SC-wb.max.Z)
            gap = min(tray_gap if obstacle.label == "Body" and tray_gap >= 4.0
                      else _clearance_lower_bound(wing,obstacle,4.0) for obstacle in obstacles)
            assert gap >= 4.0, f"Wing {name} collision/clearance at {angle}: {gap} mm"
            minimum = min(minimum,gap)
            blades.append(wing)
            # Outside a scaled root cylinder, wing and housing must stay disjoint.
            pivot_zone = bd.Cylinder(34*SC,70*SC).translate(
                (WING_PIVOT_X,side*WING_PIVOT_Y,WING_PIVOT_Z))
            housing = stowed[f"WingBay{name}"]-pivot_zone
            assert _overlap(wing,housing) < VOLUME_TOL, f"Wing/bay interference at {angle}"
            other = "Right" if name == "Left" else "Left"
            assert _overlap(wing,stowed[f"WingBay{other}"]) < VOLUME_TOL, f"Opposite wing-bay interference at {angle}"
        # A 45-degree in-plane sweep necessarily brings the two apex corners
        # over the fuselage; they stay on their own side (no crossing) with a
        # small gap instead of the old perpendicular-pose 16 mm rule.
        pair_gap = _clearance_lower_bound(blades[0],blades[1],5.01)
        assert pair_gap > 5, f"Wing/wing proximity at {angle}: {pair_gap} mm"
        pair_minimum = min(pair_minimum,pair_gap)
        samples.append(angle)
    return {"angles_degrees": samples, "minimum_certified_fixed_geometry_clearance_mm": minimum,
            "minimum_certified_wing_pair_clearance_mm": pair_minimum,
            "method":"BREP-verified tray half-spaces and conservative AABBs; exact distance fallback"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--diagnose", action="store_true")
    args = parser.parse_args()
    models = {pose: read_step(ROOT/f"AGM-110_Ballista_{pose}.step") for pose in ("Stowed","Deployed")}
    parts = {pose:_parts(m) for pose,m in models.items()}
    if args.diagnose:
        for pose,model in models.items():
            print(pose, json.dumps(_bounds(model)))
        for label,p in parts["Stowed"].items():
            print(label, json.dumps(_bounds(p)), "solids", len(p.solids()))
        for a,b in [("SeekerWindow","SeekerBezel"),("WingBayLeft","Body"),
                    ("WingLeftPivotCap","WingLeft"),("TailRoot1","Body")]:
            print(a,b,"overlap",_overlap(parts["Stowed"][a],parts["Stowed"][b]),
                  "gap",parts["Stowed"][a].distance_to(parts["Stowed"][b]))
        return
    for pose,model in models.items():
        print(f"Checking {pose}: solids, dimensions and interfaces", flush=True)
        _common(model,parts[pose])
    _poses(parts["Stowed"],parts["Deployed"])
    _check_folded_alignment(parts["Stowed"])
    clearance = _deployment_clearance(parts["Stowed"])
    sb, db = models["Stowed"].bounding_box(), models["Deployed"].bounding_box()
    assert sb.size.Y < AGM68_ENVELOPE and sb.size.Z < AGM68_ENVELOPE, "Stowed carriage envelope"
    # Deployed span: pivot lateral offset plus the rotated blade. The blade's
    # axial length is unscaled, so the sin term does not carry the scale.
    expected_span = 2*(WING_PIVOT_Y + WING_LENGTH*sin(radians(WING_ANGLE))
                       + (WING_CHORD-14*SC)/2*cos(radians(WING_ANGLE)))
    _near(db.size.Y, expected_span, "scaled 40-degree deployed span")
    assert db.size.Y > sb.size.Y
    report = {"ok":True, "part_count_per_pose":len(COMMON_LABELS),
              "body_mm":[LENGTH,BODY_WIDTH,BODY_HEIGHT],
              "stowed":_bounds(models["Stowed"]), "deployed":_bounds(models["Deployed"]),
              "deployment":clearance, "groups":sorted({semantic_group(k) for k in COMMON_LABELS}),
              "wing_recess":{"translation_z_mm":27*SC,"pivot_z_mm":WING_PIVOT_Z},
              "wing_planform":{"chord_mm":WING_CHORD,"stowed_angle_degrees":0,"deployed_angle_degrees":WING_ANGLE,
                               "folded_center_gap_mm":21*SC,"folded_outer_gap_mm":BODY_WIDTH/2-146.5*SC},
              "recess_smoothing":{"lip_radius_mm":2*SC,"bay_radius_mm":3*SC,"tray_radius_mm":6*SC},
              "intakes":{"center_x_mm":-668,"forward_translation_mm":200,"shell_depth_mm":42*SC,"clear_mouths_per_side":3,
                         "opening_witness_depth_mm":25*SC,"body_intrusion":False},
              "lateral_scale":SC,
              "scope":"CAD exterior/poses; aircraft rack fit and runtime not verified"}
    (ROOT/"Ballista_checks.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
