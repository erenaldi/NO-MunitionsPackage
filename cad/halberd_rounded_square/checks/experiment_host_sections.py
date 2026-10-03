"""Benchmark: N detail cuts on the whole main host vs on short sections (Codex handoff experiment).

Cutters are the REAL removed regions of the saved geometry: solids of (R18 main host - R19 main host),
i.e. the panel grooves, ring seats and seams the R19 builder cut. Both variants apply the same
cutters in the same order. A = sequential on the whole host (current practice). B = split into
sections, each cutter into its section, straddlers last, rejoin once. Read-only: inputs come from the
main copy; writes only reviews/experiment_host_sections.json. Budgets abort loudly.
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT.parent / "shared"))

import check_kit as ck  # noqa: E402
import host_sections as hs  # noqa: E402
from surface_detail import checked_cut  # noqa: E402

MAIN = Path(r"C:\Users\erena\Desktop\Nuclear Option Munitions Package\cad\halberd_rounded_square\STEP")
HOST = "main_body_intake_r12"
MAX_CUTTERS = int(sys.argv[1]) if len(sys.argv) > 1 else 120
SECTION_LEN = 250.0
A_BUDGET_S = 700.0

st = ck.Stages(stage_budget_s=900, total_budget_s=2400)
out = {"max_panels": MAX_CUTTERS}

st.stage("load R18/R19 hosts")
h18 = ck.load_leaves(MAIN / "halberd_r18_access.step")[2][HOST]
h19 = ck.load_leaves(MAIN / "halberd_r19_surface.step")[2][HOST]
out["faces_r18"], out["faces_r19"] = len(h18.faces()), len(h19.faces())

st.stage("build the real R19 main-panel cutters on the R18 host")
sys.path.insert(0, str(ROOT / "src"))
import halberd_r19_surface as r19  # noqa: E402
plan = [p for p in r19.plan_layout() if p["stage"] == "main"]
rect = tuple((p["id"], p["clock"], p["x"], p["length"], p["width"], p["tangent"], p["screws"])
             for p in plan if p["kind"] == "rect")
rnd = tuple((p["id"], p["clock"], p["x"], p["length"], p["tangent"], p["screws"])
            for p in plan if p["kind"] == "round")
# first MAX_CUTTERS panels in plan order (rect first as the builder does)
rect = rect[:MAX_CUTTERS]
rnd = rnd[:max(0, MAX_CUTTERS - len(rect))]
t = time.time()
cutters, _heads, _data = r19.build_panels(h18, rect, rnd, "main", [])
out["cutter_build_s"] = round(time.time() - t, 1)
out["panels"] = len(rect) + len(rnd)
out["cutters"] = len(cutters)
print("panels", out["panels"], "cutters", len(cutters), "built in", out["cutter_build_s"], flush=True)

st.stage("A: whole host, sequential")
host = h18
a_rows, t_a0 = [], time.time()
done_a = 0
for k, c in enumerate(cutters):
    t = time.time()
    host = checked_cut(host, c)
    a_rows.append(round(time.time() - t, 3))
    done_a += 1
    if time.time() - t_a0 > A_BUDGET_S:
        print("A budget reached after", done_a, flush=True)
        break
out["A"] = {"cuts_done": done_a, "seconds": round(time.time() - t_a0, 1),
            "first_quarter_avg": round(sum(a_rows[:max(1, done_a // 4)]) / max(1, done_a // 4), 3),
            "last_quarter_avg": round(sum(a_rows[-max(1, done_a // 4):]) / max(1, done_a // 4), 3),
            "faces_after": len(host.faces()), "volume": host.volume}
host_a = host
print("A", out["A"], flush=True)

st.stage("B: sections")
t_b0 = time.time()
bb = h18.bounding_box()
bounds = hs.choose_boundaries(cutters[:done_a], bb.min.X, bb.max.X, SECTION_LEN)
out['boundaries'] = bounds
t = time.time()
sections = hs.split_host(h18, bounds)
split_s = time.time() - t
inside, straddle = [], []
for c in cutters[:done_a]:
    try:
        hs.section_of(sections, c)
        inside.append(c)
    except ValueError:
        straddle.append(c)
t = time.time()
rows = hs.apply_cuts(sections, inside)
cut_s = time.time() - t
faces_sections = hs.face_report(sections)
t = time.time()
joined = hs.rejoin(sections)
join_s = time.time() - t
t = time.time()
for c in straddle:
    joined = checked_cut(joined, c)
late_s = time.time() - t
out["B"] = {"sections": len(sections), "section_len": SECTION_LEN, "cutters_in_section": len(inside),
            "straddlers": len(straddle), "split_s": round(split_s, 1), "cuts_s": round(cut_s, 1),
            "rejoin_s": round(join_s, 1), "straddler_cuts_s": round(late_s, 1),
            "total_s": round(time.time() - t_b0, 1), "faces_after": len(joined.faces()),
            "volume": joined.volume, "max_section_faces": max(f["faces"] for f in faces_sections),
            "section_faces": faces_sections,
            "cut_avg_s": round(sum(r[2] for r in rows) / max(1, len(rows)), 3)}
print("B", {k: v for k, v in out["B"].items() if k != "section_faces"}, flush=True)

st.stage("equivalence A vs B")
da, db = ck.removed_volume(host_a, joined)
out["equivalence"] = {"A_minus_B_mm3": da, "B_minus_A_mm3": db,
                      "volume_diff_mm3": host_a.volume - joined.volume}
print("EQUIV", out["equivalence"], flush=True)
out["timings"] = st.done()
(ROOT / "reviews" / "experiment_host_sections.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
