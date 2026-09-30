"""R19 full-body cosmetic surface detailing on the saved R18 access model.

Propagates the approved forward prototype (halberd_r19_surface_proto.py):
engraved hairline panels (rectangular and round, each with its own screw
pattern) on the four flat faces of the main body and booster, plus radial
screw rings with a circumferential seam at the nose joint, both sides of the
stage joint and the booster aft joint. See R19_SURFACE_DETAIL_DIRECTION.md.

Layout rules: panels sit on the flat cardinal faces (with irregular sideways
offsets so no centreline columns form), on the intake-housing flanks and ridge
tops, and on the booster faces. Stations are staggered per face so no
synchronized rows form across faces; fins, fairings, the intake inlet and
recesses, and existing R18 hatches keep >= 2 mm.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from cadgen import build123d as bd, srgb, step

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from surface_detail import checked_cut, clock_frame, skin_point  # noqa: E402

from halberd_r18_access_build import materials_for_labels  # noqa: E402
from halberd_r18_access_shapes import METAL, load_saved_parts  # noqa: E402
import halberd_r19_surface_proto as proto  # noqa: E402
from halberd_r19_intake_walls import even_intake_walls, precise_volume  # noqa: E402
from halberd_r17_interface_shapes import _slotted_head_local  # noqa: E402
from halberd_r18_access_shapes import load_manifest  # noqa: E402
from halberd_r18_access import ACCESS_LABELS  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
ACCESS_STEP = ROOT / "STEP" / "halberd_r18_access.step"
OUTPUT_METADATA = ROOT / "reviews" / "halberd_r19_surface.json"
MAIN_HOST = "main_body_intake_r12"
BOOSTER_HOST = "booster_body"
HARDWARE_GROUP = "r19_surface_hardware"
GROOVE_WIDTH = proto.GROOVE_WIDTH
GROOVE_DEPTH = proto.GROOVE_DEPTH
FEATURE_CLEARANCE = 2.0      # new detail to existing R18 detail / fins / fairings
RING_SPACING = 26.0          # target arc spacing of joint-ring screws (nose ring ~25)
RIDGE_RADIUS_LIMIT = 115.0   # skip ring screws on the diagonal intake ridges


def two_end(length):
    e = length / 2.0 - 7.0
    return ((-e, 0.0), (e, 0.0))


def four_corner(length, width):
    e, t = length / 2.0 - 7.0, width / 2.0 - 5.0
    return ((-e, -t), (-e, t), (e, -t), (e, t))


def bolt4_diag(diameter):
    r = (diameter / 2.0 - 3.5) * math.cos(math.radians(45.0))
    return ((-r, -r), (-r, r), (r, -r), (r, r))


def bolt3(diameter):
    r = diameter / 2.0 - 3.5
    return tuple((r * math.sin(math.radians(a)), r * math.cos(math.radians(a)))
                 for a in (0.0, 120.0, 240.0))


def plus4(diameter):
    r = diameter / 2.0 - 3.5
    return ((-r, 0.0), (r, 0.0), (0.0, -r), (0.0, r))


CENTRE = ((0.0, 0.0),)

def hinge_row(length, width, pitch=12.0):
    """Screws along one long edge only (a hinged-cover look)."""
    count = int((length - 10.0) // pitch) + 1
    span = (count - 1) * pitch
    edge = width / 2.0 - 3.5
    return tuple((-span / 2.0 + i * pitch, edge) for i in range(count))



# Composition (2026-09-29 user feedback: mid-section too dense, not varied):
# a moderately dense forward cluster (X 250..1085) and aft cluster
# (X -1085..-650), and a quiet mid-section (X -650..250) carrying only a few
# statement pieces: the raised F05 strip and its top-face mirror, one vent
# grille, one raised boss and two long ridge strips.
#
# Engraved rectangular: (id, clock, X, length, width, tangent offset, screws)
# Engraved round:       (id, clock, X, diameter, tangent offset, screws)
MAIN_RECT = (
    # +Z face (raised F05 mirror strip spans X -110..390 at tangent -22..-6)
    ("Z01", 0.0, 600.0, 90.0, 22.0, -22.0, four_corner(90.0, 22.0)),
    ("Z09", 0.0, -880.0, 70.0, 18.0, 22.0, two_end(70.0)),
    ("Z10", 0.0, -1030.0, 36.0, 14.0, -20.0, two_end(36.0)),
    # +Y face (F04A 350-530, F04B -855..-725)
    ("Y01", 90.0, 610.0, 50.0, 16.0, 22.0, two_end(50.0)),
    ("Y07", 90.0, -650.0, 56.0, 16.0, 24.0, hinge_row(56.0, 16.0)),
    ("Y09", 90.0, -1040.0, 44.0, 16.0, 18.0, two_end(44.0)),
    # -Z face (raised F05 strip X -110..390 at tangent 6..22)
    ("B02", 180.0, 455.0, 64.0, 18.0, -24.0, two_end(64.0)),
    ("B09", 180.0, -1030.0, 40.0, 14.0, -20.0, two_end(40.0)),
    # -Y face (F03A X=572-608)
    ("N01", 270.0, 650.0, 44.0, 16.0, 24.0, two_end(44.0)),
    ("N02", 270.0, 450.0, 100.0, 20.0, -18.0, hinge_row(100.0, 20.0)),
    ("N08", 270.0, -700.0, 50.0, 16.0, -26.0, two_end(50.0)),
)
MAIN_ROUND = (
    ("Y02", 90.0, 270.0, 20.0, -24.0, bolt3(20.0)),
    ("Y08", 90.0, -960.0, 16.0, -26.0, CENTRE),
    ("B01", 180.0, 560.0, 24.0, 22.0, plus4(24.0)),
    ("B08", 180.0, -930.0, 14.0, 28.0, CENTRE),
    ("N03", 270.0, 300.0, 18.0, 24.0, bolt3(18.0)),
    ("N09", 270.0, -830.0, 20.0, 24.0, plus4(20.0)),
)
# Intake housings on the diagonals. Each housing has a narrow flat top and
# two planar flanks whose normals sit 60 deg either side of the diagonal
# (clocks 15, 75, 105, 165, 195, 255, 285, 345). Flank panels are placed with
# the ray along the flank normal (clock = flank normal) at the flank's own
# sideways offset (+/-90..95 mm), so outlines and screws are undistorted.
# Clear of the forward inlet (X > 560), the recesses (X -445..-365) and fins.
HOUSING_RECT = (
    ("H01", 345.0, 380.0, 110.0, 22.0, 90.0, four_corner(110.0, 22.0)),
    ("H02", 345.0, -800.0, 60.0, 16.0, 93.0, two_end(60.0)),
    ("H08", 195.0, 300.0, 56.0, 18.0, -90.0, hinge_row(56.0, 18.0)),
    ("H10", 195.0, -760.0, 90.0, 18.0, -94.0, two_end(90.0)),
    ("H11", 165.0, 480.0, 80.0, 20.0, 90.0, two_end(80.0)),
    ("H16", 285.0, -740.0, 44.0, 14.0, -93.0, two_end(44.0)),
    ("H20", 15.0, 520.0, 40.0, 14.0, -90.0, two_end(40.0)),
    ("H22", 15.0, -660.0, 70.0, 18.0, -93.0, two_end(70.0)),
    # Long ridge-top strips on the diagonally opposite 45/225 ridges (mid
    # statement) plus one forward strip (clock = diagonal, top is narrow)
    ("T01", 45.0, 150.0, 140.0, 10.0, 0.0, two_end(140.0)),
    ("T05", 225.0, -50.0, 160.0, 10.0, 0.0, two_end(160.0)),
    ("T07", 315.0, 400.0, 90.0, 10.0, 0.0, two_end(90.0)),
)
HOUSING_ROUND = (
    ("H05", 105.0, -830.0, 16.0, -93.0, CENTRE),
    ("H19", 255.0, -720.0, 20.0, 93.0, plus4(20.0)),
    ("H24", 75.0, 450.0, 22.0, 90.0, plus4(22.0)),
    ("T02", 45.0, -690.0, 10.0, 0.0, CENTRE),
    ("T04", 135.0, 350.0, 12.0, 0.0, CENTRE),
    ("T06", 225.0, -770.0, 10.0, 0.0, CENTRE),
)
# Booster flat faces X=-1150..-1500 (F10 +Z -1498..-1402, F03B -Y -1402..-1378)
BOOSTER_RECT = (
    ("BZ1", 0.0, -1230.0, 60.0, 18.0, 20.0, two_end(60.0)),
    ("BN1", 270.0, -1220.0, 50.0, 16.0, -20.0, hinge_row(50.0, 16.0)),
    ("BN3", 270.0, -1455.0, 36.0, 14.0, -16.0, two_end(36.0)),
)
BOOSTER_ROUND = (
    ("BZ2", 0.0, -1330.0, 16.0, -22.0, CENTRE),
    ("BY1", 90.0, -1210.0, 24.0, -18.0, bolt4_diag(24.0)),
    ("BB2", 180.0, -1440.0, 14.0, 22.0, CENTRE),
    ("BN2", 270.0, -1300.0, 20.0, 18.0, bolt3(20.0)),
)

# New raised / vented families, all on planar skin (flat faces or flanks).
RAISED_HEIGHT = 1.5
RAISED_CHAMFER = 0.3
# Raised plate: (id, stage, clock, X, length, width, tangent, screws)
RAISED_PLATES = (
    ("RP1", "main", 0.0, -720.0, 100.0, 22.0, 16.0, four_corner(100.0, 22.0)),
    ("RP2", "main", 180.0, -780.0, 90.0, 20.0, -16.0, two_end(90.0)),
    # (A 110 mm plate on the 75-deg housing flank failed the planarity guard:
    # the flank follows the housing taper, so raised plates stay on flat faces.)
    ("RP3", "main", 270.0, -900.0, 70.0, 18.0, 18.0, two_end(70.0)),
    ("RP4", "booster", 180.0, -1300.0, 100.0, 20.0, -14.0, four_corner(100.0, 20.0)),
)
# Raised boss with a recessed centre: (id, stage, clock, X, diameter, tangent, screws)
BOSSES = (
    ("RB1", "main", 0.0, 470.0, 24.0, 14.0, bolt3(24.0)),
    ("RB2", "main", 270.0, -170.0, 22.0, -14.0, ()),
    # (RB3 on the 285-deg housing flank overlapped the skin by 0.10 mm3: the
    # flank curves slightly between planarity samples. Bosses stay on flat faces.)
    ("RB3", "main", 180.0, 320.0, 20.0, -18.0, ()),
)
# Vent grille: engraved outline + slots: (id, stage, clock, X, length, width,
# tangent, slot count, screws)
LOUVRES = (
    ("LV1", "main", 90.0, 150.0, 70.0, 22.0, 14.0, 5, two_end(70.0)),
    ("LV2", "main", 180.0, -880.0, 50.0, 18.0, -18.0, 4, two_end(50.0)),
    ("LV3", "main", 270.0, -1000.0, 60.0, 18.0, -18.0, 4, two_end(60.0)),
    ("LV4", "booster", 90.0, -1380.0, 70.0, 20.0, 14.0, 5, two_end(70.0)),
)
SLOT_WIDTH = 1.4
SLOT_DEPTH = 0.6
# F05 underside strip raised above the skin and mirrored to the top face.
F05_STRIP_HEIGHT = 2.0
F05_TERMINAL_HEIGHT = 2.5
F05_CHAMFER = 0.4
F05_REPLACED = ("main_r18_F05_terminal_left", "main_r18_F05_center_strip",
                "main_r18_F05_terminal_right", "main_r18_F05_fastener_1",
                "main_r18_F05_fastener_2")
RAISED_GROUP = "r19_surface_raised"

# Joint rings: (id, host, ring X, seam X or None, slab side: +1 = X >= seam)
RINGS = (
    ("RMA", MAIN_HOST, -1108.0, -1096.0, -1),
    ("RBF", BOOSTER_HOST, -1138.0, -1150.0, +1),
    ("RBA", BOOSTER_HOST, -1515.0, -1508.0, -1),
)


# ---------------------------------------------------------------------------
# Even distribution (2026-09-29 user direction): keep exactly the designs in
# the tables above (size, outline, screw pattern) but re-station them so the
# detail density is uniform along the body. Joint rings/seams, the raised F05
# pair and the R18 hatches stay fixed. The tables' own X/clock/tangent values
# are ignored; plan_layout() assigns them.
#
# Main body: N evenly spaced stations over MAIN_SPAN; booster likewise. Each
# station takes the next design of the category scheduled for it, on the next
# lane in a rotating sequence, skipping lanes blocked at that X. Categories
# are spread evenly over their allowed zones (Bresenham scheduling), so the
# mid-section cannot become denser just because it has more lanes.
MAIN_SPAN = (-1080.0, 1045.0)
BOOSTER_SPAN = (-1496.0, -1160.0)
FWD_START = 690.0             # round forward section: engraved designs only
PLANAR_END = 660.0            # flat faces end at the shoulder
HOUSING_ZONE = ((-820.0, -470.0), (-335.0, 540.0))  # flanks/ridges usable X
END_MARGIN = 4.0
FLANK_T = {15.0: -91.0, 75.0: 91.0, 105.0: -91.0, 165.0: 91.0,
           195.0: -91.0, 255.0: 91.0, 285.0: -91.0, 345.0: 91.0}
FLANK_ORDER = (15.0, 195.0, 105.0, 285.0, 75.0, 255.0, 165.0, 345.0)
RIDGE_ORDER = (45.0, 225.0, 135.0, 315.0)
FLAT_ORDER = (0.0, 180.0, 90.0, 270.0)
FWD_ORDER = (45.0, 180.0, 315.0, 90.0, 225.0, 0.0, 135.0, 270.0)
# Blocked X intervals per flat-face clock (hatches and the raised F05 pair).
FLAT_BLOCKED = {
    0.0: ((-115.0, 395.0), (820.0, 980.0)),      # F05 mirror strip; F02
    180.0: ((-115.0, 395.0),),                    # F05 strip
    90.0: ((345.0, 535.0), (-860.0, -720.0)),     # F04A; F04B
    270.0: ((567.0, 613.0),),                     # F03A
}
FWD_BLOCKED = {0.0: ((820.0, 980.0),)}           # F02
BOOSTER_BLOCKED = {0.0: ((-1502.0, -1398.0),), 270.0: ((-1406.0, -1374.0),)}


# Transverse panels (2026-09-29 user: one rectangular panel per cardinal face
# turned to run around the body, chosen where two similar panels sit next to
# each other). Candidates per face were the members of adjacent pairs with
# dissimilarity < 0.35 and gap < 300 mm in the even-distribution plan; +Z has
# no such pair, so both of its panels were candidates. random.Random(19)
# picked one per face. Each keeps its station; its old width becomes the
# axial length, its old length (capped to the 50 mm usable flat) the width
# around the body, with the two end screws moved to the circumferential ends.
TRANSVERSE_CAP = 50.0
TRANSVERSE = {"P03": 0.0, "P02": 90.0, "Z10": 180.0, "B02": 270.0}  # id: face clock


def _turned(item):
    pid, cat, kind, length, width, screws, slots = item
    across = min(length, TRANSVERSE_CAP)
    e = across / 2.0 - 7.0
    return (pid, cat, kind, width, across, ((0.0, -e), (0.0, e)), slots)


def _design_pool():
    """Every movable design: (id, category, kind, length, width, screws, slots)."""
    pool = []
    for r in proto.PANELS:
        pool.append((r[0], "flat", "rect", r[3], r[4], r[5], None))
    for r in proto.ROUND_PANELS:
        pool.append((r[0], "flat", "round", r[3], r[3], r[4], None))
    for r in MAIN_RECT:
        pool.append((r[0], "flat", "rect", r[3], r[4], r[6], None))
    for r in MAIN_ROUND:
        pool.append((r[0], "flat", "round", r[3], r[3], r[5], None))
    for r in HOUSING_RECT:
        cat = "ridge" if r[0].startswith("T") else "flank"
        pool.append((r[0], cat, "rect", r[3], r[4], r[6], None))
    for r in HOUSING_ROUND:
        cat = "ridge" if r[0].startswith("T") else "flank"
        pool.append((r[0], cat, "round", r[3], r[3], r[5], None))
    for r in BOOSTER_RECT:
        pool.append((r[0], "booster", "rect", r[3], r[4], r[6], None))
    for r in BOOSTER_ROUND:
        pool.append((r[0], "booster", "round", r[3], r[3], r[5], None))
    for r in RAISED_PLATES:
        pool.append((r[0], "planar" if r[1] == "main" else "booster", "plate",
                     r[4], r[5], r[7], None))
    for r in BOSSES:
        pool.append((r[0], "planar", "boss", r[4], r[4], r[6], None))
    for r in LOUVRES:
        pool.append((r[0], "planar" if r[1] == "main" else "booster", "louvre",
                     r[4], r[5], r[8], r[7]))
    # Planner order keeps each turned panel's original length so no other
    # design moves from its approved station.
    ORDER_LENGTH.update({p[0]: p[3] for p in pool if p[0] in TRANSVERSE})
    return [_turned(p) if p[0] in TRANSVERSE else p for p in pool]


ORDER_LENGTH = {}


def _interleave(items):
    """Alternate kinds (and sizes within a kind) so neighbours differ."""
    by_kind = {}
    for item in sorted(items, key=lambda i: (-ORDER_LENGTH.get(i[0], i[3]), i[0])):
        by_kind.setdefault(item[2], []).append(item)
    for kind, queue in by_kind.items():   # alternate large/small within a kind
        big, small = queue[:(len(queue) + 1) // 2], queue[(len(queue) + 1) // 2:][::-1]
        by_kind[kind] = [q for pair in zip(big, small + [None]) for q in pair if q]
    # Proportional merge: each kind is spread over the whole sequence rather
    # than alternating until the smaller kind runs out.
    keyed = []
    for kind, queue in sorted(by_kind.items()):
        for i, item in enumerate(queue):
            keyed.append(((i + 0.5) / len(queue), kind, item))
    return [item for _, _, item in sorted(keyed, key=lambda row: (row[0], row[1]))]


def _schedule(count, stations):
    """Pick `count` evenly spread entries of `stations` (Bresenham)."""
    if count > len(stations):
        raise ValueError(("more designs than stations in zone", count, len(stations)))
    return [stations[int((k + 0.5) * len(stations) / count)] for k in range(count)]


def _in_zone(x, half, zones):
    return any(a + half + END_MARGIN <= x <= b - half - END_MARGIN for a, b in zones)


def _free(x, half, blocked):
    return all(x + half + END_MARGIN <= a or x - half - END_MARGIN >= b for a, b in blocked)


def plan_layout():
    """Deterministic, evenly distributed placement of every movable design."""
    pool = _design_pool()
    cats = {c: _interleave([p for p in pool if p[1] == c])
            for c in ("flat", "flank", "ridge", "planar", "booster")}
    plan, occupied, sign = [], {}, {}

    def flat_t(lane, width, scale=1.0):
        sign[lane] = -sign.get(lane, -1.0)
        return scale * sign[lane] * max(0.0, min(18.0, 30.0 - width / 2.0 - 3.0))

    def fits(key, x, half, t, half_w):
        return all(not (x - half - END_MARGIN < x1 and x + half + END_MARGIN > x0 and
                        t - half_w - 2.0 < t1 and t + half_w + 2.0 > t0)
                   for x0, x1, t0, t1 in occupied.get(key, ()))

    def place(item, stage, x, lanes, tangent_for, blocked, zones=None):
        pid, cat, kind, length, width, screws, slots = item
        half = length / 2.0
        if pid in TRANSVERSE:   # a turned panel stays on its chosen face
            lanes = [lane for lane in lanes if lane == TRANSVERSE[pid]]
        if zones:   # clamp the station into the nearest zone the part fits
            spans = [(a + half + END_MARGIN, b - half - END_MARGIN) for a, b in zones
                     if b - a >= length + 2.0 * END_MARGIN]
            x = min((min(max(x, lo), hi) for lo, hi in spans), key=lambda c: abs(c - x))
        for shift in (0.0, 12.0, -12.0, 24.0, -24.0, 36.0, -36.0):
            xs = x + shift
            if zones and not _in_zone(xs, half, zones):
                continue
            for lane in lanes:
                if not _free(xs, half, blocked.get(lane, ())):
                    continue
                t = tangent_for(lane, width)
                if fits((stage, lane), xs, half, t, width / 2.0):
                    occupied.setdefault((stage, lane), []).append(
                        (xs - half, xs + half, t - width / 2.0, t + width / 2.0))
                    plan.append({"id": pid, "stage": stage, "kind": kind, "clock": lane,
                                 "x": xs, "tangent": t, "length": length, "width": width,
                                 "screws": screws, "slots": slots, "category": cat})
                    return lane
        raise ValueError((pid, "no free lane near station", x))

    def rotated(order, key):
        k = rot.get(key, 0) % len(order)
        return order[k:] + order[:k]

    rot = {}
    # Main body: one evenly spaced station per design.
    main_items = cats["flat"] + cats["flank"] + cats["ridge"] + cats["planar"]
    n = len(main_items)
    step = (MAIN_SPAN[1] - MAIN_SPAN[0]) / n
    stations = [MAIN_SPAN[0] + (k + 0.5) * step for k in range(n)]
    housing = [i for i, x in enumerate(stations) if _in_zone(x, 10.0, HOUSING_ZONE)]
    flank_ridge = cats["flank"] + cats["ridge"]
    hs = _schedule(len(flank_ridge), housing)
    ridge_slots = set(_schedule(len(cats["ridge"]), hs))
    flank_iter, ridge_iter = iter(cats["flank"]), iter(cats["ridge"])
    assign = {i: next(ridge_iter) if i in ridge_slots else next(flank_iter) for i in hs}
    rest = [i for i in range(n) if i not in assign]
    planar_ok = [i for i in rest if stations[i] <= PLANAR_END - 40.0]
    ps = _schedule(len(cats["planar"]), planar_ok)
    assign.update(zip(ps, cats["planar"]))
    fs = [i for i in rest if i not in ps]
    if len(fs) != len(cats["flat"]):
        raise ValueError(("station accounting", len(fs), len(cats["flat"])))
    assign.update(zip(fs, cats["flat"]))

    for i in range(n):
        item, x = assign[i], stations[i]
        cat = item[1]
        if cat == "flank":
            lane = place(item, "main", x, rotated(FLANK_ORDER, "flank"),
                         lambda l, w: FLANK_T[l], {}, HOUSING_ZONE)
            rot["flank"] = FLANK_ORDER.index(lane) + 1
        elif cat == "ridge":
            lane = place(item, "main", x, rotated(RIDGE_ORDER, "ridge"),
                         lambda l, w: 0.0, {}, HOUSING_ZONE)
            rot["ridge"] = RIDGE_ORDER.index(lane) + 1
        elif x >= FWD_START:
            lane = place(item, "main", x, rotated(FWD_ORDER, "fwd"),
                         lambda l, w: flat_t(("fwd", l), w, 0.5), FWD_BLOCKED,
                         ((FWD_START, MAIN_SPAN[1]),))
            rot["fwd"] = FWD_ORDER.index(lane) + 1
        else:
            lane = place(item, "main", x, rotated(FLAT_ORDER, "flat"), flat_t,
                         FLAT_BLOCKED, ((MAIN_SPAN[0], PLANAR_END),))
            rot["flat"] = FLAT_ORDER.index(lane) + 1

    # Booster: its own evenly spaced stations.
    items = cats["booster"]
    step = (BOOSTER_SPAN[1] - BOOSTER_SPAN[0]) / len(items)
    for j, item in enumerate(items):
        x = BOOSTER_SPAN[0] + (j + 0.5) * step
        lane = place(item, "booster", x, rotated(FLAT_ORDER, "booster"),
                     lambda l, w: flat_t(("booster", l), w), BOOSTER_BLOCKED,
                     (BOOSTER_SPAN,))
        rot["booster"] = FLAT_ORDER.index(lane) + 1
    if len(plan) != len(pool):
        raise ValueError(("plan lost designs", len(plan), len(pool)))
    return plan


def _local(host, x0, x1):
    return host & bd.Box(x1 - x0, 600.0, 600.0).translate(((x0 + x1) / 2.0, 0.0, 0.0))


def perimeter_clocks(host, x, spacing):
    """Clocks of evenly arc-spaced skin points around a cross-section."""
    samples, radii = [], []
    for degree in range(360):
        hit = skin_point(host, x, 0.0, float(degree))
        samples.append((float(degree), hit["point"]))
        radii.append(hit["measured_radius_mm"])
    lengths = [0.0]
    for index in range(1, 361):
        a, b = samples[index - 1][1], samples[index % 360][1]
        lengths.append(lengths[-1] + (b - a).length)
    perimeter = lengths[-1]
    count = max(4, int(round(perimeter / spacing / 4.0)) * 4)  # keep 4-fold symmetry
    clocks = []
    for k in range(count):
        target = perimeter * k / count
        i = next(j for j in range(1, 361) if lengths[j] >= target)
        f = (target - lengths[i - 1]) / (lengths[i] - lengths[i - 1])
        clocks.append((samples[i - 1][0] + f) % 360.0)
    return clocks, perimeter, min(radii), max(radii)


def _near(shape, others, clearance):
    box = shape.bounding_box()
    for other in others:
        ob = other.bounding_box()
        if (box.min.X - clearance > ob.max.X or ob.min.X - clearance > box.max.X or
                box.min.Y - clearance > ob.max.Y or ob.min.Y - clearance > box.max.Y or
                box.min.Z - clearance > ob.max.Z or ob.min.Z - clearance > box.max.Z):
            continue
        if shape.distance_to(other) < clearance:
            return other.label
    return None


def ring_hardware(host, ring_id, x, stage, obstacles):
    clocks, perimeter, r_min, r_max = perimeter_clocks(host, x, RING_SPACING)
    seats, heads, kept, skipped = [], [], [], []
    for clock in clocks:
        if skin_point(host, x, 0.0, clock)["measured_radius_mm"] > RIDGE_RADIUS_LIMIT:
            skipped.append((clock, "intake ridge"))
            continue
        tag = f"{ring_id}_{int(round(clock * 10)):04d}"
        s, h, _ = proto.slotted_hardware(host, tag, x, clock, ((0.0, 0.0),), stage,
                                         extended_seat=True)
        blocker = _near(h[0], obstacles, FEATURE_CLEARANCE)
        if blocker:
            skipped.append((clock, blocker))
            continue
        seats.extend(s)
        heads.extend(h)
        kept.append(clock)
    return seats, heads, {"x_mm": x, "perimeter_mm": perimeter,
                          "section_radius_mm": [r_min, r_max],
                          "kept_clocks": kept,
                          "skipped": [[c, why] for c, why in skipped]}


def cut_ring_with_seam(host, seats, seam_x, side, section_radius_max):
    """Cut ring seats on a local slab and rejoin at a designed seam groove.

    OCC can silently skip seat cuts on the long host; a local slab cuts
    reliably. The slab's split plane becomes one wall of a circumferential
    groove (skin band minus a copy scaled radially about X).
    """
    far = 800.0
    lo, hi = (seam_x, seam_x + far) if side > 0 else (seam_x - far, seam_x)
    box = bd.Box(hi - lo, 600.0, 600.0).translate(((lo + hi) / 2.0, 0.0, 0.0))
    slab, rest = host & box, host - box
    for seat in seats:
        slab = checked_cut(slab, seat)
    b0, b1 = (seam_x, seam_x + GROOVE_WIDTH) if side > 0 else (seam_x - GROOVE_WIDTH, seam_x)
    band = slab & bd.Box(b1 - b0, 600.0, 600.0).translate(((b0 + b1) / 2.0, 0.0, 0.0))
    scale = 1.0 - GROOVE_DEPTH / section_radius_max
    groove = band - band.scale((1.0, scale, scale), about=(0.0, 0.0, 0.0))
    slab = checked_cut(slab, groove)
    joined = (rest + slab).clean()
    if not joined.is_valid or len(joined.solids()) != 1:
        raise ValueError(("ring slab rejoin is invalid or split", seam_x))
    return joined, groove


def build_panels(host, table, round_table, stage, obstacles):
    cutters, heads, data = [], [], {}
    rows = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], None) for r in table]
    rows += [(r[0], r[1], r[2], r[3], r[3], r[4], r[5], "circle") for r in round_table]
    for pid, clock, x, length, width, tangent, screws, shape in rows:
        local = _local(host, x - length / 2.0 - 25.0, x + length / 2.0 + 25.0)
        outer = bd.Wire.make_circle(length / 2.0) if shape else None
        try:
            cut, h, d = proto.engraved_panel(local, pid, clock, x, length, width, screws,
                                             outer=outer, tangent_offset=tangent, stage=stage,
                                             extended_seat=True)
        except Exception as error:
            raise ValueError((pid, "panel construction failed", repr(error))) from error
        for part in (cut[0], *h):
            blocker = _near(part, obstacles, FEATURE_CLEARANCE)
            if blocker:
                raise ValueError((pid, "panel within clearance of existing detail", blocker))
        d["outline"] = shape or "chamfered_rectangle"
        cutters.extend(cut)
        heads.extend(h)
        data[pid] = d
    return cutters, heads, data


def planar_frame(host, clock, x, tangent, half_length, half_width, name, round_=False):
    """Plane on flat native skin; raises unless the footprint is planar.

    Samples the footprint outline (a circle for round parts) and centre.
    """
    centre = skin_point(host, x, tangent, clock)
    origin, normal = centre["point"], centre["normal"]
    if round_:
        samples = [(half_length * math.cos(math.radians(a)),
                    half_width * math.sin(math.radians(a))) for a in range(0, 360, 30)]
    else:
        samples = [(dx, dt) for dx in (-half_length, 0.0, half_length)
                   for dt in (-half_width, 0.0, half_width)]
    for dx, dt in samples:
        if True:
            hit = skin_point(host, x + dx, tangent + dt, clock)
            if hit["normal"].dot(normal) < 0.99999 or                     abs((hit["point"] - origin).dot(normal)) > 0.005:
                raise ValueError((name, "raised detail footprint is not planar skin", dx, dt))
    axis = bd.Vector(1.0, 0.0, 0.0)
    x_dir = (axis - normal * normal.dot(axis)).normalized()
    return bd.Plane(origin=origin, x_dir=x_dir, z_dir=normal)


CHAMFERS_USED = {}


def raised_local(face, z0, z1, chamfer, name=None):
    """Local prism z0..z1 with its top edges chamfered.

    Acute corners (e.g. the F05 angled split lines) can defeat a chamfer, so
    it steps down to half size and then none; the size used is recorded.
    """
    solid = bd.Solid.extrude(face.moved(bd.Location((0.0, 0.0, z0))),
                             bd.Vector(0.0, 0.0, z1 - z0))
    used = 0.0
    for size in (chamfer, chamfer / 2.0):
        if not size:
            break
        top = [e for e in solid.edges() if abs(e.center().Z - z1) < 1e-6]
        try:
            candidate = bd.chamfer(top, size).solids()[0]
        except ValueError:
            continue
        if candidate.is_valid:
            solid, used = candidate, size
            break
    if name:
        CHAMFERS_USED[name] = used
    return solid


def heads_on_top(part, plane, height, screws, label_prefix):
    """R17 heads seated into the top of a raised part (seats cut from it)."""
    head_local, _ = _slotted_head_local()
    seat_local = proto.seat_tool_extended()
    heads = []
    for index, (dx, dt) in enumerate(screws, 1):
        location = plane.location * bd.Location((dx, dt, height))
        part = checked_cut(part, seat_local.moved(location))
        head = head_local.moved(location)
        head.label = f"{label_prefix}_fastener_{index}"
        heads.append(head)
    return part, heads


def raised_plate(host, pid, stage, clock, x, length, width, tangent, screws):
    plane = planar_frame(host, clock, x, tangent, length / 2.0, width / 2.0, pid)
    local = raised_local(bd.Face(proto._panel_wire(length, width)), 0.0,
                         RAISED_HEIGHT, RAISED_CHAMFER, pid)
    part, heads = heads_on_top(local.moved(plane.location), plane, RAISED_HEIGHT,
                               screws, f"{stage}_r19_{pid}")
    part.label = f"{stage}_r19_{pid}_plate"
    return part, heads, {"kind": "raised_plate", "clock_degrees": clock, "center_x_mm": x,
                         "tangent_offset_mm": tangent, "length_mm": length,
                         "width_mm": width, "height_mm": RAISED_HEIGHT}


def raised_boss(host, pid, stage, clock, x, diameter, tangent, screws):
    plane = planar_frame(host, clock, x, tangent, diameter / 2.0, diameter / 2.0, pid,
                         round_=True)
    local = raised_local(bd.Face(bd.Wire.make_circle(diameter / 2.0)), 0.0,
                         RAISED_HEIGHT, 0.4, pid)
    recess = bd.Solid.extrude(
        bd.Face(bd.Wire.make_circle(diameter * 0.22)).moved(
            bd.Location((0.0, 0.0, RAISED_HEIGHT - 0.6))), bd.Vector(0.0, 0.0, 1.0))
    local = checked_cut(local, recess)
    part, heads = heads_on_top(local.moved(plane.location), plane, RAISED_HEIGHT,
                               screws, f"{stage}_r19_{pid}")
    part.label = f"{stage}_r19_{pid}_boss"
    return part, heads, {"kind": "raised_boss", "clock_degrees": clock, "center_x_mm": x,
                         "tangent_offset_mm": tangent, "diameter_mm": diameter,
                         "height_mm": RAISED_HEIGHT, "recess_diameter_mm": diameter * 0.44}


def louvre_slots(host, pid, clock, x, length, width, tangent, count):
    """Engraved vent slots inside a louvre panel (planar skin only)."""
    plane = planar_frame(host, clock, x, tangent, length / 2.0, width / 2.0, pid)
    span = length - 26.0
    cutters, centres = [], []
    for i in range(count):
        dx = -span / 2.0 + span * i / (count - 1)
        slot = bd.SlotOverall(width - 7.0, SLOT_WIDTH, rotation=90).faces()[0]
        tool = bd.Solid.extrude(slot.moved(bd.Location((dx, 0.0, -SLOT_DEPTH))),
                                bd.Vector(0.0, 0.0, SLOT_DEPTH + 1.0))
        tool = tool.moved(plane.location)
        tool.label = f"{pid}_slot_{i + 1}"
        cutters.append(tool)
        centres.append(dx)
    return cutters, centres


def raised_f05(host, manifest_feature):
    """Replace the flush F05 strip with raised pieces and mirror them to +Z.

    The R18 pocket (0.8 mm) stays; the raised pieces fill it and stand
    F05_STRIP_HEIGHT (strip) / F05_TERMINAL_HEIGHT (end pieces) above the skin.
    """
    from halberd_r18_access_build import _f05_cover_sections

    f = manifest_feature
    floor = skin_point(host, f["x"], f["tangent"], f["clock"])
    outside = skin_point(host, f["x"], f["tangent"] - 12.0, f["clock"])
    depth = (outside["point"] - floor["point"]).dot(floor["normal"])
    if abs(depth - 0.8) > 0.01:
        raise ValueError(("F05 pocket depth not 0.8 mm", depth))
    origin = floor["point"] + floor["normal"] * depth
    normal = floor["normal"]
    plane = bd.Plane(origin=origin, x_dir=(1.0, 0.0, 0.0), z_dir=normal)
    parts, heads = [], []
    screws = [tuple(s) for s in f["screws"]]
    for key, face in _f05_cover_sections(f):
        height = F05_TERMINAL_HEIGHT if key.startswith("terminal") else F05_STRIP_HEIGHT
        part = raised_local(face, -depth, height, F05_CHAMFER,
                            f"F05_{key}").moved(plane.location)
        box = face.bounding_box()
        inside = [sc for sc in screws
                  if box.min.X + 2.0 < sc[0] < box.max.X - 2.0 and
                  box.min.Y + 2.0 < sc[1] < box.max.Y - 2.0]
        if inside:
            part, h = heads_on_top(part, plane, height, inside, f"main_r19_F05_{key}")
            heads.extend(h)
        part.label = f"main_r19_F05_{key}_raised"
        parts.append(part)
    if len(heads) != len(screws):
        raise ValueError(("F05 screws not all placed on a raised piece", len(heads), len(screws)))
    pocket = bd.Solid.extrude(
        bd.Face(bd.Wire.make_polygon([(a, b, 0.0) for a, b in f["outline"]], close=True))
        .moved(bd.Location((0.0, 0.0, -depth))), bd.Vector(0.0, 0.0, depth + 3.0))
    mirror_pocket = pocket.moved(plane.location).mirror(bd.Plane.XY)
    mirror_pocket.label = "main_r19_F05M_pocket"
    mirrored = []
    for part in (*parts, *heads):
        copy = part.mirror(bd.Plane.XY)
        copy.label = part.label.replace("main_r19_F05_", "main_r19_F05M_")
        mirrored.append(copy)
    return parts, heads, mirror_pocket, mirrored, {
        "pocket_depth_mm": depth, "strip_height_mm": F05_STRIP_HEIGHT,
        "terminal_height_mm": F05_TERMINAL_HEIGHT, "mirror_plane": "XY"}


def build_r19_surface():
    scene, saved = load_saved_parts(ACCESS_STEP)
    main, booster = saved[MAIN_HOST], saved[BOOSTER_HOST]
    others = [p for label, p in saved.items() if label not in (MAIN_HOST, BOOSTER_HOST)]
    main_details = [p for p in others if not p.label.startswith("booster")]
    booster_details = [p for p in others if p.label.startswith("booster")]
    meta = {"source_step": "STEP/halberd_r18_access.step",
            "source_document_hash": scene.document_hash,
            "rings": {}, "panels": {}, "seams": {}}
    new_heads = []
    before = {MAIN_HOST: main.volume, BOOSTER_HOST: booster.volume}

    # 0. Even inlet side walls (2026-09-29 user): re-cut the four inlet
    # channels before any other Boolean on the main host.
    original = main
    main, meta["intake_walls"] = even_intake_walls(main)
    gain, loss = main - original, original - main
    meta["intake_walls"]["host_gain_mm3"] = precise_volume(gain) if gain else 0.0
    meta["intake_walls"]["host_loss_mm3"] = precise_volume(loss) if loss else 0.0

    # 1. Joint rings first: slab rejoins must precede panel Booleans on a host.
    nose_seats, nose_heads = proto._ring_fasteners(saved["main_joint_fastener_1"])
    nose_rmax = max(skin_point(main, proto.RING_SLAB_X + 0.2, 0.0, float(d))["measured_radius_mm"]
                    for d in range(0, 360, 5))
    main, nose_groove = cut_ring_with_seam(main, nose_seats, proto.RING_SLAB_X, +1, nose_rmax)
    new_heads.extend(nose_heads)
    meta["rings"]["nose"] = {"x_mm": 1078.0, "heads": 24, "r16_kept": 4}
    meta["seams"]["nose"] = {"x_mm": [proto.RING_SLAB_X, proto.RING_SLAB_X + GROOVE_WIDTH],
                             "volume_mm3": nose_groove.volume, "radius_max_mm": nose_rmax}

    for ring_id, host_label, x, seam_x, side in RINGS:
        stage = "main" if host_label == MAIN_HOST else "booster"
        host = main if stage == "main" else booster
        obstacles = main_details if stage == "main" else booster_details
        seats, heads, info = ring_hardware(host, ring_id, x, stage, obstacles)
        if seam_x is None:
            for seat in seats:
                host = checked_cut(host, seat)
        else:
            rmax = max(skin_point(host, seam_x + side * GROOVE_WIDTH / 2.0, 0.0,
                                  float(d))["measured_radius_mm"] for d in range(0, 360, 2))
            host, groove = cut_ring_with_seam(host, seats, seam_x, side, rmax)
            meta["seams"][ring_id] = {
                "x_mm": sorted([seam_x, seam_x + side * GROOVE_WIDTH]),
                "volume_mm3": groove.volume, "radius_max_mm": rmax,
                "depth_range_mm": [GROOVE_DEPTH * info["section_radius_mm"][0] / rmax,
                                   GROOVE_DEPTH]}
        info["heads"] = len(heads)
        meta["rings"][ring_id] = info
        new_heads.extend(heads)
        if stage == "main":
            main = host
        else:
            booster = host

    # 2. F05: raise the underside strip and mirror it to the top face. The
    # flush R18 F05 pieces and their two heads are replaced.
    f05 = next(i for i in load_manifest()["individual_access_features"] if i["id"] == "F05")
    f05_parts, f05_heads, mirror_pocket, f05_mirror, meta["f05"] = raised_f05(main, f05)
    kept_details = [p for p in main_details if p.label not in F05_REPLACED]
    for part in f05_mirror:
        blocker = _near(part, kept_details, FEATURE_CLEARANCE)
        if blocker:
            raise ValueError((part.label, "mirrored F05 within clearance of", blocker))
    main = checked_cut(main, mirror_pocket)
    raised_parts = [*f05_parts, *(p for p in f05_mirror if "_fastener_" not in p.label)]
    new_heads.extend(f05_heads)
    new_heads.extend(p for p in f05_mirror if "_fastener_" in p.label)
    main_details = kept_details + list(raised_parts)

    # 3. Every movable design at its evenly distributed station (plan_layout).
    plan = plan_layout()
    meta["plan"] = [{k: v for k, v in p.items() if k != "screws"} for p in plan]
    for stage, obstacles in (("main", main_details), ("booster", booster_details)):
        host = main if stage == "main" else booster
        mine = [p for p in plan if p["stage"] == stage]
        rect = tuple((p["id"], p["clock"], p["x"], p["length"], p["width"], p["tangent"],
                      p["screws"]) for p in mine if p["kind"] == "rect")
        rnd = tuple((p["id"], p["clock"], p["x"], p["length"], p["tangent"], p["screws"])
                    for p in mine if p["kind"] == "round")
        cutters, heads, data = build_panels(host, rect, rnd, stage, obstacles)
        for cutter in cutters:
            host = checked_cut(host, cutter)
        if not host.is_valid or len(host.solids()) != 1:
            raise ValueError((stage, "panel cuts invalidated the host"))
        for head in heads:
            if host.is_inside(head.center()):
                raise ValueError((head.label, "fastener centre lies inside the host skin"))
        meta["panels"].update({pid: dict(d, stage=stage) for pid, d in data.items()})
        new_heads.extend(heads)
        if stage == "main":
            main = host
        else:
            booster = host

    # 4. Raised plates and bosses (added parts on planar skin) and vent
    # grilles (engraved outline + slots cut into the host), at planned stations.
    placed = list(raised_parts)
    meta["raised"], meta["louvres"] = {}, {}

    def _check_clear(shape, stage, name):
        pool = (main_details if stage == "main" else booster_details) + placed
        blocker = _near(shape, [p for p in pool if p is not shape], FEATURE_CLEARANCE)
        if blocker:
            raise ValueError((name, "within clearance of", blocker))

    for p in plan:
        pid, stage, clock, x, t = p["id"], p["stage"], p["clock"], p["x"], p["tangent"]
        host = main if stage == "main" else booster
        if p["kind"] == "plate":
            part, heads, d = raised_plate(host, pid, stage, clock, x, p["length"],
                                          p["width"], t, p["screws"])
        elif p["kind"] == "boss":
            part, heads, d = raised_boss(host, pid, stage, clock, x, p["length"], t,
                                         p["screws"])
        else:
            continue
        _check_clear(part, stage, pid)
        placed.append(part)
        raised_parts.append(part)
        new_heads.extend(heads)
        meta["raised"][pid] = dict(d, stage=stage)
    for p in plan:
        if p["kind"] != "louvre":
            continue
        pid, stage, clock, x, t = p["id"], p["stage"], p["clock"], p["x"], p["tangent"]
        length, width, count = p["length"], p["width"], p["slots"]
        host = main if stage == "main" else booster
        local = _local(host, x - length / 2.0 - 25.0, x + length / 2.0 + 25.0)
        cut, heads, d = proto.engraved_panel(local, pid, clock, x, length, width, p["screws"],
                                             tangent_offset=t, stage=stage,
                                             extended_seat=True)
        slots, centres = louvre_slots(host, pid, clock, x, length, width, t, count)
        _check_clear(cut[0], stage, pid)
        for cutter in (*cut, *slots):
            host = checked_cut(host, cutter)
        for head in heads:
            if host.is_inside(head.center()):
                raise ValueError((head.label, "fastener centre lies inside the host skin"))
        new_heads.extend(heads)
        placed.append(cut[0])
        d["outline"] = "chamfered_rectangle"
        meta["panels"][pid] = dict(d, stage=stage)
        meta["louvres"][pid] = {"stage": stage, "clock_degrees": clock, "center_x_mm": x,
                                "tangent_offset_mm": t, "slot_x_offsets_mm": centres,
                                "slot_width_mm": SLOT_WIDTH, "slot_depth_mm": SLOT_DEPTH,
                                "slot_length_mm": width - 7.0}
        if stage == "main":
            main = host
        else:
            booster = host

    for label, host in ((MAIN_HOST, main), (BOOSTER_HOST, booster)):
        host.label, host.color = label, saved[label].color
    for head in new_heads:
        head.color = srgb(METAL)
    labels = [h.label for h in new_heads]
    if len(labels) != len(set(labels)):
        raise ValueError("duplicate R19 hardware labels")
    for part in raised_parts:
        part.color = saved[MAIN_HOST].color
        if not part.is_valid or len(part.solids()) != 1:
            raise ValueError((part.label, "raised part invalid or not one solid"))
    raised_labels = [p.label for p in raised_parts]
    if len(set(labels + raised_labels)) != len(labels) + len(raised_labels):
        raise ValueError("duplicate R19 raised/hardware labels")
    hardware = bd.Compound(children=new_heads, label=HARDWARE_GROUP)
    raised = bd.Compound(children=raised_parts, label=RAISED_GROUP)
    parts = [main if l == MAIN_HOST else booster if l == BOOSTER_HOST else p
             for l, p in saved.items() if l not in F05_REPLACED]
    meta.update({
        "host_volume_removed_mm3": {MAIN_HOST: before[MAIN_HOST] - main.volume,
                                    BOOSTER_HOST: before[BOOSTER_HOST] - booster.volume},
        "hardware_labels": labels,
        "raised_labels": raised_labels,
        "top_chamfer_used_mm": dict(CHAMFERS_USED),
        "replaced_r18_labels": list(F05_REPLACED),
        "panel_count": len(meta["panels"]),
        "ring_head_count": sum(r["heads"] for r in meta["rings"].values()),
    })
    OUTPUT_METADATA.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return bd.Compound(children=[*parts, hardware, raised], label="Halberd_R19_Surface")


def _materials():
    kept = [label for label in ACCESS_LABELS if label not in F05_REPLACED]
    materials = materials_for_labels(kept, include_all_base=True)
    materials["assignments"].append({"targets": [f"#{HARDWARE_GROUP}"],
                                     "material": "detail_metal"})
    materials["assignments"].append({"targets": [f"#{RAISED_GROUP}"],
                                     "material": "detail_paint"})
    return materials


MATERIALS = _materials()


@step(out="../STEP/halberd_r19_surface.step", materials=MATERIALS)
def halberd_r19_surface():
    return build_r19_surface()


if __name__ == "__main__":
    halberd_r19_surface()
