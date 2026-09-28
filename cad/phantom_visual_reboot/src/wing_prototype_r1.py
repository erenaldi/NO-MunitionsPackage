"""One reversible main-wing prototype, before opposite-side propagation.

mm, +X forward, +Z dorsal. Same rigid wing at 0/-45/-90 degrees around
one visible vertical pin. This is visual packaging, not flight engineering.
"""
from cadgen import build123d as bd, step
from sketch_nose_r1_shapes import tag
from symmetric_body_r7 import body

HINGE_X = -160.0
HINGE_Z = 89.5
SPAN = 650.0
THICKNESS = 4.0
POSES = {'deployed':0.0, 'midfold':-45.0, 'stowed':-90.0}


def axis():
    return bd.Axis((HINGE_X,0,0),(0,0,1))


def wing(angle):
    profile = bd.Face(bd.Wire.make_polygon([
        (HINGE_X+x,y,HINGE_Z) for x,y in
        [(-70,15),(70,15),(30,SPAN),(-60,SPAN)]],close=True))
    panel = bd.extrude(profile,amount=THICKNESS)
    root = bd.Cylinder(22,THICKNESS,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)).translate((HINGE_X,0,HINGE_Z))
    bore = bd.Cylinder(4.1,THICKNESS+2,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)).translate((HINGE_X,0,HINGE_Z-1))
    return tag(((panel+root)-bore).rotate(axis(),angle),
               'prototype_starboard_wing', '#8498A0')


def hardware():
    saddle = tag(bd.Box(60,50,6).translate((HINGE_X,0,86)),
                 'prototype_hinge_saddle','#697D85')
    pin = bd.Cylinder(4,6,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)).translate((HINGE_X,0,88.5))
    cap = bd.Cylinder(8,2,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)).translate((HINGE_X,0,94))
    return [saddle,tag(pin+cap,'prototype_hinge_pin_and_cap','#566A73')]


def assembly(state):
    return bd.Compound(children=[body(),*hardware(),wing(POSES[state])],
                       label='RDM9_one_wing_prototype_'+state)


@step(out='../STEP/K_Wing_Prototype_R1_Deployed.step')
def deployed():
    return assembly('deployed')


@step(out='../STEP/K_Wing_Prototype_R1_Stowed.step')
def stowed():
    return assembly('stowed')


@step(out='../STEP/K_Wing_Prototype_R1_Midfold.step')
def midfold():
    return assembly('midfold')


if __name__ == '__main__':
    deployed()
    stowed()
    midfold()
