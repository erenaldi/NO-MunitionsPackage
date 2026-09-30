"""A12 additive sensor studies: shells untouched, sensors only add material."""

import json
from pathlib import Path

from check_a import intersection, limits, same, saved

ROOT = Path(__file__).resolve().parents[1]


def main():
    a11 = saved("A11_TealNose_Bare.step")
    report = {}
    for n in (1, 2, 3, 4, 5):
        study = saved(f"A12_Sensors_C{n}.step")
        base = {k: v for k, v in study.items() if not k.startswith("sensor_")}
        sensors = {k: v for k, v in study.items() if k.startswith("sensor_")}
        assert set(base) == set(a11) and sensors, n
        for name, part in base.items():
            same(part, a11[name])                      # nothing subtracted
        shells = (base["forward_sensor_shell"], base["aft_sensor_shell"])
        info = {}
        for name, part in sensors.items():
            overlap = max(intersection(part, s) for s in shells)
            for other, op in sensors.items():
                if other < name:
                    assert intersection(part, op) < 0.5, (n, name, other, "overlap")
            assert overlap < 0.5, (n, name, "overlaps shell", overlap)
            (x0, x1), (y0, y1), (z0, z1) = limits(part)
            assert z0 >= -223.05 and z1 <= 0.05, (n, name, "outside Z band", z0, z1)
            assert max(abs(y0), abs(y1)) <= 200.05, (n, name, "wider than 400", y0, y1)
            supports = list(shells)+[p for k, p in sensors.items() if k != name]
            near = min(part.distance_to(s) for s in supports)
            assert near < 0.05, (n, name, "floating: no shell/sensor support", near)
            info[name] = {"volume_mm3": round(part.volume, 1),
                          "x": [round(x0, 1), round(x1, 1)],
                          "z": [round(z0, 1), round(z1, 1)],
                          "overlap_with_shell_mm3": round(overlap, 4),
                          "gap_to_shell_mm": round(near, 4)}
        allx = [limits(p)[0] for p in study.values()]
        env = [round(max(v[1] for v in allx)-min(v[0] for v in allx), 1)]
        report[f"C{n}"] = {"parts": len(sensors), "x_span_mm": env[0],
                           "sensors": info}
    out = {"ok": True, "shells_identical_to_A11": True,
           "additive_only": True, "user_visual_approval": False,
           "concepts": report}
    (ROOT/"reviews"/"A12_Sensors_Checks.json").write_text(
        json.dumps(out, indent=1)+"\n", encoding="utf-8")
    print(json.dumps({k: (v["parts"], v["x_span_mm"]) for k, v in report.items()}), "ok")


if __name__ == "__main__":
    main()
