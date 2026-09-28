"""Read serialized rounded-cap Spear artifacts; guard all selected fin/core geometry."""

import json
from pathlib import Path

from cadgen import build123d as bd, read_step
from cadgen.geometry import boundary_edges, self_intersections, topology_errors

from check_spear_revisions import cap_radius_at, overlap, parts_from, radial_max, same_solid


ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / "STEP"
OFFSET = 270.


def main():
    prior = parts_from(STEP / "Spear_Selected_SketchLow_Boattail.step")
    updated = parts_from(STEP / "Spear_RoundedTip_Boattail.step")
    separated = parts_from(STEP / "Spear_RoundedTip_Boattail_Separated.step")
    focus = {part.label: part for part in
             read_step(STEP / "Spear_RoundedTip_Cap_Focus.step").children}
    assert set(updated) == set(prior) == set(separated)
    assert set(focus) == {"turning_cap", "thruster_0", "thruster_90", "thruster_180", "thruster_270"}

    for label in updated:
        if label != "turning_cap":
            assert same_solid(updated[label], prior[label]), (label, "non-cap geometry changed")
        if label in focus:
            assert same_solid(updated[label], focus[label]), (label, "isolated cap differs")
        moved = label == "turning_cap" or label.startswith("thruster_")
        restored = separated[label].translate((OFFSET, 0, 0)) if moved else separated[label]
        assert same_solid(updated[label], restored), (label, "separated geometry changed")

    cap, body, nozzle = (updated[name] for name in ("turning_cap", "body", "main_nozzle"))
    for label, candidate in (("assembled", cap), ("separated", separated["turning_cap"]),
                             ("cap focus", focus["turning_cap"])):
        assert not topology_errors(candidate), f"{label}: invalid cap topology"
        assert len(candidate.shells()) == 1 and not boundary_edges(candidate.shells()[0]), (
            label, "cap shell is open"
        )
        assert not self_intersections(candidate), f"{label}: cap self-intersection"
    bounds = cap.bounding_box()
    assert abs(bounds.min.X + 600.) < .002 and abs(bounds.max.X + 420.) < .002, (
        f"rounded cap overshot datums: {bounds.min.X}, {bounds.max.X}"
    )
    assert overlap(cap, body) < .001 and overlap(separated["turning_cap"], body) < .001
    assert not same_solid(cap, prior["turning_cap"]), "rounded tip indistinguishable from flat cap"
    radii = {str(x): round(cap_radius_at(cap, x), 3)
             for x in (-599.5, -595., -580., -566., -523., -485., -421.)}
    assert cap_radius_at(cap, -599.5) < 8., "flat rear disc still prominent"
    assert cap_radius_at(prior["turning_cap"], -599.5) > 30.
    assert all(cap_radius_at(cap, x) < cap_radius_at(cap, y)
               for x, y in ((-599.5, -595.), (-595., -580.),
                            (-580., -566.), (-566., -523.), (-523., -485.)))
    assert cap_radius_at(cap, -485.) > 61. and cap_radius_at(cap, -421.) > 60.
    for angle in (0, 90, 180, 270):
        assert overlap(updated[f"thruster_{angle}"], cap) > .001

    lip = bd.Box(2, 2, 2).translate((-415., 27., 0.))
    bore = bd.Box(2, 2, 2).translate((-415., 0., 0.))
    assert overlap(lip, nozzle) > .001 and overlap(bore, nozzle) < .001
    assert overlap(bore, body) < .001
    envelope = max(radial_max(part) for part in updated.values())
    assert abs(envelope-79.009) < .02
    report = {"ok": True, "length_mm": 1200., "radial_envelope_mm": round(envelope, 3),
              "cap_rear_radius_sections_mm": radii, "tip_closed": True,
              "cap_topology_and_self_intersections_checked": True,
              "approved_fins_preserved": True, "separation_shape_preserved": True}
    (ROOT / "reviews" / "spear_rounded_cap_checks.json").write_text(
        json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print("PASS: rounded closed boattail, preserved fourfold fins, cap separation")


if __name__ == "__main__":
    main()
