"""B2H square rear-nozzle check (concept-level, static): validity, void containment, attachment chain, non-attached-to-nothing test,
petal-to-petal clearance. Not a motion, airflow or structural check."""
import json, sys, itertools
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import aft_exhaust_r1 as aft
import engine_bay_b2h as g
from cadgen import build123d as bd

ROOT = Path(__file__).resolve().parents[1]
parts = g.nozzle_parts()
by = {p.label: p for p in parts}
liner = aft.liner()
tool = aft.inner_liner_tool()

def vol(a, c):
    i = a & c
    return 0.0 if i is None else sum(s.volume for s in i.solids())

rep = {"part_count": len(parts), "all_valid_solids": all(p.is_valid and p.volume > 0 for p in parts)}
# 1. containment: everything except intended wall-embeds lies inside the open liner void
out_of_void = {p.label: round(p.volume - vol(p, tool), 3) for p in parts}
rep["outside_liner_void_mm3"] = {k: v for k, v in out_of_void.items() if v > 0.001}
# 2. attachment graph (edges = positive-volume overlap, > 0.01 mm3)
labels = [p.label for p in parts] + ["LINER"]
shapes = {p.label: p for p in parts}
shapes["LINER"] = liner
edges = {}
for a, b in itertools.combinations(labels, 2):
    if a == "LINER" or b == "LINER":
        other = b if a == "LINER" else a
        v = vol(shapes[other], liner)
    else:
        v = vol(shapes[a], shapes[b])
    if v > 0.01:
        edges[f"{a} <-> {b}"] = round(v, 3)
rep["overlap_edges"] = edges
adj = {l: set() for l in labels}
for k in edges:
    a, b = k.split(" <-> "); adj[a].add(b); adj[b].add(a)
seen, stack = {"LINER"}, ["LINER"]
while stack:
    n = stack.pop()
    for m in adj[n]:
        if m not in seen: seen.add(m); stack.append(m)
rep["parts_not_attached_to_liner_chain"] = [l for l in labels if l not in seen]
# 3. petal overlaps: petals may touch the ring but adjacent petals must not intersect each other
pet = [p for p in parts if any(k in p.label for k in ("petal", "flap", "facet"))]
rep["petal_petal_overlap_mm3"] = {f"{a.label}|{b.label}": round(vol(a, b), 3) for a, b in itertools.combinations(pet, 2) if vol(a, b) > 0.001}
print(json.dumps({k: v for k, v in rep.items() if k != "overlap_edges"}, indent=1))
(ROOT / "reviews" / "engine_bay_b2h_nozzle_checks.json").write_text(json.dumps(rep, indent=1))
