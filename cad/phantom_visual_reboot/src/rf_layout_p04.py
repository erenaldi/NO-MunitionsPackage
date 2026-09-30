"""P04 study: NON-CUTTING annotated flush-RF layout on the B2H Stowed baseline (design frame, mm; +X fwd, +Y stbd, +Z up).

Adds thin colored proud patches to a copy of the B2H stowed leaves: teal = recommended RF zone, amber = optional RF zone,
red = keep-out (pylon strip, folded fins, ramp/door, wing slots).  Nothing is subtracted or edited; baseline STEPs untouched.
Output: STEP/S_RF_Layout_P04_Study.step.  Fictional game-art layout only; no functional/RF-performance claim.
"""
from pathlib import Path

from cadgen import build123d as bd, read_step, step

ROOT = Path(__file__).resolve().parents[1]
T = 0.6  # proud thickness of study patches
TEAL, AMBER, RED = bd.Color(0.0, 0.75, 0.7), bd.Color(1.0, 0.7, 0.0), bd.Color(0.9, 0.1, 0.1)

# Zone tables: (label, x0, x1, u0, u1) with u = Y for top/belly faces, Z for flank faces
RF_FLANK = ("B_flank_pair", -650.0, -350.0, -28.0, 28.0)
RF_BELLY = ("C_belly_pair", 130.0, 420.0, 22.0, 62.0)          # each side, |Y| in [22, 62]
RF_DORSAL = ("D_dorsal_aft_optional", -1030.0, -830.0, -40.0, 40.0)
NOSE_CHEEK = ("A_nose_cheek", 815.0, 960.0, -12.0, 30.0)      # X range, Z range (Y follows the faceted nose flank)


def leaves(node):
    kids = list(getattr(node, "children", ()) or ())
    return [l for k in kids for l in leaves(k)] if kids else [node]


def box(x0, x1, y0, y1, z0, z1):
    return bd.Box(x1 - x0, y1 - y0, z1 - z0).moved(bd.Location(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)))


def top(x0, x1, y0, y1):
    return box(x0, x1, y0, y1, 86.0, 86.0 + T)


def belly(x0, x1, y0, y1):
    return box(x0, x1, y0, y1, -86.0 - T, -86.0)


def flank(x0, x1, z0, z1, side):
    return box(x0, x1, 86.0, 86.0 + T, z0, z1) if side > 0 else box(x0, x1, -86.0 - T, -86.0, z0, z1)


def paint(shape, label, color):
    shape.label, shape.color = label, color
    return shape


def nose_cheek(body, side):
    """Skin patch on the faceted nose flank: body shifted outward by T, cut to an X/Z window, minus the body."""
    x0, x1, z0, z1 = NOSE_CHEEK[1:]
    win = box(x0, x1, 0.0 if side > 0 else -120.0, 120.0 if side > 0 else 0.0, z0, z1)
    shifted = body.moved(bd.Location((0, side * T, 0)))
    return (win & shifted) - body


def build():
    out, body = [], None
    for p in leaves(read_step(str(ROOT / "STEP" / "S_EngineBay_B2H_Stowed_Full.step"))):
        q = p.translate((0.0, 0.0, 0.0))
        q.label, q.color = p.label, p.color
        out.append(q)
        if "symmetric_body" in str(p.label):
            body = p
    ov = []
    # --- recommended RF (teal)
    for s, n in ((1, "stbd"), (-1, "port")):
        ov.append(paint(nose_cheek(body, s), f"RF_A_nose_cheek_{n}", TEAL))
        ov.append(paint(flank(*RF_FLANK[1:], s), f"RF_B_flank_{n}", TEAL))
        ov.append(paint(belly(RF_BELLY[1], RF_BELLY[2], s * RF_BELLY[3], s * RF_BELLY[4]) if s > 0 else
                        belly(RF_BELLY[1], RF_BELLY[2], -RF_BELLY[4], -RF_BELLY[3]), f"RF_C_belly_{n}", TEAL))
    # --- optional (amber)
    ov.append(paint(top(*RF_DORSAL[1:3], *RF_DORSAL[3:]), "RF_D_dorsal_aft_optional", AMBER))
    # --- keep-outs (red)
    ov.append(paint(top(-770.0, 686.0, -67.0, 67.0), "KEEP_pylon_strip_top", RED))
    for n, x0, x1 in (("aft_fins", -1335.0, -1075.0),):
        ov.append(paint(top(x0, x1, -86.0, 86.0), f"KEEP_{n}_top", RED))
        ov.append(paint(belly(x0, x1, -86.0, 86.0), f"KEEP_{n}_belly", RED))
        for s in (1, -1):
            ov.append(paint(flank(x0, x1, -86.0, 86.0, s), f"KEEP_{n}_flank{s}", RED))
    ov.append(paint(belly(-953.0, 53.0, -64.0, 64.0), "KEEP_ramp_door_belly", RED))
    for s in (1, -1):
        ov.append(paint(flank(-455.0, 555.0, 62.0, 86.0, s), f"KEEP_wing_slot_flank{s}", RED))
    return out + ov


@step(out="../STEP/S_RF_Layout_P04_Study.step")
def rf_layout():
    return bd.Compound(children=build(), label="S_RF_Layout_P04_Study_NONCUTTING")


if __name__ == "__main__":
    rf_layout()
