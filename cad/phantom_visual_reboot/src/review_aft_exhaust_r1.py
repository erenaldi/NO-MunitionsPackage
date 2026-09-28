"""Saved exhaust section and actual-donor-pylon reference review artifacts."""
import json
from cadgen import build123d as bd, read_step, declare_input, srgb, step
from ramp_intake_r1 import ROOT


def leaves(shape):
    if shape.children:
        return [p for child in shape.children for p in leaves(child)]
    return [shape]


@step(out='../STEP/S_AftExhaust_R1_AftSection.step')
def aft_section():
    source = read_step(ROOT/'STEP/S_AftExhaust_R1_Deployed.step')
    clip = bd.Box(1155,500,400).translate((-827.5,250,0))
    pieces = []
    for part in leaves(source):
        common = part & clip
        if common is not None and common.volume > .0001:
            common.label = str(part.label)+'_SECTION_REVIEW_ONLY'
            common.color = part.color
            pieces.append(common)
    return bd.Compound(children=pieces,label='AFT_HALF_SECTION_REVIEW_ONLY')


def pylon_surface():
    path = ROOT/'reference/agm1_mount/pylon_candidate_frame.json'
    declare_input(path)
    data = json.loads(path.read_text(encoding='utf-8'))
    vertices = data['vertices_CAD_mm']
    faces = [bd.Face(bd.Wire.make_polygon([vertices[i] for i in tri],close=True))
             for tri in data['triangles']]
    result = bd.Compound(children=faces,label='ACTUAL_DONOR_PYLON_SURFACE_REFERENCE_ONLY')
    result.color = srgb('#C4874D')
    return result


@step(out='../reference/agm1_mount/DonorPylon_Surface.step')
def donor_pylon():
    return pylon_surface()


@step(out='../reference/agm1_mount/Phantom_DonorFit_Unchanged.step')
def donor_fit():
    source = read_step(ROOT/'STEP/S_AftExhaust_R1_Stowed.step')
    return bd.Compound(children=[source,pylon_surface()],label='UNCHANGED_DONOR_PLACEMENT_COLLISION_REVIEW')


def jobs():
    views = [
        ('STEP/S_AftExhaust_R1_Stowed.step','stowed_rear',[-1,1,.65],[0,0,0],1000),
        ('STEP/S_AftExhaust_R1_Deployed.step','deployed_rear',[-1,1,.65],[0,0,0],1100),
        ('STEP/S_AftExhaust_R1_Stowed.step','rear_opening',[-1,0,0],[-1400,0,0],125),
        ('STEP/S_AftExhaust_R1_Stowed.step','rear_close',[-1,.3,.2],[-1360,0,0],170),
        ('STEP/S_AftExhaust_R1_AftSection.step','duct_section',[0,-1,0],[-827.5,0,0],470),
        ('STEP/S_AftExhaust_R1_Liner.step','liner',[-1,1,.7],[-1350,0,0],110),
        ('reference/agm1_mount/DonorPylon_Surface.step','actual_pylon',[1,-1,.7],[0,0,150],650),
        ('reference/agm1_mount/Phantom_DonorFit_Unchanged.step','donor_fit_collision',[1,-1,.7],[0,0,60],1000),
    ]
    packet = [{'input':path,'mode':'view','output':{'tightFrame':False},'outputs':[{
        'path':f'reviews/S_Aft_R1_{name}.png','camera':{'direction':direction,'up':[0,0,1],
        'target':target,'orthographicHalfHeight':hh,'projection':'orthographic'}}]}
        for path,name,direction,target,hh in views]
    (ROOT/'review_aft_exhaust_r1.json').write_text(json.dumps(packet,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    aft_section()
    donor_pylon()
    donor_fit()
    jobs()
