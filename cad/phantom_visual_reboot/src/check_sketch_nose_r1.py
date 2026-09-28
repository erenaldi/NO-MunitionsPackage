"""Independent exported-STEP checks for the user-drawn D square/nose prototype."""

import json
import math
from pathlib import Path

from cadgen import build123d as bd, read_step


ROOT = Path(__file__).resolve().parents[1]
PARTS = {"square_body_chined_nose", "flush_rf_port", "flush_rf_starboard",
         "hinge_seat_port", "hinge_seat_starboard", "wing_port", "wing_starboard"} | {
             "tail_fin_%03d" % a for a in (45, 135, 225, 315)}


def leaves(shape):
    if shape.children:
        return [item for child in shape.children for item in leaves(child)]
    return [shape]


def near(a, b, tolerance=.005):
    assert abs(a-b) <= tolerance, (a, b)


def cross(body, x):
    plane = bd.Plane(origin=(x, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    faces = bd.section(body, section_by=plane).faces()
    assert len(faces) == 1, (x, len(faces))
    return faces[0]


def main():
    poses = {}
    facts = {}
    for state in ("deployed", "stowed"):
        source = ROOT / "STEP" / ("D_SketchNose_R1_%s.step" % state.title())
        shape = read_step(source)
        parts = {p.label: p for p in leaves(shape)}
        assert set(parts) == PARTS and len(leaves(shape)) == len(PARTS)
        overall = shape.bounding_box()
        near(overall.min.X, -1400)
        near(overall.max.X, 1400)
        maxima = {}
        for name, part in parts.items():
            assert part.is_valid and len(part.solids()) == 1 and part.volume > 0, name
            maxima[name] = max(math.hypot(v.center().Y, v.center().Z) for v in part.vertices())
            if state == "stowed":
                assert maxima[name] <= 125.001, (name, maxima[name])
        poses[state] = parts
        facts[state] = dict(length_mm=overall.size.X,
                            radial_max_mm=round(max(maxima.values()), 4),
                            by_part_mm={k:round(v,4) for k,v in maxima.items()})

    deployed, stowed = poses["deployed"], poses["stowed"]
    a = deployed["square_body_chined_nose"]
    near(a.bounding_box().size.Y, 172)
    near(a.bounding_box().size.Z, 172)
    mid = cross(a, 0)
    # An actual rounded-square midsection: 172 x 172 with four 10 mm radii.
    theoretical = 172**2 - (4-math.pi)*10**2
    near(mid.area, theoretical, .06)
    assert len(mid.outer_wire().edges()) == 8
    for x in (1000, 1160):
        face = cross(a, x)
        v = [p.center() for p in face.vertices()]
        keel = min(v, key=lambda p:p.Z)
        near(keel.Y, 0)
        side_bottom = min(p.Z for p in v if abs(p.Y) > 15)
        assert side_bottom - keel.Z >= 15, (x, side_bottom, keel.Z)
    near(min(v.center().Y for v in cross(a, 1160).vertices()), -45, .1)
    assert cross(a, 1398).area < 10., "bottom-view nose did not reach a tiny apex"
    assert cross(a, 1000).area > cross(a, 1160).area > cross(a, 1398).area

    identity = {}
    for label in sorted(PARTS):
        p, q = deployed[label], stowed[label]
        near(p.volume, q.volume, max(.02, p.volume*1e-7))
        if label.startswith("wing_"):
            offset = 14 if label.endswith("starboard") else -14
            q = q.rotate(bd.Axis((-120, offset, 0), (0, 0, 1)), 90.)
        if label.startswith("tail_fin_"):
            angle = int(label.rsplit("_", 1)[-1])
            theta = math.radians(angle)
            fold = 90. if math.sin(theta)*math.cos(theta) > 0 else -90.
            q = q.rotate(bd.Axis((0,108*math.sin(theta),108*math.cos(theta)),(1,0,0)), -fold)
        error = (p-q).volume + (q-p).volume
        assert error <= max(.03, p.volume*1e-7), (label,error)
        identity[label] = round(error,6)
    contacts = {}
    for state, parts in poses.items():
        body = parts["square_body_chined_nose"]
        for side in ("port", "starboard"):
            seat = parts["hinge_seat_"+side]
            assert (seat & body).volume > 1, (state, side, "body seat")
            assert (seat & parts["wing_"+side]).volume > 1, (state, side, "wing seat")
        for angle in (45,135,225,315):
            fin = parts["tail_fin_%03d"%angle]
            assert (fin & body).volume > 1, (state,angle,"root")
            if state == "stowed":
                assert (fin-body).volume > fin.volume*.35, (state,angle,"fin swallowed")
        contacts[state] = True

    mid_slab = read_step(ROOT / "STEP/D_SketchNose_R1_MidSection.step")
    nose_slab = read_step(ROOT / "STEP/D_SketchNose_R1_NoseSection.step")
    assert len(leaves(mid_slab)) == len(leaves(nose_slab)) == 1
    near(mid_slab.bounding_box().size.Y,172)
    near(mid_slab.bounding_box().size.Z,172)
    assert nose_slab.bounding_box().size.Y < 100
    result = dict(ok=True, states=facts, square_section_area_mm2=round(mid.area,3),
                  nose_section_1160_area_mm2=round(cross(a,1160).area,3),
                  tip_section_1398_area_mm2=round(cross(a,1398).area,3),
                  inverse_pose_symmetric_difference_mm3=identity, contacts=contacts)
    target = ROOT/"reviews/sketch_nose_r1_checks.json"
    target.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("ok","square_section_area_mm2",
                                          "nose_section_1160_area_mm2",
                                          "tip_section_1398_area_mm2")}))


if __name__ == "__main__":
    main()
