"""Independent checks against exported paired STEPs; no generator imports."""

import argparse
import json
import math
from pathlib import Path

from cadgen import build123d as bd, read_step


ROOT = Path(__file__).resolve().parents[1]
NAMES = {"A": "Facet", "B": "Shoulder", "C": "Keel"}
EXPECTED = {"faceted_body", "flush_rf_port", "flush_rf_starboard",
            "hinge_seat_port", "hinge_seat_starboard",
            "wing_port", "wing_starboard"} | {
                "tail_fin_%03d" % angle for angle in (45, 135, 225, 315)}
HINGE_X = {"A": -120., "B": -40., "C": -220.}


def leaves(shape):
    if shape.children:
        return [leaf for child in shape.children for leaf in leaves(child)]
    return [shape]


def close(a, b, tolerance=0.003):
    assert abs(a-b) <= tolerance, (a, b)


def check(key):
    states = {}
    models = {}
    for pose in ("deployed", "stowed"):
        target = ROOT / "STEP" / ("%s_%s_%s.step" % (key, NAMES[key], pose.title()))
        model = read_step(target)
        parts = {part.label: part for part in leaves(model)}
        assert len(parts) == len(EXPECTED) == len(leaves(model)), (pose, set(parts))
        assert set(parts) == EXPECTED, (pose, set(parts)^EXPECTED)
        bounds = model.bounding_box()
        close(bounds.min.X, -1400., .005)
        close(bounds.max.X, 1400., .005)
        largest_radius = 0.
        radius_by_part = {}
        for label, part in parts.items():
            assert part.is_valid and len(part.solids()) == 1 and part.volume > 0, label
            radius = max(math.hypot(vertex.center().Y, vertex.center().Z)
                         for vertex in part.vertices())
            radius_by_part[label] = round(radius, 4)
            largest_radius = max(largest_radius, radius)
            if pose == "stowed":
                assert radius <= 125.001, (key, label, radius)
        states[pose] = dict(path=str(target.relative_to(ROOT)),
                            length_mm=bounds.size.X,
                            max_vertex_radius_mm=round(largest_radius, 4),
                            radius_by_part_mm=radius_by_part)
        models[pose] = parts

    deployed, stowed = models["deployed"], models["stowed"]
    host = deployed["faceted_body"]
    pose_identity = {}
    for label in sorted(EXPECTED):
        a, b = deployed[label], stowed[label]
        close(a.volume, b.volume, max(.01, a.volume * 1e-7))
        if label.startswith("wing_"):
            y = 14. if label == "wing_starboard" else -14.
            axis = bd.Axis((HINGE_X[key], y, 0), (0, 0, 1))
            b = b.rotate(axis, 90.)
        elif label.startswith("tail_fin_"):
            angle = int(label.rsplit("_", 1)[-1])
            theta = math.radians(angle)
            axis = bd.Axis((0., 55.*math.sin(theta), 55.*math.cos(theta)), (1, 0, 0))
            fold = 75. if math.sin(theta)*math.cos(theta) > 0 else -75.
            b = b.rotate(axis, -fold)
        difference = (a - b).volume + (b - a).volume
        assert difference <= max(.02, a.volume*1e-7), (key, label, difference)
        pose_identity[label] = round(difference, 6)
    for pose, parts in models.items():
        for side in ("port", "starboard"):
            seat = parts["hinge_seat_" + side]
            wing = parts["wing_" + side]
            assert (seat & parts["faceted_body"]).volume > 1., (key, pose, side, "seat")
            assert (seat & wing).volume > 1., (key, pose, side, "wing")
        for angle in (45, 135, 225, 315):
            fin = parts["tail_fin_%03d" % angle]
            assert (fin & parts["faceted_body"]).volume > 1., (key, pose, angle, "fin root")
            if pose == "stowed":
                assert (fin - parts["faceted_body"]).volume > fin.volume*.45, (
                    key, angle, "folded fin swallowed by body")
    # Side panels remain mirror-balanced about the midplane in both states.
    for pose, parts in models.items():
        close(parts["flush_rf_port"].volume, parts["flush_rf_starboard"].volume)
    mock = None
    if key == "A":
        context = {p.label: p for p in leaves(read_step(ROOT / "STEP" / "A_Facet_Stowed_MockPad.step"))}
        pad = context.pop("MOCK_700x80_pylon_pad_NOT_DONOR")
        assert set(context) == EXPECTED
        overlap = {}
        for label, part in context.items():
            intersection = part & pad
            overlap[label] = intersection.volume if intersection else 0.
        assert max(overlap.values()) < .01, ("mock pad collision", overlap)
        mock = dict(label="R5-derived mock pad, not donor rack", zero_overlap=True,
                    pad_floor_mm=round(pad.bounding_box().min.Z, 4))
    return dict(key=key, ok=True, occurrences=len(EXPECTED), states=states,
                inverse_pose_symmetric_difference_mm3=pose_identity,
                wing_seat_contacts=True, mock_pad=mock)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("keys", nargs="*", choices=NAMES)
    keys = parser.parse_args().keys or list(NAMES)
    results = [check(key) for key in keys]
    output = ROOT / "reviews" / ("checks_" + "".join(keys) + ".json")
    output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([dict(key=result["key"], ok=True,
                           stowed_radius_mm=result["states"]["stowed"]["max_vertex_radius_mm"])
                      for result in results]))
