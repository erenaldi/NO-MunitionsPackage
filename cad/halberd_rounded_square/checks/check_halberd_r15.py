"""Saved-artifact checks for the R15 four-face service-cover propagation.

Validates against the preserved R14 artifact: all 26 non-body parts Boolean and
color identical; the main body loses exactly three 124x30x1.2 mm seats that are
rigid rotated copies of the R13 seat; the four cover families are rigid rotated
copies of the saved R14 originals with correct local recess depths; every detail
part contacts the body, stays inside the R12 undetailed skin, and the twelve new
parts avoid every non-body baseline part; the four intake channels stay open;
separated -340 X transforms; 3370 mm length; material sidecars hash-bound with
resolved properties; the focus crop is an exact clip of the saved full document;
and every saved full/focus placement passes single-solid, positive-volume,
topology, closed-shell and self-intersection checks (no sampling).
"""
import json
from itertools import combinations
from cadgen import build123d as bd, read_scene
from cadgen.geometry import topology_errors, boundary_edges, self_intersections
from check_halberd_r8 import ROOT, load, close, identical, volume, point, occupied

MAIN = "main_body_intake_r12"
COVERS = tuple(f"main_service_cover_{i}" for i in range(1, 5))
BORDERS = tuple(f"main_service_border_{i}" for i in range(1, 5))
FASTENERS = tuple(f"main_service_fastener_{i}" for i in range(1, 9))
SERVICE = COVERS + BORDERS + FASTENERS
NEW_SERVICE = COVERS[1:] + BORDERS[1:] + FASTENERS[2:]
FINISHES = {f"main_intake_dark_recess_{i}": "interior" for i in range(1, 5)}
FINISHES.update({f"main_intake_dark_floor_{i}": "occlusion" for i in range(1, 5)})
FINISHES.update({"main_nozzle_dark_recess": "interior", "booster_nozzle_dark_recess": "interior",
                 "main_nozzle_dark_floor": "occlusion", "booster_nozzle_dark_floor": "occlusion"})
DETAIL_ROLES = {f"main_service_cover_{i}": "detail_paint" for i in range(1, 5)}
DETAIL_ROLES.update({f"main_service_border_{i}": "detail_border" for i in range(1, 5)})
DETAIL_ROLES.update({f"main_service_fastener_{i}": "detail_metal" for i in range(1, 9)})
FOCUS_CLIP = bd.Box(220., 320., 320.).translate((-320., 0, 0))


def boxes_overlap(a, b):
    aa, bb = a.bounding_box(), b.bounding_box()
    return not (aa.max.X < bb.min.X or bb.max.X < aa.min.X or
                aa.max.Y < bb.min.Y or bb.max.Y < aa.min.Y or
                aa.max.Z < bb.min.Z or bb.max.Z < aa.min.Z)


def check_native(name, count):
    scene = read_scene(ROOT / "STEP" / (name + ".step"))
    sidecar = json.loads((ROOT / "STEP" / (name + ".step.json")).read_text())
    assert sidecar["documentHash"] == scene.document_hash, "material sidecar is stale"
    appearance = sidecar["appearance"]
    expected = dict(FINISHES)
    expected.update(DETAIL_ROLES)
    assert len(appearance["assignments"]) == len(expected) == 28
    r12 = json.loads((ROOT / "STEP" / "halberd_r12.step.json").read_text())["appearance"]["materials"]
    authority = {role: dict(metalness=r12[role]["metalness"], roughness=r12[role]["roughness"],
                            name=r12[role]["name"]) for role in ("interior", "occlusion")}
    authority.update({
        "detail_paint": dict(metalness=.15, roughness=.65, name="Service cover paint"),
        "detail_border": dict(metalness=.05, roughness=.9, name="Recessed joint"),
        "detail_metal": dict(metalness=.65, roughness=.38, name="Small metallic hardware"),
    })
    for role in ("interior", "occlusion"):
        inherited = appearance["materials"][role]
        assert inherited["metalness"] == authority[role]["metalness"], role
        assert inherited["roughness"] == authority[role]["roughness"], role
        assert inherited["name"] == authority[role]["name"], role
    rows = []
    for leaf in scene.leaves():
        shape = scene.resolve(leaf.ref).shape()
        assert len(shape.solids()) == 1 and shape.volume > 0, leaf.label
        assert not topology_errors(shape), leaf.label
        assert all(not boundary_edges(shell) for shell in shape.shells()), leaf.label
        assert not self_intersections(shape), leaf.label
        if leaf.label in expected:
            assigned = appearance["assignments"][leaf.ref.lstrip("#")]
            resolved = appearance["materials"][assigned]
            want = authority[expected[leaf.label]]
            assert resolved["metalness"] == want["metalness"], leaf.label
            assert resolved["roughness"] == want["roughness"], leaf.label
            assert resolved["name"] == want["name"], leaf.label
        rows.append(dict(label=leaf.label, ref=leaf.ref, volume_mm3=shape.volume))
    assert len(rows) == count
    return dict(document=name, document_hash=scene.document_hash, placements=rows)


def check_focus_native(name, count):
    scene = read_scene(ROOT / "STEP" / (name + ".step"))
    sidecar = json.loads((ROOT / "STEP" / (name + ".step.json")).read_text())
    assert sidecar["documentHash"] == scene.document_hash, "material sidecar is stale"
    appearance = sidecar["appearance"]
    assert len(appearance["assignments"]) == len(DETAIL_ROLES) == 16
    authority = {
        "detail_paint": dict(metalness=.15, roughness=.65, name="Service cover paint"),
        "detail_border": dict(metalness=.05, roughness=.9, name="Recessed joint"),
        "detail_metal": dict(metalness=.65, roughness=.38, name="Small metallic hardware"),
    }
    rows = []
    for leaf in scene.leaves():
        shape = scene.resolve(leaf.ref).shape()
        assert len(shape.solids()) == 1 and shape.volume > 0, leaf.label
        assert not topology_errors(shape), leaf.label
        assert all(not boundary_edges(shell) for shell in shape.shells()), leaf.label
        assert not self_intersections(shape), leaf.label
        if leaf.label in DETAIL_ROLES:
            assigned = appearance["assignments"][leaf.ref.lstrip("#")]
            resolved = appearance["materials"][assigned]
            want = authority[DETAIL_ROLES[leaf.label]]
            assert resolved["metalness"] == want["metalness"], leaf.label
            assert resolved["roughness"] == want["roughness"], leaf.label
            assert resolved["name"] == want["name"], leaf.label
        rows.append(dict(label=leaf.label, ref=leaf.ref, volume_mm3=shape.volume))
    assert len(rows) == count
    return dict(document=name, placements=rows)


def check_focus_matches(name, full, selected):
    """The review crop must show the actual saved full model, not a surrogate."""
    _, cropped = load(name)
    assert set(cropped) == set(selected)
    for label in selected:
        expected = full[label] & FOCUS_CLIP
        identical(cropped[label], expected)
        assert tuple(cropped[label].color) == tuple(full[label].color), label


if __name__ == "__main__":
    path = ROOT / "reviews" / "halberd_R15_checks.json"
    path.write_text(json.dumps({"ok": False, "status": "Checks incomplete"}) + "\n")
    model, p = load("halberd_r15")
    _, q = load("halberd_r15_separated")
    _, old = load("halberd_r14")
    _, r12 = load("halberd_r12")
    assert set(p) == set(q) == set(old) | set(NEW_SERVICE) and len(p) == 39
    main = p[MAIN]
    assert tuple(main.color) == tuple(old[MAIN].color), "main body finish changed"
    for name, shape in p.items():
        if name in old and name != MAIN:
            identical(shape, old[name])
            assert tuple(shape.color) == tuple(old[name].color), name
        restored = q[name].moved(bd.Location((340, 0, 0))) if name.startswith("booster") else q[name]
        identical(shape, restored)
    # Exactly three new seats, each a rigid rotated copy of the R13 seat.
    removed = old[MAIN] - main
    assert volume(main - old[MAIN]) < .01, "main body gained volume"
    seat1 = r12[MAIN] - old[MAIN]
    sb = seat1.bounding_box()
    close(sb.min.Z, 98.8)
    close(sb.max.Z, 100.)
    close(sb.size.Z, 1.2)
    close(sb.min.X, -382.)
    close(sb.max.X, -258.)
    close(sb.size.Y, 30.)
    seats = removed.solids()
    assert len(seats) == 3, "expected exactly three new seats"
    for solid in seats:
        restored = [solid.rotate(bd.Axis.X, clock) for clock in (90., 180., 270.)]
        assert any(volume(r - seat1) < .05 and volume(seat1 - r) < .05 for r in restored), \
            "seat is not a rigid rotated copy of the R13 seat"
    # Four copies of the original detail family, correct local recess depths.
    contacts = {}
    for i in range(1, 5):
        clock = (i - 1) * 90.
        cover = p[f"main_service_cover_{i}"].rotate(bd.Axis.X, clock)
        border = p[f"main_service_border_{i}"].rotate(bd.Axis.X, clock)
        identical(cover, old["main_service_cover_1"])
        identical(border, old["main_service_border_1"])
        assert tuple(p[f"main_service_cover_{i}"].color) == tuple(old["main_service_cover_1"].color)
        assert tuple(p[f"main_service_border_{i}"].color) == tuple(old["main_service_border_1"].color)
        close(cover.bounding_box().max.Z, 99.85)
        close(border.bounding_box().max.Z, 99.1)
        assert volume(cover & border) < .01, (i, "cover/border overlap")
        for j, x in enumerate((-368., -272.), 2 * i - 1):
            screw = p[f"main_service_fastener_{j}"].rotate(bd.Axis.X, clock)
            identical(screw, old[f"main_service_fastener_{j - 2 * (i - 1)}"])
            assert tuple(p[f"main_service_fastener_{j}"].color) == \
                tuple(old[f"main_service_fastener_{j - 2 * (i - 1)}"].color)
            close(screw.bounding_box().max.Z, 99.65)
            assert not occupied((x, 0, 99.55), [screw]), "slot missing"
            assert occupied((x + .65, 0, 99.55), [screw]), "head missing"
            assert volume(screw & cover) < .01, (j, "fastener intersects countersink")
    for name in SERVICE:
        assert volume(p[name] - r12[MAIN]) < .01, (name, "detail changes approved outer silhouette")
        contact = volume(p[name] & main)
        assert contact > .01, (name, "unseated detail")
        contacts[name] = contact
    # Repeated details may contact their seats, but not intersect one another.
    for first, second in combinations(SERVICE, 2):
        if boxes_overlap(p[first], p[second]):
            assert volume(p[first] & p[second]) < .01, (first, second, "detail/detail interference")
    # The twelve new parts must avoid every non-body baseline part.
    nonbody = [name for name in old if name != MAIN]
    for name in NEW_SERVICE:
        for other in nonbody:
            if boxes_overlap(p[name], old[other]):
                assert volume(p[name] & old[other]) < .01, (name, other, "interference")
    # All four intake channels stay open through the panel station.
    for i in range(1, 5):
        back = max(v.X for v in p[f"main_intake_dark_floor_{i}"].vertices())
        for x in (back + .1, -300., -100., 100., 400., 560.):
            assert not occupied(point(x, 120., 45. + 90 * (i - 1)),
                                [main, p[f"main_intake_dark_recess_{i}"], p[f"main_intake_dark_floor_{i}"]])
    close(model.bounding_box().size.X, 3370.)
    check_focus_matches("halberd_r15_focus", p, (MAIN, *SERVICE))
    native = [check_native("halberd_r15", 39), check_native("halberd_r15_separated", 39),
              check_focus_native("halberd_r15_focus", 17)]
    report = dict(ok=True, parts_per_state=39, unchanged_R14_parts=26,
                  new_seats=3, seat_depth_mm=1.2, service_detail_parts=16,
                  cover_recess_mm=.15, fastener_recess_mm=.35,
                  contact_volumes_mm3=contacts, native_placement_checks=native)
    path.write_text(json.dumps(report, indent=2) + "\n")
    print("PASS: 26 unchanged R14 parts exact; three 1.2 mm seats; four rigid cover")
    print("families with real slots; no silhouette expansion or baseline interference;")
    print("open channels, stage transforms, materials and 95 valid placements.")
