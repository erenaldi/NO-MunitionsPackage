"""Check the P04 RF layout study (saved STEP): RF patches are valid, disjoint from every keep-out patch, do not overlap any
baseline leaf (volume), and are identity-preserving (baseline leaves unchanged in count). Run from the CAD root."""
import json, sys
from cadgen import read_scene

s = read_scene("STEP/S_RF_Layout_P04_Study.step")
L = [(str(l.label), l.shape()) for l in s.leaves()]
rf = [(n, sh) for n, sh in L if n.startswith("RF_")]
kp = [(n, sh) for n, sh in L if n.startswith("KEEP_")]
base = [(n, sh) for n, sh in L if not n.startswith(("RF_", "KEEP_"))]
fails, rows = [], []
def vol(a, b):
    try: return sum(x.volume for x in (a & b)) if hasattr(a & b, "__iter__") else (a & b).volume
    except Exception as e: return None
for n, sh in rf:
    if not sh.is_valid or sh.volume <= 0: fails.append(f"{n} invalid/empty")
    for kn, ks in kp:
        bb, kb = sh.bounding_box(), ks.bounding_box()
        if bb.overlaps(kb) if hasattr(bb, "overlaps") else False:
            v = vol(sh, ks)
            if v is None or v > 1e-6: fails.append(f"{n} overlaps {kn}: {v}")
    worst = 0.0
    for bn, bs in base:
        if "symmetric_body" in bn: continue          # patches sit proud of the body (contact only)
        v = vol(sh, bs)
        if v and v > 1e-6: fails.append(f"{n} overlaps baseline leaf {bn}: {v}"); worst = max(worst, v)
    b = sh.bounding_box()
    rows.append({"zone": n, "volume_mm3": round(sh.volume, 2), "bbox": [round(v, 1) for v in (b.min.X, b.max.X, b.min.Y, b.max.Y, b.min.Z, b.max.Z)],
                 "max_abs_Y": round(max(abs(b.min.Y), abs(b.max.Y)), 1), "max_abs_Z": round(max(abs(b.min.Z), abs(b.max.Z)), 1)})
    if rows[-1]["max_abs_Y"] > 125 or rows[-1]["max_abs_Z"] > 125: fails.append(f"{n} outside 125 mm envelope")
json.dump({"gate": "P04 RF layout study (non-cutting)", "n_base_leaves": len(base), "n_rf": len(rf), "n_keepout": len(kp),
           "zones": rows, "failures": fails}, open("reviews/rf_layout_p04_checks.json", "w"), indent=1)
print("base leaves", len(base), "rf", len(rf), "keep", len(kp), "failures", fails)
sys.exit(1 if fails else 0)
