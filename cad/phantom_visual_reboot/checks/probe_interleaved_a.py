"""In-memory A packing gate only; never rebuild or modify N artifacts."""
import itertools
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import build123d as bd
import joined_wing_r3 as baseline


def housing():
    box = baseline.box
    h = box(-450, 550, -74, 74, 86, 88)
    for y in (19, 41):
        h += box(-300, 250, y-1, y+1, 88, 88.5)
    h += box(-300, 250, -74, -70, 88, 93.5)
    h += box(-300, 250, -72, -18, 93, 93.5)
    for y in (-41, -19):
        h += box(-300, 250, y-1, y+1, 93.5, 94)
    return baseline.tag(h.clean(), 'supported_housing', '#697B84')


def candidate_parts():
    old_layers, old_housing = baseline.LAYERS, baseline.housing
    try:
        baseline.LAYERS = {'starboard': (88.75, 99.25), 'port': (94.25, 104.75)}
        baseline.housing = housing
        parts = baseline.components(0)
    finally:
        baseline.LAYERS, baseline.housing = old_layers, old_housing
    saved = bd.import_step(ROOT / 'STEP/N_JoinedWing_R3_Stowed.step')
    parts.extend(p for p in saved.children if p.label.startswith('RDM9_'))
    return {p.label: p for p in parts}


def main():
    parts = candidate_parts()
    panels = {s+'_'+k for s in ('starboard', 'port') for k in ('front', 'rear')}
    failures = []
    report = {'scope': 'A in-memory stowed feasibility only; no motion or saved candidate validation',
              'parts': {}, 'pairs': [], 'supports': [], 'failures': failures}
    body = next(n for n in parts if n.startswith('RDM9_'))
    allowed = {frozenset(('supported_housing', body))}
    for side in ('starboard', 'port'):
        allowed.add(frozenset(('supported_housing', side+'_fixed_root')))
        allowed.add(frozenset((body, side+'_fixed_root')))
    report['intentional_attachment_pairs'] = [sorted(p) for p in allowed]
    for name, p in parts.items():
        b = p.bounding_box()
        radius = math.hypot(max(abs(b.min.Y), abs(b.max.Y)), max(abs(b.min.Z), abs(b.max.Z)))
        valid = bool(p.is_valid and len(p.solids()) == 1 and p.volume > 0)
        report['parts'][name] = {'valid_single_solid': valid, 'radial_bound_mm': radius}
        if not valid or radius >= 125:
            failures.append([name, 'valid/envelope', valid, radius])
    for a, b in itertools.combinations(parts, 2):
        gap = parts[a].distance_to(parts[b])
        intersection = parts[a] & parts[b] if gap < .001 else None
        overlap = 0 if intersection is None else intersection.volume
        row = {'a': a, 'b': b, 'clearance_mm': gap, 'overlap_mm3': overlap}
        report['pairs'].append(row)
        if (a in panels or b in panels) and gap <= .2:
            failures.append([a, b, 'panel clearance', gap, overlap])
        if overlap >= .001 and frozenset((a, b)) not in allowed:
            failures.append([a, b, 'unexpected overlap', overlap])
    for name in [body, *[s+'_'+k for s in ('starboard', 'port') for k in ('fixed_root', 'carriage')]]:
        gap = parts[name].distance_to(parts['supported_housing'])
        report['supports'].append({'part': name, 'housing_gap_mm': gap})
        if gap > .001:
            failures.append([name, 'unsupported', gap])
    report['passed'] = not failures
    (ROOT / 'reviews/interleaved_a_feasibility.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'passed': report['passed'], 'max_radius_mm': max(p['radial_bound_mm'] for p in report['parts'].values()),
                      'supports': report['supports'], 'failures': failures}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
