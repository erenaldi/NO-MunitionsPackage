"""A2 — A housing with approved additive reinforcement, fused one solid.

Same body, panel factories, X/Y pose law, layer heights (5.5 mm offset) and
hardware formulas as A (interleaved_wing_a). Only the dorsal housing changes:
the original A housing is retained whole and fused with the probe-passed
additive support material (reviews/a_outer_support_probe.json,
reviews/a_track_support_probe.json):

- second continuous web  X -300..250, Y -44..-42, Z 88..93 (21-sample pass);
- three cross ribs at X -250 / -50 / 150, each X+-5, Y -70..-42, Z 88..93,
  joining the original outer wall (Y -74..-70) to the new web;
- two inner-guide posts centred X 190 / 225, each X+-5, Y -20..-18, Z 88..93
  (probe-passed stations).

Positive X is FORWARD. Not production approval.
"""
from cadgen import build123d as bd, step
from interleaved_wing_a import (LAYERS, pose, place_panel, box, tag, cylinder,
                                body, housing as a_housing,
                                components as a_components)

WEB = (-300.0, 250.0, -44.0, -42.0, 88.0, 93.0)
RIB_STATIONS = (-250.0, -50.0, 150.0)
POST_STATIONS = (190.0, 225.0)
HALF = 5.0


def housing():
    h = a_housing()
    h = h + box(*WEB)
    for x in RIB_STATIONS:
        h = h + box(x - HALF, x + HALF, -70.0, -42.0, 88.0, 93.0)
    for x in POST_STATIONS:
        h = h + box(x - HALF, x + HALF, -20.0, -18.0, 88.0, 93.0)
    return tag(h.clean(), 'supported_housing', '#697B84')


def components(fraction):
    parts = a_components(fraction)
    housing_parts = [p for p in parts if getattr(p, 'label', None) == 'supported_housing']
    if len(housing_parts) != 1:
        raise RuntimeError('expected exactly one A housing part, found %d' % len(housing_parts))
    parts = [p for p in parts if getattr(p, 'label', None) != 'supported_housing']
    parts.insert(0, housing())
    return parts


def assembly(fraction, full=True):
    parts = components(fraction)
    if full:
        parts.insert(0, body())
    return bd.Compound(children=parts, label='Phantom_interleaved_A2')


@step(out='../STEP/O_Interleaved_A2_Stowed.step')
def stowed():
    return assembly(0)


@step(out='../STEP/O_Interleaved_A2_Module_Stowed.step')
def module_stowed():
    return assembly(0, False)


@step(out='../STEP/O_Interleaved_A2_Midfold.step')
def midfold():
    return assembly(.5)


@step(out='../STEP/O_Interleaved_A2_Deployed.step')
def deployed():
    return assembly(1)


if __name__ == '__main__':
    stowed()
    module_stowed()
    midfold()
    deployed()