"""R2: inward-biased chord doubling of the joined fore/aft panels.

Approved bounded revision of the R1 joined side. Same body, dorsal housing,
pivots, panel layers, link lengths (900/600) and pose law. Only the panel
polygon sections broaden inward in stow: the negative local-Y edge is kept
exactly at the R1 value while the positive local-Y edge grows, doubling the
chord widths (120/88 forward, 88/68 rear) toward the global centreline in
stow. Endpoint +/-12 tabs and the circular bore cylinders/holes are unchanged.
"""
from cadgen import build123d as bd, step
from joined_wing_r1 import (pose, STATES, FRONT_LENGTH, REAR_LENGTH, FRONT_Z,
                            REAR_Z, THICKNESS, cylinder, fixed_housing,
                            fixed_root, tag, body)


def panel_local(length, root_neg, root_pos, tip_neg, tip_pos):
    # Negative local-Y edge kept at the R1 value; positive edge broadened.
    outline = [(0, -12), (25, root_neg), (length - 25, tip_neg),
               (length, -12), (length, 12), (length - 25, tip_pos),
               (25, root_pos), (0, 12)]
    face = bd.Face(bd.Wire.make_polygon([(x, y, 0) for x, y in outline], close=True))
    panel = bd.extrude(face, amount=THICKNESS)
    for x in (0, length):
        panel = panel + cylinder(12, THICKNESS, (x, 0), 0)
        panel = panel - cylinder(3.75, THICKNESS + 2, (x, 0), -1)
    return panel.clean()


def components(fraction):
    data = pose(fraction)
    front = panel_local(FRONT_LENGTH, -30, 90, -22, 66).rotate(
        bd.Axis.Z, data['front_angle']).translate((*data['front'], FRONT_Z))
    rear = panel_local(REAR_LENGTH, -22, 66, -17, 51).rotate(
        bd.Axis.Z, data['rear_angle']).translate((*data['rear'], REAR_Z))
    slider = bd.Box(60, 16, 2).translate((*data['rear'], 89.25))
    slider = slider + cylinder(3.5, 7, data['rear'], 89)
    slider = slider + cylinder(7, 2, data['rear'], 95.5)
    join_pin = cylinder(3.5, 14, data['joint'], 90.5) + cylinder(7, 2, data['joint'], 103)
    return [fixed_housing(), fixed_root(),
            tag(slider.clean(), 'sliding_rear_root_carriage', '#566B76'),
            tag(front, 'forward_lifting_panel', '#849EAB'),
            tag(rear, 'rear_lifting_panel', '#A8B9BF'),
            tag(join_pin.clean(), 'outboard_join_pin', '#4F626B')]


def assembly(state, with_body=True):
    parts = components(STATES[state])
    if with_body:
        parts.insert(0, body())
    return bd.Compound(children=parts, label='Phantom_joined_side_R2_' + state)


@step(out='../STEP/M_JoinedWing_R2_Stowed.step')
def stowed():
    return assembly('Stowed')


@step(out='../STEP/M_JoinedWing_R2_Midfold.step')
def midfold():
    return assembly('Midfold')


@step(out='../STEP/M_JoinedWing_R2_Deployed.step')
def deployed():
    return assembly('Deployed')


@step(out='../STEP/M_JoinedWing_R2_Module_Stowed.step')
def module_stowed():
    return assembly('Stowed', False)


@step(out='../STEP/M_JoinedWing_R2_Module_Midfold.step')
def module_midfold():
    return assembly('Midfold', False)


@step(out='../STEP/M_JoinedWing_R2_Module_Deployed.step')
def module_deployed():
    return assembly('Deployed', False)


if __name__ == '__main__':
    stowed()
    midfold()
    deployed()
    module_stowed()
    module_midfold()
    module_deployed()