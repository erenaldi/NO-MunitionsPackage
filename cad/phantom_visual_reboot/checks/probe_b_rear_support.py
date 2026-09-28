"""B rear-support mechanism gate — measurement first, no B assembly.

One bounded feasibility probe for the primary-selected B mechanism on the
starboard rear root only: replace the starboard rear carriage with (1) a
longitudinal shoe on the existing guides, (2) a captive transverse tongue
sliding 22 mm, (3) a telescoping vertical stem lifting the rear pivot 5.5 mm.

This gate measures the stowed vertical budget under the starboard rear root
from the saved A STEP (STEP/O_Interleaved_A_Stowed.step) and decides whether a
credible captive stage can exist at all. If the budget blocks a credible
package, the probe reports measured dimensions and stops; it does not force
zero-thickness/floating/overlapping stages or new layer heights. No B
assembly is built and no feasible-assembly claim is made.
"""
import json
from pathlib import Path
import build123d as bd

ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / 'STEP/O_Interleaved_A_Stowed.step'
OUT = ROOT / 'reviews/b_rear_support_probe.json'

# Trial stage thicknesses (assumptions, NOT universal engineering minima).
# This stacked architecture is only one possible B support arrangement.
SHOE_MIN = 0.5
# Assumed transverse plate including retention shoulders.
TONGUE_MIN = 1.0
# Assumed retracted stem footprint; telescopic construction is not modelled.
STEM_MIN = 2.0
# Task-minimum moving clearance per sliding interface.
CLEARANCE = 0.25


def vol(s):
    return 0.0 if s is None else s.volume


def top_z(s):
    return None if s is None else s.bounding_box().max.Z


def main():
    parts = {p.label: p for p in bd.import_step(STEP).children}
    missing = [n for n in ('starboard_rear', 'supported_housing', 'starboard_carriage') if n not in parts]
    if missing:
        raise SystemExit('missing saved parts: ' + ', '.join(missing))

    panel = parts['starboard_rear']
    housing = parts['supported_housing']
    carriage = parts['starboard_carriage']

    # --- 1. Starboard rear panel: bottom/top Z and root XY (stowed). ---
    pb = panel.bounding_box()
    panel_z_min, panel_z_max = pb.min.Z, pb.max.Z
    # Root bore centre: carriage slab bbox centre (slab is X170..230, Y22..38).
    cb = carriage.bounding_box()
    root_x, root_y = (cb.min.X + cb.max.X) / 2, (cb.min.Y + cb.max.Y) / 2

    # --- 2. Housing top under the starboard rear root region. ---
    region = bd.Box(60, 16, 11).translate((root_x, root_y, 90.5))  # X+-30, Y+-8, Z85..96
    housing_top_under_root = top_z(housing & region)

    # --- 3. Existing guide tops (Y18..20 and Y40..42, X-300..250). ---
    guide_tops = {}
    for gy in (19, 41):
        g = bd.Box(550, 2, 11).translate((-25, gy, 90.5))
        guide_tops[gy] = top_z(housing & g)

    # --- 4. Current carriage slab top (lowest solid portion, avoiding the
    # pivot cylinder r3.5 at the root centre: sample Y22..26.5 slab-only band). ---
    slab = carriage & bd.Box(60, 4, 2).translate((root_x, root_y - 8, 88))
    carriage_slab_top = top_z(slab)

    # --- 5. Vertical budgets. ---
    budget_base_to_panel = panel_z_min - housing_top_under_root
    budget_guide_to_panel = panel_z_min - max(v for v in guide_tops.values() if v is not None)

    # --- 6. Credible package height estimate (stowed, retracted). ---
    package_floor = SHOE_MIN + CLEARANCE + TONGUE_MIN + CLEARANCE + STEM_MIN
    package_realistic = 1.0 + CLEARANCE + 1.0 + CLEARANCE + 2.0  # shoe on guides
    fits = budget_base_to_panel >= package_floor

    report = {
        'scope': 'B starboard-rear support mechanism gate: stowed vertical budget '
                 'under the starboard rear root vs shoe/tongue/stem package; '
                 'measurement first, no B assembly, no feasibility claim',
        'mechanism_under_study': {
            'stage1': 'longitudinal shoe on existing guides (Y18..20, Y40..42, Z88..88.5)',
            'stage2': 'captive transverse tongue sliding 22 mm',
            'stage3': 'telescoping vertical stem lifting rear pivot 5.5 mm',
            'probe_constraints_not_additional_user_locks': ['A stowed layer heights', 'fixed base/body',
                                   'panel geometry unchanged', 'no cutouts in panels/body',
                                   'min 0.25 mm moving clearance', 'radius 125 envelope']},
        'saved_source': str(STEP.relative_to(ROOT)),
        'measurements_mm': {
            'starboard_rear_panel_z_bottom': panel_z_min,
            'starboard_rear_panel_z_top': panel_z_max,
            'starboard_rear_root_xy': [root_x, root_y],
            'housing_top_z_under_root_region': housing_top_under_root,
            'existing_guide_top_z': guide_tops,
            'current_carriage_slab_top_z': carriage_slab_top,
            'current_carriage_bbox_z': [cb.min.Z, cb.max.Z],
            'budget_housing_top_to_panel_bottom': budget_base_to_panel,
            'budget_guide_top_to_panel_bottom': budget_guide_to_panel},
        'package_assumptions_mm': {
            'shoe_min': SHOE_MIN, 'tongue_min': TONGUE_MIN, 'stem_retracted_min': STEM_MIN,
            'moving_clearance_each': CLEARANCE,
            'package_floor_height': package_floor,
            'package_realistic_height': package_realistic},
        'verdict': 'BLOCKED' if not fits else 'FITS',
        'limitations': 'Only the selected serially stacked package is rejected. No stage solids, retention or motion were built. Alternative side-supported/cam/linkage layouts and revised layer heights remain untested; body/panels/envelope remain user locks.',
        'blocker': None,
        'end_state_probe': 'not run (blocked at measurement gate)' if not fits else 'pending',
    }

    if not fits:
        report['blocker'] = (
            'Stowed vertical space under the starboard rear root is only '
            f'{budget_base_to_panel:.2f} mm (housing top {housing_top_under_root:.2f} -> panel '
            f'bottom {panel_z_min:.2f}); the existing guides already occupy Z88..88.5, leaving '
            f'{budget_guide_to_panel:.2f} mm above them. The current carriage slab '
            f'(Z{cb.min.Z:.2f}..{carriage_slab_top:.2f}) already fills the between-guide height. '
            f'The assumed stacked package totals {package_floor:.2f} mm '
            f'(shoe {SHOE_MIN} + clearance {CLEARANCE} + tongue {TONGUE_MIN} + clearance '
            f'{CLEARANCE} + retracted stem {STEM_MIN}), i.e. {package_floor / budget_base_to_panel:.1f}x '
            'the available budget; the alternate assumed on-guide package totals '
            f'{package_realistic:.2f} mm. No zero-thickness/floating/overlapping stage or new '
            'layer height is allowed in this probe, so this assumed package does not fit '
            'the current A geometry. This does not prove B impossible.')
    else:
        report['end_state_probe'] = 'not implemented in this gate (fit check passed unexpectedly)'

    OUT.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
