"""Tail-only Kris/PL-10 exterior art hybrid; neither original model is modified.

Reuse the authored Kris lattice and cant, scaled uniformly to the PL-10 body.
Keep the PL-10's four tail stations and TVC mounting datum and outer profile.
Matching-profile saddles and triangular static vanes; no active mechanisms.
"""

import math
from pathlib import Path

from cadgen import build123d as bd, read_step, report, srgb, step

from generate_kris import BODY_RADIUS as KRIS_BODY_RADIUS
from generate_pl10 import beveled_plate, cylinder, fastener


BODY_RADIUS = 72.5
GRID_SCALE = BODY_RADIUS / KRIS_BODY_RADIUS
AZIMUTHS = (0, 90, 180, 270)
HINGE_RADIUS = 105 * GRID_SCALE
HINGE_Z = 158 * GRID_SCALE
HINGE_HALF_LENGTH = (45 + 18) * GRID_SCALE / 2
BODY_COLOR = srgb("#D0D0C9")
METAL_COLOR = srgb("#8E9797")
GRID_COLOR = srgb("#252A2D")
SEEKER_WINDOW_MATERIAL = {
    "roughness": 0.06, "metalness": 0.05,
    "clearcoat": 1.0, "clearcoatRoughness": 0.025,
}
REMOVED_PREFIXES = ("stepped_tail_fin_", "tail_mount_", "tvc_exterior_mount_", "tvc_static_vane_")
AFT_BORE_RADIUS = 60.0
GROUP_INNER_WALL = BODY_RADIUS - 0.6
GROUP_RADIAL_OFFSETS = {i: AFT_BORE_RADIUS - GROUP_INNER_WALL for i in range(1, 5)}
TVC_REAR_Z = -28.25
TVC_FRONT_Z = -8.25
TVC_CHAMFER_RADIAL = 6.0
TVC_CHAMFER_AXIAL = 9.0
VANE_REAR_Z = TVC_REAR_Z + 4.0 + 15.0
VANE_AXIAL_SPAN = 35.0
VANE_INWARD_SPAN = 35.0
VANE_MOUNT_DIAMETER = 7.0
VANE_MOUNT_HEIGHT = 0.5
HOUSING_RETURN_START_Z = 165.0
HOUSING_RETURN_END_Z = 225.0
PROTOTYPE_FIN_STATION = 2  # Reference station for the approved fin geometry.
GRID_CANT_DEGREES = 18.0
GRID_DEPTH = 45.0 * GRID_SCALE
GRID_FRAME_WIDTH = 3.5
PROTOTYPE_FOOT_ROOT_RADIUS = 75.6
PROTOTYPE_FOOT_FILLET = 3.0  # Fits the shorter, narrower foot while retaining rounding.
PROTOTYPE_FOOT_WIDTH = 32.0
PROTOTYPE_FOOT_HEIGHT_SCALE = 0.5
PROTOTYPE_SPAN_SCALE = 1.25
PROTOTYPE_WIDTH_SCALE = 1.5
HEX_CELL_PITCH = 28.75  # 26.75 mm clear opening: 1.671875x the previous 16 mm.
HEX_WALL_THICKNESS = 2.0
HEX_COLUMN_PHASE = 0.5625
HEX_ROW_PHASE = 0.5


def end_on_outline(shape):
    """Convex outer outline of the faceted TVC block, excluding its vane pocket."""
    points = sorted({(round(v.X, 9), round(v.Y, 9)) for v in shape.vertices()})
    def cross(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    chains = []
    for sequence in (points, list(reversed(points))):
        chain = []
        for point in sequence:
            while len(chain) >= 2 and cross(chain[-2], chain[-1], point) <= 1e-8:
                chain.pop()
            chain.append(point)
        chains.append(chain[:-1])
    outline = chains[0] + chains[1]
    if len(outline) < 3:
        raise ValueError("TVC mount has no closed end-on outline")
    return outline


def hex_fin_prototype():
    """Prototype with a 32 mm rounded mounting foot and 2 mm shared hex walls.

    Symmetric interpretation of the supplied top view. The rounded flared foot
    replaces the cylindrical hinge, and the frame retains its 18-degree cant.
    """
    original_tip = math.sqrt(263.0 ** 2 - 21.0 ** 2) * GRID_SCALE
    image_scale = (original_tip - HINGE_RADIUS) / 662.0
    original_neck = HINGE_RADIUS + 51.0 * image_scale
    housing_roof = BODY_RADIUS + 16 + GROUP_RADIAL_OFFSETS[PROTOTYPE_FIN_STATION]
    neck_radius = housing_roof + (original_neck - housing_roof) * PROTOTYPE_FOOT_HEIGHT_SCALE
    tip_radius = neck_radius + (original_tip - original_neck) * PROTOTYPE_SPAN_SCALE
    shoulder_radius = neck_radius + 99.0 * image_scale * PROTOTYPE_SPAN_SCALE
    width_scale = image_scale * PROTOTYPE_WIDTH_SCALE
    neck_half_width = PROTOTYPE_FOOT_WIDTH * 95.0 / 225.0
    shoulder_half_width, tip_half_width = 200.0 * width_scale, 89.0 * width_scale
    # Solve for the pre-fillet corner width so the finished rounded foot—not
    # the discarded sharp-corner construction polygon—is exactly 32 mm wide.
    run = neck_radius - PROTOTYPE_FOOT_ROOT_RADIUS
    def finished_half_width(raw):
        flare = raw - neck_half_width
        return raw + PROTOTYPE_FOOT_FILLET - PROTOTYPE_FOOT_FILLET * (math.hypot(run, flare) + flare) / run
    low, high = PROTOTYPE_FOOT_WIDTH / 2, PROTOTYPE_FOOT_WIDTH / 2 + 2 * PROTOTYPE_FOOT_FILLET
    if finished_half_width(high) < PROTOTYPE_FOOT_WIDTH / 2:
        raise ValueError("Foot width cannot accommodate the selected fillet")
    for _ in range(60):
        middle = (low + high) / 2
        if finished_half_width(middle) < PROTOTYPE_FOOT_WIDTH / 2:
            low = middle
        else:
            high = middle
    foot_half_width = (low + high) / 2
    outer = [
        (neck_radius, -neck_half_width), (shoulder_radius, -shoulder_half_width),
        (tip_radius, -tip_half_width), (tip_radius, tip_half_width),
        (shoulder_radius, shoulder_half_width), (neck_radius, neck_half_width),
    ]
    outer_wire = bd.Wire.make_polygon([(x, y, 0) for x, y in outer], close=True)
    inner_wire = outer_wire.offset_2d(-GRID_FRAME_WIDTH, kind=bd.Kind.INTERSECTION)
    if bd.Face(inner_wire).area >= bd.Face(outer_wire).area:
        raise ValueError("Fin frame offset did not shrink the aperture")
    # One outline lets the neck fillets flow into the frame rather than leaving
    # sharp corners where a separately rounded foot would meet it.
    combined = [(PROTOTYPE_FOOT_ROOT_RADIUS, -foot_half_width), *outer,
                (PROTOTYPE_FOOT_ROOT_RADIUS, foot_half_width)]
    face = bd.Face(bd.Wire.make_polygon([(x, y, 0) for x, y in combined], close=True))
    foot_corners = [v for v in face.vertices()
                    if abs(v.X - PROTOTYPE_FOOT_ROOT_RADIUS) < 1e-6 or abs(v.X - neck_radius) < 1e-6]
    face = face.fillet_2d(PROTOTYPE_FOOT_FILLET, foot_corners)
    blank = bd.Solid.extrude(face, (0, 0, GRID_DEPTH))
    report("clipped hexagonal infill with shared 2 mm walls")
    aperture = bd.Face(inner_wire)
    tile_radius = HEX_CELL_PITCH / math.sqrt(3)
    hole_radius = (HEX_CELL_PITCH - HEX_WALL_THICKNESS) / math.sqrt(3)
    column_pitch = 1.5 * tile_radius
    origin = (neck_radius + tip_radius) / 2
    cutters = []
    for column in range(math.floor((neck_radius - origin) / column_pitch) - 1,
                        math.ceil((tip_radius - origin) / column_pitch) + 2):
        x = origin + (column + HEX_COLUMN_PHASE) * column_pitch
        for row in range(math.floor(-shoulder_half_width / HEX_CELL_PITCH) - 2,
                         math.ceil(shoulder_half_width / HEX_CELL_PITCH) + 3):
            y = (row + HEX_ROW_PHASE) * HEX_CELL_PITCH + (column % 2) * HEX_CELL_PITCH / 2
            hexagon = bd.Face(bd.Wire.make_polygon([
                (x + hole_radius * math.cos(math.radians(60 * k)),
                 y + hole_radius * math.sin(math.radians(60 * k)), 0)
                for k in range(6)
            ], close=True))
            clipped = hexagon & aperture
            if clipped is not None and clipped.area > 1e-8:
                for hole in clipped.faces():
                    cutters.append(bd.Solid.extrude(hole, (0, 0, GRID_DEPTH + 2)).translate((0, 0, -1)))
    if not cutters:
        raise ValueError("Hexagonal lattice generated no cell openings")
    blank = blank.cut(*cutters)
    z0 = HINGE_Z - GRID_DEPTH / 2
    slope = -math.tan(math.radians(GRID_CANT_DEGREES))
    return blank.transform_geometry(bd.Matrix([
        [1, 0, 0, 0], [0, 1, 0, 0],
        [slope, 0, 1, z0 - slope * HINGE_RADIUS], [0, 0, 0, 1],
    ]))


def footprint_prism(outline, z0, z1):
    wire = bd.Wire.make_polygon([(x, y, z0) for x, y in outline], close=True)
    return bd.Solid.extrude(bd.Face(wire), (0, 0, z1 - z0))


def saddle(outline, z0, z1):
    result = footprint_prism(outline, z0, z1)
    # The markup calls for a straight inner wall, tangent after the group offset.
    mask = bd.Box(100, 200, z1 - z0 + 2).translate((GROUP_INNER_WALL + 50, 0, (z0 + z1) / 2))
    return result & mask


def concave_return(outline, radial_offset):
    """Smooth inward return from the housing outline to the actual body cylinder."""
    clipped = []
    for a, b in zip(outline, outline[1:] + outline[:1]):
        inside_a, inside_b = a[0] >= GROUP_INNER_WALL, b[0] >= GROUP_INNER_WALL
        if inside_a:
            clipped.append(a)
        if inside_a != inside_b:
            t = (GROUP_INNER_WALL - a[0]) / (b[0] - a[0])
            clipped.append((GROUP_INNER_WALL, a[1] + t * (b[1] - a[1])))

    # Split edges where they enter the body, so the terminal outer edges are
    # true circular arcs; hidden parts of the closing profile remain straight.
    segments = []
    for a, b in zip(clipped, clipped[1:] + clipped[:1]):
        ax, ay = a[0] + radial_offset, a[1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        aa, bb = dx * dx + dy * dy, 2 * (ax * dx + ay * dy)
        cc = ax * ax + ay * ay - BODY_RADIUS ** 2
        disc = bb * bb - 4 * aa * cc
        cuts = [0.0, 1.0]
        if aa > 1e-12 and disc > 0:
            cuts.extend(t for t in ((-bb - math.sqrt(disc)) / (2 * aa),
                                    (-bb + math.sqrt(disc)) / (2 * aa)) if 1e-8 < t < 1 - 1e-8)
        cuts.sort()
        for t0, t1 in zip(cuts, cuts[1:]):
            segments.append(((a[0] + t0 * dx, a[1] + t0 * dy),
                             (a[0] + t1 * dx, a[1] + t1 * dy)))

    def mapped(point, fraction, z):
        x, y = point[0] + radial_offset, point[1]
        radius = math.hypot(x, y)
        if radius > BODY_RADIUS:
            factor = fraction + (1 - fraction) * BODY_RADIUS / radius
            x, y = x * factor, y * factor
        return (x - radial_offset, y, z)

    wires = []
    for t in (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0):
        # Zero endpoint slopes with an inward-bowed middle, rather than a cone.
        fraction = (1 - 3 * t * t + 2 * t * t * t) ** 2
        z = HOUSING_RETURN_START_Z + t * (HOUSING_RETURN_END_Z - HOUSING_RETURN_START_Z)
        edges = []
        for a, b in segments:
            pa, pb = mapped(a, fraction, z), mapped(b, fraction, z)
            pm = mapped(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), fraction, z)
            cross = (pm[0] - pa[0]) * (pb[1] - pa[1]) - (pm[1] - pa[1]) * (pb[0] - pa[0])
            edges.append(bd.Edge.make_line(pa, pb) if abs(cross) < 1e-8
                         else bd.Edge.make_three_point_arc(pa, pm, pb))
        wires.append(bd.Wire(edges))
    return bd.Solid.make_loft(wires, ruled=False)


def rounded_return(outline, radial_offset):
    """Approved rounded planform with a smooth noseward arched end."""
    cap = concave_return(outline, radial_offset)
    half_width = max(abs(point[1]) for point in outline)
    length = HOUSING_RETURN_END_Z - HOUSING_RETURN_START_Z
    # Analytic elliptical planform: full width at the shoulder, rounded at the
    # noseward end. Intersect the existing valid roof instead of pinching a loft.
    mask = bd.extrude(bd.Ellipse(length, half_width), amount=200)
    mask = mask.rotate(bd.Axis.Y, 90).translate((0, 0, HOUSING_RETURN_START_Z))
    return cap & mask


def fitted_housing(outline, grid, radial_offset, rounded=False, hinge_covers=True):
    # Express the stationary grid in the moving group's local coordinates.
    pocket_grid = grid.translate((-radial_offset, 0, 0))
    cap = rounded_return(outline, radial_offset) if rounded else concave_return(outline, radial_offset)
    housing = saddle(outline, 85, HOUSING_RETURN_START_Z).fuse(cap)
    housing -= pocket_grid
    collars = []
    cover_stations = (HINGE_Z - HINGE_HALF_LENGTH - 1.5, HINGE_Z + HINGE_HALF_LENGTH - 1) if hinge_covers else ()
    for z in cover_stations:
        collar = cylinder(z, z + 2.5, 12.5).translate((HINGE_RADIUS, 0, 0))
        collar &= saddle(outline, z, z + 2.5)
        collar -= pocket_grid
        collars.append(collar)
        housing -= collar
    return housing, collars


@step(out="IRM-S4_Kris_PL10_Hybrid.step")
def kris_hybrid():
    source = read_step(Path(__file__).with_name("PL-10_Stencil_Revision.step"))
    parts = [part for part in source.children if not part.label.startswith(REMOVED_PREFIXES)]
    if len(source.children) - len(parts) != 40:
        raise ValueError("Unexpected PL-10 tail/TVC part set; review the hybrid filter")
    seeker_window = next(part for part in parts if part.label == "dark_nose_window")
    seeker_window.cad_material = dict(SEEKER_WINDOW_MATERIAL)
    source_mount = next(part for part in source.children if part.label == "tvc_exterior_mount_1")
    outline = end_on_outline(source_mount)

    def add(shape, label, color, angle, radial_offset=0):
        if radial_offset:
            shape = shape.translate((radial_offset, 0, 0))
        shape = shape.rotate(bd.Axis.Z, angle)
        shape.label, shape.color = label, color
        shape.cad_material = {"roughness": 0.55, "metalness": 0.35}
        parts.append(shape)

    report("Kris lattice fin and matching-profile saddles")
    grid = hex_fin_prototype()
    # The TVC block, support and fin housing share one exposed end-on outline.
    support = saddle(outline, -8.25, 85)
    housing_groups = {offset: fitted_housing(outline, grid, offset, True, hinge_covers=False)
                      for offset in set(GROUP_RADIAL_OFFSETS.values())}

    report("sketched chamfered mounting blocks and right-triangular vanes")
    mount_profile = [
        (GROUP_INNER_WALL, TVC_FRONT_Z), (BODY_RADIUS + 16, TVC_FRONT_Z),
        (BODY_RADIUS + 16, TVC_REAR_Z),
        (GROUP_INNER_WALL + TVC_CHAMFER_RADIAL, TVC_REAR_Z),
        (GROUP_INNER_WALL, TVC_REAR_Z + TVC_CHAMFER_AXIAL),
    ]
    wire = bd.Wire.make_polygon([(x, -26, z) for x, z in mount_profile], close=True)
    mount = bd.Solid.extrude(bd.Face(wire), (0, 52, 0))
    mount &= footprint_prism(outline, TVC_REAR_Z, TVC_FRONT_Z)
    # Vertical root at the blue inner wall; horizontal aft edge and inward point.
    vane = beveled_plate([
        (GROUP_INNER_WALL - VANE_INWARD_SPAN, VANE_REAR_Z),
        (GROUP_INNER_WALL, VANE_REAR_Z),
        (GROUP_INNER_WALL, VANE_REAR_Z + VANE_AXIAL_SPAN),
    ], thickness=1.4, bevel=0.2)
    # The raised root enters the circular aft opening. Trim the tiny corner
    # interference at its tangential thickness without changing the side profile.
    aft_cover = next(part for part in source.children if part.label == "aft_end_cover")
    local_aft_cover = aft_cover.translate((-GROUP_RADIAL_OFFSETS[1], 0, 0))
    vane -= local_aft_cover
    boss = cylinder(0, VANE_MOUNT_HEIGHT, VANE_MOUNT_DIAMETER / 2).rotate(bd.Axis.Y, -90)
    boss = boss.translate((GROUP_INNER_WALL, 0, VANE_REAR_Z + VANE_AXIAL_SPAN / 2))
    # Preserve the full circular exposed face while fitting the back to the bore.
    boss -= local_aft_cover
    vane -= boss

    for i, angle in enumerate(AZIMUTHS, 1):
        offset = GROUP_RADIAL_OFFSETS.get(i, 0.0)
        housing, collars = housing_groups[offset]
        add(grid, f"kris_grid_fin_{i}", GRID_COLOR, angle)
        add(housing, f"grid_fin_housing_{i}", BODY_COLOR, angle, offset)
        add(support, f"grid_tvc_support_{i}", BODY_COLOR, angle, offset)
        add(mount, f"tvc_exterior_mount_{i}", METAL_COLOR, angle, offset)
        add(vane, f"tvc_static_vane_{i}", GRID_COLOR, angle, offset)
        for j, collar in enumerate(collars, 1):
            add(collar, f"grid_hinge_cover_{i}_{j}", METAL_COLOR, angle, offset)
        for side, suffix in ((-1, "left"), (1, "right")):
            bolt = fastener(151, BODY_RADIUS + 15.7, 1.4).translate((0, side * 8, 0))
            add(bolt, f"grid_housing_fastener_{i}_{suffix}", METAL_COLOR, angle, offset)

    # Append these so the existing component references retain their ordering.
    for i, angle in enumerate(AZIMUTHS, 1):
        add(boss, f"tvc_vane_mount_{i}", METAL_COLOR, angle, GROUP_RADIAL_OFFSETS[i])

    report("complementary body pockets beneath all fin housings")
    # Keep separate selectable housings, but remove the competing body skin.
    # The housings fill these pockets; their exterior is not duplicated beneath.
    index = next(i for i, part in enumerate(parts) if part.label == "body_section_1")
    original_body = parts[index]
    housings = [part for part in parts if part.label.startswith("grid_fin_housing_")]
    trimmed_body = original_body.cut(*housings)
    body_solids = sorted(trimmed_body.solids(), key=lambda solid: solid.volume, reverse=True)
    if not body_solids:
        raise ValueError("Body pocket boolean removed the connected body")
    fragments = sum(solid.volume for solid in body_solids[1:])
    if fragments > original_body.volume * 1e-6:
        raise ValueError("Body pockets produced significant disconnected material")
    # Remove only negligible, disconnected surface flakes from the near-tangent
    # boolean. They are not part of a connected body and cause rendering speckles.
    trimmed_body = body_solids[0]
    loss = original_body.volume - trimmed_body.volume
    if loss < -1e-4 or loss > sum(part.volume for part in housings) + 1e-4:
        raise ValueError("Body pocket boolean violated the material-volume bound")
    trimmed_body.label = original_body.label
    trimmed_body.color = original_body.color
    trimmed_body.cad_material = getattr(original_body, "cad_material", {"roughness": 0.65, "metalness": 0.1})
    parts[index] = trimmed_body

    model = bd.Compound(children=parts, label="IRM_S4_Kris_PL10_Tail_Hybrid")
    if len({part.label for part in parts}) != len(parts):
        raise ValueError("Duplicate hybrid part labels")
    if abs(model.bounding_box().max.Z - 2870) > 0.01 or abs(model.bounding_box().min.Z + 28.25) > 0.01:
        raise ValueError("Hybrid changed the nose tip or TVC aft extent")
    return model


if __name__ == "__main__":
    kris_hybrid()
