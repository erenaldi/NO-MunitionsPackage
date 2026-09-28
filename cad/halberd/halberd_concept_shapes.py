"""Clean-sheet exterior concept studies; no imports from production Halberd CAD.

Millimeters; X forward, Z dorsal. Shapes describe fictional game visuals only.
Both studies share presentation datums, not production geometry or engine design.
"""
from cadgen import build123d as bd, srgb

NOSE = 1683.5
TAIL = -1683.5
SEAM = -336.7
HULL = srgb("#A6ADAF")
TRIM = srgb("#626C70")
DARK = srgb("#333B3E")
CERAMIC = srgb("#D3D5D1")


def tagged(shape, label, color=HULL):
    shape.label = label
    shape.color = color
    shape.cad_material = {"roughness": 0.72, "metalness": 0.08}
    return shape


def disk(x, radius):
    return bd.Circle(radius).rotate(bd.Axis.Y, 90).translate((x, 0, 0))


def barrel(a, b, radius):
    return bd.loft([disk(a, radius), disk(b, radius)], ruled=True)


def revolved_envelope(stations):
    return bd.loft([disk(x, r) for x, r in stations], ruled=True)


def oval(x, radial, half_width, half_height):
    # Y is lateral, Z is radial in the unrotated intake prototype.
    return bd.Ellipse(half_height, half_width).rotate(bd.Axis.Y, 90).translate((x, 0, radial))


def clock(shape, angle):
    return shape.rotate(bd.Axis.X, -angle)


def fin(aft, forward, tip_aft, tip_forward, radius, root_radius, thickness):
    # Sculpted wedge blade rather than the previous model's sampled aerofoil.
    wires = []
    for z, a, b, t in ((root_radius, aft, forward, thickness),
                        (radius, tip_aft, tip_forward, thickness * 0.45)):
        wires.append(bd.Wire.make_polygon([
            (a, 0, z), (a + (b-a)*0.35, -t/2, z),
            (b, 0, z), (a + (b-a)*0.35, t/2, z),
        ], close=True))
    return bd.Solid.make_loft(wires, ruled=True)


def visual_nozzle(aft, extent, radius):
    # Closed blind recess only, no interior propulsion model.
    shell = barrel(aft, aft + extent, radius)
    cavity = revolved_envelope([(aft - 1, radius - 9),
                                (aft + extent * 0.65, radius * 0.43),
                                (aft + extent - 5, radius * 0.38)])
    return shell - cavity


def mounting(parts, wide=False):
    for i, x in enumerate((100.0, 590.0), 1):
        width = 32 if wide else 25
        shoe = bd.Box(68, width, 12).translate((x, 0, 101))
        shoe = shoe - bd.Box(42, width-10, 5).translate((x, 0, 107))
        parts.append(tagged(shoe, f"mount_shoe_{i}", TRIM))


def pod():
    angles = (60, 180, 300)
    parts = []
    body = revolved_envelope([(SEAM+70, 88), (-180, 99), (910, 99), (1120, 93)])
    parts.append(tagged(body, "sustainer_body"))
    nose = bd.loft([disk(1120, 93), disk(1290, 83), disk(1470, 53),
                    disk(1610, 21), disk(NOSE, 0.8)], ruled=False)
    parts.append(tagged(nose, "radome", CERAMIC))
    parts.append(tagged(visual_nozzle(SEAM, 70, 88), "sustainer_nozzle", TRIM))
    for i, angle in enumerate(angles, 1):
        outer = bd.loft([oval(170, 91, 19, 14), oval(300, 106, 37, 35),
                         oval(530, 117, 45, 43), oval(730, 124, 38, 34)], ruled=True)
        hollow = bd.loft([oval(410, 128, 24, 19), oval(580, 131, 29, 24),
                          oval(740, 128, 30, 26)], ruled=True)
        parts.append(tagged(clock(outer-hollow, angle), f"intake_pod_{i}"))
        blade = fin(-235, 45, -220, -55, 191, 90, 10)
        parts.append(tagged(clock(blade, angle), f"sustainer_fin_{i}", TRIM))
    booster = revolved_envelope([(TAIL+110, 103), (-1450, 108), (-500, 108), (SEAM, 88)])
    # Deliberate dished face on the detached cartridge.
    booster -= revolved_envelope([(SEAM-12, 57), (SEAM+1, 67)])
    parts.append(tagged(booster, "booster_body"))
    parts.append(tagged(visual_nozzle(TAIL, 110, 103), "booster_nozzle", TRIM))
    for i, angle in enumerate(angles, 1):
        parts.append(tagged(clock(fin(-1550, -1080, -1495, -1310, 216, 101, 13), angle),
                            f"booster_fin_{i}", TRIM))
    mounting(parts)
    return bd.Compound(children=parts, label="Halberd_Pod_Three_Intakes")


def rounded_square(x, width, corner):
    return bd.RectangleRounded(width, width, corner).rotate(bd.Axis.Y, 90).translate((x, 0, 0))


def shoulder():
    angles = (45, 135, 225, 315)
    # Four-sided shoulders are the primary hull, not added intake pods.
    hull = bd.loft([disk(SEAM+70, 91), rounded_square(-170, 190, 34),
                    rounded_square(420, 198, 32), rounded_square(650, 192, 32),
                    disk(850, 86), disk(1080, 86)], ruled=True)
    for angle in angles:
        cavity = bd.loft([oval(350, 113, 17, 10), oval(535, 123, 23, 15),
                          oval(790, 114, 25, 20)], ruled=True)
        hull = hull - clock(cavity, angle)
    parts = [tagged(hull, "sustainer_body")]
    nose = bd.loft([disk(1080, 86), disk(1280, 80), disk(1475, 52),
                    disk(1625, 16), disk(NOSE, 0.8)], ruled=False)
    parts.append(tagged(nose, "radome", CERAMIC))
    parts.append(tagged(visual_nozzle(SEAM, 70, 91), "sustainer_nozzle", TRIM))
    for i, angle in enumerate(angles, 1):
        # Dark inset floors establish readable depth without painted fake holes.
        floor = bd.loft([oval(355, 112, 15, 3), oval(540, 108, 21, 3)], ruled=True)
        parts.append(tagged(clock(floor, angle), f"intake_floor_{i}", DARK))
        parts.append(tagged(clock(fin(-220, 40, -175, -35, 197, 99, 9), angle),
                            f"sustainer_fin_{i}", TRIM))
    booster = revolved_envelope([(TAIL+100, 97), (-1480, 103), (-490, 103), (SEAM, 91)])
    booster -= revolved_envelope([(SEAM-10, 60), (SEAM+1, 69)])
    parts.append(tagged(booster, "booster_body"))
    parts.append(tagged(visual_nozzle(TAIL, 100, 97), "booster_nozzle", TRIM))
    for i, angle in enumerate(angles, 1):
        parts.append(tagged(clock(fin(-1540, -1070, -1580, -1370, 211, 96, 11), angle),
                            f"booster_fin_{i}", TRIM))
    mounting(parts, wide=True)
    return bd.Compound(children=parts, label="Halberd_Shoulder_Four_Intakes")
