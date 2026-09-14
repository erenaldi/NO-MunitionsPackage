"""AGM-110 Ballista RC1 exterior master; mm, +X forward, +Z dorsal.

Reference-driven fictional game art, not a functional weapon design. Two
identical wing solids sweep about ventral +Z datums; only their placements
change between export configurations.

Width basis (user direction): the central body cross-section lands between the
AGM-48 and AGM-68 central diameters, both slice-measured from runtime mesh
dumps. All lateral (Y) and vertical (Z) constants are the authored baseline
times LATERAL_SCALE; axial (X) values are untouched so the length stays at
105% of the AGM-68.
"""

from cadgen import build123d as bd
from cadgen import srgb


AGM68_LENGTH = 2470.88
AGM68_ENVELOPE = 493.303031  # complete vanilla mesh envelope, NOT body diameter
LENGTH = AGM68_LENGTH * 1.05
HALF_LENGTH = LENGTH / 2

# Authored pre-rescale body cross-section, kept only as the scale reference.
LEGACY_BODY_WIDTH = AGM68_ENVELOPE * 0.60
AGM48_CENTRAL_DIAMETER = 180.0  # AGM1.geometry.obj, slice-median
AGM68_CENTRAL_DIAMETER = 300.0  # AGM_heavy.geometry.obj, fin-free slices
TARGET_CENTRAL_WIDTH = (AGM48_CENTRAL_DIAMETER + AGM68_CENTRAL_DIAMETER) / 2
LATERAL_SCALE = TARGET_CENTRAL_WIDTH / LEGACY_BODY_WIDTH
K = LATERAL_SCALE

BODY_WIDTH = TARGET_CENTRAL_WIDTH
BODY_HEIGHT = BODY_WIDTH
HALF_WIDTH = BODY_WIDTH / 2
HALF_HEIGHT = BODY_HEIGHT / 2
CORNER_CHAMFER = 33.0 * K

WING_LENGTH = 975.0  # pivot-to-tip; full stowed axial envelope stays -580..425
WING_CHORD = 136.0 * K
WING_THICKNESS = 15.0 * K
WING_STOWED_ANGLE = 0.0
WING_ANGLE = 45.0  # sweep out-and-aft at 45 degrees from the body axis
WING_PIVOT_X = 395.0
WING_PIVOT_Y = 78.5 * K
WING_RECESS_SHIFT = 27.0 * K
WING_PIVOT_Z = -174.0 * K + WING_RECESS_SHIFT
WING_TRAY_AFT_X = -600.0
WING_TRAY_FORWARD_X = 480.0
WING_TRAY_INNER_Y = 10.0 * K
WING_TRAY_OUTER_Y = 198.0 * K
WING_TRAY_CEILING_Z = -133.5 * K
WING_TRAY_BLEND_RADIUS = 6.0 * K
WING_BAY_BLEND_RADIUS = 3.0 * K
WING_RECESS_LIP_RADIUS = 2.0 * K
TAIL_RADIUS = 279.0 * K
TAIL_ANGLES = (45.0, 135.0, 225.0, 315.0)
SEEKER_WINDOW_WIDTH = 125.0 * K
SEEKER_WINDOW_HEIGHT = 94.0 * K
SEEKER_GLASS_FRONT = HALF_LENGTH - 12.0
NOZZLE_EXIT_X = -HALF_LENGTH
NOZZLE_OUTER_RADIUS = 85.0 * K
NOZZLE_INNER_RADIUS = 66.0 * K
NOZZLE_DEPTH = 132.0

# Low-profile intake artwork: visible cavity depth, not a flow simulation.
INTAKE_X = -668.0  # complete aft-service assembly moved 200 mm toward +X/nose
INTAKE_BACK_Y = 110.0 * K
INTAKE_LIP_Y = 152.0 * K
INTAKE_SPLITTER_Z = (-12.0 * K, 12.0 * K)

BODY_COLOR = srgb("#626C70")
PANEL_COLOR = srgb("#4E595F")
WING_COLOR = srgb("#747E83")
HARDWARE_COLOR = srgb("#303B42")
EDGE_COLOR = srgb("#8D9699")
WINDOW_COLOR = srgb("#2B4858")
NOZZLE_COLOR = srgb("#66554C")
RECESS_COLOR = srgb("#192329")
ACCENT_COLOR = srgb("#BD8839")


def _style(shape, label, color, roughness=0.58, metalness=0.22):
    shape.label = label
    shape.color = color
    shape.cad_material = {"roughness": roughness, "metalness": metalness}
    return shape


def _face(points):
    return bd.Face(bd.Wire.make_polygon(points, close=True))


def _chamfered_section(x, width, height, chamfer):
    w, h = width / 2, height / 2
    c = min(chamfer, w * 0.8, h * 0.8)
    return _face([(x, -w+c, -h), (x, w-c, -h), (x, w, -h+c),
                  (x, w, h-c), (x, w-c, h), (x, -w+c, h),
                  (x, -w, h-c), (x, -w, -h+c)])


def _body_loft(stations):
    return bd.loft([_chamfered_section(*s) for s in stations], ruled=True)


def _tube_x(x, length, radius):
    return bd.Cylinder(radius, length).rotate(bd.Axis.Y, 90).translate((x+length/2, 0, 0))


def _round_loft(stations):
    return bd.loft([bd.Face(bd.Wire.make_circle(r, bd.Plane(origin=(x, 0, 0),
                       x_dir=(0, 1, 0), z_dir=(1, 0, 0)))) for x, r in stations], ruled=True)


def _panel_xy(x, y, z, length, width, depth, bevel=8):
    """Octagonal plan with constructed edge bevel; no fragile edge selectors."""
    def section(height, inset):
        a, b = length/2-inset, width/2-inset
        c = min(bevel, b*0.6)
        return _face([(x-a+c,y-b,height), (x+a-c,y-b,height),
                      (x+a,y-b+c,height), (x+a,y+b-c,height),
                      (x+a-c,y+b,height), (x-a+c,y+b,height),
                      (x-a,y+b-c,height), (x-a,y-b+c,height)])
    return bd.loft([section(z, 0), section(z+depth-1, 0),
                    section(z+depth, 1)], ruled=True)


def _side_panel(x, side, z, length, height, depth=3.2):
    # XY panel mapped onto the +Y side, then mirrored for the left.
    panel = _panel_xy(x, -z, HALF_WIDTH-0.7, length, height, depth)
    panel = panel.rotate(bd.Axis.X, -90)
    return panel if side > 0 else panel.mirror(bd.Plane.XZ)


def _intake_section(y, length, height, bevel=7):
    a, h, c = length/2, height/2, bevel
    return _face([(INTAKE_X-a+c,y,-h),(INTAKE_X+a-c,y,-h),
                  (INTAKE_X+a,y,-h+c),(INTAKE_X+a,y,h-c),
                  (INTAKE_X+a-c,y,h),(INTAKE_X-a+c,y,h),
                  (INTAKE_X-a,y,h-c),(INTAKE_X-a,y,-h+c)])


def _intake_loft(stations):
    return bd.loft([_intake_section(*station) for station in stations], ruled=True)


def _intake_socket():
    return _intake_loft([(INTAKE_BACK_Y-1*K,130,68*K), (136*K,150,86*K), (159*K,150,86*K)])


def _intakes():
    """Mirrored recessed three-channel scoops with depth and shaped ramp floors."""
    outer = _intake_loft([(INTAKE_BACK_Y,128,66*K), (136*K,148,84*K), (INTAKE_LIP_Y,148,84*K)])
    bore = _intake_loft([(INTAKE_BACK_Y+3*K,122,60*K), (138*K,140,76*K), (156*K,140,76*K)])
    duct = outer-bore  # closed wall/back solid; outward mouth remains open
    ramp_face = _face([(INTAKE_X+x,y,-25*K) for x,y in
                       [(-57,112*K),(67,112*K),(67,149*K),(54,147*K),(24,133*K),(-16,119*K),(-57,116*K)]])
    ramp = (bd.Solid.extrude(ramp_face,(0,0,50*K)) & bore).solids()[0]
    parts = []
    for side,name in ((-1,"Left"),(1,"Right")):
        def place(shape):
            return shape.mirror(bd.Plane.XZ) if side < 0 else shape.moved(bd.Location((0,0,0)))
        parts.append(_style(place(duct), f"Intake{name}Duct", HARDWARE_COLOR, 0.62, 0.28))
        parts.append(_style(place(ramp), f"Intake{name}Ramp", PANEL_COLOR, 0.54, 0.32))
        for i,z in enumerate(INTAKE_SPLITTER_Z,1):
            divider = bd.Box(120,38*K,2*K).translate((INTAKE_X,133*K,z)) & bore
            parts.append(_style(place(divider.solids()[0]), f"Intake{name}Splitter{i}", PANEL_COLOR, 0.64, 0.22))
    return parts


def _fuselage():
    body = _body_loft([
        (-HALF_LENGTH, 218*K, 212*K, 31*K), (-1160, 278*K, 278*K, 35*K),
        (-1040, BODY_WIDTH, BODY_HEIGHT, CORNER_CHAMFER),
        (855, BODY_WIDTH, BODY_HEIGHT, CORNER_CHAMFER),
        (1020, 270*K, 258*K, 39*K), (1210, 211*K, 184*K, 35*K),
        (HALF_LENGTH, 172*K, 146*K, 25*K),
    ])
    # Open aft socket: the nozzle occupies this clearance, not an uncut body.
    body = body - _tube_x(-HALF_LENGTH-2, NOZZLE_DEPTH+6, 88*K)
    # Faceted optical socket, entirely open to the nose plane.
    body = body - _body_loft([(HALF_LENGTH-49, 153*K, 125*K, 24*K),
                              (HALF_LENGTH+2, 153*K, 125*K, 24*K)])
    socket = _intake_socket()
    body = body - [socket, socket.mirror(bd.Plane.XZ)]
    # Semi-recessed blades sweep through open-sided trays around a central keel.
    # Both export poses share the same pockets; no pose-specific body geometry.
    for side in (-1,1):
        # Rounded dilation contains the entire old rectangular clearance tray.
        # It removes extra material around the shoulders instead of shrinking
        # the verified wing-motion space when introducing the inner radii.
        r = WING_TRAY_BLEND_RADIUS
        tray_box = bd.Box(WING_TRAY_FORWARD_X-WING_TRAY_AFT_X+2*r,
                          WING_TRAY_OUTER_Y-WING_TRAY_INNER_Y+2*r,
                          WING_TRAY_CEILING_Z+200*K+2*r)
        tray = bd.fillet(tray_box.edges(),r).translate(
            ((WING_TRAY_FORWARD_X+WING_TRAY_AFT_X)/2,
             side*(WING_TRAY_INNER_Y+WING_TRAY_OUTER_Y)/2,
             (WING_TRAY_CEILING_Z-200*K)/2))
        body = body-tray
        # Preserve the fixed hardware's seating height while rounding its socket.
        r = WING_BAY_BLEND_RADIUS
        socket_box = bd.Box(904+2*r,74*K+2*r,39.2*K)
        bay_socket = bd.fillet(socket_box.edges(),r).translate((20,side*WING_PIVOT_Y,-140.4*K))
        body = body-bay_socket
    # Remove the sharp convex lips where the pockets meet the underside skin.
    # Select by the authored skin datum, not unstable edge indices.
    lip_edges = []
    for edge in body.edges():
        b = edge.bounding_box()
        if (abs(b.min.Z+HALF_HEIGHT) < 1e-4 and abs(b.max.Z+HALF_HEIGHT) < 1e-4
                and b.min.X > -620 and b.max.X < 490 and edge.length > 10):
            lip_edges.append(edge)
    if not lip_edges:
        raise ValueError("No wing-recess skin edges found for lip smoothing")
    body = bd.fillet(lip_edges,WING_RECESS_LIP_RADIUS)
    # Recessed panel breaks; deep core remains continuous.
    tools = []
    for x in (-1030, -735, 680, 851):
        outside = bd.Box(2.0, 340*K, 340*K).translate((x, 0, 0))
        core = _body_loft([(x-2, BODY_WIDTH-3*K, BODY_HEIGHT-3*K, CORNER_CHAMFER),
                          (x+2, BODY_WIDTH-3*K, BODY_HEIGHT-3*K, CORNER_CHAMFER)])
        tools.append(outside-core)
    return _style(body-tools, "Body", BODY_COLOR)


def _seeker():
    base = HALF_LENGTH
    surround = _body_loft([(base-49, 152*K, 124*K, 24*K), (base-20, 152*K, 124*K, 24*K),
                            (base-1, 150*K, 122*K, 24*K)])
    aperture = _body_loft([(base-39, 118*K, 86*K, 18*K), (base-13, 126*K, 95*K, 20*K),
                           (base+1, 139*K, 108*K, 22*K)])
    surround = surround-aperture
    glass = _body_loft([(SEEKER_GLASS_FRONT-4, 123*K, 92*K, 19*K),
                        (SEEKER_GLASS_FRONT, SEEKER_WINDOW_WIDTH,
                         SEEKER_WINDOW_HEIGHT, 20*K)])
    seal = _body_loft([(base-17, 128*K, 97*K, 20*K), (base-11.8, 128*K, 97*K, 20*K)])
    seal = seal - _body_loft([(base-18, 124.8*K, 93.8*K, 20*K), (base-10, 124.8*K, 93.8*K, 20*K)])
    # The seal bridges the glass-to-bezel seating gap, preserving the optical path.
    return [_style(surround, "SeekerBezel", HARDWARE_COLOR, 0.38, 0.48),
            _style(glass, "SeekerWindow", WINDOW_COLOR, 0.10, 0.08),
            _style(seal, "SeekerSeal", RECESS_COLOR, 0.86, 0.0)]


def _nozzle():
    x = NOZZLE_EXIT_X
    outer = _round_loft([(x, 85*K), (x+10, 85*K), (x+25, 80*K), (x+85, 56*K), (x+132, 56*K)])
    bore = _round_loft([(x-2, 67*K), (x+1, 66*K), (x+70, 36*K), (x+134, 36*K)])
    bell = outer-bore
    lip = _tube_x(x, 7, 87*K)-_tube_x(x-1, 9, 85.1*K)
    back = _tube_x(x+130, 3, 36*K)
    collar = _tube_x(x+12, 6, 99*K)-_tube_x(x+11, 8, 88.5*K)
    return [_style(bell, "HybridNozzle", NOZZLE_COLOR, 0.46, 0.55),
            _style(lip, "NozzleExitLip", EDGE_COLOR, 0.38, 0.7),
            _style(back, "NozzleRecess", RECESS_COLOR, 0.94, 0.0),
            _style(collar, "NozzleRetention", HARDWARE_COLOR)]


def _wing_local():
    """Parallel chord edges align with body X when stowed; only ends are clipped.

    The hinge is nearer the forward end to keep the enlarged inboard root corners
    apart throughout sweep. The paired stowed panels have a scaled center gap and
    end inboard of each maximum-width body side in plan projection.
    """
    sections = []
    for x, chord, thickness in [(30, 72*K, 12*K), (5, WING_CHORD, 15*K),
                                 (-90, WING_CHORD, WING_THICKNESS),
                                 (-875, WING_CHORD, 8*K),
                                 (-WING_LENGTH+7, WING_CHORD, 6*K),
                                 (-WING_LENGTH, WING_CHORD-14*K, 5*K)]:
        c, t = chord/2, thickness/2
        sections.append(_face([(x,-c,-0.6*K),(x,-c*0.72,-t*0.75),
                                (x,-c*0.22,-t),(x,c*0.76,-t*0.34),(x,c,-0.5*K),
                                (x,c,0.5*K),(x,c*0.76,t*0.34),(x,-c*0.22,t),
                                (x,-c*0.72,t*0.75),(x,-c,0.6*K)]))
    return bd.loft(sections, ruled=True)


def wing_placement(shape, side, angle):
    """Explicit rigid transform; left is the mirror of the right local part."""
    if side < 0:
        shape = shape.mirror(bd.Plane.XZ)
    return shape.rotate(bd.Axis.Z, -side*angle).translate(
        (WING_PIVOT_X, side*WING_PIVOT_Y, WING_PIVOT_Z))


def _wings(angle):
    parts = []
    blade = _wing_local()
    cap = bd.Cylinder(24*K, 5*K).translate((0, 0, -8.0*K))
    for side, name in ((-1, "Left"), (1, "Right")):
        parts.append(_style(wing_placement(blade, side, angle), f"Wing{name}", WING_COLOR))
        parts.append(_style(wing_placement(cap, side, angle), f"Wing{name}PivotCap", HARDWARE_COLOR))
    return parts


def _wing_housings():
    parts = []
    for side, name in ((-1, "Left"), (1, "Right")):
        y = side*WING_PIVOT_Y
        housing = _panel_xy(20, y, 147.0*K, 900, 70*K, 11*K, 20*K).mirror(bd.Plane.XY)
        # Tapered cover stops above rotating wing; boss and axle bridge the gap.
        boss = bd.Cylinder(32*K, 9*K).translate((WING_PIVOT_X, y, -160*K))
        axle = bd.Cylinder(12*K, 15*K).translate((WING_PIVOT_X, y, -168*K))
        housing = (housing + boss + axle).translate((0,0,WING_RECESS_SHIFT))
        parts.append(_style(housing, f"WingBay{name}", PANEL_COLOR))
    return parts


def _tail_controls():
    parts = []
    for index, angle in enumerate(TAIL_ANGLES, 1):
        sections = []
        for radius, aft, front, thick in [(182*K,-1140,-838,14*K),
                                           (215*K,-1130,-877,11*K),
                                           (TAIL_RADIUS,-1080,-943,5*K)]:
            sections.append(_face([(aft,-0.6*K,radius), (aft+35,-thick/2,radius),
                                    (front-34,-thick/2,radius), (front,-0.7*K,radius),
                                    (front,0.7*K,radius),(front-34,thick/2,radius),
                                    (aft+35,thick/2,radius),(aft,0.6*K,radius)]))
        fin = bd.loft(sections, ruled=True).rotate(bd.Axis.X, angle)
        saddle_sections = []
        for x, width, lower, upper in [(-1161.5,3*K,167*K,176*K), (-1140,18*K,170*K,190*K),
                                       (-1050,18*K,181*K,193*K), (-840,15*K,182*K,193*K),
                                       (-818.5,2*K,182*K,187*K)]:
            saddle_sections.append(_face([(x,-width,lower),(x,width,lower),
                                           (x,width,upper-4*K),(x,width*0.58,upper),
                                           (x,-width*0.58,upper),(x,-width,upper-4*K)]))
        saddle = bd.loft(saddle_sections, ruled=True).rotate(bd.Axis.X, angle)
        parts.append(_style(fin, f"TailControl{index}", WING_COLOR))
        parts.append(_style(saddle, f"TailRoot{index}", HARDWARE_COLOR))
    return parts


def _mounting_hardware():
    rail = _panel_xy(-70, 0, HALF_HEIGHT-0.8, 800, 24*K, 9*K, 10*K)
    # Raised center rib provides a narrow, legible rail rather than a floating bar.
    rail = rail + bd.Box(700, 9*K, 7*K).translate((-70, 0, HALF_HEIGHT+10*K))
    parts = [_style(rail, "MountRail", HARDWARE_COLOR)]
    for x, name in ((155, "ForwardLug"), (-330, "AftLug")):
        shoe = _panel_xy(x, 0, HALF_HEIGHT+7*K, 52, 38*K, 16*K, 8*K)
        shoe = shoe - bd.Box(30, 42*K, 5*K).translate((x, 0, HALF_HEIGHT+13*K))
        # Top and foot connected by the forward/aft end walls.
        parts.append(_style(shoe, name, EDGE_COLOR, 0.43, 0.65))
    service = _panel_xy(438, 0, HALF_HEIGHT-0.6, 138, 49*K, 4*K, 12*K)
    parts.append(_style(service, "DorsalUmbilicalCover", PANEL_COLOR))
    return parts


def _surface_details():
    parts = []
    for side, name in ((-1, "Left"), (1, "Right")):
        for x, length, height, z, token in [(INTAKE_X, 196, 105*K, 0, "AftService"),
                                           (480, 244, 99*K, 0, "Avionics"),
                                           (-190, 775, 43*K, -77*K, "StowageEdge")]:
            panel = _side_panel(x, side, z, length, height)
            if token == "AftService":
                aperture = _intake_loft([(109*K,148,84*K),(155*K,148,84*K)])
                panel = panel-(aperture if side > 0 else aperture.mirror(bd.Plane.XZ))
            parts.append(_style(panel, f"{token}{name}", PANEL_COLOR))
        for x in (INTAKE_X-83, INTAKE_X+83, 383, 577):
            for z in (-34*K, 34*K):
                screw = bd.Cylinder(3.3, 1.3).rotate(bd.Axis.X, 90).translate(
                    (x, side*(HALF_WIDTH+3), z))
                parts.append(_style(screw, f"PanelFastener{name}_{x:g}_{z:g}", EDGE_COLOR))
    belly = _panel_xy(715, 0, HALF_HEIGHT-0.5, 177, 128*K, 3.5*K, 16*K).mirror(bd.Plane.XY)
    parts.append(_style(belly, "VentralServiceCover", PANEL_COLOR))
    # Narrow nose-section ID band is shallow raised geometry with no coincident skin.
    band = _body_loft([(877, 294*K, 293*K, 34*K), (886, 292.6*K, 291*K, 34*K)])
    inside = _body_loft([(876, 288*K, 287*K, 34*K), (887, 288*K, 287*K, 34*K)])
    parts.append(_style(band-inside, "SeekerIdentificationBand", ACCENT_COLOR, 0.62, 0.12))
    return parts


def semantic_group(label):
    """Single source of Unity grouping intent; unknown labels fail closed."""
    if label == "Body":
        return "body"
    if label == "SeekerWindow":
        return "seeker_glass"
    if label in {"SeekerBezel", "SeekerSeal"}:
        return "seeker_bezel"
    if label.startswith("WingLeft"):
        return "wing_left"
    if label.startswith("WingRight"):
        return "wing_right"
    if label.startswith("TailControl"):
        return "tail_" + label[-1]
    if label.startswith("Nozzle") or label == "HybridNozzle":
        return "propulsion"
    if label.startswith("Intake"):
        return "intakes"
    if label in {"MountRail", "ForwardLug", "AftLug", "DorsalUmbilicalCover"}:
        return "mounting"
    if label.startswith(("WingBay", "TailRoot", "AftService", "Avionics", "StowageEdge",
                         "Vent", "PanelFastener")) or label == "SeekerIdentificationBand":
        return "fixed_hardware"
    raise ValueError(f"Unclassified Ballista part: {label}")


def make_ballista(deployed=False, wing_angle=None, detail=True):
    angle = WING_ANGLE if deployed else WING_STOWED_ANGLE
    if wing_angle is not None:
        angle = wing_angle
    parts = [_fuselage(), *_seeker(), *_nozzle(), *_wing_housings(),
             *_tail_controls(), *_mounting_hardware(), *_wings(angle), *_intakes()]
    if detail:
        parts.extend(_surface_details())
    for part in parts:
        semantic_group(part.label)
    return bd.Compound(label="AGM-110 Ballista " + ("Deployed" if deployed else "Stowed"),
                       children=parts)
