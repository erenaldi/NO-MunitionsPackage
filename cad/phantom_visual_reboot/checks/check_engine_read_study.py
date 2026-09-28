"""Containment check for the rough engine-read studies (visual concepts only).

Reports, per option, how much of each insert part lies outside the R1 passage voids
(liner inner tool + connector + original intake stub). Struts/pylons are built to
embed ~1.5 mm into the wall as attachment stand-ins; anything else outside is a defect.
Not an approval and not a clearance/airflow claim.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import aft_exhaust_r1 as aft
import engine_read_study as e
from cadgen import build123d as bd

void = aft.inner_liner_tool() + aft.connector_cutter() + aft.ruled_loft(e.STUB_SECTIONS)
void = void.clean()
report = {}
worst_non_mount = 0.0
for name, fn in e.OPTIONS.items():
    rows = []
    for p in fn():
        inter = p & void
        outside = p.volume - (sum(s.volume for s in inter.solids()) if inter is not None else 0.0)
        mount = any(k in p.label for k in ("strut", "pylon"))
        rows.append((p.label, round(p.volume, 2), round(max(outside, 0.0), 2), mount))
        if not mount:
            worst_non_mount = max(worst_non_mount, outside)
    bad = [r for r in rows if not r[3] and r[2] > 0.5]
    report[name] = {"parts": len(rows), "non_mount_parts_outside_gt_0.5mm3": bad,
                    "mount_parts_embedding_mm3": {r[0]: r[2] for r in rows if r[3]}}
    print(name, "parts", len(rows), "non-mount outside>0.5mm3:", bad)
out = Path(__file__).resolve().parents[1] / "reviews" / "engine_read_study_checks.json"
out.write_text(json.dumps(report, indent=1))
print("worst non-mount outside mm3:", round(worst_non_mount, 3))
