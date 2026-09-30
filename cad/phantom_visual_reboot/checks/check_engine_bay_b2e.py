"""B2E (ramp +15 mm tangential) detail-pass interference report (concept-level; not an approval, not a swept-motion or airflow check).

For each pose (Stowed = door closed, engine level; Deployed = door open, engine on the 3.04 deg ramp) reports the
intersection volume (mm3) of every detail part against: the review body (after chamber/duct/cavity/seat cuts),
the ramp part, the R1 liner, and against every other detail part group. Mount-type parts that are meant to touch
or embed (mount pads, nozzle ring, tail struts) are reported but flagged as expected contact.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import aft_exhaust_r1 as aft
import engine_bay_b2 as b
import engine_bay_b2e as d
from cadgen import build123d as bd

ROOT = Path(__file__).resolve().parents[1]
EXPECT = ("mount_pad", "nozzle_ring", "tail_strut")

def vol(a, c):
    i = a & c
    return 0.0 if i is None else round(sum(s.volume for s in i.solids()), 3)

report = {}
for state in ("Stowed", "Deployed"):
    body, parts, clip = d.body_cut(state)
    ramp = parts["intake_r1_ramp"] & clip
    liner = aft.liner() & clip
    det = d.detail_parts(state)
    rows = {}
    for p in det:
        bb = p.bounding_box()
        row = {"body": vol(p, body), "ramp": vol(p, ramp), "liner": vol(p, liner)}
        row["expected_contact"] = any(k in p.label for k in EXPECT)
        rows[p.label] = row
    pair = []
    groups = {"engine": [p for p in det if p.label.startswith(("b2_engine", "b2d_face", "b2d_inlet", "b2d_fan", "b2d_spinner"))],
              "door": [p for p in det if p.label.startswith("b2d_door")],
              "nozzle": [p for p in det if p.label.startswith(("b2d_nozzle", "b2d_tail"))]}
    cross = {}
    for a, c in (("engine", "door"), ("engine", "nozzle"), ("door", "nozzle")):
        tot = 0.0
        for pa in groups[a]:
            for pc in groups[c]:
                tot += vol(pa, pc)
        cross[f"{a}_vs_{c}"] = round(tot, 3)
    bad = {k: v for k, v in rows.items() if not v["expected_contact"] and (v["body"] > 0.5 or v["ramp"] > 0.5 or v["liner"] > 0.5)}
    report[state] = {"non_expected_interference_gt_0.5mm3": bad, "cross_group_mm3": cross,
                     "expected_contact_parts": {k: v for k, v in rows.items() if v["expected_contact"]},
                     "part_count": len(rows)}
    print(state, "parts", len(rows), "non-expected interference:", bad, "cross:", cross)
(ROOT / "reviews" / "engine_bay_b2e_checks.json").write_text(json.dumps(report, indent=1))
