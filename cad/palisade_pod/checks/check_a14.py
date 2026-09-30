"""A14: D4 front mounts + rear inset-look window; shells untouched, additive."""

import json
from pathlib import Path

from check_a import intersection, limits, same, saved

ROOT = Path(__file__).resolve().parents[1]


def main():
    a11 = saved("A11_TealNose_Bare.step")
    study = saved("A14_Sensors.step")
    base = {k: v for k, v in study.items() if not k.startswith("sensor_")}
    sensors = {k: v for k, v in study.items() if k.startswith("sensor_")}
    assert set(base) == set(a11), "housing parts changed"
    for name, part in base.items():
        same(part, a11[name])                       # nothing subtracted
    front = [k for k in sensors if k.startswith("sensor_front")]
    rear = [k for k in sensors if k.startswith("sensor_rear")]
    assert front and rear and all("window" in k for k in rear), (front, rear)
    shells = (base["forward_sensor_shell"], base["aft_sensor_shell"])
    info = {}
    names = sorted(sensors)
    for i, name in enumerate(names):
        part = sensors[name]
        overlap = max(intersection(part, s) for s in shells)
        assert overlap < 0.5, (name, "overlaps shell", overlap)
        for other in names[:i]:
            assert intersection(part, sensors[other]) < 0.5, (name, other)
        (x0, x1), (y0, y1), (z0, z1) = limits(part)
        assert z0 >= -223.05 and z1 <= 0.05, (name, "outside Z band", z0, z1)
        assert max(abs(y0), abs(y1)) <= 200.05, (name, "wider than 400", y0, y1)
        supports = list(shells)+[sensors[o] for o in names if o != name]
        near = min(part.distance_to(s) for s in supports)
        assert near < 0.05, (name, "floating", near)
        info[name] = {"volume_mm3": round(part.volume, 1),
                      "x": [round(x0, 1), round(x1, 1)],
                      "gap_mm": round(near, 4)}
    allx = [limits(p)[0] for p in study.values()]
    span = round(max(v[1] for v in allx)-min(v[0] for v in allx), 1)
    rear_x = min(v["x"][0] for k, v in info.items() if k.startswith("sensor_rear"))
    assert rear_x >= -1670-0.5, ("rear window protrudes past the rear tip", rear_x)
    out = {"ok": True, "shells_identical_to_A11": True, "additive_only": True,
           "front_parts": len(front), "rear_parts": len(rear),
           "x_span_mm": span, "rear_extent_x_mm": rear_x,
           "user_visual_approval": False, "sensors": info}
    (ROOT/"reviews"/"A14_Sensors_Checks.json").write_text(
        json.dumps(out, indent=1)+"\n", encoding="utf-8")
    print("A14 ok", len(front), len(rear), span, rear_x)


if __name__ == "__main__":
    main()
