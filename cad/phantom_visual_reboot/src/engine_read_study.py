"""Rough engine-read concept studies (visual only) for the Phantom intake-to-exhaust passage.

Three contrasting variants of the approved 'option 4' idea (compressor face + core + turbine/nozzle).
Coordinates: mm, +X forward, +Y starboard, +Z dorsal. Parts live inside the R1 passage voids.
No airflow, thermal, or propulsion claim; the R1 body/liner are untouched (context only).
"""

from __future__ import annotations

import math
from pathlib import Path

from cadgen import build123d as bd, read_step, srgb, step

import aft_exhaust_r1 as aft

ROOT = Path(__file__).resolve().parents[1]

STUB_SECTIONS = ((-1030.0, 116.0, 49.0, -52.5, 5.0), (-953.3, 116.0, 49.0, -52.5, 5.0))
METAL = srgb("#9aa3ad")
DARK = srgb("#2b2f35")
HOT = srgb("#b8743a")
BLADE = srgb("#c9ced4")

# Passage centre line (X, centreY, centreZ, widthY, heightZ) from the R1 sections.
PATH = ((-1305.0, 76.0, 76.0, 0.0), (-1270.0, 80.0, 70.0, -10.0), (-1150.0, 100.0, 60.0, -35.0), (-1030.0, 116.0, 49.0, -52.5))


def lerp(a, b, t):
    return a + (b - a) * t


def duct_at(x):
    """Interpolated (widthY, heightZ, centerZ) of the connector passage at x (-1305..-1030)."""
    if x < -1305.0:  # straight 76 x 76 throat behind the connector
        return 76.0, 76.0, 0.0
    if x > -1030.0:  # original intake stub keeps the last connector section
        return 116.0, 49.0, -52.5
    for (x0, w0, h0, z0), (x1, w1, h1, z1) in zip(PATH, PATH[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            return lerp(w0, w1, t), lerp(h0, h1, t), lerp(z0, z1, t)
    raise ValueError(x)


def liner_half(x):
    """Half-width of the open inner liner at x (-1394..-1310), rounded-square interior."""
    pts = ((-1394.0, 58.0), (-1360.0, 51.0), (-1310.0, 38.0))
    for (x0, h0), (x1, h1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return lerp(h0, h1, (x - x0) / (x1 - x0))
    raise ValueError(x)


def label(shape, name, color):
    shape.label = name
    shape.color = color
    return shape


def cyl_x(x0, x1, r, y=0.0, z=0.0):
    c = bd.Cylinder(r, x1 - x0, rotation=(0, 90, 0))
    return c.translate(((x0 + x1) / 2.0, y, z))


def _cone(xa, xb, ra, rb, y, z):
    plane = bd.Plane(origin=(xa, y, z), z_dir=(1.0 if xb > xa else -1.0, 0.0, 0.0))
    return bd.Solid.make_cone(ra, max(rb, 0.01), abs(xb - xa), plane)


def rotor(x, r, hub_r, blades, thick, y=0.0, z=0.0, pitch=28.0, ring=True):
    """Bladed rotor disc facing +/-X: hub, blades, optional thin outer ring."""
    parts = [cyl_x(x - thick / 2, x + thick / 2, hub_r, y, z)]
    for i in range(blades):
        ang = 360.0 * i / blades
        blade = bd.Box(thick, r - hub_r + 0.6, 1.2)
        blade = blade.rotate(bd.Axis.Y, 0)  # radial along +Y initially
        blade = blade.rotate(bd.Axis.X, 0)
        blade = bd.Pos(0, (r + hub_r) / 2.0, 0) * blade
        # pitch about the radial (Y) axis, then spin about X
        blade = blade.rotate(bd.Axis(origin=(0, 0, 0), direction=(0, 1, 0)), pitch)
        blade = blade.rotate(bd.Axis.X, ang).translate((x, y, z))
        parts.append(blade)
    if ring:
        outer = cyl_x(x - thick / 2, x + thick / 2, r + 0.8, y, z)
        inner = cyl_x(x - thick / 2 - 1, x + thick / 2 + 1, r - 0.4, y, z)
        parts.append(outer - inner)
    solid = parts[0]
    for p in parts[1:]:
        solid = solid + p
    return solid.clean()


def strut_across(x, y0, z0, y1, z1, thick=2.5, depth=7.0, embed=1.5):
    """Flat strut from (y0,z0) to (y1,z1), depth along X; extended embed mm past each end."""
    dy, dz = y1 - y0, z1 - z0
    length = math.hypot(dy, dz) + 2 * embed
    ang = math.degrees(math.atan2(dz, dy))
    b = bd.Box(depth, length, thick)
    b = b.rotate(bd.Axis.X, ang)
    return b.translate((x, (y0 + y1) / 2.0, (z0 + z1) / 2.0))


def core_loft(records):
    return aft.ruled_loft(records)


def petals_round(x0, x1, r0, r1, count, thick=1.6, y=0.0, z=0.0, gap=2.0):
    """Converging round nozzle petals: radius r0 at x0 (aft, open end) to r1 at x1 (forward)."""
    parts = []
    span = abs(x1 - x0)
    ang = math.degrees(math.atan2(r0 - r1, span))
    rm = (r0 + r1) / 2.0
    width = 2 * math.pi * rm / count - gap
    length = math.hypot(span, r0 - r1)
    xm = (x0 + x1) / 2.0
    for i in range(count):
        p = bd.Box(length, width, thick)
        # local X is nozzle axis; tilt so the aft end is farther out
        p = p.rotate(bd.Axis.Y, ang if x0 < x1 else -ang)
        p = bd.Pos(xm, 0, rm) * p
        p = p.rotate(bd.Axis.X, 360.0 * i / count).translate((0, y, z))
        parts.append(p)
    return parts


# ---------------------------------------------------------------------------
# Option 1: triple fan bank, spindle core, turbine + tail cone + petal nozzle
# ---------------------------------------------------------------------------
def option1():
    parts = []
    # compressor face: three small rotors across the 116 x 49 throat + guide ring
    for k, yy in enumerate((-36.0, 0.0, 36.0)):
        parts.append(label(rotor(-985.0, 17.5, 4.5, 14, 6.0, y=yy, z=-52.5), f"o1_fan_{k}", BLADE))
    for k, yy in enumerate((-18.0, 18.0)):
        parts.append(label(bd.Box(3, 1.6, 44).translate((-996.0, yy, -52.5)), f"o1_fan_divider_{k}", METAL))
    # spindle core following the passage
    secs = []
    for x in (-1317.0, -1220.0, -1150.0, -1080.0, -1010.0):
        w, h, cz = duct_at(x)
        secs.append((x, 0.42 * w, 0.5 * h, cz, 0.45 * min(0.42 * w, 0.5 * h)))
    core = core_loft(secs)
    parts.append(label(core, "o1_core_spindle", METAL))
    for x in (-1250.0, -1120.0):
        w, h, cz = duct_at(x)
        for ang in (0, 90, 180, 270):
            dy = math.cos(math.radians(ang)); dz = math.sin(math.radians(ang))
            y0, z0 = dy * 0.21 * w * 0.9, cz + dz * 0.25 * h * 0.9
            y1, z1 = dy * (w / 2.0), cz + dz * (h / 2.0)
            parts.append(label(strut_across(x, y0, z0, y1, z1, 2.4, 6.0, 1.5), f"o1_strut_{int(-x)}_{ang}", DARK))
    # turbine, tail cone, nozzle
    parts.append(label(rotor(-1322.0, 34.0, 10.0, 26, 7.0, pitch=-25.0), "o1_turbine", HOT))
    parts.append(label(_cone(-1325.5, -1356.0, 10.0, 1.0, 0.0, 0.0), "o1_tail_cone", HOT))
    for i, p in enumerate(petals_round(-1391.0, -1352.0, 52.0, 44.0, 12)):
        parts.append(label(p, f"o1_nozzle_petal_{i}", METAL))
    return parts


# ---------------------------------------------------------------------------
# Option 2: guide-vane cascade + spinner, oval banded can, afterburner spray ring, flap nozzle
# ---------------------------------------------------------------------------
def option2():
    parts = []
    # inlet guide-vane grid across the throat + single fan and spinner
    for k in range(13):
        yy = -54.0 + k * 9.0
        parts.append(label(bd.Box(9.0, 0.9, 44.0).translate((-975.0, yy, -52.5)), f"o2_igv_{k:02d}", METAL))
    for k, zz in enumerate((-70.0, -35.0)):
        parts.append(label(bd.Box(9.0, 112.0, 1.2).translate((-975.0, 0.0, zz)), f"o2_igv_rib_{k}", METAL))
    parts.append(label(rotor(-990.0, 22.0, 8.0, 18, 6.0, z=-52.5), "o2_fan", BLADE))
    parts.append(label(_cone(-987.0, -970.0, 8.0, 1.5, 0.0, -52.5), "o2_spinner", METAL))
    # flattened oval can with raised bands
    secs = []
    for x in (-1317.0, -1220.0, -1150.0, -1080.0, -1015.0):
        w, h, cz = duct_at(x)
        secs.append((x, 0.62 * w, 0.62 * h, cz, 0.4 * min(0.62 * w, 0.62 * h)))
    parts.append(label(core_loft(secs), "o2_core_can", METAL))
    for k, x in enumerate((-1260.0, -1200.0, -1140.0, -1080.0)):
        w, h, cz = duct_at(x)
        outer = aft.ruled_loft(((x - 3, 0.62 * w + 6, 0.62 * h + 6, cz, 0.4 * min(0.62 * w, 0.62 * h)), (x + 3, 0.62 * w + 6, 0.62 * h + 6, cz, 0.4 * min(0.62 * w, 0.62 * h))))
        inner = aft.ruled_loft(((x - 4, 0.62 * w, 0.62 * h, cz, 0.4 * min(0.62 * w, 0.62 * h)), (x + 4, 0.62 * w, 0.62 * h, cz, 0.4 * min(0.62 * w, 0.62 * h))))
        parts.append(label((outer - inner).clean(), f"o2_can_band_{k}", DARK))
    for x in (-1235.0, -1110.0):
        w, h, cz = duct_at(x)
        for side, sgn in (("port", -1), ("stbd", 1)):
            parts.append(label(strut_across(x, sgn * 0.31 * w, cz, sgn * (w / 2.0 - 1.0), cz, 3.0, 10.0, 1.5), f"o2_pylon_{int(-x)}_{side}", DARK))
    # turbine + afterburner spray ring with spokes
    parts.append(label(rotor(-1322.0, 34.0, 11.0, 30, 7.0, pitch=-22.0), "o2_turbine", HOT))
    ring = cyl_x(-1348.0, -1343.0, 30.0) - cyl_x(-1349.0, -1342.0, 27.0)
    parts.append(label(ring, "o2_spray_ring", DARK))
    for i in range(6):
        sp = bd.Box(4.0, 27.0, 1.6)
        sp = bd.Pos(-1345.5, 15.0, 0.0) * sp
        parts.append(label(sp.rotate(bd.Axis.X, 60.0 * i), f"o2_spray_spoke_{i}", DARK))
    parts.append(label(cyl_x(-1352.0, -1336.0, 6.0), "o2_spray_hub", DARK))
    # four flat flap plates lining the square liner, sloped inward toward the throat
    x0, x1 = -1391.0, -1350.0
    for name, ang, off in (("top", 0.0, 0.0), ("bottom", 180.0, 0.0), ("port", 90.0, 0.0), ("stbd", 270.0, 0.0)):
        flap = bd.Box(math.hypot(x1 - x0, 9.0), 74.0, 1.8)
        flap = flap.rotate(bd.Axis.Y, math.degrees(math.atan2(9.0, x1 - x0)))
        flap = bd.Pos((x0 + x1) / 2.0, 0.0, 51.0) * flap
        parts.append(label(flap.rotate(bd.Axis.X, ang), f"o2_flap_{name}", METAL))
    return parts


# ---------------------------------------------------------------------------
# Option 3: twin engines matched to the slot-shaped throat: two fans, two cores, two nozzles
# ---------------------------------------------------------------------------
def option3():
    parts = []
    inlet_y = (-29.0, 29.0)
    exit_y = (-25.0, 25.0)
    for k, yy in enumerate(inlet_y):
        parts.append(label(rotor(-985.0, 22.0, 6.5, 16, 6.0, y=yy, z=-52.5), f"o3_fan_{k}", BLADE))
        parts.append(label(_cone(-982.0, -966.0, 6.5, 1.2, yy, -52.5), f"o3_spinner_{k}", METAL))
    parts.append(label(bd.Box(4.0, 2.2, 45.0).translate((-978.0, 0.0, -52.5)), "o3_center_divider", METAL))
    # twin cores blending from inlet spacing to exit spacing along the passage
    for k, (yi, ye) in enumerate(zip(inlet_y, exit_y)):
        secs = []
        for x in (-1317.0, -1220.0, -1150.0, -1080.0, -1010.0):
            w, h, cz = duct_at(x)
            t = (x + 1317.0) / 307.0
            yc = lerp(ye * 0.9, yi, t)
            secs.append((x, yc, 0.34 * h, 0.34 * h, cz))
        # build each core from circular sections
        loops = [bd.Wire.make_circle(0.5 * h_, bd.Plane(origin=(x_, yc_, cz_), z_dir=(1, 0, 0))) for x_, yc_, h_, _, cz_ in secs]
        core = bd.Solid.make_loft(loops, ruled=False)
        parts.append(label(core, f"o3_core_{k}", METAL))
    for x in (-1240.0, -1110.0):
        w, h, cz = duct_at(x)
        t = (x + 1300.0) / 270.0
        for k, yi, ye in ((0, inlet_y[0], exit_y[0]), (1, inlet_y[1], exit_y[1])):
            yc = lerp(ye * 0.9, yi, (x + 1317.0) / 307.0)
            wall = -1.0 if k == 0 else 1.0
            parts.append(label(strut_across(x, yc, cz, wall * (w / 2.0 - 1.0), cz, 2.4, 6.0, 1.5), f"o3_strut_{int(-x)}_{k}", DARK))
        parts.append(label(strut_across(x, 0.0, cz + 0.5 * h * 0.45, 0.0, cz + h / 2.0 - 1.0, 2.4, 6.0, 1.5), f"o3_strut_up_{int(-x)}", DARK))
    for k, ye in enumerate(exit_y):
        parts.append(label(rotor(-1322.0, 15.0, 5.0, 16, 6.0, y=ye * 0.9, pitch=-25.0), f"o3_turbine_{k}", HOT))
        parts.append(label(_cone(-1325.0, -1345.0, 5.0, 0.8, ye * 0.9, 0.0), f"o3_tail_cone_{k}", HOT))
        for i, p in enumerate(petals_round(-1391.0, -1358.0, 23.0, 19.0, 10, thick=1.4, y=ye)):
            parts.append(label(p, f"o3_nozzle_{k}_petal_{i}", METAL))
    parts.append(label(bd.Box(30.0, 1.6, 84.0).translate((-1376.0, 0.0, 0.0)), "o3_nozzle_divider", DARK))
    return parts


OPTIONS = {"O1_TripleFan": option1, "O2_VaneCascade": option2, "O3_TwinEngine": option3}


def insert(name):
    return bd.Compound(children=OPTIONS[name](), label=f"EngineRead_{name}_Insert")


def context_leaves():
    """Read the saved half-section review geometry as tracked input (context only)."""
    root = read_step(str(ROOT / "STEP" / "S_AftExhaust_R1_AftSection.step"))
    keep = ("RDM9_R7_symmetric_body", "aft_exhaust_r1_liner", "intake_r1_ramp", "tail_r4")
    out = []

    def visit(n):
        c = list(getattr(n, "children", ()) or ())
        if c:
            for k in c:
                visit(k)
        elif any(str(n.label).startswith(k) for k in keep):
            out.append(n)

    visit(root)
    return out


def composite(name):
    return bd.Compound(children=context_leaves() + OPTIONS[name](), label=f"S_EngineRead_{name}")


@step(out="../STEP/S_EngineRead_O1_TripleFan_Insert.step")
def o1_insert():
    return insert("O1_TripleFan")


@step(out="../STEP/S_EngineRead_O2_VaneCascade_Insert.step")
def o2_insert():
    return insert("O2_VaneCascade")


@step(out="../STEP/S_EngineRead_O3_TwinEngine_Insert.step")
def o3_insert():
    return insert("O3_TwinEngine")


@step(out="../STEP/S_EngineRead_O1_TripleFan_Context.step")
def o1_context():
    return composite("O1_TripleFan")


@step(out="../STEP/S_EngineRead_O2_VaneCascade_Context.step")
def o2_context():
    return composite("O2_VaneCascade")


@step(out="../STEP/S_EngineRead_O3_TwinEngine_Context.step")
def o3_context():
    return composite("O3_TwinEngine")


if __name__ == "__main__":
    for fn in (o1_insert, o2_insert, o3_insert, o1_context, o2_context, o3_context):
        fn()
