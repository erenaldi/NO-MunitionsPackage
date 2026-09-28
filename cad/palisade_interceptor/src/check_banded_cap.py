"""Saved-artifact checks for the red-box cap band and ONE detailed nozzle."""

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
    def load_preview(path):
        shape = read_step(path)
        result = {part.label: part for part in shape.children}
        assert len(shape.children) == len(result) == 12, (path, "missing or duplicate component")
        assert all(len(part.solids()) == 1 and part.is_valid and part.volume > 0
                   for part in result.values()), path
        return result

    updated = load_preview(STEP / "Spear_BandedCap_Nozzle0.step")
    apart = load_preview(STEP / "Spear_BandedCap_Nozzle0_Separated.step")
    isolated = {part.label: part for part in read_step(STEP / "Spear_BandedCap_Cap_Focus.step").children}
    assert set(updated) == set(apart) == set(prior) | {"thruster_0_throat"}
    assert set(isolated) == {"turning_cap", "thruster_0", "thruster_90",
                             "thruster_180", "thruster_270", "thruster_0_throat"}
    for label, part in updated.items():
        if label in prior and label not in ("turning_cap", "thruster_0"):
            assert same_solid(part, prior[label]), (label, "protected Spear part changed")
        if label in isolated:
            assert same_solid(part, isolated[label]), (label, "isolated cap differs")
        moved = label == "turning_cap" or label.startswith("thruster_")
        restored = apart[label].translate((OFFSET, 0, 0)) if moved else apart[label]
        assert same_solid(part, restored), (label, "stage geometry changed")

    cap, nozzle, insert = (updated[name] for name in
                           ("turning_cap", "thruster_0", "thruster_0_throat"))
    body, main = updated["body"], updated["main_nozzle"]
    assert not same_solid(cap, prior["turning_cap"])
    assert not same_solid(nozzle, prior["thruster_0"])
    assert abs(cap.bounding_box().min.X+600.) < .002
    assert abs(cap.bounding_box().max.X+420.) < .002
    assert overlap(cap, body) < .001 and overlap(apart["turning_cap"], body) < .001
    for label, part in (("cap", cap), ("nozzle", nozzle), ("throat", insert),
                        ("separated cap", apart["turning_cap"]),
                        ("isolated cap", isolated["turning_cap"])):
        assert len(part.solids()) == 1 and part.volume > 0
        assert not topology_errors(part), (label, "topology")
        assert len(part.shells()) == 1 and not boundary_edges(part.shells()[0]), (label, "open shell")
        assert not self_intersections(part), (label, "self-intersection")

    sections = {str(x): round(cap_radius_at(cap, x), 3)
                for x in (-599.5, -566., -520., -500., -470., -440., -421.)}
    assert cap_radius_at(cap, -599.5) < 8. and cap_radius_at(cap, -566.) > 33.
    assert cap_radius_at(cap, -520.) > 61. and cap_radius_at(cap, -470.) > 60.5
    assert cap_radius_at(cap, -440.) > 60.5 and cap_radius_at(cap, -421.) > 60.
    assert overlap(nozzle, cap) > .001, "new nozzle has no seated root"
    assert abs(nozzle.bounding_box().min.X + 482.) < .1
    assert abs(nozzle.bounding_box().max.X + 458.) < .1
    mouth = bd.Box(1., 1., 1.).translate((-470., 66.5, 0.))
    lip = bd.Box(1., 1., 1.).translate((-470., 67.6, 9.))
    throat = bd.Box(1., 1., 1.).translate((-470., 55., 0.))
    dark_back = bd.Box(1., 1., 1.).translate((-470., 49., 0.))
    blind_back = bd.Box(1., 1., 1.).translate((-470., 46., 0.))
    assert overlap(mouth, nozzle) < .001 and overlap(mouth, cap) < .001
    assert overlap(lip, nozzle) > .001, "missing stepped front lip"
    assert overlap(throat, cap) < .001 and overlap(blind_back, cap) > .001
    assert overlap(throat, nozzle) < .001, "throat blocked"
    assert overlap(dark_back, insert) > .001 and overlap(insert, cap) < .001
    assert insert.distance_to(cap) < .002, "dark inset floats inside cap socket"
    # Original other three nozzles remain attached and are not accidentally
    # described as already detailed.
    for angle in (90, 180, 270):
        assert overlap(updated[f"thruster_{angle}"], cap) > .001
    main_bore = bd.Box(2, 2, 2).translate((-415., 0., 0.))
    assert overlap(main_bore, main) < .001 and overlap(main_bore, body) < .001
    envelope = max(radial_max(part) for part in updated.values())
    assert abs(envelope-79.009) < .02
    report = {"ok": True, "length_mm": 1200., "radial_envelope_mm": round(envelope, 3),
              "band_and_tip_section_radii_mm": sections,
              "prototype_nozzle": "thruster_0", "detailed_nozzle_count": 1,
              "dark_blind_throat": True,
              "other_three_nozzles_original": True,
              "blind_recess_and_open_bore": True, "approved_fins_preserved": True,
              "stage_shapes_preserved": True}
    (ROOT / "reviews" / "spear_banded_cap_checks.json").write_text(
        json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print("PASS: banded cap, one recessed stepped nozzle, preserved Spear and stage")


if __name__ == "__main__":
    main()
