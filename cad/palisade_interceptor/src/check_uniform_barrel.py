"""Verify constant small-diameter Spear barrel/cap from serialized STEP."""

import json
import math
from pathlib import Path

from cadgen import build123d as bd, read_step
from cadgen.geometry import boundary_edges, self_intersections, topology_errors

from check_spear_revisions import cap_radius_at, overlap, radial_max, same_solid


ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / "STEP"
RADIUS = 54.56
CAP_SEAM = -470.
NOSE_BASE = 355.
OFFSET = 270.


def get_parts(name, count):
    result = read_step(STEP / name)
    parts = {item.label: item for item in result.children}
    assert len(parts) == len(result.children) == count, (name, "duplicate or missing part")
    assert all(item.is_valid and len(item.solids()) == 1 and item.volume > 0
               for item in parts.values()), (name, "invalid or nonpositive part")
    return parts


def main():
    previous = get_parts("Spear_ShortCap_ThinFins.step", 12)
    full = get_parts("Spear_UniformBarrel.step", 12)
    apart = get_parts("Spear_UniformBarrel_Separated.step", 12)
    focus = get_parts("Spear_UniformBarrel_Cap_Focus.step", 6)
    assert set(full) == set(apart) == set(previous)
    assert set(focus) == {"turning_cap", "thruster_0", "thruster_0_throat",
                          "thruster_90", "thruster_180", "thruster_270"}

    body, cap, nozzle = (full[label] for label in ("body", "turning_cap", "main_nozzle"))
    assert abs(body.bounding_box().min.X-CAP_SEAM) < .002
    assert abs(body.bounding_box().max.X-600.) < .002
    assert abs(cap.bounding_box().min.X+600.) < .002
    assert abs(cap.bounding_box().max.X-CAP_SEAM) < .002
    assert abs(cap.bounding_box().size.X-130.) < .002
    stations = {str(x): round(cap_radius_at(body, x), 3)
                for x in (-469., -400., -255., 0., 190., 300., 354.5)}
    assert all(abs(value-RADIUS) < .02 for value in stations.values()), (
        "barrel still changes diameter", stations
    )
    cap_stations = {str(x): round(cap_radius_at(cap, x), 3)
                    for x in (-599.5, -577., -535., -500., -471.)}
    assert abs(cap_stations["-599.5"]-(RADIUS-22.)) < 9., "rear fillet lost"
    assert all(abs(cap_stations[str(x)]-RADIUS) < .02
               for x in (-577., -535., -500., -471.))
    assert abs(cap_radius_at(body, -469.)-cap_radius_at(cap, -471.)) < .02
    assert overlap(cap, body) < .001 and overlap(apart["turning_cap"], body) < .001

    # An untouched nose starts at X=355; saved assembly comparison, not just
    # reused source parameters, establishes its physical shape identity.
    fore = bd.Box(260., 250., 250.).translate((485., 0., 0.))
    assert same_solid(body & fore, previous["body"] & fore), "pointed nose changed"
    assert same_solid(nozzle, previous["main_nozzle"]), "main nozzle moved or resized"
    lip = bd.Box(2., 2., 2.).translate((-465., 27., 0.))
    bore = bd.Box(2., 2., 2.).translate((-465., 0., 0.))
    blind_floor = bd.Box(2., 2., 2.).translate((-365., 0., 0.))
    assert overlap(lip, nozzle) > .001
    assert overlap(bore, nozzle) < .001 and overlap(bore, body) < .001
    assert overlap(blind_floor, body) > .001, "body cavity drilled through"

    fin0 = full["aft_fin_0"]
    for index in range(4):
        old, new = previous[f"aft_fin_{index}"], full[f"aft_fin_{index}"]
        assert abs(old.bounding_box().min.X-new.bounding_box().min.X) < .002
        assert abs(old.bounding_box().max.X-new.bounding_box().max.X) < .002
        assert abs(radial_max(new)-79.) < .1
        assert overlap(new, body) > .001, f"{index}: fin root floats off smaller barrel"
        assert overlap(new, cap) < .001
        assert same_solid(fin0.rotate(bd.Axis.X, index*90), new)

    nozzles = {}
    for index in (0, 90, 180, 270):
        label = f"thruster_{index}"
        part = full[label]
        nozzles[label] = round(part.bounding_box().center().X, 3)
        assert abs(nozzles[label]+535.) < .002
        assert overlap(part, cap) > .001, (label, "not seated on smaller cap")
    prototype = full["thruster_0"]
    assert abs(prototype.bounding_box().max.Y-60.76) < .1
    mouth = bd.Box(1., 1., 1.).translate((-535., 59., 0.))
    deep = bd.Box(1., 1., 1.).translate((-535., 41.56, 0.))
    back = bd.Box(1., 1., 1.).translate((-535., 39., 0.))
    assert overlap(mouth, cap) < .001 and overlap(mouth, prototype) < .001
    assert overlap(deep, full["thruster_0_throat"]) > .001
    assert overlap(back, cap) > .001, "detailed nozzle pierces cap"

    for label, part in full.items():
        if label in focus:
            assert same_solid(part, focus[label]), (label, "focus differs")
        moved = label == "turning_cap" or label.startswith("thruster_")
        restored = apart[label].translate((OFFSET, 0, 0)) if moved else apart[label]
        assert same_solid(part, restored), (label, "separated geometry changed")
    for label in ("body", "turning_cap", "main_nozzle", "aft_fin_0",
                  "thruster_0", "thruster_0_throat"):
        part = full[label]
        assert not topology_errors(part), (label, "invalid topology")
        assert len(part.shells()) == 1 and not boundary_edges(part.shells()[0]), (label, "open shell")
        assert not self_intersections(part), (label, "self intersection")
    radial_envelope = max(radial_max(part) for part in full.values())
    assert abs(radial_envelope-79.) < .1
    result = {"ok": True, "total_length_mm": 1200., "cap_length_mm": 130.,
              "barrel_and_cap_radius_mm": RADIUS, "body_station_radii_mm": stations,
              "cap_station_radii_mm": cap_stations,
              "maximum_radial_envelope_mm": round(radial_envelope, 3),
              "pointed_nose_exactly_preserved": True,
              "fin_roots_attached_to_narrow_barrel": True,
              "cap_nozzle_stations_x_mm": nozzles,
              "nozzle_and_stage_geometry_preserved": True}
    (ROOT / "reviews" / "spear_uniform_barrel_checks.json").write_text(
        json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print("PASS: constant 54.56 mm barrel and cap, nose/fins/motor stages checked")


if __name__ == "__main__":
    main()
