"""R24 F11 rollout: the user-accepted R24p folded lip seats (booster_fin_fairing_1, clock 45)
repeated on booster_fin_fairing_2/3/4 (clocks 135, 225, 315), two seats per fin.

Cosmetic game-asset detailing only, built on the saved R24p model (read-only; fin 1 and
its seats are kept as saved).

Reuse: the seat recipe is the R24p module itself (Lip, outline_uw, build_seat and its
constants); nothing is copied. build_seat reads the module globals FIN and CLOCK, so they
are set per fin before each call, and the R24p "booster_r24p_F11_1" labels are renamed
to "booster_r24_F11_<n>". Each fin's ledge, lip and flank are measured by the same normal
rays (Lip raises if the ledge, straight lip or flank face is not found as on fin 1).
Each fin leaf is a separate 12-face host, so it is cut directly; every cut proves
removed volume > 0.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from cadgen import read_scene, step
from cadgen import build123d as bd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from surface_detail import checked_cut  # noqa: E402
from root_geometry import local_crop_box  # noqa: E402
from check_kit import Stages, min_distance, precise_volume  # noqa: E402

import halberd_r20_fin_seats as r20  # noqa: E402
import halberd_r24p_flank_lip_seats as r24p  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SAVED = ROOT / "STEP" / "r24p_flank_seats.step"
OUTPUT_METADATA = ROOT / "reviews" / "halberd_r24_booster_seats.json"
STAGE_LOG = Path(r"C:\Users\erena\AppData\Local\Temp\claude\C--Users-erena-Desktop-Nuclear-Option-Munitions-Package--claude-worktrees-pensive-edison-684f85\df37c5b2-f2ee-434a-923d-6e40752e7dc5\scratchpad\r24_build_stages.log")
FINS = ((2, "booster_fin_fairing_2", 135.0), (3, "booster_fin_fairing_3", 225.0),
        (4, "booster_fin_fairing_4", 315.0))
OLD_PREFIX = "booster_r24p_F11_1"
HARDWARE_GROUP = r24p.HARDWARE_GROUP
OLD_COVER_GROUP = r24p.COVER_GROUP
COVER_GROUP = "r24_lip_seat_covers"


def _relabel(shape, n):
    shape.label = shape.label.replace(OLD_PREFIX, f"booster_r24_F11_{n}")
    return shape


def fin_seats(saved, n, fin, clock, st):
    """Two R24p seats on one fin leaf; returns (new fin leaf, covers, heads, metadata)."""
    r24p.FIN, r24p.CLOCK = fin, clock
    r24p.CALLS["skin_point"] = 0
    fin0 = saved[fin]
    fc = fin0 & local_crop_box(clock, r24p.CROP_X, r24p.CROP_T, r24p.CROP_R)
    built = [r24p.build_seat(fc, key, s) for key, s in r24p.SIDES]
    calls = r24p.CALLS["skin_point"]
    for b in built:
        for part in (b["pocket"], b["cover"], *b["seats"], *b["heads"]):
            _relabel(part, n)
        m = b["meta"]
        m["cover_label"] = b["cover"].label
        m["head_labels"] = [h.label for h in b["heads"]]
    st.stage(f"fin{n}_clearance")

    new_parts = [p for b in built for p in (b["pocket"], b["cover"], *b["heads"])]
    skin = [f for b in built for f in b["skin_faces"]]
    fin_other = [f for f in fc.faces() if not any(f.is_same(g) for g in skin)]
    gap_fin = min_distance(new_parts, fin_other)
    gap_detail = min_distance(new_parts, [p for l, p in saved.items() if l != fin])
    gap_seats = min_distance([built[0]["pocket"]], [built[1]["pocket"]])
    if min(gap_fin, gap_detail, gap_seats) < r24p.FEATURE_CLEARANCE:
        raise ValueError((fin, "seat within clearance", gap_fin, gap_detail, gap_seats))
    st.stage(f"fin{n}_cut")

    fin1, removed = fin0, {}
    for cutter in [c for b in built for c in (b["pocket"], *b["seats"])]:
        before = precise_volume(fin1)
        fin1 = checked_cut(fin1, cutter)
        removed[cutter.label] = before - precise_volume(fin1)
        if removed[cutter.label] <= 1e-3:
            raise ValueError((cutter.label, "cutter removed no host material"))
    if not fin1.is_valid or len(fin1.solids()) != 1:
        raise ValueError((fin, "fin leaf invalid or split after seat cuts"))
    fin1 = fin1.solids()[0]
    heads = [h for b in built for h in b["heads"]]
    for head in heads:
        if fin1.is_inside(head.center()):
            raise ValueError((head.label, "head centre inside host"))
    fin1.label, fin1.color = fin, fin0.color
    covers = [b["cover"] for b in built]
    meta = {
        "fin": fin, "fin_clock_degrees": clock,
        "seats": {b["meta"]["cover_label"][:-len("_cover")]: b["meta"] for b in built},
        "removed_mm3": removed, "host_volume_removed_mm3": sum(removed.values()),
        "faces": {"fin_before": len(fin0.faces()), "fin_after": len(fin1.faces()),
                  "cover_faces": [len(c.faces()) for c in covers],
                  "head_faces": [len(h.faces()) for h in heads]},
        "skin_point_calls": calls,
        "min_distance_to_other_fin_faces_mm": gap_fin,
        "min_distance_to_other_leaves_mm": gap_detail,
        "min_distance_between_seats_mm": gap_seats,
    }
    return fin1, covers, heads, meta


def build_r24():
    with STAGE_LOG.open("w", encoding="utf-8") as log:
        st = Stages(stage_budget_s=200.0, total_budget_s=290.0, out=log)
        scene = read_scene(SAVED)
        saved = {r.label: scene.resolve(r.ref).shape() for r in scene.leaves()}
        replace, covers, heads, fins_meta = {}, [], [], {}
        for n, fin, clock in FINS:
            st.stage(f"fin{n}_seats")
            fin1, c, h, m = fin_seats(saved, n, fin, clock, st)
            replace[fin], fins_meta[fin] = fin1, m
            covers += c
            heads += h
        st.stage("assemble")

        labels = [p.label for p in heads + covers]
        if len(set(labels)) != len(labels) or set(labels) & set(saved):
            raise ValueError("duplicate R24 labels")
        children = []
        for node in scene.roots[0].children:
            group = r20._rebuild(scene, node, replace)
            if node.label == HARDWARE_GROUP:
                group = bd.Compound(children=[*group.children, *heads], label=HARDWARE_GROUP)
            elif node.label == OLD_COVER_GROUP:
                group = bd.Compound(children=[*group.children, *covers], label=COVER_GROUP)
            children.append(group)

        meta = {
            "source_step": str(SAVED.relative_to(ROOT)),
            "source_document_hash": scene.document_hash,
            "units": "mm; clock 0 = +Z, 90 = +Y; tangent = (0, cos, -sin)",
            "recipe": "halberd_r24p_flank_lip_seats.build_seat (imported, unchanged)",
            "fins": fins_meta, "hardware_group": HARDWARE_GROUP, "cover_group": COVER_GROUP,
            "hardware_labels": [h.label for h in heads], "cover_labels": [c.label for c in covers],
            "skin_point_calls": sum(m["skin_point_calls"] for m in fins_meta.values()),
        }
        meta["stage_seconds"] = st.done()
    OUTPUT_METADATA.write_text(json.dumps(meta, indent=2, default=float) + "\n", encoding="utf-8")
    return bd.Compound(children=children, label="halberd_r24_booster_seats")


def _materials():
    materials = copy.deepcopy(r20.MATERIALS)
    materials["assignments"].append({"targets": [f"#{COVER_GROUP}"], "material": "detail_paint"})
    return materials


MATERIALS = _materials()


@step(out="../STEP/r24_booster_seats.step", materials=MATERIALS)
def r24_booster_seats():
    return build_r24()


if __name__ == "__main__":
    r24_booster_seats()
