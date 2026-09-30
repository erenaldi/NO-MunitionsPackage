"""Measure host skin radius vs X/clock and map obstructions (R19 full-body planning)."""
import json, sys
from pathlib import Path
sys.path.insert(0, "src")
sys.path.insert(0, str(Path("../shared").resolve()))
from halberd_r18_access_shapes import load_saved_parts
from surface_detail import skin_point

scene, saved = load_saved_parts(Path("STEP/halberd_r18_access.step"))

HOSTS = {"main_body_intake_r12": (-1123.33, 1085.0), "booster_body": (-1685.0, -1123.33)}
CLOCKS = [c * 15.0 for c in range(24)]

# obstruction boxes: every other part, padded
def obstacles(host_label):
    out = []
    for label, sh in saved.items():
        if label in HOSTS:
            continue
        b = sh.bounding_box()
        out.append((label, b.min.X-4, b.max.X+4, b.min.Y-4, b.max.Y+4, b.min.Z-4, b.max.Z+4))
    return out

result = {}
for host_label, (x0, x1) in HOSTS.items():
    host = saved[host_label]
    obs = obstacles(host_label)
    stations = []
    n = 40
    for i in range(n + 1):
        x = x0 + 6.0 + (x1 - x0 - 12.0) * i / n
        row = {"x": round(x, 2), "clocks": {}}
        for c in CLOCKS:
            try:
                sp = skin_point(host, x, 0.0, c)
                r = sp["measured_radius_mm"]
                p = sp["point"]
                dot = sp["normal"].dot(__import__("surface_detail").clock_frame(c)[0])
                blockers = [o[0] for o in obs
                            if o[1] <= p.X <= o[2] and o[3] <= p.Y <= o[4] and o[5] <= p.Z <= o[6]]
                row["clocks"][int(c)] = {"r": round(r, 2), "ndot": round(dot, 3),
                                         "block": blockers}
            except Exception as e:
                row["clocks"][int(c)] = {"err": str(e)[:60]}
        stations.append(row)
    result[host_label] = stations

Path("tmp/section_map.json").write_text(json.dumps(result, indent=1))
for host_label, stations in result.items():
    print("=====", host_label)
    print("   X     " + " ".join(f"{int(c):>4d}" for c in CLOCKS))
    for row in stations:
        cells = []
        for c in CLOCKS:
            d = row["clocks"][int(c)]
            if "err" in d:
                cells.append("  ??")
            elif d["block"]:
                cells.append("   X")
            else:
                cells.append(f"{d['r']:4.0f}")
        print(f"{row['x']:8.1f} " + " ".join(cells))
