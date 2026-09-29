"""A11 teal-outline nose: only the forward shell may differ from approved A10."""

import json
from pathlib import Path

from cadgen import build123d as bd

from check_a import limits, same, saved, saved_spear
from check_a10 import slice_span

ROOT = Path(__file__).resolve().parents[1]
OUTER = (3482., 400., 223.)


def main():
    old = saved("A10_DroopedEnds_Bare.step")
    bare = saved("A11_TealNose_Bare.step")
    full = saved("A11_TealNose_Filled.step")
    assert len(bare) == 9 and len(full) == 13 and set(bare) == set(old)
    for name, shape in bare.items():
        same(shape, full[name])
        if name != "forward_sensor_shell":
            same(shape, old[name])
    nose = bare["forward_sensor_shell"]
    assert nose.is_valid and nose.volume > 0
    assert all(abs(a-b) < .01 for a, b in zip(limits(nose)[0], (1325, 1812)))
    tip = slice_span(nose, 1811.97)
    assert tip[0] < 30 and tip[1] < 16 and abs((tip[2]+tip[3])/2+135) < 3, tip
    profile = {}
    for x in (1350., 1450., 1550., 1650., 1750., 1790.):
        w, h, low, high = slice_span(nose, x)
        assert -223.5 <= low and high <= .5, (x, low, high)
        profile[x] = (low, high)
    tops = [profile[x][1] for x in sorted(profile)]
    bots = [profile[x][0] for x in sorted(profile)]
    assert tops == sorted(tops, reverse=True), profile      # roof only descends
    assert bots == sorted(bots), profile                    # belly only rises
    for state in (bare, full):
        b = [limits(s) for s in state.values()]
        dims = [round(max(v[i][1] for v in b)-min(v[i][0] for v in b), 3)
                for i in range(3)]
        assert all(abs(d-t) < .5 for d, t in zip(dims, OUTER)), dims
    radius, length = saved_spear()
    assert abs(length-1200) < .002 and abs(radius*2-158.013) < .02
    report = {"ok": True, "outer_xyz_mm": list(OUTER),
              "front_fairing_length_mm": 487,
              "tip_section_yz_zmin_zmax_mm": tip,
              "slice_zmin_zmax_by_x_mm": {str(k): v for k, v in profile.items()},
              "law": "independent superellipse roof (n1.75,m1.4) and belly (n1.88,m2.59), tip 12mm at -135",
              "only_forward_shell_differs_from_A10": True,
              "user_visual_approval": False,
              "donor_aircraft_door_clearance_verified": False}
    (ROOT/"reviews"/"A11_TealNose_Checks.json").write_text(
        json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
