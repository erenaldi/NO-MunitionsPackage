"""One linked fore/aft wing side with carriage-driven visual deployment.

Original game-asset geometry. DiamondBack joined architecture is sourced;
these link lengths, layers, hinge axes and pose law are explicitly inferred.
"""
import math
from cadgen import build123d as bd, step
from sketch_nose_r1_shapes import tag
from symmetric_body_r7 import body

FRONT_X = 500.0
ROOT_Y = 35.0
FRONT_LENGTH = 900.0
REAR_LENGTH = 600.0
FRONT_Z = 98.0
REAR_Z = 91.0
THICKNESS = 4.0
STOW_OFFSET = 5.0
STOW_SEPARATION = math.sqrt(FRONT_LENGTH**2-STOW_OFFSET**2)-math.sqrt(REAR_LENGTH**2-STOW_OFFSET**2)
OPEN_SEPARATION = 750.0
STATES = {'Stowed':0.0,'Midfold':0.5,'Deployed':1.0}


def pose(fraction):
    if not 0 <= fraction <= 1:
        raise ValueError('Pose fraction must be within [0,1]')
    separation=STOW_SEPARATION+(OPEN_SEPARATION-STOW_SEPARATION)*fraction
    aft=(FRONT_LENGTH**2-REAR_LENGTH**2+separation**2)/(2*separation)
    outward=math.sqrt(FRONT_LENGTH**2-aft**2)
    front=(FRONT_X,ROOT_Y)
    rear=(FRONT_X-separation,ROOT_Y)
    joint=(FRONT_X-aft,ROOT_Y+outward)
    front_angle=math.degrees(math.atan2(outward,-aft))
    rear_angle=math.degrees(math.atan2(outward,separation-aft))
    return dict(front=front,rear=rear,joint=joint,front_angle=front_angle,
                rear_angle=rear_angle,separation=separation)


def cylinder(radius,height,point,z):
    return bd.Cylinder(radius,height,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)).translate((*point,z))


def panel_local(length,root_width,tip_width):
    # The lifting members themselves connect the root and outboard joint.
    outline=[(0,-12),(25,-root_width/2),(length-25,-tip_width/2),
             (length,-12),(length,12),(length-25,tip_width/2),
             (25,root_width/2),(0,12)]
    face=bd.Face(bd.Wire.make_polygon([(x,y,0) for x,y in outline],close=True))
    panel=bd.extrude(face,amount=THICKNESS)
    for x in (0,length):
        panel=panel+cylinder(12,THICKNESS,(x,0),0)
        panel=panel-cylinder(3.75,THICKNESS+2,(x,0),-1)
    return panel.clean()


def fixed_housing():
    base=bd.Box(1000,120,4).translate((50,0,86))
    # An open, readable longitudinal guide for the moving rear-root carriage.
    for y in (24,46):
        base=base+bd.Box(540,4,2.5).translate((-30,y,89))
    return tag(base.clean(),'joined_wing_dorsal_housing','#697B84')


def fixed_root():
    point=(FRONT_X,ROOT_Y)
    pedestal=cylinder(10,10.5,point,87)
    shaft=cylinder(3.5,7,point,97)
    cap=cylinder(7,2,point,103)
    return tag((pedestal+shaft+cap).clean(),'fixed_forward_root','#4F626B')


def components(fraction):
    data=pose(fraction)
    front=panel_local(FRONT_LENGTH,60,44).rotate(bd.Axis.Z,data['front_angle']).translate((*data['front'],FRONT_Z))
    rear=panel_local(REAR_LENGTH,44,34).rotate(bd.Axis.Z,data['rear_angle']).translate((*data['rear'],REAR_Z))
    slider=bd.Box(60,16,2).translate((*data['rear'],89.25))
    slider=slider+cylinder(3.5,7,data['rear'],89)
    slider=slider+cylinder(7,2,data['rear'],95.5)
    join_pin=cylinder(3.5,14,data['joint'],90.5)+cylinder(7,2,data['joint'],103)
    return [fixed_housing(),fixed_root(),
            tag(slider.clean(),'sliding_rear_root_carriage','#566B76'),
            tag(front,'forward_lifting_panel','#849EAB'),
            tag(rear,'rear_lifting_panel','#A8B9BF'),
            tag(join_pin.clean(),'outboard_join_pin','#4F626B')]


def assembly(state,with_body=True):
    parts=components(STATES[state])
    if with_body:
        parts.insert(0,body())
    return bd.Compound(children=parts,label='Phantom_joined_side_R1_'+state)


@step(out='../STEP/L_JoinedWing_R1_Stowed.step')
def stowed():
    return assembly('Stowed')


@step(out='../STEP/L_JoinedWing_R1_Midfold.step')
def midfold():
    return assembly('Midfold')


@step(out='../STEP/L_JoinedWing_R1_Deployed.step')
def deployed():
    return assembly('Deployed')


@step(out='../STEP/L_JoinedWing_R1_Module_Stowed.step')
def module_stowed():
    return assembly('Stowed',False)


@step(out='../STEP/L_JoinedWing_R1_Module_Midfold.step')
def module_midfold():
    return assembly('Midfold',False)


@step(out='../STEP/L_JoinedWing_R1_Module_Deployed.step')
def module_deployed():
    return assembly('Deployed',False)


if __name__ == '__main__':
    stowed()
    midfold()
    deployed()
    module_stowed()
    module_midfold()
    module_deployed()
