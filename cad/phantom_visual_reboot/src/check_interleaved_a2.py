"""A2 full A-family checks plus saved additive housing/support regression."""
import json
import build123d as bd
from check_interleaved_a import main, ROOT, difference, volume


def support_regression():
    report = {'scope': 'saved A2 vs A and direct housing support volumes', 'states': {}, 'supports': [], 'failures': []}
    for state in ('Stowed', 'Module_Stowed', 'Midfold', 'Deployed'):
        old = {p.label:p for p in bd.import_step(ROOT/f'STEP/O_Interleaved_A_{state}.step').children}
        new = {p.label:p for p in bd.import_step(ROOT/f'STEP/O_Interleaved_A2_{state}.step').children}
        assert set(old) == set(new)
        deltas = {n:difference(old[n],new[n]) for n in old if n != 'supported_housing'}
        removed = volume(old['supported_housing']-new['supported_housing'])
        report['states'][state] = {'unchanged_parts_difference_mm3': deltas, 'housing_removed_mm3': removed}
        if max(deltas.values()) > .01 or removed > .001:
            report['failures'].append([state, 'original geometry changed'])
    housing = new['supported_housing']
    # Independent required primitive extents, not imported from generator.
    extents = [(-300,250,-44,-42,88,93)]
    extents += [(x-5,x+5,-70,-42,88,93) for x in (-250,-50,150)]
    extents += [(x-5,x+5,-20,-18,88,93) for x in (190,225)]
    for bounds in extents:
        x0,x1,y0,y1,z0,z1 = bounds
        block = bd.Box(x1-x0,y1-y0,z1-z0).translate(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))
        missing = volume(block-housing)
        report['supports'].append({'bounds_mm':bounds, 'missing_volume_mm3':missing})
        if missing > .001:
            report['failures'].append([bounds,'missing support material',missing])
    report['passed'] = not report['failures']
    (ROOT/'reviews/interleaved_a2_support_checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('A2 saved support regression:', report['passed'], flush=True)
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    support_regression()
    main('O_Interleaved_A2','interleaved_a2_checks.json')
