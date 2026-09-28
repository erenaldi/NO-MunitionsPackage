"""Independent exported-shape checks for the R2 inward-biased chord doubling.

Preserves every R1 threshold (0.2 mm sampled clearance, 0.001 mm^3
intersection volume, 0.01 mm^3 part difference, 125 mm stowed radial bound,
0.001 mm bore-center distance) and adds: exact panel local-edge verification
via slab sections, exact 2x chord widths, unchanged body/static/moving
hardware vs the saved L artifacts, and changed panels vs L.
"""
import json
import math
from pathlib import Path
import build123d as bd
from OCP.BRepAdaptor import BRepAdaptor_Surface
from joined_wing_r2 import pose, STATES, FRONT_Z, REAR_Z

ROOT = Path(__file__).resolve().parents[1]
BODY = 'RDM9_R7_symmetric_body_20mm_wedge_R4'
FRONT = 'forward_lifting_panel'
REAR = 'rear_lifting_panel'
SLIDER = 'sliding_rear_root_carriage'
JOIN = 'outboard_join_pin'
STATIC = {'joined_wing_dorsal_housing', 'fixed_forward_root'}
EXPECTED = STATIC | {FRONT, REAR, SLIDER, JOIN}
# Approved R2 edges: negative local-Y edge exactly the R1 value, positive
# edge broadened inward in stow. Widths are exactly 2x the R1 widths.
EDGES = {
    FRONT: dict(length=900.0, root_neg=-30.0, root_pos=90.0,
                tip_neg=-22.0, tip_pos=66.0),
    REAR: dict(length=600.0, root_neg=-22.0, root_pos=66.0,
               tip_neg=-17.0, tip_pos=51.0),
}
OLD_WIDTHS = {FRONT: (60.0, 44.0), REAR: (44.0, 34.0)}


def volume(shape):
    return 0 if shape is None else shape.volume


def difference(a, b):
    return volume(a - b) + volume(b - a)


def bore_centers(part):
    centers = set()
    for face in part.faces():
        if face.geom_type == bd.GeomType.CYLINDER:
            cyl = BRepAdaptor_Surface(face.wrapped).Cylinder()
            if abs(cyl.Radius() - 3.75) < .0001:
                centers.add((round(cyl.Location().X(), 6), round(cyl.Location().Y(), 6)))
    assert len(centers) == 2, centers
    return centers


def assert_center(centers, point):
    assert min(math.dist(p, point) for p in centers) < .001, (centers, point)


def local(part, label, data):
    if label in (FRONT, REAR):
        key = 'front' if label == FRONT else 'rear'
        x, y = data[key]
        z = FRONT_Z if label == FRONT else REAR_Z
        return part.translate((-x, -y, -z)).rotate(bd.Axis.Z, -data[key + '_angle'])
    if label in (SLIDER, JOIN):
        x, y = data['rear' if label == SLIDER else 'joint']
        return part.translate((-x, -y, 0))
    return part


def place(part, label, data):
    if label in (FRONT, REAR):
        key = 'front' if label == FRONT else 'rear'
        z = FRONT_Z if label == FRONT else REAR_Z
        return part.rotate(bd.Axis.Z, data[key + '_angle']).translate((*data[key], z))
    if label in (SLIDER, JOIN):
        return part.translate((*data['rear' if label == SLIDER else 'joint'], 0))
    return part


def slab_extent(part, x, width=0.5):
    """Local-coordinate Y extent of the panel through a thin X slab."""
    cut = part & bd.Box(width, 1000, 1000).translate((x, 0, 0))
    box = cut.bounding_box()
    return box.min.Y, box.max.Y


def check_panel_edges(part, label, data):
    e = EDGES[label]
    length = e['length']
    canonical = local(part, label, data)
    box = canonical.bounding_box()
    # Bore cylinders (radius 12) at both ends extend the local X bbox.
    assert abs(box.min.X + 12) < .01 and abs(box.max.X - (length + 12)) < .01, (label, box.min.X, box.max.X)
    assert abs(box.min.Z) < .01 and abs(box.max.Z - 4.0) < .01, (label, box.min.Z, box.max.Z)
    # Endpoint +/-12 tabs unchanged (bore cylinders radius 12 at both ends).
    # The 0.5-wide slab also catches the adjacent polygon edges, so allow the
    # local slope over half the slab width.
    for x in (0.0, length):
        lo, hi = slab_extent(canonical, x)
        slope_neg = (e['root_neg'] + 12) / 25 if x == 0 else (e['tip_neg'] + 12) / 25
        slope_pos = (e['root_pos'] - 12) / 25 if x == 0 else (e['tip_pos'] - 12) / 25
        exp_lo = -12 + 0.25 * slope_neg
        exp_hi = 12 + 0.25 * slope_pos
        assert abs(lo - exp_lo) < .02 and abs(hi - exp_hi) < .02, (label, x, lo, hi, exp_lo, exp_hi)
    # Broad chard sections at x=25 and x=length-25: negative edge exactly old,
    # positive edge broadened; widths exactly 2x the R1 values.
    lo_root, hi_root = slab_extent(canonical, 25.0)
    assert abs(lo_root - e['root_neg']) < .05 and abs(hi_root - e['root_pos']) < .05, (label, lo_root, hi_root)
    lo_tip, hi_tip = slab_extent(canonical, length - 25.0)
    assert abs(lo_tip - e['tip_neg']) < .05 and abs(hi_tip - e['tip_pos']) < .05, (label, lo_tip, hi_tip)
    old_root, old_tip = OLD_WIDTHS[label]
    assert abs((e['root_pos'] - e['root_neg']) - 2 * old_root) < 1e-9
    assert abs((e['tip_pos'] - e['tip_neg']) - 2 * old_tip) < 1e-9
    assert e['root_neg'] == -old_root / 2 and e['tip_neg'] == -old_tip / 2
    assert e['root_pos'] == 3 * old_root / 2 and e['tip_pos'] == 3 * old_tip / 2
    return dict(root=(round(lo_root, 3), round(hi_root, 3)),
                tip=(round(lo_tip, 3), round(hi_tip, 3)))


baseline = bd.import_step(ROOT / 'STEP/J_Symmetric_Body_R7.step')
reference = {}
report = {'states': {}, 'panel_edges_mm': EDGES}
for state, fraction in STATES.items():
    print('Checking saved', state, flush=True)
    assembly = bd.import_step(ROOT / ('STEP/M_JoinedWing_R2_' + state + '.step'))
    module = bd.import_step(ROOT / ('STEP/M_JoinedWing_R2_Module_' + state + '.step'))
    old = bd.import_step(ROOT / ('STEP/L_JoinedWing_R1_' + state + '.step'))
    parts = {p.label: p for p in assembly.children}
    module_parts = {p.label: p for p in module.children}
    old_parts = {p.label: p for p in old.children}
    assert set(parts) == EXPECTED | {BODY} and set(module_parts) == EXPECTED
    for part in [*parts.values(), *module_parts.values()]:
        assert part.is_valid and len(part.solids()) == 1 and part.volume > 0, part.label
    assert abs(assembly.bounding_box().size.X - 2800) < .001
    assert difference(parts[BODY], baseline) < .01
    data = pose(fraction)
    for label in EXPECTED:
        assert difference(parts[label], module_parts[label]) < .01, label
        canonical = local(parts[label], label, data)
        if state == 'Stowed':
            reference[label] = canonical
        else:
            assert difference(canonical, reference[label]) < .01, label
    # Unchanged body and static/moving hardware vs the saved L artifacts;
    # the panels themselves must have changed.
    for label in STATIC | {SLIDER, JOIN}:
        assert difference(parts[label], old_parts[label]) < .01, label
    for label in (FRONT, REAR):
        assert difference(parts[label], old_parts[label]) > 1000, label
    for label, key, length in [(FRONT, 'front', 900), (REAR, 'rear', 600)]:
        centers = bore_centers(parts[label])
        assert_center(centers, data[key])
        assert_center(centers, data['joint'])
        assert abs(math.dist(*centers) - length) < .001
    bounds = {}
    if state == 'Stowed':
        for label, part in parts.items():
            box = part.bounding_box()
            bound = math.hypot(max(abs(box.min.Y), abs(box.max.Y)),
                               max(abs(box.min.Z), abs(box.max.Z)))
            assert bound < 125, (label, bound)
            bounds[label] = bound
    report['states'][state] = {'valid_solids': 7, 'module_valid_solids': 6,
                               'pose': data, 'stowed_radial_bounds_mm': bounds,
                               'panel_slab_extents_mm': {
                                   label: check_panel_edges(parts[label], label, data)
                                   for label in (FRONT, REAR)}}

# Pose intermediate points from the saved parts, never regenerating a panel.
sampled = []
minimum_clearance = 1e9
last_rear = 1e9
for i in range(21):
    fraction = i / 20
    print('Checking motion sample', i, 'of 20', flush=True)
    data = pose(fraction)
    assert data['rear'][0] < last_rear
    last_rear = data['rear'][0]
    parts = {label: place(part, label, data) for label, part in reference.items()}
    for label, key, length in [(FRONT, 'front', 900), (REAR, 'rear', 600)]:
        assert abs(math.dist(data[key], data['joint']) - length) < .0001
        for other in [baseline, *[p for name, p in parts.items() if name != label]]:
            assert volume(parts[label] & other) < .001, (fraction, label, other.label)
            clearance = parts[label].distance_to(other)
            assert clearance > .2, (fraction, label, other.label, clearance)
            minimum_clearance = min(minimum_clearance, clearance)
    assert volume(parts[SLIDER] & parts['joined_wing_dorsal_housing']) < .001
    assert volume(parts[JOIN] & parts['joined_wing_dorsal_housing']) < .001
    sampled.append({'fraction': fraction, 'rear_root_x': data['rear'][0],
                    'outboard_joint': data['joint']})
report['sampled_motion'] = sampled
report['minimum_sampled_panel_clearance_mm'] = minimum_clearance
report['rearward_carriage_travel_mm'] = pose(0)['rear'][0] - pose(1)['rear'][0]
report['all_rigid_parts_identical_after_inverse_pose'] = True
report['hardware_identical_to_L'] = True
report['panels_changed_vs_L'] = True
print(json.dumps(report, indent=2))
(ROOT / 'reviews/joined_wing_r2_checks.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')