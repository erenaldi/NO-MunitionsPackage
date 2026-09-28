"""A — interleaved two-set packaging; probe-passed layer heights and housing.

Same body, panel factories, X/Y pose law and hardware formulas as N/R3
(joined_wing_r3). Only the layer heights and the dorsal housing change to the
values validated in-memory by checks/probe_interleaved_a.py (passed):
starboard rear 88.75 / front 99.25, port rear 94.25 / front 104.75, giving
5.5 mm corresponding-panel offset; shelf lowered to Z93..93.5 with guides
93.5..94 and beam top 93.5. Not production approval.
"""
from cadgen import build123d as bd, step
from joined_wing_r1 import pose as old_pose, cylinder, tag, body
from joined_wing_r2 import panel_local

LAYERS = {'starboard': (88.75, 99.25), 'port': (94.25, 104.75)}


def pose(fraction, side):
    p = old_pose(fraction)
    return {**p, **{key: (p[key][0], (p[key][1]-5)*(1 if side=='starboard' else -1))
                   for key in ('front', 'rear', 'joint')}}


def box(x0,x1,y0,y1,z0,z1):
    return bd.Box(x1-x0,y1-y0,z1-z0).translate(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))


def housing():
    h=box(-450,550,-74,74,86,88)
    for y in (19,41):
        h=h+box(-300,250,y-1,y+1,88,88.5)
    h=h+box(-300,250,-74,-70,88,93.5)
    h=h+box(-300,250,-72,-18,93,93.5)
    for y in (-41,-19):
        h=h+box(-300,250,y-1,y+1,93.5,94)
    return tag(h.clean(),'supported_housing','#697B84')


def place_panel(panel, side, kind, fraction):
    p=old_pose(fraction)
    z=LAYERS[side][0 if kind=='rear' else 1]
    result=panel.rotate(bd.Axis.Z,p[kind+'_angle']).translate((p[kind][0],p[kind][1]-5,z))
    return result if side=='starboard' else result.mirror(bd.Plane.XZ)


def components(fraction):
    parts=[housing()]
    for side,(rz,fz) in LAYERS.items():
        p=pose(fraction,side)
        front=place_panel(panel_local(900,-30,90,-22,66),side,'front',fraction)
        rear=place_panel(panel_local(600,-22,66,-17,51),side,'rear',fraction)
        parts.extend([tag(front,side+'_front','#849EAB' if side=='starboard' else '#9CAAA0'),
                      tag(rear,side+'_rear','#B4C4CC' if side=='starboard' else '#C1C8AA')])
        foot=cylinder(10,fz-.25-87,p['front'],87)
        shaft=cylinder(3.5,fz+4.5-87,p['front'],87)
        cap=cylinder(7,.5,p['front'],fz+4.25)
        parts.append(tag((foot+shaft+cap).clean(),side+'_fixed_root','#4F626B'))
        x,y=p['rear']
        bottom=rz-.75
        carriage=box(x-30,x+30,y-8,y+8,bottom,bottom+.5)
        carriage=carriage+cylinder(3.5,5.25,p['rear'],bottom)
        carriage=carriage+cylinder(7,.5,p['rear'],rz+4.25)
        parts.append(tag(carriage.clean(),side+'_carriage','#566B76'))
        pin=cylinder(3.5,fz+4.5-(rz-.25),p['joint'],rz-.25)
        pin=pin+cylinder(7,.5,p['joint'],fz+4.25)
        parts.append(tag(pin.clean(),side+'_join','#4F626B'))
    return parts


def assembly(fraction, full=True):
    parts=components(fraction)
    if full:
        parts.insert(0,body())
    return bd.Compound(children=parts,label='Phantom_interleaved_A')


@step(out='../STEP/O_Interleaved_A_Stowed.step')
def stowed():
    return assembly(0)


@step(out='../STEP/O_Interleaved_A_Module_Stowed.step')
def module_stowed():
    return assembly(0,False)


@step(out='../STEP/O_Interleaved_A_Midfold.step')
def midfold():
    return assembly(.5)


@step(out='../STEP/O_Interleaved_A_Deployed.step')
def deployed():
    return assembly(1)


if __name__=='__main__':
    stowed()
    module_stowed()
    midfold()
    deployed()