"""B clearance blocker, using saved A panels; NOT a supported B assembly."""
import itertools
import json
from pathlib import Path
import build123d as bd

ROOT = Path(__file__).resolve().parents[1]


def main():
    parts = {p.label: p for p in bd.import_step(ROOT/'STEP/O_Interleaved_A_Deployed.step').children}
    names = [s+'_'+k for s in ('starboard', 'port') for k in ('front', 'rear')]

    def panels(stroke, lift):
        return {n: parts[n].translate((0, stroke if n.startswith('starboard') else -stroke,
                                      lift if n.startswith('starboard') else 0)) for n in names}

    def evidence(stroke, lift):
        ps = panels(stroke, lift)
        rows = []
        for a, b in itertools.combinations(ps, 2):
            gap = ps[a].distance_to(ps[b])
            v = ps[a] & ps[b] if gap < .001 else None
            rows.append({'a': a, 'b': b, 'gap_mm': gap, 'overlap_mm3': 0 if v is None else v.volume})
        return rows

    initial = evidence(0, 5.5)
    # Bounded bisection for equal outward travel of both complete wing sets.
    low, high = 0., 60.
    assert min(r['gap_mm'] for r in evidence(high, 5.5)) > .2
    for _ in range(17):
        mid = (low+high)/2
        if min(r['gap_mm'] for r in evidence(mid, 5.5)) > .2:
            high = mid
        else:
            low = mid
    stroke = float(int(high)+1)
    rows = []
    for phase in ('outward', 'lift'):
        for i in range(21):
            travel = stroke*i/20 if phase == 'outward' else stroke
            lift = 0 if phase == 'outward' else 5.5*i/20
            pairs = evidence(travel, lift)
            rows.append({'phase': phase, 'fraction': i/20, 'stroke_mm_per_side': travel, 'lift_mm': lift,
                         'min_panel_gap_mm': min(r['gap_mm'] for r in pairs)})
    translated = panels(stroke, 5.5)
    # Test naive rigidly moved existing supports against the unchanged housing.
    supports = []
    for side in ('starboard', 'port'):
        for kind in ('fixed_root', 'carriage'):
            name = side+'_'+kind
            p = parts[name].translate((0, stroke if side == 'starboard' else -stroke,
                                      5.5 if side == 'starboard' else 0))
            supports.append({'part': name, 'housing_gap_mm': p.distance_to(parts['supported_housing'])})
    report = {'scope': 'B panel clearance probe, no B hardware or feasible assembly claim',
              'zero_stroke_levelled_pairs': initial, 'minimum_symmetric_stroke_bracket_mm': [low, high],
              'sampled_stroke_mm_per_side': stroke, 'lift_starboard_mm': 5.5, 'panel_samples': rows,
              'panel_only_sampled_pass': all(r['min_panel_gap_mm'] > .2 for r in rows),
              'naively_translated_support_gaps': supports,
              'deployed_width_mm': max(p.bounding_box().max.Y for p in translated.values())-min(p.bounding_box().min.Y for p in translated.values()),
              'supported_mechanism_verified': False}
    (ROOT/'reviews/levelling_b_clearance_probe.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'panel_samples'}, indent=2))


if __name__ == '__main__':
    main()
