"""Selected hybrid: Chisel body, Sculpted rear, original Shoulder nose/intakes.

Exterior game geometry only. Millimeters, centered X-axis, Z dorsal.
"""
from cadgen import build123d as bd, step
from halberd_concept_shapes import (
    tagged, disk, barrel, oval, clock, fin, visual_nozzle, CERAMIC, TRIM, DARK,
)
from halberd_shoulder_variants import section

LENGTH = 3367.0
HALF = LENGTH / 2
SEAM = -336.7
WIDTH = 208.0
CORNER = 12.0
NOSE_BASE = 1080.0
ANGLES = (45, 135, 225, 315)
NOSE_CYLINDER_RADIUS = 86.0
TRANSITION_END_X = 850.0
INTAKE_END_X = 850.0


def intake_section(x, radial, half_width, half_height):
    """Exact elliptical section with explicit quadrant edges.

    Avoid a single periodic surface around each trimmed intake: the viewport
    mesher can lose triangles where the trim crosses that surface's UV seam.
    Quadrants keep the same ellipse but give the mesher bounded surface patches.
    """
    wire=bd.Wire([
        bd.Edge.make_ellipse(half_height,half_width,start_angle=a,end_angle=a+90)
        for a in (0,90,180,270)
    ])
    return bd.Face(wire).rotate(bd.Axis.Y,90).translate((x,0,radial))


def intake_exit_blend():
    """Continue the intake's elliptical curvature, wholly behind the original end.

    A fixed-normal sweep retains the actual curved section across its width;
    there is no planar floor and no extended scallop on the nose cylinder.
    """
    rise=(INTAKE_END_X-790)/5*(3/170)
    path=bd.Edge.make_bezier(
        (790,0,106),(802,0,106+rise),(814,0,106+2*rise),
        (826,0,110),(838,0,110),(INTAKE_END_X,0,110),
    )
    return bd.sweep(intake_section(790,106,42,24),path=path,normal=(1,0,0))


def intake_passage():
    """Corner subtraction beneath the original skin, not an external housing.

    Its forward footprint approaches the circular nose silhouette. The internal
    centerline moves inward with decreasing X. The front uses the existing
    curved section and ends at the original square-to-round transition.
    """
    passage = bd.loft([
        intake_section(350, 70, 18, 10),
        # Keep the buried part narrow enough to retain both flat side skins.
        # Most of the widening belongs in the exposed square-to-round transition.
        intake_section(535, 86, 20, 17),
        # Open through the curved crown before widening through the adjacent flats.
        # This avoids two side slots with a thin pointed strip left between them.
        intake_section(620, 99, 23, 20),
        intake_section(790, 106, 42, 24),
    ], ruled=True)
    return passage.fuse(intake_exit_blend())


@step(out="Halberd_Shoulder_Hybrid.step")
def halberd_shoulder_hybrid():
    # Chisel's planar body turns into the original round forebody ahead of the intakes.
    body = bd.loft([
        section(SEAM, WIDTH, WIDTH, CORNER),
        section(400, WIDTH, WIDTH, CORNER),
        section(650, 192, 192, 32),
        disk(TRANSITION_END_X, NOSE_CYLINDER_RADIUS), disk(NOSE_BASE, NOSE_CYLINDER_RADIUS),
    ], ruled=True)
    passage = intake_passage()
    for angle in ANGLES:
        body -= clock(passage, angle)
    radius = WIDTH*.31
    body -= barrel(SEAM-1, SEAM+70, radius)
    parts = [tagged(body, "sustainer_body")]
    nose = bd.loft([disk(NOSE_BASE, 86), disk(1280, 80), disk(1475, 52),
                    disk(1625, 16), disk(HALF, .8)], ruled=False)
    parts.append(tagged(nose, "radome", CERAMIC))
    parts.append(tagged(visual_nozzle(SEAM, 70, radius), "sustainer_nozzle", TRIM))
    for i, angle in enumerate(ANGLES, 1):
        # Dark recessed backing at the blind aft end, entirely inside the hull.
        # Preserve the semantic label; this cannot become an external cover.
        floor = bd.loft([oval(349.5, 70, 18, 10), oval(352, 70, 17.5, 9.5)], ruled=True)
        parts.append(tagged(clock(floor, angle), f"intake_floor_{i}", DARK))
        aft = SEAM+95
        parts.append(tagged(clock(fin(aft, aft+360, aft-30, aft+114, 220, WIDTH*.52, 11), angle),
                            f"sustainer_fin_{i}", TRIM))

    # Full section is constant across the seam. The rear then becomes progressively softer.
    booster = bd.loft([
        section(-HALF, WIDTH*.8, WIDTH*.8, 62.4),
        section(-HALF+240, WIDTH, WIDTH, 78),
        section(-1000, WIDTH, WIDTH, 64),
        section(SEAM-180, WIDTH, WIDTH, CORNER),
        section(SEAM, WIDTH, WIDTH, CORNER),
    ], ruled=True)
    booster -= barrel(-HALF-1, -HALF+75, radius*.82)
    booster -= bd.loft([disk(SEAM-10, radius*.68), disk(SEAM+1, radius*.8)], ruled=True)
    parts.append(tagged(booster, "booster_body"))
    parts.append(tagged(visual_nozzle(-HALF, 75, radius*.82), "booster_nozzle", TRIM))
    for i, angle in enumerate(ANGLES, 1):
        aft = -HALF+110
        parts.append(tagged(clock(fin(aft, aft+430, aft+71.5, aft+252.1, 242, 96, 13), angle),
                            f"booster_fin_{i}", TRIM))
    for i, x in enumerate((0, 480), 1):
        parts.append(tagged(bd.Box(62, 25, 10).translate((x, 0, 105)), f"mount_{i}", TRIM))
    return bd.Compound(children=parts, label="Halberd_Shoulder_Hybrid")


if __name__ == "__main__":
    halberd_shoulder_hybrid()
