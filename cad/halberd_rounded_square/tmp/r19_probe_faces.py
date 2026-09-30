"""Exploratory: flat-face widths per station and booster aft profile."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parents[0] / "shared"))

from surface_detail import skin_point  # noqa: E402
from halberd_r18_access_shapes import load_saved_parts  # noqa: E402

scene, saved = load_saved_parts(ROOT / "STEP" / "halberd_r18_access.step")
main, booster = saved["main_body_intake_r12"], saved["booster_body"]


def flat_extent(host, x, clock):
    """Largest |tangent| (both signs) where the skin stays at radius ~100 with radial normal."""
    out = []
    for sign in (1, -1):
        last = 0.0
        for t in range(0, 120, 1):
            try:
                s = skin_point(host, x, sign * t, clock)
            except Exception:  # noqa: BLE001
                break
            n = s["normal"]
            from surface_detail import clock_frame
            radial, _ = clock_frame(clock)
            if abs(s["measured_radius_mm"] - 100.0) > 0.05 or n.dot(radial) < 0.9999:
                break
            last = t
        out.append(sign * last)
    return out


for x in (680, 650, 600, 500, 300, 0, -300, -360, -400, -450, -500, -700, -850, -900, -1000, -1100):
    print(x, {c: flat_extent(main, x, c) for c in (0, 90, 180, 270)})
for x in (-1130, -1200, -1300, -1450, -1490, -1520, -1550):
    print(x, {c: flat_extent(booster, x, c) for c in (0, 90, 180, 270)})

for x in range(-1480, -1690, -5):
    try:
        r0 = skin_point(booster, x, 0.0, 0)["measured_radius_mm"]
        r45 = skin_point(booster, x, 0.0, 45)["measured_radius_mm"]
    except Exception as exc:  # noqa: BLE001
        r0 = r45 = float("nan")
    print(f"booster X={x} r0={r0:.3f} r45={r45:.3f}")

# Booster circumferential edges (constant-X loops) reveal section joints.
xs = set()
for e in booster.edges():
    b = e.bounding_box()
    if b.max.X - b.min.X < 1e-4:
        xs.add(round(b.min.X, 3))
print("booster constant-X edge stations:", sorted(xs))
xs = set()
for e in main.edges():
    b = e.bounding_box()
    if b.max.X - b.min.X < 1e-4:
        xs.add(round(b.min.X, 3))
print("main constant-X edge stations:", sorted(xs))
for i in range(1, 5):
    f = saved[f"booster_fin_fairing_{i}"]
    print("fairing", i, "overlap body", (f & booster).volume if (f & booster) else 0.0)
    m = saved[f"main_fin_{i}"]
    print("main fin", i, "overlap body", (m & main).volume if (m & main) else 0.0)
