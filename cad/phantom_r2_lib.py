"""RDM-9 Phantom round-2 candidates: shared wedge-nose airframe and appendage kits.

Coordinate convention: the missile axis is X with the nose forward, the runtime
pivot sits at X=0, +Z is dorsal and +Y is starboard. The body is a smooth
elliptical loft whose nose rises into an upward wedge that leads the eye into
the RF emitter housings (2026-09-20 user art direction).

The 2026-09-20 adversarial-review repairs are structural, not cosmetic:

- The loft is ruled with densified stations: the round-1 non-ruled spline
  crowned the 200 x 154 mm spec midbody to 209.87 mm, and a measured probe
  showed the plateau pin destabilizing the interpolator outright (779 mm
  bulge). Ruled lofting between elliptical stations is deterministic and
  lands exactly on the spec section; the dense nose stations keep the wedge
  transitions visually smooth.
- The nozzle lip outer radius (54 mm) sits inside the 142 x 112 mm tail face
  semi-minor (56 mm), so the ring is recessed flush instead of standing ~4 mm
  proud of the smooth body.
- Appendage roots bury into the body wall (tailplane roots moved from y=96,
  which left a visible root gap aft, to y=72 inside the aft body width).
- Every candidate must clear a dorsal pylon-pad mockup zone (a 700 x 80 mm
  pad face 1 mm above the body crown), so no fixed dorsal feature may rise
  into the carriage interface.

R3 Dart of record (2026-09-20 user decisions): the Dart silhouette is
selected, the side RF/lens emitter panels are removed, and dorsal pop-out
wings are added, rendered deployed like the real ADM-160 spring-out wings.
The wing roots stay buried in the dorsal crown inside the 250 mm carriage
envelope; the deployed span intentionally exceeds it, so the wing pair is
exempt from the radial envelope gates and the rack visual will show
deployed wings.

R4 revision (2026-09-20, after user review of R3): the nose converges to a
full sharp point riding at +30 mm (upward wedge preserved), and the wings
become a real swept planform - 420 mm root chord, 110 mm tip chord, 30
degree leading-edge sweep, raked tips, 2.5 degree dihedral, +-700 mm span.
The R4 body is one smooth non-ruled loft (no station ring bands) whose
stability was found empirically: the apex vertex anchors the spline, the
tail stations must be monotone without duplicates, and equal-value plateau
stations must sit every 200 mm or the cubic crowns mid-span. Measured
clamp: 200.64 x 154.73 mm against the 201.5 x 155.5 gate.

R5 revision (2026-09-20, folding concept): the deployed wing panel thins
from 4.0 to 2.5 mm so it can park inside the fuselage, and a retracted
configuration is added. With a 1.4 m span against the locked 250 mm
carriage envelope no external hinge fold fits (span needs the 2.8 m axis,
but then the 420 mm chord lies across a 200 mm body), so the retraction is
internal - Tomahawk-style: the panels park in a dorsal bay and deploy
through a 6 mm spine slot (x -950..-250, floor z=71). The retracted model
shows the dark panel stack through the slot plus an aft hinge fairing
(x -1000..-950) that deliberately stays clear of the pylon-pad mockup
zone, and it keeps the full 125/124 mm envelope gates - nothing is
exempt, because fitting the carriage envelope is the retracted state's
entire purpose.
"""

from cadgen import build123d as bd
from cadgen import report, srgb


LENGTH = 2800.0
HALF_LENGTH = LENGTH * 0.5
ENVELOPE_RADIUS = 125.0
DESIGN_RADIUS = 124.0

BODY_WIDTH = 200.0
BODY_HEIGHT = 154.0
TAIL_WIDTH = 142.0
TAIL_HEIGHT = 112.0
NOSE_CAP_WIDTH = 70.0
NOSE_CAP_HEIGHT = 12.0
NOSE_CAP_RISE = 30.0
BORE_RADIUS = 32.0
LIP_RADIUS = 48.0

# (x, width, height, dorsal offset). The loft is ruled: stations are dense
# near the tail step and the nose wedge so the linear tapers stay smooth,
# and the 200 x 154 mm midbody is held exactly between -900 and +600. The
# nose wedge is deliberately strong: the ventral line climbs from -77 at
# x=600 to +24 at the tip while the dorsal line eases from +77 to +36, so
# the side view reads as an upward wedge whose blade rides well above the
# centerline (2026-09-20 user art direction; the first two passes, cap rise
# +11 then +15, still read pencil at render scale).
BODY_SECTIONS = (
    (-1400.0, TAIL_WIDTH, TAIL_HEIGHT, 0.0),
    (-1375.0, TAIL_WIDTH, TAIL_HEIGHT, 0.0),
    (-1300.0, 160.0, 128.0, 0.0),
    (-1250.0, 176.0, 142.0, 0.0),
    (-1150.0, 191.0, 149.0, 0.0),
    (-1050.0, BODY_WIDTH, BODY_HEIGHT, 0.0),
    (-900.0, BODY_WIDTH, BODY_HEIGHT, 0.0),
    (600.0, BODY_WIDTH, BODY_HEIGHT, 0.0),
    (700.0, 198.0, 150.0, 1.0),
    (900.0, 188.0, 134.0, 5.0),
    (1080.0, 174.0, 112.0, 10.0),
    (1150.0, 162.0, 96.0, 13.0),
    (1240.0, 142.0, 68.0, 17.0),
    (1300.0, 120.0, 46.0, 21.0),
    (1340.0, 102.0, 34.0, 24.0),
    (1360.0, 92.0, 28.0, 26.0),
    (1380.0, 80.0, 20.0, 28.0),
    (1390.0, 74.0, 16.0, 29.0),
    (1400.0, NOSE_CAP_WIDTH, NOSE_CAP_HEIGHT, NOSE_CAP_RISE),
)

# R4 dart4 body: a smooth non-ruled loft (no station ring bands) fused with
# a ruled single-segment tip cone into a sharp apex vertex at (1400, 0,
# +30). Station rules found empirically (see probes): monotone tail without
# duplicate stations, equal-value plateau stations every 200 mm (larger
# spans crown the cubic mid-span), and a ruled - not spline - tip because a
# pure vertex-ended spline fails cadgen's strict topology check even after
# fix(). Measured clamp 200.64 x 154.73 mm.
R4_BODY_MAIN_SECTIONS = (
    (-1400.0, TAIL_WIDTH, TAIL_HEIGHT, 0.0),
    (-1320.0, 152.0, 120.0, 0.0),
    (-1240.0, 168.0, 138.0, 0.0),
    (-1160.0, 184.0, 148.0, 0.0),
    (-1080.0, 196.0, 153.0, 0.0),
    (-1000.0, BODY_WIDTH, BODY_HEIGHT, 0.0),
    (-800.0, BODY_WIDTH, BODY_HEIGHT, 0.0),
    (-600.0, BODY_WIDTH, BODY_HEIGHT, 0.0),
    (-400.0, BODY_WIDTH, BODY_HEIGHT, 0.0),
    (-200.0, BODY_WIDTH, BODY_HEIGHT, 0.0),
    (0.0, BODY_WIDTH, BODY_HEIGHT, 0.0),
    (200.0, BODY_WIDTH, BODY_HEIGHT, 0.0),
    (400.0, BODY_WIDTH, BODY_HEIGHT, 0.0),
    (600.0, BODY_WIDTH, BODY_HEIGHT, 0.0),
    (700.0, 198.0, 150.0, 1.0),
    (900.0, 188.0, 134.0, 5.0),
    (1080.0, 174.0, 112.0, 10.0),
    (1150.0, 162.0, 96.0, 13.0),
    (1240.0, 142.0, 68.0, 17.0),
    (1300.0, 120.0, 46.0, 21.0),
    (1340.0, 86.0, 30.0, 25.0),
    (1360.0, 60.0, 18.0, 27.0),
    (1380.0, 34.0, 8.0, 28.8),
)
R4_TIP_SECTIONS = ((1380.0, 34.0, 8.0, 28.8),)
R4_APEX = (1400.0, 0.0, 30.0)

BODY_SPECS = {
    "sled": (BODY_SECTIONS, True, None, None),
    "rails": (BODY_SECTIONS, True, None, None),
    "dart": (BODY_SECTIONS, True, None, None),
    "dart3": (BODY_SECTIONS, True, None, None),
    "dart4": (R4_BODY_MAIN_SECTIONS, False, R4_APEX, R4_TIP_SECTIONS),
    "dart5": (R4_BODY_MAIN_SECTIONS, False, R4_APEX, R4_TIP_SECTIONS),
    # Retracted configuration shares the dart4/dart5 body; the dorsal
    # retraction slot is cut in make_r2.
    "dart5r": (R4_BODY_MAIN_SECTIONS, False, R4_APEX, R4_TIP_SECTIONS),
}

# Dorsal retraction bay (Tomahawk-style internal carriage): the 1.4 m span
# cannot externally fold into the 250 mm envelope, so the thin wing panels
# park inside the fuselage and deploy through a spine slot. The slot runs
# aft from the wing box; the hinge fairing caps its aft end so the retracted
# parts stay clear of the pylon-pad mockup zone (x -350..+350).
RETRACTION_SLOT = {
    "x_aft": -950.0,
    "x_fore": -250.0,
    "y_half": 3.0,
    "z_floor": 71.0,
    "z_top": 80.0,
}
STOWED_STACK = {
    "x_aft": -944.0,
    "x_fore": -256.0,
    "y_half": 2.5,
    "z_floor": 71.0,
    "z_top": 73.4,
}
HINGE_FAIRING = {
    "x_aft": -1000.0,
    "x_fore": -950.0,
    "y_half": 10.0,
    "z_bottom": 73.0,
    "z_top": 79.0,
}

BODY_COLOR = srgb("#8F989B")
RF_PANEL_COLOR = srgb("#C1B7A9")
EMITTER_COLOR = srgb("#D8CFC0")
FIN_COLOR = srgb("#707A7D")
NOZZLE_COLOR = srgb("#40474A")
RECESS_COLOR = srgb("#15191A")
PAD_COLOR = srgb("#3A3F42")

PYLON_PAD = {
    "x_aft": -350.0,
    "x_fore": 350.0,
    "y_half": 40.0,
    "z_bottom": 78.0,
    "z_top": 132.0,
}


def section_wire(x, width, height, z_center=0.0):
    """Smooth elliptical fuselage section normal to X."""
    return (
        bd.Ellipse(height * 0.5, width * 0.5)
        .rotate(bd.Axis.Y, 90.0)
        .translate((x, 0.0, z_center))
    )


def cylinder_x(x_min, x_max, radius):
    return (
        bd.Cylinder(radius, x_max - x_min, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
        .rotate(bd.Axis.Y, 90.0)
        .translate((x_min, 0.0, 0.0), transform=True)
    )


def annular_cylinder_x(x_min, x_max, outer_radius, inner_radius):
    return cylinder_x(x_min, x_max, outer_radius) - cylinder_x(
        x_min - 0.5, x_max + 0.5, inner_radius
    )


def profile_prism_xz(points, width, y_center=0.0):
    wire = bd.Wire.make_polygon(
        [(x, y_center - width * 0.5, z) for x, z in points],
        close=True,
    )
    return bd.Solid.extrude(bd.Face(wire), (0.0, width, 0.0))


def plate_from_xy(points, z_min, thickness):
    wire = bd.Wire.make_polygon([(x, y, z_min) for x, y in points], close=True)
    return bd.Solid.extrude(bd.Face(wire), (0.0, 0.0, thickness))


def chamfered_side_panel(side, x_aft, x_fore, y_inner, y_outer, z_half, z_chamfer, x_chamfer):
    """Flush slab on one side of the body, chamfered fore/aft and top/bottom."""
    points = [
        (x_aft, -(z_half - z_chamfer)),
        (x_aft + x_chamfer, -z_half),
        (x_fore - x_chamfer, -z_half),
        (x_fore, -(z_half - z_chamfer)),
        (x_fore, z_half - z_chamfer),
        (x_fore - x_chamfer, z_half),
        (x_aft + x_chamfer, z_half),
        (x_aft, z_half - z_chamfer),
    ]
    thickness = abs(y_outer - y_inner)
    wire = bd.Wire.make_polygon([(x, side * y_inner, z) for x, z in points], close=True)
    return bd.Solid.extrude(bd.Face(wire), (0.0, side * thickness, 0.0))


def horizontal_fin(side, root_aft, root_front, tip_aft, tip_front, root_y, tip_y, z_center, thickness):
    points = [
        (root_aft, side * root_y),
        (root_front, side * root_y),
        (tip_front, side * tip_y),
        (tip_aft, side * tip_y),
    ]
    if side < 0.0:
        points.reverse()
    return plate_from_xy(points, z_center - thickness * 0.5, thickness)


def vertical_fin(points, width=6.0):
    return profile_prism_xz(points, width)


# Pop-out wing planforms: dorsal-mounted, rendered deployed like the real
# ADM-160 spring-out wings. Points are (x, y_outboard) for the starboard
# half, extruded to a plate and rotated for dihedral about the dorsal
# hinge. The root edge is buried in the dorsal crown (inside the 250 mm
# carriage envelope); the deployed span intentionally exceeds it.
# r3: the first pop-out attempt - near-square plan the user rejected.
# r4: real swept planform - 420 mm root chord, 110 mm tip chord, 30 degree
# LE sweep, raked tip corners, 2.5 degree dihedral, +-700 mm span.
WING_SPECS = {
    "r3": {
        "points": ((-350.0, 18.0), (250.0, 18.0), (420.0, 550.0), (-180.0, 550.0)),
        "z_min": 68.0,
        "thickness": 5.0,
        "dihedral": 5.0,
    },
    "r4": {
        "points": (
            (210.0, 14.0),
            (-194.0, 672.0),
            (-224.0, 700.0),
            (-308.0, 700.0),
            (-210.0, 14.0),
        ),
        "z_min": 66.0,
        "thickness": 4.0,
        "dihedral": 2.5,
    },
    # r5: same swept planform thinned for the folding/retraction concept -
    # a 2.5 mm panel slides into the dorsal bay where the 4 mm plate would
    # double the stowed stack height.
    "r5": {
        "points": (
            (210.0, 14.0),
            (-194.0, 672.0),
            (-224.0, 700.0),
            (-308.0, 700.0),
            (-210.0, 14.0),
        ),
        "z_min": 66.0,
        "thickness": 2.5,
        "dihedral": 2.5,
    },
}
WING_LIMITS = {"r3": {"y": 600.0, "z": 200.0}, "r4": {"y": 760.0, "z": 160.0}}


def popout_wing(side, spec_key):
    """One deployed wing half, hinged at the dorsal centerline with dihedral."""
    spec = WING_SPECS[spec_key]
    points = [(x, side * y) for x, y in spec["points"]]
    if side < 0.0:
        points.reverse()
    wing = plate_from_xy(points, spec["z_min"], spec["thickness"])
    return wing.rotate(
        bd.Axis((0.0, 0.0, spec["z_min"]), (1.0, 0.0, 0.0)),
        side * spec["dihedral"],
    )


def style(part, label, color, roughness=0.64, metalness=0.18):
    part.label = label
    part.color = color
    part.cad_material = {"roughness": roughness, "metalness": metalness}
    return part


def make_body(sections=BODY_SECTIONS, ruled=True, apex=None, tip_sections=None):
    profiles = [
        section_wire(x, width, height, z_center) for x, width, height, z_center in sections
    ]
    if apex is None:
        body = bd.loft(profiles, ruled=ruled)
    elif tip_sections is None:
        body = bd.loft(profiles + [bd.Vertex(*apex)], ruled=ruled)
    else:
        tip_profiles = [
            section_wire(x, width, height, z_center) for x, width, height, z_center in tip_sections
        ]
        body = bd.loft(profiles, ruled=ruled).fuse(
            bd.loft(tip_profiles + [bd.Vertex(*apex)], ruled=True)
        )
    cavity = cylinder_x(-HALF_LENGTH - 1.0, -1335.0, BORE_RADIUS)
    return body - cavity


def make_nozzle_parts():
    lip = annular_cylinder_x(-1400.0, -1382.0, LIP_RADIUS, BORE_RADIUS)
    recess = cylinder_x(-1340.0, -1335.0, BORE_RADIUS)
    return lip, recess


def _appendages(candidate):
    if candidate == "sled":
        parts = []
        for side, name in ((-1.0, "port"), (1.0, "starboard")):
            panel = chamfered_side_panel(
                side, -650.0, 690.0, 78.0, 118.0, 22.0, 8.0, 30.0
            )
            parts.append((panel, f"wing_panel_{name}", RF_PANEL_COLOR, 0.5, 0.12))
            emitter = chamfered_side_panel(
                side, 70.0, 570.0, 114.0, 123.0, 11.0, 3.0, 20.0
            )
            parts.append((emitter, f"rf_emitter_{name}", EMITTER_COLOR, 0.5, 0.12))
            tailplane = horizontal_fin(
                side, -1280.0, -760.0, -1160.0, -900.0, 72.0, 123.5, 0.0, 6.0
            )
            parts.append((tailplane, f"tailplane_{name}", FIN_COLOR, 0.64, 0.18))
        parts.append((
            vertical_fin([(-700.0, 40.0), (-420.0, 58.0), (-520.0, 96.0), (-680.0, 96.0)]),
            "dorsal_spine",
            FIN_COLOR,
            0.64,
            0.18,
        ))
        parts.append((
            vertical_fin([(-640.0, -40.0), (-330.0, -56.0), (-420.0, -123.5), (-590.0, -123.5)]),
            "ventral_keel",
            FIN_COLOR,
            0.64,
            0.18,
        ))
        return parts
    if candidate == "rails":
        parts = []
        for side, name in ((-1.0, "port"), (1.0, "starboard")):
            midwing = horizontal_fin(
                side, -700.0, -100.0, -560.0, -260.0, 70.0, 123.5, 0.0, 12.0
            )
            parts.append((midwing, f"midwing_{name}", FIN_COLOR, 0.64, 0.18))
            panel = chamfered_side_panel(
                side, 60.0, 580.0, 74.0, 104.0, 52.0, 10.0, 40.0
            )
            parts.append((panel, f"rf_panel_{name}", RF_PANEL_COLOR, 0.5, 0.12))
            tailplane = horizontal_fin(
                side, -1280.0, -760.0, -1160.0, -900.0, 72.0, 123.5, 0.0, 6.0
            )
            parts.append((tailplane, f"tailplane_{name}", FIN_COLOR, 0.64, 0.18))
        parts.append((
            vertical_fin([(-1280.0, 52.0), (-760.0, 70.0), (-890.0, 123.5), (-1170.0, 123.5)]),
            "dorsal_fin",
            FIN_COLOR,
            0.64,
            0.18,
        ))
        parts.append((
            vertical_fin([(-1260.0, -40.0), (-860.0, -60.0), (-980.0, -123.5), (-1160.0, -123.5)]),
            "ventral_keel",
            FIN_COLOR,
            0.64,
            0.18,
        ))
        return parts
    if candidate == "dart":
        parts = []
        for side, name in ((-1.0, "port"), (1.0, "starboard")):
            tail_fin = horizontal_fin(
                side, -1340.0, -1130.0, -1250.0, -1190.0, 56.0, 123.5, 0.0, 6.0
            )
            parts.append((tail_fin, f"tail_fin_{name}", FIN_COLOR, 0.64, 0.18))
            panel = chamfered_side_panel(
                side, 60.0, 580.0, 74.0, 104.0, 52.0, 10.0, 40.0
            )
            parts.append((panel, f"rf_panel_{name}", RF_PANEL_COLOR, 0.5, 0.12))
        parts.append((
            vertical_fin([(-1340.0, 40.0), (-1140.0, 54.0), (-1210.0, 123.5), (-1310.0, 123.5)]),
            "dorsal_fin",
            FIN_COLOR,
            0.64,
            0.18,
        ))
        parts.append((
            vertical_fin([(-1330.0, -40.0), (-1150.0, -52.0), (-1220.0, -123.5), (-1300.0, -123.5)]),
            "ventral_fin",
            FIN_COLOR,
            0.64,
            0.18,
        ))
        return parts
    if candidate == "dart3":
        parts = []
        for side, name in ((-1.0, "port"), (1.0, "starboard")):
            tail_fin = horizontal_fin(
                side, -1340.0, -1130.0, -1250.0, -1190.0, 56.0, 123.5, 0.0, 6.0
            )
            parts.append((tail_fin, f"tail_fin_{name}", FIN_COLOR, 0.64, 0.18))
            parts.append((popout_wing(side, "r3"), f"wing_{name}", FIN_COLOR, 0.55, 0.24))
        parts.append((
            vertical_fin([(-1340.0, 40.0), (-1140.0, 54.0), (-1210.0, 123.5), (-1310.0, 123.5)]),
            "dorsal_fin",
            FIN_COLOR,
            0.64,
            0.18,
        ))
        parts.append((
            vertical_fin([(-1330.0, -40.0), (-1150.0, -52.0), (-1220.0, -123.5), (-1300.0, -123.5)]),
            "ventral_fin",
            FIN_COLOR,
            0.64,
            0.18,
        ))
        return parts
    if candidate == "dart5":
        parts = []
        for side, name in ((-1.0, "port"), (1.0, "starboard")):
            tail_fin = horizontal_fin(
                side, -1340.0, -1130.0, -1250.0, -1190.0, 56.0, 123.5, 0.0, 6.0
            )
            parts.append((tail_fin, f"tail_fin_{name}", FIN_COLOR, 0.64, 0.18))
            parts.append((popout_wing(side, "r5"), f"wing_{name}", FIN_COLOR, 0.55, 0.24))
        parts.append((
            vertical_fin([(-1340.0, 40.0), (-1140.0, 54.0), (-1210.0, 123.5), (-1310.0, 123.5)]),
            "dorsal_fin",
            FIN_COLOR,
            0.64,
            0.18,
        ))
        parts.append((
            vertical_fin([(-1330.0, -40.0), (-1150.0, -52.0), (-1220.0, -123.5), (-1300.0, -123.5)]),
            "ventral_fin",
            FIN_COLOR,
            0.64,
            0.18,
        ))
        return parts
    if candidate == "dart5r":
        # Retracted configuration: no deployed wings. The thin panels park
        # inside the dorsal bay; the only external evidence is the dark
        # panel stack visible through the spine slot plus the hinge
        # fairing that caps its aft end. Tail surfaces are unchanged.
        parts = []
        for side, name in ((-1.0, "port"), (1.0, "starboard")):
            tail_fin = horizontal_fin(
                side, -1340.0, -1130.0, -1250.0, -1190.0, 56.0, 123.5, 0.0, 6.0
            )
            parts.append((tail_fin, f"tail_fin_{name}", FIN_COLOR, 0.64, 0.18))
        parts.append((
            vertical_fin([(-1340.0, 40.0), (-1140.0, 54.0), (-1210.0, 123.5), (-1310.0, 123.5)]),
            "dorsal_fin",
            FIN_COLOR,
            0.64,
            0.18,
        ))
        parts.append((
            vertical_fin([(-1330.0, -40.0), (-1150.0, -52.0), (-1220.0, -123.5), (-1300.0, -123.5)]),
            "ventral_fin",
            FIN_COLOR,
            0.64,
            0.18,
        ))
        parts.append(
            (
                bd.Box(
                    STOWED_STACK["x_fore"] - STOWED_STACK["x_aft"],
                    STOWED_STACK["y_half"] * 2.0,
                    STOWED_STACK["z_top"] - STOWED_STACK["z_floor"],
                    align=(bd.Align.MIN, bd.Align.CENTER, bd.Align.MIN),
                ).translate((STOWED_STACK["x_aft"], 0.0, STOWED_STACK["z_floor"])),
                "stowed_wing_stack",
                RECESS_COLOR,
                0.88,
                0.04,
            )
        )
        parts.append(
            (
                bd.Box(
                    HINGE_FAIRING["x_fore"] - HINGE_FAIRING["x_aft"],
                    HINGE_FAIRING["y_half"] * 2.0,
                    HINGE_FAIRING["z_top"] - HINGE_FAIRING["z_bottom"],
                    align=(bd.Align.MIN, bd.Align.CENTER, bd.Align.MIN),
                ).translate((HINGE_FAIRING["x_aft"], 0.0, HINGE_FAIRING["z_bottom"])),
                "hinge_fairing",
                FIN_COLOR,
                0.55,
                0.24,
            )
        )
        return parts
    raise ValueError(f"unknown candidate: {candidate}")


def _retraction_slot_box():
    return bd.Box(
        RETRACTION_SLOT["x_fore"] - RETRACTION_SLOT["x_aft"],
        RETRACTION_SLOT["y_half"] * 2.0,
        RETRACTION_SLOT["z_top"] - RETRACTION_SLOT["z_floor"],
        align=(bd.Align.MIN, bd.Align.CENTER, bd.Align.MIN),
    ).translate((RETRACTION_SLOT["x_aft"], 0.0, RETRACTION_SLOT["z_floor"]))


def make_r2(candidate):
    """Assemble one Phantom candidate. candidate: sled | rails | dart | dart3 | dart4 | dart5 | dart5r."""
    report(f"RDM-9 Phantom candidate: {candidate}")
    sections, ruled, apex, tip_sections = BODY_SPECS[candidate]
    body = make_body(sections, ruled, apex, tip_sections)
    if candidate == "dart5r":
        body = body - _retraction_slot_box()
    body = style(body, "smooth_body", BODY_COLOR)
    lip, recess = make_nozzle_parts()
    parts = [
        body,
        style(lip, "nozzle_lip", NOZZLE_COLOR, 0.5, 0.34),
        style(recess, "nozzle_recess", RECESS_COLOR, 0.88, 0.04),
    ]
    for shape, label, color, roughness, metalness in _appendages(candidate):
        parts.append(style(shape, label, color, roughness, metalness))
    label = {
        "sled": "RDM-9_Phantom_R2_Sled",
        "rails": "RDM-9_Phantom_R2_Rails",
        "dart": "RDM-9_Phantom_R2_Dart",
        "dart3": "RDM-9_Phantom_R3_Dart",
        "dart4": "RDM-9_Phantom_R4_Dart",
        "dart5": "RDM-9_Phantom_R5_Dart",
        "dart5r": "RDM-9_Phantom_R5_Dart_Retracted",
    }[candidate]
    return bd.Compound(children=parts, label=label)


def make_r2_context(candidate):
    """Candidate plus a dorsal pylon-pad mockup for carriage-context review."""
    compound = make_r2(candidate)
    pad = bd.Box(
        PYLON_PAD["x_fore"] - PYLON_PAD["x_aft"],
        PYLON_PAD["y_half"] * 2.0,
        PYLON_PAD["z_top"] - PYLON_PAD["z_bottom"],
        align=(bd.Align.MIN, bd.Align.CENTER, bd.Align.MIN),
    ).translate((PYLON_PAD["x_aft"], 0.0, PYLON_PAD["z_bottom"]))
    parts = list(compound.children) + [
        style(pad, "pylon_pad", PAD_COLOR, 0.55, 0.30),
    ]
    label = {
        "sled": "RDM-9_Phantom_R2_Context_Sled",
        "rails": "RDM-9_Phantom_R2_Context_Rails",
        "dart": "RDM-9_Phantom_R2_Context_Dart",
        "dart3": "RDM-9_Phantom_R3_Context_Dart",
        "dart4": "RDM-9_Phantom_R4_Context_Dart",
        "dart5": "RDM-9_Phantom_R5_Context_Dart",
        "dart5r": "RDM-9_Phantom_R5_Context_Dart_Retracted",
    }[candidate]
    return bd.Compound(children=parts, label=label)
