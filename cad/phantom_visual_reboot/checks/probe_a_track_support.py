"""A track-support feasibility probe — direct support under the inner guide.

One narrow gate for the primary finding that the A shelf (Z93..93.5,
Y-72..-18) is supported only at the side beam Y-74..-70. Measures whether
support material under the inner guide (Y-19) is collision-free through the
21 original deployment samples, using the saved stowed parts transformed by
the checker's rigid-pose formulas (check_interleaved_a.py moved()). No
source/build changes; probe artifacts only.

Attempt 1: continuous inner web X-300..250, Y-20..-18, Z88..93 (fuses shelf
to base, directly under inner guide Y-19).
Attempt 2 (only if the web is blocked): bounded survey of up to 6 X stations
of narrow posts (X+-5, Y-20..-18, Z88..93) along the inner guide.

Thresholds match check_interleaved_a.py: panel gap > .2 mm, unexpected
overlap < .001 mm3, radial bound < 125 mm. The lower starboard rear panel is
NOT exempted. Attachment = face contact with the housing (shelf/base); any
candidate/body overlap outside the housing's own body-attachment region is
treated as unexpected.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import build123d as bd
from interleaved_wing_a import LAYERS, pose, place_panel
from joined_wing_r1 import pose as old_pose

STEP = ROOT / 'STEP/O_Interleaved_A_Stowed.step'
OUT = ROOT / 'reviews/a_track_support_probe.json'
BODY_PREFIX = 'RDM9_'
PANELS = {s + '_' + k for s in ('starboard', 'port') for k in ('front', 'rear')}
WEB = (-300.0, 250.0, -20.0, -18.0, 88.0, 93.0)
STATIONS = (-250.0, -50.0, 150.0, 190.0, 225.0, 250.0)
POST_HALF = 5.0
PANEL_GAP_MIN = 0.2
OVERLAP_MAX = 0.001
RADIUS_MAX = 125.0


def box(x0, x1, y0, y1, z0, z1):
    return bd.Box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def vol(s):
    return 0.0 if s is None else s.volume


def radial(s):
    b = s.bounding_box()
    return math.hypot(max(abs(b.min.Y), abs(b.max.Y)), max(abs(b.min.Z), abs(b.max.Z)))


def canonical(part, side, kind):
    p = old_pose(0)
    if side == 'port':
        part = part.mirror(bd.Plane.XZ)
    x, y = p[kind]
    z = LAYERS[side][0 if kind == 'rear' else 1]
    return part.translate((-x, -y + 5, -z)).rotate(bd.Axis.Z, -p[kind + '_angle'])


def main():
    base = {p.label: p for p in bd.import_step(STEP).children}
    missing = [n for n in ('supported_housing', 'starboard_rear') if n not in base]
    if missing:
        raise SystemExit('missing saved parts: ' + ', '.join(missing))
    body = next(n for n in base if n.startswith(BODY_PREFIX))
    housing = base['supported_housing']
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

    def attachment(candidate):
        gap = candidate.distance_to(housing)
        ov_housing = vol(candidate & housing)
        cand_body = candidate & base[body]
        housing_body = housing & base[body]
        outside = 0.0
        if cand_body is not None and housing_body is not None:
            outside = vol(cand_body - housing_body)
        elif cand_body is not None:
            outside = vol(cand_body)
        return {'housing_gap_mm': gap, 'housing_overlap_mm3': ov_housing,
                'body_overlap_mm3': vol(cand_body), 'body_overlap_outside_housing_mm3': outside}

    def check(candidate, name):
        samples, failures = [], []
        for i in range(21):
            f = i / 20
            sample = moved(f)
            row = {'fraction': f, 'panel_gaps_mm': {}, 'overlaps_mm3': {}}
            for label, part in sample.items():
                if label == body:
                    continue  # static; body contact handled once in attachment()
                gap = candidate.distance_to(part)
                if label in PANELS:
                    row['panel_gaps_mm'][label] = gap
                    if gap <= PANEL_GAP_MIN:
                        failures.append([name, f, label, 'panel clearance', gap])
                elif gap < 0.001:
                    ov = vol(candidate & part)
                    if ov >= OVERLAP_MAX:
                        row['overlaps_mm3'][label] = ov
                        failures.append([name, f, label, 'overlap', ov])
            samples.append(row)
        return samples, failures

    report = {
        'scope': f'A shelf support web bounds {WEB}: collision-free support '
                 'material through 21 original deployment samples (saved stowed parts, '
                 'checker rigid-pose transforms). No source/build changes.',
        'saved_source': str(STEP.relative_to(ROOT)),
        'thresholds': {'panel_gap_min_mm': PANEL_GAP_MIN, 'overlap_max_mm3': OVERLAP_MAX,
                       'radius_max_mm': RADIUS_MAX},
        'attempts': [],
    }

    # --- Attempt 1: continuous inner web. ---
    web = box(*WEB)
    web_attach = attachment(web)
    web_samples, web_failures = check(web, 'continuous_web')
    web_min_gap = min(r['panel_gaps_mm'].get('starboard_rear', 1e9) for r in web_samples)
    web_pass = not web_failures and web_attach['housing_gap_mm'] <= 0.001 \
        and web_attach['body_overlap_outside_housing_mm3'] < OVERLAP_MAX \
        and radial(web) < RADIUS_MAX
    report['attempts'].append({
        'name': 'continuous_web',
        'primitive_mm': {'x': [WEB[0], WEB[1]], 'y': [WEB[2], WEB[3]], 'z': [WEB[4], WEB[5]]},
        'radial_bound_mm': radial(web),
        'attachment': web_attach,
        'min_starboard_rear_gap_mm': web_min_gap,
        'sample_count': len(web_samples),
        'passed': web_pass,
        'failures': web_failures,
    })

    # --- Attempt 2 (only if the web is blocked): bounded post survey. ---
    posts_report = None
    if not web_pass:
        stations = []
        for x in STATIONS:
            post = box(x - POST_HALF, x + POST_HALF, WEB[2], WEB[3], WEB[4], WEB[5])
            post_attach = attachment(post)
            post_samples, post_failures = check(post, 'post_x' + str(x))
            post_min_gap = min(r['panel_gaps_mm'].get('starboard_rear', 1e9) for r in post_samples)
            post_pass = not post_failures and post_attach['housing_gap_mm'] <= 0.001 \
                and post_attach['body_overlap_outside_housing_mm3'] < OVERLAP_MAX \
                and radial(post) < RADIUS_MAX
            stations.append({
                'station_mm': x,
                'primitive_mm': {'x': [x - POST_HALF, x + POST_HALF], 'y': [WEB[2], WEB[3]],
                                 'z': [WEB[4], WEB[5]]},
                'radial_bound_mm': radial(post),
                'attachment': post_attach,
                'min_starboard_rear_gap_mm': post_min_gap,
                'passed': post_pass,
                'failures': post_failures,
            })
        viable = [s['station_mm'] for s in stations if s['passed']]
        posts_report = {
            'name': 'discrete_posts',
            'post_primitive_mm': {'x_half_width': POST_HALF, 'y': [WEB[2], WEB[3]],
                                  'z': [WEB[4], WEB[5]]},
            'stations': stations,
            'viable_stations_mm': viable,
            'passed': bool(viable),
        }
        report['attempts'].append(posts_report)

    report['verdict'] = 'BLOCKED' if not web_pass and (posts_report is None or not posts_report['passed']) \
        else 'VIABLE'
    if web_pass:
        report['selected'] = {'attempt': 'continuous_web',
                              'primitive_mm': {'x': [WEB[0], WEB[1]], 'y': [WEB[2], WEB[3]],
                                               'z': [WEB[4], WEB[5]]}}
    elif posts_report and posts_report['passed']:
        report['selected'] = {'attempt': 'discrete_posts',
                              'viable_stations_mm': posts_report['viable_stations_mm'],
                              'post_primitive_mm': posts_report['post_primitive_mm']}
    else:
        report['blocker'] = ('No support primitive under the inner guide (Y-20..-18, Z88..93) is '
                             'collision-free through all 21 samples; see per-attempt failures.')

    OUT.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'verdict': report['verdict'], 'selected': report.get('selected'),
                      'attempts': [{k: a[k] for k in ('name', 'passed', 'failures') if k in a}
                                   for a in report['attempts']]}, indent=2))


if __name__ == '__main__':
    main()
