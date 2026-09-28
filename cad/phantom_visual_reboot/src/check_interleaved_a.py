"""Saved A candidate evidence; retain all diagnostics on failure.

Validates the four saved O_Interleaved_A_* STEP files: exact body and
canonical R2 panel identity, 12/11 valid single positive solids, stowed
radius<125, panel clearances>.2, unexpected intersections<.001 (only the
explicit original fixed-attachment pairs exempt), housing/body/fixed-root and
both carriage supports, saved mid/deployed parts as rigid transforms of saved
stowed, and 21 simultaneous deployment samples with all-pair collision and
support coverage (N/R3 checker parity). No thresholds weakened.
"""
import itertools
import json
import math
from pathlib import Path
import build123d as bd
from interleaved_wing_a import LAYERS, pose, place_panel
from joined_wing_r1 import pose as old_pose

ROOT = Path(__file__).resolve().parents[1]
BODY = 'RDM9_R7_symmetric_body_20mm_wedge_R4'


def volume(s):
    return 0 if s is None else s.volume


def difference(a, b):
    return volume(a - b) + volume(b - a)


def canonical(part, side, kind):
    p = old_pose(0)
    if side == 'port':
        part = part.mirror(bd.Plane.XZ)
    x, y = p[kind]
    z = LAYERS[side][0 if kind == 'rear' else 1]
    return part.translate((-x, -y + 5, -z)).rotate(bd.Axis.Z, -p[kind + '_angle'])


def main(prefix='O_Interleaved_A', report_name='interleaved_a_checks.json'):
    full = bd.import_step(ROOT / ('STEP/' + prefix + '_Stowed.step'))
    parts = {p.label: p for p in full.children}
    module = {p.label: p for p in bd.import_step(ROOT / ('STEP/' + prefix + '_Module_Stowed.step')).children}
    old = {p.label: p for p in bd.import_step(ROOT / 'STEP/M_JoinedWing_R2_Stowed.step').children}
    panels = [side + '_' + kind for side in LAYERS for kind in ('front', 'rear')]
    failures = []
    report = {'artifact_prefix': prefix, 'scope': 'saved A-family stowed + saved-pose identity + 21 simultaneous samples; '
                       'continuous sweep, strength, actuation, locks and rack unverified',
              'parts': {}, 'module': {}, 'panel_pairs': [], 'identity_mm3': {},
              'support_contacts': [], 'saved_pose_identity': {}, 'samples': [],
              'failures': failures}

    # Exact body identity against saved R2 body.
    report['body_difference_mm3'] = difference(parts[BODY], old[BODY])
    if report['body_difference_mm3'] > .01:
        failures.append(('body changed', report['body_difference_mm3']))

    # 12 valid single positive solids (full), 11 (module); stowed radius < 125.
    if len(parts) != 12:
        failures.append(('full part count', len(parts)))
    if len(module) != 11:
        failures.append(('module part count', len(module)))
    for name, part in parts.items():
        b = part.bounding_box()
        radius = math.hypot(max(abs(b.min.Y), abs(b.max.Y)), max(abs(b.min.Z), abs(b.max.Z)))
        valid = part.is_valid and len(part.solids()) == 1 and part.volume > 0
        report['parts'][name] = {'valid_single_solid': valid, 'radial_bound_mm': radius}
        if not valid or radius >= 125:
            failures.append((name, 'valid/envelope', valid, radius))
    for name, part in module.items():
        valid = part.is_valid and len(part.solids()) == 1 and part.volume > 0
        report['module'][name] = {'valid_single_solid': valid}
        if not valid:
            failures.append((name, 'module valid', valid))
        if name not in parts or difference(part, parts[name]) > .01:
            failures.append((name, 'module/full identity mismatch'))
    if set(module) != set(parts) - {BODY}:
        failures.append(('module label mismatch', sorted(set(module) ^ (set(parts) - {BODY}))))

    # Canonical R2 panel identity.
    for side in LAYERS:
        for kind, oldname, oldz in [('front', 'forward_lifting_panel', 98), ('rear', 'rear_lifting_panel', 91)]:
            p = old_pose(0)
            x, y = p[kind]
            ref = old[oldname].translate((-x, -y, -oldz)).rotate(bd.Axis.Z, -p[kind + '_angle'])
            delta = difference(canonical(parts[side + '_' + kind], side, kind), ref)
            report['identity_mm3'][side + '_' + kind] = delta
            if delta > .01:
                failures.append((side, kind, 'panel identity', delta))

    # All-pair clearances/intersections; only explicit original fixed attachments exempt.
    allowed = {frozenset(('supported_housing', BODY))}
    for side in ('starboard', 'port'):
        allowed.add(frozenset(('supported_housing', side + '_fixed_root')))
        allowed.add(frozenset((BODY, side + '_fixed_root')))
    report['intentional_attachment_pairs'] = [sorted(p) for p in allowed]
    for a, b in itertools.combinations(parts, 2):
        gap = parts[a].distance_to(parts[b])
        overlap = volume(parts[a] & parts[b]) if gap < .001 else 0
        is_panel = a in panels or b in panels
        if is_panel:
            report['panel_pairs'].append({'a': a, 'b': b, 'clearance_mm': gap, 'overlap_mm3': overlap})
            if gap <= .2 or overlap >= .001:
                failures.append((a, b, 'interference', gap, overlap))
        if overlap >= .001 and frozenset((a, b)) not in allowed:
            failures.append((a, b, 'unexpected overlap', overlap))

    # Housing/body/fixed-root and both carriages support.
    for name in [BODY, *[side + '_' + kind for side in LAYERS for kind in ('fixed_root', 'carriage')]]:
        gap = parts[name].distance_to(parts['supported_housing'])
        overlap = volume(parts[name] & parts['supported_housing'])
        report['support_contacts'].append({'part': name, 'gap_mm': gap, 'overlap_mm3': overlap})
        if gap > .001:
            failures.append((name, 'unsupported', gap))

    # Saved mid/deployed parts are rigid transforms of saved stowed parts.
    base = dict(parts)
    canon = {side + '_' + kind: canonical(base[side + '_' + kind], side, kind)
             for side in ('port', 'starboard') for kind in ('front', 'rear')}

    def moved(f):
        result = dict(base)
        for side in ('port', 'starboard'):
            for kind in ('front', 'rear'):
                label = side + '_' + kind
                result[label] = place_panel(canon[label], side, kind, f)
            start, end = pose(0, side), pose(f, side)
            for kind, key in [('carriage', 'rear'), ('join', 'joint')]:
                dx = end[key][0] - start[key][0]
                dy = end[key][1] - start[key][1]
                result[side + '_' + kind] = base[side + '_' + kind].translate((dx, dy, 0))
        return result

    for state, f in [('Midfold', .5), ('Deployed', 1)]:
        saved = {p.label: p for p in bd.import_step(ROOT / ('STEP/' + prefix + '_' + state + '.step')).children}
        expected = moved(f)
        if set(saved) != set(expected):
            failures.append((state, 'label mismatch', sorted(set(saved) ^ set(expected))))
            continue
        invalid = [l for l, p in saved.items() if not (p.is_valid and len(p.solids()) == 1 and p.volume > 0)]
        if invalid:
            failures.append((state, 'invalid saved parts', invalid))
        deltas = {label: difference(saved[label], p) for label, p in expected.items()}
        report['saved_pose_identity'][state] = deltas
        bad = {l: d for l, d in deltas.items() if d > .01}
        if bad:
            failures.append((state, 'pose identity', bad))

    # 21 simultaneous deployment samples; all-pair collision and support coverage.
    for i in range(21):
        print('Motion sample', i, '/20', flush=True)
        sample = moved(i / 20)
        minimum = 1e9
        for a, b in itertools.combinations(sample, 2):
            is_panel = a in panels or b in panels
            gap = sample[a].distance_to(sample[b])
            if is_panel:
                minimum = min(minimum, gap)
                if gap <= .2:
                    failures.append([i / 20, a, b, 'panel clearance', gap])
            support_pair = (a == 'supported_housing' and (b.endswith('fixed_root') or b.startswith('RDM9_'))) or \
                           (b == 'supported_housing' and (a.endswith('fixed_root') or a.startswith('RDM9_')))
            support_pair = support_pair or (a.startswith('RDM9_') and b.endswith('fixed_root')) or \
                           (b.startswith('RDM9_') and a.endswith('fixed_root'))
            if gap < .001 and not support_pair:
                overlap = volume(sample[a] & sample[b])
                if overlap >= .001:
                    failures.append([i / 20, a, b, 'overlap', overlap])
        for side in ('port', 'starboard'):
            gap = sample[side + '_carriage'].distance_to(sample['supported_housing'])
            if gap > .001:
                failures.append([i / 20, side, 'carriage support', gap])
        report['samples'].append({'fraction': i / 20, 'minimum_panel_clearance_mm': minimum})

    report['passed'] = not failures
    (ROOT / 'reviews' / report_name).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': not failures, 'failures': failures}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
