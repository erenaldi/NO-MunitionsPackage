"""Check shortened-cap, moved nozzle and thinner fins in exported STEP files."""

import json
import math
from pathlib import Path

from cadgen import build123d as bd, read_step
from cadgen.geometry import boundary_edges, self_intersections, topology_errors

from check_spear_revisions import cap_radius_at, cut_volume, overlap, radial_max, same_solid


ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / "STEP"
DISPLACEMENT = 270.


def load(name, count):
    model = read_step(STEP / name)
    parts = {part.label: part for part in model.children}
    assert len(parts) == len(model.children) == count, name
    assert all(len(part.solids()) == 1 and part.is_valid and part.volume > 0
               for part in parts.values()), name
    return parts


def plate_width(part, radial_position):
    vertices, _ = part.tessellate(.15)
    tangent = (-math.sqrt(.5), math.sqrt(.5))  # fin 0 at 45°
    samples = [v.Y*tangent[0]+v.Z*tangent[1] for v in vertices
               if abs(math.hypot(v.Y, v.Z)-radial_position) < .12]
    assert samples, (part.label, radial_position, "missing root/tip vertices")
    return max(samples)-min(samples)


def main():
    baseline = load("Spear_FlushJunction_Cap.step", 12)
    assembled = load("Spear_ShortCap_ThinFins.step", 12)
    separated = load("Spear_ShortCap_ThinFins_Separated.step", 12)
    focus = load("Spear_ShortCap_ThinFins_Cap_Focus.step", 6)
    assert set(baseline) == set(assembled) == set(separated)
    assert set(focus) == {"turning_cap", "thruster_0", "thruster_0_throat",
                          "thruster_90", "thruster_180", "thruster_270"}
    body, cap = assembled["body"], assembled["turning_cap"]
    assert abs(cap.bounding_box().min.X+600.) < .002
    assert abs(cap.bounding_box().max.X+470.) < .002
    assert abs(body.bounding_box().min.X+470.) < .002
    assert abs(body.bounding_box().max.X-600.) < .002
    assert abs(baseline["turning_cap"].bounding_box().max.X+420.) < .002
    unchanged_body = bd.Box(1050., 250., 250.).translate((105., 0., 0.))
    assert same_solid(body & unchanged_body,
                      baseline["body"] & unchanged_body), "body changed forward of old seam"
    assert abs(cap_radius_at(cap, -471.)-62.) < .03
    assert abs(cap_radius_at(body, -469.)-62.) < .03
    assert abs(cap_radius_at(body, -421.)-62.) < .03
    assert overlap(body, cap) < .001 and overlap(separated["turning_cap"], body) < .001
    assert same_solid(assembled["main_nozzle"].translate((50., 0., 0)),
                      baseline["main_nozzle"]), "main nozzle did not follow seam"
    assert overlap(assembled["main_nozzle"], body) < .001

    # Four nozzle housings move to one mid-cap axial station. Existing three
    # basic housings and the one detailed shroud retain their cross-sections.
    old_detailed_x = baseline["thruster_0"].bounding_box().center().X
    moved_nozzle_x = assembled["thruster_0"].bounding_box().center().X
    assert abs(moved_nozzle_x+535.) < .002
    assert same_solid(assembled["thruster_0"].translate((old_detailed_x-moved_nozzle_x, 0, 0)),
                      baseline["thruster_0"])
    assert same_solid(assembled["thruster_0_throat"].translate((old_detailed_x-moved_nozzle_x, 0, 0)),
                      baseline["thruster_0_throat"])
    nozzle_centers = {}
    for angle in (0, 90, 180, 270):
        label = f"thruster_{angle}"
        part = assembled[label]
        nozzle_centers[label] = round(part.bounding_box().center().X, 3)
        assert abs(nozzle_centers[label]+535.) < .002, (label, "nozzle outside mid-cap station")
        assert part.bounding_box().max.X < -470., (label, "nozzle bridges seam")
        assert overlap(part, cap) > .001, (label, "nozzle detached")

    old_root = plate_width(baseline["aft_fin_0"], 55.)
    old_tip = plate_width(baseline["aft_fin_0"], 79.)
    new_root = plate_width(assembled["aft_fin_0"], 55.)
    new_tip = plate_width(assembled["aft_fin_0"], 79.)
    assert abs(old_root-7.) < .05 and abs(old_tip-2.4) < .05
    assert abs(new_root-6.) < .05 and abs(new_tip-2.) < .05
    for index in range(4):
        label = f"aft_fin_{index}"
        before, after = baseline[label], assembled[label]
        assert not same_solid(before, after), (label, "fin thickness unchanged")
        assert abs(before.bounding_box().min.X-after.bounding_box().min.X) < .002
        assert abs(before.bounding_box().max.X-after.bounding_box().max.X) < .002
        assert abs(radial_max(before)-radial_max(after)) < .02
        assert overlap(after, body) > .001 and overlap(after, cap) < .001
        assert same_solid(assembled["aft_fin_0"].rotate(bd.Axis.X, index*90), after)

    for label, part in assembled.items():
        if label in focus:
            assert same_solid(part, focus[label]), (label, "focus differs")
        moved = label == "turning_cap" or label.startswith("thruster_")
        restored = separated[label].translate((DISPLACEMENT, 0, 0)) if moved else separated[label]
        assert same_solid(part, restored), (label, "separated shape changed",
                                           cut_volume(part, restored), cut_volume(restored, part),
                                           tuple(part.bounding_box().min), tuple(restored.bounding_box().min),
                                           part.volume, restored.volume,
                                           overlap(part, restored), cut_volume(part, part))
    for label in ("body", "turning_cap", "main_nozzle", "aft_fin_0", "thruster_0", "thruster_0_throat"):
        part = assembled[label]
        assert not topology_errors(part), (label, "invalid topology")
        assert len(part.shells()) == 1 and not boundary_edges(part.shells()[0]), (label, "open shell")
        assert not self_intersections(part), (label, "self-intersection")
    mouth = bd.Box(1., 1., 1.).translate((-535., 66.5, 0.))
    blind = bd.Box(1., 1., 1.).translate((-535., 46., 0.))
    assert overlap(mouth, cap) < .001 and overlap(mouth, assembled["thruster_0"]) < .001
    assert overlap(blind, cap) > .001
    main_bore = bd.Box(2., 2., 2.).translate((-465., 0., 0.))
    assert overlap(main_bore, body) < .001 and overlap(main_bore, assembled["main_nozzle"]) < .001
    envelope = max(radial_max(part) for part in assembled.values())
    assert abs(envelope-79.009) < .02
    result = {"ok": True, "total_length_mm": 1200., "cap_length_mm": 130.,
              "new_seam_x_mm": -470., "max_radius_mm": round(envelope, 3),
              "cap_body_radius_at_seam_mm": 62., "nozzle_stations_x_mm": nozzle_centers,
              "original_fin_root_tip_thickness_mm": [round(old_root, 3), round(old_tip, 3)],
              "new_fin_root_tip_thickness_mm": [round(new_root, 3), round(new_tip, 3)],
              "forward_body_exact": True, "main_nozzle_relinked": True,
              "fourfold_symmetric_fins": True, "detached_shapes_preserved": True}
    (ROOT / "reviews" / "spear_short_cap_checks.json").write_text(
        json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print("PASS: 130 mm cap, aft-extended body, relocated stages and thin fins")


if __name__ == "__main__":
    main()
